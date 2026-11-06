"""Testes do trajeto mais rápido em G_E (F-ROTA, RF-ROT-01).

As redes são montadas à mão com os campos de RedeConstrutores (a Rede de P0-DADOS ainda
não existe) e passam pelo construir_ge de verdade. Coordenadas perto de BH; 0,001 grau de
latitude = 111,19 m. Espera padrão 300 s; faixa pico_manha (06h a 09h).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import networkx as nx
import pytest

from transporte.algoritmos.trajeto import (
    A_PE,
    ESPERA,
    ONIBUS,
    Trecho,
    trajeto_mais_rapido,
)
from transporte.modelo.construtores import construir_ge

LAT0, LON0 = -19.92, -43.94
M_POR_MILESIMO = 6_371_000.0 * math.pi / 180 * 0.001  # 111,19 m
H7 = 7 * 3600


@dataclass
class Parada:
    id: str
    lat: float
    lon: float


@dataclass
class Padrao:
    id: str
    paradas: tuple[str, ...]


@dataclass
class Rede:
    paradas: dict[str, Parada] = field(default_factory=dict)
    padroes: dict[str, Padrao] = field(default_factory=dict)
    viagens: dict[str, list[list[int]]] = field(default_factory=dict)


def ge(paradas, padroes, esperas=None):
    """paradas: [(id, milésimos de grau ao norte)]; padroes: [(id, seq, tempos)], com
    tempos = durações entre paradas seguidas de uma viagem que parte às 07h."""
    r = Rede()
    for pid, norte in paradas:
        r.paradas[pid] = Parada(pid, LAT0 + norte / 1000, LON0)
    for pid, seq, tempos in padroes:
        horarios = [H7]
        for d in tempos:
            horarios.append(horarios[-1] + d)
        r.padroes[pid] = Padrao(pid, tuple(seq))
        r.viagens[pid] = [horarios]
    return construir_ge(r, "pico_manha", esperas=esperas)


# Paradas a 1112 m umas das outras (sem caminhada), salvo indicação.
LONGE = [("A", 0), ("B", 10), ("C", 20)]


def test_linha_direta():
    v = ge(LONGE, [("P1", "ABC", [100, 200])])
    t = trajeto_mais_rapido(v, "A", "C")
    assert t.tempo_total_s == 600.0  # 300 de espera + 100 + 200
    assert t.baldeacoes == 0
    assert t.trechos == (
        Trecho(ESPERA, ("A",), 300.0, "P1"),
        Trecho(ONIBUS, ("A", "B", "C"), 300.0, "P1"),
    )
    assert t.tempo_por_tipo() == {A_PE: 0.0, ESPERA: 300.0, ONIBUS: 300.0}


def test_uma_baldeacao():
    v = ge(LONGE, [("P1", "AB", [100]), ("P2", "BC", [50])])
    t = trajeto_mais_rapido(v, "A", "C")
    assert t.tempo_total_s == 750.0  # 300 + 100 + 0 (desembarque) + 300 + 50
    assert t.baldeacoes == 1
    assert t.trechos == (
        Trecho(ESPERA, ("A",), 300.0, "P1"),
        Trecho(ONIBUS, ("A", "B"), 100.0, "P1"),
        Trecho(ESPERA, ("B",), 300.0, "P2"),
        Trecho(ONIBUS, ("B", "C"), 50.0, "P2"),
    )


def test_baldeacao_vence_linha_direta_lenta():
    # Direta: 300 + 2000 = 2300. Com troca: 300 + 100 + 300 + 100 = 800.
    padroes = [("LENTA", "AC", [2000]), ("P2", "AB", [100]), ("P3", "BC", [100])]
    t = trajeto_mais_rapido(ge(LONGE, padroes), "A", "C")
    assert (t.tempo_total_s, t.baldeacoes) == (800.0, 1)


def test_espera_longa_faz_preferir_a_linha_direta():
    # Espera de 1800 s (intervalo regular de 1 h) nas linhas da troca.
    # Direta: 300 + 2000 = 2300. Com troca: 1800 + 100 + 1800 + 100 = 3800.
    padroes = [("LENTA", "AC", [2000]), ("P2", "AB", [100]), ("P3", "BC", [100])]
    esperas = {("P2", "pico_manha"): 1800.0, ("P3", "pico_manha"): 1800.0}
    t = trajeto_mais_rapido(ge(LONGE, padroes, esperas), "A", "C")
    assert (t.tempo_total_s, t.baldeacoes) == (2300.0, 0)
    assert [tr.padrao for tr in t.trechos] == ["LENTA", "LENTA"]


def test_so_a_pe():
    v = ge([("A", 0), ("D", 1)], [])
    t = trajeto_mais_rapido(v, "A", "D")
    assert t.tempo_total_s == pytest.approx(M_POR_MILESIMO / 1.2)
    assert t.baldeacoes == 0
    assert len(t.trechos) == 1
    assert t.trechos[0].tipo == A_PE
    assert t.trechos[0].paradas == ("A", "D")
    assert t.trechos[0].padrao is None


def test_caminhadas_seguidas_viram_um_trecho():
    # A, B e E a 278 m em linha: A-B e B-E dentro do raio, A-E (556 m) fora.
    v = ge([("A", 0), ("B", 2.5), ("E", 5)], [])
    t = trajeto_mais_rapido(v, "A", "E")
    perna = 2.5 * M_POR_MILESIMO / 1.2
    assert t.tempo_total_s == pytest.approx(2 * perna)
    assert len(t.trechos) == 1
    assert t.trechos[0].paradas == ("A", "B", "E")
    assert t.trechos[0].tempo_s == pytest.approx(2 * perna)


def test_a_pe_ate_a_linha_e_a_pe_no_fim():
    # W perto de A, Z perto de C; a linha vai de A a C.
    paradas = [("W", -1), ("A", 0), ("C", 20), ("Z", 21)]
    t = trajeto_mais_rapido(ge(paradas, [("P1", "AC", [500])]), "W", "Z")
    perna = M_POR_MILESIMO / 1.2
    assert [tr.tipo for tr in t.trechos] == [A_PE, ESPERA, ONIBUS, A_PE]
    assert t.trechos[0].paradas == ("W", "A")
    assert t.trechos[3].paradas == ("C", "Z")
    assert t.tempo_total_s == pytest.approx(2 * perna + 300 + 500)
    assert t.baldeacoes == 0


def test_origem_igual_ao_destino():
    t = trajeto_mais_rapido(ge(LONGE, [("P1", "AB", [100])]), "A", "A")
    assert (t.tempo_total_s, t.baldeacoes, t.trechos) == (0.0, 0, ())


def test_destino_inalcancavel():
    # Só existe A -> B; de B não se volta para A.
    v = ge(LONGE, [("P1", "AB", [100])])
    assert trajeto_mais_rapido(v, "B", "A") is None
    assert trajeto_mais_rapido(v, "A", "C") is None


def test_parada_inexistente():
    v = ge(LONGE, [("P1", "AB", [100])])
    with pytest.raises(KeyError):
        trajeto_mais_rapido(v, "A", "X")
    with pytest.raises(KeyError):
        trajeto_mais_rapido(v, "X", "A")


def test_respeita_falhas():
    # Sem a linha rápida (vértice da plataforma desativado), sobra a lenta.
    padroes = [("LENTA", "AC", [2000]), ("P2", "AB", [100]), ("P3", "BC", [100])]
    v = ge(LONGE, padroes)
    v.grafo.desativar_vertice(v.plataforma[("B", "P3")])
    t = trajeto_mais_rapido(v, "A", "C")
    assert (t.tempo_total_s, t.baldeacoes) == (2300.0, 0)
    v.grafo.reativar_tudo()
    assert trajeto_mais_rapido(v, "A", "C").tempo_total_s == 800.0


# --- Comparação com o NetworkX (só em tests/) ------------------------------------------


def _para_networkx(g):
    h = nx.DiGraph()
    h.add_nodes_from(range(g.num_vertices()))
    for a in range(g.num_arestas()):
        u, v, peso, _ = g.aresta(a)
        if g.aresta_ativa(a) and (not h.has_edge(u, v) or peso < h[u][v]["weight"]):
            h.add_edge(u, v, weight=peso)
    return h


def _rede_aleatoria(rnd):
    paradas = [(f"S{i}", rnd.uniform(0, 100)) for i in range(25)]  # 11 km
    nomes = [p for p, _ in paradas]
    padroes = []
    for k in range(12):
        seq = rnd.sample(nomes, rnd.randint(2, 8))
        padroes.append((f"L{k}", seq, [rnd.randint(1, 20) * 30 for _ in seq[1:]]))
    # Esperas de 1 a 15 min (metade de intervalos de 2 a 30 min).
    esperas = {(f"L{k}", "pico_manha"): rnd.randint(2, 30) * 30.0 for k in range(12)}
    return ge(paradas, padroes, esperas), nomes


@pytest.mark.parametrize("semente", range(15))
def test_igual_ao_networkx(semente):
    rnd = random.Random(semente)
    v, nomes = _rede_aleatoria(rnd)
    h = _para_networkx(v.grafo)
    for _ in range(20):
        o, d = rnd.choice(nomes), rnd.choice(nomes)
        t = trajeto_mais_rapido(v, o, d)
        try:
            esperado = nx.dijkstra_path_length(
                h, v.vertice_da_parada[o], v.vertice_da_parada[d]
            )
        except nx.NetworkXNoPath:
            assert t is None
            continue
        assert t.tempo_total_s == pytest.approx(esperado)
        # Os trechos somam o total, e as baldeações batem com as esperas.
        assert sum(tr.tempo_s for tr in t.trechos) == pytest.approx(esperado)
        esperas = sum(1 for tr in t.trechos if tr.tipo == ESPERA)
        assert t.baldeacoes == max(0, esperas - 1)
        # Trechos encadeados: cada um começa onde o anterior terminou.
        for antes, depois in zip(t.trechos, t.trechos[1:], strict=False):
            assert depois.paradas[0] == antes.paradas[-1]
