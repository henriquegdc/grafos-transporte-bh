"""Testes de transporte.algoritmos.centralidade (F-MET: RF-MET-01, 02 e 03).

Gabaritos à mão em grafos pequenos e, para grafos aleatórios com semente fixa e falhas
aleatórias, comparação com o NetworkX (só nos testes). No NetworkX a falha é a remoção do
vértice ou da aresta.
"""

from __future__ import annotations

import random

import networkx as nx
import pytest

from transporte.algoritmos.centralidade import (
    Graus,
    distribuicao_graus,
    graus,
    intermediacao,
    ranking,
)
from transporte.grafo.grafo import Grafo


def novo_grafo(n: int, arestas: list[tuple]) -> Grafo:
    """Arestas como (u, v, peso) ou (u, v, peso, tipo)."""
    g = Grafo()
    for u in range(n):
        g.adicionar_vertice(str(u))
    for aresta in arestas:
        g.adicionar_aresta(*aresta)
    return g


@pytest.fixture
def g() -> Grafo:
    """Grafo dos gabaritos à mão, todos os pesos 1 (ids das arestas entre colchetes).

        0 -[0]-> 1 -[1]-> 2 -[4]-> 4
        0 -[2]-> 3 -[3]-> 2

    Caminhos mínimos que passam por vértices intermediários:
        (0, 2): 0-1-2 e 0-3-2      -> 1 e 3 ganham 1/2 cada
        (0, 4): 0-1-2-4 e 0-3-2-4  -> 1 e 3 ganham 1/2 cada; 2 ganha 1
        (1, 4): 1-2-4              -> 2 ganha 1
        (3, 4): 3-2-4              -> 2 ganha 1
    Intermediação: [0, 1, 3, 1, 0].
    """
    return novo_grafo(5, [(0, 1, 1), (1, 2, 1), (0, 3, 1), (3, 2, 1), (2, 4, 1)])


# --- graus e distribuição (RF-MET-01) -------------------------------------------------


def test_graus_gabarito(g):
    r = graus(g)
    assert isinstance(r, Graus)
    assert r.entrada == [0, 1, 2, 1, 1]
    assert r.saida == [2, 1, 1, 1, 0]


def test_graus_paralelas_e_laco():
    # Decisão M1: paralelas contam uma vez cada; laço conta 1 na entrada e 1 na saída.
    g = novo_grafo(2, [(0, 1, 1), (0, 1, 2), (1, 1, 1)])
    r = graus(g)
    assert r.saida == [2, 1]
    assert r.entrada == [0, 3]


def test_graus_filtrados_por_tipo():
    g = novo_grafo(
        3,
        [
            (0, 1, 60, "viagem"),
            (1, 0, 90, "caminhada"),
            (0, 2, 30, "caminhada"),
            (1, 2, 50, "viagem"),
        ],
    )
    so_viagem = graus(g, tipos={"viagem"})
    assert so_viagem.saida == [1, 1, 0]
    assert so_viagem.entrada == [0, 1, 1]
    todos = graus(g)
    assert todos.saida == [2, 2, 0]
    assert graus(g, tipos=[]).saida == [0, 0, 0]


def test_graus_respeitam_desativacao(g):
    g.desativar_vertice(2)
    g.desativar_aresta(0)
    r = graus(g)
    assert r.saida == [1, 0, 0, 0, 0]  # só 0 -> 3 sobra
    assert r.entrada == [0, 0, 0, 1, 0]


def test_graus_grafo_vazio():
    r = graus(Grafo())
    assert r.entrada == [] and r.saida == []


def test_distribuicao_gabarito(g):
    r = graus(g)
    assert distribuicao_graus(g, r.entrada) == {0: 1, 1: 3, 2: 1}
    assert distribuicao_graus(g, r.saida) == {0: 1, 1: 3, 2: 1}
    assert list(distribuicao_graus(g, [5, 0, 5, 2, 0])) == [0, 2, 5]  # ordem crescente


def test_distribuicao_ignora_vertices_desativados(g):
    g.desativar_vertice(0)
    assert distribuicao_graus(g, graus(g).saida) == {0: 1, 1: 3}


def test_distribuicao_tamanho_errado_levanta_value_error(g):
    with pytest.raises(ValueError):
        distribuicao_graus(g, [1, 2])


# --- intermediação (RF-MET-02) --------------------------------------------------------


@pytest.mark.parametrize("ponderado", [True, False])
def test_intermediacao_gabarito(g, ponderado):
    assert intermediacao(g, ponderado=ponderado) == [0.0, 1.0, 3.0, 1.0, 0.0]


def test_intermediacao_pesos_mudam_os_caminhos():
    # Mesmo grafo, mas 3 -> 2 custa 5: o caminho por 3 deixa de ser mínimo com pesos.
    #   (0, 2) e (0, 4) passam só por 1; (1, 4) e (3, 4) passam por 2.
    g = novo_grafo(5, [(0, 1, 1), (1, 2, 1), (0, 3, 1), (3, 2, 5), (2, 4, 1)])
    assert intermediacao(g, ponderado=True) == [0.0, 2.0, 3.0, 0.0, 0.0]
    assert intermediacao(g, ponderado=False) == [0.0, 1.0, 3.0, 1.0, 0.0]


def test_intermediacao_normalizada(g):
    # n = 5 vértices ativos: divide por (5 - 1)(5 - 2) = 12.
    assert intermediacao(g, normalizar=True) == pytest.approx(
        [0, 1 / 12, 3 / 12, 1 / 12, 0]
    )


def test_intermediacao_respeita_vertice_desativado(g):
    # Sem o 1: (0, 2) e (0, 4) só passam por 3; (0, 4) e (3, 4) passam por 2.
    g.desativar_vertice(1)
    assert intermediacao(g) == [0.0, 0.0, 2.0, 2.0, 0.0]
    g.reativar_vertice(1)
    assert intermediacao(g) == [0.0, 1.0, 3.0, 1.0, 0.0]


def test_intermediacao_normalizada_usa_so_vertices_ativos(g):
    # Com 4 ativos, o divisor é (4 - 1)(4 - 2) = 6.
    g.desativar_vertice(1)
    assert intermediacao(g, normalizar=True) == pytest.approx([0, 0, 2 / 6, 2 / 6, 0])


def test_intermediacao_paralelas_contam_como_uma_ligacao():
    # Decisão M3: 0 -> 1 duplicada. Por vértices, (0, 3) tem 2 caminhos (por 1 e por 2),
    # então cada um ganha 1/2. Contando arestas paralelas daria 2/3 e 1/3.
    g = novo_grafo(4, [(0, 1, 1), (0, 1, 1), (1, 3, 1), (0, 2, 1), (2, 3, 1)])
    assert intermediacao(g) == [0.0, 0.5, 0.5, 0.0]


def test_intermediacao_paralela_usa_o_menor_peso():
    # 0 -> 1 com pesos 5 e 1: pelo menor, 0-1-2 custa 2 < 3 da aresta direta.
    g = novo_grafo(3, [(0, 1, 5), (0, 1, 1), (1, 2, 1), (0, 2, 3)])
    assert intermediacao(g) == [0.0, 1.0, 0.0]


def test_intermediacao_peso_zero_levanta_value_error():
    # Decisão M2: peso 0 só é recusado no modo ponderado e fora de laços.
    g = novo_grafo(3, [(0, 1, 0), (1, 2, 1)])
    with pytest.raises(ValueError):
        intermediacao(g, ponderado=True)
    assert intermediacao(g, ponderado=False) == [0.0, 1.0, 0.0]


def test_intermediacao_laco_de_peso_zero_e_ignorado():
    g = novo_grafo(3, [(0, 1, 1), (1, 1, 0), (1, 2, 1)])
    assert intermediacao(g) == [0.0, 1.0, 0.0]


def test_intermediacao_peso_zero_em_aresta_desativada_nao_conta():
    g = novo_grafo(3, [(0, 1, 0), (0, 1, 2), (1, 2, 1)])
    g.desativar_aresta(0)
    assert intermediacao(g) == [0.0, 1.0, 0.0]


def test_intermediacao_grafos_triviais():
    assert intermediacao(Grafo()) == []
    assert intermediacao(novo_grafo(1, [])) == [0.0]
    assert intermediacao(novo_grafo(2, [(0, 1, 1), (1, 0, 1)]), normalizar=True) == [
        0.0,
        0.0,
    ]


def test_intermediacao_ciclo_dirigido():
    # Ciclo 0 -> 1 -> 2 -> 0: cada vértice é o único intermediário de exatamente um par.
    g = novo_grafo(3, [(0, 1, 1), (1, 2, 1), (2, 0, 1)])
    assert intermediacao(g) == [1.0, 1.0, 1.0]


# --- ranking (RF-MET-03) --------------------------------------------------------------


def test_ranking_gabarito(g):
    bc = intermediacao(g)
    assert ranking(g, bc, 3) == [(2, 3.0), (1, 1.0), (3, 1.0)]  # empate 1 x 3: menor id


def test_ranking_k_grande_e_k_zero(g):
    bc = intermediacao(g)
    assert ranking(g, bc, 100) == [(2, 3.0), (1, 1.0), (3, 1.0), (0, 0.0), (4, 0.0)]
    assert ranking(g, bc, 0) == []
    assert ranking(g, bc, -1) == []


def test_ranking_ignora_vertices_desativados(g):
    valores = [9.0, 1.0, 3.0, 1.0, 0.0]
    g.desativar_vertice(0)
    assert ranking(g, valores, 2) == [(2, 3.0), (1, 1.0)]


def test_ranking_tamanho_errado_levanta_value_error(g):
    with pytest.raises(ValueError):
        ranking(g, [1.0], 1)


# --- comparação com o NetworkX --------------------------------------------------------


def grafo_aleatorio(semente: int, peso_min: int = 1) -> tuple[Grafo, nx.MultiDiGraph]:
    """Mesmo grafo aleatório nas duas estruturas, com falhas aleatórias.

    Pesos múltiplos de 1/4 (somas exatas no float), o que gera muitos empates de
    distância: é o caso que testa a contagem de caminhos mínimos do Brandes. Inclui
    arestas paralelas e laços.
    """
    rng = random.Random(semente)
    n = rng.randint(1, 35)
    m = rng.randint(0, 4 * n)
    g = Grafo()
    ref = nx.MultiDiGraph()
    for u in range(n):
        g.adicionar_vertice(str(u))
        ref.add_node(u)
    for _ in range(m):
        u, v, p = rng.randrange(n), rng.randrange(n), rng.randint(peso_min, 12) / 4
        tipo = rng.choice(["viagem", "caminhada"])
        a = g.adicionar_aresta(u, v, p, tipo)
        ref.add_edge(u, v, key=a, weight=p, tipo=tipo)
    for a in rng.sample(range(m), k=m // 6):
        g.desativar_aresta(a)
        u, v, _, _ = g.aresta(a)
        ref.remove_edge(u, v, key=a)
    for u in rng.sample(range(n), k=n // 8):
        g.desativar_vertice(u)
        ref.remove_node(u)
    return g, ref


def como_lista(g: Grafo, ref_valores: dict, padrao=0) -> list:
    return [ref_valores.get(v, padrao) for v in range(g.num_vertices())]


@pytest.mark.parametrize("semente", range(30))
def test_graus_iguais_ao_networkx(semente):
    g, ref = grafo_aleatorio(semente)
    r = graus(g)
    assert r.entrada == como_lista(g, dict(ref.in_degree()))
    assert r.saida == como_lista(g, dict(ref.out_degree()))


@pytest.mark.parametrize("semente", range(10))
def test_graus_por_tipo_iguais_ao_networkx(semente):
    g, ref = grafo_aleatorio(semente)
    so_viagem = nx.MultiDiGraph()
    so_viagem.add_nodes_from(ref.nodes)
    so_viagem.add_edges_from(
        (u, v, k, d)
        for u, v, k, d in ref.edges(keys=True, data=True)
        if d["tipo"] == "viagem"
    )
    r = graus(g, tipos={"viagem"})
    assert r.entrada == como_lista(g, dict(so_viagem.in_degree()))
    assert r.saida == como_lista(g, dict(so_viagem.out_degree()))


@pytest.mark.parametrize("semente", range(30))
@pytest.mark.parametrize("ponderado", [True, False])
@pytest.mark.parametrize("normalizar", [False, True])
def test_intermediacao_igual_ao_networkx(semente, ponderado, normalizar):
    g, ref = grafo_aleatorio(semente)
    esperado = nx.betweenness_centrality(
        ref, normalized=normalizar, weight="weight" if ponderado else None
    )
    obtido = intermediacao(g, ponderado=ponderado, normalizar=normalizar)
    assert obtido == pytest.approx(como_lista(g, esperado, 0.0), abs=1e-9)


@pytest.mark.parametrize("semente", range(5))
def test_intermediacao_com_peso_zero_so_aceita_sem_pesos(semente):
    g, ref = grafo_aleatorio(semente + 100, peso_min=0)
    tem_zero = any(
        p == 0 and u != v for u in range(g.num_vertices()) for v, p, _ in g.vizinhos(u)
    )
    if tem_zero:
        with pytest.raises(ValueError):
            intermediacao(g, ponderado=True)
    esperado = nx.betweenness_centrality(ref, normalized=False, weight=None)
    assert intermediacao(g, ponderado=False) == pytest.approx(
        como_lista(g, esperado, 0.0), abs=1e-9
    )
