"""Comunidades de paradas por propagação de rótulos (F-MET-OPC: RF-MET-06).

Funciona sobre qualquer Grafo do núcleo; a feature usa G_P (docs/fontes/modelagem.md §3.5)
tratado como não dirigido: u e v são vizinhos se há aresta utilizável u -> v ou v -> u.
Comunidade é um grupo de paradas mais ligadas entre si do que com o resto da rede; a
propagação de rótulos (Raghavan, Albert e Kumara, 2007) não precisa saber o número de
grupos de antemão. A modularidade mede a qualidade da partição encontrada.

Notação: V = número de vértices, E = número de arestas.

estado: implementado
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass

from transporte.grafo.grafo import Grafo

SEM_COMUNIDADE = -1
MAX_ITER_PADRAO = 100


@dataclass(frozen=True)
class Comunidades:
    """Partição dos vértices ativos em comunidades. Espaço O(V).

    Atributos:
        rotulos: rotulos[v] = comunidade de v, numeradas 0, 1, ... pela ordem do menor
            vértice de cada uma; SEM_COMUNIDADE (-1) para vértice desativado.
        quantidade: número de comunidades (vértice isolado é uma comunidade sozinho).
        iteracoes: passadas completas pelos vértices até parar.
        convergiu: True se parou porque nenhum rótulo mudou; False se parou em max_iter.
        semente: semente da ordem de visita (RNF-07).
    """

    rotulos: list[int]
    quantidade: int
    iteracoes: int
    convergiu: bool
    semente: int

    def tamanhos(self) -> list[int]:
        """tamanhos[c] = número de vértices da comunidade c. O(V)."""
        contagem = [0] * self.quantidade
        for c in self.rotulos:
            if c != SEM_COMUNIDADE:
                contagem[c] += 1
        return contagem


def vizinhanca_nao_dirigida(g: Grafo) -> list[list[int]]:
    """Vizinhos distintos de cada vértice com as arestas tratadas como não dirigidas.

    Ignora laços, arestas paralelas e o sentido; só arestas utilizáveis (Grafo.vizinhos),
    então vértice desativado fica sem vizinhos e não aparece na lista de ninguém. A lista
    de cada vértice sai em ordem crescente, para o resultado não depender da ordem de
    inserção das arestas.
    Complexidade: tempo O(V + E log E) no pior caso, pela ordenação das listas; espaço
        O(V + E).
    """
    n = g.num_vertices()
    conjuntos: list[set[int]] = [set() for _ in range(n)]
    for u in range(n):
        for v, _peso, _a in g.vizinhos(u):
            if v != u:
                conjuntos[u].add(v)
                conjuntos[v].add(u)
    return [sorted(c) for c in conjuntos]


def propagar_rotulos(
    g: Grafo, semente: int = 0, max_iter: int = MAX_ITER_PADRAO
) -> Comunidades:
    """Comunidades por propagação de rótulos assíncrona (RF-MET-06).

    Cada vértice ativo começa com o próprio rótulo. A cada iteração, os vértices são
    visitados numa ordem embaralhada com random.Random(semente), e cada um adota o rótulo
    mais frequente entre os vizinhos (não dirigido, sem peso), já com as mudanças feitas
    nesta mesma iteração. Empate: se o rótulo atual está entre os mais frequentes, ele
    fica (critério de parada de Raghavan et al., que evita oscilar entre rótulos
    empatados); senão vence o menor rótulo. Para quando uma iteração inteira não muda
    nenhum rótulo ou depois de max_iter iterações. Com a mesma semente, o resultado é
    sempre o mesmo.

    Entradas:
        g: grafo (G_P na feature); pesos e sentido são ignorados.
        semente: semente da ordem de visita.
        max_iter: limite de iterações (>= 1).
    Saída: Comunidades com os rótulos renumerados a partir de 0.
    Casos de borda: max_iter < 1 levanta ValueError; grafo sem vértices ativos dá 0
        comunidades; vértice isolado fica sozinho.
    Complexidade: tempo O(V + E log E) para a vizinhança mais O(V + E) por iteração (cada
        vértice conta os rótulos dos vizinhos uma vez); espaço O(V + E).
    """
    if max_iter < 1:
        raise ValueError(f"max_iter deve ser >= 1, recebido {max_iter}")
    viz = vizinhanca_nao_dirigida(g)
    n = g.num_vertices()
    ativos = [v for v in range(n) if g.vertice_ativo(v)]
    rotulo = list(range(n))
    rng = random.Random(semente)
    ordem = list(ativos)
    iteracoes = 0
    convergiu = False
    while iteracoes < max_iter:
        iteracoes += 1
        rng.shuffle(ordem)
        mudou = False
        for v in ordem:
            if not viz[v]:
                continue
            frequencia: dict[int, int] = {}
            for w in viz[v]:
                frequencia[rotulo[w]] = frequencia.get(rotulo[w], 0) + 1
            maior = max(frequencia.values())
            if frequencia.get(rotulo[v], 0) == maior:
                continue
            rotulo[v] = min(r for r, f in frequencia.items() if f == maior)
            mudou = True
        if not mudou:
            convergiu = True
            break
    return _renumerar(n, ativos, rotulo, iteracoes, convergiu, semente)


def _renumerar(
    n: int,
    ativos: Sequence[int],
    rotulo: list[int],
    iteracoes: int,
    convergiu: bool,
    semente: int,
) -> Comunidades:
    """Troca os rótulos finais por 0, 1, ... na ordem do menor vértice de cada comunidade.
    O(V)."""
    novo: dict[int, int] = {}
    rotulos = [SEM_COMUNIDADE] * n
    for v in ativos:  # ativos está em ordem crescente
        rotulos[v] = novo.setdefault(rotulo[v], len(novo))
    return Comunidades(rotulos, len(novo), iteracoes, convergiu, semente)


def modularidade(g: Grafo, rotulos: Sequence[int]) -> float:
    """Modularidade de Newman da partição, com G tratado como não dirigido e sem pesos.

    Q = soma, sobre as comunidades c, de L_c / m - (d_c / 2m)^2, em que m = número de
    arestas não dirigidas distintas (de vizinhanca_nao_dirigida), L_c = arestas com as duas
    pontas em c e d_c = soma dos graus dos vértices de c. Q próximo de 0: as ligações
    internas são as esperadas ao acaso; quanto maior (até 1), mais separadas as
    comunidades. É o mesmo valor de nx.community.modularity no grafo não dirigido simples.

    Entradas: o grafo e um rótulo por vértice (como Comunidades.rotulos); vértice com
        rótulo SEM_COMUNIDADE (ou desativado) não entra.
    Casos de borda: len(rotulos) diferente de g.num_vertices() levanta ValueError; grafo
        sem arestas dá 0.
    Complexidade: tempo O(V + E log E), dominado pela vizinhança; espaço O(V + E).
    """
    n = g.num_vertices()
    if len(rotulos) != n:
        raise ValueError(f"esperado um rótulo por vértice ({n}), recebidos {len(rotulos)}")
    viz = vizinhanca_nao_dirigida(g)

    def valido(v: int) -> bool:
        return rotulos[v] != SEM_COMUNIDADE and g.vertice_ativo(v)

    m = 0
    internas: dict[int, int] = {}
    graus: dict[int, int] = {}
    for u in range(n):
        if not valido(u):
            continue
        for v in viz[u]:
            if not valido(v):
                continue
            graus[rotulos[u]] = graus.get(rotulos[u], 0) + 1
            if u < v:
                m += 1
                if rotulos[u] == rotulos[v]:
                    internas[rotulos[u]] = internas.get(rotulos[u], 0) + 1
    if m == 0:
        return 0.0
    return sum(internas.get(c, 0) / m - (d / (2 * m)) ** 2 for c, d in graus.items())
