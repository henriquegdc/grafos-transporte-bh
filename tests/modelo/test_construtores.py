"""Testes dos construtores de G_P e G_E e da persistência (P0-MODELO).

A Rede de P0-DADOS ainda não existe; os testes usam uma rede mínima com os campos de
`RedeConstrutores`. Coordenadas perto de BH; 0,001 grau de latitude = R * pi / 180 * 0,001
= 111,19 m (ao longo do meridiano a haversine dá exatamente R * delta_latitude).
"""

from __future__ import annotations

import math
import pickle
import random
from dataclasses import dataclass, field

import pytest

from transporte.grafo.buscas import caminho_arestas, dijkstra
from transporte.modelo.construtores import (
    _distancia_m,
    _pares_caminhada,
    carregar,
    construir_ge,
    construir_gp,
    salvar,
)
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import (
    CAMINHADA,
    DESEMBARQUE,
    EMBARQUE,
    VIAGEM,
    VisaoGE,
    VisaoGP,
)

LAT0, LON0 = -19.92, -43.94
M_POR_MILESIMO = 6_371_000.0 * math.pi / 180 * 0.001  # 111,19 m
H7, H20 = 7 * 3600, 20 * 3600  # pico da manhã e noite


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


def rede(paradas, padroes):
    """paradas: [(id, milésimos de grau ao norte)]; padroes: [(id, seq, viagens)]."""
    r = Rede()
    for pid, norte in paradas:
        r.paradas[pid] = Parada(pid, LAT0 + norte / 1000, LON0)
    for pid, seq, viagens in padroes:
        r.padroes[pid] = Padrao(pid, tuple(seq))
        r.viagens[pid] = viagens
    return r


def arestas(visao, tipo=None):
    """{(rótulo origem, rótulo destino): [pesos]} das arestas, opcionalmente de um tipo."""
    g = visao.grafo
    saida = {}
    for a in range(g.num_arestas()):
        u, v, peso, t = g.aresta(a)
        if tipo is None or t == tipo:
            saida.setdefault((g.rotulo(u), g.rotulo(v)), []).append(peso)
    return saida


# --- G_P -------------------------------------------------------------------------------


@pytest.fixture
def rede_gp():
    # A e D no mesmo ponto (um stop_id por sentido); B 111 m ao norte; C 1112 m ao norte.
    return rede(
        [("A", 0), ("B", 1), ("C", 10), ("D", 0)],
        [
            # A->B: 60, 50, 70 (mediana 60). B->C: 240, 270, 330.
            ("P1", "ABC", [[100, 160, 400], [200, 250, 520], [300, 370, 700]]),
            # B->C: 300. Junto com P1: 240, 270, 300, 330 -> mediana 285.
            ("P2", "BC", [[0, 300]]),
            # C->D: 0 s (horário arredondado) -> piso de 1 s.
            ("P3", "CD", [[1000, 1000]]),
            # D->A: só diferença negativa (erro de cadastro) -> piso de 1 s (D8).
            ("P4", "DA", [[500, 490]]),
        ],
    )


def test_gp_vertices_seguem_a_ordem_das_paradas(rede_gp):
    v = construir_gp(rede_gp)
    assert isinstance(v, VisaoGP)
    assert v.nome == "G_P"
    assert v.parada_do_vertice == ["A", "B", "C", "D"]
    assert v.vertice_da_parada == {"A": 0, "B": 1, "C": 2, "D": 3}
    assert v.grafo.num_vertices() == 4


def test_gp_viagem_com_mediana_e_piso(rede_gp):
    assert arestas(construir_gp(rede_gp), VIAGEM) == {
        ("A", "B"): [60.0],
        ("B", "C"): [285.0],  # trecho de dois padrões: uma aresta só
        ("C", "D"): [1.0],
        ("D", "A"): [1.0],
    }


def test_gp_caminhada_nos_dois_sentidos(rede_gp):
    t = M_POR_MILESIMO / 1.2  # 92,66 s
    cam = arestas(construir_gp(rede_gp), CAMINHADA)
    assert set(cam) == {
        ("A", "B"),
        ("B", "A"),
        ("A", "D"),
        ("D", "A"),
        ("B", "D"),
        ("D", "B"),
    }
    assert cam[("A", "B")] == [pytest.approx(t)]
    assert cam[("B", "D")] == [pytest.approx(t)]
    assert cam[("A", "D")] == [1.0]  # 0 m -> piso


def test_gp_parametros_mudam_raio_e_piso(rede_gp):
    params = Parametros(raio_caminhada_m=50, peso_minimo_s=5)
    v = construir_gp(rede_gp, params)
    assert set(arestas(v, CAMINHADA)) == {("A", "D"), ("D", "A")}
    assert arestas(v, VIAGEM)[("C", "D")] == [5.0]


def test_gp_mediana_de_quantidade_par():
    r = rede(
        [("A", 0), ("B", 10)], [("P", "AB", [[0, 10], [0, 20], [0, 40], [0, 100]])]
    )
    assert arestas(construir_gp(r), VIAGEM) == {("A", "B"): [30.0]}


def test_gp_diferenca_negativa_fica_fora_da_mediana():
    # 60, 80 e -500 (erro de cadastro). Sem o filtro a mediana seria 60; com ele, 70 (D8).
    r = rede([("A", 0), ("B", 10)], [("P", "AB", [[0, 60], [0, 80], [600, 100]])])
    assert arestas(construir_gp(r), VIAGEM) == {("A", "B"): [70.0]}


def test_gp_parada_isolada_e_padrao_sem_viagens():
    r = rede([("A", 0), ("B", 10), ("Z", 50)], [("P", "AB", [])])
    v = construir_gp(r)
    assert v.grafo.num_vertices() == 3
    assert v.grafo.vizinhos(v.vertice_da_parada["Z"]) == []
    assert arestas(v, VIAGEM) == {("A", "B"): [1.0]}  # trecho sem horário -> piso


def test_gp_parada_repetida_em_sequencia_nao_gera_laco():
    r = rede([("A", 0), ("B", 10)], [("P", "AAB", [[0, 30, 90]])])
    assert arestas(construir_gp(r), VIAGEM) == {("A", "B"): [60.0]}


def test_gp_rede_vazia():
    v = construir_gp(Rede())
    assert v.grafo.num_vertices() == 0
    assert v.grafo.num_arestas() == 0


def test_gp_parada_inexistente_levanta_key_error():
    r = rede([("A", 0)], [("P", "AX", [[0, 10]])])
    with pytest.raises(KeyError):
        construir_gp(r)


# --- G_E -------------------------------------------------------------------------------


@pytest.fixture
def rede_ge():
    # Paradas a 1112 m uma da outra: sem caminhada.
    return rede(
        [("A", 0), ("B", 10), ("C", 20)],
        [
            ("P1", "ABC", [[H7, H7 + 100, H7 + 300], [H7 + 600, H7 + 700, H7 + 900]]),
            ("P2", "BC", [[H20, H20 + 50]]),
        ],
    )


def test_ge_pico_manha(rede_ge):
    v = construir_ge(rede_ge, "pico_manha")
    assert isinstance(v, VisaoGE)
    assert (v.nome, v.faixa) == ("G_E", "pico_manha")
    assert v.vertice_da_parada == {"A": 0, "B": 1, "C": 2}
    assert v.plataforma == {
        ("A", "P1"): 3,
        ("B", "P1"): 4,
        ("C", "P1"): 5,
        ("B", "P2"): 6,
        ("C", "P2"): 7,
    }
    # P2 não parte no pico da manhã: sem embarque. Última parada sem embarque, primeira
    # sem desembarque.
    assert arestas(v, EMBARQUE) == {("A", "A@P1"): [300.0], ("B", "B@P1"): [300.0]}
    assert arestas(v, VIAGEM) == {
        ("A@P1", "B@P1"): [100.0],
        ("B@P1", "C@P1"): [200.0],
        ("B@P2", "C@P2"): [50.0],
    }
    assert arestas(v, DESEMBARQUE) == {
        ("B@P1", "B"): [0.0],
        ("C@P1", "C"): [0.0],
        ("C@P2", "C"): [0.0],
    }
    assert arestas(v, CAMINHADA) == {}


def test_ge_noite_embarca_so_no_padrao_que_parte(rede_ge):
    v = construir_ge(rede_ge, "noite")
    assert arestas(v, EMBARQUE) == {("B", "B@P2"): [300.0]}


def test_ge_espera_vem_da_tabela_sem_transformar(rede_ge):
    # A F-ESPERA entrega a espera pronta (H/2 ou E[H²]/(2E[H])); o construtor só aplica.
    v = construir_ge(rede_ge, "pico_manha", esperas={("P1", "pico_manha"): 437.5})
    assert arestas(v, EMBARQUE) == {("A", "A@P1"): [437.5], ("B", "B@P1"): [437.5]}


def test_ge_espera_de_outra_faixa_nao_se_aplica(rede_ge):
    v = construir_ge(rede_ge, "pico_manha", esperas={("P1", "noite"): 900.0})
    assert arestas(v, EMBARQUE)[("A", "A@P1")] == [300.0]


def test_ge_espera_ausente_usa_espera_padrao(rede_ge):
    v = construir_ge(rede_ge, "pico_manha", esperas={})
    assert arestas(v, EMBARQUE)[("A", "A@P1")] == [300.0]


def test_ge_espera_zero_vale(rede_ge):
    # 0 é espera válida (não pode cair no padrão por ser falsy).
    v = construir_ge(rede_ge, "pico_manha", esperas={("P1", "pico_manha"): 0.0})
    assert arestas(v, EMBARQUE)[("A", "A@P1")] == [0.0]


def test_ge_espera_negativa_levanta(rede_ge):
    with pytest.raises(ValueError):
        construir_ge(rede_ge, "pico_manha", esperas={("P1", "pico_manha"): -1.0})


def test_ge_trajeto_e_baldeacoes():
    # A -> B pela P1, troca para P2 em B, B -> C. Custo = 300 + 100 + 0 + 300 + 50.
    r = rede(
        [("A", 0), ("B", 10), ("C", 20)],
        [("P1", "AB", [[H7, H7 + 100]]), ("P2", "BC", [[H7, H7 + 50]])],
    )
    v = construir_ge(r, "pico_manha")
    res = dijkstra(v.grafo, v.vertice_da_parada["A"])
    destino = v.vertice_da_parada["C"]
    assert res.dist[destino] == 750.0
    assert v.baldeacoes(caminho_arestas(res, destino)) == 1


def test_ge_linha_circular_usa_uma_plataforma_por_parada():
    # A aparece em k = 0, 2 e 4: um embarque e um desembarque só para A@P.
    r = rede(
        [("A", 0), ("B", 10), ("C", 20)],
        [("P", "ABACA", [[H7, H7 + 100, H7 + 250, H7 + 400, H7 + 500]])],
    )
    v = construir_ge(r, "pico_manha")
    assert v.plataforma == {("A", "P"): 3, ("B", "P"): 4, ("C", "P"): 5}
    assert arestas(v, EMBARQUE) == {
        ("A", "A@P"): [300.0],
        ("B", "B@P"): [300.0],
        ("C", "C@P"): [300.0],
    }
    assert arestas(v, VIAGEM) == {
        ("A@P", "B@P"): [100.0],
        ("B@P", "A@P"): [150.0],
        ("A@P", "C@P"): [150.0],
        ("C@P", "A@P"): [100.0],
    }
    assert arestas(v, DESEMBARQUE) == {
        ("B@P", "B"): [0.0],
        ("A@P", "A"): [0.0],
        ("C@P", "C"): [0.0],
    }


def test_ge_caminhada_igual_a_do_gp(rede_gp):
    assert arestas(construir_ge(rede_gp, "entrepico"), CAMINHADA) == arestas(
        construir_gp(rede_gp), CAMINHADA
    )


def test_ge_padrao_de_uma_parada_e_ignorado():
    r = rede([("A", 0)], [("P", "A", [[H7]])])
    v = construir_ge(r, "pico_manha")
    assert v.plataforma == {}
    assert v.grafo.num_arestas() == 0


def test_ge_faixa_inexistente_levanta_key_error(rede_ge):
    with pytest.raises(KeyError):
        construir_ge(rede_ge, "madrugada")


def test_ge_parada_inexistente_levanta_key_error():
    r = rede([("A", 0)], [("P", "AX", [[H7, H7 + 10]])])
    with pytest.raises(KeyError):
        construir_ge(r, "pico_manha")


def test_ge_padrao_de_uma_parada_inexistente_levanta_key_error():
    # Mesma checagem do G_P: vale antes de ignorar o padrão de uma parada só.
    r = rede([("A", 0)], [("P", "X", [[H7]])])
    with pytest.raises(KeyError):
        construir_ge(r, "pico_manha")


# --- Caminhada: grade espacial contra a busca ingênua ---------------------------------


def test_distancia_ao_longo_do_meridiano():
    assert _distancia_m(LAT0, LON0, LAT0 + 0.001, LON0) == pytest.approx(M_POR_MILESIMO)
    assert _distancia_m(LAT0, LON0, LAT0, LON0) == 0.0


@pytest.mark.parametrize("semente", range(10))
def test_grade_igual_a_busca_ingenua(semente):
    rnd = random.Random(semente)
    paradas = [
        Parada(str(i), LAT0 + rnd.uniform(-0.01, 0.01), LON0 + rnd.uniform(-0.01, 0.01))
        for i in range(300)
    ]
    raio = rnd.choice([100.0, 300.0, 500.0])
    esperado = {
        (i, j)
        for i in range(len(paradas))
        for j in range(i + 1, len(paradas))
        if _distancia_m(paradas[i].lat, paradas[i].lon, paradas[j].lat, paradas[j].lon)
        <= raio
    }
    obtido = _pares_caminhada(paradas, raio)
    assert {(i, j) for i, j, _ in obtido} == esperado
    assert len(obtido) == len(esperado)


# --- Persistência ----------------------------------------------------------------------


@pytest.mark.parametrize("construir", ["gp", "ge"])
def test_salvar_e_carregar_ida_e_volta(tmp_path, rede_gp, construir):
    v = (
        construir_gp(rede_gp)
        if construir == "gp"
        else construir_ge(rede_gp, "pico_manha")
    )
    arq = tmp_path / "cache" / "sub" / "visao.pkl"  # pastas criadas por salvar
    salvar(v, arq)
    lida = carregar(arq)
    assert type(lida) is type(v)
    assert arestas(lida) == arestas(v)
    assert lida.vertice_da_parada == v.vertice_da_parada


def test_salvar_sobrescreve(tmp_path, rede_gp):
    arq = tmp_path / "v.pkl"
    salvar(construir_gp(Rede()), arq)
    salvar(construir_gp(rede_gp), arq)
    assert carregar(arq).grafo.num_vertices() == 4


def test_carregar_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        carregar(tmp_path / "nao-existe.pkl")


def test_carregar_arquivo_sem_visao(tmp_path):
    arq = tmp_path / "x.pkl"
    arq.write_bytes(pickle.dumps({"nao": "visao"}))
    with pytest.raises(TypeError):
        carregar(arq)
