"""Centralidades das paradas sobre G_P (F-MET: RF-MET-01, RF-MET-02, RF-MET-03).

Funciona sobre qualquer Grafo do núcleo; a feature usa G_P (docs/fontes/modelagem.md §3.4).
Respeita vértices e arestas desativados (só usa o que Grafo.vizinhos devolve), então a
F-RES pode recalcular as centralidades depois de uma falha sem reconstruir o grafo.

Notação: V = número de vértices, E = número de arestas.

estado: planejado
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass

from transporte.grafo.grafo import Grafo


@dataclass
class Graus:
    """Graus de cada vértice. Espaço O(V).

    Atributos:
        entrada: entrada[v] = número de arestas utilizáveis que chegam em v.
        saida: saida[v] = número de arestas utilizáveis que saem de v.
    Vértice desativado tem grau 0 nas duas listas.
    """

    entrada: list[int]
    saida: list[int]


def graus(g: Grafo, tipos: Collection[str] | None = None) -> Graus:
    """Grau de entrada e de saída de cada vértice (RF-MET-01).

    Conta arestas utilizáveis (aresta, origem e destino ativos), como Grafo.vizinhos.
    Arestas paralelas contam uma vez cada; um laço conta 1 na entrada e 1 na saída.

    Entradas:
        g: grafo (G_P na feature).
        tipos: se informado, só conta arestas desses tipos (ex.: {"viagem"} para ignorar
            a caminhada, que liga paradas vizinhas e inflaria o grau).
    Complexidade: tempo O(V + E); espaço O(V).
    """
    raise NotImplementedError("estado: planejado")


def distribuicao_graus(g: Grafo, valores: list[int]) -> dict[int, int]:
    """Distribuição de graus: grau -> quantos vértices ativos têm esse grau (RF-MET-01).

    Entradas: o grafo (para saber quais vértices estão ativos) e uma lista de graus
        indexada por vértice, como Graus.entrada ou Graus.saida.
    Saída: dicionário em ordem crescente de grau; vértices desativados não entram.
    Casos de borda: len(valores) diferente de g.num_vertices() levanta ValueError.
    Complexidade: tempo O(V + D log D), D = número de graus distintos; espaço O(D).
    """
    raise NotImplementedError("estado: planejado")


def intermediacao(
    g: Grafo, ponderado: bool = True, normalizar: bool = False
) -> list[float]:
    """Intermediação (betweenness) de cada vértice pelo algoritmo de Brandes (RF-MET-02).

    bc[v] = soma, sobre os pares ordenados (s, t) com s != v != t, da fração dos caminhos
    mínimos de s a t que passam por v. O grafo é dirigido, então (s, t) e (t, s) contam
    separados. Caminhos são sequências de vértices: arestas paralelas entre os mesmos
    vértices viram uma só, com o menor peso, e laços são ignorados.

    Entradas:
        g: grafo (G_P na feature).
        ponderado: True usa os pesos (tempo) com um Dijkstra por origem; False conta
            arestas, com uma BFS por origem.
        normalizar: divide por (n - 1)(n - 2), n = vértices ativos, o máximo possível
            num grafo dirigido; resultado em [0, 1]. Sem efeito se n <= 2.
    Saída: lista indexada por vértice; vértice desativado tem 0.
    Casos de borda: com ponderado=True, aresta utilizável de peso 0 (fora laços) levanta
        ValueError, porque com peso 0 a contagem de caminhos mínimos do Brandes deixa de
        ser correta (ver decisão M2 no arquivo da feature).
    Complexidade: ponderado, tempo O(V (V + E) log V); sem pesos, tempo O(V (V + E));
        espaço O(V + E) nos dois casos.
    """
    raise NotImplementedError("estado: planejado")


def ranking(g: Grafo, valores: list[float], k: int) -> list[tuple[int, float]]:
    """As k paradas mais centrais: pares (vértice, valor) em ordem decrescente de valor
    (RF-MET-03).

    Só vértices ativos entram. Empate de valor sai pelo menor id, para o ranking ser
    determinístico.
    Casos de borda: k <= 0 devolve []; k maior que o número de vértices ativos devolve
        todos; len(valores) diferente de g.num_vertices() levanta ValueError.
    Complexidade: tempo O(V log V); espaço O(V).
    """
    raise NotImplementedError("estado: planejado")
