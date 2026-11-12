"""Falhas e resiliência sobre G_P (F-RES: RF-RES-01, RF-RES-02, RF-RES-03).

Uma falha remove paradas, trechos ou linhas de G_P desativando vértices e arestas do núcleo
(Grafo.desativar_*), sem reconstruir o grafo. A simulação mede o grafo antes e depois e
desfaz a falha ao terminar, então a mesma VisaoGP serve para várias simulações seguidas
(o ranking da F-RES-2 depende disso).

Medidas:
    - componentes fortemente conexas (Tarjan iterativo) antes e depois (RF-RES-02);
    - paradas isoladas pela falha (ficaram sozinhas na componente) e desconectadas
      (saíram da maior componente);
    - eficiência global antes e depois e a perda relativa (RF-RES-03).

Notação: V = número de vértices, E = número de arestas, s = número de origens da eficiência.

estado: implementado
"""

from __future__ import annotations

import random
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from transporte.grafo.buscas import INF, dijkstra
from transporte.grafo.grafo import Grafo
from transporte.modelo.visoes import VIAGEM, VisaoGP

Trecho = tuple[str, str]
"""Par (parada de origem, parada de destino) de uma aresta de viagem de G_P."""


# --- RF-RES-02: componentes fortemente conexas ----------------------------------------


def componentes_fortes(g: Grafo) -> list[list[int]]:
    """Componentes fortemente conexas pelo algoritmo de Tarjan, em versão iterativa.

    Só considera vértices ativos e arestas utilizáveis (as de Grafo.vizinhos); vértice
    desativado não aparece em nenhuma componente.

    Saída: lista de componentes, cada uma uma lista de vértices. As componentes saem em
        ordem topológica reversa do grafo de componentes (a primeira não tem aresta para
        nenhuma outra), que é a ordem natural do Tarjan.
    Por que iterativo: a versão recursiva empilha uma chamada por vértice do caminho da
        DFS; em G_P real esse caminho passa de mil vértices e estoura o limite de recursão
        do Python. Aqui a pilha de chamadas é uma lista explícita.
    Casos de borda: grafo vazio devolve []; vértice sem arestas é uma componente unitária;
        laço não muda nada; arestas paralelas são tratadas como uma.
    Complexidade: tempo O(V + E): cada vértice entra uma vez na DFS e na pilha, e cada
        aresta é olhada uma vez; espaço O(V + E), contando as listas de vizinhos guardadas
        na pilha de chamadas.
    """
    n = g.num_vertices()
    indice = [-1] * n  # ordem de descoberta na DFS; -1 = não visitado
    low = [0] * n  # menor índice alcançável pela subárvore de v com uma aresta de volta
    na_pilha = [False] * n
    pilha: list[int] = []
    componentes: list[list[int]] = []
    contador = 0

    for raiz in range(n):
        if indice[raiz] != -1 or not g.vertice_ativo(raiz):
            continue
        indice[raiz] = low[raiz] = contador
        contador += 1
        pilha.append(raiz)
        na_pilha[raiz] = True
        # Cada quadro: [vértice, vizinhos, próximo vizinho a olhar].
        chamadas: list[list] = [[raiz, g.vizinhos(raiz), 0]]
        while chamadas:
            quadro = chamadas[-1]
            v, viz, i = quadro
            if i < len(viz):
                quadro[2] = i + 1
                w = viz[i][0]
                if indice[w] == -1:
                    # "Chamada recursiva": desce para w.
                    indice[w] = low[w] = contador
                    contador += 1
                    pilha.append(w)
                    na_pilha[w] = True
                    chamadas.append([w, g.vizinhos(w), 0])
                elif na_pilha[w]:
                    low[v] = min(low[v], indice[w])
                continue
            # Todos os vizinhos de v vistos: "retorno da chamada".
            chamadas.pop()
            if chamadas:
                pai = chamadas[-1][0]
                low[pai] = min(low[pai], low[v])
            if low[v] == indice[v]:
                # v é a raiz da componente: tudo acima dele na pilha é a componente.
                componente: list[int] = []
                while True:
                    w = pilha.pop()
                    na_pilha[w] = False
                    componente.append(w)
                    if w == v:
                        break
                componentes.append(componente)
    return componentes


def _maior(componentes: Sequence[list[int]]) -> set[int]:
    """Vértices da maior componente; empate fica com a primeira. Vazio se não há nenhuma."""
    if not componentes:
        return set()
    return set(max(componentes, key=len))


# --- RF-RES-03: eficiência global ------------------------------------------------------


def eficiencia_global(
    g: Grafo,
    origens: Iterable[int] | None = None,
    n_referencia: int | None = None,
) -> float:
    """Eficiência global: média de 1/d(i, j) sobre os pares ordenados i != j.

    PROVISÓRIA: a eficiência global é da F-EFI (RF-EFI-01), que ainda não publicou a
    assinatura. Esta versão segue a definição de docs/fontes/modelagem.md §3.5 e deve ser
    trocada pela da F-EFI quando ela existir (pendência no arquivo da F-RES).

    Entradas:
        g: grafo ponderado (G_P na feature); d = soma dos pesos, em segundos.
        origens: vértices de onde partem os Dijkstras. None = todos os vértices ativos
            (exata). Uma amostra dá a estimativa O(s (V + E) log V). Origem desativada
            soma 0, mas continua contando no denominador.
        n_referencia: número de vértices do denominador. None = vértices ativos agora. A
            simulação de falha passa o número de antes da falha, para que remover uma
            parada nunca aumente a eficiência (ver simular_falha).
    Saída: soma(1/d) / (s * (n_referencia - 1)), em 1/s. Par sem caminho soma 0, então o
        valor está definido em grafo desconexo. Menos de 2 vértices: 0.0.
    Casos de borda: par de vértices distintos a distância 0 levanta ValueError (1/0); em
        G_P não acontece, porque todo peso tem o piso Parametros.peso_minimo_s.
    Complexidade: tempo O(s (V + E) log V), um Dijkstra por origem; espaço O(V).
    """
    n_ativos = sum(1 for v in range(g.num_vertices()) if g.vertice_ativo(v))
    n = n_ativos if n_referencia is None else n_referencia
    lista = (
        [v for v in range(g.num_vertices()) if g.vertice_ativo(v)]
        if origens is None
        else list(origens)
    )
    # Sem origens explícitas, as n_referencia origens incluem as desativadas, que somam 0.
    s = n if origens is None else len(lista)
    if n < 2 or s == 0:
        return 0.0
    soma = 0.0
    for o in lista:
        if not g.vertice_ativo(o):
            continue
        dist = dijkstra(g, o).dist
        for v, d in enumerate(dist):
            if v == o or d == INF:
                continue
            if d == 0:
                raise ValueError(
                    f"distância 0 entre vértices distintos {o} e {v}: eficiência infinita"
                )
            soma += 1.0 / d
    return soma / (s * (n - 1))


# --- RF-RES-01: a falha ----------------------------------------------------------------


class _PadraoComLinha(Protocol):
    @property
    def linha_id(self) -> str: ...
    @property
    def paradas(self) -> Sequence[str]: ...


class _RedeComPadroes(Protocol):
    @property
    def padroes(self) -> Mapping[str, _PadraoComLinha]: ...


def indexar_linhas(rede: _RedeComPadroes) -> dict[Trecho, set[str]]:
    """Mapa trecho -> linhas que passam por ele, para remover linhas de G_P.

    G_P junta numa aresta só o mesmo trecho usado por várias linhas (construir_gp), então
    remover uma linha só pode tirar os trechos que nenhuma outra linha usa. Este índice é
    calculado uma vez por rede e reaproveitado em todas as simulações.

    Entrada: o modelo normalizado (P0-DADOS); usa só padroes[*].linha_id e .paradas.
    Casos de borda: parada repetida em sequência no padrão não gera trecho, como em
        construir_gp.
    Complexidade: tempo e espaço O(K), K = total de paradas somado sobre os padrões.
    """
    indice: dict[Trecho, set[str]] = {}
    for padrao in rede.padroes.values():
        seq = padrao.paradas
        for k in range(len(seq) - 1):
            if seq[k] != seq[k + 1]:
                indice.setdefault((seq[k], seq[k + 1]), set()).add(padrao.linha_id)
    return indice


@dataclass(frozen=True)
class Falha:
    """O que sai de operação. Os três campos podem ser combinados.

    Atributos:
        paradas: ids de paradas do GTFS; a parada sai com todas as arestas que a tocam
            (viagem e caminhada).
        trechos: pares (a, b) de paradas; sai a aresta de viagem a -> b (só nesse sentido).
            A caminhada entre a e b continua.
        linhas: ids de linhas do GTFS; saem os trechos de viagem que só essas linhas
            usam. As paradas continuam, porque outras linhas e a caminhada as atendem.
    """

    paradas: tuple[str, ...] = ()
    trechos: tuple[Trecho, ...] = ()
    linhas: tuple[str, ...] = ()


@dataclass
class ResultadoFalha:
    """Saída de simular_falha. Espaço O(V).

    Atributos:
        falha: a falha simulada.
        componentes_antes, componentes_depois: componentes fortemente conexas (listas de
            vértices de G_P), na ordem de componentes_fortes.
        paradas_isoladas: ids das paradas ativas que ficaram sozinhas na sua componente
            depois da falha e não estavam sozinhas antes: não conseguem mais ir a nenhuma
            outra parada e voltar. As paradas removidas não entram.
        paradas_desconectadas: ids das paradas ativas que estavam na maior componente
            antes e ficaram fora dela depois (inclui as isoladas que vieram da maior).
            Empate de tamanho: a maior é a primeira na ordem de componentes_fortes.
        eficiencia_antes, eficiencia_depois: eficiência global (1/s), com o mesmo
            denominador e as mesmas origens.
        perda_eficiencia: (antes - depois) / antes, entre 0 e 1; 0.0 se antes == 0.
        vertices_desativados, arestas_desativadas: o que a falha desligou (só o que estava
            ativo), já reativado ao fim da simulação.
        amostra: número de origens usadas na eficiência; None = exata.
    """

    falha: Falha
    componentes_antes: list[list[int]]
    componentes_depois: list[list[int]]
    paradas_isoladas: list[str]
    paradas_desconectadas: list[str]
    eficiencia_antes: float
    eficiencia_depois: float
    perda_eficiencia: float
    vertices_desativados: list[int] = field(default_factory=list)
    arestas_desativadas: list[int] = field(default_factory=list)
    amostra: int | None = None


def _arestas_de_viagem(visao: VisaoGP) -> dict[Trecho, list[int]]:
    """Trecho (a, b) -> ids das arestas de viagem a -> b em G_P. O(E)."""
    g = visao.grafo
    nomes = visao.parada_do_vertice
    mapa: dict[Trecho, list[int]] = {}
    for a in range(g.num_arestas()):
        u, v, _peso, tipo = g.aresta(a)
        if tipo == VIAGEM:
            mapa.setdefault((nomes[u], nomes[v]), []).append(a)
    return mapa


def aplicar_falha(
    visao: VisaoGP,
    falha: Falha,
    linhas_do_trecho: Mapping[Trecho, set[str]] | None = None,
) -> tuple[list[int], list[int]]:
    """Desativa em G_P o que a falha remove e devolve (vértices, arestas) desligados.

    Só devolve o que estava ativo e foi desligado agora, para que desfazer_falha não
    religue algo que já estava desligado antes (ex.: numa falha em sequência, F-RES-OPC).

    Entradas:
        linhas_do_trecho: saída de indexar_linhas; obrigatório se a falha tem linhas.
    Casos de borda: parada, trecho de viagem ou linha inexistentes levantam KeyError, e
        nada é desativado; linhas sem índice levantam ValueError.
    Complexidade: tempo O(E + p + t + K), p, t = paradas e trechos da falha, K = tamanho
        do índice de linhas; espaço O(E) para o mapa de trechos.
    """
    g = visao.grafo
    viagem = _arestas_de_viagem(visao)

    # Valida tudo antes de desativar qualquer coisa: falha inválida não deixa meio grafo
    # desligado.
    vertices = [visao.vertice_da_parada[p] for p in falha.paradas]
    for trecho in falha.trechos:
        if trecho not in viagem:
            raise KeyError(f"trecho de viagem inexistente em G_P: {trecho}")
    arestas = [a for trecho in falha.trechos for a in viagem[trecho]]
    if falha.linhas:
        if linhas_do_trecho is None:
            raise ValueError("falha com linhas exige linhas_do_trecho (indexar_linhas)")
        conhecidas = set().union(*linhas_do_trecho.values()) if linhas_do_trecho else set()
        for linha in falha.linhas:
            if linha not in conhecidas:
                raise KeyError(f"linha inexistente: {linha}")
        removidas = set(falha.linhas)
        for trecho, linhas in linhas_do_trecho.items():
            if linhas <= removidas and trecho in viagem:
                arestas.extend(viagem[trecho])

    desligados_v = []
    for v in vertices:
        if g.vertice_ativo(v):
            g.desativar_vertice(v)
            desligados_v.append(v)
    desligados_a = []
    for a in dict.fromkeys(arestas):  # sem repetir, na ordem
        if g.aresta_ativa(a):
            g.desativar_aresta(a)
            desligados_a.append(a)
    return desligados_v, desligados_a


def desfazer_falha(visao: VisaoGP, vertices: Iterable[int], arestas: Iterable[int]) -> None:
    """Reativa o que aplicar_falha desligou. Complexidade: O(número de itens)."""
    g = visao.grafo
    for v in vertices:
        g.reativar_vertice(v)
    for a in arestas:
        g.reativar_aresta(a)


def simular_falha(
    visao: VisaoGP,
    falha: Falha,
    linhas_do_trecho: Mapping[Trecho, set[str]] | None = None,
    amostra: int | None = None,
    semente: int = 0,
) -> ResultadoFalha:
    """Simula a falha em G_P e compara a rede antes e depois (RF-RES-01 a 03).

    Aplica a falha, mede, e desfaz ao terminar (inclusive se der erro): a visão sai como
    entrou.

    Entradas:
        visao: G_P (P0-MODELO).
        falha: paradas, trechos e linhas que saem de operação.
        linhas_do_trecho: indexar_linhas(rede); obrigatório se a falha tem linhas.
        amostra: número de origens sorteadas para a eficiência; None = exata, com todos os
            vértices ativos. As mesmas origens valem antes e depois, para a perda ser
            comparável; origem removida pela falha soma 0 depois.
        semente: semente do sorteio das origens (RNF-07, reprodutível).
    Decisão: a eficiência depois da falha usa o mesmo denominador de antes (n antes da
        falha). Renormalizar pelo n de depois faria a remoção de uma parada mal conectada
        aumentar a eficiência, porque os pares ruins dela sairiam da média; com o mesmo
        n, os pares da parada removida contam 0 e a perda nunca é negativa.
    Casos de borda: os de aplicar_falha; falha vazia dá perda 0.
    Complexidade: tempo O(s (V + E) log V) com amostra de s origens, O(V (V + E) log V)
        exata (duas eficiências), mais O(V + E) de dois Tarjan; espaço O(V + E).
    """
    g = visao.grafo
    ativos = [v for v in range(g.num_vertices()) if g.vertice_ativo(v)]
    n = len(ativos)
    if amostra is None or amostra >= n:
        origens = ativos
        amostra_usada = None
    else:
        origens = random.Random(semente).sample(ativos, amostra)
        amostra_usada = amostra

    componentes_antes = componentes_fortes(g)
    eficiencia_antes = eficiencia_global(g, origens, n)

    vertices, arestas = aplicar_falha(visao, falha, linhas_do_trecho)
    try:
        componentes_depois = componentes_fortes(g)
        eficiencia_depois = eficiencia_global(g, origens, n)
    finally:
        desfazer_falha(visao, vertices, arestas)

    nomes = visao.parada_do_vertice
    removidos = set(vertices)
    sozinhas_antes = {c[0] for c in componentes_antes if len(c) == 1}
    isoladas = sorted(
        nomes[c[0]]
        for c in componentes_depois
        if len(c) == 1 and c[0] not in sozinhas_antes
    )
    maior_depois = _maior(componentes_depois)
    desconectadas = sorted(
        nomes[v]
        for v in _maior(componentes_antes)
        if v not in maior_depois and v not in removidos
    )
    perda = (
        (eficiencia_antes - eficiencia_depois) / eficiencia_antes if eficiencia_antes else 0.0
    )
    return ResultadoFalha(
        falha=falha,
        componentes_antes=componentes_antes,
        componentes_depois=componentes_depois,
        paradas_isoladas=isoladas,
        paradas_desconectadas=desconectadas,
        eficiencia_antes=eficiencia_antes,
        eficiencia_depois=eficiencia_depois,
        perda_eficiencia=perda,
        vertices_desativados=vertices,
        arestas_desativadas=arestas,
        amostra=amostra_usada,
    )
