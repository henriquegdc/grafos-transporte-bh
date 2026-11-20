"""Testes da F-RES-2 (ranking de criticidade) e da F-RES-OPC (falhas em sequência).

Gabaritos à mão nos grafos pequenos; consistência com simular_falha (F-RES) em grafos
aleatórios com semente fixa.
"""

from __future__ import annotations

import random
from pathlib import Path
from types import SimpleNamespace

import pytest

from transporte.dados.leitor_gtfs import ler
from transporte.grafo.grafo import Grafo
from transporte.modelo.construtores import construir_gp
from transporte.modelo.visoes import CAMINHADA, VIAGEM, VisaoGP
from transporte.simulacao.falhas import (
    Falha,
    candidatos_criticidade,
    indexar_linhas,
    paradas_mais_centrais,
    ranking_criticidade,
    sequencia_aleatoria,
    sequencia_dirigida,
    simular_falha,
    simular_falhas,
)

REDE_TESTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"


def _visao(
    paradas: list[str],
    viagens: list[tuple[str, str, float]],
    caminhadas: list[tuple[str, str, float]] = (),
) -> VisaoGP:
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


def _ida_e_volta(pares: list[tuple[str, str]], peso: float = 60) -> list[tuple[str, str, float]]:
    return [(a, b, peso) for a, b in pares] + [(b, a, peso) for a, b in pares]


def _estado(g: Grafo) -> tuple[list[bool], list[bool]]:
    return (
        [g.vertice_ativo(v) for v in range(g.num_vertices())],
        [g.aresta_ativa(a) for a in range(g.num_arestas())],
    )


# Triângulo A-B-C, ponte C-D e ponte D-E, tudo nos dois sentidos com 60 s.
# C e D são articulações. Distâncias (em minutos): A-B, A-C, B-C, C-D, D-E = 1;
# A-D, B-D, C-E = 2; A-E, B-E = 3. Soma de 1/d por par não ordenado = 5 + 3/2 + 2/3 = 43/6.
#   sem C: sobram A-B e D-E -> 2      -> perda 1 - 12/43 = 31/43
#   sem D: sobra o triângulo -> 3     -> perda 1 - 18/43 = 25/43
#   sem A (ou B): 43/6 - 17/6 = 26/6  -> perda 17/43
#   sem E: 43/6 - 13/6 = 30/6         -> perda 13/43
PARADAS = ["A", "B", "C", "D", "E"]
ARTICULACAO = _ida_e_volta([("A", "B"), ("B", "C"), ("A", "C"), ("C", "D"), ("D", "E")])


def _rede_articulacao() -> VisaoGP:
    return _visao(PARADAS, ARTICULACAO)


# --- F-RES-2: candidatos e ranking -------------------------------------------------------


def test_paradas_mais_centrais_gabarito() -> None:
    # Intermediação: C está em A,B <-> D,E (8 pares ordenados); D em A,B,C <-> E (6).
    visao = _rede_articulacao()
    assert paradas_mais_centrais(visao, 2) == ["C", "D"]
    assert paradas_mais_centrais(visao, 0) == []
    assert len(paradas_mais_centrais(visao, 99)) == 5


def test_ranking_gabarito_articulacao_lidera() -> None:
    visao = _rede_articulacao()
    candidatos = [Falha(paradas=(p,)) for p in PARADAS]
    r = ranking_criticidade(visao, candidatos)
    assert [x.falha.paradas[0] for x in r] == ["C", "D", "A", "B", "E"]
    assert [x.perda_eficiencia for x in r] == pytest.approx(
        [31 / 43, 25 / 43, 17 / 43, 17 / 43, 13 / 43]
    )
    assert len(r[0].paradas_desconectadas) == 2  # {A, B} e {D, E}: uma delas sobra


def test_ranking_ponte_de_mao_unica_lidera() -> None:
    # A <-> B <-> C, e a única ida de C para D é o trecho C -> D (D -> C volta).
    # Sem C -> D, D fica sem entrada: perde ida de A, B e C.
    visao = _visao(
        ["A", "B", "C", "D"],
        _ida_e_volta([("A", "B"), ("B", "C")]) + [("C", "D", 60), ("D", "C", 60)],
    )
    candidatos = [Falha(trechos=(t,)) for t in [("A", "B"), ("C", "D"), ("B", "C")]]
    r = ranking_criticidade(visao, candidatos)
    # B -> C também corta A e B de D e de C: tira 4 pares (A-C, A-D, B-C, B-D), mais que
    # C -> D, que tira 3 (A-D, B-D, C-D). A -> B tira A-B, A-C e A-D.
    assert r[0].falha.trechos == (("B", "C"),)
    perdas = {x.falha.trechos[0]: x.perda_eficiencia for x in r}
    assert perdas[("B", "C")] > perdas[("C", "D")] > 0


def test_ranking_igual_a_simular_falha() -> None:
    for semente in range(6):
        rng = random.Random(semente)
        paradas = [f"p{i}" for i in range(25)]
        viagens = [(paradas[i], paradas[i + 1], 60) for i in range(24)]
        viagens += [(rng.choice(paradas), rng.choice(paradas), rng.randint(30, 300))
                    for _ in range(35)]
        visao = _visao(paradas, [(a, b, p) for a, b, p in viagens if a != b])
        candidatos = [Falha(paradas=(p,)) for p in rng.sample(paradas, 6)]
        antes = _estado(visao.grafo)
        r = ranking_criticidade(visao, candidatos, amostra=8, semente=semente)
        assert _estado(visao.grafo) == antes
        perdas = [x.perda_eficiencia for x in r]
        assert perdas == sorted(perdas, reverse=True)
        for x in r:
            s = simular_falha(visao, x.falha, amostra=8, semente=semente)
            assert x.perda_eficiencia == s.perda_eficiencia
            assert x.eficiencia_antes == s.eficiencia_antes
            assert x.paradas_desconectadas == s.paradas_desconectadas
            assert x.paradas_isoladas == s.paradas_isoladas


REDE_LINHAS = SimpleNamespace(
    padroes={
        "L1-ida": SimpleNamespace(linha_id="L1", paradas=("A", "B", "C")),
        "L1-volta": SimpleNamespace(linha_id="L1", paradas=("C", "B", "A")),
        "L2-ida": SimpleNamespace(linha_id="L2", paradas=("B", "C", "D")),
        "L2-volta": SimpleNamespace(linha_id="L2", paradas=("D", "C", "B")),
    }
)
VIAGENS_LINHAS = _ida_e_volta([("A", "B"), ("B", "C"), ("C", "D")])


def test_candidatos_paradas_e_linhas() -> None:
    visao = _visao(["A", "B", "C", "D"], VIAGENS_LINHAS)
    indice = indexar_linhas(REDE_LINHAS)
    c = candidatos_criticidade(visao, 2, indice)
    assert c == [Falha(paradas=("B",)), Falha(paradas=("C",)),
                 Falha(linhas=("L1",)), Falha(linhas=("L2",))]
    assert candidatos_criticidade(visao, 0, None) == []
    so_uma = candidatos_criticidade(visao, 0, indice, n_linhas=1, semente=3)
    assert len(so_uma) == 1 and so_uma[0].linhas[0] in {"L1", "L2"}
    assert so_uma == candidatos_criticidade(visao, 0, indice, n_linhas=1, semente=3)


def test_ranking_com_linhas() -> None:
    # L1 e L2 isolam uma ponta cada (A e D); simétrico, mesma perda. Sem B, A e C-D se
    # separam: B lidera.
    visao = _visao(["A", "B", "C", "D"], VIAGENS_LINHAS)
    indice = indexar_linhas(REDE_LINHAS)
    r = ranking_criticidade(visao, candidatos_criticidade(visao, 2, indice), indice)
    assert r[0].falha.paradas in {("B",), ("C",)}
    perdas = {x.falha: x.perda_eficiencia for x in r}
    assert perdas[Falha(linhas=("L1",))] == pytest.approx(perdas[Falha(linhas=("L2",))])


def test_ranking_vazio_e_candidato_invalido() -> None:
    visao = _rede_articulacao()
    assert ranking_criticidade(visao, []) == []
    antes = _estado(visao.grafo)
    with pytest.raises(KeyError):
        ranking_criticidade(visao, [Falha(paradas=("A",)), Falha(paradas=("X",))])
    assert _estado(visao.grafo) == antes


# --- F-RES-OPC: falhas em sequência ------------------------------------------------------


def _junta(falhas: list[Falha]) -> Falha:
    return Falha(
        paradas=tuple(p for f in falhas for p in f.paradas),
        trechos=tuple(t for f in falhas for t in f.trechos),
        linhas=tuple(linha for f in falhas for linha in f.linhas),
    )


def test_sequencia_gabarito_articulacao() -> None:
    # Tira D e depois C: depois de D, perda 25/43; depois de C também, sobra só A-B (1).
    visao = _rede_articulacao()
    passos = simular_falhas(visao, [Falha(paradas=("D",)), Falha(paradas=("C",))])
    assert [p.perda_eficiencia for p in passos] == pytest.approx([25 / 43, 1 - 6 / 43])
    assert passos[0].paradas_desconectadas == ["E"]
    assert passos[1].paradas_desconectadas == ["E"]  # {A, B} virou a maior componente
    assert passos[1].vertices_desativados == [2]  # só o que o passo desligou


def test_linhas_se_acumulam() -> None:
    # B <-> C é de L1 e L2: tirar L1 deixa o trecho; tirar L2 depois o derruba.
    visao = _visao(["A", "B", "C", "D"], VIAGENS_LINHAS)
    indice = indexar_linhas(REDE_LINHAS)
    passos = simular_falhas(visao, [Falha(linhas=("L1",)), Falha(linhas=("L2",))], indice)
    assert len(passos[0].arestas_desativadas) == 2
    assert len(passos[1].arestas_desativadas) == 4
    assert passos[1].eficiencia_depois == 0.0


@pytest.mark.parametrize("semente", range(8))
def test_final_igual_a_tudo_de_uma_vez(semente: int) -> None:
    rng = random.Random(semente)
    paradas = [f"p{i}" for i in range(20)]
    viagens = [(rng.choice(paradas), rng.choice(paradas), rng.randint(30, 300))
               for _ in range(60)]
    viagens = [(a, b, p) for a, b, p in viagens if a != b]
    visao = _visao(paradas, viagens, caminhadas=[(paradas[0], paradas[1], 200)])
    trechos = sorted({(a, b) for a, b, _ in viagens})
    falhas = [Falha(paradas=(p,)) for p in rng.sample(paradas, 3)]
    falhas += [Falha(trechos=(t,)) for t in rng.sample(trechos, 3)]
    rng.shuffle(falhas)
    antes = _estado(visao.grafo)
    passos = simular_falhas(visao, falhas, amostra=10, semente=semente)
    assert _estado(visao.grafo) == antes
    junto = simular_falha(visao, _junta(falhas), amostra=10, semente=semente)
    final = passos[-1]
    assert final.eficiencia_depois == pytest.approx(junto.eficiencia_depois)
    assert {frozenset(c) for c in final.componentes_depois} == {
        frozenset(c) for c in junto.componentes_depois
    }
    assert final.paradas_isoladas == junto.paradas_isoladas
    assert final.paradas_desconectadas == junto.paradas_desconectadas
    perdas = [p.perda_eficiencia for p in passos]
    assert perdas == sorted(perdas)  # remover mais nunca encurta caminho


def test_linhas_em_sequencia_igual_a_juntas() -> None:
    visao = _visao(["A", "B", "C", "D"], VIAGENS_LINHAS)
    indice = indexar_linhas(REDE_LINHAS)
    passos = simular_falhas(visao, [Falha(linhas=("L1",)), Falha(linhas=("L2",))], indice)
    junto = simular_falha(visao, Falha(linhas=("L1", "L2")), indice)
    assert passos[-1].perda_eficiencia == junto.perda_eficiencia == pytest.approx(1.0)


def test_sequencia_desfaz_inclusive_com_erro() -> None:
    visao = _rede_articulacao()
    g = visao.grafo
    g.desativar_aresta(0)  # já estava fora: não pode ser religada
    antes = _estado(g)
    simular_falhas(visao, [Falha(paradas=("C",)), Falha(paradas=("C", "D"))])
    assert _estado(g) == antes
    with pytest.raises(KeyError):
        simular_falhas(visao, [Falha(paradas=("C",)), Falha(paradas=("X",))])
    assert _estado(g) == antes
    assert simular_falhas(visao, []) == []


def test_dirigida_e_aleatoria() -> None:
    visao = _rede_articulacao()
    assert sequencia_dirigida(visao, 2) == [Falha(paradas=("C",)), Falha(paradas=("D",))]
    a = sequencia_aleatoria(visao, 3, semente=5)
    assert a == sequencia_aleatoria(visao, 3, semente=5)
    assert len({f.paradas for f in a}) == 3
    assert len(sequencia_aleatoria(visao, 99)) == 5
    assert sequencia_aleatoria(visao, 0) == []
    # O ataque dirigido derruba mais que qualquer sequência aleatória de 2 paradas aqui:
    # C e D são as duas articulações.
    dirigida = simular_falhas(visao, sequencia_dirigida(visao, 2))[-1].perda_eficiencia
    for s in range(10):
        aleatoria = simular_falhas(visao, sequencia_aleatoria(visao, 2, s))[-1]
        assert dirigida >= aleatoria.perda_eficiencia - 1e-12


def test_aleatoria_nao_repete_as_origens_da_amostra() -> None:
    # Com random.Random(semente) nos dois sorteios, as paradas removidas seriam as
    # primeiras origens da eficiência. Aqui, em 200 paradas, as listas diferem.
    paradas = [f"p{i}" for i in range(200)]
    visao = _visao(paradas, [(paradas[i], paradas[i + 1], 60) for i in range(199)])
    removidas = [f.paradas[0] for f in sequencia_aleatoria(visao, 5, semente=2026)]
    origens = random.Random(2026).sample(range(200), 5)
    assert removidas != [paradas[v] for v in origens]


def test_rede_teste_ranking_e_sequencia() -> None:
    rede = ler(REDE_TESTE)
    visao = construir_gp(rede)
    indice = indexar_linhas(rede)
    antes = _estado(visao.grafo)
    candidatos = candidatos_criticidade(visao, 2, indice)
    r = ranking_criticidade(visao, candidatos, indice)
    assert len(r) == len(candidatos)
    passos = simular_falhas(visao, sequencia_dirigida(visao, 2), indice)
    assert len(passos) == 2
    assert _estado(visao.grafo) == antes
