"""Medições da F-ROTA-2 (A* contra Dijkstra) e da F-ROTA-OPC (Yen) no feed real.

Uso: python benchmarks/medir_rota_extensoes.py [dados/brutos/bhtrans.zip]

Precisa do feed baixado por scripts/baixar_gtfs.py. Monta o G_E do pico da manhã com as
esperas da F-ESPERA (como a página Trajetos), sorteia pares de paradas com semente fixa e:

- RF-ROT-04: roda Dijkstra e A* pela mesma busca contada e informa vértices expandidos e
  tempo (mediana, p95 e máximo), a razão entre eles e as divergências de custo, que devem
  ser 0 porque a heurística é consistente;
- RF-ROT-03: mede `parada_mais_proxima` (varredura linear) em pontos sorteados na caixa
  das paradas;
- RF-ROT-05: mede `trajetos_alternativos` com k = 3 e k = 5 em uma amostra menor de pares
  com trajeto, com A* nos desvios, e confere que os custos não decrescem.
"""

from __future__ import annotations

import platform
import random
import sys
from itertools import pairwise
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from transporte.algoritmos.a_estrela import (
    comparar,
    coordenadas_ge,
    dijkstra_contado,
    parada_mais_proxima,
    trajeto_a_estrela,
    velocidade_maxima,
)
from transporte.algoritmos.alternativos import trajetos_alternativos
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import _distancia_m, construir_ge
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import CAMINHADA, VIAGEM
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos

SEMENTE = 2026
FAIXA = "pico_manha"
N_COMPARACOES = 200
N_PONTOS = 1000
N_YEN = 20


def _quantis(valores: list[float]) -> str:
    v = sorted(valores)
    return (
        f"mediana {v[len(v) // 2]:.1f}, p95 {v[int(0.95 * (len(v) - 1))]:.1f}, máximo {v[-1]:.1f}"
    )


def main(caminho: str) -> None:
    print("python", platform.python_version(), platform.platform(), platform.processor())
    params = Parametros()
    rede = ler(caminho)
    print(f"rede: dia={rede.dia} paradas={len(rede.paradas)} padroes={len(rede.padroes)}")

    inicio = perf_counter()
    esperas = calcular_esperas(estimar_intervalos(rede, params))
    ge = construir_ge(rede, FAIXA, params, esperas)
    coords = coordenadas_ge(ge, rede.paradas)
    vmax = velocidade_maxima(ge, coords)
    print(
        f"G_E[{FAIXA}] com esperas: V={ge.grafo.num_vertices()} E={ge.grafo.num_arestas()} "
        f"vmax={vmax:.1f} m/s ({3.6 * vmax:.0f} km/h); preparo {perf_counter() - inicio:.2f} s"
    )

    rng = random.Random(SEMENTE)
    paradas = sorted(rede.paradas)
    pares = [tuple(rng.sample(paradas, 2)) for _ in range(N_COMPARACOES)]
    exp_d, exp_a, ms_d, ms_a, razoes = [], [], [], [], []
    divergencias = 0
    com_trajeto = []
    for o, d in pares:
        c = comparar(ge, coords, vmax, o, d)
        td, ta = c.dijkstra.trajeto, c.a_estrela.trajeto
        if (td is None) != (ta is None) or (
            td is not None and abs(td.tempo_total_s - ta.tempo_total_s) > 1e-6
        ):
            divergencias += 1
        if td is None:
            continue
        com_trajeto.append((o, d))
        exp_d.append(c.dijkstra.expandidos)
        exp_a.append(c.a_estrela.expandidos)
        ms_d.append(1e3 * c.dijkstra.tempo_s)
        ms_a.append(1e3 * c.a_estrela.tempo_s)
        razoes.append(c.a_estrela.expandidos / c.dijkstra.expandidos)
    print(
        f"comparacao x{N_COMPARACOES}: com trajeto {len(com_trajeto)}; divergencias {divergencias}"
    )
    print(f"  expandidos Dijkstra: {_quantis(exp_d)}")
    print(f"  expandidos A*:       {_quantis(exp_a)}")
    print(f"  A*/Dijkstra (expandidos): {_quantis([100 * r for r in razoes])} (%)")
    print(f"  tempo Dijkstra (ms): {_quantis(ms_d)}")
    print(f"  tempo A* (ms):       {_quantis(ms_a)}")

    # Experimento (não está em src/): vmax sem as arestas no piso de 1 s (decisão M2), que
    # são artefato do GTFS (duas paradas seguidas com o mesmo horário). A heurística deixa
    # de ser admissível nessas arestas; mede o ganho e quanto o A* erra por isso.
    g = ge.grafo
    piso = [
        g.aresta(a)[2] <= params.peso_minimo_s and g.aresta(a)[3] in (VIAGEM, CAMINHADA)
        for a in range(g.num_arestas())
    ]
    vmax_sem_piso = 0.0
    for a in range(g.num_arestas()):
        u, v, peso, tipo = g.aresta(a)
        if tipo in (VIAGEM, CAMINHADA) and not piso[a]:
            vmax_sem_piso = max(vmax_sem_piso, _distancia_m(*coords[u], *coords[v]) / peso)
    print(
        f"experimento sem o piso: {sum(piso)} arestas no piso; "
        f"vmax={vmax_sem_piso:.1f} m/s ({3.6 * vmax_sem_piso:.0f} km/h)"
    )
    exp_x, ms_x, erros = [], [], []
    for (o, d), base in zip(com_trajeto, exp_d, strict=True):
        b = trajeto_a_estrela(ge, coords, vmax_sem_piso, o, d)
        otimo = dijkstra_contado(ge, o, d).trajeto.tempo_total_s
        exp_x.append(100 * b.expandidos / base)
        ms_x.append(1e3 * b.tempo_s)
        erros.append(100 * (b.trajeto.tempo_total_s - otimo) / otimo)
    print(f"  A*/Dijkstra (expandidos): {_quantis(exp_x)} (%)")
    print(f"  tempo A* (ms): {_quantis(ms_x)}")
    print(
        f"  trajetos piores que o ótimo: {sum(e > 1e-9 for e in erros)}/{len(erros)}; "
        f"excesso {_quantis(erros)} (%)"
    )

    lats = [float(p.lat) for p in rede.paradas.values()]
    lons = [float(p.lon) for p in rede.paradas.values()]
    pontos = [
        (rng.uniform(min(lats), max(lats)), rng.uniform(min(lons), max(lons)))
        for _ in range(N_PONTOS)
    ]
    inicio = perf_counter()
    distancias = [parada_mais_proxima(rede.paradas, lat, lon)[1] for lat, lon in pontos]
    duracao = perf_counter() - inicio
    print(
        f"parada_mais_proxima x{N_PONTOS}: {1e3 * duracao / N_PONTOS:.2f} ms por ponto; "
        f"distancia {_quantis(distancias)} (m)"
    )

    amostra = com_trajeto[:N_YEN]
    for k in (3, 5):
        tempos, achados = [], []
        for o, d in amostra:
            inicio = perf_counter()
            ts = trajetos_alternativos(ge, o, d, k, coords, vmax)
            tempos.append(perf_counter() - inicio)
            achados.append(len(ts))
            custos = [t.tempo_total_s for t in ts]
            # Tolerância: caminhos de mesmo custo somados em ordens diferentes diferem em 1 ulp.
            assert all(a <= b + 1e-6 for a, b in pairwise(custos)), (o, d, custos)
        print(
            f"yen k={k} x{len(amostra)}: tempo (s) {_quantis(tempos)}; "
            f"trajetos achados: {_quantis(achados)}"
        )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dados/brutos/bhtrans.zip")
