"""Visões de grafo construídas a partir do modelo normalizado (docs/fontes/modelagem.md §3.4).

Cada visão guarda o Grafo do núcleo e os mapas entre os identificadores do GTFS e os
vértices. As visões G_L (F-BALD) e G_T (F-ESPERA-2) também herdam de Visao, mas são
definidas pelos donos dessas features.

estado: planejado
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transporte.grafo.grafo import Grafo

# Valores do parâmetro `tipo` de Grafo.adicionar_aresta usados pelas visões.
VIAGEM = "viagem"
CAMINHADA = "caminhada"
EMBARQUE = "embarque"
DESEMBARQUE = "desembarque"


@dataclass
class Visao:
    """Base das visões: um Grafo do núcleo e o nome da visão.

    Atributos:
        grafo: grafo dirigido e ponderado do núcleo (P0-GRAFO).
        nome: "G_P", "G_E", "G_L" ou "G_T".
    """

    grafo: Grafo
    nome: str


@dataclass
class VisaoGP(Visao):
    """G_P · paradas. Um vértice por parada.

    Arestas dirigidas:
        VIAGEM: parada seguinte em algum padrão; peso = tempo mediano de viagem (s).
        CAMINHADA: paradas a até Parametros.raio_caminhada_m; peso = distância / velocidade (s).

    Atributos:
        vertice_da_parada: id da parada no GTFS -> vértice.
        parada_do_vertice: vértice -> id da parada (inverso do anterior).

    Usada por F-MET, F-EFI e F-RES. Espaço O(V + E).
    """

    vertice_da_parada: dict[str, int] = field(default_factory=dict)
    parada_do_vertice: list[str] = field(default_factory=list)


@dataclass
class VisaoGE(Visao):
    """G_E · parada × linha. Um vértice por parada e um vértice de plataforma por par
    (parada, padrão).

    Arestas dirigidas:
        EMBARQUE: parada -> plataforma; peso = espera esperada (s).
        VIAGEM: plataforma -> plataforma seguinte do mesmo padrão; peso = tempo mediano (s).
        DESEMBARQUE: plataforma -> parada; peso 0.
        CAMINHADA: parada -> parada a até o raio de caminhada; peso = distância / velocidade (s).

    Trocar de linha obriga a sair da plataforma, voltar à parada e pagar um novo embarque,
    por isso um único Dijkstra soma caminhada, espera, viagem e baldeações.

    Atributos:
        vertice_da_parada: id da parada -> vértice da parada.
        plataforma: (id da parada, id do padrão) -> vértice da plataforma.
        faixa: nome da faixa horária cujas esperas estão nas arestas de embarque.

    Usada por F-ROTA, F-ESPERA e F-EFI. Espaço O(V + E).
    """

    vertice_da_parada: dict[str, int] = field(default_factory=dict)
    plataforma: dict[tuple[str, str], int] = field(default_factory=dict)
    faixa: str = ""

    def baldeacoes(self, arestas: list[int]) -> int:
        """Número de baldeações de um caminho: embarques - 1 (0 se não embarca).

        Entrada: ids das arestas do caminho, na ordem.
        Saída: inteiro >= 0.
        Complexidade: tempo O(k), k = número de arestas do caminho; espaço O(1).
        """
        raise NotImplementedError("estado: planejado")
