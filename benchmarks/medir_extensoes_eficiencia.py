"""Medição sequencial de F-EFI-2 e F-EFI-OPC no mesmo feed e com os mesmos pares."""

import argparse
import hashlib
import json
import platform
from dataclasses import asdict
from pathlib import Path

from transporte.algoritmos.eficiencia import comparar_faixas, indices_desvio, medias_por_quadrante
from transporte.algoritmos.isocronas import isocrona
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_ge
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos
from transporte.util.medicao import medir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("feed", type=Path)
    parser.add_argument("--origem", required=True)
    parser.add_argument("--faixa", default="pico_manha")
    parser.add_argument("--pares", type=int, default=12)
    parser.add_argument("--semente", type=int, default=2026)
    parser.add_argument("--repeticoes", type=int, default=5)
    parser.add_argument("--saida", type=Path, default=Path("benchmarks/resultados"))
    args = parser.parse_args()
    rede = ler(args.feed)
    esperas = calcular_esperas(estimar_intervalos(rede))
    ge = construir_ge(rede, args.faixa, esperas=esperas)
    if args.origem not in ge.vertice_da_parada:
        parser.error("origem ausente no feed")
    amostragem = (args.pares, args.semente)
    args.saida.mkdir(parents=True, exist_ok=True)
    with args.feed.open("rb") as arq:
        sha = hashlib.file_digest(arq, "sha256").hexdigest()
    base = {
        "feed": args.feed.name,
        "sha256": sha,
        "dia": rede.dia,
        "maquina": platform.platform(),
        "processador": platform.processor(),
        "python": platform.python_version(),
        "pares": args.pares,
        "semente": args.semente,
    }

    def registrar(feature, dados):
        destino = args.saida / f"{feature.lower()}-{args.feed.stem}.json"
        destino.write_text(json.dumps(base | dados, ensure_ascii=False, indent=2) + "\n")
        print(destino, flush=True)

    tempos = isocrona(ge, args.origem, 3600)
    desvios = indices_desvio(rede, ge, *amostragem)
    registrar(
        "F-EFI-2",
        {
            "origem": args.origem,
            "faixa": args.faixa,
            "V": ge.grafo.num_vertices(),
            "E": ge.grafo.num_arestas(),
            "alcance": {
                str(m): sum(t <= m * 60 for t in tempos.values()) for m in (15, 30, 45, 60)
            },
            "pares_avaliados": [
                asdict(p) | {"desvio": p.desvio, "min_por_km": p.min_por_km} for p in desvios
            ],
            "media_por_quadrante": medias_por_quadrante(desvios),
            "medicoes": {
                "isocrona": asdict(
                    medir(isocrona, ge, args.origem, 3600, repeticoes=args.repeticoes)
                ),
                "indices_desvio": asdict(
                    medir(indices_desvio, rede, ge, *amostragem, repeticoes=args.repeticoes)
                ),
            },
        },
    )
    resultados = comparar_faixas(rede, *amostragem)
    registrar(
        "F-EFI-OPC",
        {
            "faixas": [asdict(r) for r in resultados],
            "medicoes": {
                "comparar_faixas": asdict(
                    medir(comparar_faixas, rede, *amostragem, repeticoes=args.repeticoes)
                )
            },
        },
    )


if __name__ == "__main__":
    main()
