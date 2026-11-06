"""Tempo de P0-MODELO (construir_gp, construir_ge) e F-ROTA (trajeto_mais_rapido) no feed real.

Uso: PYTHONPATH=src python benchmarks/medir_modelo_rota.py [dados/brutos/bhtrans.zip]

Precisa da leitura do GTFS (transporte.dados, P0-DADOS, PR #42) e do feed baixado por
scripts/baixar_gtfs.py. Mede com `medir` (5 repetições), faz 200 consultas de trajeto entre
pares de paradas sorteados com semente fixa em G_E do pico da manhã e confere cada tempo
total com o Dijkstra do NetworkX no mesmo grafo (permitido em benchmarks/).
"""

from __future__ import annotations

import platform
import random
import sys

import networkx as nx

from transporte.algoritmos.trajeto import trajeto_mais_rapido
from transporte.modelo.construtores import construir_ge, construir_gp
from transporte.modelo.parametros import Parametros
from transporte.util.medicao import medir

REPETICOES = 5
N_CONSULTAS = 200
SEMENTE = 2026
FAIXA_CONSULTAS = "pico_manha"


def main(caminho: str) -> None:
    # Import local: transporte.dados chega com o PR #42 (P0-DADOS); fora do topo, o
    # módulo continua importável e a ordem dos imports não muda quando ele entrar.
    from transporte.dados.leitor_gtfs import ler

    print(
        "python", platform.python_version(), platform.platform(), platform.processor()
    )
    rede = ler(caminho)
    print(
        f"rede: dia={rede.dia} paradas={len(rede.paradas)} padroes={len(rede.padroes)} "
        f"viagens={len(rede.viagens_por_id)}"
    )

    gp = construir_gp(rede)
    m = medir(construir_gp, rede, repeticoes=REPETICOES)
    print(
        f"construir_gp: V={gp.grafo.num_vertices()} E={gp.grafo.num_arestas()} {m.formatar()}"
    )

    ges = {}
    for faixa in Parametros().faixas:
        ge = construir_ge(rede, faixa.nome)
        ges[faixa.nome] = ge
        m = medir(construir_ge, rede, faixa.nome, repeticoes=REPETICOES)
        print(
            f"construir_ge[{faixa.nome}]: V={ge.grafo.num_vertices()} "
            f"E={ge.grafo.num_arestas()} {m.formatar()}"
        )

    ge = ges[FAIXA_CONSULTAS]
    rng = random.Random(SEMENTE)
    paradas = sorted(rede.paradas)
    pares = [tuple(rng.sample(paradas, 2)) for _ in range(N_CONSULTAS)]

    def todas() -> list:
        return [trajeto_mais_rapido(ge, o, d) for o, d in pares]

    m = medir(todas, repeticoes=REPETICOES)
    print(
        f"trajeto_mais_rapido x{N_CONSULTAS} ({FAIXA_CONSULTAS}): {m.formatar()}; "
        f"por consulta {1e3 * m.media_s / N_CONSULTAS:.1f} ms"
    )
    # Pior caso por consulta (RNF-05): cada consulta medida sozinha, 3 repetições.
    por_consulta = sorted(
        medir(trajeto_mais_rapido, ge, o, d, repeticoes=3).media_s for o, d in pares
    )
    p95 = por_consulta[int(0.95 * (N_CONSULTAS - 1))]
    print(
        f"por consulta: mediana {1e3 * por_consulta[N_CONSULTAS // 2]:.1f} ms, "
        f"p95 {1e3 * p95:.1f} ms, máximo {1e3 * por_consulta[-1]:.1f} ms"
    )
    resultados = todas()
    achados = [t for t in resultados if t is not None]
    print(f"com trajeto: {len(achados)}/{N_CONSULTAS}")
    if achados:
        tempos = sorted(t.tempo_total_s for t in achados)
        bald = [t.baldeacoes for t in achados]
        print(
            f"tempo total mediano: {tempos[len(tempos) // 2] / 60:.1f} min; "
            f"baldeacoes 0/1/2: {[sum(b == k for b in bald) for k in (0, 1, 2)]}, "
            f"3 ou mais: {sum(b >= 3 for b in bald)}"
        )

    g = ge.grafo
    referencia = nx.DiGraph()
    for a in range(g.num_arestas()):
        u, v, peso, _ = g.aresta(a)
        if not referencia.has_edge(u, v) or referencia[u][v]["weight"] > peso:
            referencia.add_edge(u, v, weight=peso)
    divergencias = 0
    for (o, d), t in zip(pares, resultados, strict=True):
        s, alvo = ge.vertice_da_parada[o], ge.vertice_da_parada[d]
        try:
            ref = nx.dijkstra_path_length(referencia, s, alvo)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            ref = None
        ok = (ref is None and t is None) or (
            ref is not None and t is not None and abs(ref - t.tempo_total_s) < 1e-6
        )
        divergencias += not ok
    print(f"divergencias com NetworkX: {divergencias}/{N_CONSULTAS}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dados/brutos/bhtrans.zip")
