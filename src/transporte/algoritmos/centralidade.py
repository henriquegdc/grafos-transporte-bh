"""Centralidades das paradas sobre G_P (F-MET: RF-MET-01, RF-MET-02, RF-MET-03; RNF-06).

Funciona sobre qualquer Grafo do núcleo; a feature usa G_P (docs/fontes/modelagem.md §3.4).
Respeita vértices e arestas desativados (só usa o que Grafo.vizinhos devolve), então a
F-RES pode recalcular as centralidades depois de uma falha sem reconstruir o grafo.

Notação: V = número de vértices, E = número de arestas, k = origens sorteadas.

estado: implementado
"""

from __future__ import annotations

import math
import random
from collections import deque
from collections.abc import Collection, Sequence
from dataclasses import dataclass

from transporte.grafo.grafo import Grafo
from transporte.grafo.heap import HeapMin

_INF = float("inf")


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


def _checar_tamanho(g: Grafo, valores: list) -> None:
    if len(valores) != g.num_vertices():
        raise ValueError(
            f"esperado um valor por vértice ({g.num_vertices()}), recebidos {len(valores)}"
        )


# --- RF-MET-01 ------------------------------------------------------------------------


def graus(g: Grafo, tipos: Collection[str] | None = None) -> Graus:
    """Grau de entrada e de saída de cada vértice (RF-MET-01).

    Conta arestas utilizáveis (aresta, origem e destino ativos), como Grafo.vizinhos.
    Arestas paralelas contam uma vez cada; um laço conta 1 na entrada e 1 na saída.

    Entradas:
        g: grafo (G_P na feature).
        tipos: se informado, só conta arestas desses tipos (ex.: {"viagem"} para ignorar
            a caminhada, que liga paradas vizinhas e inflaria o grau).
    Complexidade: tempo O(V + E), cada aresta é vista uma vez, a partir da origem;
        espaço O(V).
    """
    n = g.num_vertices()
    entrada = [0] * n
    saida = [0] * n
    filtro = None if tipos is None else set(tipos)
    for u in range(n):
        for v, _peso, a in g.vizinhos(u):
            if filtro is not None and g.aresta(a)[3] not in filtro:
                continue
            saida[u] += 1
            entrada[v] += 1
    return Graus(entrada, saida)


def distribuicao_graus(g: Grafo, valores: list[int]) -> dict[int, int]:
    """Distribuição de graus: grau -> quantos vértices ativos têm esse grau (RF-MET-01).

    Entradas: o grafo (para saber quais vértices estão ativos) e uma lista de graus
        indexada por vértice, como Graus.entrada ou Graus.saida.
    Saída: dicionário em ordem crescente de grau; vértices desativados não entram.
    Casos de borda: len(valores) diferente de g.num_vertices() levanta ValueError.
    Complexidade: tempo O(V + D log D), D = número de graus distintos; espaço O(D).
    """
    _checar_tamanho(g, valores)
    contagem: dict[int, int] = {}
    for v, grau in enumerate(valores):
        if g.vertice_ativo(v):
            contagem[grau] = contagem.get(grau, 0) + 1
    return {grau: contagem[grau] for grau in sorted(contagem)}


# --- RF-MET-02 ------------------------------------------------------------------------


def _adjacencia_simples(g: Grafo, ponderado: bool) -> list[list[tuple[int, float]]]:
    """Adjacência sem laços e sem arestas paralelas (decisão M3): para cada vértice, os
    vizinhos distintos com o menor peso entre as arestas paralelas.

    Montada uma vez e reaproveitada pelas V buscas do Brandes. Com ponderado=True,
    aresta de peso 0 levanta ValueError (decisão M2).
    Complexidade: tempo e espaço O(V + E).
    """
    adj: list[list[tuple[int, float]]] = []
    for u in range(g.num_vertices()):
        menor: dict[int, float] = {}
        for v, peso, a in g.vizinhos(u):
            if v == u:
                continue  # laço nunca está num caminho mínimo entre vértices distintos
            if ponderado and peso == 0:
                raise ValueError(
                    f"intermediação ponderada exige peso > 0; aresta {a} ({u} -> {v}) tem 0"
                )
            if v not in menor or peso < menor[v]:
                menor[v] = peso
        adj.append(list(menor.items()))
    return adj


def _caminhos_por_dijkstra(
    adj: list[list[tuple[int, float]]], s: int
) -> tuple[list[int], list[list[int]], list[float]]:
    """Fase 1 do Brandes com pesos: Dijkstra a partir de s que, além da distância, conta
    os caminhos mínimos (sigma) e guarda todos os predecessores em caminhos mínimos.

    Devolve (ordem, preds, sigma): ordem = vértices na ordem em que foram fechados
    (distância não decrescente). Como todo peso é > 0, quando v é fechado todos os seus
    predecessores já foram fechados antes, então sigma[v] já está completo e pode ser
    repassado aos vizinhos.
    Complexidade: tempo O((V + E) log V), com inserção preguiçosa no HeapMin; espaço O(V + E).
    """
    n = len(adj)
    dist = [_INF] * n
    sigma = [0.0] * n
    preds: list[list[int]] = [[] for _ in range(n)]
    fechado = [False] * n
    ordem: list[int] = []
    dist[s] = 0.0
    sigma[s] = 1.0
    heap = HeapMin()
    heap.inserir(0.0, s)
    while not heap.vazio():
        d, v = heap.extrair_min()
        if fechado[v]:
            continue  # entrada desatualizada da inserção preguiçosa
        fechado[v] = True
        ordem.append(v)
        for w, peso in adj[v]:
            nova = d + peso
            if nova < dist[w]:
                # Caminho estritamente melhor: descarta os predecessores antigos.
                dist[w] = nova
                sigma[w] = sigma[v]
                preds[w] = [v]
                heap.inserir(nova, w)
            elif nova == dist[w]:
                # Outro caminho mínimo até w, passando por v.
                sigma[w] += sigma[v]
                preds[w].append(v)
    return ordem, preds, sigma


def _caminhos_por_bfs(
    adj: list[list[tuple[int, float]]], s: int
) -> tuple[list[int], list[list[int]], list[float]]:
    """Fase 1 do Brandes sem pesos: BFS a partir de s contando caminhos mínimos.

    Mesmo formato de _caminhos_por_dijkstra; a ordem é a de saída da fila (por camada).
    Complexidade: tempo O(V + E); espaço O(V + E).
    """
    n = len(adj)
    dist = [-1] * n
    sigma = [0.0] * n
    preds: list[list[int]] = [[] for _ in range(n)]
    ordem: list[int] = []
    dist[s] = 0
    sigma[s] = 1.0
    fila = deque([s])
    while fila:
        v = fila.popleft()
        ordem.append(v)
        for w, _peso in adj[v]:
            if dist[w] < 0:
                dist[w] = dist[v] + 1
                fila.append(w)
            if dist[w] == dist[v] + 1:
                sigma[w] += sigma[v]
                preds[w].append(v)
    return ordem, preds, sigma


def intermediacao(
    g: Grafo, ponderado: bool = True, normalizar: bool = False
) -> list[float]:
    """Intermediação (betweenness) de cada vértice pelo algoritmo de Brandes (RF-MET-02).

    bc[v] = soma, sobre os pares ordenados (s, t) com s != v != t, da fração dos caminhos
    mínimos de s a t que passam por v. O grafo é dirigido, então (s, t) e (t, s) contam
    separados. Caminhos são sequências de vértices: arestas paralelas entre os mesmos
    vértices viram uma só, com o menor peso, e laços são ignorados.

    Para cada origem s ativa: (1) uma busca conta os caminhos mínimos sigma[v] e guarda os
    predecessores; (2) os vértices são percorridos do mais distante para o mais próximo,
    acumulando a dependência delta[v] = soma, sobre os sucessores w de v em caminhos
    mínimos, de sigma[v] / sigma[w] * (1 + delta[w]); bc[v] recebe delta[v]. Isso evita
    somar par a par, que custaria O(V^3) só para enumerar os pares.

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
    Complexidade: ponderado, tempo O(V (V + E) log V), V Dijkstras; sem pesos, tempo
        O(V (V + E)), V BFS; a fase 2 custa O(V + E) por origem nos dois casos.
        Espaço O(V + E): a adjacência simplificada e as listas de uma origem por vez.
    """
    ativos = [v for v in range(g.num_vertices()) if g.vertice_ativo(v)]
    bc, _ = _somar_dependencias(g, ativos, ponderado, quadrados=False)
    escala = _escala_normalizacao(len(ativos), normalizar)
    return [x * escala for x in bc] if escala != 1.0 else bc


def _somar_dependencias(
    g: Grafo, origens: Sequence[int], ponderado: bool, quadrados: bool
) -> tuple[list[float], list[float]]:
    """Fases 1 e 2 do Brandes a partir de cada origem dada; devolve, por vértice, a soma
    das dependências delta_s[v] sobre as origens s e, se `quadrados`, a soma dos quadrados
    (para o erro padrão da estimativa amostrada).

    Complexidade: tempo O(|origens| (V + E) log V) ponderado, O(|origens| (V + E)) sem
    pesos; espaço O(V + E).
    """
    n = g.num_vertices()
    adj = _adjacencia_simples(g, ponderado)
    fase1 = _caminhos_por_dijkstra if ponderado else _caminhos_por_bfs
    soma = [0.0] * n
    soma_q = [0.0] * n if quadrados else []
    for s in origens:
        ordem, preds, sigma = fase1(adj, s)
        delta = [0.0] * n
        # Fase 2: do mais distante para o mais próximo, cada w repassa a sua dependência
        # aos predecessores na proporção dos caminhos mínimos que vêm de cada um.
        for w in reversed(ordem):
            coef = (1.0 + delta[w]) / sigma[w]
            for v in preds[w]:
                delta[v] += sigma[v] * coef
            if w != s:
                soma[w] += delta[w]
                if quadrados:
                    soma_q[w] += delta[w] * delta[w]
    return soma, soma_q


def _escala_normalizacao(n_ativos: int, normalizar: bool) -> float:
    """1 / ((n - 1)(n - 2)) com normalizar e n > 2; senão 1 (decisão M4)."""
    if normalizar and n_ativos > 2:
        return 1.0 / ((n_ativos - 1) * (n_ativos - 2))
    return 1.0


@dataclass(frozen=True)
class EstimativaIntermediacao:
    """Intermediação estimada por amostragem de origens (RNF-06). Espaço O(V).

    Atributos:
        valores: estimativa de bc[v] para cada vértice; vértice desativado tem 0.
        erro_padrao: erro padrão da estimativa de cada vértice, na mesma escala de
            `valores`; 0 quando todas as origens entram (resultado exato).
        tamanho_amostra: k, número de origens usadas.
        tamanho_populacao: N, número de vértices ativos (origens possíveis).
        semente: semente do sorteio, para reproduzir a amostra (RNF-07).
    """

    valores: list[float]
    erro_padrao: list[float]
    tamanho_amostra: int
    tamanho_populacao: int
    semente: int

    @property
    def exata(self) -> bool:
        """True quando a amostra cobre todas as origens. O(1)."""
        return self.tamanho_amostra == self.tamanho_populacao


def estimar_intermediacao(
    g: Grafo,
    tamanho_amostra: int | None = None,
    semente: int = 0,
    ponderado: bool = True,
    normalizar: bool = False,
) -> EstimativaIntermediacao:
    """Intermediação por amostragem de origens, com erro padrão (RNF-06; Brandes e Pich).

    O Brandes exato soma, sobre todas as N origens s, a dependência delta_s[v] de cada
    vértice. Aqui só k origens, sorteadas sem reposição, entram na soma, e a estimativa é
    N vezes a média das k dependências: bc~[v] = (N / k) * soma delta_s[v]. Em média, sobre
    todas as amostras possíveis, ela é igual ao valor exato (estimador não viesado). O erro
    padrão de cada vértice é N * s_v / sqrt(k) * sqrt((N - k) / N), s_v = desvio amostral
    das k dependências de v e (N - k) / N a correção de população finita: vai a 0 quando a
    amostra cobre todas as origens.

    Entradas:
        g: grafo (G_P na feature).
        tamanho_amostra: k; None ou k >= N usa todas as origens (exato, erro 0).
        semente: semente do sorteio das origens (RNF-07).
        ponderado, normalizar: como em `intermediacao`.
    Saída: EstimativaIntermediacao.
    Casos de borda: k <= 0 levanta ValueError; com k = 1 não há variância amostral e o
        erro padrão sai como infinito (inf) em todo vértice com estimativa > 0; peso 0
        com ponderado=True levanta ValueError, como em `intermediacao`.
    Complexidade: tempo O(k (V + E) log V) ponderado, O(k (V + E)) sem pesos, mais O(V) do
        sorteio; espaço O(V + E). Com k origens, custa k / N do exato.
    """
    if tamanho_amostra is not None and tamanho_amostra <= 0:
        raise ValueError(f"tamanho_amostra deve ser positivo, recebido {tamanho_amostra}")
    ativos = [v for v in range(g.num_vertices()) if g.vertice_ativo(v)]
    populacao = len(ativos)
    if tamanho_amostra is None or tamanho_amostra >= populacao:
        origens: list[int] = ativos
    else:
        origens = sorted(random.Random(semente).sample(ativos, tamanho_amostra))
    return _estimar_por_origens(g, origens, populacao, semente, ponderado, normalizar)


def _estimar_por_origens(
    g: Grafo,
    origens: Sequence[int],
    populacao: int,
    semente: int,
    ponderado: bool,
    normalizar: bool,
) -> EstimativaIntermediacao:
    """Estimativa a partir de origens já escolhidas (separada do sorteio para os testes
    conferirem a média sobre todas as amostras possíveis). O(k (V + E) log V)."""
    k = len(origens)
    soma, soma_q = _somar_dependencias(g, origens, ponderado, quadrados=k < populacao)
    escala = _escala_normalizacao(populacao, normalizar)
    if k == populacao:
        return EstimativaIntermediacao(
            [x * escala for x in soma], [0.0] * len(soma), k, populacao, semente
        )
    fator = populacao / k * escala
    valores = [x * fator for x in soma]
    erros: list[float] = []
    fpc = (populacao - k) / populacao
    for v in range(len(soma)):
        media = soma[v] / k
        if k == 1:
            erros.append(math.inf if soma[v] > 0 else 0.0)
            continue
        # Variância amostral (n - 1); max(0, .) protege de -1e-17 por arredondamento.
        var = max(0.0, (soma_q[v] - k * media * media) / (k - 1))
        erros.append(populacao * escala * math.sqrt(var / k * fpc))
    return EstimativaIntermediacao(valores, erros, k, populacao, semente)


# --- RF-MET-03 ------------------------------------------------------------------------


def ranking(g: Grafo, valores: list[float], k: int) -> list[tuple[int, float]]:
    """As k paradas mais centrais: pares (vértice, valor) em ordem decrescente de valor
    (RF-MET-03).

    Só vértices ativos entram. Empate de valor sai pelo menor id, para o ranking ser
    determinístico.
    Casos de borda: k <= 0 devolve []; k maior que o número de vértices ativos devolve
        todos; len(valores) diferente de g.num_vertices() levanta ValueError.
    Complexidade: tempo O(V log V), pela ordenação; espaço O(V).
    """
    _checar_tamanho(g, valores)
    if k <= 0:
        return []
    candidatos = [
        (v, valores[v]) for v in range(g.num_vertices()) if g.vertice_ativo(v)
    ]
    candidatos.sort(key=lambda par: (-par[1], par[0]))
    return candidatos[:k]
