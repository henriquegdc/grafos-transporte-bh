"""Nossos algoritmos contra os equivalentes do NetworkX no mesmo grafo (RF-AVA-03).

Uso (medição final, nesta ordem com complexidade_empirica.py):
    PYTHONPATH=src python benchmarks/comparar_networkx.py --feed dados/brutos/bhtrans.zip

Validação rápida (sem o feed, poucos tamanhos e repetições):
    PYTHONPATH=src python benchmarks/comparar_networkx.py --lados 5 10 --repeticoes 1 --saida /tmp/x.json

Para cada grafo (o G_P do feed real, se `--feed` for dado, e o G_P de redes sintéticas de
`transporte.dados.sinteticas`), mede com `medir` o nosso algoritmo e o do NetworkX sobre o
mesmo grafo e confere que os resultados batem:

    BFS          nosso `bfs`                 x nx.single_source_shortest_path_length
    Dijkstra     nosso `dijkstra`            x nx.single_source_dijkstra_path_length
    Brandes      `intermediacao` (exato) ou  x nx.betweenness_centrality (exato) ou
                 `estimar_intermediacao`       nx.betweenness_centrality_subset com as
                 (k origens sorteadas)         mesmas k origens, todos os destinos
    Tarjan       `componentes_fortes`        x nx.strongly_connected_components

O Brandes exato custa O(V (V + E) log V): acima de `--limite-exato` vértices (o G_P real
tem 9.660) os dois lados rodam só a partir das mesmas k origens, o que custa k / V do
exato e ainda confere a soma das dependências origem a origem.

O grafo do NetworkX é montado uma vez, fora da medição (`para_networkx`), como o nosso.
Grava um JSON em benchmarks/resultados/comparacao-networkx-<data>.json.

Ponto de extensão: cada algoritmo é uma `Comparacao` na lista `COMPARACOES`. Para incluir
proximidade (F-MET-2, contra nx.closeness_centrality(wf_improved=True), atenção à direção:
o NetworkX usa distância de entrada em grafo dirigido) e propagação de rótulos (F-MET-OPC,
contra nx.community.asyn_lpa_communities; as partições não precisam coincidir, então a
conferência deve ser a modularidade de cada uma calculada pelo nx.community.modularity),
basta escrever as três funções (nosso, networkx, iguais) e acrescentar a entrada. Nada mais
no script muda.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parent))

from avaliacao_comum import gravar_json, maquina, para_networkx, sha256

from transporte.algoritmos.centralidade import estimar_intermediacao, intermediacao
from transporte.dados.sinteticas import gerar_rede_sintetica
from transporte.grafo.buscas import INF, bfs, dijkstra
from transporte.grafo.grafo import Grafo
from transporte.modelo.construtores import construir_gp
from transporte.simulacao.falhas import componentes_fortes
from transporte.util.medicao import medir

SEMENTE = 2026
LADOS = (10, 30, 60)
TOLERANCIA = 1e-6


@dataclass
class Contexto:
    """O que as comparações recebem: os dois grafos e as origens sorteadas."""

    g: Grafo
    ref: nx.DiGraph
    origens: list[int]
    origens_brandes: list[int]
    brandes_exato: bool
    semente: int


@dataclass(frozen=True)
class Comparacao:
    """Um algoritmo nosso e o equivalente do NetworkX.

    nosso(ctx) e networkx(ctx) são cronometrados com `medir`; iguais(a, b, ctx) recebe as
    saídas de uma execução extra de cada um e diz se os resultados batem. escopo(ctx)
    descreve o que uma execução faz (por exemplo "20 origens").
    """

    algoritmo: str
    complexidade: str
    escopo: Callable[[Contexto], str]
    nosso: Callable[[Contexto], Any]
    networkx: Callable[[Contexto], Any]
    iguais: Callable[[Any, Any, Contexto], bool]


def _perto(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=TOLERANCIA, abs_tol=TOLERANCIA)


def _distancias_iguais(nossas: list, deles: list) -> bool:
    """Lista de Resultado (nosso) x lista de dicionários {vértice: distância} (NetworkX)."""
    for r, esperado in zip(nossas, deles, strict=True):
        obtido = {v: d for v, d in enumerate(r.dist) if d != INF}
        if obtido.keys() != esperado.keys():
            return False
        if not all(_perto(obtido[v], esperado[v]) for v in obtido):
            return False
    return True


# --- BFS ------------------------------------------------------------------------------


def _bfs_nosso(ctx: Contexto) -> list:
    return [bfs(ctx.g, o) for o in ctx.origens]


def _bfs_nx(ctx: Contexto) -> list:
    return [nx.single_source_shortest_path_length(ctx.ref, o) for o in ctx.origens]


# --- Dijkstra -------------------------------------------------------------------------


def _dijkstra_nosso(ctx: Contexto) -> list:
    return [dijkstra(ctx.g, o) for o in ctx.origens]


def _dijkstra_nx(ctx: Contexto) -> list:
    return [
        nx.single_source_dijkstra_path_length(ctx.ref, o, weight="weight") for o in ctx.origens
    ]


# --- Brandes --------------------------------------------------------------------------


def _brandes_nosso(ctx: Contexto) -> list[float]:
    if ctx.brandes_exato:
        return intermediacao(ctx.g, ponderado=True)
    est = estimar_intermediacao(
        ctx.g, tamanho_amostra=len(ctx.origens_brandes), semente=ctx.semente
    )
    # Desfaz o fator N / k para ficar com a soma das dependências das k origens, que é o
    # que o betweenness_centrality_subset devolve.
    fator = est.tamanho_amostra / est.tamanho_populacao
    return [x * fator for x in est.valores]


def _brandes_nx(ctx: Contexto) -> dict:
    if ctx.brandes_exato:
        return nx.betweenness_centrality(ctx.ref, weight="weight", normalized=False)
    return nx.betweenness_centrality_subset(
        ctx.ref, sources=ctx.origens_brandes, targets=list(ctx.ref.nodes),
        weight="weight", normalized=False,
    )


def _brandes_iguais(nosso: list[float], deles: dict, ctx: Contexto) -> bool:
    escala = max([1.0, *deles.values()])
    return all(
        math.isclose(nosso[v], deles.get(v, 0.0), rel_tol=TOLERANCIA, abs_tol=TOLERANCIA * escala)
        for v in range(len(nosso))
    )


def _brandes_escopo(ctx: Contexto) -> str:
    if ctx.brandes_exato:
        return "exato (todas as origens)"
    return f"{len(ctx.origens_brandes)} origens sorteadas"


# --- Tarjan ---------------------------------------------------------------------------


def _tarjan_iguais(nosso: list[list[int]], deles: list[set[int]], _ctx: Contexto) -> bool:
    return {frozenset(c) for c in nosso} == {frozenset(c) for c in deles}


COMPARACOES: list[Comparacao] = [
    Comparacao(
        "BFS", "O(V + E) por origem",
        lambda ctx: f"{len(ctx.origens)} origens",
        _bfs_nosso, _bfs_nx, lambda a, b, _c: _distancias_iguais(a, b),
    ),
    Comparacao(
        "Dijkstra", "O((V + E) log V) por origem",
        lambda ctx: f"{len(ctx.origens)} origens",
        _dijkstra_nosso, _dijkstra_nx, lambda a, b, _c: _distancias_iguais(a, b),
    ),
    Comparacao(
        "Brandes (intermediação)", "O(V (V + E) log V) exato; O(k (V + E) log V) com k origens",
        _brandes_escopo, _brandes_nosso, _brandes_nx, _brandes_iguais,
    ),
    Comparacao(
        "Tarjan (componentes fortes)", "O(V + E)",
        lambda _ctx: "grafo inteiro",
        lambda ctx: componentes_fortes(ctx.g),
        lambda ctx: list(nx.strongly_connected_components(ctx.ref)),
        _tarjan_iguais,
    ),
    # Extensão (ver docstring do módulo): proximidade (F-MET-2) e propagação de rótulos
    # (F-MET-OPC) entram aqui como novas Comparacao, quando as funções estiverem na main.
]


def comparar_grafo(
    nome: str,
    g: Grafo,
    repeticoes: int,
    n_origens: int,
    n_origens_brandes: int,
    limite_exato: int,
    semente: int = SEMENTE,
) -> dict:
    """Roda todas as COMPARACOES num grafo e devolve o bloco do JSON."""
    ref = para_networkx(g)
    ativos = [v for v in range(g.num_vertices()) if g.vertice_ativo(v)]
    origens = random.Random(semente).sample(ativos, min(n_origens, len(ativos)))
    exato = len(ativos) <= limite_exato or n_origens_brandes >= len(ativos)
    # Mesmo sorteio que estimar_intermediacao faz por dentro, para os dois lados usarem
    # exatamente as mesmas origens.
    origens_b = sorted(random.Random(semente).sample(ativos, min(n_origens_brandes, len(ativos))))
    ctx = Contexto(g, ref, origens, origens_b, exato, semente)
    linhas = []
    for comp in COMPARACOES:
        nosso = medir(comp.nosso, ctx, repeticoes=repeticoes)
        deles = medir(comp.networkx, ctx, repeticoes=repeticoes)
        iguais = comp.iguais(comp.nosso(ctx), comp.networkx(ctx), ctx)
        linhas.append({
            "algoritmo": comp.algoritmo,
            "complexidade": comp.complexidade,
            "escopo": comp.escopo(ctx),
            "nosso_media_s": nosso.media_s,
            "nosso_desvio_s": nosso.desvio_s,
            "nosso": nosso.formatar(),
            "networkx_media_s": deles.media_s,
            "networkx_desvio_s": deles.desvio_s,
            "networkx": deles.formatar(),
            "razao_nosso_sobre_networkx": nosso.media_s / deles.media_s if deles.media_s else None,
            "resultados_iguais": iguais,
        })
        print(f"{nome}: {comp.algoritmo}: nosso {nosso.formatar()}, "
              f"networkx {deles.formatar()}, iguais={iguais}", file=sys.stderr)
    return {"grafo": nome, "V": g.num_vertices(), "E": g.num_arestas(), "algoritmos": linhas}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--feed", type=Path, default=None, help="GTFS real (ZIP ou pasta)")
    parser.add_argument("--lados", type=int, nargs="*", default=list(LADOS),
                        help="lados das redes sintéticas (V = lado²)")
    parser.add_argument("--repeticoes", type=int, default=3)
    parser.add_argument("--origens", type=int, default=20, help="origens de BFS e Dijkstra")
    parser.add_argument("--origens-brandes", type=int, default=20,
                        help="k origens do Brandes quando V passa do limite do exato")
    parser.add_argument("--limite-exato", type=int, default=1000,
                        help="até quantos vértices o Brandes roda exato")
    parser.add_argument("--saida", type=Path, default=None)
    args = parser.parse_args()

    comando = "python benchmarks/comparar_networkx.py " + " ".join(
        a.replace("\\", "/") for a in sys.argv[1:]
    )
    resultado: dict = {
        "comando": comando.strip(),
        "data": str(date.today()),
        "maquina": maquina(),
        "semente": SEMENTE,
        "repeticoes": args.repeticoes,
        "networkx": nx.__version__,
        "grafos": [],
    }
    parametros = {
        "repeticoes": args.repeticoes,
        "n_origens": args.origens,
        "n_origens_brandes": args.origens_brandes,
        "limite_exato": args.limite_exato,
    }
    if args.feed is not None:
        from transporte.dados.leitor_gtfs import ler

        resultado["feed"] = {
            "caminho": str(args.feed).replace("\\", "/"),
            "sha256": sha256(args.feed) if args.feed.is_file() else None,
        }
        rede = ler(args.feed)
        resultado["grafos"].append(
            comparar_grafo("G_P (feed real)", construir_gp(rede).grafo, **parametros)
        )
    for lado in args.lados:
        g = construir_gp(gerar_rede_sintetica(lado, SEMENTE)).grafo
        resultado["grafos"].append(
            comparar_grafo(f"G_P sintética {lado}x{lado}", g, **parametros)
        )
    resultado["todos_iguais"] = all(
        linha["resultados_iguais"] for bloco in resultado["grafos"] for linha in bloco["algoritmos"]
    )
    saida = args.saida or Path("benchmarks/resultados") / f"comparacao-networkx-{date.today()}.json"
    gravar_json(resultado, saida)


if __name__ == "__main__":
    main()
