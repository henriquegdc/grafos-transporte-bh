"""Integração da F-ROTA com P0-DADOS, F-ESPERA e P0-MODELO na rede de teste.

Caminho completo: `ler()` da `dados/rede-teste/`, esperas de `calcular_esperas`
(F-ESPERA), `construir_ge` e `trajeto_mais_rapido`. Respostas à mão a partir do
`GABARITO.md` da pasta: L1 = A -> B -> C, 300 s por trecho, espera de 600 s no pico da
manhã (partidas a cada 1200 s); L2 = A -> D, 480 s, espera de 300 s no entrepico.

Com raio de caminhada de 100 m nenhum par de paradas fica a pé (o par mais próximo está a
cerca de 152 m), o que obriga o ônibus. Com o raio padrão (300 m), A e C ficam a 0,002 grau
de latitude (222 m) e a caminhada direta vence o ônibus.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from transporte.algoritmos.trajeto import A_PE, ESPERA, ONIBUS, Trecho, trajeto_mais_rapido
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_ge
from transporte.modelo.parametros import Parametros
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos

REDE_TESTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"
SEM_CAMINHADA = Parametros(raio_caminhada_m=100)
M_POR_GRAU = 6_371_000.0 * math.pi / 180


@pytest.fixture(scope="module")
def rede():
    return ler(REDE_TESTE)


def _padrao(rede, linha: str) -> str:
    (padrao,) = [p.id for p in rede.padroes.values() if p.linha_id == linha]
    return padrao


def _ge(rede, faixa: str, params: Parametros):
    esperas = calcular_esperas(estimar_intervalos(rede, params))
    return construir_ge(rede, faixa, params, esperas)


def test_pico_da_manha_a_ate_c_pela_l1(rede):
    l1 = _padrao(rede, "L1")
    t = trajeto_mais_rapido(_ge(rede, "pico_manha", SEM_CAMINHADA), "A", "C")
    assert t is not None
    assert t.trechos == (
        Trecho(ESPERA, ("A",), 600, l1),
        Trecho(ONIBUS, ("A", "B", "C"), 600, l1),
    )
    assert t.tempo_total_s == 1200
    assert t.baldeacoes == 0
    assert t.tempo_por_tipo() == {A_PE: 0, ESPERA: 600, ONIBUS: 600}


def test_entrepico_a_ate_d_pela_l2(rede):
    l2 = _padrao(rede, "L2")
    t = trajeto_mais_rapido(_ge(rede, "entrepico", SEM_CAMINHADA), "A", "D")
    assert t is not None
    assert t.trechos == (
        Trecho(ESPERA, ("A",), 300, l2),
        Trecho(ONIBUS, ("A", "D"), 480, l2),
    )
    assert t.tempo_total_s == 780


def test_pico_da_manha_sem_l2_nao_chega_em_d(rede):
    # A L2 só parte a partir das 09:00, fora do pico (06h a 09h); sem caminhada, D isola.
    assert trajeto_mais_rapido(_ge(rede, "pico_manha", SEM_CAMINHADA), "A", "D") is None


def test_sem_sentido_contrario(rede):
    assert trajeto_mais_rapido(_ge(rede, "pico_manha", SEM_CAMINHADA), "C", "A") is None


def test_caminhada_direta_vence_o_onibus(rede):
    params = Parametros()
    t = trajeto_mais_rapido(_ge(rede, "pico_manha", params), "A", "C")
    assert t is not None
    ((trecho,),) = [t.trechos]
    assert trecho.tipo == A_PE
    assert trecho.paradas == ("A", "C")
    esperado = 0.002 * M_POR_GRAU / params.velocidade_caminhada_ms  # cerca de 185 s
    assert t.tempo_total_s == pytest.approx(esperado, abs=1)
    assert t.baldeacoes == 0
