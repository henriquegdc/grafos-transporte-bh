"""Testes do construtor de G_L (F-BALD, RF-GRF-06).

Redes montadas à mão com os campos de RedeConstrutores. Coordenadas perto de BH;
0,001 grau de latitude = 111,19 m, então paradas a 0,01 grau (1,1 km) nunca têm caminhada e
paradas a 0,002 grau (222 m) sempre têm, com o raio padrão de 300 m.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from transporte.modelo.construtores import carregar, salvar
from transporte.modelo.linhas import construir_gl
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import BALDEACAO, VisaoGL

LAT0, LON0 = -19.92, -43.94
H7 = 7 * 3600
H10 = 10 * 3600


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


def rede(paradas: dict[str, tuple[float, float]], padroes: dict[str, str], partida=H7) -> Rede:
    """paradas: id -> (dlat, dlon) em graus a partir de (LAT0, LON0); padrões: id -> "ABC"
    (uma letra por parada). Cada padrão ganha uma viagem com a partida dada."""
    r = Rede()
    for pid, (dlat, dlon) in paradas.items():
        r.paradas[pid] = Parada(pid, LAT0 + dlat, LON0 + dlon)
    for pid, seq in padroes.items():
        r.padroes[pid] = Padrao(pid, tuple(seq))
        r.viagens[pid] = [[partida + 60 * k for k in range(len(seq))]]
    return r


def longe(*ids: str) -> dict[str, tuple[float, float]]:
    """Paradas a 0,01 grau umas das outras, em fila (sem caminhada entre elas)."""
    return {pid: (0.01 * k, 0.0) for k, pid in enumerate(ids)}


def arestas(gl: VisaoGL) -> dict[tuple[str, str], tuple]:
    g = gl.grafo
    saida = {}
    for a in range(g.num_arestas()):
        u, v, peso, tipo = g.aresta(a)
        assert peso == 1.0 and tipo == BALDEACAO
        saida[(gl.padrao_do_vertice[u], gl.padrao_do_vertice[v])] = gl.transferencias[a]
    return saida


def test_vertices_um_por_padrao_na_ordem_da_rede():
    gl = construir_gl(rede(longe(*"ABCD"), {"P2": "CD", "P1": "AB"}))
    assert gl.nome == "G_L"
    assert gl.padrao_do_vertice == ["P2", "P1"]
    assert gl.vertice_do_padrao == {"P2": 0, "P1": 1}
    assert gl.paradas_do_padrao == [("C", "D"), ("A", "B")]
    assert gl.grafo.num_arestas() == 0  # nenhuma parada em comum, nenhuma perto


def test_troca_na_mesma_parada_respeita_o_sentido():
    # P1: A -> B; P2: B -> C. Desce de P1 em B (posição 1) e embarca em P2 em B (posição 0).
    gl = construir_gl(rede(longe(*"ABC"), {"P1": "AB", "P2": "BC"}))
    assert arestas(gl) == {("P1", "P2"): ((1, "B", 0, "B"),)}
    # Não há P2 -> P1: em P2, B é a primeira parada (não se desce ali) e em P1 é a última
    # (não se embarca ali).


def test_sem_troca_na_primeira_parada_nem_embarque_na_ultima():
    # P1 e P2 começam em A: ninguém desce em A de nenhum dos dois.
    # P3 e P4 terminam em D: ninguém embarca em D em nenhum dos dois.
    gl = construir_gl(rede(longe(*"ABCDE"), {"P1": "AB", "P2": "AC", "P3": "BD", "P4": "CD"}))
    pares = set(arestas(gl))
    assert ("P1", "P2") not in pares and ("P2", "P1") not in pares
    assert ("P3", "P4") not in pares and ("P4", "P3") not in pares
    # B: desce de P1 (pos. 1), embarca em P3 (pos. 0). C: P2 -> P4.
    assert pares == {("P1", "P3"), ("P2", "P4")}


def test_troca_a_pe_entre_paradas_a_ate_o_raio():
    # B e C a 0,002 grau (222 m): troca a pé de P1 (desce em B) para P2 (embarca em C).
    paradas = {"A": (0.0, 0.0), "B": (0.01, 0.0), "C": (0.012, 0.0), "D": (0.03, 0.0)}
    gl = construir_gl(rede(paradas, {"P1": "AB", "P2": "CD"}))
    assert arestas(gl) == {("P1", "P2"): ((1, "B", 0, "C"),)}
    # Com raio de 200 m, B e C ficam longe demais e a troca some.
    gl = construir_gl(rede(paradas, {"P1": "AB", "P2": "CD"}), Parametros(raio_caminhada_m=200))
    assert arestas(gl) == {}


def test_proximas_tem_a_propria_parada_primeiro_e_depois_por_distancia():
    paradas = {"A": (0.0, 0.0), "B": (0.002, 0.0), "C": (0.001, 0.0), "D": (0.01, 0.0)}
    gl = construir_gl(rede(paradas, {"P1": "AD"}))
    assert [pid for pid, _ in gl.proximas["A"]] == ["A", "C", "B"]
    assert gl.proximas["A"][0] == ("A", 0.0)
    assert gl.proximas["A"][1][1] == pytest.approx(111.19, abs=0.1)
    assert gl.proximas["D"] == (("D", 0.0),)


def test_embarques_por_parada_sem_a_ultima_posicao():
    gl = construir_gl(rede(longe(*"ABC"), {"P1": "ABC", "P2": "BC"}))
    p1, p2 = gl.vertice_do_padrao["P1"], gl.vertice_do_padrao["P2"]
    assert gl.embarques == {"A": ((p1, 0),), "B": ((p1, 1), (p2, 0))}


def test_trocas_dominadas_saem_e_as_nao_dominadas_ficam_em_ordem():
    # P1: A B C D E; P2: B X C Y (passa por B e C de P1).
    # Candidatas P1 -> P2: (desce em B, pos. 1; embarca em B, pos. 0) e
    # (desce em C, pos. 2; embarca em C, pos. 2). Nenhuma domina a outra: a de C serve a
    # quem embarcou em P1 em B, a de B embarca mais cedo em P2.
    gl = construir_gl(rede(longe(*"ABCDEXY"), {"P1": "ABCDE", "P2": "BXCY"}))
    assert arestas(gl)[("P1", "P2")] == ((2, "C", 2, "C"), (1, "B", 0, "B"))
    # P2 -> P1: só C serve (B é a primeira parada de P2); a única candidata.
    assert arestas(gl)[("P2", "P1")] == ((2, "C", 2, "C"),)


def test_troca_que_desce_mais_tarde_e_embarca_mais_cedo_domina():
    # P1: A B C; P2: B C D. Candidatas P1 -> P2: (1, B, 0, B) e (2, C, 1, C).
    # Sem dominância entre elas (a segunda desce mais tarde, mas embarca mais tarde).
    gl = construir_gl(rede(longe(*"ABCD"), {"P1": "ABC", "P2": "BCD"}))
    assert arestas(gl)[("P1", "P2")] == ((2, "C", 1, "C"), (1, "B", 0, "B"))
    # Dominância pura: P4: A B C; P5: X C B Y, em que B (pos. 2) vem depois de C (pos. 1).
    # Candidatas P4 -> P5: (1, B, 2, B) e (2, C, 1, C). (2, C, 1, C) desce mais tarde e
    # embarca mais cedo: domina (1, B, 2, B).
    gl = construir_gl(rede(longe(*"ABCXY"), {"P4": "ABC", "P5": "XCBY"}))
    assert arestas(gl)[("P4", "P5")] == ((2, "C", 1, "C"),)


def test_embarcar_mais_cedo_vence_caminhar_menos():
    # P1: A B; P2: C D E com C a 222 m de B e D a 111 m de B. Candidatas P1 -> P2:
    # (1, B, 0, C) e (1, B, 1, D). A primeira desce na mesma posição e embarca mais cedo,
    # então domina, mesmo andando mais: a G_L conta baldeações, não metros.
    paradas = {
        "A": (0.0, 0.0),
        "B": (0.01, 0.0),
        "C": (0.012, 0.0),
        "D": (0.011, 0.0),
        "E": (0.03, 0.0),
    }
    gl = construir_gl(rede(paradas, {"P1": "AB", "P2": "CDE"}))
    assert arestas(gl)[("P1", "P2")] == ((1, "B", 0, "C"),)


def test_padrao_circular_tem_uma_entrada_por_ocorrencia():
    # P1: A B C A (volta a A). P2: A D. Desce de P1 em A na pos. 3 e embarca em P2 em A.
    gl = construir_gl(rede(longe(*"ABCD"), {"P1": "ABCA", "P2": "AD"}))
    p1 = gl.vertice_do_padrao["P1"]
    assert (p1, 0) in gl.embarques["A"] and (p1, 3) not in gl.embarques["A"]
    assert arestas(gl)[("P1", "P2")] == ((3, "A", 0, "A"),)
    # P2 -> P1 não existe: P2 só desce em D, que P1 não atende.
    assert ("P2", "P1") not in arestas(gl)


def test_laco_no_mesmo_padrao():
    # Circular: desce em A (posição 3) e pega o mesmo P1 de novo em A (posição 0).
    gl = construir_gl(rede(longe(*"ABC"), {"P1": "ABCA"}))
    assert arestas(gl) == {("P1", "P1"): ((3, "A", 0, "A"),)}
    # A pé: P2 vai de A a D; D fica a 222 m de A. Desce em D e pega P2 de novo em A.
    paradas = {"A": (0.0, 0.0), "D": (0.002, 0.0)}
    gl = construir_gl(rede(paradas, {"P2": "AD"}))
    assert arestas(gl) == {("P2", "P2"): ((1, "D", 0, "A"),)}
    # Sem caminhada nem repetição, não há laço.
    assert construir_gl(rede(longe(*"AB"), {"P3": "AB"})).grafo.num_arestas() == 0


def test_padrao_com_uma_parada_fica_fora():
    gl = construir_gl(rede(longe(*"AB"), {"P0": "A", "P1": "AB"}))
    assert gl.padrao_do_vertice == ["P1"]


def test_faixa_filtra_padroes_sem_partida_nela():
    r = rede(longe(*"ABC"), {"P1": "AB", "P2": "BC"})
    r.viagens["P2"] = [[H10, H10 + 60]]  # P2 só parte às 10h (entrepico)
    gl = construir_gl(r, faixa="pico_manha")
    assert gl.faixa == "pico_manha"
    assert gl.padrao_do_vertice == ["P1"]
    assert construir_gl(r, faixa="entrepico").padrao_do_vertice == ["P2"]
    assert construir_gl(r).padrao_do_vertice == ["P1", "P2"]


def test_faixa_inexistente_e_parada_inexistente_levantam_keyerror():
    r = rede(longe(*"AB"), {"P1": "AB"})
    with pytest.raises(KeyError):
        construir_gl(r, faixa="madrugada")
    r.padroes["P2"] = Padrao("P2", ("A", "Z"))
    with pytest.raises(KeyError):
        construir_gl(r)


def test_rede_vazia():
    gl = construir_gl(Rede())
    assert gl.grafo.num_vertices() == 0 and gl.grafo.num_arestas() == 0
    assert gl.proximas == {} and gl.embarques == {}


def test_uma_lista_de_trocas_por_aresta():
    gl = construir_gl(rede(longe(*"ABCDE"), {"P1": "ABC", "P2": "BD", "P3": "CE", "P4": "DC"}))
    assert len(gl.transferencias) == gl.grafo.num_arestas() > 0
    assert all(gl.transferencias)  # toda aresta tem pelo menos uma troca


def test_salvar_e_carregar(tmp_path):
    gl = construir_gl(rede(longe(*"ABC"), {"P1": "AB", "P2": "BC"}))
    caminho = tmp_path / "cache" / "gl.pkl"
    salvar(gl, caminho)
    lido = carregar(caminho)
    assert isinstance(lido, VisaoGL)
    assert lido.transferencias == gl.transferencias
    assert lido.padrao_do_vertice == gl.padrao_do_vertice
