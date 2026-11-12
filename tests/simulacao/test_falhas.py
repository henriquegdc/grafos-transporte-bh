"""Testes da F-RES: Tarjan iterativo, eficiência global e simulação de falhas em G_P.

Gabaritos calculados à mão nos grafos pequenos; NetworkX só para comparar resultados em
grafos aleatórios (permitido em tests/, AGENTS.md §3).
"""

from __future__ import annotations

import random
from pathlib import Path
from types import SimpleNamespace

import networkx as nx
import pytest

from transporte.dados.leitor_gtfs import ler
from transporte.grafo.grafo import Grafo
from transporte.modelo.construtores import construir_gp
from transporte.modelo.visoes import CAMINHADA, VIAGEM, VisaoGP
from transporte.simulacao.falhas import (
    Falha,
    aplicar_falha,
    componentes_fortes,
    desfazer_falha,
    eficiencia_global,
    indexar_linhas,
    simular_falha,
)

REDE_TESTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"


def _grafo(n: int, arestas: list[tuple[int, int, float]]) -> Grafo:
    g = Grafo()
    for i in range(n):
        g.adicionar_vertice(str(i))
    for u, v, p in arestas:
        g.adicionar_aresta(u, v, p)
    return g


def _conjuntos(componentes: list[list[int]]) -> set[frozenset[int]]:
    return {frozenset(c) for c in componentes}


def _visao(
    paradas: list[str],
    viagens: list[tuple[str, str, float]],
    caminhadas: list[tuple[str, str, float]] = (),
) -> VisaoGP:
    """VisaoGP montada à mão; caminhada entra nos dois sentidos, como em construir_gp."""
    g = Grafo()
    visao = VisaoGP(grafo=g, nome="G_P")
    for p in paradas:
        visao.vertice_da_parada[p] = g.adicionar_vertice(p)
        visao.parada_do_vertice.append(p)
    vp = visao.vertice_da_parada
    for a, b, peso in viagens:
        g.adicionar_aresta(vp[a], vp[b], peso, VIAGEM)
    for a, b, peso in caminhadas:
        g.adicionar_aresta(vp[a], vp[b], peso, CAMINHADA)
        g.adicionar_aresta(vp[b], vp[a], peso, CAMINHADA)
    return visao


def _estado(g: Grafo) -> tuple[list[bool], list[bool]]:
    return (
        [g.vertice_ativo(v) for v in range(g.num_vertices())],
        [g.aresta_ativa(a) for a in range(g.num_arestas())],
    )


# --- componentes_fortes: gabarito à mão ------------------------------------------------


def test_grafo_vazio() -> None:
    assert componentes_fortes(Grafo()) == []


def test_vertice_sozinho() -> None:
    assert componentes_fortes(_grafo(1, [])) == [[0]]


def test_laco_nao_muda_componente() -> None:
    assert componentes_fortes(_grafo(2, [(0, 0, 1), (0, 1, 1)])) == [[1], [0]]


def test_exemplo_a_mao() -> None:
    # Ciclo 0->1->2->0, ponte 2->3, ciclo 3<->4 e o vértice 5 solto.
    g = _grafo(6, [(0, 1, 1), (1, 2, 1), (2, 0, 1), (2, 3, 1), (3, 4, 1), (4, 3, 1)])
    comps = componentes_fortes(g)
    assert _conjuntos(comps) == {frozenset({0, 1, 2}), frozenset({3, 4}), frozenset({5})}
    # Ordem topológica reversa: {3, 4} (sem saída) sai antes de {0, 1, 2}.
    pos = {v: i for i, c in enumerate(comps) for v in c}
    assert pos[3] < pos[0]


def test_aresta_de_mao_unica_nao_junta() -> None:
    assert _conjuntos(componentes_fortes(_grafo(2, [(0, 1, 1)]))) == {
        frozenset({0}),
        frozenset({1}),
    }


def test_arestas_paralelas() -> None:
    g = _grafo(2, [(0, 1, 1), (0, 1, 2), (1, 0, 1)])
    assert _conjuntos(componentes_fortes(g)) == {frozenset({0, 1})}


def test_respeita_vertice_desativado() -> None:
    g = _grafo(3, [(0, 1, 1), (1, 2, 1), (2, 0, 1)])
    g.desativar_vertice(1)
    assert _conjuntos(componentes_fortes(g)) == {frozenset({0}), frozenset({2})}


def test_respeita_aresta_desativada() -> None:
    g = _grafo(3, [(0, 1, 1), (1, 2, 1), (2, 0, 1)])
    g.desativar_aresta(2)
    assert len(componentes_fortes(g)) == 3


def test_caminho_longo_nao_estoura_recursao() -> None:
    n = 50_000
    g = _grafo(n, [(i, i + 1, 1) for i in range(n - 1)])
    assert len(componentes_fortes(g)) == n


def test_ciclo_longo_e_uma_componente() -> None:
    n = 50_000
    g = _grafo(n, [(i, (i + 1) % n, 1) for i in range(n)])
    [comp] = componentes_fortes(g)
    assert len(comp) == n


# --- componentes_fortes: comparação com NetworkX ---------------------------------------


@pytest.mark.parametrize("semente", range(40))
def test_igual_ao_networkx(semente: int) -> None:
    rng = random.Random(semente)
    n = rng.randint(1, 40)
    arestas = [
        (rng.randrange(n), rng.randrange(n), 1.0) for _ in range(rng.randint(0, 3 * n))
    ]
    g = _grafo(n, arestas)
    for v in range(n):
        if rng.random() < 0.1:
            g.desativar_vertice(v)
    for a in range(g.num_arestas()):
        if rng.random() < 0.1:
            g.desativar_aresta(a)

    ref = nx.DiGraph()
    ref.add_nodes_from(v for v in range(n) if g.vertice_ativo(v))
    for u in range(n):
        for v, _p, _a in g.vizinhos(u):
            ref.add_edge(u, v)
    esperado = {frozenset(c) for c in nx.strongly_connected_components(ref)}
    assert _conjuntos(componentes_fortes(g)) == esperado


# --- eficiencia_global -----------------------------------------------------------------


def test_eficiencia_a_mao() -> None:
    # 0 <-2-> 1 <-4-> 2. d: 0-1 = 2, 1-2 = 4, 0-2 = 6, nos dois sentidos.
    # Soma de 1/d = 2 * (1/2 + 1/4 + 1/6) = 11/6; pares ordenados = 3 * 2 = 6.
    g = _grafo(3, [(0, 1, 2), (1, 0, 2), (1, 2, 4), (2, 1, 4)])
    assert eficiencia_global(g) == pytest.approx(11 / 36)


def test_eficiencia_par_sem_caminho_soma_zero() -> None:
    # Só 0 -> 1 com peso 2: um par de 2 tem caminho. E = (1/2) / 2.
    assert eficiencia_global(_grafo(2, [(0, 1, 2)])) == pytest.approx(0.25)


def test_eficiencia_menos_de_dois_vertices() -> None:
    assert eficiencia_global(Grafo()) == 0.0
    assert eficiencia_global(_grafo(1, [])) == 0.0


def test_eficiencia_n_referencia_mantem_denominador() -> None:
    g = _grafo(3, [(0, 1, 2), (1, 0, 2), (1, 2, 4), (2, 1, 4)])
    g.desativar_vertice(2)
    # Sobram 0 <-> 1 (soma 1). Com n = 2: 1/2; com n = 3, como antes da falha: 1/6.
    assert eficiencia_global(g) == pytest.approx(0.5)
    assert eficiencia_global(g, n_referencia=3) == pytest.approx(1 / 6)


def test_eficiencia_distancia_zero_levanta() -> None:
    with pytest.raises(ValueError):
        eficiencia_global(_grafo(2, [(0, 1, 0)]))


@pytest.mark.parametrize("semente", range(15))
def test_eficiencia_igual_ao_networkx(semente: int) -> None:
    rng = random.Random(semente)
    n = rng.randint(2, 25)
    arestas = [
        (rng.randrange(n), rng.randrange(n), float(rng.randint(1, 20)))
        for _ in range(rng.randint(0, 3 * n))
    ]
    g = _grafo(n, arestas)
    ref = nx.MultiDiGraph()
    ref.add_nodes_from(range(n))
    for u, v, p in arestas:
        ref.add_edge(u, v, weight=p)
    soma = 0.0
    for o in range(n):
        for v, d in nx.single_source_dijkstra_path_length(ref, o).items():
            if v != o:
                soma += 1 / d
    assert eficiencia_global(g) == pytest.approx(soma / (n * (n - 1)))


# --- falhas em G_P ---------------------------------------------------------------------
#
# Rede da mão: linha L1 faz A -> B -> C e volta C -> B -> A; linha L2 faz B -> C -> D e
# volta D -> C -> B. B -> C e C -> B são usados pelas duas linhas. Tempos em segundos.

PARADAS = ["A", "B", "C", "D"]
VIAGENS = [
    ("A", "B", 60), ("B", "C", 60), ("C", "B", 60), ("B", "A", 60),
    ("C", "D", 60), ("D", "C", 60),
]  # fmt: skip
REDE = SimpleNamespace(
    padroes={
        "L1-ida": SimpleNamespace(linha_id="L1", paradas=("A", "B", "C")),
        "L1-volta": SimpleNamespace(linha_id="L1", paradas=("C", "B", "A")),
        "L2-ida": SimpleNamespace(linha_id="L2", paradas=("B", "C", "D")),
        "L2-volta": SimpleNamespace(linha_id="L2", paradas=("D", "C", "B")),
    }
)


def test_indexar_linhas() -> None:
    indice = indexar_linhas(REDE)
    assert indice[("A", "B")] == {"L1"}
    assert indice[("B", "C")] == {"L1", "L2"}
    assert indice[("C", "D")] == {"L2"}
    assert len(indice) == 6


def test_indexar_ignora_parada_repetida() -> None:
    rede = SimpleNamespace(padroes={"p": SimpleNamespace(linha_id="L", paradas=("A", "A", "B"))})
    assert indexar_linhas(rede) == {("A", "B"): {"L"}}


def test_falha_vazia_nao_muda_nada() -> None:
    r = simular_falha(_visao(PARADAS, VIAGENS), Falha())
    assert r.perda_eficiencia == 0.0
    assert r.paradas_isoladas == [] and r.paradas_desconectadas == []
    assert _conjuntos(r.componentes_antes) == _conjuntos(r.componentes_depois)


def test_remover_parada_central() -> None:
    # Sem B, A fica sem ida e sem volta; C <-> D continua.
    visao = _visao(PARADAS, VIAGENS)
    r = simular_falha(visao, Falha(paradas=("B",)))
    assert _conjuntos(r.componentes_antes) == {frozenset({0, 1, 2, 3})}
    assert _conjuntos(r.componentes_depois) == {frozenset({0}), frozenset({2, 3})}
    assert r.paradas_isoladas == ["A"]
    assert r.paradas_desconectadas == ["A"]
    # Antes (d em minutos): A-B 1, A-C 2, A-D 3, B-C 1, B-D 2, C-D 1, simétrico.
    # Soma de 1/d = 2 * (1 + 1/2 + 1/3 + 1 + 1/2 + 1) / 60 = 26/3/60; 12 pares.
    assert r.eficiencia_antes == pytest.approx((26 / 3) / 60 / 12)
    # Depois só C <-> D: 2/60, com o mesmo denominador de 12 pares.
    assert r.eficiencia_depois == pytest.approx((2 / 60) / 12)
    assert r.perda_eficiencia == pytest.approx(1 - 2 / (26 / 3))
    assert r.vertices_desativados == [1]


def test_remover_trecho_so_em_um_sentido() -> None:
    visao = _visao(PARADAS, VIAGENS)
    r = simular_falha(visao, Falha(trechos=(("A", "B"),)))
    # A ainda chega em B? Não: A -> B era a única saída de A. B -> A continua.
    assert r.paradas_isoladas == ["A"]
    assert len(r.arestas_desativadas) == 1
    u, v, _p, tipo = visao.grafo.aresta(r.arestas_desativadas[0])
    assert (visao.parada_do_vertice[u], visao.parada_do_vertice[v], tipo) == ("A", "B", VIAGEM)


def test_caminhada_mantem_conexao() -> None:
    # Com caminhada A <-> C, tirar B -> A não isola A: A chega a C a pé.
    visao = _visao(PARADAS, VIAGENS, caminhadas=[("A", "C", 300)])
    r = simular_falha(visao, Falha(trechos=(("B", "A"),)))
    assert r.paradas_isoladas == []
    assert r.perda_eficiencia > 0  # B -> A ficou mais longo (B -> C -> A)


def test_remover_linha_preserva_trecho_compartilhado() -> None:
    visao = _visao(PARADAS, VIAGENS)
    r = simular_falha(visao, Falha(linhas=("L1",)), indexar_linhas(REDE))
    nomes = visao.parada_do_vertice
    removidos = set()
    for a in r.arestas_desativadas:
        u, v, _p, _t = visao.grafo.aresta(a)
        removidos.add((nomes[u], nomes[v]))
    # Só os trechos exclusivos da L1; B <-> C segue com a L2.
    assert removidos == {("A", "B"), ("B", "A")}
    assert r.paradas_isoladas == ["A"]
    assert r.vertices_desativados == []


def test_remover_as_duas_linhas_tira_todas_as_viagens() -> None:
    visao = _visao(PARADAS, VIAGENS)
    r = simular_falha(visao, Falha(linhas=("L1", "L2")), indexar_linhas(REDE))
    assert len(r.arestas_desativadas) == 6
    assert r.eficiencia_depois == 0.0
    assert r.perda_eficiencia == pytest.approx(1.0)
    assert sorted(r.paradas_isoladas) == PARADAS


def test_falha_combinada() -> None:
    visao = _visao(PARADAS, VIAGENS)
    r = simular_falha(visao, Falha(paradas=("D",), trechos=(("A", "B"),)))
    assert r.vertices_desativados == [3]
    assert len(r.arestas_desativadas) == 1


def test_simulacao_desfaz_a_falha() -> None:
    visao = _visao(PARADAS, VIAGENS)
    g = visao.grafo
    g.desativar_aresta(5)  # D -> C já estava fora antes da simulação
    antes = _estado(g)
    simular_falha(visao, Falha(paradas=("B",), linhas=("L2",)), indexar_linhas(REDE))
    assert _estado(g) == antes
    assert not g.aresta_ativa(5)  # não religou o que já estava desligado


def test_aplicar_e_desfazer() -> None:
    visao = _visao(PARADAS, VIAGENS)
    antes = _estado(visao.grafo)
    vs, ars = aplicar_falha(visao, Falha(paradas=("C",)))
    assert not visao.grafo.vertice_ativo(2)
    desfazer_falha(visao, vs, ars)
    assert _estado(visao.grafo) == antes


@pytest.mark.parametrize(
    ("falha", "erro"),
    [
        (Falha(paradas=("X",)), KeyError),
        (Falha(trechos=(("A", "D"),)), KeyError),
        (Falha(paradas=("A",), trechos=(("A", "D"),)), KeyError),
        (Falha(linhas=("L9",)), KeyError),
    ],
)
def test_falha_invalida_nao_desliga_nada(falha: Falha, erro: type[Exception]) -> None:
    visao = _visao(PARADAS, VIAGENS)
    antes = _estado(visao.grafo)
    with pytest.raises(erro):
        simular_falha(visao, falha, indexar_linhas(REDE))
    assert _estado(visao.grafo) == antes


def test_linha_sem_indice_levanta() -> None:
    with pytest.raises(ValueError):
        simular_falha(_visao(PARADAS, VIAGENS), Falha(linhas=("L1",)))


def test_amostra_reprodutivel_e_mesmas_origens() -> None:
    rng = random.Random(7)
    paradas = [f"p{i}" for i in range(30)]
    viagens = [(paradas[i], paradas[i + 1], 60) for i in range(29)]
    viagens += [(rng.choice(paradas), rng.choice(paradas), 90) for _ in range(40)]
    viagens = [(a, b, p) for a, b, p in viagens if a != b]
    visao = _visao(paradas, viagens)
    f = Falha(paradas=("p10",))
    r1 = simular_falha(visao, f, amostra=8, semente=3)
    r2 = simular_falha(visao, f, amostra=8, semente=3)
    assert r1.amostra == 8
    assert r1.eficiencia_antes == r2.eficiencia_antes
    assert r1.perda_eficiencia == r2.perda_eficiencia
    assert 0.0 <= r1.perda_eficiencia <= 1.0


def test_amostra_maior_que_n_e_exata() -> None:
    visao = _visao(PARADAS, VIAGENS)
    exata = simular_falha(visao, Falha(paradas=("B",)))
    r = simular_falha(visao, Falha(paradas=("B",)), amostra=100)
    assert r.amostra is None
    assert r.eficiencia_antes == exata.eficiencia_antes


# --- integração com a rede de teste (P0-DADOS + P0-MODELO) ------------------------------


def test_rede_teste_ponta_a_ponta() -> None:
    rede = ler(REDE_TESTE)
    visao = construir_gp(rede)
    indice = indexar_linhas(rede)
    g = visao.grafo
    antes = _estado(g)

    ref = nx.DiGraph()
    ref.add_nodes_from(range(g.num_vertices()))
    for u in range(g.num_vertices()):
        for v, _p, _a in g.vizinhos(u):
            ref.add_edge(u, v)
    esperado = {frozenset(c) for c in nx.strongly_connected_components(ref)}

    for parada in rede.paradas:
        r = simular_falha(visao, Falha(paradas=(parada,)))
        assert _conjuntos(r.componentes_antes) == esperado
        assert 0.0 <= r.perda_eficiencia <= 1.0
        assert parada not in r.paradas_isoladas
    for linha in rede.linhas:
        r = simular_falha(visao, Falha(linhas=(linha,)), indice)
        assert 0.0 <= r.perda_eficiencia <= 1.0
    assert _estado(g) == antes
