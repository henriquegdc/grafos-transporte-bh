"""Testes de transporte.algoritmos.comunidades (F-MET-OPC: RF-MET-06).

Gabaritos com cliques (a partição certa é óbvia) e modularidade comparada com
nx.community.modularity para a mesma partição, em grafos aleatórios com semente fixa
(NetworkX só nos testes).
"""

from __future__ import annotations

import random

import networkx as nx
import pytest

from transporte.algoritmos.comunidades import (
    SEM_COMUNIDADE,
    Comunidades,
    modularidade,
    propagar_rotulos,
    vizinhanca_nao_dirigida,
)
from transporte.grafo.grafo import Grafo


def novo_grafo(n: int, arestas: list[tuple[int, int]]) -> Grafo:
    g = Grafo()
    for u in range(n):
        g.adicionar_vertice(str(u))
    for u, v in arestas:
        g.adicionar_aresta(u, v, 1.0)
    return g


def cliques(tamanhos: list[int], pontes: list[tuple[int, int]] = ()) -> Grafo:
    """Cliques dirigidos (as duas direções) de vértices consecutivos, mais pontes u -> v."""
    arestas: list[tuple[int, int]] = []
    inicio = 0
    for t in tamanhos:
        membros = range(inicio, inicio + t)
        arestas += [(u, v) for u in membros for v in membros if u != v]
        inicio += t
    return novo_grafo(inicio, arestas + list(pontes))


def grupos(c: Comunidades) -> set[frozenset[int]]:
    por_rotulo: dict[int, set[int]] = {}
    for v, r in enumerate(c.rotulos):
        if r != SEM_COMUNIDADE:
            por_rotulo.setdefault(r, set()).add(v)
    return {frozenset(s) for s in por_rotulo.values()}


def como_networkx(g: Grafo) -> nx.Graph:
    """Grafo não dirigido simples com os vértices ativos (mesma regra do módulo)."""
    ref = nx.Graph()
    ref.add_nodes_from(v for v in range(g.num_vertices()) if g.vertice_ativo(v))
    for u in range(g.num_vertices()):
        for v, _p, _a in g.vizinhos(u):
            if u != v:
                ref.add_edge(u, v)
    return ref


# --- propagação de rótulos ------------------------------------------------------------


@pytest.mark.parametrize("semente", range(5))
def test_cliques_disjuntos_sao_as_comunidades(semente):
    c = propagar_rotulos(cliques([4, 5, 3]), semente=semente)
    assert grupos(c) == {frozenset(range(4)), frozenset(range(4, 9)), frozenset(range(9, 12))}
    assert c.quantidade == 3 and c.convergiu
    assert c.rotulos == [0] * 4 + [1] * 5 + [2] * 3  # renumeradas pelo menor vértice
    assert c.tamanhos() == [4, 5, 3]


@pytest.mark.parametrize("semente", range(5))
def test_cliques_ligados_por_uma_aresta_ficam_separados(semente):
    # K5 e K5 com uma ponte 4 -> 5: cada ponta da ponte tem 4 vizinhos no próprio clique e
    # 1 no outro, então nenhum rótulo atravessa.
    c = propagar_rotulos(cliques([5, 5], [(4, 5)]), semente=semente)
    assert grupos(c) == {frozenset(range(5)), frozenset(range(5, 10))}


def test_mesma_semente_mesmo_resultado():
    rng = random.Random(1)
    g = novo_grafo(40, [(rng.randrange(40), rng.randrange(40)) for _ in range(90)])
    assert propagar_rotulos(g, semente=3) == propagar_rotulos(g, semente=3)


def test_vertice_isolado_e_desativado():
    g = cliques([3], [])
    g.adicionar_vertice("isolado")  # 3
    g.adicionar_vertice("desligado")  # 4
    g.adicionar_aresta(4, 0, 1.0)
    g.desativar_vertice(4)
    c = propagar_rotulos(g)
    assert c.rotulos == [0, 0, 0, 1, SEM_COMUNIDADE]
    assert c.quantidade == 2


def test_bordas():
    vazio = propagar_rotulos(Grafo())
    assert vazio.quantidade == 0 and vazio.rotulos == [] and vazio.convergiu
    with pytest.raises(ValueError):
        propagar_rotulos(Grafo(), max_iter=0)


def test_max_iter_interrompe_sem_convergir():
    # Um caminho longo precisa de várias iterações; com 1 não dá para concluir que parou.
    g = novo_grafo(30, [(i, i + 1) for i in range(29)])
    c = propagar_rotulos(g, semente=0, max_iter=1)
    assert c.iteracoes == 1 and not c.convergiu


def test_vizinhanca_ignora_sentido_lacos_e_paralelas():
    g = novo_grafo(3, [(0, 1), (0, 1), (1, 0), (2, 2), (2, 1)])
    assert vizinhanca_nao_dirigida(g) == [[1], [0, 2], [1]]


# --- modularidade ---------------------------------------------------------------------


def test_modularidade_gabarito_dois_triangulos_com_ponte():
    # Dois triângulos 0-1-2 e 3-4-5 ligados por 2-3: m = 7, cada lado tem 3 arestas
    # internas e soma de graus 7. Q = 2 (3/7 - (7/14)^2) = 6/7 - 1/2.
    g = novo_grafo(6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (2, 3)])
    assert modularidade(g, [0, 0, 0, 1, 1, 1]) == pytest.approx(6 / 7 - 1 / 2)
    assert modularidade(g, [0] * 6) == pytest.approx(0.0)  # uma comunidade só: Q = 0


def test_modularidade_bordas():
    assert modularidade(novo_grafo(3, []), [0, 1, 2]) == 0.0
    with pytest.raises(ValueError):
        modularidade(novo_grafo(3, []), [0, 1])


@pytest.mark.parametrize("semente", range(15))
def test_modularidade_igual_ao_networkx(semente):
    rng = random.Random(semente)
    n = rng.randint(2, 40)
    g = novo_grafo(n, [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(1, 4 * n))])
    for v in rng.sample(range(n), k=n // 8):
        g.desativar_vertice(v)
    ref = como_networkx(g)
    for particao in (propagar_rotulos(g, semente=semente).rotulos,
                     [rng.randrange(4) if g.vertice_ativo(v) else SEM_COMUNIDADE
                      for v in range(n)]):
        conjuntos: dict[int, set[int]] = {}
        for v, r in enumerate(particao):
            if r != SEM_COMUNIDADE:
                conjuntos.setdefault(r, set()).add(v)
        if ref.number_of_edges() == 0:
            assert modularidade(g, particao) == 0.0
            continue
        esperado = nx.community.modularity(ref, list(conjuntos.values()))
        assert modularidade(g, particao) == pytest.approx(esperado, abs=1e-12)


@pytest.mark.parametrize("semente", range(5))
def test_rotulos_encontram_modularidade_alta_em_cliques_com_ponte(semente):
    g = cliques([6, 6, 6], [(5, 6), (11, 12)])
    c = propagar_rotulos(g, semente=semente)
    assert c.quantidade == 3
    assert modularidade(g, c.rotulos) > 0.5
