"""Tempo da F-BALD (construir_gl, menos_baldeacoes) no feed real.

Uso: python benchmarks/medir_baldeacoes.py [dados/brutos/bhtrans.zip]

Mede com `medir` (5 repetições) a construção da G_L do dia e do pico da manhã e 200
consultas entre pares de paradas sorteados com a mesma semente do medir_modelo_rota.py
(F-ROTA), na G_L do pico da manhã. Confere cada resultado com o NetworkX (permitido em
benchmarks/) num grafo de estados independente da G_L, e conta em quantos pares o BFS comum
sobre a G_L, que ignora o sentido dos padrões, daria menos baldeações que o real.
"""

from __future__ import annotations

import platform
import random
import sys

import networkx as nx

from transporte.algoritmos.baldeacoes import menos_baldeacoes
from transporte.dados.leitor_gtfs import ler
from transporte.grafo.buscas import INF, bfs
from transporte.modelo.linhas import construir_gl
from transporte.util.medicao import medir

REPETICOES = 5
N_CONSULTAS = 200
SEMENTE = 2026
FAIXA = "pico_manha"


def _referencia(gl, rede) -> nx.DiGraph:
    """Grafo de estados: chegou à parada, pronto para embarcar, embarcou, a bordo. Peso 1 no
    embarque; o caminho mínimo é o número de ônibus. Caminhada pelos pares de gl.proximas
    (a grade espacial é conferida contra a busca ingênua nos testes do P0-MODELO)."""
    g = nx.DiGraph()
    for x, vizinhas in gl.proximas.items():
        for y, _d in vizinhas:
            g.add_edge(("chegou", x), ("pronto", y), weight=0)
    for pid in gl.padrao_do_vertice:
        seq = rede.padroes[pid].paradas
        for k in range(len(seq) - 1):
            g.add_edge(("pronto", seq[k]), ("embarcou", pid, k), weight=1)
            g.add_edge(("embarcou", pid, k), ("a bordo", pid, k + 1), weight=0)
            if k >= 1:
                g.add_edge(("a bordo", pid, k), ("a bordo", pid, k + 1), weight=0)
        for k in range(1, len(seq)):
            g.add_edge(("a bordo", pid, k), ("chegou", seq[k]), weight=0)
    return g


def _limite_bfs_comum(gl, origem: str, destino: str) -> float:
    """Baldeações que um BFS comum sobre a G_L daria: menor distância de um padrão que
    embarca perto da origem a um padrão que desce perto do destino."""
    inicio = {p for y, _ in gl.proximas[origem] for p, _ in gl.embarques.get(y, ())}
    perto = {y for y, _ in gl.proximas[destino]}
    fim = [v for v, seq in enumerate(gl.paradas_do_padrao) if any(x in perto for x in seq[1:])]
    melhor = INF
    for s in inicio:
        dist = bfs(gl.grafo, s).dist
        melhor = min(melhor, min((dist[f] for f in fim), default=INF))
    return melhor


def main(caminho: str) -> None:
    print("python", platform.python_version(), platform.platform(), platform.processor())
    rede = ler(caminho)
    print(
        f"rede: dia={rede.dia} paradas={len(rede.paradas)} padroes={len(rede.padroes)} "
        f"viagens={len(rede.viagens_por_id)}"
    )

    for faixa in (None, FAIXA):
        gl = construir_gl(rede, faixa=faixa)
        m = medir(construir_gl, rede, faixa=faixa, repeticoes=REPETICOES)
        trocas = sum(len(t) for t in gl.transferencias)
        print(
            f"construir_gl[{faixa or 'dia'}]: V={gl.grafo.num_vertices()} "
            f"E={gl.grafo.num_arestas()} trocas={trocas} {m.formatar()}"
        )

    gl = construir_gl(rede, faixa=FAIXA)
    rng = random.Random(SEMENTE)
    paradas = sorted(rede.paradas)
    pares = [tuple(rng.sample(paradas, 2)) for _ in range(N_CONSULTAS)]

    def todas() -> list:
        return [menos_baldeacoes(gl, o, d) for o, d in pares]

    m = medir(todas, repeticoes=REPETICOES)
    print(
        f"menos_baldeacoes x{N_CONSULTAS} ({FAIXA}): {m.formatar()}; "
        f"por consulta {1e3 * m.media_s / N_CONSULTAS:.2f} ms"
    )
    por_consulta = sorted(
        medir(menos_baldeacoes, gl, o, d, repeticoes=3).media_s for o, d in pares
    )
    p95 = por_consulta[int(0.95 * (N_CONSULTAS - 1))]
    print(
        f"por consulta: mediana {1e3 * por_consulta[N_CONSULTAS // 2]:.2f} ms, "
        f"p95 {1e3 * p95:.2f} ms, máximo {1e3 * por_consulta[-1]:.2f} ms"
    )

    resultados = todas()
    achados = [t for t in resultados if t is not None]
    print(f"com trajeto: {len(achados)}/{N_CONSULTAS}")
    bald = [t.baldeacoes for t in achados]
    print(
        "baldeacoes 0/1/2/3: "
        f"{[sum(b == k for b in bald) for k in range(4)]}, 4 ou mais: {sum(b >= 4 for b in bald)}"
    )
    a_pe = sum(1 for t in achados if t.trechos and not t.padroes())
    com_troca_a_pe = sum(1 for t in achados if any(x != y for x, y in t.trocas()))
    print(f"so a pe: {a_pe}; com alguma troca a pe: {com_troca_a_pe}")

    ref = _referencia(gl, rede)
    divergencias = 0
    for (o, d), t in zip(pares, resultados, strict=True):
        try:
            esperado = nx.dijkstra_path_length(ref, ("chegou", o), ("pronto", d))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            esperado = None
        obtido = None if t is None else len(t.padroes())
        divergencias += esperado != obtido
    print(f"divergencias com NetworkX: {divergencias}/{N_CONSULTAS}")

    menores = 0
    comparados = 0
    for (o, d), t in zip(pares, resultados, strict=True):
        if t is None or not t.padroes():
            continue
        comparados += 1
        menores += _limite_bfs_comum(gl, o, d) < t.baldeacoes
    print(f"BFS comum daria menos baldeacoes que o real: {menores}/{comparados}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dados/brutos/bhtrans.zip")
