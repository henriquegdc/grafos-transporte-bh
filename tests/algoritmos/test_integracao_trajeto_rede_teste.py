"""Integração da F-ROTA com a leitura do GTFS (P0-DADOS) na rede de teste.

Lê `dados/rede-teste/` com `ler()`, monta o G_E com `construir_ge` e confere
`trajeto_mais_rapido` contra o `GABARITO.md`: L1 = A -> B -> C com 300 s por trecho e
partidas de A às 08:00, 08:20 e 24:10; L2 = A -> D com 480 s, de 10 em 10 minutos entre
09:00 e 10:00. Espera provisória de 300 s em todo embarque (D6).

À mão, as distâncias: A-C = 222,4 m (mesma longitude, 0,002 grau de latitude), A-D = 209 m,
A-B = B-C = B-D = 152,7 m e C-D = 305 m, fora do raio de 300 m. Com o raio padrão, andar
vence o ônibus em toda a rede; com raio de 100 m não há caminhada e o ônibus aparece.
"""

from __future__ import annotations

from dataclasses import replace
from itertools import pairwise
from pathlib import Path

import pytest

from transporte.algoritmos.trajeto import A_PE, ESPERA, ONIBUS, Trecho, trajeto_mais_rapido
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import _distancia_m, construir_ge
from transporte.modelo.parametros import Parametros

REDE_TESTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"
SEM_CAMINHADA = replace(Parametros(), raio_caminhada_m=100.0)


@pytest.fixture(scope="module")
def rede():
    return ler(REDE_TESTE)


def _padrao(rede, linha: str) -> str:
    (padrao,) = [p.id for p in rede.padroes.values() if p.linha_id == linha]
    return padrao


def _caminhada_s(rede, *paradas: str) -> float:
    total = 0.0
    for a, b in pairwise(paradas):
        pa, pb = rede.paradas[a], rede.paradas[b]
        total += _distancia_m(pa.lat, pa.lon, pb.lat, pb.lon) / 1.2
    return total


def test_onibus_direto_no_pico_da_manha(rede):
    ge = construir_ge(rede, "pico_manha", SEM_CAMINHADA)
    t = trajeto_mais_rapido(ge, "A", "C")
    l1 = _padrao(rede, "L1")
    assert t is not None
    assert t.tempo_total_s == 300 + 300 + 300
    assert t.baldeacoes == 0
    assert t.trechos == (
        Trecho(ESPERA, ("A",), 300, l1),
        Trecho(ONIBUS, ("A", "B", "C"), 600, l1),
    )
    assert t.tempo_por_tipo() == {A_PE: 0, ESPERA: 300, ONIBUS: 600}


def test_linha_sem_partida_na_faixa_nao_serve(rede):
    # L2 só parte entre 09:00 e 10:00; no pico da manhã, sem caminhada, D é inalcançável.
    ge = construir_ge(rede, "pico_manha", SEM_CAMINHADA)
    assert trajeto_mais_rapido(ge, "A", "D") is None
    # No entrepico é a L1 que não parte (08:00, 08:20 e 24:10).
    ge = construir_ge(rede, "entrepico", SEM_CAMINHADA)
    assert trajeto_mais_rapido(ge, "B", "C") is None


def test_onibus_de_frequencia_no_entrepico(rede):
    ge = construir_ge(rede, "entrepico", SEM_CAMINHADA)
    t = trajeto_mais_rapido(ge, "A", "D")
    l2 = _padrao(rede, "L2")
    assert t is not None
    assert t.tempo_total_s == 300 + 480
    assert t.trechos == (Trecho(ESPERA, ("A",), 300, l2), Trecho(ONIBUS, ("A", "D"), 480, l2))


def test_com_caminhada_andar_vence_o_onibus(rede):
    ge = construir_ge(rede, "pico_manha")
    t = trajeto_mais_rapido(ge, "A", "C")
    assert t is not None
    assert t.baldeacoes == 0
    assert len(t.trechos) == 1 and t.trechos[0].tipo == A_PE
    assert t.trechos[0].paradas == ("A", "C")
    assert t.tempo_total_s == pytest.approx(_caminhada_s(rede, "A", "C"))
    assert t.tempo_total_s < 900


def test_caminhadas_seguidas_viram_um_trecho(rede):
    # C-D passa de 300 m; o caminho a pé vai por B e sai como um trecho só.
    ge = construir_ge(rede, "pico_manha")
    t = trajeto_mais_rapido(ge, "C", "D")
    assert t is not None
    assert t.trechos == (Trecho(A_PE, ("C", "B", "D"), t.tempo_total_s),)
    assert t.tempo_total_s == pytest.approx(_caminhada_s(rede, "C", "B", "D"))


def test_origem_igual_destino_e_parada_inexistente(rede):
    ge = construir_ge(rede, "pico_manha")
    t = trajeto_mais_rapido(ge, "A", "A")
    assert t is not None and t.tempo_total_s == 0 and t.trechos == ()
    with pytest.raises(KeyError):
        trajeto_mais_rapido(ge, "A", "Z")
