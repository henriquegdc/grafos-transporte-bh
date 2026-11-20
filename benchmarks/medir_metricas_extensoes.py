"""Tempo e resultados da F-MET-2 (proximidade) e da F-MET-OPC (comunidades) em G_P.

Uso:
    python benchmarks/medir_metricas_extensoes.py dados/brutos/bhtrans.zip
        [--repeticoes 3] [--exato] [--saida arquivo.json]

Mede com `medir`: a proximidade amostrada (sentido de saída, como a página) para alguns
tamanhos de amostra e a propagação de rótulos com a modularidade. Com --exato, roda uma
vez a proximidade exata (um Dijkstra por parada; dezenas de minutos no G_P real) e compara
cada amostra com ela: paradas em comum no top 10 e no top 50 e erro relativo mediano nas
100 primeiras. Confere a proximidade exata (só com --exato) e a modularidade com o
NetworkX no mesmo grafo (permitido em benchmarks/). Grava um JSON em
benchmarks/resultados/.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from datetime import date
from pathlib import Path

import networkx as nx

from transporte.algoritmos.centralidade import proximidade, ranking
from transporte.algoritmos.comunidades import (
    SEM_COMUNIDADE,
    modularidade,
    propagar_rotulos,
)
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_gp
from transporte.util.medicao import medir

SEMENTE = 2026
AMOSTRAS = (25, 50, 100, 200)


def _como_networkx(g) -> tuple[nx.DiGraph, nx.Graph]:
    """G_P como DiGraph (menor peso entre paralelas) e como Graph simples não dirigido."""
    dirigido = nx.DiGraph()
    dirigido.add_nodes_from(range(g.num_vertices()))
    for u in range(g.num_vertices()):
        for v, peso, _a in g.vizinhos(u):
            if u == v:
                continue
            if not dirigido.has_edge(u, v) or peso < dirigido[u][v]["weight"]:
                dirigido.add_edge(u, v, weight=peso)
    return dirigido, dirigido.to_undirected(as_view=False)


def _comparar(g, exato: list[float], estimado: list[float]) -> dict:
    top10 = {v for v, _ in ranking(g, exato, 10)}
    top50 = {v for v, _ in ranking(g, exato, 50)}
    top100 = [v for v, _ in ranking(g, exato, 100)]
    erros = [abs(estimado[v] - exato[v]) / exato[v] for v in top100 if exato[v] > 0]
    return {
        "top10_em_comum": len(top10 & {v for v, _ in ranking(g, estimado, 10)}),
        "top50_em_comum": len(top50 & {v for v, _ in ranking(g, estimado, 50)}),
        "erro_relativo_mediano_top100": statistics.median(erros) if erros else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("caminho", type=Path)
    parser.add_argument("--repeticoes", type=int, default=3)
    parser.add_argument("--exato", action="store_true", help="roda a proximidade exata")
    parser.add_argument("--saida", type=Path, default=None)
    args = parser.parse_args()

    rede = ler(args.caminho)
    visao = construir_gp(rede)
    g = visao.grafo
    resultado: dict = {
        "comando": "python benchmarks/medir_metricas_extensoes.py "
        + str(args.caminho).replace("\\", "/")
        + f" --repeticoes {args.repeticoes}"
        + (" --exato" if args.exato else ""),
        "maquina": {
            "plataforma": platform.platform(),
            "processador": platform.processor(),
            "python": platform.python_version(),
        },
        "rede": {"dia": str(rede.dia), "paradas": len(rede.paradas), "padroes": len(rede.padroes)},
        "G_P": {"V": g.num_vertices(), "E": g.num_arestas()},
        "semente": SEMENTE,
        "repeticoes": args.repeticoes,
    }
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    dirigido, nao_dirigido = _como_networkx(g)

    def nome(v: int) -> list:
        parada = visao.parada_do_vertice[v]
        return [parada, getattr(rede.paradas[parada], "nome", "")]

    # --- F-MET-2: proximidade ---------------------------------------------------------
    exato = None
    if args.exato:
        inicio = time.perf_counter()
        exato = proximidade(g)
        segundos = time.perf_counter() - inicio
        # O NetworkX usa distâncias de entrada; a de saída é a de entrada no reverso.
        ref = nx.closeness_centrality(dirigido.reverse(), distance="weight", wf_improved=True)
        diferenca = max(abs(exato[v] - ref[v]) for v in range(g.num_vertices()))
        resultado["proximidade_exata"] = {
            "segundos_uma_execucao": round(segundos, 1),
            "maior_diferenca_networkx": diferenca,
            "top10": [nome(v) + [x] for v, x in ranking(g, exato, 10)],
        }
        print("exato:", json.dumps(resultado["proximidade_exata"], ensure_ascii=False))

    resultado["proximidade_amostrada"] = {}
    for k in AMOSTRAS:
        valores = proximidade(g, tamanho_amostra=k, semente=SEMENTE)
        linha: dict = {
            "tempo": medir(
                proximidade, g, "saida", k, SEMENTE, repeticoes=args.repeticoes
            ).formatar(),
            "top5": [nome(v) + [x] for v, x in ranking(g, valores, 5)],
        }
        if exato is not None:
            linha.update(_comparar(g, exato, valores))
        resultado["proximidade_amostrada"][k] = linha
        print(f"proximidade k={k}:", json.dumps(linha, ensure_ascii=False))

    # --- F-MET-OPC: comunidades -------------------------------------------------------
    c = propagar_rotulos(g, semente=SEMENTE)
    q = modularidade(g, c.rotulos)
    conjuntos: dict[int, set[int]] = {}
    for v, r in enumerate(c.rotulos):
        if r != SEM_COMUNIDADE:
            conjuntos.setdefault(r, set()).add(v)
    q_nx = nx.community.modularity(nao_dirigido, list(conjuntos.values()))
    tamanhos = sorted(c.tamanhos(), reverse=True)
    sementes = [propagar_rotulos(g, semente=s) for s in range(SEMENTE, SEMENTE + 5)]
    resultado["comunidades"] = {
        "tempo_propagacao": medir(
            propagar_rotulos, g, SEMENTE, repeticoes=args.repeticoes
        ).formatar(),
        "tempo_modularidade": medir(
            modularidade, g, c.rotulos, repeticoes=args.repeticoes
        ).formatar(),
        "quantidade": c.quantidade,
        "iteracoes": c.iteracoes,
        "convergiu": c.convergiu,
        "modularidade": q,
        "modularidade_networkx": q_nx,
        "maiores_10": tamanhos[:10],
        "unitarias": sum(1 for t in tamanhos if t == 1),
        "variacao_5_sementes": {
            "sementes": [SEMENTE, SEMENTE + 4],
            "quantidade": [x.quantidade for x in sementes],
            "modularidade": [modularidade(g, x.rotulos) for x in sementes],
        },
    }
    print("comunidades:", json.dumps(resultado["comunidades"], ensure_ascii=False))

    saida = args.saida or Path("benchmarks/resultados") / f"metricas-extensoes-{date.today()}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(resultado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("gravado em", saida)


if __name__ == "__main__":
    main()
