"""Testes do gerador de redes sintéticas (RF-DAD-05, F-AVAL-OPC)."""

from __future__ import annotations

from itertools import pairwise

import networkx as nx
import pytest

from transporte.dados.sinteticas import LADOS_PADRAO, gerar_rede_sintetica, redes_crescentes
from transporte.modelo.construtores import construir_ge, construir_gp
from transporte.modelo.visoes import CAMINHADA, VIAGEM


def test_gabarito_grade_2x2() -> None:
    # 2x2: 4 paradas, linhas F0, F1, C0, C1 com ida e volta; cada padrão tem 1 trecho.
    rede = gerar_rede_sintetica(2, semente=7, deslocamento_m=0.0)
    assert sorted(rede.paradas) == ["S0_0", "S0_1", "S1_0", "S1_1"]
    assert sorted(rede.linhas) == ["C0", "C1", "F0", "F1"]
    assert len(rede.padroes) == 8
    assert rede.padroes["F0-ida"].paradas == ("S0_0", "S0_1")
    assert rede.padroes["F0-volta"].paradas == ("S0_1", "S0_0")
    assert len(rede.viagens_por_id) == 8 * 4
    g = construir_gp(rede).grafo
    tipos = [g.aresta(a)[3] for a in range(g.num_arestas())]
    # Viagem: 4 linhas x 2 sentidos = 8 arestas. Caminhada: 4 retas (200 m) e 2 diagonais
    # (283 m) dentro do raio de 300 m, nos dois sentidos = 12.
    assert tipos.count(VIAGEM) == 8
    assert tipos.count(CAMINHADA) == 12


def test_viagens_respeitam_faixas_e_ordem() -> None:
    rede = gerar_rede_sintetica(5, semente=3, trecho_min_s=90, trecho_max_s=120)
    for padrao_id, viagens in rede.viagens.items():
        assert len(viagens) == 4
        n = len(rede.padroes[padrao_id].paradas)
        for horarios in viagens:
            assert len(horarios) == n
            difs = [b - a for a, b in pairwise(horarios)]
            assert all(90 <= d <= 120 for d in difs)
        partidas = [h[0] for h in viagens]
        assert partidas == sorted(partidas)
    for (padrao_id, parada_id), horarios in rede.partidas.items():
        assert parada_id in rede.padroes[padrao_id].paradas
        assert horarios == sorted(horarios)


def test_mesma_semente_mesma_rede_e_semente_diferente_muda() -> None:
    a = gerar_rede_sintetica(6, semente=11)
    b = gerar_rede_sintetica(6, semente=11)
    c = gerar_rede_sintetica(6, semente=12)
    assert a.paradas == b.paradas and a.viagens == b.viagens
    assert a.viagens != c.viagens


@pytest.mark.parametrize("lado", [1, 3, 8])
def test_passa_pelos_construtores_e_e_fortemente_conexa(lado: int) -> None:
    rede = gerar_rede_sintetica(lado, semente=lado)
    gp = construir_gp(rede).grafo
    ge = construir_ge(rede, "pico_manha").grafo
    assert gp.num_vertices() == lado * lado
    # Linhas nos dois sentidos e caminhada simétrica: tudo alcança tudo.
    ref = nx.DiGraph()
    ref.add_nodes_from(range(gp.num_vertices()))
    ref.add_edges_from((gp.aresta(a)[0], gp.aresta(a)[1]) for a in range(gp.num_arestas()))
    assert nx.is_strongly_connected(ref)
    # G_E: uma plataforma por (parada, padrão); com lado >= 2 cada parada está em 4 padrões.
    assert ge.num_vertices() == lado * lado * (5 if lado >= 2 else 1)


def test_tamanho_cresce_com_o_lado() -> None:
    redes = redes_crescentes((3, 6, 9), semente=1)
    tamanhos = [construir_gp(r).grafo.num_arestas() for _, r in redes]
    assert [lado for lado, _ in redes] == [3, 6, 9]
    assert tamanhos == sorted(tamanhos) and len(set(tamanhos)) == 3
    assert LADOS_PADRAO == tuple(sorted(LADOS_PADRAO))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"lado": 0},
        {"lado": 3, "viagens_por_padrao": 0},
        {"lado": 3, "espacamento_m": 0},
        {"lado": 3, "deslocamento_m": -1},
        {"lado": 3, "trecho_min_s": 200, "trecho_max_s": 100},
        {"lado": 3, "intervalo_min_s": 0},
    ],
)
def test_parametros_invalidos(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        gerar_rede_sintetica(**kwargs)
