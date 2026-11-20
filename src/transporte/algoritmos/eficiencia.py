"""Métricas de eficiência global e de duração de viagens (F-EFI).

Eficiência estrutural opera sobre G_P. Tempos de viagem usam G_E e consideram apenas
pares de paradas, seguindo a duração total do caminho de F-ROTA.

estado: implementado
"""

from __future__ import annotations

import math
import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from transporte.algoritmos.trajeto import trajeto_mais_rapido
from transporte.dados.modelo import Rede
from transporte.grafo.buscas import INF, dijkstra
from transporte.grafo.grafo import Grafo
from transporte.modelo.construtores import _distancia_m, construir_ge
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import VisaoGE
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos


@dataclass(frozen=True)
class Estimativa:
    """Valor de uma métrica e informação da amostragem.

    Atributos:
        valor: estimativa; None quando nenhuma viagem amostrada foi alcançável.
        erro_padrao: erro padrão da média; None quando não é estimável. Uma enumeração
            exata retorna 0.0; sem observações alcançáveis, não há estimativa.
        tamanho_amostra: origens ou pares sorteados, conforme a métrica.
        tamanho_populacao: número de origens ou de pares ordenados possíveis.
        pares_alcancaveis: viagens alcançáveis observadas; None para eficiência global.
    Espaço O(1).
    """

    valor: float | None
    erro_padrao: float | None
    tamanho_amostra: int
    tamanho_populacao: int
    pares_alcancaveis: int | None = None


def _inteiro_positivo(nome: str, valor: int) -> None:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TypeError(f"{nome} deve ser int, recebido {type(valor).__name__}")
    if valor < 1:
        raise ValueError(f"{nome} deve ser >= 1, recebido {valor}")


def _semente_valida(semente: int) -> None:
    if isinstance(semente, bool) or not isinstance(semente, int):
        raise TypeError(f"semente deve ser int, recebido {type(semente).__name__}")


def _validar_origens(g: Grafo, origens: Iterable[int]) -> list[int]:
    lista = list(origens)
    if len(lista) != len(set(lista)):
        raise ValueError("origens não pode conter vértices repetidos")
    for origem in lista:
        if isinstance(origem, bool) or not isinstance(origem, int):
            raise TypeError("cada origem deve ser um id de vértice inteiro")
        if not 0 <= origem < g.num_vertices():
            raise IndexError(f"vértice inexistente: {origem}")
    return lista


def _soma_reciprocos(g: Grafo, origem: int) -> float:
    """Soma 1/d da origem aos demais vértices alcançáveis. O(Dijkstra)."""
    if not g.vertice_ativo(origem):
        return 0.0
    distancias = dijkstra(g, origem).dist
    soma = 0.0
    for destino, distancia in enumerate(distancias):
        if destino == origem or distancia == INF:
            continue
        if distancia == 0:
            raise ValueError(
                f"distância 0 entre vértices distintos {origem} e {destino}: eficiência infinita"
            )
        soma += 1.0 / distancia
    return soma


def eficiencia_global(
    g: Grafo,
    origens: Iterable[int] | None = None,
    n_referencia: int | None = None,
) -> float:
    """Média de 1/d(i, j) sobre pares ordenados distintos, em um grafo ponderado.

    Compatível com o contrato provisório consumido pela F-RES. A feature usa G_P, cujos
    pesos têm piso positivo; não aplicar diretamente a todos os vértices de G_E, que
    contém arestas de desembarque com peso zero.

    Entradas:
        g: grafo direcionado com pesos não negativos.
        origens: conjunto sem repetição de fontes dos Dijkstras. None usa todas as origens
            ativas. Uma origem inativa contribui zero, mas permanece no denominador.
        n_referencia: população original de vértices usada no denominador; None usa o
            número de vértices ativos. Deve ser >= ao número de vértices ativos.
    Saída: soma de 1/d dividida por s * (n_referencia - 1), em 1/unidade do peso. Pares
        sem caminho somam zero. Menos de dois vértices, ou conjunto vazio de origens,
        devolve 0.0.
    Casos de borda: origem inválida levanta IndexError; origem repetida ou população
        menor que a quantidade de vértices ativos levanta ValueError; tipos inválidos
        levantam TypeError; distância zero entre vértices distintos levanta ValueError.
    Complexidade: tempo O(V + s (V + E) log V), com s buscas de Dijkstra; espaço
        O(V + E + s), incluindo a lista de origens.
    """
    ativos = sum(g.vertice_ativo(v) for v in range(g.num_vertices()))
    if n_referencia is None:
        n = ativos
    else:
        if isinstance(n_referencia, bool) or not isinstance(n_referencia, int):
            raise TypeError("n_referencia deve ser int")
        if n_referencia < ativos or n_referencia < 0:
            raise ValueError("n_referencia não pode ser menor que os vértices ativos")
        n = n_referencia

    lista = (
        [v for v in range(g.num_vertices()) if g.vertice_ativo(v)]
        if origens is None
        else _validar_origens(g, origens)
    )
    quantidade_origens = n if origens is None else len(lista)
    if n < 2 or quantidade_origens == 0:
        return 0.0

    soma = sum(_soma_reciprocos(g, origem) for origem in lista)
    return soma / (quantidade_origens * (n - 1))


def _erro_padrao(valores: list[float]) -> float | None:
    if len(valores) < 2:
        return None
    media = sum(valores) / len(valores)
    variancia = sum((valor - media) ** 2 for valor in valores) / (len(valores) - 1)
    return math.sqrt(variancia / len(valores))


def estimar_eficiencia_global(
    g: Grafo,
    tamanho_amostra: int | None = None,
    semente: int = 0,
) -> Estimativa:
    """Estima eficiência global amostrando origens uniformemente sem reposição.

    A contribuição de cada origem é a média de 1/d para todos os demais vértices,
    contando pares inalcançáveis como zero. O erro informado é o erro padrão amostral
    das contribuições por origem, com correção para população finita; com amostra exata,
    é zero.

    Entradas:
        g: G_P recomendado para a métrica estrutural.
        tamanho_amostra: número de origens sorteadas; None calcula todas as origens.
        semente: semente inteira para tornar a amostra reproduzível.
    Saída: Estimativa em 1/unidade do peso, com tamanho da amostra e população.
    Casos de borda: grafo com menos de dois vértices tem eficiência zero; tamanho
        inválido levanta ValueError ou TypeError; peso zero entre vértices distintos
        levanta ValueError.
    Complexidade: tempo O(V + s (V + E) log V), sendo s o número de origens avaliadas;
        espaço O(V + E + s).
    """
    _semente_valida(semente)
    vertices = [v for v in range(g.num_vertices()) if g.vertice_ativo(v)]
    populacao = len(vertices)
    if tamanho_amostra is None:
        amostra = vertices
        exata = True
    else:
        _inteiro_positivo("tamanho_amostra", tamanho_amostra)
        if tamanho_amostra > populacao:
            raise ValueError("tamanho_amostra não pode exceder o número de origens ativas")
        rng = random.Random(semente)
        amostra = rng.sample(vertices, tamanho_amostra)
        exata = tamanho_amostra == populacao

    if populacao < 2:
        return Estimativa(0.0, 0.0, len(amostra), populacao)

    contribuicoes = [_soma_reciprocos(g, origem) / (populacao - 1) for origem in amostra]
    valor = sum(contribuicoes) / len(contribuicoes)
    if exata:
        erro = 0.0
    else:
        erro_amostral = _erro_padrao(contribuicoes)
        erro = (
            None
            if erro_amostral is None
            else erro_amostral * math.sqrt((populacao - len(amostra)) / populacao)
        )
    return Estimativa(valor, erro, len(amostra), populacao)


def tempo_medio_viagem(
    ge: VisaoGE,
    tamanho_amostra: int,
    semente: int = 0,
) -> Estimativa:
    """Estima a duração média do caminho mais rápido entre pares de paradas em G_E.

    Cada par ordenado distinto é sorteado uniformemente sem reposição. Para cada origem
    sorteada, roda-se uma busca Dijkstra e consulta-se o custo total do caminho, com a
    semântica de `Trajeto.tempo_total_s` da F-ROTA: caminhada, espera esperada e viagem.
    Plataformas não entram na população; pares sem caminho são contados à parte, não como
    viagens de duração zero. O erro é o erro padrão amostral dos tempos alcançáveis;
    uma enumeração exata com pelo menos uma viagem alcançável tem erro zero.

    Entradas:
        ge: G_E de uma faixa horária.
        tamanho_amostra: número de pares OD sorteados; deve ser >= 1.
        semente: semente inteira para tornar os pares reproduzíveis.
    Saída: Estimativa em segundos; valor None se nenhum par sorteado for alcançável.
    Casos de borda: com menos de duas paradas ativas, devolve valor None e população zero;
        parâmetros inválidos levantam ValueError ou TypeError; em amostra incompleta com
        menos de duas viagens alcançáveis o erro padrão é None; sem viagens alcançáveis,
        valor e erro padrão são None.
    Complexidade: tempo O(V + k (V + E) log V + m), k origens distintas e m pares
        sorteados; espaço O(V + E + m).
    """
    _inteiro_positivo("tamanho_amostra", tamanho_amostra)
    _semente_valida(semente)
    g = ge.grafo
    paradas = [vertice for vertice in ge.vertice_da_parada.values() if g.vertice_ativo(vertice)]
    if len(paradas) < 2:
        return Estimativa(None, None, 0, 0, 0)

    populacao = len(paradas) * (len(paradas) - 1)
    destinos_por_origem: dict[int, list[int]] = {}
    for origem, destino in sortear_pares(paradas, tamanho_amostra, semente):
        destinos_por_origem.setdefault(origem, []).append(destino)

    tempos = []
    for origem, destinos in destinos_por_origem.items():
        distancias = dijkstra(g, origem).dist
        tempos.extend(distancias[destino] for destino in destinos if distancias[destino] != INF)

    valor = sum(tempos) / len(tempos) if tempos else None
    erro = 0.0 if tamanho_amostra == populacao and tempos else _erro_padrao(tempos)
    return Estimativa(valor, erro, tamanho_amostra, populacao, len(tempos))


def sortear_pares[T](paradas: Sequence[T], tamanho_amostra: int, semente: int) -> list[tuple[T, T]]:
    """Amostra pares ordenados de IDs distintos, uniformemente e sem reposição.

    Menos de duas paradas dá lista vazia. Amostra excessiva ou não positiva
    gera ValueError. Mesmo conjunto na mesma ordem e semente repetem os pares.
    Tempo e espaço O(m) para m pares, sem materializar a população quadrática.
    """
    _inteiro_positivo("tamanho_amostra", tamanho_amostra)
    _semente_valida(semente)
    n = len(paradas)
    if n < 2:
        return []
    if tamanho_amostra > n * (n - 1):
        raise ValueError("tamanho_amostra não pode exceder o número de pares OD possíveis")
    indices = random.Random(semente).sample(range(n * (n - 1)), tamanho_amostra)
    pares = []
    for indice in indices:
        i, j = divmod(indice, n - 1)
        if j >= i:
            j += 1
        pares.append((paradas[i], paradas[j]))
    return pares


@dataclass(frozen=True)
class DesvioPar:
    origem: str
    destino: str
    quadrante: str
    direta_m: float
    percorrida_m: float | None
    tempo_s: float | None

    @property
    def desvio(self) -> float | None:
        if not self.direta_m or self.percorrida_m is None:
            return None
        return self.percorrida_m / self.direta_m

    @property
    def min_por_km(self) -> float | None:
        if not self.direta_m or self.tempo_s is None:
            return None
        return self.tempo_s / 60 / (self.direta_m / 1000)


def indices_desvio(
    rede: Rede, ge: VisaoGE, tamanho_amostra: int, semente: int = 0
) -> list[DesvioPar]:
    """Calcula desvios nos trajetos de menor tempo em G_E para pares sorteados.

    Soma haversine entre paradas consecutivas caminhadas e de ônibus. O
    quadrante da origem usa o centro do retângulo das paradas ativas da visão.
    Preserva pares sem caminho ou com distância direta zero (razões None).
    Com menos de duas paradas devolve []. Para m pares, tempo O(V+m(V+E)log(E+2))
    e espaço auxiliar O(V+E+m), incluindo as reconstruções de F-ROTA.
    """
    paradas = [p for p, v in ge.vertice_da_parada.items() if ge.grafo.vertice_ativo(v)]
    pares = sortear_pares(paradas, tamanho_amostra, semente)
    if not pares:
        return []
    lats = [rede.paradas[p].lat for p in paradas]
    lons = [rede.paradas[p].lon for p in paradas]
    centro_lat = (min(lats) + max(lats)) / 2
    centro_lon = (min(lons) + max(lons)) / 2

    def distancia(a: str, b: str) -> float:
        p, q = rede.paradas[a], rede.paradas[b]
        return _distancia_m(p.lat, p.lon, q.lat, q.lon)

    resultado = []
    for origem, destino in pares:
        ponto = rede.paradas[origem]
        quadrante = ("N" if ponto.lat >= centro_lat else "S") + (
            "L" if ponto.lon >= centro_lon else "O"
        )
        trajeto = trajeto_mais_rapido(ge, origem, destino)
        percorrida = tempo = None
        if trajeto is not None:
            tempo = trajeto.tempo_total_s
            percorrida = sum(
                distancia(a, b)
                for trecho in trajeto.trechos
                for a, b in zip(trecho.paradas, trecho.paradas[1:])
            )
        resultado.append(
            DesvioPar(origem, destino, quadrante, distancia(origem, destino), percorrida, tempo)
        )
    return resultado


@dataclass(frozen=True)
class IndicadoresFaixa:
    faixa: str
    pares: int
    alcancaveis: int
    eficiencia_por_s: float | None
    tempo_medio_s: float | None
    erro_eficiencia_por_s: float | None
    erro_tempo_medio_s: float | None
    vertices: int
    arestas: int


def comparar_faixas(
    rede: Rede, tamanho_amostra: int, semente: int = 0, params: Parametros | None = None
) -> list[IndicadoresFaixa]:
    """Compara tempo e eficiência entre os mesmos pares de paradas nas faixas.

    Constrói G_E por faixa com as esperas da F-ESPERA. Divide a soma de 1/t
    por todos os pares e a soma dos tempos só pelos alcançáveis. Sem pares
    ambas as médias são None; com pares e nenhum alcançável a eficiência é
    zero. Erro padrão amostral na eficiência com correção populacional; na
    duração, usa os alcançáveis como em tempo_medio_viagem. Censo tem erro
    zero para estimativas definidas. Tempo O(F·(construção de G_E + k(V+E)log(E+2)+m)) para F faixas,
    m pares e k origens distintas, mais a estimação inicial das esperas.
    Espaço O(V+E+m+F) além da tabela de esperas e do trabalho dos construtores.
    """
    params = params or Parametros()
    pares = sortear_pares(list(rede.paradas), tamanho_amostra, semente)
    destinos_por_origem: dict[str, list[str]] = {}
    for origem, destino in pares:
        destinos_por_origem.setdefault(origem, []).append(destino)
    esperas = calcular_esperas(estimar_intervalos(rede, params))
    resultado = []
    populacao = len(rede.paradas) * (len(rede.paradas) - 1)
    for faixa in params.faixas:
        ge = construir_ge(rede, faixa.nome, params, esperas=esperas)
        tempos = []
        for origem, destinos in destinos_por_origem.items():
            v_origem = ge.vertice_da_parada[origem]
            ultimo = ge.vertice_da_parada[destinos[0]] if len(destinos) == 1 else None
            dist = dijkstra(ge.grafo, v_origem, ultimo).dist
            for destino in destinos:
                tempo = dist[ge.vertice_da_parada[destino]]
                if tempo != INF:
                    if tempo == 0:
                        raise ValueError(
                            "Duração zero entre paradas distintas: eficiência infinita."
                        )
                    tempos.append(tempo)
        inversos = [1 / t for t in tempos] + [0.0] * (len(pares) - len(tempos))
        erro_eficiencia = _erro_padrao(inversos)
        erro_tempo = _erro_padrao(tempos)
        if pares and len(pares) == populacao:
            erro_eficiencia = 0.0
            erro_tempo = 0.0 if tempos else None
        elif erro_eficiencia is not None:
            erro_eficiencia *= math.sqrt(1 - len(pares) / populacao)
        resultado.append(
            IndicadoresFaixa(
                faixa.nome,
                len(pares),
                len(tempos),
                sum(inversos) / len(pares) if pares else None,
                sum(tempos) / len(tempos) if tempos else None,
                erro_eficiencia,
                erro_tempo,
                ge.grafo.num_vertices(),
                ge.grafo.num_arestas(),
            )
        )
    return resultado


def medias_por_quadrante(desvios: Sequence[DesvioPar]) -> dict[str, float]:
    """Média das razões definidas por quadrante de origem. Sem observações, {}.

    Tempo O(m) nos m pares, espaço O(1) para os quatro quadrantes.
    """
    somas: dict[str, float] = {}
    contagens: dict[str, int] = {}
    for par in desvios:
        if par.desvio is not None:
            somas[par.quadrante] = somas.get(par.quadrante, 0.0) + par.desvio
            contagens[par.quadrante] = contagens.get(par.quadrante, 0) + 1
    return {q: soma / contagens[q] for q, soma in sorted(somas.items())}
