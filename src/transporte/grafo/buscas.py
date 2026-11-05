"""BFS e Dijkstra genéricos, com reconstrução de caminho (RF-GRF-02).

Operam sobre qualquer Grafo do núcleo e respeitam vértices e arestas desativados
(só percorrem o que Grafo.vizinhos devolve). O Dijkstra usa o HeapMin próprio com
inserção preguiçosa: em vez de diminuir a chave de um vértice já no heap, insere de novo
com a distância menor e descarta, na extração, as entradas desatualizadas. O heap chega a
O(E) entradas e, como log E <= 2 log V, a complexidade continua O((V + E) log V).

Notação: V = número de vértices, E = número de arestas.

estado: planejado
"""

from __future__ import annotations

from dataclasses import dataclass

from transporte.grafo.grafo import Grafo

INF = float("inf")
"""Distância de um vértice não alcançado."""

SEM_PRED = -1
"""Valor de pred e pred_aresta na origem e nos vértices não alcançados."""


@dataclass
class Resultado:
    """Saída de uma busca a partir de uma origem. Espaço O(V).

    Atributos:
        origem: vértice de onde a busca partiu.
        dist: dist[v] = custo do melhor caminho origem -> v (soma dos pesos no Dijkstra,
            número de arestas na BFS); INF se v não foi alcançado.
        pred: pred[v] = vértice anterior a v no melhor caminho; SEM_PRED na origem e nos
            não alcançados.
        pred_aresta: pred_aresta[v] = id da aresta pred[v] -> v usada no melhor caminho;
            SEM_PRED na origem e nos não alcançados. Distingue arestas paralelas e permite
            ler o tipo de cada trecho (ex.: contar embarques em G_E).
    """

    origem: int
    dist: list[float]
    pred: list[int]
    pred_aresta: list[int]


def bfs(g: Grafo, origem: int) -> Resultado:
    """Busca em largura: caminhos com o menor número de arestas, ignorando os pesos.

    Casos de borda: origem inexistente levanta IndexError; origem desativada não alcança
        nada, nem a si mesma (todas as distâncias ficam INF).
    Complexidade: tempo O(V + E), cada vértice entra na fila uma vez e cada aresta é
        olhada uma vez; espaço O(V).
    """
    raise NotImplementedError("estado: planejado")


def dijkstra(g: Grafo, origem: int, destino: int | None = None) -> Resultado:
    """Caminhos mínimos a partir da origem, com pesos não negativos.

    Entradas:
        g: grafo do núcleo (pesos >= 0, garantidos por Grafo.adicionar_aresta).
        origem: vértice de partida.
        destino: se informado, a busca para assim que o destino é fechado; só dist[destino]
            e o caminho até ele são garantidos (vértices ainda abertos podem ter distância
            provisória maior que a real).
    Casos de borda: origem ou destino inexistentes levantam IndexError; origem desativada
        não alcança nada, nem a si mesma; empates entre caminhos de mesmo custo são
        desfeitos pela ordem do heap (menor id de vértice primeiro).
    Complexidade: tempo O((V + E) log V); espaço O(V + E), por causa das entradas
        repetidas no heap.
    """
    raise NotImplementedError("estado: planejado")


def caminho(r: Resultado, destino: int) -> list[int]:
    """Vértices do melhor caminho r.origem -> destino, na ordem, incluindo as pontas.

    Casos de borda: destino não alcançado devolve []; destino == origem alcançada devolve
        [origem].
    Complexidade: tempo e espaço O(k), k = número de vértices do caminho.
    """
    raise NotImplementedError("estado: planejado")


def caminho_arestas(r: Resultado, destino: int) -> list[int]:
    """Ids das arestas do melhor caminho r.origem -> destino, na ordem.

    É a entrada de VisaoGE.baldeacoes. Casos de borda: destino não alcançado ou igual à
        origem devolve [].
    Complexidade: tempo e espaço O(k), k = número de arestas do caminho.
    """
    raise NotImplementedError("estado: planejado")
