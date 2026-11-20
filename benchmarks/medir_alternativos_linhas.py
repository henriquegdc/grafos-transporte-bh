"""Quantas sequências de linhas distintas saem dos alternativos do Yen no feed real (F-ROTA-OPC).

Uso: python benchmarks/medir_alternativos_linhas.py [dados/brutos/bhtrans.zip] [pares] [k]

Monta o G_E do pico da manhã com as esperas da F-ESPERA (como a página Trajetos), sorteia
pares de paradas com semente fixa (só os que têm trajeto) e, em cada par:

- Yen puro (`trajetos_alternativos`, k caminhos): quantas sequências de `linha_id` distintas
  há entre os k e a diferença de tempo entre o 1º e o último;
- filtro por linhas (`alternativos_por_linhas`, teto 2 · k caminhos): quantas sequências
  distintas achou, quantos caminhos do Yen aceitou e a diferença de tempo entre a 1ª e a
  última sequência.

Os tempos de relógio dependem da carga da máquina; as contagens não.
"""

from __future__ import annotations

import platform
import random
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from transporte.algoritmos.a_estrela import coordenadas_ge, velocidade_maxima
from transporte.algoritmos.alternativos import (
    alternativos_por_linhas,
    sequencia_de_linhas,
    trajetos_alternativos,
)
from transporte.algoritmos.trajeto import trajeto_mais_rapido
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_ge
from transporte.modelo.parametros import Parametros
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos

SEMENTE = 2026
FAIXA = "pico_manha"


def main(caminho: str, n_pares: int, k: int) -> None:
    print("python", platform.python_version(), platform.platform(), platform.processor())
    params = Parametros()
    rede = ler(caminho)
    print(f"rede: dia={rede.dia} paradas={len(rede.paradas)} padroes={len(rede.padroes)}")
    esperas = calcular_esperas(estimar_intervalos(rede, params))
    ge = construir_ge(rede, FAIXA, params, esperas)
    coords = coordenadas_ge(ge, rede.paradas)
    vmax = velocidade_maxima(ge, coords)
    print(f"G_E[{FAIXA}]: V={ge.grafo.num_vertices()} E={ge.grafo.num_arestas()}")
    linha_do_padrao = {pid: p.linha_id for pid, p in rede.padroes.items()}

    rng = random.Random(SEMENTE)
    paradas = sorted(rede.paradas)
    pares = []
    while len(pares) < n_pares:
        o, d = rng.sample(paradas, 2)
        if trajeto_mais_rapido(ge, o, d) is not None:
            pares.append((o, d))

    tot_puro = tot_filtro = tot_aceitos = 0
    pares_uma_seq = 0
    for o, d in pares:
        inicio = perf_counter()
        puros = trajetos_alternativos(ge, o, d, k, coords, vmax)
        s_puro = perf_counter() - inicio
        seqs = {sequencia_de_linhas(t, linha_do_padrao) for t in puros}
        dif_puro = puros[-1].tempo_total_s - puros[0].tempo_total_s

        inicio = perf_counter()
        alts = alternativos_por_linhas(ge, o, d, k, linha_do_padrao, coords, vmax)
        s_filtro = perf_counter() - inicio
        aceitos = sum(a.variantes for a in alts)
        dif_filtro = alts[-1].trajeto.tempo_total_s - alts[0].trajeto.tempo_total_s
        assert alts[0].trajeto.tempo_total_s == puros[0].tempo_total_s

        tot_puro += len(seqs)
        tot_filtro += len(alts)
        tot_aceitos += aceitos
        pares_uma_seq += len(seqs) == 1
        print(
            f"{o}->{d}: puro {len(puros)} caminhos, {len(seqs)} sequencia(s), "
            f"1o-ultimo {dif_puro:.0f} s, {s_puro:.1f} s | "
            f"filtro {len(alts)} sequencia(s) em {aceitos} caminhos, "
            f"1a-ultima {dif_filtro:.0f} s, {s_filtro:.1f} s; "
            f"variantes {[a.variantes for a in alts]}"
        )
    print(
        f"total k={k} x{n_pares}: puro {tot_puro} sequencias distintas em {k * n_pares} "
        f"caminhos ({pares_uma_seq} pares com uma so); filtro {tot_filtro} sequencias em "
        f"{tot_aceitos} caminhos aceitos (teto {2 * k} por par)"
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    main(
        args[0] if args else "dados/brutos/bhtrans.zip",
        int(args[1]) if len(args) > 1 else 8,
        int(args[2]) if len(args) > 2 else 5,
    )
