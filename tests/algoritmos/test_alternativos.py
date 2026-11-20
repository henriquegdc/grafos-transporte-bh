"""Testes dos k trajetos alternativos em G_E pelo Yen (F-ROTA-OPC, RF-ROT-05).

Mesmas redes à mão de test_a_estrela (paradas a 1112 m, sem caminhada, salvo indicação;
espera padrão 300 s). A comparação usa `nx.shortest_simple_paths`, que também lista os
caminhos sem ciclo em ordem crescente de custo.
"""

from __future__ import annotations

import random
from itertools import islice

import networkx as nx
import pytest

# Módulo irmão: sem __init__.py, o pytest põe a pasta de cada teste no sys.path.
from test_a_estrela import LONGE, _para_networkx, _rede_aleatoria, montar

from transporte.algoritmos.alternativos import (
    alternativos_por_linhas,
    sequencia_de_linhas,
    trajetos_alternativos,
)
from transporte.algoritmos.trajeto import ESPERA, trajeto_mais_rapido

PADROES = [("LENTA", "AC", [2000]), ("P2", "AB", [100]), ("P3", "BC", [100])]


def test_lista_do_mais_rapido_ao_mais_lento():
    _r, ge, _c, _v = montar(LONGE, PADROES)
    ts = trajetos_alternativos(ge, "A", "C", 5)
    # Só há dois caminhos sem ciclo: com troca em B (800 s) e a linha lenta (2300 s).
    assert [t.tempo_total_s for t in ts] == [800.0, 2300.0]
    assert ts[0] == trajeto_mais_rapido(ge, "A", "C")
    assert [t.baldeacoes for t in ts] == [1, 0]
    assert [[tr.padrao for tr in t.trechos if tr.tipo == ESPERA] for t in ts] == [
        ["P2", "P3"],
        ["LENTA"],
    ]


def test_k_1_e_o_trajeto_mais_rapido():
    _r, ge, _c, _v = montar(LONGE, PADROES)
    assert trajetos_alternativos(ge, "A", "C", 1) == [trajeto_mais_rapido(ge, "A", "C")]


def test_bordas():
    _r, ge, _c, _v = montar(LONGE, PADROES)
    assert trajetos_alternativos(ge, "C", "A", 3) == []
    (vazio,) = trajetos_alternativos(ge, "A", "A", 3)
    assert (vazio.tempo_total_s, vazio.trechos) == (0.0, ())
    with pytest.raises(ValueError):
        trajetos_alternativos(ge, "A", "C", 0)
    with pytest.raises(KeyError):
        trajetos_alternativos(ge, "A", "X", 2)


def test_restaura_o_estado_e_respeita_falhas_anteriores():
    _r, ge, _c, _v = montar(LONGE, PADROES)
    g = ge.grafo
    lenta = ge.plataforma[("A", "LENTA")]
    g.desativar_vertice(lenta)
    ts = trajetos_alternativos(ge, "A", "C", 5)
    assert [t.tempo_total_s for t in ts] == [800.0]  # a lenta continua fora
    assert not g.vertice_ativo(lenta)
    outros = [v for v in range(g.num_vertices()) if v != lenta]
    assert all(g.vertice_ativo(v) for v in outros)
    assert all(g.aresta_ativa(a) for a in range(g.num_arestas()))


# P2b faz o mesmo A -> B que P2, 50 s mais lento, e é da mesma linha: o 2º caminho do Yen
# (850 s) é uma variante do 1º (800 s), e o 3º (2300 s) é outra linha.
COM_VARIANTE = [*PADROES, ("P2b", "AB", [150])]
LINHAS = {"LENTA": "L-LENTA", "P2": "L2", "P2b": "L2", "P3": "L3"}


def test_yen_puro_devolve_a_variante():
    _r, ge, _c, _v = montar(LONGE, COM_VARIANTE)
    assert [t.tempo_total_s for t in trajetos_alternativos(ge, "A", "C", 2)] == [800.0, 850.0]


def test_por_linhas_pula_variantes_da_mesma_sequencia():
    _r, ge, coords, vmax = montar(LONGE, COM_VARIANTE)
    for args in ((), (coords, vmax)):
        alts = alternativos_por_linhas(ge, "A", "C", 2, LINHAS, *args)
        assert [(a.trajeto.tempo_total_s, a.linhas, a.variantes) for a in alts] == [
            (800.0, ("L2", "L3"), 2),
            (2300.0, ("L-LENTA",), 1),
        ]
        assert alts[0].trajeto == trajeto_mais_rapido(ge, "A", "C")


def test_por_linhas_para_no_teto_e_quando_acabam_os_caminhos():
    _r, ge, _c, _v = montar(LONGE, COM_VARIANTE)
    # Teto de 2 caminhos: só o de 800 s e a variante, uma sequência só.
    (unico,) = alternativos_por_linhas(ge, "A", "C", 2, LINHAS, teto=2)
    assert (unico.linhas, unico.variantes) == (("L2", "L3"), 2)
    # Pedindo 5, acabam os caminhos sem ciclo (3) antes: duas sequências.
    assert len(alternativos_por_linhas(ge, "A", "C", 5, LINHAS)) == 2
    # Sem o mapa de linhas, cada padrão vale como linha: três sequências.
    assert len(alternativos_por_linhas(ge, "A", "C", 5, {})) == 3


def test_por_linhas_bordas_e_estado():
    _r, ge, _c, _v = montar(LONGE, COM_VARIANTE)
    g = ge.grafo
    assert alternativos_por_linhas(ge, "C", "A", 3, LINHAS) == []
    (vazio,) = alternativos_por_linhas(ge, "A", "A", 3, LINHAS)
    assert (vazio.linhas, vazio.variantes, vazio.trajeto.trechos) == ((), 1, ())
    with pytest.raises(ValueError):
        alternativos_por_linhas(ge, "A", "C", 0, LINHAS)
    with pytest.raises(ValueError):
        alternativos_por_linhas(ge, "A", "C", 3, LINHAS, teto=2)
    # Parar no meio do Yen (teto) deixa o grafo como estava.
    alternativos_por_linhas(ge, "A", "C", 2, LINHAS, teto=2)
    assert all(g.vertice_ativo(v) for v in range(g.num_vertices()))
    assert all(g.aresta_ativa(a) for a in range(g.num_arestas()))


def test_sequencia_de_linhas():
    _r, ge, _c, _v = montar(LONGE, COM_VARIANTE)
    t = trajeto_mais_rapido(ge, "A", "C")
    assert sequencia_de_linhas(t, LINHAS) == ("L2", "L3")
    assert sequencia_de_linhas(t, {}) == ("P2", "P3")


@pytest.mark.parametrize("semente", range(10))
def test_igual_ao_networkx(semente):
    rnd = random.Random(semente)
    (_r, ge, coords, vmax), nomes = _rede_aleatoria(rnd)
    h = _para_networkx(ge.grafo)
    for _ in range(5):
        o, d = rnd.choice(nomes), rnd.choice(nomes)
        if o == d:
            continue
        s, t = ge.vertice_da_parada[o], ge.vertice_da_parada[d]
        try:
            caminhos = list(islice(nx.shortest_simple_paths(h, s, t, weight="weight"), 4))
        except nx.NetworkXNoPath:
            assert trajetos_alternativos(ge, o, d, 4) == []
            continue
        esperado = [nx.path_weight(h, c, "weight") for c in caminhos]
        com_a_estrela = trajetos_alternativos(ge, o, d, 4, coords, vmax)
        com_dijkstra = trajetos_alternativos(ge, o, d, 4)
        for ts in (com_a_estrela, com_dijkstra):
            assert [x.tempo_total_s for x in ts] == pytest.approx(esperado)
            assert all(
                sum(tr.tempo_s for tr in x.trechos) == pytest.approx(x.tempo_total_s) for x in ts
            )
