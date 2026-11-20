from __future__ import annotations

import pytest

from transporte.algoritmos.eficiencia import (
    eficiencia_global,
    estimar_eficiencia_global,
    tempo_medio_viagem,
)
from transporte.algoritmos.trajeto import trajeto_mais_rapido
from transporte.grafo.grafo import Grafo
from transporte.modelo.visoes import CAMINHADA, DESEMBARQUE, EMBARQUE, VIAGEM, VisaoGE
from transporte.simulacao.falhas import (
    eficiencia_global as eficiencia_global_provisoria_f_res,
)


def _grafo(
    qtd: int,
    arestas: list[tuple[int, int, float] | tuple[int, int, float, str]],
) -> Grafo:
    g = Grafo()
    for vertice in range(qtd):
        g.adicionar_vertice(str(vertice))
    for aresta in arestas:
        origem, destino, peso = aresta[:3]
        tipo = aresta[3] if len(aresta) == 4 else ""
        g.adicionar_aresta(origem, destino, peso, tipo)
    return g


def _ge_de_teste() -> VisaoGE:
    g = _grafo(
        5,
        [
            (0, 3, 10, EMBARQUE),  # embarque em A
            (3, 4, 100, VIAGEM),  # viagem até B
            (4, 1, 0, DESEMBARQUE),  # plataforma não é uma parada OD
            (1, 2, 20, CAMINHADA),  # caminhada de B a C
        ],
    )
    return VisaoGE(
        grafo=g,
        nome="G_E",
        vertice_da_parada={"A": 0, "B": 1, "C": 2},
        plataforma={("A", "P1"): 3, ("B", "P1"): 4},
        faixa="pico_manha",
    )


def test_eficiencia_global_direcionada_com_gabarito() -> None:
    g = _grafo(3, [(0, 1, 2), (1, 2, 3), (0, 2, 10)])

    # Distâncias: 0->1=2, 0->2=5, 1->2=3; os três caminhos inversos não existem.
    assert eficiencia_global(g) == pytest.approx((1 / 2 + 1 / 5 + 1 / 3) / 6)


def test_pares_inalcancaveis_contribuem_com_zero() -> None:
    assert eficiencia_global(_grafo(2, [(0, 1, 4)])) == pytest.approx(1 / 8)


def test_origens_e_denominador_reproduzem_contrato_da_f_res() -> None:
    g = _grafo(3, [(0, 1, 2), (1, 0, 2), (1, 2, 4), (2, 1, 4)])
    g.desativar_vertice(2)

    assert eficiencia_global(g, n_referencia=3) == pytest.approx(1 / 6)
    assert eficiencia_global(g, origens=[0], n_referencia=3) == pytest.approx(1 / 4)
    assert eficiencia_global(g, origens=[2], n_referencia=3) == 0.0


@pytest.mark.parametrize(
    ("origens", "n_referencia", "erro"),
    [
        ([0, 0], None, ValueError),
        ([2], 1, ValueError),
        ([1.5], None, TypeError),
        ([3], None, IndexError),
    ],
)
def test_eficiencia_global_valida_origens_e_denominador(origens, n_referencia, erro) -> None:
    with pytest.raises(erro):
        eficiencia_global(_grafo(2, [(0, 1, 1)]), origens, n_referencia)


def test_eficiencia_global_rejeita_distancia_zero() -> None:
    with pytest.raises(ValueError, match="distância 0"):
        eficiencia_global(_grafo(2, [(0, 1, 0)]))


def test_eficiencia_nao_deve_usar_todos_os_vertices_de_ge() -> None:
    with pytest.raises(ValueError, match="distância 0"):
        eficiencia_global(_ge_de_teste().grafo)


@pytest.mark.parametrize("semente", range(5))
def test_eficiencia_global_confere_com_networkx(semente: int) -> None:
    import random

    import networkx as nx

    rng = random.Random(semente)
    arestas = [(rng.randrange(6), rng.randrange(6), rng.randint(1, 20)) for _ in range(18)]
    g = _grafo(6, arestas)
    referencia = nx.MultiDiGraph()
    referencia.add_nodes_from(range(6))
    referencia.add_weighted_edges_from(arestas)
    soma = 0.0
    for origem in range(6):
        for destino, distancia in nx.single_source_dijkstra_path_length(referencia, origem).items():
            if origem != destino:
                soma += 1 / distancia

    assert eficiencia_global(g) == pytest.approx(soma / (6 * 5))


def test_eficiencia_global_mantem_compatibilidade_com_a_f_res() -> None:
    g = _grafo(4, [(0, 1, 2), (1, 0, 2), (1, 2, 4), (2, 1, 4)])
    g.desativar_vertice(2)

    assert eficiencia_global(g, n_referencia=4) == pytest.approx(
        eficiencia_global_provisoria_f_res(g, n_referencia=4)
    )
    assert eficiencia_global(g, origens=[0, 2], n_referencia=4) == pytest.approx(
        eficiencia_global_provisoria_f_res(g, origens=[0, 2], n_referencia=4)
    )


def test_estimativa_exata_e_amostrada_reprodutivel() -> None:
    g = _grafo(4, [(0, 1, 1), (1, 0, 2), (2, 3, 3)])
    exata = estimar_eficiencia_global(g)
    amostra_a = estimar_eficiencia_global(g, tamanho_amostra=3, semente=17)
    amostra_b = estimar_eficiencia_global(g, tamanho_amostra=3, semente=17)

    assert exata.valor == pytest.approx(eficiencia_global(g))
    assert exata.erro_padrao == 0.0
    assert amostra_a == amostra_b
    assert amostra_a.tamanho_amostra == 3
    assert amostra_a.tamanho_populacao == 4
    assert amostra_a.erro_padrao is not None


@pytest.mark.parametrize(
    ("tamanho_amostra", "semente", "erro"),
    [
        (0, 0, ValueError),
        (5, 0, ValueError),
        (True, 0, TypeError),
        (1, False, TypeError),
    ],
)
def test_estimativa_global_rejeita_parametros_invalidos(tamanho_amostra, semente, erro) -> None:
    with pytest.raises(erro):
        estimar_eficiencia_global(_grafo(4, []), tamanho_amostra=tamanho_amostra, semente=semente)


def test_tempo_medio_usa_pares_de_paradas_e_omite_inalcancaveis() -> None:
    ge = _ge_de_teste()
    estimativa = tempo_medio_viagem(ge, tamanho_amostra=6, semente=8)

    # A->B=110 s, A->C=130 s, B->C=20 s; os demais pares não têm trajeto.
    assert estimativa.valor == pytest.approx((110 + 130 + 20) / 3)
    caminhos = [
        trajeto_mais_rapido(ge, origem, destino)
        for origem, destino in (("A", "B"), ("A", "C"), ("B", "C"))
    ]
    assert estimativa.valor == pytest.approx(
        sum(caminho.tempo_total_s for caminho in caminhos if caminho is not None) / 3
    )
    assert estimativa.pares_alcancaveis == 3
    assert estimativa.tamanho_amostra == 6
    assert estimativa.tamanho_populacao == 6
    assert estimativa.erro_padrao == 0.0


def test_tempo_medio_amostrado_e_reprodutivel() -> None:
    ge = _ge_de_teste()
    primeira = tempo_medio_viagem(ge, tamanho_amostra=4, semente=23)
    segunda = tempo_medio_viagem(ge, tamanho_amostra=4, semente=23)

    assert primeira == segunda
    assert primeira.tamanho_amostra == 4
    assert primeira.pares_alcancaveis is not None
    assert primeira.erro_padrao is None or primeira.erro_padrao >= 0


@pytest.mark.parametrize(
    ("tamanho_amostra", "semente", "erro"),
    [
        (0, 0, ValueError),
        (7, 0, ValueError),
        (1.5, 0, TypeError),
        (1, False, TypeError),
    ],
)
def test_tempo_medio_rejeita_parametros_invalidos(tamanho_amostra, semente, erro) -> None:
    with pytest.raises(erro):
        tempo_medio_viagem(_ge_de_teste(), tamanho_amostra=tamanho_amostra, semente=semente)
