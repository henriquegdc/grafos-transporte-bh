"""Testes do trajeto com menos baldeações sobre G_L (F-BALD, RF-BAL-01 e RF-BAL-02).

As redes são montadas à mão com os campos de RedeConstrutores e passam pelo construir_gl de
verdade. 0,001 grau de latitude = 111,19 m; paradas a 0,01 grau (1,1 km) não têm caminhada
entre si, e a 0,002 grau (222 m) têm, com o raio padrão de 300 m.

A comparação com o NetworkX monta, só no teste, um grafo de estados independente da G_L
(chegou à parada, pronto para embarcar na parada, embarcou no padrão na posição k, a bordo
na posição k), com peso 1 no embarque e 0 no resto: o caminho mínimo nele é o número mínimo
de ônibus. A caminhada é calculada par a par, sem a grade espacial.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import networkx as nx
import pytest

from transporte.algoritmos.baldeacoes import TrechoBaldeacao, menos_baldeacoes
from transporte.algoritmos.trajeto import A_PE, ONIBUS
from transporte.grafo.buscas import INF, bfs
from transporte.modelo.linhas import construir_gl

LAT0, LON0 = -19.92, -43.94
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


def rede(paradas: dict[str, tuple[float, float]], padroes: dict) -> Rede:
    """paradas: id -> (dlat, dlon) em graus a partir de (LAT0, LON0); padrões: id -> "ABC"
    ou tupla de ids. Cada padrão ganha uma viagem às 07h."""
    r = Rede()
    for pid, (dlat, dlon) in paradas.items():
        r.paradas[pid] = Parada(pid, LAT0 + dlat, LON0 + dlon)
    for pid, seq in padroes.items():
        r.padroes[pid] = Padrao(pid, tuple(seq))
        r.viagens[pid] = [[H7 + 60 * k for k in range(len(seq))]]
    return r


def longe(*ids: str) -> dict[str, tuple[float, float]]:
    """Paradas a 0,01 grau umas das outras, em fila (sem caminhada entre elas)."""
    return {pid: (0.01 * k, 0.0) for k, pid in enumerate(ids)}


def onibus(seq: str, padrao: str) -> TrechoBaldeacao:
    return TrechoBaldeacao(ONIBUS, tuple(seq), padrao)


def a_pe(de: str, para: str) -> TrechoBaldeacao:
    return TrechoBaldeacao(A_PE, (de, para))


# --- Gabarito à mão ---------------------------------------------------------------------


def test_linha_direta_tem_zero_baldeacoes():
    gl = construir_gl(rede(longe(*"ABCD"), {"P1": "ABCD"}))
    t = menos_baldeacoes(gl, "A", "C")
    assert t.baldeacoes == 0
    assert t.trechos == (onibus("ABC", "P1"),)
    assert t.padroes() == ["P1"] and t.trocas() == []


def test_uma_troca_na_mesma_parada():
    gl = construir_gl(rede(longe(*"ABC"), {"P1": "AB", "P2": "BC"}))
    t = menos_baldeacoes(gl, "A", "C")
    assert t.baldeacoes == 1
    assert t.trechos == (onibus("AB", "P1"), onibus("BC", "P2"))
    assert t.padroes() == ["P1", "P2"]
    assert t.trocas() == [("B", "B")]


def test_troca_a_pe_entre_paradas_proximas():
    # B e C a 222 m: desce de P1 em B, anda até C, embarca em P2.
    paradas = {"A": (0.0, 0.0), "B": (0.01, 0.0), "C": (0.012, 0.0), "D": (0.03, 0.0)}
    gl = construir_gl(rede(paradas, {"P1": "AB", "P2": "CD"}))
    t = menos_baldeacoes(gl, "A", "D")
    assert t.baldeacoes == 1
    assert t.trechos == (onibus("AB", "P1"), a_pe("B", "C"), onibus("CD", "P2"))
    assert t.trocas() == [("B", "C")]


def test_a_pe_nas_pontas():
    # O a 222 m de A (embarque) e D a 222 m de E (destino).
    paradas = {"O": (-0.002, 0.0), "A": (0.0, 0.0), "D": (0.02, 0.0), "E": (0.022, 0.0)}
    gl = construir_gl(rede(paradas, {"P1": "AD"}))
    t = menos_baldeacoes(gl, "O", "E")
    assert t.baldeacoes == 0
    assert t.trechos == (a_pe("O", "A"), onibus("AD", "P1"), a_pe("D", "E"))


def test_ordem_dentro_do_padrao_importa():
    # P1: S B A E. P2: B D. P3: E B.
    # Em G_L há P1 -> P2 (desce em B, posição 1), e um BFS comum diria 1 baldeação de A a D.
    # Mas quem embarca em P1 em A (posição 2) não volta a B por P1: precisa ir até E,
    # pegar P3 de volta a B e então P2. São 2 baldeações.
    gl = construir_gl(rede(longe(*"SBAED"), {"P1": "SBAE", "P2": "BD", "P3": "EB"}))
    t = menos_baldeacoes(gl, "A", "D")
    assert t.baldeacoes == 2
    assert t.trechos == (onibus("AE", "P1"), onibus("EB", "P3"), onibus("BD", "P2"))
    assert t.trocas() == [("E", "E"), ("B", "B")]
    # O BFS do núcleo, que ignora a ordem, dá o limite inferior de 1.
    r = bfs(gl.grafo, gl.vertice_do_padrao["P1"])
    assert r.dist[gl.vertice_do_padrao["P2"]] == 1


def test_padrao_alcancado_de_novo_em_posicao_mais_cedo():
    # Q: Q0 Q1 O Q3, com a origem O na posição 2 de Q. P1: O Q0. R: Q1 D.
    # Camada 1: Q embarcado na posição 2 (em O), P1 na posição 0.
    # Camada 2: P1 desce em Q0 e embarca em Q na posição 0, mais cedo que 2: Q melhora.
    # Camada 3: Q, agora a partir da posição 0, desce em Q1 e pega R até D.
    # Quem visitasse cada padrão uma vez só não acharia trajeto.
    paradas = longe("O", "Q0", "Q1", "Q3", "D")
    padroes = {"Q": ("Q0", "Q1", "O", "Q3"), "P1": ("O", "Q0"), "R": ("Q1", "D")}
    gl = construir_gl(rede(paradas, padroes))
    t = menos_baldeacoes(gl, "O", "D")
    assert t.baldeacoes == 2
    assert t.padroes() == ["P1", "Q", "R"]
    assert t.trechos[1] == TrechoBaldeacao(ONIBUS, ("Q0", "Q1"), "Q")


def test_menos_baldeacoes_vence_caminho_com_mais_paradas():
    # Direto por P1 (A ... E, 4 paradas) contra P2 + P3 (A C, C E): vence o direto.
    gl = construir_gl(rede(longe(*"ABCDE"), {"P2": "AC", "P3": "CE", "P1": "ABCDE"}))
    t = menos_baldeacoes(gl, "A", "E")
    assert t.baldeacoes == 0 and t.padroes() == ["P1"]


def test_empate_prefere_menos_caminhada_no_fim():
    # Dois padrões diretos: P1 termina em D (destino), P2 termina em E, a 222 m de D.
    paradas = {"A": (0.0, 0.0), "D": (0.02, 0.0), "E": (0.022, 0.0)}
    gl = construir_gl(rede(paradas, {"P2": "AE", "P1": "AD"}))
    t = menos_baldeacoes(gl, "A", "D")
    assert t.trechos == (onibus("AD", "P1"),)


def test_destino_perto_da_origem_vai_a_pe():
    paradas = {"A": (0.0, 0.0), "B": (0.002, 0.0)}
    gl = construir_gl(rede(paradas, {"P1": "AB"}))
    t = menos_baldeacoes(gl, "A", "B")
    assert t.baldeacoes == 0 and t.trechos == (a_pe("A", "B"),)
    assert t.padroes() == [] and t.trocas() == []


def test_origem_igual_ao_destino():
    gl = construir_gl(rede(longe(*"AB"), {"P1": "AB"}))
    t = menos_baldeacoes(gl, "A", "A")
    assert t.baldeacoes == 0 and t.trechos == ()


def test_inalcancavel_devolve_none():
    gl = construir_gl(rede(longe(*"ABCD"), {"P1": "AB", "P2": "CD"}))
    assert menos_baldeacoes(gl, "A", "D") is None
    # Contra o sentido do padrão também não dá.
    assert menos_baldeacoes(gl, "B", "A") is None


def test_parada_sem_nenhum_padrao():
    gl = construir_gl(rede(longe(*"ABX"), {"P1": "AB"}))
    assert menos_baldeacoes(gl, "X", "B") is None
    assert menos_baldeacoes(gl, "A", "X") is None


def test_parada_inexistente_levanta_keyerror():
    gl = construir_gl(rede(longe(*"AB"), {"P1": "AB"}))
    with pytest.raises(KeyError):
        menos_baldeacoes(gl, "Z", "B")
    with pytest.raises(KeyError):
        menos_baldeacoes(gl, "A", "Z")


def test_padrao_circular_so_anda_para_a_frente():
    # P1: A B C A. De B a A: segue até o fim (C, A), sem baldeação.
    gl = construir_gl(rede(longe(*"ABC"), {"P1": "ABCA"}))
    assert menos_baldeacoes(gl, "B", "A").trechos == (onibus("BCA", "P1"),)
    # De C a B o ônibus não volta: vai até o fim (A), e lá se pega o próximo P1. Conta como
    # baldeação, porque é outro embarque (outra espera).
    t = menos_baldeacoes(gl, "C", "B")
    assert t.baldeacoes == 1
    assert t.trechos == (onibus("CA", "P1"), onibus("AB", "P1"))


def test_descer_andar_e_pegar_o_mesmo_padrao_mais_atras():
    # P1: A B C D, com D a 222 m de A. De C a B: P1 até D, anda até A e pega P1 de novo
    # até B.
    paradas = {"A": (0.0, 0.0), "B": (0.01, 0.0), "C": (0.01, 0.01), "D": (0.002, 0.0)}
    gl = construir_gl(rede(paradas, {"P1": "ABCD"}))
    t = menos_baldeacoes(gl, "C", "B")
    assert t.baldeacoes == 1
    assert t.trechos == (onibus("CD", "P1"), a_pe("D", "A"), onibus("AB", "P1"))


def test_falha_de_padrao_e_de_troca():
    # A -> D: direto por P1, ou P2 + P3 com troca em B.
    gl = construir_gl(rede(longe(*"ABD"), {"P1": "AD", "P2": "AB", "P3": "BD"}))
    g = gl.grafo
    assert menos_baldeacoes(gl, "A", "D").padroes() == ["P1"]
    g.desativar_vertice(gl.vertice_do_padrao["P1"])
    assert menos_baldeacoes(gl, "A", "D").padroes() == ["P2", "P3"]
    # Desativa a aresta P2 -> P3: sem P1 e sem a troca, não há trajeto.
    (a,) = [a for a in range(g.num_arestas()) if g.aresta(a)[:2] == (
        gl.vertice_do_padrao["P2"], gl.vertice_do_padrao["P3"])]
    g.desativar_aresta(a)
    assert menos_baldeacoes(gl, "A", "D") is None
    g.reativar_tudo()
    assert menos_baldeacoes(gl, "A", "D").padroes() == ["P1"]


def test_padrao_desativado_no_destino():
    gl = construir_gl(rede(longe(*"ABC"), {"P1": "AB", "P2": "BC"}))
    gl.grafo.desativar_vertice(gl.vertice_do_padrao["P2"])
    assert menos_baldeacoes(gl, "A", "C") is None


# --- Comparação com o NetworkX e propriedades em redes aleatórias -----------------------


def _distancia_m(p: Parada, q: Parada) -> float:
    """Haversine, escrita de novo aqui para a referência não depender da grade espacial."""
    f1, f2 = math.radians(p.lat), math.radians(q.lat)
    h = (
        math.sin((f2 - f1) / 2) ** 2
        + math.cos(f1) * math.cos(f2) * math.sin(math.radians(q.lon - p.lon) / 2) ** 2
    )
    return 2 * 6_371_000.0 * math.asin(min(1.0, math.sqrt(h)))


def _rede_aleatoria(rng: random.Random, n_paradas: int, n_padroes: int) -> Rede:
    r = Rede()
    for k in range(n_paradas):
        pid = f"s{k}"
        # Área de cerca de 2,2 km x 2,2 km: umas paradas ficam a até 300 m, outras não.
        r.paradas[pid] = Parada(pid, LAT0 + rng.uniform(0, 0.02), LON0 + rng.uniform(0, 0.02))
    ids = list(r.paradas)
    for k in range(n_padroes):
        seq = rng.sample(ids, rng.randint(2, 6))
        if rng.random() < 0.15:
            seq.append(seq[0])  # circular
        pid = f"p{k}"
        r.padroes[pid] = Padrao(pid, tuple(seq))
        r.viagens[pid] = [[H7 + 60 * i for i in range(len(seq))]]
    return r


def _referencia(r: Rede, raio_m: float = 300.0) -> nx.DiGraph:
    g = nx.DiGraph()
    paradas = list(r.paradas.values())
    for p in paradas:
        g.add_edge(("chegou", p.id), ("pronto", p.id), weight=0)
        for q in paradas:
            if p.id != q.id and _distancia_m(p, q) <= raio_m:
                g.add_edge(("chegou", p.id), ("pronto", q.id), weight=0)
    for pad in r.padroes.values():
        seq = pad.paradas
        # "embarcou" (ainda parado na posição k) só segue viagem; "a bordo" (chegou à
        # posição k andando de ônibus) pode seguir ou descer. Sem essa separação, embarcar e
        # descer na mesma posição encadearia duas caminhadas pelo preço de um ônibus.
        for k in range(len(seq) - 1):
            g.add_edge(("pronto", seq[k]), ("embarcou", pad.id, k), weight=1)
            g.add_edge(("embarcou", pad.id, k), ("a bordo", pad.id, k + 1), weight=0)
            if k >= 1:
                g.add_edge(("a bordo", pad.id, k), ("a bordo", pad.id, k + 1), weight=0)
        for k in range(1, len(seq)):
            g.add_edge(("a bordo", pad.id, k), ("chegou", seq[k]), weight=0)
    return g


def _onibus_minimos(ref: nx.DiGraph, origem: str, destino: str) -> int | None:
    if origem == destino:
        return 0
    try:
        return nx.dijkstra_path_length(ref, ("chegou", origem), ("pronto", destino))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def _conferir_trechos(r: Rede, t, origem: str, destino: str) -> None:
    """O trajeto é executável: trechos encadeados, ônibus para a frente no padrão, a pé
    só entre paradas a até o raio e nunca duas caminhadas seguidas."""
    if origem == destino:
        assert t.trechos == ()
        return
    assert t.trechos[0].paradas[0] == origem
    assert t.trechos[-1].paradas[-1] == destino
    for a, b in zip(t.trechos, t.trechos[1:]):
        assert a.paradas[-1] == b.paradas[0]
        assert not (a.tipo == A_PE and b.tipo == A_PE)
    for tr in t.trechos:
        assert len(tr.paradas) >= 2
        if tr.tipo == A_PE:
            p, q = (r.paradas[x] for x in tr.paradas)
            assert tr.paradas[0] != tr.paradas[1]
            assert _distancia_m(p, q) <= 300.0
        else:
            seq = r.padroes[tr.padrao].paradas
            n = len(tr.paradas)
            assert any(tuple(seq[b : b + n]) == tr.paradas for b in range(len(seq) - n + 1))
    assert t.baldeacoes == max(0, len(t.padroes()) - 1)
    assert len(t.trocas()) == max(0, len(t.padroes()) - 1)


@pytest.mark.parametrize("semente", range(12))
def test_igual_ao_networkx_em_redes_aleatorias(semente):
    rng = random.Random(semente)
    r = _rede_aleatoria(rng, n_paradas=rng.randint(8, 25), n_padroes=rng.randint(3, 14))
    gl = construir_gl(r)
    ref = _referencia(r)
    ids = list(r.paradas)
    for _ in range(40):
        origem, destino = rng.choice(ids), rng.choice(ids)
        esperado = _onibus_minimos(ref, origem, destino)
        t = menos_baldeacoes(gl, origem, destino)
        if esperado is None:
            assert t is None, (origem, destino)
            continue
        assert t is not None, (origem, destino)
        assert len(t.padroes()) == esperado, (origem, destino)
        _conferir_trechos(r, t, origem, destino)


def test_bfs_comum_da_limite_inferior():
    """Propriedade: o BFS do núcleo em G_L, que ignora a ordem dentro do padrão, nunca dá
    mais baldeações que o resultado exato."""
    rng = random.Random(99)
    vistos_menor = 0
    for _ in range(10):
        r = _rede_aleatoria(rng, n_paradas=20, n_padroes=12)
        gl = construir_gl(r)
        for _ in range(30):
            origem, destino = rng.sample(list(r.paradas), 2)
            t = menos_baldeacoes(gl, origem, destino)
            if t is None or not t.padroes():
                continue
            inicio = {p for y, _ in gl.proximas[origem] for p, _ in gl.embarques.get(y, ())}
            perto = {y for y, _ in gl.proximas[destino]}
            fim = {
                v
                for v, seq in enumerate(gl.paradas_do_padrao)
                if any(x in perto for x in seq[1:])
            }
            limite = min(
                (bfs(gl.grafo, s).dist[f] for s in inicio for f in fim), default=INF
            )
            assert limite <= t.baldeacoes
            vistos_menor += limite < t.baldeacoes
    # Nas redes sorteadas, o BFS comum erra para menos em algum par: a ordem importa.
    assert vistos_menor > 0
