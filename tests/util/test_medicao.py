"""Testes de transporte.util.medicao (RF-AVA-01).

O relógio é trocado por um falso, de leituras conhecidas, para que média e desvio tenham
gabarito calculado à mão. Um teste final usa o relógio real, só para conferir a integração.
"""

from __future__ import annotations

import math
import statistics
import time
from collections.abc import Callable, Iterable

import pytest

from transporte.util import medicao
from transporte.util.medicao import Medicao, medir


def relogio_falso(duracoes: Iterable[float]) -> Callable[[], float]:
    """Relógio que faz cada par (início, fim) de leituras durar o próximo valor de `duracoes`."""
    leituras: list[float] = []
    agora = 0.0
    for d in duracoes:
        leituras += [agora, agora + d]
        agora += d + 100.0  # intervalo entre execuções, que não pode entrar na conta
    it = iter(leituras)
    return lambda: next(it)


@pytest.fixture
def usar_duracoes(monkeypatch: pytest.MonkeyPatch) -> Callable[[list[float]], None]:
    def aplicar(duracoes: list[float]) -> None:
        monkeypatch.setattr(medicao, "_relogio", relogio_falso(duracoes))

    return aplicar


def nada(*_args: object, **_kwargs: object) -> None:
    return None


# Gabarito à mão ---------------------------------------------------------------------------


def test_tres_execucoes_media_e_desvio_amostral(usar_duracoes):
    # Durações 1, 2, 3: média 2; desvios -1, 0, 1; soma dos quadrados 2; 2/(3-1) = 1; raiz 1.
    usar_duracoes([1.0, 2.0, 3.0])
    m = medir(nada, repeticoes=3)
    assert m == Medicao(media_s=2.0, desvio_s=1.0, repeticoes=3)


def test_oito_execucoes_divisor_n_menos_1(usar_duracoes):
    # Durações 2,4,4,4,5,5,7,9: média 40/8 = 5; quadrados 9,1,1,1,0,0,4,16 = 32.
    # Desvio amostral = raiz(32/7) ≈ 2,138 (o populacional seria raiz(32/8) = 2).
    usar_duracoes([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    m = medir(nada, repeticoes=8)
    assert m.media_s == pytest.approx(5.0)
    assert m.desvio_s == pytest.approx(math.sqrt(32 / 7))
    assert m.repeticoes == 8


def test_tempos_iguais_tem_desvio_zero(usar_duracoes):
    usar_duracoes([0.25] * 5)
    m = medir(nada)
    assert m.media_s == pytest.approx(0.25)
    assert m.desvio_s == pytest.approx(0.0)
    assert m.repeticoes == 5  # padrão do contrato


def test_intervalo_entre_execucoes_nao_e_medido(usar_duracoes):
    # O relógio falso avança 100 s entre uma execução e outra; nada disso pode aparecer.
    usar_duracoes([0.5, 0.5])
    assert medir(nada, repeticoes=2).media_s == pytest.approx(0.5)


def test_confere_com_statistics(usar_duracoes):
    duracoes = [0.013, 0.011, 0.017, 0.012, 0.015, 0.014]
    usar_duracoes(duracoes)
    m = medir(nada, repeticoes=len(duracoes))
    assert m.media_s == pytest.approx(statistics.mean(duracoes))
    assert m.desvio_s == pytest.approx(statistics.stdev(duracoes))


# Casos de borda ---------------------------------------------------------------------------


def test_uma_repeticao_tem_desvio_zero(usar_duracoes):
    usar_duracoes([0.7])
    assert medir(nada, repeticoes=1) == Medicao(media_s=0.7, desvio_s=0.0, repeticoes=1)


@pytest.mark.parametrize("repeticoes", [0, -1, -10])
def test_repeticoes_menor_que_um_falha_sem_executar(repeticoes):
    chamadas = []
    with pytest.raises(ValueError):
        medir(lambda: chamadas.append(1), repeticoes=repeticoes)
    assert chamadas == []


@pytest.mark.parametrize("repeticoes", [2.0, "5", None, True])
def test_repeticoes_nao_inteiro_falha(repeticoes):
    with pytest.raises(TypeError):
        medir(nada, repeticoes=repeticoes)


def test_excecao_da_funcao_se_propaga():
    def quebra() -> None:
        raise RuntimeError("falhou")

    with pytest.raises(RuntimeError, match="falhou"):
        medir(quebra, repeticoes=3)


# Repasse de argumentos --------------------------------------------------------------------


def test_repassa_args_e_kwargs_em_todas_as_execucoes():
    recebidos = []

    def registra(a, b, *, c):
        recebidos.append((a, b, c))

    medir(registra, 1, "x", c=[3], repeticoes=4)
    assert recebidos == [(1, "x", [3])] * 4


def test_kwargs_da_funcao_nao_colidem_com_repeticoes():
    recebidos = []
    medir(lambda **kw: recebidos.append(kw), repeticoes=2, alvo=7)
    assert recebidos == [{"alvo": 7}, {"alvo": 7}]


# Medicao ----------------------------------------------------------------------------------


def test_medicao_e_imutavel():
    m = Medicao(media_s=1.0, desvio_s=0.0, repeticoes=1)
    with pytest.raises(AttributeError):
        m.media_s = 2.0  # type: ignore[misc]


@pytest.mark.parametrize(
    ("media", "desvio", "n", "esperado"),
    [
        (0.000_000_25, 0.000_000_05, 1000, "0.250 µs ± 0.050 µs (n=1000)"),
        (0.000_999, 0.000_001, 4, "999.000 µs ± 1.000 µs (n=4)"),
        (0.012345, 0.000678, 5, "12.345 ms ± 0.678 ms (n=5)"),
        (2.5, 0.25, 3, "2.500 s ± 0.250 s (n=3)"),
        (1.0, 0.0, 1, "1.000 s ± 0.000 s (n=1)"),
    ],
)
def test_formatar(media, desvio, n, esperado):
    assert Medicao(media, desvio, n).formatar() == esperado


# Relógio real -----------------------------------------------------------------------------


def test_relogio_real_mede_pelo_menos_o_sleep():
    m = medir(time.sleep, 0.01, repeticoes=3)
    assert m.repeticoes == 3
    assert m.media_s >= 0.009  # tolerância para a resolução do relógio do sistema
    assert m.desvio_s >= 0.0
