"""Tempo e erro da F-MET (centralidades) no G_P do feed real.

Uso:
    python benchmarks/medir_centralidade.py dados/brutos/bhtrans.zip [--exato]

Mede com `medir`: graus (todas as arestas e só viagem) e a intermediação amostrada
(`estimar_intermediacao`) para alguns tamanhos de amostra. Com --exato, roda uma vez o
Brandes exato (todas as origens; cerca de 40 min no G_P real) e guarda o vetor em
dados/cache/, fora do Git; com o exato disponível, compara cada amostra com ele: erro
relativo nas paradas mais centrais, sobreposição do top 10 e do top 50 e cobertura do
intervalo de 2 erros padrão (RNF-06). Grava um JSON em benchmarks/resultados/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import time
from datetime import date
from pathlib import Path

from transporte.algoritmos.centralidade import (
    distribuicao_graus,
    estimar_intermediacao,
    graus,
    ranking,
)
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_gp
from transporte.modelo.visoes import VIAGEM
from transporte.util.medicao import medir

SEMENTE = 2026
AMOSTRAS = (25, 50, 100, 200)


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _exato(g, cache: Path) -> tuple[list[float], float | None]:
    """Vetor exato (do cache, se existir) e o tempo da execução, se rodou agora."""
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))["valores"], None
    inicio = time.perf_counter()
    valores = estimar_intermediacao(g).valores
    duracao = time.perf_counter() - inicio
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"valores": valores, "segundos": duracao}), encoding="utf-8")
    return valores, duracao


def _comparar(g, exato: list[float], est) -> dict:
    """Erro da estimativa contra o exato."""
    top10 = {v for v, _ in ranking(g, exato, 10)}
    top50 = {v for v, _ in ranking(g, exato, 50)}
    top100 = [v for v, _ in ranking(g, exato, 100)]
    erros_rel = [abs(est.valores[v] - exato[v]) / exato[v] for v in top100 if exato[v] > 0]
    positivos = [v for v in range(len(exato)) if exato[v] > 0]

    def cobertura(vertices: list[int]) -> float:
        """Fração em que o exato cai em estimativa ± 2 erros padrão."""
        dentro = sum(
            1 for v in vertices if abs(est.valores[v] - exato[v]) <= 2 * est.erro_padrao[v]
        )
        return dentro / len(vertices)

    return {
        "top10_em_comum": len(top10 & {v for v, _ in ranking(g, est.valores, 10)}),
        "top50_em_comum": len(top50 & {v for v, _ in ranking(g, est.valores, 50)}),
        "erro_relativo_mediano_top100": statistics.median(erros_rel),
        "erro_relativo_maximo_top100": max(erros_rel),
        "cobertura_2_erros_padrao_top100": cobertura(top100),
        "cobertura_2_erros_padrao_todas": cobertura(positivos),
        "erro_padrao_zero_todas": sum(1 for v in positivos if est.erro_padrao[v] == 0)
        / len(positivos),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("caminho", type=Path)
    parser.add_argument("--exato", action="store_true", help="roda (ou lê do cache) o exato")
    parser.add_argument("--repeticoes", type=int, default=3)
    parser.add_argument("--saida", type=Path, default=None)
    args = parser.parse_args()

    sha = _sha256(args.caminho)
    rede = ler(args.caminho)
    visao = construir_gp(rede)
    g = visao.grafo
    resultado: dict = {
        "comando": "python benchmarks/medir_centralidade.py "
        + str(args.caminho).replace("\\", "/")
        + (" --exato" if args.exato else ""),
        "feed": {"caminho": str(args.caminho).replace("\\", "/"), "sha256": sha},
        "maquina": {
            "plataforma": platform.platform(),
            "processador": platform.processor(),
            "python": platform.python_version(),
        },
        "rede": {"dia": str(rede.dia), "paradas": len(rede.paradas), "padroes": len(rede.padroes)},
        "G_P": {"V": g.num_vertices(), "E": g.num_arestas()},
        "semente": SEMENTE,
        "repeticoes": args.repeticoes,
    }
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

    r = graus(g)
    rv = graus(g, tipos={VIAGEM})
    resultado["graus"] = {
        "tempo_todas": medir(graus, g, repeticoes=args.repeticoes).formatar(),
        "tempo_so_viagem": medir(graus, g, {VIAGEM}, repeticoes=args.repeticoes).formatar(),
        "saida_maxima_todas": max(r.saida),
        "saida_maxima_viagem": max(rv.saida),
        "distribuicao_saida_viagem": distribuicao_graus(g, rv.saida),
        "top5_saida_viagem": [
            [visao.parada_do_vertice[v], int(x)] for v, x in ranking(g, rv.saida, 5)
        ],
    }
    print("graus:", json.dumps(resultado["graus"], ensure_ascii=False))

    exato = None
    if args.exato:
        cache = Path("dados/cache") / f"intermediacao-exata-{sha[:12]}.json"
        exato, segundos = _exato(g, cache)
        if segundos is None:
            segundos = json.loads(cache.read_text(encoding="utf-8"))["segundos"]
        resultado["exato"] = {
            "segundos_uma_execucao": round(segundos, 1),
            "top10": [
                [visao.parada_do_vertice[v], rede.paradas[visao.parada_do_vertice[v]].nome, x]
                for v, x in ranking(g, exato, 10)
            ],
        }
        print("exato:", json.dumps(resultado["exato"], ensure_ascii=False))

    resultado["amostras"] = {}
    for k in AMOSTRAS:
        est = estimar_intermediacao(g, k, semente=SEMENTE)
        linha: dict = {
            "tempo": medir(
                estimar_intermediacao, g, k, SEMENTE, repeticoes=args.repeticoes
            ).formatar(),
        }
        if exato is not None:
            linha.update(_comparar(g, exato, est))
        resultado["amostras"][k] = linha
        print(f"k={k}:", json.dumps(linha, ensure_ascii=False))

    saida = args.saida or Path("benchmarks/resultados") / f"centralidade-{date.today()}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(resultado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("gravado em", saida)


if __name__ == "__main__":
    main()
