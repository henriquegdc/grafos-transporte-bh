"""Testes de VisaoGE.baldeacoes (P0-MODELO): embarques - 1, ou 0 se não embarca."""

from __future__ import annotations

import pytest

from transporte.grafo.grafo import Grafo
from transporte.modelo.visoes import CAMINHADA, DESEMBARQUE, EMBARQUE, VIAGEM, VisaoGE


@pytest.fixture
def visao():
    # Paradas 0 e 1, plataformas 2 e 3. Arestas na ordem dos ids:
    # 0 embarque 0->2, 1 viagem 2->3, 2 desembarque 3->1, 3 caminhada 1->0,
    # 4 embarque 1->3.
    g = Grafo()
    for r in ("A", "B", "A@P", "B@P"):
        g.adicionar_vertice(r)
    g.adicionar_aresta(0, 2, 300, EMBARQUE)
    g.adicionar_aresta(2, 3, 100, VIAGEM)
    g.adicionar_aresta(3, 1, 0, DESEMBARQUE)
    g.adicionar_aresta(1, 0, 90, CAMINHADA)
    g.adicionar_aresta(1, 3, 300, EMBARQUE)
    return VisaoGE(grafo=g, nome="G_E")


@pytest.mark.parametrize(
    ("caminho", "esperado"),
    [
        ([], 0),  # origem == destino
        ([3], 0),  # só caminhada
        ([0, 1, 2], 0),  # um embarque
        ([0, 1, 2, 4], 1),  # dois embarques
        ([0, 1, 2, 4, 0, 4], 3),  # quatro embarques
    ],
)
def test_baldeacoes(visao, caminho, esperado):
    assert visao.baldeacoes(caminho) == esperado


def test_aresta_inexistente_levanta_index_error(visao):
    with pytest.raises(IndexError):
        visao.baldeacoes([99])
