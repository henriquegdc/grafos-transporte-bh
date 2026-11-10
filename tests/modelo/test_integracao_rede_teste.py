"""Integração de P0-MODELO com a leitura do GTFS (P0-DADOS) na rede de teste.

Lê `dados/rede-teste/` com `ler()` e confere G_P e G_E contra o `GABARITO.md` da pasta:
L1 = A -> B -> C com 300 s por trecho e partidas de A às 08:00, 08:20 e 24:10; L2 = A -> D
com 480 s, de 10 em 10 minutos entre 09:00 e 10:00. À mão: A, B e D ficam a menos de 300 m
uns dos outros e de C só D fica fora (0,002 grau em cada eixo = 305 m), logo 5 pares de
caminhada. Enquanto `transporte.dados` não estiver na `main` (PR #42), o módulo é pulado.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from transporte.modelo.construtores import construir_ge, construir_gp
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import CAMINHADA, DESEMBARQUE, EMBARQUE, VIAGEM

leitor = pytest.importorskip("transporte.dados.leitor_gtfs")

REDE_TESTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"


@pytest.fixture(scope="module")
def rede():
    if not (REDE_TESTE / "stops.txt").exists():
        pytest.skip("dados/rede-teste ainda não está no repositório")
    return leitor.ler(REDE_TESTE)


def _padrao(rede, linha: str) -> str:
    (padrao,) = [p.id for p in rede.padroes.values() if p.linha_id == linha]
    return padrao


def _arestas(visao, tipo: str) -> dict[tuple[str, str], float]:
    """Arestas de um tipo como {(rótulo de origem, rótulo de destino): peso}."""
    g = visao.grafo
    saida = {}
    for a in range(g.num_arestas()):
        u, v, peso, t = g.aresta(a)
        if t == tipo:
            saida[(g.rotulo(u), g.rotulo(v))] = peso
    return saida


def test_rede_de_teste_atende_o_protocolo(rede):
    assert rede.dia == "2026-11-04"
    assert set(rede.paradas) == {"A", "B", "C", "D"}
    l1, l2 = _padrao(rede, "L1"), _padrao(rede, "L2")
    assert rede.padroes[l1].paradas == ("A", "B", "C")
    assert rede.padroes[l2].paradas == ("A", "D")
    assert len(rede.viagens[l1]) == 3
    assert len(rede.viagens[l2]) == 6  # frequência expandida: 09:00 a 09:50


def test_gp_da_rede_de_teste(rede):
    gp = construir_gp(rede)
    g = gp.grafo
    assert g.num_vertices() == 4
    v = gp.vertice_da_parada
    viagem = {
        (u, w): peso
        for a in range(g.num_arestas())
        for u, w, peso, t in [g.aresta(a)]
        if t == VIAGEM
    }
    assert viagem == {
        (v["A"], v["B"]): 300,
        (v["B"], v["C"]): 300,
        (v["A"], v["D"]): 480,
    }
    assert len(_arestas(gp, CAMINHADA)) == 10  # 5 pares, nos dois sentidos
    assert g.num_arestas() == 13


def test_ge_pico_da_manha_so_embarca_na_l1(rede):
    params = Parametros()
    ge = construir_ge(rede, "pico_manha")
    l1, l2 = _padrao(rede, "L1"), _padrao(rede, "L2")
    assert set(ge.plataforma) == {("A", l1), ("B", l1), ("C", l1), ("A", l2), ("D", l2)}
    g = ge.grafo
    assert g.num_vertices() == 9

    def rotulo(parada: str, padrao: str | None = None) -> str:
        if padrao is None:
            return g.rotulo(ge.vertice_da_parada[parada])
        return g.rotulo(ge.plataforma[(parada, padrao)])

    # Partidas da L1 às 08:00 e 08:20; a L2 só começa às 09:00. Sem embarque em C (D9).
    assert _arestas(ge, EMBARQUE) == {
        (rotulo("A"), rotulo("A", l1)): params.espera_padrao_s,
        (rotulo("B"), rotulo("B", l1)): params.espera_padrao_s,
    }
    assert _arestas(ge, VIAGEM) == {
        (rotulo("A", l1), rotulo("B", l1)): 300,
        (rotulo("B", l1), rotulo("C", l1)): 300,
        (rotulo("A", l2), rotulo("D", l2)): 480,
    }
    assert _arestas(ge, DESEMBARQUE) == {
        (rotulo("B", l1), rotulo("B")): 0,
        (rotulo("C", l1), rotulo("C")): 0,
        (rotulo("D", l2), rotulo("D")): 0,
    }
    assert len(_arestas(ge, CAMINHADA)) == 10
    assert g.num_arestas() == 18


def test_ge_entrepico_so_embarca_na_l2(rede):
    ge = construir_ge(rede, "entrepico")
    l2 = _padrao(rede, "L2")
    g = ge.grafo
    embarques = _arestas(ge, EMBARQUE)
    assert list(embarques) == [
        (g.rotulo(ge.vertice_da_parada["A"]), g.rotulo(ge.plataforma[("A", l2)]))
    ]


def test_ge_noite_fica_sem_embarque(rede):
    # A partida das 24:10 da L1 cai depois do fim da faixa da noite (24h).
    assert _arestas(construir_ge(rede, "noite"), EMBARQUE) == {}
