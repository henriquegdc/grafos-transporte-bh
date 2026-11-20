"""Falhas e resiliência sobre G_P (F-RES: RF-RES-01 a 03; F-RES-2: RF-RES-04;
F-RES-OPC: RF-RES-05).

Uma falha remove paradas, trechos ou linhas de G_P desativando vértices e arestas do núcleo
(Grafo.desativar_*), sem reconstruir o grafo. A simulação mede o grafo antes e depois e
desfaz a falha ao terminar, então a mesma VisaoGP serve para várias simulações seguidas
(o ranking da F-RES-2 depende disso).

Medidas:
    - componentes fortemente conexas (Tarjan iterativo) antes e depois (RF-RES-02);
    - paradas isoladas pela falha (ficaram sozinhas na componente) e desconectadas
      (saíram da maior componente);
    - eficiência global antes e depois e a perda relativa (RF-RES-03), com a
      `eficiencia_global` da F-EFI (transporte.algoritmos.eficiencia).

Notação: V = número de vértices, E = número de arestas, s = número de origens da eficiência.

estado: implementado
"""

from __future__ import annotations

import random
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from transporte.algoritmos.centralidade import estimar_intermediacao, ranking
from transporte.algoritmos.eficiencia import eficiencia_global
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
    base = _linha_de_base(visao, amostra, semente)
    vertices, arestas = aplicar_falha(visao, falha, linhas_do_trecho)
    try:
        return _comparar(visao, base, falha, vertices, arestas, set(vertices))
    finally:
        desfazer_falha(visao, vertices, arestas)


@dataclass
class _Base:
    """Estado da rede antes das falhas: origens sorteadas, n e as medidas de antes."""

    origens: list[int]
    n: int
    amostra: int | None
    componentes: list[list[int]]
    eficiencia: float


def _linha_de_base(visao: VisaoGP, amostra: int | None, semente: int) -> _Base:
    """Sorteia as origens e mede componentes e eficiência antes de qualquer falha.

    Complexidade: O(V + E) do Tarjan mais s Dijkstras.
    """
    g = visao.grafo
    ativos = [v for v in range(g.num_vertices()) if g.vertice_ativo(v)]
    n = len(ativos)
    if amostra is None or amostra >= n:
        origens, amostra_usada = ativos, None
    else:
        origens, amostra_usada = random.Random(semente).sample(ativos, amostra), amostra
    return _Base(origens, n, amostra_usada, componentes_fortes(g),
                 eficiencia_global(g, origens, n))


def _comparar(
    visao: VisaoGP,
    base: _Base,
    falha: Falha,
    vertices: list[int],
    arestas: list[int],
    removidos: set[int],
) -> ResultadoFalha:
    """Mede o grafo com a falha já aplicada e compara com a linha de base.

    `removidos` são todos os vértices fora de operação desde a base (numa sequência,
    inclui os dos passos anteriores). Complexidade: O(V + E) mais s Dijkstras.
    """
    g = visao.grafo
    componentes_depois = componentes_fortes(g)
    eficiencia_depois = eficiencia_global(g, base.origens, base.n)
    nomes = visao.parada_do_vertice
    sozinhas_antes = {c[0] for c in base.componentes if len(c) == 1}
    isoladas = sorted(
        nomes[c[0]]
        for c in componentes_depois
        if len(c) == 1 and c[0] not in sozinhas_antes
    )
    maior_depois = _maior(componentes_depois)
    desconectadas = sorted(
        nomes[v]
        for v in _maior(base.componentes)
        if v not in maior_depois and v not in removidos
    )
    antes = base.eficiencia
    perda = (antes - eficiencia_depois) / antes if antes else 0.0
    return ResultadoFalha(
        falha=falha,
        componentes_antes=base.componentes,
        componentes_depois=componentes_depois,
        paradas_isoladas=isoladas,
        paradas_desconectadas=desconectadas,
        eficiencia_antes=antes,
        eficiencia_depois=eficiencia_depois,
        perda_eficiencia=perda,
        vertices_desativados=vertices,
        arestas_desativadas=arestas,
        amostra=base.amostra,
    )


# --- RF-RES-04: ranking de criticidade (F-RES-2) -------------------------------------


def paradas_mais_centrais(
    visao: VisaoGP,
    n: int,
    amostra_intermediacao: int | None = None,
    semente: int = 0,
) -> list[str]:
    """As n paradas de maior intermediação ponderada em G_P (F-MET), da maior para a menor.

    Entradas:
        n: quantas paradas; n <= 0 devolve [].
        amostra_intermediacao: origens do Brandes amostrado (estimar_intermediacao);
            None = exato, O(V (V + E) log V), cerca de 40 min no G_P real.
        semente: semente do sorteio das origens do Brandes.
    Empate: menor vértice primeiro (ranking da F-MET), então a saída é determinística.
    Complexidade: tempo O(k (V + E) log V + V log V), k = origens do Brandes; espaço
        O(V + E).
    """
    if n <= 0:
        return []
    est = estimar_intermediacao(visao.grafo, amostra_intermediacao, semente=semente)
    return [visao.parada_do_vertice[v] for v, _ in ranking(visao.grafo, est.valores, n)]


def candidatos_criticidade(
    visao: VisaoGP,
    n_paradas: int,
    linhas_do_trecho: Mapping[Trecho, set[str]] | None = None,
    n_linhas: int | None = None,
    amostra_intermediacao: int | None = None,
    semente: int = 0,
) -> list[Falha]:
    """Falhas candidatas do ranking: as n_paradas mais centrais e as linhas (RF-RES-04).

    Simular todas as paradas custaria V simulações; a intermediação (F-MET) escolhe as que
    mais caminhos mínimos atravessam, que são as suspeitas naturais. As linhas são poucas
    (centenas), então entram todas, ou uma amostra sorteada se n_linhas for menor.

    Entradas:
        n_paradas: paradas candidatas (0 = nenhuma).
        linhas_do_trecho: indexar_linhas(rede); None = nenhuma linha candidata.
        n_linhas: None = todas as linhas do índice; senão, n_linhas sorteadas com a semente.
        amostra_intermediacao, semente: como em paradas_mais_centrais.
    Saída: uma Falha por candidato, paradas primeiro e depois linhas em ordem de id.
    Complexidade: a de paradas_mais_centrais mais O(K + L log L), L = linhas.
    """
    falhas = [
        Falha(paradas=(p,))
        for p in paradas_mais_centrais(visao, n_paradas, amostra_intermediacao, semente)
    ]
    if linhas_do_trecho:
        linhas = sorted(set().union(*linhas_do_trecho.values()))
        if n_linhas is not None and n_linhas < len(linhas):
            linhas = sorted(random.Random(semente).sample(linhas, max(0, n_linhas)))
        falhas += [Falha(linhas=(linha,)) for linha in linhas]
    return falhas


def ranking_criticidade(
    visao: VisaoGP,
    candidatos: Sequence[Falha],
    linhas_do_trecho: Mapping[Trecho, set[str]] | None = None,
    amostra: int | None = None,
    semente: int = 0,
) -> list[ResultadoFalha]:
    """Ordena as falhas candidatas pela perda de eficiência que causam (RF-RES-04).

    Cada candidato é simulado sozinho a partir da rede intacta, com as mesmas origens
    sorteadas (mesma amostra e semente) e o mesmo denominador, então as perdas são
    comparáveis entre si e cada uma é igual à de simular_falha com os mesmos parâmetros.
    A linha de base (componentes e eficiência antes) é medida uma vez só, não uma por
    candidato: o ranking custa c + 1 eficiências, não 2c.

    Entradas: candidatos (ex.: candidatos_criticidade); o resto como em simular_falha.
    Saída: um ResultadoFalha por candidato, em ordem decrescente de perda; empate pela
        quantidade de paradas desconectadas (mais primeiro) e depois pela ordem de
        entrada (ordenação estável).
    Casos de borda: lista vazia devolve []; candidato inválido levanta o erro de
        aplicar_falha e a visão volta ao estado de entrada.
    Complexidade: tempo O((c + 1) s (V + E) log V + c (V + E)), c candidatos e s origens
        (s = V sem amostra); espaço O(c V) pelas componentes guardadas em cada resultado.
    """
    if not candidatos:
        return []
    base = _linha_de_base(visao, amostra, semente)
    resultados = []
    for falha in candidatos:
        vertices, arestas = aplicar_falha(visao, falha, linhas_do_trecho)
        try:
            resultados.append(_comparar(visao, base, falha, vertices, arestas, set(vertices)))
        finally:
            desfazer_falha(visao, vertices, arestas)
    resultados.sort(key=lambda r: (-r.perda_eficiencia, -len(r.paradas_desconectadas)))
    return resultados


# --- RF-RES-05: falhas múltiplas e em sequência (F-RES-OPC) ------------------------------


def simular_falhas(
    visao: VisaoGP,
    falhas: Sequence[Falha],
    linhas_do_trecho: Mapping[Trecho, set[str]] | None = None,
    amostra: int | None = None,
    semente: int = 0,
) -> list[ResultadoFalha]:
    """Aplica as falhas uma depois da outra e mede a rede depois de cada passo (RF-RES-05).

    O passo k compara a rede intacta com a rede sem as falhas 0..k (efeito acumulado),
    sempre com as mesmas origens e o mesmo denominador. Ao terminar (inclusive com erro),
    desfaz tudo na ordem inversa: a visão sai como entrou.

    Decisão: as linhas se acumulam. Um trecho usado pelas linhas L1 e L2 continua depois
        que L1 falha, mas cai quando L2 também falha, porque nenhuma linha restante o
        atende. Por isso o passo k aplica as paradas e trechos da falha k junto com todas
        as linhas que falharam até ali, e o estado final é igual ao de uma falha única que
        junta todas (testado).
    Saída: um ResultadoFalha por passo; nele `falha` é a falha do passo,
        vertices_desativados e arestas_desativadas são o que o passo desligou a mais, e
        isoladas, desconectadas e perda são acumuladas desde a rede intacta.
    Casos de borda: lista vazia devolve []; falha inválida levanta o erro de aplicar_falha
        e desfaz os passos anteriores.
    Complexidade: tempo O((k + 1) s (V + E) log V + k (V + E + K)), k passos, s origens;
        espaço O(k V) pelas componentes de cada passo.
    """
    if not falhas:
        return []
    base = _linha_de_base(visao, amostra, semente)
    desligados: list[tuple[list[int], list[int]]] = []
    removidos: set[int] = set()
    linhas: dict[str, None] = {}
    resultados = []
    try:
        for falha in falhas:
            linhas.update(dict.fromkeys(falha.linhas))
            efetiva = Falha(falha.paradas, falha.trechos, tuple(linhas))
            vertices, arestas = aplicar_falha(visao, efetiva, linhas_do_trecho)
            desligados.append((vertices, arestas))
            removidos.update(vertices)
            resultados.append(_comparar(visao, base, falha, vertices, arestas, removidos))
    finally:
        for vertices, arestas in reversed(desligados):
            desfazer_falha(visao, vertices, arestas)
    return resultados


def sequencia_dirigida(
    visao: VisaoGP, k: int, amostra_intermediacao: int | None = None, semente: int = 0
) -> list[Falha]:
    """Ataque dirigido: as k paradas de maior intermediação, da maior para a menor.

    Decisão: a intermediação é calculada uma vez, na rede intacta, e não recalculada a
        cada remoção; recalcular custaria k Brandes. Complexidade: a de
        paradas_mais_centrais.
    """
    return [Falha(paradas=(p,)) for p in paradas_mais_centrais(
        visao, k, amostra_intermediacao, semente)]


def sequencia_aleatoria(visao: VisaoGP, k: int, semente: int = 0) -> list[Falha]:
    """Falhas aleatórias: k paradas ativas sorteadas sem reposição com a semente.

    Decisão: o sorteio usa um gerador derivado da semente (texto "sequencia_aleatoria:"
        + semente), não random.Random(semente). Com a mesma semente da eficiência, as k
        paradas sorteadas seriam exatamente as k primeiras origens da amostra (mesma lista
        de ativos, mesmo gerador), e a remoção "aleatória" derrubaria as próprias origens.
    Casos de borda: k maior que o número de paradas ativas usa todas; k <= 0 devolve [].
    Complexidade: O(V).
    """
    g = visao.grafo
    ativos = [v for v in range(g.num_vertices()) if g.vertice_ativo(v)]
    k = max(0, min(k, len(ativos)))
    sorteados = random.Random(f"sequencia_aleatoria:{semente}").sample(ativos, k)
    return [Falha(paradas=(visao.parada_do_vertice[v],)) for v in sorteados]
