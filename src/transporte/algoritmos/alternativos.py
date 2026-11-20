"""k trajetos alternativos em G_E pelo algoritmo de Yen (F-ROTA-OPC, RF-ROT-05).

Yen lista os k caminhos sem ciclo de menor custo, em ordem crescente de custo. O primeiro
é o trajeto mais rápido. Para achar o i-ésimo, cada vértice do (i-1)-ésimo caminho vira, um
por vez, ponto de desvio: o trecho até ele (a raiz) é mantido, as arestas que os caminhos já
aceitos usam logo depois dessa mesma raiz são desativadas, os vértices da raiz (menos o
desvio) também, e uma busca do desvio ao destino completa o candidato. O melhor candidato
ainda não aceito vira o i-ésimo caminho.

Desativar e reativar usam a API de falhas do núcleo (RF-GRF-03). Só é reativado o que esta
função desativou, então falhas simuladas antes (F-RES) continuam valendo e o grafo volta
ao estado em que estava. As buscas de desvio usam o A* da F-ROTA-2 quando há coordenadas:
remover arestas não aumenta a velocidade de nenhuma aresta restante, então a heurística
continua consistente e o custo do desvio continua o ótimo.

Caminhos distintos são distintos em arestas de G_E: dois trajetos podem passar pelas mesmas
paradas e diferir na linha usada num trecho, ou num trecho a pé. No feed real, os k
primeiros costumam ser variantes do mesmo trajeto (trocar uma parada antes, outro trecho a
pé); `alternativos_por_linhas` continua tirando caminhos do Yen até achar k sequências de
linhas distintas ou bater um teto.

estado: implementado
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import islice
from typing import TYPE_CHECKING

from transporte.algoritmos.a_estrela import _buscar, _trajeto
from transporte.algoritmos.trajeto import ONIBUS
from transporte.grafo.buscas import INF
from transporte.grafo.heap import HeapMin

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

    from transporte.algoritmos.trajeto import Trajeto
    from transporte.modelo.visoes import VisaoGE


def _vertices(ge: VisaoGE, s: int, arestas: Sequence[int]) -> list[int]:
    """Vértices de um caminho a partir das arestas, com a origem. O(k)."""
    g = ge.grafo
    return [s, *(g.aresta(a)[1] for a in arestas)]


def _yen(
    ge: VisaoGE,
    s: int,
    t: int,
    coords: Sequence[tuple[float, float]] | None,
    vmax: float,
) -> Iterator[tuple[float, list[int]]]:
    """Gera os caminhos sem ciclo de s a t, em ordem crescente de custo, sob demanda.

    Cada caminho só é calculado quando pedido, então quem consome pode parar a qualquer
    momento. O grafo está no estado original a cada `yield` (as desativações de um desvio
    são desfeitas no `finally` antes de seguir). Tempo por caminho: O(n · (V + E) log V).
    """
    g = ge.grafo
    custo, arestas, _ = _buscar(ge, s, t, coords, vmax)
    if custo == INF:
        return
    aceitos: list[list[int]] = [arestas]
    yield custo, arestas
    vistos = {tuple(arestas)}
    candidatos: list[tuple[float, list[int]]] = []
    fila = HeapMin()  # (custo, índice em candidatos)

    while True:
        anterior = aceitos[-1]
        vertices = _vertices(ge, s, anterior)
        custo_raiz = 0.0
        for i in range(len(anterior)):
            desvio = vertices[i]
            raiz = anterior[:i]
            desativadas: list[int] = []
            desativados: list[int] = []
            try:
                for caminho in aceitos:
                    if len(caminho) > i and caminho[:i] == raiz:
                        a = caminho[i]
                        if g.aresta_ativa(a):
                            g.desativar_aresta(a)
                            desativadas.append(a)
                for v in vertices[:i]:
                    if g.vertice_ativo(v):
                        g.desativar_vertice(v)
                        desativados.append(v)
                custo_desvio, resto, _ = _buscar(ge, desvio, t, coords, vmax)
            finally:
                for a in desativadas:
                    g.reativar_aresta(a)
                for v in desativados:
                    g.reativar_vertice(v)
            if custo_desvio != INF:
                completo = raiz + resto
                chave = tuple(completo)
                if chave not in vistos:
                    vistos.add(chave)
                    candidatos.append((custo_raiz + custo_desvio, completo))
                    fila.inserir(custo_raiz + custo_desvio, len(candidatos) - 1)
            custo_raiz += g.aresta(anterior[i])[2]
        if fila.vazio():
            return
        _c, indice = fila.extrair_min()
        custo, caminho = candidatos[indice]
        aceitos.append(caminho)
        yield custo, caminho


def trajetos_alternativos(
    ge: VisaoGE,
    origem: str,
    destino: str,
    k: int,
    coords: Sequence[tuple[float, float]] | None = None,
    vmax: float = INF,
) -> list[Trajeto]:
    """Até k trajetos sem ciclo de origem a destino, do mais rápido ao mais lento.

    Entradas:
        ge: G_E de uma faixa horária.
        origem, destino: ids de paradas do GTFS.
        k: número de trajetos pedidos (>= 1).
        coords, vmax: os de `a_estrela.coordenadas_ge` e `a_estrela.velocidade_maxima`;
            com eles os desvios usam A*, sem eles, Dijkstra. O resultado é o mesmo.
    Saída: lista com até k Trajetos, em ordem crescente de tempo total; menos que k se não
        houver mais caminhos sem ciclo; vazia se o destino é inalcançável. Empates de custo
        saem na ordem em que foram encontrados.
    Casos de borda: k < 1 levanta ValueError; parada inexistente levanta KeyError;
        origem == destino devolve só o trajeto vazio; o estado ativo de vértices e arestas
        é restaurado mesmo se a busca levantar exceção.
    Complexidade: tempo O(k · n · (V + E) log V), n = vértices do maior caminho aceito (uma
        busca por ponto de desvio); espaço O(V + E + k · n + C · n), C candidatos guardados.
    """
    if k < 1:
        raise ValueError(f"k deve ser >= 1, recebeu {k}")
    s = ge.vertice_da_parada[origem]
    t = ge.vertice_da_parada[destino]
    return [
        _trajeto(ge, origem, destino, c, caminho)
        for c, caminho in islice(_yen(ge, s, t, coords, vmax), k)
    ]


def sequencia_de_linhas(trajeto: Trajeto, linha_do_padrao: Mapping[str, str]) -> tuple[str, ...]:
    """Linhas dos trechos de ônibus, na ordem; padrão fora do mapa vale pelo próprio id. O(k)."""
    return tuple(
        linha_do_padrao.get(tr.padrao, tr.padrao)
        for tr in trajeto.trechos
        if tr.tipo == ONIBUS and tr.padrao is not None
    )


@dataclass(frozen=True)
class Alternativo:
    """Um trajeto por sequência de linhas, com quantas variantes dela o Yen achou.

    Atributos:
        trajeto: o mais rápido entre os caminhos com essa sequência de linhas.
        linhas: a sequência de `linha_id` dos trechos de ônibus (vazia se só a pé).
        variantes: caminhos do Yen com essa sequência, contando o próprio trajeto, entre os
            aceitos até a busca parar (os outros mudam só onde trocar, o trecho a pé ou o
            padrão da mesma linha).
    """

    trajeto: Trajeto
    linhas: tuple[str, ...]
    variantes: int


def alternativos_por_linhas(
    ge: VisaoGE,
    origem: str,
    destino: str,
    k: int,
    linha_do_padrao: Mapping[str, str],
    coords: Sequence[tuple[float, float]] | None = None,
    vmax: float = INF,
    teto: int | None = None,
) -> list[Alternativo]:
    """Até k trajetos com sequências de linhas distintas, do mais rápido ao mais lento.

    Tira caminhos do Yen em ordem de custo e guarda o primeiro de cada sequência de
    `linha_id` (as seguintes só somam variantes), até ter k sequências distintas ou aceitar
    `teto` caminhos. No feed real, os k primeiros caminhos do Yen costumam ser o mesmo
    trajeto com a troca uma parada antes ou outro trecho a pé; este filtro mostra opções
    que a pessoa reconhece como diferentes.
    Entradas: as de `trajetos_alternativos`, mais `linha_do_padrao` (id do padrão ->
        `linha_id`, como em `rede.padroes`) e `teto` (caminhos do Yen aceitos no máximo;
        padrão 2 · k).
    Saída: lista de Alternativo em ordem crescente de tempo; menos que k se o teto ou os
        caminhos sem ciclo acabarem antes; vazia se o destino é inalcançável.
    Casos de borda: k < 1 ou teto < k levanta ValueError; o estado do grafo é restaurado.
    Complexidade: tempo O(teto · n · (V + E) log V), o do Yen com teto caminhos; espaço o
        do Yen mais O(k) grupos.
    """
    if k < 1:
        raise ValueError(f"k deve ser >= 1, recebeu {k}")
    teto = 2 * k if teto is None else teto
    if teto < k:
        raise ValueError(f"teto deve ser >= k, recebeu {teto} com k = {k}")
    s = ge.vertice_da_parada[origem]
    t = ge.vertice_da_parada[destino]
    grupos: dict[tuple[str, ...], list] = {}  # sequência -> [Trajeto, variantes]
    for c, caminho in islice(_yen(ge, s, t, coords, vmax), teto):
        trajeto = _trajeto(ge, origem, destino, c, caminho)
        linhas = sequencia_de_linhas(trajeto, linha_do_padrao)
        if linhas in grupos:
            grupos[linhas][1] += 1
        elif len(grupos) < k:
            grupos[linhas] = [trajeto, 1]
        if len(grupos) == k:
            break
    return [Alternativo(tr, linhas, n) for linhas, (tr, n) in grupos.items()]
