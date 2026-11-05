"""Testes de transporte.grafo.grafo (RF-GRF-01, RF-GRF-03).

Gabaritos à mão num grafo pequeno e, para grafos aleatórios com semente fixa, comparação
das arestas utilizáveis com o subgrafo equivalente montado no NetworkX (só nos testes).
"""

from __future__ import annotations

import math
import random

import networkx as nx
import pytest

from transporte.grafo.grafo import Grafo


@pytest.fixture
def g() -> Grafo:
    """Grafo pequeno usado nos gabaritos à mão.

    0 --a0(2.0, viagem)--> 1 --a2(1.5)--> 2
    0 --a1(4.0, caminhada)-----------------^
    1 --a3(3.0)--> 1   (laço)
    1 --a4(9.0)--> 2   (paralela a a2)
    3                   (isolado)
    """
    g = Grafo()
    for rotulo in ["A", "B", "C", "D"]:
        g.adicionar_vertice(rotulo)
    g.adicionar_aresta(0, 1, 2.0, "viagem")
    g.adicionar_aresta(0, 2, 4.0, "caminhada")
    g.adicionar_aresta(1, 2, 1.5)
    g.adicionar_aresta(1, 1, 3.0)
    g.adicionar_aresta(1, 2, 9)
    return g


# --- construção e consulta ------------------------------------------------------------


def test_grafo_vazio():
    g = Grafo()
    assert g.num_vertices() == 0
    assert g.num_arestas() == 0


def test_ids_sequenciais():
    g = Grafo()
    assert [g.adicionar_vertice(r) for r in "xyz"] == [0, 1, 2]
    assert g.adicionar_aresta(0, 1, 1.0) == 0
    assert g.adicionar_aresta(1, 2, 1.0) == 1


def test_contagens_e_rotulos(g):
    assert g.num_vertices() == 4
    assert g.num_arestas() == 5
    assert [g.rotulo(u) for u in range(4)] == ["A", "B", "C", "D"]


def test_aresta_devolve_dados(g):
    assert g.aresta(0) == (0, 1, 2.0, "viagem")
    assert g.aresta(1) == (0, 2, 4.0, "caminhada")
    assert g.aresta(2) == (1, 2, 1.5, "")


def test_peso_inteiro_vira_float(g):
    _, _, peso, _ = g.aresta(4)
    assert peso == 9.0
    assert isinstance(peso, float)


def test_vizinhos_em_ordem_de_insercao_com_laco_e_paralela(g):
    assert g.vizinhos(0) == [(1, 2.0, 0), (2, 4.0, 1)]
    assert g.vizinhos(1) == [(2, 1.5, 2), (1, 3.0, 3), (2, 9.0, 4)]
    assert g.vizinhos(2) == []
    assert g.vizinhos(3) == []


def test_peso_zero_aceito():
    g = Grafo()
    g.adicionar_vertice("a")
    g.adicionar_vertice("b")
    g.adicionar_aresta(0, 1, 0)
    assert g.vizinhos(0) == [(1, 0.0, 0)]


@pytest.mark.parametrize("peso", [-1.0, -1e-9, math.inf, -math.inf, math.nan])
def test_peso_invalido_levanta_value_error(g, peso):
    with pytest.raises(ValueError):
        g.adicionar_aresta(0, 1, peso)
    assert g.num_arestas() == 5  # nada foi gravado


@pytest.mark.parametrize(("u", "v"), [(4, 0), (0, 4), (-1, 0), (0, -1)])
def test_aresta_com_vertice_inexistente_levanta_index_error(g, u, v):
    with pytest.raises(IndexError):
        g.adicionar_aresta(u, v, 1.0)
    assert g.num_arestas() == 5


@pytest.mark.parametrize(
    "chamada",
    [
        lambda g: g.vizinhos(4),
        lambda g: g.vizinhos(-1),
        lambda g: g.rotulo(4),
        lambda g: g.vertice_ativo(-1),
        lambda g: g.desativar_vertice(4),
        lambda g: g.reativar_vertice(4),
        lambda g: g.aresta(5),
        lambda g: g.aresta(-1),
        lambda g: g.aresta_ativa(5),
        lambda g: g.desativar_aresta(5),
        lambda g: g.reativar_aresta(-1),
    ],
)
def test_ids_inexistentes_levantam_index_error(g, chamada):
    with pytest.raises(IndexError):
        chamada(g)


# --- desativação e reativação (RF-GRF-03) ---------------------------------------------


def test_desativar_aresta(g):
    g.desativar_aresta(2)
    assert not g.aresta_ativa(2)
    assert g.vizinhos(1) == [(1, 3.0, 3), (2, 9.0, 4)]
    # Os dados continuam lá e os ids não mudam.
    assert g.aresta(2) == (1, 2, 1.5, "")
    assert g.num_arestas() == 5


def test_desativar_vertice_esconde_saidas_e_entradas(g):
    g.desativar_vertice(1)
    assert not g.vertice_ativo(1)
    assert g.vizinhos(1) == []  # saídas de 1
    assert g.vizinhos(0) == [(2, 4.0, 1)]  # a0 entra em 1
    # As arestas em si continuam ativas (decisão G5): voltam ao reativar o vértice.
    assert g.aresta_ativa(0)
    assert g.num_vertices() == 4


def test_reativar_vertice_volta_ao_estado_anterior(g):
    antes = [g.vizinhos(u) for u in range(4)]
    g.desativar_vertice(1)
    g.reativar_vertice(1)
    assert [g.vizinhos(u) for u in range(4)] == antes


def test_reativar_vertice_nao_reativa_aresta_desativada_a_parte(g):
    g.desativar_aresta(2)
    g.desativar_vertice(1)
    g.reativar_vertice(1)
    assert g.vizinhos(1) == [(1, 3.0, 3), (2, 9.0, 4)]


def test_desativar_e_reativar_sao_idempotentes(g):
    g.desativar_aresta(0)
    g.desativar_aresta(0)
    g.desativar_vertice(2)
    g.desativar_vertice(2)
    assert g.vizinhos(0) == []
    g.reativar_aresta(0)
    g.reativar_aresta(0)
    g.reativar_vertice(2)
    g.reativar_vertice(2)
    assert g.vizinhos(0) == [(1, 2.0, 0), (2, 4.0, 1)]


def test_reativar_tudo(g):
    antes = [g.vizinhos(u) for u in range(4)]
    g.desativar_vertice(0)
    g.desativar_vertice(3)
    g.desativar_aresta(2)
    g.desativar_aresta(4)
    g.reativar_tudo()
    assert all(g.vertice_ativo(u) for u in range(4))
    assert all(g.aresta_ativa(a) for a in range(5))
    assert [g.vizinhos(u) for u in range(4)] == antes


def test_adicionar_depois_de_desativar(g):
    g.desativar_vertice(3)
    v = g.adicionar_vertice("E")
    a = g.adicionar_aresta(v, 3, 1.0)
    assert (v, a) == (4, 5)
    assert g.vizinhos(v) == []  # destino 3 está inativo
    g.reativar_tudo()
    assert g.vizinhos(v) == [(3, 1.0, 5)]


# --- reverso --------------------------------------------------------------------------


def test_reverso_inverte_mantendo_ids(g):
    r = g.reverso()
    assert r.num_vertices() == 4
    assert r.num_arestas() == 5
    assert [r.rotulo(u) for u in range(4)] == ["A", "B", "C", "D"]
    assert r.aresta(0) == (1, 0, 2.0, "viagem")
    assert r.aresta(1) == (2, 0, 4.0, "caminhada")
    assert r.vizinhos(0) == []
    assert r.vizinhos(1) == [(0, 2.0, 0), (1, 3.0, 3)]
    assert r.vizinhos(2) == [(0, 4.0, 1), (1, 1.5, 2), (1, 9.0, 4)]


def test_reverso_mantem_estado_e_e_independente(g):
    g.desativar_aresta(2)
    g.desativar_vertice(3)
    r = g.reverso()
    assert not r.aresta_ativa(2)
    assert not r.vertice_ativo(3)
    r.reativar_tudo()
    r.desativar_vertice(0)
    assert not g.aresta_ativa(2)  # o original não mudou
    assert g.vertice_ativo(0)
    assert g.vizinhos(0) == [(1, 2.0, 0), (2, 4.0, 1)]


def test_reverso_do_reverso_igual_ao_original(g):
    rr = g.reverso().reverso()
    for u in range(g.num_vertices()):
        assert rr.vizinhos(u) == g.vizinhos(u)
    for a in range(g.num_arestas()):
        assert rr.aresta(a) == g.aresta(a)


# --- comparação com o NetworkX --------------------------------------------------------


def grafo_aleatorio(semente: int) -> tuple[Grafo, nx.MultiDiGraph]:
    """Mesmo grafo aleatório nas duas estruturas, com falhas aleatórias aplicadas.

    No NetworkX a falha é simulada removendo o vértice ou a aresta, que é o que a
    desativação do núcleo deve equivaler para as buscas.
    """
    rng = random.Random(semente)
    n = rng.randint(1, 40)
    m = rng.randint(0, 150)
    g = Grafo()
    ref = nx.MultiDiGraph()
    for u in range(n):
        g.adicionar_vertice(str(u))
        ref.add_node(u)
    for _ in range(m):
        u, v, p = rng.randrange(n), rng.randrange(n), rng.randint(0, 20) / 4
        a = g.adicionar_aresta(u, v, p)
        ref.add_edge(u, v, key=a, weight=p)
    for a in rng.sample(range(m), k=m // 5):
        g.desativar_aresta(a)
        u, v, _, _ = g.aresta(a)
        ref.remove_edge(u, v, key=a)
    for u in rng.sample(range(n), k=n // 6):
        g.desativar_vertice(u)
        ref.remove_node(u)
    return g, ref


@pytest.mark.parametrize("semente", range(15))
def test_arestas_utilizaveis_iguais_ao_networkx(semente):
    g, ref = grafo_aleatorio(semente)
    for u in range(g.num_vertices()):
        nossas = sorted(g.vizinhos(u), key=lambda t: t[2])
        if u not in ref:
            assert nossas == []
            continue
        esperadas = sorted(
            (
                (v, d["weight"], a)
                for _, v, a, d in ref.out_edges(u, keys=True, data=True)
            ),
            key=lambda t: t[2],
        )
        assert nossas == esperadas


@pytest.mark.parametrize("semente", range(5))
def test_reverso_igual_ao_reverse_do_networkx(semente):
    g, ref = grafo_aleatorio(semente)
    r = g.reverso()
    ref_r = ref.reverse(copy=True)
    for u in range(r.num_vertices()):
        if u not in ref_r:
            assert r.vizinhos(u) == []
            continue
        esperadas = sorted((v, a) for _, v, a in ref_r.out_edges(u, keys=True))
        assert sorted((v, a) for v, _, a in r.vizinhos(u)) == esperadas
