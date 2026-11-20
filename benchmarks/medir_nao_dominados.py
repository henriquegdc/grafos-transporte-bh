"""Tempo e resultados da F-BALD-OPC (trajetos_nao_dominados) no feed real.

Uso:
    python benchmarks/medir_nao_dominados.py dados/brutos/bhtrans.zip

Monta o G_E do pico da manhã com as esperas da F-ESPERA, como a página Baldeações. Sorteia
pares de paradas com a mesma semente do medir_comparacao_baldeacoes.py (F-BALD-2) e mede com
`medir` a fronteira inteira de cada par. Resume o tamanho da fronteira, as baldeações do
mais rápido (B, que fixa o número de buscas) e o tempo por par, e confere que o último ponto
tem o tempo do trajeto_mais_rapido (F-ROTA). Grava um JSON em benchmarks/resultados/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import statistics
from collections import Counter
from datetime import date
from pathlib import Path

from transporte.algoritmos.comparacao_baldeacoes import trajetos_nao_dominados
from transporte.algoritmos.trajeto import trajeto_mais_rapido
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_ge
from transporte.modelo.parametros import Parametros
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos
from transporte.util.medicao import medir

SEMENTE = 2026
FAIXA = "pico_manha"


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _ms(segundos: float) -> float:
    return round(1e3 * segundos, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("caminho", type=Path)
    parser.add_argument("--pares", type=int, default=200)
    parser.add_argument("--repeticoes", type=int, default=3)
    parser.add_argument("--saida", type=Path, default=None)
    args = parser.parse_args()

    rede = ler(args.caminho)
    params = Parametros()
    esperas = calcular_esperas(estimar_intervalos(rede, params))
    ge = construir_ge(rede, FAIXA, params=params, esperas=esperas)

    rng = random.Random(SEMENTE)
    paradas = sorted(rede.paradas)
    pares = [tuple(rng.sample(paradas, 2)) for _ in range(args.pares)]

    tempos: list[float] = []
    tamanhos: Counter[int] = Counter()
    buscas_b: Counter[int] = Counter()
    por_tamanho: dict[int, list[float]] = {}
    divergencias = 0
    exemplo = None
    for o, d in pares:
        m = medir(trajetos_nao_dominados, ge, o, d, repeticoes=args.repeticoes)
        f = trajetos_nao_dominados(ge, o, d)
        if not f:
            continue
        tempos.append(m.media_s)
        tamanhos[len(f)] += 1
        rapido = trajeto_mais_rapido(ge, o, d)
        buscas_b[rapido.baldeacoes] += 1
        por_tamanho.setdefault(len(f), []).append(m.media_s)
        divergencias += abs(f[-1].tempo_total_s - rapido.tempo_total_s) > 1e-6
        if exemplo is None or len(f) > len(exemplo["pontos"]):
            exemplo = {
                "origem": o,
                "destino": d,
                "pontos": [
                    {"baldeacoes": t.baldeacoes, "tempo_min": round(t.tempo_total_s / 60, 1)}
                    for t in f
                ],
            }

    tempos_ord = sorted(tempos)
    n = len(tempos_ord)
    resultado = {
        "comando": "python benchmarks/medir_nao_dominados.py "
        + str(args.caminho).replace("\\", "/")
        + ("" if args.pares == 200 else f" --pares {args.pares}")
        + ("" if args.repeticoes == 3 else f" --repeticoes {args.repeticoes}"),
        "feed": {
            "caminho": str(args.caminho).replace("\\", "/"),
            "sha256": _sha256(args.caminho),
        },
        "maquina": {
            "plataforma": platform.platform(),
            "processador": platform.processor(),
            "python": platform.python_version(),
        },
        "rede": {"dia": str(rede.dia), "paradas": len(rede.paradas)},
        "ge": {"faixa": FAIXA, "V": ge.grafo.num_vertices(), "E": ge.grafo.num_arestas()},
        "semente": SEMENTE,
        "pares": args.pares,
        "repeticoes": args.repeticoes,
        "pares_alcancaveis": n,
        "tamanho_da_fronteira": {str(k): v for k, v in sorted(tamanhos.items())},
        "baldeacoes_do_mais_rapido": {str(k): v for k, v in sorted(buscas_b.items())},
        "tempo_por_par_ms": {
            "media": _ms(statistics.fmean(tempos_ord)) if n else None,
            "mediana": _ms(tempos_ord[n // 2]) if n else None,
            "p95": _ms(tempos_ord[int(0.95 * (n - 1))]) if n else None,
            "maximo": _ms(tempos_ord[-1]) if n else None,
        },
        "tempo_medio_por_tamanho_ms": {
            str(k): _ms(statistics.fmean(v)) for k, v in sorted(por_tamanho.items())
        },
        "ultimo_ponto_diverge_do_mais_rapido": divergencias,
        "maior_fronteira": exemplo,
    }
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    saida = args.saida or Path("benchmarks/resultados") / f"nao-dominados-{date.today()}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(resultado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("gravado em", saida)


if __name__ == "__main__":
    main()
