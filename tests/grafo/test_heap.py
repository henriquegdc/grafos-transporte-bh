"""Testes de transporte.grafo.heap (RF-GRF-08).

Gabaritos à mão para sequências pequenas e, para sequências aleatórias com semente fixa,
comparação com `sorted`, que dá a mesma ordem esperada de (prioridade, item).
"""

from __future__ import annotations

import random

import pytest

from transporte.grafo.heap import HeapMin


def esvaziar(h: HeapMin) -> list[tuple[float, int]]:
    """Extrai tudo do heap, na ordem."""
    saida = []
    while not h.vazio():
        saida.append(h.extrair_min())
    return saida


def test_heap_novo_esta_vazio():
    h = HeapMin()
    assert h.vazio()
    assert len(h) == 0


def test_extrair_de_heap_vazio_levanta_index_error():
    with pytest.raises(IndexError):
        HeapMin().extrair_min()


def test_um_elemento():
    h = HeapMin()
    h.inserir(7.5, 3)
    assert len(h) == 1
    assert not h.vazio()
    assert h.extrair_min() == (7.5, 3)
    assert h.vazio()


def test_ordem_a_mao():
    # Inserção fora de ordem; gabarito escrito à mão.
    h = HeapMin()
    for prioridade, item in [(5, 0), (3, 1), (8, 2), (1, 3), (9, 4), (2, 5)]:
        h.inserir(prioridade, item)
    assert len(h) == 6
    assert esvaziar(h) == [(1, 3), (2, 5), (3, 1), (5, 0), (8, 2), (9, 4)]


def test_empate_sai_pelo_menor_item():
    # Decisão G6: mesma prioridade, menor item primeiro, independente da ordem de inserção.
    h = HeapMin()
    for item in [4, 1, 3, 0, 2]:
        h.inserir(10.0, item)
    assert [item for _, item in esvaziar(h)] == [0, 1, 2, 3, 4]


def test_insercao_preguicosa_mesmo_item_varias_vezes():
    # Como no Dijkstra: o vértice 2 entra com 9 e depois com 4; a entrada menor sai antes,
    # e a desatualizada (9, 2) continua no heap até ser extraída e descartada.
    h = HeapMin()
    h.inserir(9.0, 2)
    h.inserir(6.0, 1)
    h.inserir(4.0, 2)
    assert len(h) == 3
    assert esvaziar(h) == [(4.0, 2), (6.0, 1), (9.0, 2)]


def test_infinito_e_zero():
    h = HeapMin()
    h.inserir(float("inf"), 0)
    h.inserir(0.0, 1)
    h.inserir(2.5, 2)
    assert esvaziar(h) == [(0.0, 1), (2.5, 2), (float("inf"), 0)]


def test_intercalando_insercoes_e_extracoes():
    h = HeapMin()
    h.inserir(5, 0)
    h.inserir(2, 1)
    assert h.extrair_min() == (2, 1)
    h.inserir(1, 2)
    h.inserir(7, 3)
    assert h.extrair_min() == (1, 2)
    assert h.extrair_min() == (5, 0)
    h.inserir(6, 4)
    assert esvaziar(h) == [(6, 4), (7, 3)]


@pytest.mark.parametrize("semente", range(20))
def test_aleatorio_igual_a_sorted(semente):
    rng = random.Random(semente)
    pares = [
        (rng.randint(0, 50) / 2, rng.randint(0, 30)) for _ in range(rng.randint(1, 300))
    ]
    h = HeapMin()
    for p, item in pares:
        h.inserir(p, item)
    assert len(h) == len(pares)
    assert esvaziar(h) == sorted(pares)


def test_aleatorio_intercalado_igual_a_referencia():
    # Operações misturadas, conferidas contra uma lista mantida ordenada.
    rng = random.Random(42)
    h = HeapMin()
    referencia: list[tuple[float, int]] = []
    for _ in range(2000):
        if referencia and rng.random() < 0.4:
            referencia.sort()
            assert h.extrair_min() == referencia.pop(0)
        else:
            par = (float(rng.randint(0, 100)), rng.randint(0, 100))
            h.inserir(*par)
            referencia.append(par)
        assert len(h) == len(referencia)
