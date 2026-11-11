"""Tempo e resultados da F-RES (falhas e resiliência) em G_P do feed real.

Uso: python benchmarks/medir_falhas.py [dados/brutos/bhtrans.zip]

Precisa do feed baixado por scripts/baixar_gtfs.py. Mede com `medir` (5 repetições):
Tarjan em G_P, eficiência global amostrada e simulações de falha de uma parada (a de maior
grau de saída em viagem) e de uma linha (a que tem mais trechos exclusivos). Confere as
componentes com o NetworkX no mesmo grafo (permitido em benchmarks/).
"""

from __future__ import annotations

import platform
import random
import sys

import networkx as nx

from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_gp
from transporte.modelo.visoes import VIAGEM
from transporte.simulacao.falhas import (
    Falha,
    componentes_fortes,
    eficiencia_global,
    indexar_linhas,
    simular_falha,
)
from transporte.util.medicao import medir

REPETICOES = 5
AMOSTRA = 200
SEMENTE = 2026


def _profundidade_dfs(g) -> int:
    """Maior número de quadros na pilha de chamadas da DFS, na mesma ordem do Tarjan.

    É a profundidade que a versão recursiva atingiria; justifica o Tarjan iterativo.
    """
    visto = [False] * g.num_vertices()
    maior = 0
    for raiz in range(g.num_vertices()):
        if visto[raiz]:
            continue
        visto[raiz] = True
        chamadas = [[raiz, g.vizinhos(raiz), 0]]
        while chamadas:
            maior = max(maior, len(chamadas))
            quadro = chamadas[-1]
            if quadro[2] < len(quadro[1]):
                w = quadro[1][quadro[2]][0]
                quadro[2] += 1
                if not visto[w]:
                    visto[w] = True
                    chamadas.append([w, g.vizinhos(w), 0])
            else:
                chamadas.pop()
    return maior


def main(caminho: str) -> None:
    print("python", platform.python_version(), platform.platform(), platform.processor())
    rede = ler(caminho)
    visao = construir_gp(rede)
    g = visao.grafo
    print(
        f"rede: dia={rede.dia} paradas={len(rede.paradas)} linhas={len(rede.linhas)} "
        f"padroes={len(rede.padroes)}"
    )
    print(f"G_P: V={g.num_vertices()} E={g.num_arestas()}")

    # Componentes, conferidas com o NetworkX.
    comps = componentes_fortes(g)
    ref = nx.DiGraph()
    ref.add_nodes_from(range(g.num_vertices()))
    for u in range(g.num_vertices()):
        for v, _p, _a in g.vizinhos(u):
            ref.add_edge(u, v)
    iguais = {frozenset(c) for c in comps} == {
        frozenset(c) for c in nx.strongly_connected_components(ref)
    }
    tamanhos = sorted((len(c) for c in comps), reverse=True)
    print(
        f"componentes: {len(comps)}; maior={tamanhos[0]}; unitarias="
        f"{sum(1 for t in tamanhos if t == 1)}; iguais ao NetworkX={iguais}"
    )
    print(
        f"profundidade maxima da DFS: {_profundidade_dfs(g)} "
        f"(limite de recursao do Python: {sys.getrecursionlimit()})"
    )
    print("tarjan:", medir(componentes_fortes, g, repeticoes=REPETICOES).formatar())

    ativos = list(range(g.num_vertices()))
    origens = random.Random(SEMENTE).sample(ativos, AMOSTRA)
    print(
        f"eficiencia (amostra {AMOSTRA}): {eficiencia_global(g, origens):.6e} 1/s;",
        medir(eficiencia_global, g, origens, repeticoes=REPETICOES).formatar(),
    )

    # Parada com mais saídas de viagem.
    saidas = [0] * g.num_vertices()
    for a in range(g.num_arestas()):
        u, _v, _p, tipo = g.aresta(a)
        if tipo == VIAGEM:
            saidas[u] += 1
    v_max = max(range(g.num_vertices()), key=lambda v: saidas[v])
    parada = visao.parada_do_vertice[v_max]
    falha_parada = Falha(paradas=(parada,))

    indice = indexar_linhas(rede)
    exclusivos: dict[str, int] = {}
    for linhas in indice.values():
        if len(linhas) == 1:
            (linha,) = linhas
            exclusivos[linha] = exclusivos.get(linha, 0) + 1
    linha = max(exclusivos, key=lambda x: exclusivos[x])
    falha_linha = Falha(linhas=(linha,))

    for nome, falha in (
        (f"parada {parada} ({saidas[v_max]} saidas de viagem)", falha_parada),
        (f"linha {linha} ({exclusivos[linha]} trechos exclusivos)", falha_linha),
    ):
        r = simular_falha(visao, falha, indice, amostra=AMOSTRA, semente=SEMENTE)
        print(
            f"falha {nome}: componentes {len(r.componentes_antes)} -> "
            f"{len(r.componentes_depois)}; isoladas={len(r.paradas_isoladas)}; "
            f"desconectadas={len(r.paradas_desconectadas)}; "
            f"perda de eficiencia={r.perda_eficiencia:.4%}"
        )
        t = medir(
            simular_falha, visao, falha, indice, amostra=AMOSTRA, semente=SEMENTE,
            repeticoes=REPETICOES,
        )
        print("  simular_falha:", t.formatar())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dados/brutos/bhtrans.zip")
