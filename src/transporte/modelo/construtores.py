"""Construtores das visões G_P e G_E a partir da Rede normalizada (docs/fontes/modelagem.md §3.4).

O que os construtores leem da Rede (P0-DADOS) está descrito em `RedeConstrutores`:
paradas com coordenadas, padrões com a sequência de paradas e, por padrão, os horários de
cada viagem na ordem das paradas. É a identidade da viagem que permite calcular o tempo
entre paradas consecutivas (decisão D2).

Notação das complexidades:
    V: paradas da Rede.
    L: plataformas, isto é, soma do número de paradas de cada padrão.
    N: horários das viagens (soma, sobre as viagens, do número de paradas).
    K: pares de paradas a até o raio de caminhada.

As arestas de caminhada usam uma grade espacial com células do tamanho do raio: cada
parada só é comparada com as das 9 células vizinhas, então o custo esperado é O(V + K) em
vez dos O(V²) da busca ingênua.

estado: implementado
"""

from __future__ import annotations

import math
import pickle
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol

from transporte.grafo.grafo import Grafo
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import (
    CAMINHADA,
    DESEMBARQUE,
    EMBARQUE,
    VIAGEM,
    Visao,
    VisaoGE,
    VisaoGP,
)

# Raio médio da Terra, em metros, usado na fórmula de haversine.
_RAIO_TERRA_M = 6_371_000.0


# --- O que os construtores esperam da Rede ---------------------------------------------


class ParadaConstrutores(Protocol):
    """Campos de uma parada que os construtores leem."""

    id: str
    lat: float
    lon: float


class PadraoConstrutores(Protocol):
    """Campos de um padrão que os construtores leem."""

    id: str
    paradas: Sequence[str]


class RedeConstrutores(Protocol):
    """Campos da Rede (P0-DADOS) que os construtores leem.

    Atributos:
        paradas: id da parada -> parada.
        padroes: id do padrão -> padrão (linha + sequência exata de paradas, decisão D1).
        viagens: id do padrão -> uma lista de horários por viagem do dia típico, em
            segundos desde 00:00, alinhada com padrao.paradas (horários acima de 86400 são
            válidos). Proposta a P0-DADOS: o `partidas[(padrão, parada)]` do diagrama de
            classes perde a identidade da viagem.
    """

    paradas: Mapping[str, ParadaConstrutores]
    padroes: Mapping[str, PadraoConstrutores]
    viagens: Mapping[str, Sequence[Sequence[int]]]


# --- Auxiliares ------------------------------------------------------------------------


def _distancia_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em linha reta (haversine) entre dois pontos, em metros. O(1)."""
    f1, f2 = math.radians(lat1), math.radians(lat2)
    df = f2 - f1
    dl = math.radians(lon2 - lon1)
    h = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * _RAIO_TERRA_M * math.asin(min(1.0, math.sqrt(h)))


def _pares_caminhada(
    paradas: Sequence[ParadaConstrutores], raio_m: float
) -> list[tuple[int, int, float]]:
    """Pares (i, j, distância) de paradas distintas a até raio_m, com i < j.

    Grade espacial: as coordenadas são projetadas em metros (equirretangular) e cada
    parada cai numa célula de lado raio_m; dois pontos a até raio_m ficam em células
    vizinhas, então basta comparar cada parada com as 9 células em volta. A projeção usa o
    cosseno da maior latitude em módulo, o que encolhe as distâncias leste-oeste, e a
    célula tem 0,1% de folga para cobrir a diferença de segunda ordem entre a projeção e a
    esfera; assim nenhum par dentro do raio fica fora da vizinhança. A distância final é a
    de haversine.
    Complexidade: tempo esperado O(V + K); espaço O(V + K).
    """
    if not paradas or raio_m <= 0:
        return []
    cos_ref = min(math.cos(math.radians(p.lat)) for p in paradas)
    lado = 1.001 * raio_m / (_RAIO_TERRA_M * math.pi / 180)  # raio em graus, com folga
    celulas: dict[tuple[int, int], list[int]] = {}
    chave = []
    for i, p in enumerate(paradas):
        c = (math.floor(p.lat / lado), math.floor(p.lon * cos_ref / lado))
        chave.append(c)
        celulas.setdefault(c, []).append(i)
    pares = []
    for i, p in enumerate(paradas):
        ci, cj = chave[i]
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for j in celulas.get((ci + di, cj + dj), ()):
                    if j <= i:
                        continue
                    q = paradas[j]
                    d = _distancia_m(p.lat, p.lon, q.lat, q.lon)
                    if d <= raio_m:
                        pares.append((i, j, d))
    return pares


def _mediana(valores: list[float]) -> float:
    """Mediana de uma lista não vazia (média dos dois centrais se o tamanho é par).
    Tempo O(n log n), pela ordenação."""
    ordenados = sorted(valores)
    m = len(ordenados) // 2
    if len(ordenados) % 2:
        return float(ordenados[m])
    return (ordenados[m - 1] + ordenados[m]) / 2


def _diferencas(viagens: Sequence[Sequence[int]], k: int) -> list[float]:
    """Diferenças de horário entre a parada k e a k + 1 em cada viagem, sem as negativas.

    Diferença negativa é erro de cadastro (a viagem chegaria antes de sair) e fica fora da
    mediana (decisão D8). Viagem com menos horários que paradas é ignorada.
    Complexidade: O(número de viagens).
    """
    difs = []
    for horarios in viagens:
        if len(horarios) > k + 1:
            d = horarios[k + 1] - horarios[k]
            if d >= 0:
                difs.append(float(d))
    return difs


def _peso_viagem(difs: list[float], params: Parametros) -> float:
    """Mediana das diferenças com o piso params.peso_minimo_s (decisão M2). Sem nenhuma
    diferença válida, o trecho ainda existe na sequência do padrão e recebe o piso
    (decisão D8). O(n log n)."""
    if not difs:
        return params.peso_minimo_s
    return max(params.peso_minimo_s, _mediana(difs))


def _adicionar_caminhada(
    g: Grafo,
    paradas: Sequence[ParadaConstrutores],
    vertice: Sequence[int],
    params: Parametros,
) -> None:
    """Arestas CAMINHADA nos dois sentidos entre paradas a até o raio; peso = distância /
    velocidade, com o piso. Tempo esperado O(V + K)."""
    for i, j, d in _pares_caminhada(paradas, params.raio_caminhada_m):
        peso = max(params.peso_minimo_s, d / params.velocidade_caminhada_ms)
        g.adicionar_aresta(vertice[i], vertice[j], peso, CAMINHADA)
        g.adicionar_aresta(vertice[j], vertice[i], peso, CAMINHADA)


def _paradas_conhecidas(rede: RedeConstrutores, padrao: PadraoConstrutores) -> None:
    for pid in padrao.paradas:
        if pid not in rede.paradas:
            raise KeyError(f"padrão {padrao.id} usa parada inexistente: {pid}")


# --- Construtores ----------------------------------------------------------------------


def construir_gp(rede: RedeConstrutores, params: Parametros | None = None) -> VisaoGP:
    """Constrói G_P: um vértice por parada, arestas de viagem e de caminhada.

    Entradas:
        rede: modelo normalizado (P0-DADOS), já recortado se for o caso.
        params: parâmetros da modelagem; None usa os valores padrão.
    Saída: VisaoGP com o grafo e os mapas parada <-> vértice. Os vértices seguem a ordem
        de rede.paradas.
    Arestas:
        VIAGEM a -> b para cada par de paradas consecutivas em algum padrão; peso = mediana
            das diferenças de horário de todas as viagens de todos os padrões que passam
            por esse trecho, com o piso params.peso_minimo_s.
        CAMINHADA nos dois sentidos entre paradas a até o raio; peso = distância /
            velocidade, com o piso.
    Casos de borda: parada sem nenhuma viagem vira vértice isolado (ainda pode ter
        caminhada); dois padrões com o mesmo trecho geram uma única aresta de viagem,
        com a mediana dos tempos de ambos; parada repetida em sequência no padrão não gera
        laço; diferenças negativas ficam fora da mediana e trecho sem diferença válida
        recebe o piso (D8); padrão com parada inexistente levanta KeyError; rede vazia
        devolve grafo vazio.
    Complexidade: tempo O(V + K + N log N) esperado (grade espacial; O(V² + N log N) no
        pior caso, com todas as paradas na mesma célula); espaço O(V + E).
    """
    params = params or Parametros()
    g = Grafo()
    visao = VisaoGP(grafo=g, nome="G_P")
    paradas = list(rede.paradas.values())
    for p in paradas:
        v = g.adicionar_vertice(p.id)
        visao.vertice_da_parada[p.id] = v
        visao.parada_do_vertice.append(p.id)

    # Trecho (a, b) -> diferenças de horário de todas as viagens que passam por ele.
    trechos: dict[tuple[str, str], list[float]] = {}
    for padrao in rede.padroes.values():
        _paradas_conhecidas(rede, padrao)
        viagens = rede.viagens.get(padrao.id, ())
        seq = padrao.paradas
        for k in range(len(seq) - 1):
            if seq[k] == seq[k + 1]:
                continue
            trechos.setdefault((seq[k], seq[k + 1]), []).extend(_diferencas(viagens, k))
    for (a, b), difs in trechos.items():
        g.adicionar_aresta(
            visao.vertice_da_parada[a],
            visao.vertice_da_parada[b],
            _peso_viagem(difs, params),
            VIAGEM,
        )

    _adicionar_caminhada(g, paradas, range(len(paradas)), params)
    return visao


def _partidas_na_faixa(viagens: Sequence[Sequence[int]], inicio: int, fim: int) -> bool:
    """True se alguma viagem parte (primeiro horário) dentro de [inicio, fim). O(viagens)."""
    return any(h and inicio <= h[0] < fim for h in viagens)


def construir_ge(
    rede: RedeConstrutores,
    faixa: str,
    params: Parametros | None = None,
    esperas: Mapping[tuple[str, str], float] | None = None,
) -> VisaoGE:
    """Constrói G_E para uma faixa horária: paradas, plataformas e as arestas de embarque,
    viagem, desembarque e caminhada.

    Entradas:
        rede: modelo normalizado (P0-DADOS).
        faixa: nome de uma faixa de params.faixas; define a espera nas arestas de embarque.
        params: parâmetros da modelagem; None usa os valores padrão.
        esperas: (id do padrão, nome da faixa) -> espera esperada no embarque, em segundos,
            calculada pela F-ESPERA (RF-ESP-02: H/2 com intervalo regular, E[H²]/(2 E[H])
            com intervalo irregular) e aplicada sem transformação. None, ou par ausente da
            tabela, usa params.espera_padrao_s.
    Saída: VisaoGE com o grafo, os mapas de paradas e plataformas e a faixa usada. Os
        vértices de parada vêm primeiro, na ordem de rede.paradas; depois as plataformas,
        padrão a padrão.
    Arestas:
        EMBARQUE parada -> plataforma (espera), exceto na última parada do padrão.
        VIAGEM plataforma -> plataforma seguinte do mesmo padrão; peso = mediana das
            diferenças das viagens desse padrão, com o piso.
        DESEMBARQUE plataforma -> parada (peso 0), exceto na primeira parada do padrão.
        CAMINHADA como em G_P.
    Casos de borda: padrão sem partida na faixa (nenhuma viagem cujo primeiro horário cai
        nela) não recebe aresta de embarque (não dá para embarcar nele naquela faixa),
        mesmo que a tabela de esperas traga um valor para ele; espera negativa, infinita
        ou NaN na tabela levanta ValueError (Grafo.adicionar_aresta);
        padrão com uma parada só é ignorado; padrão que passa duas vezes pela mesma parada
        (linha circular) usa uma plataforma só para ela; faixa inexistente levanta
        KeyError; padrão com parada inexistente levanta KeyError.
    Complexidade: tempo O(V + K + L + N log N) esperado (O(V² + L + N log N) no pior
        caso); espaço O(V + L + K).
    """
    params = params or Parametros()
    f = params.faixa(faixa)
    g = Grafo()
    visao = VisaoGE(grafo=g, nome="G_E", faixa=faixa)
    paradas = list(rede.paradas.values())
    for p in paradas:
        visao.vertice_da_parada[p.id] = g.adicionar_vertice(p.id)

    for padrao in rede.padroes.values():
        seq = padrao.paradas
        if len(seq) < 2:
            continue
        _paradas_conhecidas(rede, padrao)
        viagens = rede.viagens.get(padrao.id, ())
        plat = []
        for pid in seq:
            chave = (pid, padrao.id)
            if chave not in visao.plataforma:
                visao.plataforma[chave] = g.adicionar_vertice(f"{pid}@{padrao.id}")
            plat.append(visao.plataforma[chave])

        if _partidas_na_faixa(viagens, f.inicio_s, f.fim_s):
            e = None if esperas is None else esperas.get((padrao.id, faixa))
            espera = params.espera_padrao_s if e is None else e
            embarques = set()  # plataforma repetida (linha circular) embarca uma vez só
            for k in range(len(seq) - 1):
                if plat[k] not in embarques:
                    embarques.add(plat[k])
                    g.adicionar_aresta(
                        visao.vertice_da_parada[seq[k]], plat[k], espera, EMBARQUE
                    )
        for k in range(len(seq) - 1):
            if plat[k] != plat[k + 1]:
                peso = _peso_viagem(_diferencas(viagens, k), params)
                g.adicionar_aresta(plat[k], plat[k + 1], peso, VIAGEM)
        desembarques = set()
        for k in range(1, len(seq)):
            if plat[k] not in desembarques:
                desembarques.add(plat[k])
                g.adicionar_aresta(
                    plat[k], visao.vertice_da_parada[seq[k]], 0.0, DESEMBARQUE
                )

    _adicionar_caminhada(
        g, paradas, [visao.vertice_da_parada[p.id] for p in paradas], params
    )
    return visao


# --- Persistência (RF-GRF-07) ----------------------------------------------------------


def salvar(visao: Visao, caminho: Path) -> None:
    """Grava a visão em disco para não reprocessar o GTFS (RF-GRF-07).

    Usa pickle (decisão D7): o arquivo é cache gerado pela própria ferramenta em
    dados/cache/, fora do Git, e nunca vem de fonte externa.
    Entradas: a visão e o caminho do arquivo, sobrescrito se existir; as pastas que
        faltarem são criadas.
    Complexidade: tempo e espaço O(V + E).
    """
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("wb") as arq:
        pickle.dump(visao, arq, protocol=pickle.HIGHEST_PROTOCOL)


def carregar(caminho: Path) -> Visao:
    """Lê uma visão gravada por salvar.

    Entrada: caminho de um arquivo gerado por salvar. Só abrir arquivos gerados pela
        própria ferramenta: pickle de fonte desconhecida pode executar código.
    Saída: a visão, com o mesmo tipo concreto que foi salvo.
    Casos de borda: arquivo inexistente levanta FileNotFoundError; arquivo que não contém
        uma Visao levanta TypeError.
    Complexidade: tempo e espaço O(V + E).
    """
    with Path(caminho).open("rb") as arq:
        visao = pickle.load(arq)  # seguro só para cache local (D7)
    if not isinstance(visao, Visao):
        raise TypeError(f"{caminho} não contém uma Visao")
    return visao
