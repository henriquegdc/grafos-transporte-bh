"""Tempo do núcleo (P0-GRAFO): heap, BFS e Dijkstra nas visões do feed real.

Uso:
    python benchmarks/medir_nucleo.py dados/brutos/bhtrans.zip

Mede com `medir` (n = 5): o HeapMin com 100.000 inserções e extrações; BFS e Dijkstra
completos (sem destino) a partir de 20 origens sorteadas em G_P e em G_E do pico da manhã,
com as esperas da F-ESPERA. Confere as distâncias do Dijkstra com o NetworkX nas mesmas
origens (permitido em benchmarks/). Grava um JSON em benchmarks/resultados/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
from datetime import date
from pathlib import Path

import networkx as nx

from transporte.dados.leitor_gtfs import ler
from transporte.grafo.buscas import INF, bfs, dijkstra
from transporte.grafo.heap import HeapMin
from transporte.modelo.construtores import construir_ge, construir_gp
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos
from transporte.util.medicao import medir

SEMENTE = 2026
ORIGENS = 20
ITENS_HEAP = 100_000
FAIXA = "pico_manha"


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _heap(prioridades: list[float]) -> None:
    heap = HeapMin()
    for item, p in enumerate(prioridades):
        heap.inserir(p, item)
    while not heap.vazio():
        heap.extrair_min()


def _buscas(busca, g, origens: list[int]) -> None:
    for o in origens:
        busca(g, o)


def _iguais_ao_networkx(g, origens: list[int]) -> bool:
    """Distâncias do Dijkstra iguais às do NetworkX (paralelas viram a de menor peso)."""
    ref = nx.DiGraph()
    ref.add_nodes_from(range(g.num_vertices()))
    for u in range(g.num_vertices()):
        for v, peso, _a in g.vizinhos(u):
            if not ref.has_edge(u, v) or peso < ref[u][v]["weight"]:
                ref.add_edge(u, v, weight=peso)
    for o in origens:
        esperado = nx.single_source_dijkstra_path_length(ref, o)
        dist = dijkstra(g, o).dist
        obtido = {v: d for v, d in enumerate(dist) if d != INF}
        if obtido.keys() != esperado.keys():
            return False
        if any(abs(obtido[v] - esperado[v]) > 1e-6 for v in obtido):
            return False
    return True


def _linha(nome: str, g, origens: list[int], repeticoes: int) -> dict:
    alcance = [sum(1 for d in dijkstra(g, o).dist if d != INF) for o in origens]
    m_dij = medir(_buscas, dijkstra, g, origens, repeticoes=repeticoes)
    m_bfs = medir(_buscas, bfs, g, origens, repeticoes=repeticoes)
    return {
        "visao": nome,
        "V": g.num_vertices(),
        "E": g.num_arestas(),
        "dijkstra_20_origens": m_dij.formatar(),
        "dijkstra_por_busca_ms": round(1e3 * m_dij.media_s / len(origens), 1),
        "bfs_20_origens": m_bfs.formatar(),
        "bfs_por_busca_ms": round(1e3 * m_bfs.media_s / len(origens), 1),
        "vertices_alcancados_min_max": [min(alcance), max(alcance)],
        "dijkstra_igual_ao_networkx": _iguais_ao_networkx(g, origens),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("caminho", type=Path)
    parser.add_argument("--repeticoes", type=int, default=5)
    parser.add_argument("--saida", type=Path, default=None)
    args = parser.parse_args()

    rede = ler(args.caminho)
    gp = construir_gp(rede).grafo
    ge = construir_ge(rede, FAIXA, esperas=calcular_esperas(estimar_intervalos(rede))).grafo
    sorteio = random.Random(SEMENTE)
    prioridades = [sorteio.random() for _ in range(ITENS_HEAP)]
    resultado = {
        "comando": "python benchmarks/medir_nucleo.py " + str(args.caminho).replace("\\", "/"),
        "feed": {
            "caminho": str(args.caminho).replace("\\", "/"),
            "sha256": _sha256(args.caminho),
        },
        "maquina": {
            "plataforma": platform.platform(),
            "processador": platform.processor(),
            "python": platform.python_version(),
        },
        "rede": {"dia": str(rede.dia), "paradas": len(rede.paradas)},
        "semente": SEMENTE,
        "repeticoes": args.repeticoes,
        "heap_100k_inserir_e_extrair": medir(
            _heap, prioridades, repeticoes=args.repeticoes
        ).formatar(),
        "visoes": [
            _linha("G_P", gp, random.Random(SEMENTE).sample(range(gp.num_vertices()), ORIGENS),
                   args.repeticoes),
            _linha(f"G_E ({FAIXA})", ge,
                   random.Random(SEMENTE).sample(range(ge.num_vertices()), ORIGENS),
                   args.repeticoes),
        ],
    }
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    saida = args.saida or Path("benchmarks/resultados") / f"nucleo-{date.today()}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(resultado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("gravado em", saida)


if __name__ == "__main__":
    main()
