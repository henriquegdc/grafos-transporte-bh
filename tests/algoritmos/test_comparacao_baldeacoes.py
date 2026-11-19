"""Testes de menos baldeações contra mais rápido (F-BALD-2, RF-BAL-03).

As redes são montadas à mão com os campos de RedeConstrutores e passam pelos construtores
de verdade: o mesmo objeto gera o G_E (construir_ge) e a G_L (construir_gl), na faixa
pico_manha. Coordenadas perto de BH; 0,001 grau de latitude = 111,19 m; paradas a 10
milésimos (1,1 km) não têm caminhada entre si. Espera padrão 300 s, salvo indicação.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import networkx as nx
import pytest

from transporte.algoritmos.baldeacoes import menos_baldeacoes
from transporte.algoritmos.comparacao_baldeacoes import (
    ComparacaoBaldeacoes,
    comparar_baldeacoes,
    mais_rapido_com_limite,
)
from transporte.algoritmos.trajeto import A_PE, ESPERA, ONIBUS, Trecho, trajeto_mais_rapido
from transporte.modelo.construtores import construir_ge
from transporte.modelo.linhas import construir_gl
from transporte.modelo.visoes import EMBARQUE, VIAGEM

LAT0, LON0 = -19.92, -43.94
M_POR_MILESIMO = 6_371_000.0 * math.pi / 180 * 0.001  # 111,19 m
H7 = 7 * 3600
FAIXA = "pico_manha"


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


def _rede(paradas, padroes) -> Rede:
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
    return r


def visoes(paradas, padroes, esperas=None):
    r = _rede(paradas, padroes)
    return construir_ge(r, FAIXA, esperas=esperas), construir_gl(r, faixa=FAIXA)


LONGE3 = [("A", 0), ("B", 10), ("C", 20)]
LONGE4 = [("A", 0), ("B", 10), ("C", 20), ("D", 30)]


# --- Gabaritos à mão --------------------------------------------------------------------


def test_linha_direta_lenta_contra_baldeacao_rapida():
    # Mais rápido: P2 + P3 = 300 + 100 + 300 + 100 = 800 s, 1 baldeação.
    # Menos baldeações: LENTA direta = 300 + 2000 = 2300 s, 0 baldeação.
    ge, gl = visoes(LONGE3, [("LENTA", "AC", [2000]), ("P2", "AB", [100]), ("P3", "BC", [100])])
    c = comparar_baldeacoes(ge, gl, "A", "C")
    assert (c.mais_rapido.tempo_total_s, c.mais_rapido.baldeacoes) == (800.0, 1)
    assert c.menos_baldeacoes.baldeacoes == 0
    assert c.rapido_com_menos_baldeacoes.tempo_total_s == 2300.0
    assert c.rapido_com_menos_baldeacoes.trechos == (
        Trecho(ESPERA, ("A",), 300.0, "LENTA"),
        Trecho(ONIBUS, ("A", "C"), 2000.0, "LENTA"),
    )
    assert c.tempo_a_mais_s == 1500.0
    assert c.baldeacoes_evitadas == 1
    assert c.tempo_por_baldeacao_evitada_s == 1500.0


def test_mais_rapido_ja_tem_o_minimo_de_baldeacoes():
    # RAPIDA direta: 300 + 200 = 500 s, sem baldeação; não há o que evitar.
    ge, gl = visoes(LONGE3, [("RAPIDA", "AC", [200]), ("P2", "AB", [100]), ("P3", "BC", [100])])
    c = comparar_baldeacoes(ge, gl, "A", "C")
    assert c.rapido_com_menos_baldeacoes is c.mais_rapido
    assert (c.tempo_a_mais_s, c.baldeacoes_evitadas) == (0.0, 0)
    assert c.tempo_por_baldeacao_evitada_s is None


def test_escolhe_o_mais_rapido_entre_os_de_menos_baldeacoes():
    # Mais rápido: Q1 + Q2 + Q3 = 3 × 300 + 3 × 60 = 1080 s, 2 baldeações.
    # Com 1 baldeação: Q1 + R3 = 300 + 60 + 300 + 700 = 1360 s;
    #                  R1 + Q3 = 300 + 1000 + 300 + 60 = 1660 s. Nenhum direto.
    padroes = [
        ("Q1", "AB", [60]),
        ("Q2", "BC", [60]),
        ("Q3", "CD", [60]),
        ("R1", "AC", [1000]),
        ("R3", "BD", [700]),
    ]
    ge, gl = visoes(LONGE4, padroes)
    c = comparar_baldeacoes(ge, gl, "A", "D")
    assert (c.mais_rapido.tempo_total_s, c.mais_rapido.baldeacoes) == (1080.0, 2)
    assert c.menos_baldeacoes.baldeacoes == 1
    r = c.rapido_com_menos_baldeacoes
    assert (r.tempo_total_s, r.baldeacoes) == (1360.0, 1)
    assert [t.padrao for t in r.trechos if t.tipo == ONIBUS] == ["Q1", "R3"]
    assert (c.tempo_a_mais_s, c.baldeacoes_evitadas) == (280.0, 1)


def test_limite_por_baldeacoes_e_monotono_e_chega_ao_mais_rapido():
    padroes = [
        ("Q1", "AB", [60]),
        ("Q2", "BC", [60]),
        ("Q3", "CD", [60]),
        ("R1", "AC", [1000]),
        ("R3", "BD", [700]),
    ]
    ge, _ = visoes(LONGE4, padroes)
    assert mais_rapido_com_limite(ge, "A", "D", 0) is None  # nenhuma linha direta
    tempos = [mais_rapido_com_limite(ge, "A", "D", k).tempo_total_s for k in (1, 2, 5)]
    assert tempos == [1360.0, 1080.0, 1080.0]
    assert tempos[-1] == trajeto_mais_rapido(ge, "A", "D").tempo_total_s


def test_caminhadas_encadeadas_no_g_e_fazem_menos_que_o_minimo_da_g_l():
    # A, M e B a 278 m em sequência: A -> M -> B a pé tem 556 m (463 s) no G_E, mas na
    # G_L a caminhada é uma de até 300 m por vez (B3 da F-BALD), então ela precisa de
    # P1 + P2 (1 baldeação). O mais rápido (a pé) já faz menos: nada é evitado.
    paradas = [("A", 0), ("M", 2.5), ("B", 5), ("X", 20)]
    ge, gl = visoes(paradas, [("P1", "AX", [30]), ("P2", "XB", [30])])
    c = comparar_baldeacoes(ge, gl, "A", "B")
    assert c.mais_rapido.baldeacoes == 0
    assert [t.tipo for t in c.mais_rapido.trechos] == [A_PE]
    assert c.mais_rapido.tempo_total_s == pytest.approx(2 * 2.5 * M_POR_MILESIMO / 1.2)
    assert c.menos_baldeacoes.baldeacoes == 1
    assert c.rapido_com_menos_baldeacoes is c.mais_rapido
    assert (c.tempo_a_mais_s, c.baldeacoes_evitadas) == (0.0, 0)


def test_espera_da_tabela_entra_no_tempo():
    # Com a espera da LENTA em 60 s (H/2 da F-ESPERA), menos baldeações custa 60 + 2000.
    esperas = {("LENTA", FAIXA): 60.0, ("P2", FAIXA): 300.0, ("P3", FAIXA): 300.0}
    padroes = [("LENTA", "AC", [2000]), ("P2", "AB", [100]), ("P3", "BC", [100])]
    ge, gl = visoes(LONGE3, padroes, esperas)
    c = comparar_baldeacoes(ge, gl, "A", "C")
    assert c.rapido_com_menos_baldeacoes.tempo_total_s == 2060.0
    assert c.tempo_a_mais_s == 1260.0


# --- Casos de borda ----------------------------------------------------------------------


def test_origem_igual_ao_destino():
    ge, gl = visoes(LONGE3, [("P2", "AB", [100])])
    c = comparar_baldeacoes(ge, gl, "A", "A")
    assert c.mais_rapido.tempo_total_s == 0.0 and c.mais_rapido.trechos == ()
    assert (c.tempo_a_mais_s, c.baldeacoes_evitadas) == (0.0, 0)
    t = mais_rapido_com_limite(ge, "A", "A", 0)
    assert (t.tempo_total_s, t.baldeacoes, t.trechos) == (0.0, 0, ())


def test_destino_inalcancavel():
    ge, gl = visoes(LONGE3, [("P2", "AB", [100]), ("P3", "BC", [100])])
    assert comparar_baldeacoes(ge, gl, "C", "A") is None  # os padrões têm sentido
    assert mais_rapido_com_limite(ge, "C", "A", 3) is None


def test_parada_inexistente():
    ge, gl = visoes(LONGE3, [("P2", "AB", [100])])
    with pytest.raises(KeyError):
        comparar_baldeacoes(ge, gl, "A", "Z")
    with pytest.raises(KeyError):
        mais_rapido_com_limite(ge, "Z", "A", 1)


def test_visoes_de_faixas_diferentes():
    r = _rede(LONGE3, [("P2", "AB", [100])])
    ge = construir_ge(r, FAIXA)
    with pytest.raises(ValueError, match="mesma faixa"):
        comparar_baldeacoes(ge, construir_gl(r), "A", "B")  # G_L do dia inteiro
    with pytest.raises(ValueError, match="mesma faixa"):
        comparar_baldeacoes(ge, construir_gl(r, faixa="entrepico"), "A", "B")


@pytest.mark.parametrize(
    ("limite", "erro"), [(-1, ValueError), (True, TypeError), (1.0, TypeError)]
)
def test_limite_invalido(limite, erro):
    ge, _ = visoes(LONGE3, [("P2", "AB", [100])])
    with pytest.raises(erro):
        mais_rapido_com_limite(ge, "A", "B", limite)


def test_visoes_que_nao_concordam_sao_recusadas():
    # A G_L acha a LENTA (0 baldeação), mas a viagem dela foi desativada só no G_E.
    padroes = [("LENTA", "AC", [2000]), ("P2", "AB", [100]), ("P3", "BC", [100])]
    ge, gl = visoes(LONGE3, padroes)
    _desativar_viagem(ge, "A", "LENTA")
    with pytest.raises(ValueError, match="mesma rede"):
        comparar_baldeacoes(ge, gl, "A", "C")


def _desativar_viagem(ge, parada, padrao):
    for _v, _peso, a in ge.grafo.vizinhos(ge.plataforma[(parada, padrao)]):
        if ge.grafo.aresta(a)[3] == VIAGEM:
            ge.grafo.desativar_aresta(a)


def test_respeita_falhas():
    padroes = [("LENTA", "AC", [2000]), ("P2", "AB", [100]), ("P3", "BC", [100])]
    ge, gl = visoes(LONGE3, padroes)
    _desativar_viagem(ge, "A", "LENTA")
    assert mais_rapido_com_limite(ge, "A", "C", 0) is None
    assert mais_rapido_com_limite(ge, "A", "C", 1).tempo_total_s == 800.0
    # A mesma falha nas duas visões (F-RES): sem a LENTA, o mínimo passa a 1 e o mais
    # rápido já o atinge.
    gl.grafo.desativar_vertice(gl.vertice_do_padrao["LENTA"])
    c = comparar_baldeacoes(ge, gl, "A", "C")
    assert c.menos_baldeacoes.baldeacoes == 1
    assert (c.tempo_a_mais_s, c.baldeacoes_evitadas) == (0.0, 0)
    # Origem desativada não alcança nada.
    ge.grafo.desativar_vertice(ge.vertice_da_parada["A"])
    assert mais_rapido_com_limite(ge, "A", "C", 3) is None


# --- Comparação com o NetworkX (só em tests/) ------------------------------------------


def _camadas_networkx(g, origem, destino, limite):
    """Grafo em camadas explícito: nó (v, e), e = embarques feitos (0 a limite + 1).
    EMBARQUE leva da camada e para a e + 1; as outras arestas ficam na camada. Um sorvedouro
    recebe o destino de todas as camadas, com peso 0."""
    camadas = limite + 2
    h = nx.DiGraph()
    for a in range(g.num_arestas()):
        u, v, peso, tipo = g.aresta(a)
        if not (g.aresta_ativa(a) and g.vertice_ativo(u) and g.vertice_ativo(v)):
            continue
        for e in range(camadas):
            e2 = e + 1 if tipo == EMBARQUE else e
            if e2 < camadas and (
                not h.has_edge((u, e), (v, e2)) or peso < h[(u, e)][(v, e2)]["weight"]
            ):
                h.add_edge((u, e), (v, e2), weight=peso)
    h.add_node((origem, 0))
    for e in range(camadas):
        h.add_edge((destino, e), "fim", weight=0.0)
    return h


def _rede_aleatoria(rnd):
    paradas = [(f"S{i}", rnd.uniform(0, 60)) for i in range(25)]  # 6,7 km: há caminhada
    nomes = [p for p, _ in paradas]
    padroes = []
    for k in range(12):
        seq = rnd.sample(nomes, rnd.randint(2, 7))
        if rnd.random() < 0.25:
            seq.append(seq[0])  # circular
        padroes.append((f"L{k}", seq, [rnd.randint(1, 20) * 30 for _ in seq[1:]]))
    esperas = {(f"L{k}", FAIXA): rnd.randint(2, 30) * 30.0 for k in range(12)}
    ge, gl = visoes(paradas, padroes, esperas)
    return ge, gl, nomes


@pytest.mark.parametrize("semente", range(15))
def test_limite_igual_ao_networkx_em_camadas(semente):
    rnd = random.Random(semente)
    ge, _gl, nomes = _rede_aleatoria(rnd)
    for _ in range(12):
        o, d = rnd.choice(nomes), rnd.choice(nomes)
        s, t = ge.vertice_da_parada[o], ge.vertice_da_parada[d]
        for limite in range(4):
            r = mais_rapido_com_limite(ge, o, d, limite)
            try:
                esperado = nx.dijkstra_path_length(
                    _camadas_networkx(ge.grafo, s, t, limite), (s, 0), "fim"
                )
            except nx.NetworkXNoPath:
                assert r is None
                continue
            assert r.tempo_total_s == pytest.approx(esperado)
            assert r.baldeacoes <= limite
            assert sum(tr.tempo_s for tr in r.trechos) == pytest.approx(esperado)
            for antes, depois in zip(r.trechos, r.trechos[1:], strict=False):
                assert depois.paradas[0] == antes.paradas[-1]


@pytest.mark.parametrize("semente", range(15))
def test_comparacao_em_redes_aleatorias(semente):
    rnd = random.Random(100 + semente)
    ge, gl, nomes = _rede_aleatoria(rnd)
    for _ in range(25):
        o, d = rnd.choice(nomes), rnd.choice(nomes)
        c = comparar_baldeacoes(ge, gl, o, d)  # não levanta: a G_L cabe no G_E
        if c is None:
            assert trajeto_mais_rapido(ge, o, d) is None or menos_baldeacoes(gl, o, d) is None
            continue
        assert isinstance(c, ComparacaoBaldeacoes)
        r = c.rapido_com_menos_baldeacoes
        assert c.tempo_a_mais_s >= 0.0 and c.baldeacoes_evitadas >= 0
        assert r.baldeacoes <= c.menos_baldeacoes.baldeacoes
        assert r.tempo_total_s >= c.mais_rapido.tempo_total_s - 1e-9
        if c.baldeacoes_evitadas:
            assert c.mais_rapido.baldeacoes > c.menos_baldeacoes.baldeacoes
