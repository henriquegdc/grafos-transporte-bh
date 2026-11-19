"""A* com heurística geográfica em G_E e parada mais próxima de um ponto (F-ROTA-2).

RF-ROT-03: `parada_mais_proxima` liga um ponto (clique no mapa ou coordenadas) à parada
mais próxima em linha reta.
RF-ROT-04: `trajeto_a_estrela` calcula o trajeto com A* e `comparar` mede, contra o
Dijkstra, os vértices expandidos e o tempo de cada um.

A heurística. h(v) = distância em linha reta de v ao destino / velocidade máxima da rede.
A velocidade máxima é a maior razão distância / peso entre as arestas de G_E que mudam de
lugar (viagem e caminhada); embarque e desembarque não mudam de lugar. Então, para toda
aresta u -> v, w(u, v) >= d(u, v) / vmax, e pela desigualdade triangular
h(u) <= d(u, v) / vmax + h(v) <= w(u, v) + h(v): a heurística é consistente, logo
admissível, e o A* devolve o mesmo custo do Dijkstra.

A comparação. Dijkstra e A* rodam pela mesma busca (`_buscar`), com o HeapMin do núcleo e
contando cada vértice expandido; o Dijkstra é o caso h = 0. Assim a diferença medida vem só
da heurística, não de detalhes de implementação. O Dijkstra contado devolve as mesmas
distâncias do `grafo.buscas.dijkstra` (há teste para isso).

estado: implementado
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING

from transporte.algoritmos.trajeto import Trajeto, _trechos
from transporte.grafo.buscas import INF, SEM_PRED
from transporte.grafo.heap import HeapMin
from transporte.modelo.construtores import _distancia_m
from transporte.modelo.visoes import CAMINHADA, VIAGEM, VisaoGE

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from transporte.interface.protocolos import ParadaUI

Coordenadas = list[tuple[float, float]]
"""Coordenadas (lat, lon) de cada vértice de G_E; a plataforma usa as da sua parada."""

_FOLGA = 1e-9
"""Folga relativa na velocidade máxima e no teste de entrada desatualizada, contra erro de
ponto flutuante (sem ela, h poderia passar do custo real por 1 ulp)."""


@dataclass(frozen=True)
class Busca:
    """Resultado de uma busca contada.

    Atributos:
        trajeto: o trajeto encontrado, ou None se o destino é inalcançável.
        expandidos: vértices tirados do heap e expandidos (sem as entradas desatualizadas).
        tempo_s: tempo de relógio da busca e da reconstrução, em segundos.
    """

    trajeto: Trajeto | None
    expandidos: int
    tempo_s: float


@dataclass(frozen=True)
class Comparacao:
    """Dijkstra e A* na mesma consulta (RF-ROT-04)."""

    dijkstra: Busca
    a_estrela: Busca


def coordenadas_ge(ge: VisaoGE, paradas: Mapping[str, ParadaUI]) -> Coordenadas:
    """Coordenadas de cada vértice de G_E, a partir das paradas da rede.

    Entradas: G_E e o mapa id da parada -> parada (com lat e lon), como `rede.paradas`.
    Saída: lista indexada pelo vértice.
    Casos de borda: parada de G_E ausente em `paradas` levanta KeyError.
    Complexidade: tempo e espaço O(V).
    """
    coords: Coordenadas = [(0.0, 0.0)] * ge.grafo.num_vertices()
    for parada_id, v in ge.vertice_da_parada.items():
        p = paradas[parada_id]
        coords[v] = (float(p.lat), float(p.lon))
    for (parada_id, _padrao), v in ge.plataforma.items():
        p = paradas[parada_id]
        coords[v] = (float(p.lat), float(p.lon))
    return coords


def velocidade_maxima(ge: VisaoGE, coords: Sequence[tuple[float, float]]) -> float:
    """Maior distância / peso (m/s) entre as arestas de viagem e caminhada de G_E.

    É o denominador da heurística; com ele nenhuma aresta anda mais rápido que vmax, o que
    torna h consistente (ver o topo do módulo). Uma folga relativa de 1e-9 cobre o
    arredondamento.
    Casos de borda: G_E sem aresta que mude de lugar devolve INF (h vira 0 e o A* se
    comporta como o Dijkstra).
    Complexidade: tempo O(E); espaço O(1).
    """
    g = ge.grafo
    vmax = 0.0
    for a in range(g.num_arestas()):
        u, v, peso, tipo = g.aresta(a)
        if tipo not in (VIAGEM, CAMINHADA):
            continue
        d = _distancia_m(*coords[u], *coords[v])
        if d == 0:
            continue
        if peso <= 0:
            return INF
        vmax = max(vmax, d / peso)
    return INF if vmax == 0 else vmax * (1 + _FOLGA)


def _buscar(
    ge: VisaoGE,
    s: int,
    t: int,
    coords: Sequence[tuple[float, float]] | None,
    vmax: float,
) -> tuple[float, list[int], int]:
    """Busca de melhor primeiro de s a t, com f = g + h; h = 0 sem coordenadas (Dijkstra).

    Inserção preguiçosa, como o Dijkstra do núcleo: uma entrada é desatualizada quando o
    seu g já foi melhorado; ela é descartada sem contar como expansão. Para ao extrair t.
    Respeita vértices e arestas desativados (só percorre Grafo.vizinhos).
    Saída: (custo, ids das arestas do caminho, vértices expandidos); custo INF e caminho
        vazio se t é inalcançável.
    Complexidade: tempo O((V + E) log V) no pior caso; espaço O(V + E).
    """
    g = ge.grafo
    n = g.num_vertices()
    dist = [INF] * n
    pred = [SEM_PRED] * n
    pred_aresta = [SEM_PRED] * n
    h = [-1.0] * n  # calculado na primeira vez que o vértice aparece
    usar_h = coords is not None and vmax != INF
    alvo = coords[t] if usar_h else (0.0, 0.0)

    def heuristica(v: int) -> float:
        if h[v] < 0:
            h[v] = _distancia_m(*coords[v], *alvo) / vmax if usar_h else 0.0
        return h[v]

    expandidos = 0
    if not g.vertice_ativo(s):
        return INF, [], 0
    dist[s] = 0.0
    heap = HeapMin()
    heap.inserir(heuristica(s), s)
    while not heap.vazio():
        f, u = heap.extrair_min()
        if f - h[u] > dist[u] * (1 + _FOLGA) + _FOLGA:
            continue  # entrada desatualizada
        expandidos += 1
        if u == t:
            break
        du = dist[u]
        for v, peso, a in g.vizinhos(u):
            nova = du + peso
            if nova < dist[v]:
                dist[v] = nova
                pred[v] = u
                pred_aresta[v] = a
                heap.inserir(nova + heuristica(v), v)
    if dist[t] == INF:
        return INF, [], expandidos
    arestas = []
    v = t
    while v != s:
        arestas.append(pred_aresta[v])
        v = pred[v]
    arestas.reverse()
    return dist[t], arestas, expandidos


def _trajeto(ge: VisaoGE, origem: str, destino: str, custo: float, arestas: list[int]) -> Trajeto:
    return Trajeto(
        origem=origem,
        destino=destino,
        tempo_total_s=custo,
        baldeacoes=ge.baldeacoes(arestas),
        trechos=tuple(_trechos(ge, arestas)),
    )


def _busca_contada(
    ge: VisaoGE,
    origem: str,
    destino: str,
    coords: Sequence[tuple[float, float]] | None,
    vmax: float,
) -> Busca:
    s = ge.vertice_da_parada[origem]
    t = ge.vertice_da_parada[destino]
    inicio = perf_counter()
    custo, arestas, expandidos = _buscar(ge, s, t, coords, vmax)
    trajeto = None if custo == INF else _trajeto(ge, origem, destino, custo, arestas)
    return Busca(trajeto, expandidos, perf_counter() - inicio)


def trajeto_a_estrela(
    ge: VisaoGE,
    coords: Sequence[tuple[float, float]],
    vmax: float,
    origem: str,
    destino: str,
) -> Busca:
    """Trajeto mais rápido de origem a destino em G_E pelo A* (RF-ROT-04).

    Entradas:
        ge: G_E de uma faixa horária.
        coords: `coordenadas_ge(ge, rede.paradas)`.
        vmax: `velocidade_maxima(ge, coords)`; um valor menor torna h inadmissível e o
            trajeto pode deixar de ser o ótimo.
        origem, destino: ids de paradas do GTFS.
    Saída: Busca com o Trajeto (o mesmo custo de `trajeto_mais_rapido`; com empates, o
        caminho pode ser outro de mesmo custo), os vértices expandidos e o tempo.
    Casos de borda: origem == destino devolve tempo 0, nenhum trecho e 1 expandido;
        parada inexistente levanta KeyError; inalcançável devolve trajeto None.
    Complexidade: tempo O((V + E) log V) no pior caso, como o Dijkstra; na prática expande
        menos vértices, porque a heurística afasta a busca do lado oposto ao destino.
        Espaço O(V + E).
    """
    return _busca_contada(ge, origem, destino, coords, vmax)


def dijkstra_contado(ge: VisaoGE, origem: str, destino: str) -> Busca:
    """O Dijkstra pela mesma busca do A* (h = 0), para a comparação de RF-ROT-04.

    Mesmos casos de borda e complexidade de `trajeto_a_estrela`.
    """
    return _busca_contada(ge, origem, destino, None, INF)


def comparar(
    ge: VisaoGE,
    coords: Sequence[tuple[float, float]],
    vmax: float,
    origem: str,
    destino: str,
) -> Comparacao:
    """Roda Dijkstra e A* na mesma consulta. Tempo: a soma dos dois."""
    return Comparacao(
        dijkstra=dijkstra_contado(ge, origem, destino),
        a_estrela=trajeto_a_estrela(ge, coords, vmax, origem, destino),
    )


def parada_mais_proxima(
    paradas: Mapping[str, ParadaUI], lat: float, lon: float
) -> tuple[str, float]:
    """Parada mais próxima do ponto (lat, lon) em linha reta (RF-ROT-03).

    Entradas: mapa id -> parada (com lat e lon), como `rede.paradas`; o ponto em graus.
    Saída: (id da parada, distância em metros). Empate: o menor id.
    Casos de borda: sem paradas levanta ValueError.
    Complexidade: tempo O(V), uma varredura com haversine (9.659 paradas no feed real:
        poucos milissegundos por clique, então uma grade espacial não se paga); espaço O(1).
    """
    melhor: tuple[float, str] | None = None
    for parada_id, p in paradas.items():
        candidato = (_distancia_m(lat, lon, float(p.lat), float(p.lon)), parada_id)
        if melhor is None or candidato < melhor:
            melhor = candidato
    if melhor is None:
        raise ValueError("a rede não tem paradas")
    return melhor[1], melhor[0]
