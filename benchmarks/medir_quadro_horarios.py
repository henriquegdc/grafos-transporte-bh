"""Medição sequencial de F-ESPERA-2. Rode a partir da raiz com PYTHONPATH=src."""

import argparse
import json
import platform
from dataclasses import asdict
from pathlib import Path

from transporte.algoritmos.chegada_mais_cedo import chegada_mais_cedo, monte_carlo
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.horarios import construir_gt
from transporte.modelo.parametros import Parametros
from transporte.simulacao.espera import simular_trajeto
from transporte.util.medicao import medir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("feed", type=Path)
    parser.add_argument("--origem")
    parser.add_argument("--destino")
    parser.add_argument("--saida-s", type=int, default=8 * 3600)
    parser.add_argument("--janela-min", type=int, default=20)
    parser.add_argument("--amostras", type=int, default=30)
    parser.add_argument("--semente", type=int, default=42)
    parser.add_argument("--raio-m", type=float, default=Parametros().raio_caminhada_m)
    parser.add_argument("--repeticoes", type=int, default=5)
    parser.add_argument("--json", type=Path)
    parser.add_argument(
        "--sem-medicao",
        action="store_true",
        help="exporta só a consulta e a amostra, sem cronometrar",
    )
    args = parser.parse_args()
    if (args.origem is None) != (args.destino is None):
        parser.error("informe origem e destino juntos")
    rede = ler(args.feed)
    params = Parametros(raio_caminhada_m=args.raio_m)
    origem, destino = args.origem, args.destino
    if origem is None:
        # Escolhe um padrão servido na janela e um destino distinto em seu percurso.
        candidatos = [
            p
            for p in rede.padroes.values()
            if len(set(p.paradas)) > 1
            and any(
                args.saida_s <= h[0] < args.saida_s + args.janela_min * 60
                for h in rede.viagens.get(p.id, ())
            )
        ]
        if not candidatos:
            parser.error("nenhum padrão parte na janela; informe o par ou ajuste a janela")
        padrao = max(candidatos, key=lambda p: (len(p.paradas), p.id))
        origem = padrao.paradas[0]
        destino = next(p for p in reversed(padrao.paradas) if p != origem)

    tempos = {}
    if not args.sem_medicao:
        tempos["construir_gt"] = medir(construir_gt, rede, params, repeticoes=args.repeticoes)
    gt = construir_gt(rede, params)
    consulta = (gt, origem, destino, args.saida_s)
    lote = (*consulta, args.saida_s + args.janela_min * 60, args.amostras, args.semente)
    trajeto = chegada_mais_cedo(*consulta)
    amostras = monte_carlo(*lote)
    estimativa = None
    if any(f.contem(args.saida_s) for f in params.faixas):
        estimativa = simular_trajeto(rede, origem, destino, args.saida_s, params)
    if not args.sem_medicao:
        tempos["chegada_mais_cedo"] = medir(
            chegada_mais_cedo, *consulta, repeticoes=args.repeticoes
        )
        tempos["monte_carlo"] = medir(monte_carlo, *lote, repeticoes=args.repeticoes)
    resultado = {
        "feed": str(args.feed),
        "dia": rede.dia,
        "maquina": platform.platform(),
        "processador": platform.processor(),
        "python": platform.python_version(),
        "V": gt.grafo.num_vertices(),
        "E": gt.grafo.num_arestas(),
        "origem": origem,
        "destino": destino,
        "saida_s": args.saida_s,
        "janela_min": args.janela_min,
        "semente": args.semente,
        "raio_m": args.raio_m,
        "trajeto": asdict(trajeto) if trajeto else None,
        "parcelas_s": trajeto.tempo_por_tipo() if trajeto else None,
        "estimativa_h2_s": estimativa.tempo_por_tipo() if estimativa else None,
        "amostras": [asdict(a) for a in amostras],
        "tempos": {chave: asdict(m) for chave, m in tempos.items()},
    }
    prefixo = "quadro-horarios-consulta" if args.sem_medicao else "quadro-horarios"
    arquivo = args.json or Path("benchmarks/resultados") / f"{prefixo}-{args.feed.stem}.json"
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(arquivo)


if __name__ == "__main__":
    main()
