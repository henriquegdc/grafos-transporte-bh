"""Testes do A* em G_E e da parada mais próxima (F-ROTA-2, RF-ROT-03 e RF-ROT-04).

Redes montadas à mão com os campos de RedeConstrutores e passadas pelo construir_ge de
verdade. Coordenadas perto de BH; 0,001 grau de latitude = 111,19 m. Espera padrão 300 s;
faixa pico_manha (06h a 09h). As redes aleatórias espalham as paradas em duas dimensões,
para a heurística geográfica ter o que podar.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import networkx as nx
import pytest

from transporte.algoritmos.a_estrela import (
    comparar,
    coordenadas_ge,
    dijkstra_contado,
    parada_mais_proxima,
    trajeto_a_estrela,
    velocidade_maxima,
)
from transporte.algoritmos.trajeto import trajeto_mais_rapido
from transporte.grafo.buscas import INF
from transporte.modelo.construtores import _distancia_m, construir_ge
from transporte.modelo.visoes import CAMINHADA, VIAGEM

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


def montar(paradas, padroes, esperas=None):
    """paradas: [(id, milésimos ao norte, milésimos a leste)]; padroes: [(id, seq, tempos)].
    Devolve (rede, ge, coords, vmax)."""
    r = Rede()
    for pid, norte, leste in paradas:
        r.paradas[pid] = Parada(pid, LAT0 + norte / 1000, LON0 + leste / 1000)
    for pid, seq, tempos in padroes:
        horarios = [H7]
        for d in tempos:
            horarios.append(horarios[-1] + d)
        r.padroes[pid] = Padrao(pid, tuple(seq))
        r.viagens[pid] = [horarios]
    ge = construir_ge(r, "pico_manha", esperas=esperas)
    coords = coordenadas_ge(ge, r.paradas)
    return r, ge, coords, velocidade_maxima(ge, coords)


LONGE = [("A", 0, 0), ("B", 10, 0), ("C", 20, 0)]  # 1112 m entre vizinhas, sem caminhada


def test_coordenadas_da_plataforma_sao_as_da_parada():
    _r, ge, coords, _v = montar(LONGE, [("P1", "AB", [100])])
    assert coords[ge.plataforma[("A", "P1")]] == coords[ge.vertice_da_parada["A"]]
    assert coords[ge.vertice_da_parada["B"]] == pytest.approx((LAT0 + 0.01, LON0))


def test_velocidade_maxima_e_a_da_aresta_mais_rapida():
    # P1: 1112 m em 100 s (11,1 m/s); P2: 1112 m em 400 s.
    _r, _ge, _c, vmax = montar(LONGE, [("P1", "AB", [100]), ("P2", "BC", [400])])
    assert vmax == pytest.approx(10 * M_POR_MILESIMO / 100)


def test_velocidade_maxima_sem_arestas_que_andam_e_infinita():
    _r, _ge, _c, vmax = montar([("A", 0, 0), ("B", 10, 0)], [])
    assert vmax == INF


def test_trajeto_igual_ao_do_dijkstra_e_expande_menos():
    # Linha reta A -> B -> C e um ramo D -> E para o outro lado, alcançável de A a pé.
    paradas = [*LONGE, ("D", -1, 0), ("E", -15, 0)]
    padroes = [("P1", "ABC", [100, 100]), ("P2", "DE", [50])]
    _r, ge, coords, vmax = montar(paradas, padroes)
    c = comparar(ge, coords, vmax, "A", "C")
    assert c.a_estrela.trajeto == trajeto_mais_rapido(ge, "A", "C")
    assert c.dijkstra.trajeto == c.a_estrela.trajeto
    assert c.a_estrela.expandidos < c.dijkstra.expandidos
    assert c.a_estrela.tempo_s >= 0 and c.dijkstra.tempo_s >= 0


def test_origem_igual_ao_destino():
    _r, ge, coords, vmax = montar(LONGE, [("P1", "AB", [100])])
    b = trajeto_a_estrela(ge, coords, vmax, "A", "A")
    assert (b.trajeto.tempo_total_s, b.trajeto.trechos, b.expandidos) == (0.0, (), 1)


def test_inalcancavel_e_parada_inexistente():
    _r, ge, coords, vmax = montar(LONGE, [("P1", "AB", [100])])
    assert trajeto_a_estrela(ge, coords, vmax, "B", "A").trajeto is None
    assert dijkstra_contado(ge, "A", "C").trajeto is None
    with pytest.raises(KeyError):
        trajeto_a_estrela(ge, coords, vmax, "A", "X")


def test_respeita_falhas():
    padroes = [("LENTA", "AC", [2000]), ("P2", "AB", [100]), ("P3", "BC", [100])]
    _r, ge, coords, vmax = montar(LONGE, padroes)
    ge.grafo.desativar_vertice(ge.plataforma[("B", "P3")])
    assert trajeto_a_estrela(ge, coords, vmax, "A", "C").trajeto.tempo_total_s == 2300.0
    ge.grafo.desativar_vertice(ge.vertice_da_parada["A"])
    assert trajeto_a_estrela(ge, coords, vmax, "A", "C").trajeto is None


def test_parada_mais_proxima():
    r, *_ = montar(LONGE, [])
    assert parada_mais_proxima(r.paradas, LAT0 + 0.004, LON0) == (
        "A",
        pytest.approx(4 * M_POR_MILESIMO),
    )
    assert parada_mais_proxima(r.paradas, LAT0 + 0.0151, LON0 + 0.001)[0] == "C"
    # Empate exato (duas paradas no mesmo ponto): o menor id.
    r.paradas["A2"] = Parada("A2", LAT0, LON0)
    assert parada_mais_proxima(r.paradas, LAT0 + 0.004, LON0)[0] == "A"
    with pytest.raises(ValueError):
        parada_mais_proxima({}, LAT0, LON0)


# --- Redes aleatórias e NetworkX (só em tests/) -----------------------------------------


def _rede_aleatoria(rnd):
    paradas = [(f"S{i}", rnd.uniform(0, 60), rnd.uniform(0, 60)) for i in range(30)]
    nomes = [p for p, _n, _l in paradas]
    padroes = []
    for k in range(12):
        seq = rnd.sample(nomes, rnd.randint(2, 8))
        padroes.append((f"L{k}", seq, [rnd.randint(1, 20) * 30 for _ in seq[1:]]))
    esperas = {(f"L{k}", "pico_manha"): rnd.randint(2, 30) * 30.0 for k in range(12)}
    return montar(paradas, padroes, esperas), nomes


def _para_networkx(g):
    h = nx.DiGraph()
    h.add_nodes_from(range(g.num_vertices()))
    for a in range(g.num_arestas()):
        u, v, peso, _ = g.aresta(a)
        if not h.has_edge(u, v) or peso < h[u][v]["weight"]:
            h.add_edge(u, v, weight=peso)
    return h


@pytest.mark.parametrize("semente", range(15))
def test_heuristica_consistente(semente):
    (_r, ge, coords, vmax), _nomes = _rede_aleatoria(random.Random(semente))
    g = ge.grafo
    for a in range(g.num_arestas()):
        u, v, peso, tipo = g.aresta(a)
        if tipo in (VIAGEM, CAMINHADA):
            assert _distancia_m(*coords[u], *coords[v]) / vmax <= peso


@pytest.mark.parametrize("semente", range(15))
def test_igual_ao_networkx(semente):
    rnd = random.Random(semente)
    (_r, ge, coords, vmax), nomes = _rede_aleatoria(rnd)
    h = _para_networkx(ge.grafo)
    total_a, total_d = 0, 0
    for _ in range(20):
        o, d = rnd.choice(nomes), rnd.choice(nomes)
        c = comparar(ge, coords, vmax, o, d)
        try:
            esperado = nx.dijkstra_path_length(h, ge.vertice_da_parada[o], ge.vertice_da_parada[d])
        except nx.NetworkXNoPath:
            assert c.a_estrela.trajeto is None and c.dijkstra.trajeto is None
            continue
        assert c.a_estrela.trajeto.tempo_total_s == pytest.approx(esperado)
        assert c.dijkstra.trajeto.tempo_total_s == pytest.approx(esperado)
        assert sum(t.tempo_s for t in c.a_estrela.trajeto.trechos) == pytest.approx(esperado)
        total_a += c.a_estrela.expandidos
        total_d += c.dijkstra.expandidos
    assert total_a <= total_d
