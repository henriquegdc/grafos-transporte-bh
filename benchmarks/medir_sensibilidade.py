"""Mede a comparação de cenários de uma linha no GTFS carregado."""

import argparse
import hashlib
import json
import platform
from dataclasses import asdict
from pathlib import Path

from transporte.dados.leitor_gtfs import ler
from transporte.simulacao.espera import estimar_intervalos, sensibilidade_intervalo
from transporte.util.medicao import medir

# Máximo da página; com 10 pares nenhum trajeto mudou no feed de 18/11.
PARES = 100


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("feed", type=Path)
    parser.add_argument("--linha")
    parser.add_argument(
        "--json", type=Path, default=Path("benchmarks/resultados/sensibilidade-bhtrans.json")
    )
    args = parser.parse_args()
    rede = ler(args.feed)
    faixa = "pico_manha"
    linha = args.linha or next(
        rede.padroes[p].linha_id for p, f in estimar_intervalos(rede) if f == faixa
    )
    consulta = (rede, linha, faixa, 2, PARES, 42)
    r = sensibilidade_intervalo(*consulta)
    deltas = [b - a for _, _, a, b in r["pares"] if a is not None and b is not None and b != a]
    r.update(
        feed=args.feed.as_posix(),
        sha256_feed=hashlib.sha256(args.feed.read_bytes()).hexdigest(),
        aumento_medio_s_nos_que_mudaram=sum(deltas) / len(deltas) if deltas else None,
        dia=rede.dia,
        maquina=platform.platform(),
        python=platform.python_version(),
        faixa=faixa,
        linha=linha,
        fator=2,
        semente=42,
        tempos={"sensibilidade_intervalo": asdict(medir(sensibilidade_intervalo, *consulta))},
    )
    args.json.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
