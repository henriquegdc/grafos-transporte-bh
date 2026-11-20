"""Integração da F-BALD-2 com a leitura do GTFS: dados/rede-teste pelo ler() da P0-DADOS.

G_E e G_L da mesma faixa, montadas da mesma Rede, com as esperas da F-ESPERA, como faz a
página. Gabarito (dados/rede-teste/GABARITO.md e stops.txt): na faixa entrepico (09h a 16h)
só circula a L2 (A -> D, 480 s, espera H/2 = 300 s); C e D ficam a 305 m, além do raio,
mas C-B e B-D têm 153 m cada. A rede não tem troca de ônibus entre linhas na mesma faixa,
então aqui se confere o caminho dos dados reais e as propriedades em todos os pares.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path

import pytest

from transporte.algoritmos.comparacao_baldeacoes import comparar_baldeacoes
from transporte.algoritmos.trajeto import A_PE, ONIBUS
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_ge
from transporte.modelo.linhas import construir_gl
from transporte.modelo.parametros import Parametros
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos

REDE_TESTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"


@pytest.fixture(scope="module")
def rede():
    return ler(REDE_TESTE)


def _visoes(rede, faixa):
    params = Parametros()
    esperas = calcular_esperas(estimar_intervalos(rede, params))
    return (
        construir_ge(rede, faixa, params=params, esperas=esperas),
        construir_gl(rede, params, faixa=faixa),
    )


def test_c_para_d_no_entrepico(rede):
    ge, gl = _visoes(rede, "entrepico")
    c = comparar_baldeacoes(ge, gl, "C", "D")
    # Mais rápido: a pé por B (153 + 153 m, cerca de 255 s), sem ônibus.
    assert [t.tipo for t in c.mais_rapido.trechos] == [A_PE]
    assert c.mais_rapido.trechos[0].paradas == ("C", "B", "D")
    assert c.mais_rapido.tempo_total_s == pytest.approx(306 / 1.2, rel=0.01)
    # Menos baldeações na G_L: a pé até A (uma caminhada de até 300 m) e a L2 até D.
    assert [t.tipo for t in c.menos_baldeacoes.trechos] == [A_PE, ONIBUS]
    assert c.menos_baldeacoes.baldeacoes == 0
    assert c.rapido_com_menos_baldeacoes is c.mais_rapido
    assert (c.tempo_a_mais_s, c.baldeacoes_evitadas) == (0.0, 0)


@pytest.mark.parametrize("faixa", [f.nome for f in Parametros().faixas])
def test_todos_os_pares_de_todas_as_faixas(rede, faixa):
    ge, gl = _visoes(rede, faixa)
    for o, d in product(rede.paradas, repeat=2):
        c = comparar_baldeacoes(ge, gl, o, d)  # a G_L cabe no G_E: não levanta
        if c is None:
            continue
        assert c.tempo_a_mais_s >= 0.0 and c.baldeacoes_evitadas >= 0
        assert c.rapido_com_menos_baldeacoes.baldeacoes <= c.menos_baldeacoes.baldeacoes
