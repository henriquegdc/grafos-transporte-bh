"""Tempo e resultados da F-BALD-2 (comparar_baldeacoes) no feed real.

Uso: python benchmarks/medir_comparacao_baldeacoes.py [dados/brutos/bhtrans.zip]

Monta o G_E do pico da manhã com as esperas da F-ESPERA e a G_L da mesma faixa, como a
página Baldeações. Sorteia 200 pares de paradas com a mesma semente do medir_modelo_rota.py
(F-ROTA) e do medir_baldeacoes.py (F-BALD) e mede com `medir` (3 repetições por par) a
comparação inteira e, nos pares em que ela roda, o mais_rapido_com_limite. Resume o tempo a
mais e as baldeações evitadas, conta os pares em que o mais rápido faz menos baldeações que
o mínimo da G_L (caminhada encadeada) e confere cada busca com limite com o NetworkX
(permitido em benchmarks/) num grafo em camadas montado à parte.
"""

from __future__ import annotations

import platform
import random
import statistics
import sys

import networkx as nx

from transporte.algoritmos.comparacao_baldeacoes import (
    comparar_baldeacoes,
    mais_rapido_com_limite,
)
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_ge
from transporte.modelo.linhas import construir_gl
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import EMBARQUE
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos
from transporte.util.medicao import medir

REPETICOES = 3
N_CONSULTAS = 200
SEMENTE = 2026
FAIXA = "pico_manha"


def _camadas(g, limite: int) -> nx.DiGraph:
    """Nó (v, e), e = embarques feitos (0 a limite + 1); EMBARQUE sobe uma camada."""
    camadas = limite + 2
    h = nx.DiGraph()
    for a in range(g.num_arestas()):
        u, v, peso, tipo = g.aresta(a)
        for e in range(camadas):
            e2 = e + 1 if tipo == EMBARQUE else e
            if e2 < camadas and (
                not h.has_edge((u, e), (v, e2)) or peso < h[(u, e)][(v, e2)]["weight"]
            ):
                h.add_edge((u, e), (v, e2), weight=peso)
    return h


def _ms(segundos: float) -> str:
    return f"{1e3 * segundos:.1f} ms"


def main(caminho: str) -> None:
    print("python", platform.python_version(), platform.platform(), platform.processor())
    rede = ler(caminho)
    print(f"rede: dia={rede.dia} paradas={len(rede.paradas)} padroes={len(rede.padroes)}")
    params = Parametros()
    esperas = calcular_esperas(estimar_intervalos(rede, params))
    ge = construir_ge(rede, FAIXA, params=params, esperas=esperas)
    gl = construir_gl(rede, params, faixa=FAIXA)
    print(
        f"G_E[{FAIXA}]: V={ge.grafo.num_vertices()} E={ge.grafo.num_arestas()}; "
        f"G_L[{FAIXA}]: V={gl.grafo.num_vertices()} E={gl.grafo.num_arestas()}"
    )

    rng = random.Random(SEMENTE)
    paradas = sorted(rede.paradas)
    pares = [tuple(rng.sample(paradas, 2)) for _ in range(N_CONSULTAS)]

    tempos = []
    resultados = []
    for o, d in pares:
        m = medir(comparar_baldeacoes, ge, gl, o, d, repeticoes=REPETICOES)
        tempos.append(m.media_s)
        resultados.append(comparar_baldeacoes(ge, gl, o, d))
    tempos.sort()
    p95 = tempos[int(0.95 * (N_CONSULTAS - 1))]
    print(
        f"comparar_baldeacoes x{N_CONSULTAS} ({REPETICOES} repetições por par): "
        f"média {_ms(statistics.fmean(tempos))}, mediana {_ms(tempos[N_CONSULTAS // 2])}, "
        f"p95 {_ms(p95)}, máximo {_ms(tempos[-1])}"
    )

    comp = [(par, c) for par, c in zip(pares, resultados, strict=True) if c is not None]
    print(f"com comparação: {len(comp)}/{N_CONSULTAS}")
    limitados = [
        (par, c) for par, c in comp if c.rapido_com_menos_baldeacoes is not c.mais_rapido
    ]
    evitam = [c for _, c in comp if c.baldeacoes_evitadas > 0]
    abaixo = sum(
        1 for _, c in comp if c.mais_rapido.baldeacoes < c.menos_baldeacoes.baldeacoes
    )
    print(
        f"mais rápido já no mínimo: {len(comp) - len(limitados)} "
        f"(dos quais abaixo do mínimo da G_L por caminhada encadeada: {abaixo}); "
        f"busca com limite: {len(limitados)}; evitam baldeação: {len(evitam)}"
    )
    evitadas = [c.baldeacoes_evitadas for c in evitam]
    print(
        f"baldeações evitadas 1/2/3+: {evitadas.count(1)}/{evitadas.count(2)}/"
        f"{sum(e >= 3 for e in evitadas)}"
    )
    if evitam:
        a_mais = sorted(c.tempo_a_mais_s / 60 for c in evitam)
        por = sorted(c.tempo_por_baldeacao_evitada_s / 60 for c in evitam)
        print(
            f"tempo a mais (min): mediana {statistics.median(a_mais):.1f}, "
            f"média {statistics.fmean(a_mais):.1f}, máximo {a_mais[-1]:.1f}; "
            f"zero: {sum(x == 0 for x in a_mais)}"
        )
        print(
            f"por baldeação evitada (min): mediana {statistics.median(por):.1f}, "
            f"média {statistics.fmean(por):.1f}"
        )
        rel = sorted(c.tempo_a_mais_s / c.mais_rapido.tempo_total_s for c in evitam)
        print(f"tempo a mais relativo ao mais rápido: mediana {100 * statistics.median(rel):.0f}%")

    if limitados:
        t_lim = sorted(
            medir(
                mais_rapido_com_limite, ge, o, d, c.menos_baldeacoes.baldeacoes,
                repeticoes=REPETICOES,
            ).media_s
            for (o, d), c in limitados
        )
        print(
            f"mais_rapido_com_limite x{len(limitados)}: média {_ms(statistics.fmean(t_lim))}, "
            f"mediana {_ms(t_lim[len(t_lim) // 2])}, máximo {_ms(t_lim[-1])}"
        )

    divergencias = 0
    grafos: dict[int, nx.DiGraph] = {}
    for (o, d), c in limitados:
        k = c.menos_baldeacoes.baldeacoes
        if k not in grafos:
            grafos[k] = _camadas(ge.grafo, k)
        h = grafos[k]
        s, t = ge.vertice_da_parada[o], ge.vertice_da_parada[d]
        dist = nx.single_source_dijkstra_path_length(h, (s, 0))
        esperado = min(dist.get((t, e), float("inf")) for e in range(k + 2))
        divergencias += abs(esperado - c.rapido_com_menos_baldeacoes.tempo_total_s) > 1e-6
    print(f"divergências com NetworkX (busca com limite): {divergencias}/{len(limitados)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dados/brutos/bhtrans.zip")
