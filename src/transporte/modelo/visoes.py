"""Visões de grafo construídas a partir do modelo normalizado (docs/fontes/modelagem.md §3.4).

Cada visão guarda o Grafo do núcleo e os mapas entre os identificadores do GTFS e os
vértices. As visões G_L (F-BALD) e G_T (F-ESPERA-2) também herdam de Visao, mas são
definidas pelos donos dessas features; VisaoGL, no fim do arquivo, é da F-BALD.

estado: implementado
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

        Entrada: ids das arestas do caminho, na ordem, como devolve
            buscas.caminho_arestas.
        Saída: inteiro >= 0.
        Casos de borda: caminho vazio devolve 0; id de aresta inexistente levanta
            IndexError.
        Complexidade: tempo O(k), k = número de arestas do caminho; espaço O(1).
        """
        embarques = sum(1 for a in arestas if self.grafo.aresta(a)[3] == EMBARQUE)
        return max(0, embarques - 1)


# Tipo das arestas de G_L (F-BALD).
BALDEACAO = "baldeacao"

Transferencia = tuple[int, str, int, str]
"""(índice de desembarque em P, parada de desembarque, índice de embarque em Q, parada de
embarque): onde se troca do padrão P para o padrão Q numa aresta P -> Q de G_L."""


@dataclass
class VisaoGL(Visao):
    """G_L · linhas. Um vértice por padrão de linha (F-BALD, RF-GRF-06).

    Arestas dirigidas, todas com peso 1 e tipo BALDEACAO:
        P -> Q quando dá para descer de P numa parada x (que não seja a primeira de P) e
        embarcar em Q numa parada y (que não seja a última de Q), com x == y ou x e y a
        até o raio de caminhada. Q pode ser o próprio P (laço): descer, andar e pegar o
        mesmo padrão mais atrás também é uma baldeação.

    A aresta é dirigida porque cada padrão tem um sentido: descer na primeira parada ou
    embarcar na última não leva a lugar nenhum. A ordem dentro do padrão importa também
    para quem já está nele (só dá para descer depois de onde embarcou); por isso cada
    aresta guarda onde a troca acontece, e não só que ela existe.

    Atributos:
        vertice_do_padrao: id do padrão -> vértice.
        padrao_do_vertice: vértice -> id do padrão.
        paradas_do_padrao: vértice -> sequência de paradas do padrão.
        transferencias: id da aresta -> trocas não dominadas daquela aresta P -> Q, em
            ordem decrescente do índice de desembarque e crescente do de embarque. Uma
            troca (i, x, j, y) é dominada por outra que desce mais tarde (ou igual) em P e
            embarca mais cedo (ou igual) em Q, porque esta serve a todo passageiro que a
            primeira serve.
        proximas: id da parada -> paradas a até o raio, com a distância em metros; a
            própria parada vem primeiro, com 0.
        embarques: id da parada -> (vértice do padrão, índice da parada no padrão) para
            cada padrão que embarca ali (todas as posições, menos a última).
        faixa: faixa horária usada para filtrar os padrões, ou None se todos entram.

    Usada por F-BALD e F-BALD-2. Espaço O(V + E + T + K), com T trocas guardadas e K
    pares de paradas a até o raio.
    """

    vertice_do_padrao: dict[str, int] = field(default_factory=dict)
    padrao_do_vertice: list[str] = field(default_factory=list)
    paradas_do_padrao: list[tuple[str, ...]] = field(default_factory=list)
    transferencias: list[tuple[Transferencia, ...]] = field(default_factory=list)
    proximas: dict[str, tuple[tuple[str, float], ...]] = field(default_factory=dict)
    embarques: dict[str, tuple[tuple[int, int], ...]] = field(default_factory=dict)
    faixa: str | None = None
