"""Mede as métricas da F-EFI no GTFS real.

Uso: PYTHONPATH=src python benchmarks/medir_eficiencia.py [dados/brutos/bhtrans.zip]
Mede eficiência global amostrada e tempo médio de viagem em G_P/G_E, com `medir`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from dataclasses import asdict
from pathlib import Path

from transporte.algoritmos.eficiencia import (
    estimar_eficiencia_global,
    tempo_medio_viagem,
)
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_ge, construir_gp
from transporte.modelo.parametros import Parametros
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos
from transporte.util.medicao import medir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("caminho", type=Path, nargs="?", default=Path("dados/brutos/bhtrans.zip"))
    parser.add_argument("--origens", type=int, default=100)
    parser.add_argument("--pares", type=int, default=100)
    parser.add_argument("--repeticoes", type=int, default=3)
    parser.add_argument("--semente", type=int, default=2026)
    parser.add_argument("--faixa", default="pico_manha")
    args = parser.parse_args()
    if args.origens < 1 or args.pares < 1 or args.repeticoes < 1:
        parser.error("--origens, --pares e --repeticoes devem ser positivos")

    rede = ler(args.caminho)
    parametros = Parametros()
    gp = construir_gp(rede, parametros)
    esperas = calcular_esperas(estimar_intervalos(rede, parametros))
    ge = construir_ge(rede, args.faixa, parametros, esperas=esperas)

    print("Medindo eficiencia global amostrada...", flush=True)
    eficiencia = medir(
        estimar_eficiencia_global,
        gp.grafo,
        tamanho_amostra=args.origens,
        semente=args.semente,
        repeticoes=args.repeticoes,
    )
    print("Medindo tempo medio de viagem...", flush=True)
    tempo = medir(
        tempo_medio_viagem,
        ge,
        tamanho_amostra=args.pares,
        semente=args.semente,
        repeticoes=args.repeticoes,
    )

    with args.caminho.open("rb") as feed:
        sha256 = hashlib.file_digest(feed, "sha256").hexdigest()

    resultado = {
        "feed": str(args.caminho),
        "sha256": sha256,
        "comando": (
            f"python benchmarks/medir_eficiencia.py {args.caminho} "
            f"--origens {args.origens} --pares {args.pares} "
            f"--repeticoes {args.repeticoes} --semente {args.semente} --faixa {args.faixa}"
        ),
        "maquina": {
            "plataforma": platform.platform(),
            "python": platform.python_version(),
            "processador": platform.processor() or platform.machine(),
        },
        "rede": {
            "dia": rede.dia,
            "paradas": len(rede.paradas),
            "linhas": len(rede.linhas),
            "padroes": len(rede.padroes),
            "viagens": len(rede.viagens_por_id),
        },
        "faixa": args.faixa,
        "G_P": {
            "vertices": gp.grafo.num_vertices(),
            "arestas": gp.grafo.num_arestas(),
        },
        "G_E": {
            "vertices": ge.grafo.num_vertices(),
            "arestas": ge.grafo.num_arestas(),
        },
        "amostragem": {
            "origens": args.origens,
            "pares": args.pares,
            "semente": args.semente,
            "repeticoes": args.repeticoes,
        },
        "medicoes": {
            "eficiencia_global": {
                **asdict(eficiencia),
                "formatado": eficiencia.formatar(),
            },
            "tempo_medio_viagem": {
                **asdict(tempo),
                "formatado": tempo.formatar(),
            },
        },
    }
    print(json.dumps(resultado, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
