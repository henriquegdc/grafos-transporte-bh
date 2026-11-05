"""Testes de transporte.grafo.buscas (RF-GRF-02).

Gabaritos à mão em grafos pequenos e, para grafos aleatórios com semente fixa e falhas
aleatórias, comparação das distâncias com o NetworkX (só nos testes). Os pesos dos grafos
aleatórios são múltiplos de 1/4, que o float representa sem erro, então as somas podem ser
comparadas com igualdade exata.
"""

from __future__ import annotations

import random

import networkx as nx
import pytest

from transporte.grafo.buscas import (
    INF,
    SEM_PRED,
    Resultado,
    bfs,
    caminho,
    caminho_arestas,
    dijkstra,
)
from transporte.grafo.grafo import Grafo


def novo_grafo(n: int, arestas: list[tuple[int, int, float]]) -> Grafo:
    g = Grafo()
    for u in range(n):
        g.adicionar_vertice(str(u))
    for u, v, p in arestas:
        g.adicionar_aresta(u, v, p)
    return g


@pytest.fixture
def g() -> Grafo:
    """Grafo dos gabaritos à mão (ids das arestas entre colchetes).

        0 -[0] 4-> 1 -[2] 1-> 3 -[4] 3-> 4
        0 -[1] 1-> 2 -[3] 2-> 1
                   2 -[5] 8-> 3
        5 (isolado)

    Dijkstra a partir de 0: dist = [0, 3, 1, 4, 7, INF], via 0 -> 2 -> 1 -> 3 -> 4.
    BFS a partir de 0: dist = [0, 1, 1, 2, 3, INF], via 0 -> 1 -> 3 -> 4.
    """
    return novo_grafo(
        6, [(0, 1, 4), (0, 2, 1), (1, 3, 1), (2, 1, 2), (3, 4, 3), (2, 3, 8)]
    )


# --- Dijkstra: gabarito à mão ---------------------------------------------------------


def test_dijkstra_gabarito(g):
    r = dijkstra(g, 0)
    assert isinstance(r, Resultado)
    assert r.origem == 0
    assert r.dist == [0.0, 3.0, 1.0, 4.0, 7.0, INF]
    assert r.pred == [SEM_PRED, 2, 0, 1, 3, SEM_PRED]
    assert r.pred_aresta == [SEM_PRED, 3, 1, 2, 4, SEM_PRED]
    assert caminho(r, 4) == [0, 2, 1, 3, 4]
    assert caminho_arestas(r, 4) == [1, 3, 2, 4]


def test_caminho_ate_a_origem_e_inalcancavel(g):
    r = dijkstra(g, 0)
    assert caminho(r, 0) == [0]
    assert caminho_arestas(r, 0) == []
    assert caminho(r, 5) == []
    assert caminho_arestas(r, 5) == []


def test_dijkstra_aresta_paralela_escolhe_a_mais_barata():
    g = novo_grafo(2, [(0, 1, 5), (0, 1, 2), (0, 1, 7)])
    r = dijkstra(g, 0)
    assert r.dist[1] == 2.0
    assert caminho_arestas(r, 1) == [1]


def test_dijkstra_laco_e_peso_zero():
    g = novo_grafo(3, [(0, 0, 0), (0, 1, 0), (1, 2, 0), (1, 1, 3)])
    r = dijkstra(g, 0)
    assert r.dist == [0.0, 0.0, 0.0]
    assert caminho(r, 2) == [0, 1, 2]


def test_dijkstra_com_destino_para_cedo_mas_acerta_o_destino(g):
    r = dijkstra(g, 0, destino=1)
    assert r.dist[1] == 3.0
    assert caminho(r, 1) == [0, 2, 1]
    # O vértice 4 ainda não foi alcançado quando a busca parou.
    assert r.dist[4] == INF


def test_dijkstra_destino_inalcancavel_percorre_tudo(g):
    r = dijkstra(g, 0, destino=5)
    assert r.dist[5] == INF
    assert r.dist[:5] == [0.0, 3.0, 1.0, 4.0, 7.0]


def test_dijkstra_origem_igual_ao_destino(g):
    r = dijkstra(g, 3, destino=3)
    assert r.dist[3] == 0.0
    assert caminho(r, 3) == [3]


# --- desativação (RF-GRF-03 visto pelas buscas) ---------------------------------------


def test_dijkstra_desvia_de_aresta_desativada(g):
    g.desativar_aresta(3)  # 2 -> 1
    r = dijkstra(g, 0)
    assert r.dist == [0.0, 4.0, 1.0, 5.0, 8.0, INF]
    assert caminho(r, 4) == [0, 1, 3, 4]


def test_dijkstra_desvia_de_vertice_desativado(g):
    g.desativar_vertice(1)
    r = dijkstra(g, 0)
    assert r.dist == [0.0, INF, 1.0, 9.0, 12.0, INF]
    assert caminho(r, 4) == [0, 2, 3, 4]
    assert caminho_arestas(r, 4) == [1, 5, 4]


def test_reativar_restaura_o_resultado(g):
    antes = dijkstra(g, 0)
    g.desativar_vertice(1)
    g.desativar_aresta(5)
    g.reativar_tudo()
    assert dijkstra(g, 0) == antes


@pytest.mark.parametrize("busca", [bfs, dijkstra])
def test_origem_desativada_nao_alcanca_nada(g, busca):
    g.desativar_vertice(0)
    r = busca(g, 0)
    assert r.dist == [INF] * 6
    assert caminho(r, 0) == []


@pytest.mark.parametrize("busca", [bfs, dijkstra])
@pytest.mark.parametrize("origem", [6, -1])
def test_origem_inexistente_levanta_index_error(g, busca, origem):
    with pytest.raises(IndexError):
        busca(g, origem)


@pytest.mark.parametrize("destino", [6, -1])
def test_destino_inexistente_levanta_index_error(g, destino):
    with pytest.raises(IndexError):
        dijkstra(g, 0, destino)


def test_grafo_com_um_vertice():
    g = novo_grafo(1, [])
    assert dijkstra(g, 0).dist == [0.0]
    assert bfs(g, 0).dist == [0.0]


# --- BFS: gabarito à mão --------------------------------------------------------------


def test_bfs_gabarito_ignora_pesos(g):
    r = bfs(g, 0)
    assert r.dist == [0.0, 1.0, 1.0, 2.0, 3.0, INF]
    assert caminho(r, 4) == [0, 1, 3, 4]
    assert caminho_arestas(r, 4) == [0, 2, 4]


def test_bfs_desvia_de_aresta_desativada(g):
    g.desativar_aresta(2)  # 1 -> 3
    r = bfs(g, 0)
    assert r.dist[3] == 2.0
    assert caminho(r, 3) == [0, 2, 3]


# --- reverso: distância "até" um destino ----------------------------------------------


def test_dijkstra_no_reverso_da_distancia_ate_o_destino(g):
    r = dijkstra(g.reverso(), 4)
    # dist[u] = custo de u até 4 no grafo original.
    assert r.dist == [7.0, 4.0, 6.0, 3.0, 0.0, INF]
    # Os ids de aresta valem no original: o caminho 4 <- 3 <- 1 <- 2 <- 0 lido ao contrário.
    assert caminho_arestas(r, 0) == [4, 2, 3, 1]


# --- comparação com o NetworkX --------------------------------------------------------


def grafo_aleatorio(semente: int) -> tuple[Grafo, nx.MultiDiGraph]:
    """Mesmo grafo aleatório nas duas estruturas, com falhas aleatórias.

    No NetworkX a falha é a remoção do vértice ou da aresta.
    """
    rng = random.Random(semente)
    n = rng.randint(1, 60)
    m = rng.randint(0, 4 * n)
    g = Grafo()
    ref = nx.MultiDiGraph()
    for u in range(n):
        g.adicionar_vertice(str(u))
        ref.add_node(u)
    for _ in range(m):
        u, v, p = rng.randrange(n), rng.randrange(n), rng.randint(0, 40) / 4
        a = g.adicionar_aresta(u, v, p)
        ref.add_edge(u, v, key=a, weight=p)
    for a in rng.sample(range(m), k=m // 6):
        g.desativar_aresta(a)
        u, v, _, _ = g.aresta(a)
        ref.remove_edge(u, v, key=a)
    for u in rng.sample(range(n), k=n // 8):
        g.desativar_vertice(u)
        ref.remove_node(u)
    return g, ref


def conferir_caminhos(g: Grafo, r: Resultado, peso_unitario: bool) -> None:
    """Todo caminho reconstruído é válido no grafo e custa exatamente dist[v]."""
    for v in range(g.num_vertices()):
        vertices = caminho(r, v)
        arestas = caminho_arestas(r, v)
        if r.dist[v] == INF:
            assert vertices == [] and arestas == []
            continue
        assert vertices[0] == r.origem and vertices[-1] == v
        assert len(arestas) == len(vertices) - 1
        custo = 0.0
        for i, a in enumerate(arestas):
            u, w, peso, _ = g.aresta(a)
            assert (u, w) == (vertices[i], vertices[i + 1])
            assert g.aresta_ativa(a) and g.vertice_ativo(u) and g.vertice_ativo(w)
            custo += 1 if peso_unitario else peso
        assert custo == r.dist[v]


@pytest.mark.parametrize("semente", range(25))
def test_dijkstra_igual_ao_networkx(semente):
    g, ref = grafo_aleatorio(semente)
    for origem in range(g.num_vertices()):
        r = dijkstra(g, origem)
        esperado = (
            nx.single_source_dijkstra_path_length(ref, origem, weight="weight")
            if origem in ref
            else {}
        )
        assert {v: d for v, d in enumerate(r.dist) if d != INF} == esperado
        conferir_caminhos(g, r, peso_unitario=False)


@pytest.mark.parametrize("semente", range(25))
def test_bfs_igual_ao_networkx(semente):
    g, ref = grafo_aleatorio(semente)
    for origem in range(g.num_vertices()):
        r = bfs(g, origem)
        esperado = (
            nx.single_source_shortest_path_length(ref, origem) if origem in ref else {}
        )
        assert {v: d for v, d in enumerate(r.dist) if d != INF} == esperado
        conferir_caminhos(g, r, peso_unitario=True)


@pytest.mark.parametrize("semente", range(10))
def test_dijkstra_com_destino_igual_ao_completo(semente):
    g, _ = grafo_aleatorio(semente)
    rng = random.Random(1000 + semente)
    n = g.num_vertices()
    for _ in range(20):
        origem, destino = rng.randrange(n), rng.randrange(n)
        completo = dijkstra(g, origem)
        parcial = dijkstra(g, origem, destino)
        assert parcial.dist[destino] == completo.dist[destino]
        vertices = caminho(parcial, destino)
        custo = sum(g.aresta(a)[2] for a in caminho_arestas(parcial, destino))
        assert (vertices == []) == (completo.dist[destino] == INF)
        if vertices:
            assert custo == completo.dist[destino]


@pytest.mark.parametrize("semente", range(10))
def test_dijkstra_no_reverso_igual_ao_networkx(semente):
    g, ref = grafo_aleatorio(semente)
    ref_r = ref.reverse(copy=True)
    r = g.reverso()
    for destino in range(g.num_vertices()):
        res = dijkstra(r, destino)
        esperado = (
            nx.single_source_dijkstra_path_length(ref_r, destino, weight="weight")
            if destino in ref_r
            else {}
        )
        assert {v: d for v, d in enumerate(res.dist) if d != INF} == esperado
