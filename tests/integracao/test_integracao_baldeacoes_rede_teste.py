"""Integração da F-BALD com a leitura do GTFS: dados/rede-teste pelo ler() da P0-DADOS.

Gabarito (dados/rede-teste/GABARITO.md e stops.txt): L1 faz A -> B -> C com partidas às
08:00, 08:20 e 24:10; L2 faz A -> D com frequência de 600 s entre 09:00 e 10:00. Distâncias
em linha reta (haversine): A-B 153 m, A-C 222 m, A-D 209 m, B-C 153 m, B-D 153 m e C-D
305 m, então só C e D ficam além do raio de 300 m.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from transporte.algoritmos.baldeacoes import TrechoBaldeacao, menos_baldeacoes
from transporte.algoritmos.trajeto import A_PE, ONIBUS
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.linhas import construir_gl

REDE_TESTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"


@pytest.fixture(scope="module")
def rede():
    return ler(REDE_TESTE)


def _padrao_da_linha(rede, linha: str) -> str:
    (pid,) = [p.id for p in rede.padroes.values() if p.linha_id == linha]
    return pid


def test_gl_do_dia_tem_os_dois_padroes(rede):
    gl = construir_gl(rede)
    l1, l2 = _padrao_da_linha(rede, "L1"), _padrao_da_linha(rede, "L2")
    assert sorted(gl.padrao_do_vertice) == sorted([l1, l2])
    pares = {
        (gl.padrao_do_vertice[u], gl.padrao_do_vertice[v])
        for u, v, _, _ in (gl.grafo.aresta(a) for a in range(gl.grafo.num_arestas()))
    }
    # L1 desce em B ou C, perto de A (onde L2 embarca): L1 -> L2. L2 desce em D, perto de A
    # e de B (onde L1 embarca): L2 -> L1. C (fim de L1) fica a 222 m de A: laço L1 -> L1.
    # D fica a 209 m de A: laço L2 -> L2.
    assert pares == {(l1, l2), (l2, l1), (l1, l1), (l2, l2)}


def test_faixa_separa_l1_do_pico_e_l2_do_entrepico(rede):
    l1, l2 = _padrao_da_linha(rede, "L1"), _padrao_da_linha(rede, "L2")
    assert construir_gl(rede, faixa="pico_manha").padrao_do_vertice == [l1]
    assert construir_gl(rede, faixa="entrepico").padrao_do_vertice == [l2]
    # A partida de 24:10 fica fora da noite (19h a 24h): nenhuma linha nela.
    assert construir_gl(rede, faixa="noite").padrao_do_vertice == []


def test_de_d_a_c_anda_ate_b_e_pega_l1(rede):
    # C fica a 305 m de D: não dá para ir a pé. B (153 m) é o embarque mais perto em L1.
    gl = construir_gl(rede)
    t = menos_baldeacoes(gl, "D", "C")
    l1 = _padrao_da_linha(rede, "L1")
    assert t.baldeacoes == 0
    assert t.trechos == (
        TrechoBaldeacao(A_PE, ("D", "B")),
        TrechoBaldeacao(ONIBUS, ("B", "C"), l1),
    )


def test_sem_l1_no_entrepico_nao_ha_trajeto_de_d_a_c(rede):
    gl = construir_gl(rede, faixa="entrepico")
    assert menos_baldeacoes(gl, "D", "C") is None


def test_perto_vai_a_pe(rede):
    gl = construir_gl(rede)
    assert menos_baldeacoes(gl, "A", "D").trechos == (TrechoBaldeacao(A_PE, ("A", "D")),)
