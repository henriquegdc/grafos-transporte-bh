"""Complexidade empírica: tempo x tamanho em log-log nas redes sintéticas (RF-AVA-04).

Uso (medição final):
    PYTHONPATH=src python benchmarks/complexidade_empirica.py

Validação rápida (tamanhos pequenos, figura fora do relatório):
    PYTHONPATH=src python benchmarks/complexidade_empirica.py --lados 5 8 12 --lados-brandes 5 8 \
        --repeticoes 1 --saida /tmp/c.json --figura /tmp/c.png

Para cada rede sintética de `transporte.dados.sinteticas` (grade lado x lado, V = lado²),
constrói o G_P e mede com `medir`:

    BFS        uma busca a partir de uma origem sorteada        O(V + E)
    Dijkstra   uma busca completa a partir da mesma origem      O((V + E) log V)
    Tarjan     componentes fortes do grafo inteiro             O(V + E)
    Brandes    intermediação exata (V Dijkstras)               O(V (V + E) log V)

e ajusta, por mínimos quadrados, log10(tempo) = a + b log10(V + E). A inclinação b é o
expoente empírico: se t ~ (V + E)^b, dobrar o tamanho multiplica o tempo por 2^b. Como E
cresce proporcional a V nas grades (cerca de 12 V), o teórico é b = 1 para BFS e Tarjan,
um pouco acima de 1 para o Dijkstra (o fator log V) e cerca de 2 para o Brandes
(V (V + E) ~ (V + E)², também com o fator log). O Brandes roda só nos lados de
`--lados-brandes`, porque custa minutos já com poucos milhares de vértices.

Grava benchmarks/resultados/complexidade-<data>.json e a figura
relatorio/figuras/complexidade-empirica.png (matplotlib, só em benchmarks/).
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from avaliacao_comum import gravar_json, maquina

from transporte.algoritmos.centralidade import intermediacao
from transporte.dados.sinteticas import LADOS_PADRAO, gerar_rede_sintetica
from transporte.grafo.buscas import bfs, dijkstra
from transporte.modelo.construtores import construir_gp
from transporte.simulacao.falhas import componentes_fortes
from transporte.util.medicao import medir

SEMENTE = 2026
LADOS_BRANDES = (10, 15, 20, 30, 40)
FIGURA = Path("relatorio/figuras/complexidade-empirica.png")

# nome -> (complexidade teórica, inclinação teórica em log-log contra V + E, função(g, o))
ALGORITMOS: dict[str, tuple[str, float, Callable]] = {
    "BFS": ("O(V + E)", 1.0, lambda g, o: bfs(g, o)),
    "Dijkstra": ("O((V + E) log V)", 1.0, lambda g, o: dijkstra(g, o)),
    "Tarjan": ("O(V + E)", 1.0, lambda g, _o: componentes_fortes(g)),
    "Brandes": ("O(V (V + E) log V)", 2.0, lambda g, _o: intermediacao(g, ponderado=True)),
}


def regressao_loglog(xs: list[float], ys: list[float]) -> dict:
    """Mínimos quadrados de log10(y) = a + b log10(x). Devolve inclinação b, intercepto a
    e R². Precisa de ao menos dois x distintos. O(n)."""
    lx = [math.log10(x) for x in xs]
    ly = [math.log10(y) for y in ys]
    n = len(lx)
    mx, my = sum(lx) / n, sum(ly) / n
    sxx = sum((x - mx) ** 2 for x in lx)
    if n < 2 or sxx == 0:
        raise ValueError("a regressão precisa de ao menos dois tamanhos distintos")
    sxy = sum((x - mx) * (y - my) for x, y in zip(lx, ly))
    b = sxy / sxx
    a = my - b * mx
    sqt = sum((y - my) ** 2 for y in ly)
    sqr = sum((y - (a + b * x)) ** 2 for x, y in zip(lx, ly))
    return {"inclinacao": b, "intercepto": a, "r2": 1 - sqr / sqt if sqt else 1.0}


def medir_tamanhos(
    lados: list[int], lados_brandes: list[int], repeticoes: int, repeticoes_brandes: int
) -> list[dict]:
    """Mede cada algoritmo em cada tamanho; devolve um bloco por algoritmo."""
    pontos: dict[str, list[dict]] = {nome: [] for nome in ALGORITMOS}
    for lado in sorted(set(lados) | set(lados_brandes)):
        g = construir_gp(gerar_rede_sintetica(lado, SEMENTE)).grafo
        origem = random.Random(SEMENTE).randrange(g.num_vertices())
        for nome, (_c, _b, func) in ALGORITMOS.items():
            if nome == "Brandes":
                if lado not in lados_brandes:
                    continue
                reps = repeticoes_brandes
            elif lado not in lados:
                continue
            else:
                reps = repeticoes
            m = medir(func, g, origem, repeticoes=reps)
            v, e = g.num_vertices(), g.num_arestas()
            pontos[nome].append({
                "lado": lado, "V": v, "E": e, "V_mais_E": v + e,
                "media_s": m.media_s, "desvio_s": m.desvio_s, "repeticoes": reps,
                "tempo": m.formatar(),
            })
            print(f"{nome} lado={lado} V={v} E={e}: {m.formatar()}", file=sys.stderr)
    blocos = []
    for nome, (complexidade, teorica, _f) in ALGORITMOS.items():
        pts = pontos[nome]
        ajuste = (
            regressao_loglog([p["V_mais_E"] for p in pts], [p["media_s"] for p in pts])
            if len({p["V_mais_E"] for p in pts}) >= 2 else None
        )
        blocos.append({
            "algoritmo": nome,
            "complexidade_teorica": complexidade,
            "inclinacao_teorica": teorica,
            "inclinacao_medida": ajuste["inclinacao"] if ajuste else None,
            "intercepto": ajuste["intercepto"] if ajuste else None,
            "r2": ajuste["r2"] if ajuste else None,
            "pontos": pts,
        })
    return blocos


def desenhar(blocos: list[dict], figura: Path) -> None:
    """Gráfico log-log: pontos medidos e a reta ajustada de cada algoritmo."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=150)
    for bloco in blocos:
        pts = bloco["pontos"]
        if not pts:
            continue
        xs = [p["V_mais_E"] for p in pts]
        ys = [p["media_s"] for p in pts]
        rotulo = bloco["algoritmo"]
        if bloco["inclinacao_medida"] is not None:
            rotulo += f" (b = {bloco['inclinacao_medida']:.2f}; teórico {bloco['complexidade_teorica']})"
        linha = ax.plot(xs, ys, "o", label=rotulo)[0]
        if bloco["inclinacao_medida"] is not None:
            a, b = bloco["intercepto"], bloco["inclinacao_medida"]
            xr = [min(xs), max(xs)]
            ax.plot(xr, [10 ** (a + b * math.log10(x)) for x in xr], "-",
                    color=linha.get_color(), linewidth=1)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("|V| + |E| do G_P sintético")
    ax.set_ylabel("tempo médio (s)")
    ax.grid(True, which="both", linewidth=0.3, alpha=0.5)
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    figura.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figura)
    plt.close(fig)
    print("figura em", figura)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lados", type=int, nargs="*", default=list(LADOS_PADRAO))
    parser.add_argument("--lados-brandes", type=int, nargs="*", default=list(LADOS_BRANDES))
    parser.add_argument("--repeticoes", type=int, default=5)
    parser.add_argument("--repeticoes-brandes", type=int, default=3)
    parser.add_argument("--saida", type=Path, default=None)
    parser.add_argument("--figura", type=Path, default=FIGURA)
    args = parser.parse_args()

    blocos = medir_tamanhos(args.lados, args.lados_brandes, args.repeticoes,
                            args.repeticoes_brandes)
    comando = "python benchmarks/complexidade_empirica.py " + " ".join(
        a.replace("\\", "/") for a in sys.argv[1:]
    )
    resultado = {
        "comando": comando.strip(),
        "data": str(date.today()),
        "maquina": maquina(),
        "semente": SEMENTE,
        "grafo": "G_P de redes sintéticas em grade (transporte.dados.sinteticas)",
        "figura": str(args.figura).replace("\\", "/"),
        "algoritmos": blocos,
    }
    desenhar(blocos, args.figura)
    saida = args.saida or Path("benchmarks/resultados") / f"complexidade-{date.today()}.json"
    gravar_json(resultado, saida)


if __name__ == "__main__":
    main()
