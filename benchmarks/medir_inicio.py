"""Desempenho da preparação da página Início, sem o navegador ou o mapa.

Uso na raiz: PYTHONPATH=src python benchmarks/medir_inicio.py dados/brutos/bhtrans.zip
"""

import argparse
import hashlib
import json
import platform
from dataclasses import asdict
from pathlib import Path

from transporte.dados.leitor_gtfs import ler
from transporte.interface.app import _carregar_rede_em_cache, _resumo_visoes, carregar_rede
from transporte.util.medicao import medir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("feed", type=Path, help="ZIP GTFS usado pela página Início")
    parser.add_argument("--repeticoes", type=int, default=3)
    parser.add_argument(
        "--json", type=Path, default=Path("benchmarks/resultados/inicio-bhtrans.json")
    )
    args = parser.parse_args()

    def carga_fria():
        # Cada repetição precisa reconstruir a Rede pelo mesmo caminho da interface.
        _carregar_rede_em_cache.clear()
        return carregar_rede(args.feed, ler)

    fria = medir(carga_fria, repeticoes=args.repeticoes)
    quente = medir(carregar_rede, args.feed, ler, repeticoes=args.repeticoes)
    rede = carregar_rede(args.feed, ler)
    montar = medir(_resumo_visoes, rede, repeticoes=args.repeticoes)
    contagens, faixa = _resumo_visoes(rede)
    with args.feed.open("rb") as arquivo:
        digest = hashlib.file_digest(arquivo, "sha256").hexdigest()
    dados = {
        "feed": str(args.feed),
        "sha256": digest,
        "dia": rede.dia,
        "maquina": platform.platform(),
        "python": platform.python_version(),
        "faixa": faixa,
        "visoes": {visao: {"V": v, "E": e} for visao, (v, e) in contagens.items()},
        "tempos": {
            "carga_cache_frio": asdict(fria),
            "carga_cache_quente": asdict(quente),
            "montagem_gp_ge": asdict(montar),
        },
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.json)


if __name__ == "__main__":
    main()
