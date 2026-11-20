"""Tempo e resultados da F-RES-2 (ranking de criticidade) e da F-RES-OPC (falhas em
sequência) em G_P do feed real.

Uso:
    python benchmarks/medir_falhas_extensoes.py dados/brutos/bhtrans.zip
        [--paradas 10] [--linhas 20] [--amostra 30] [--amostra-intermediacao 100]
        [--k 10] [--repeticoes 1] [--saida arquivo.json]

Mede com `medir`: candidatos_criticidade (Brandes amostrado), ranking_criticidade com as
--paradas mais centrais e --linhas sorteadas, e simular_falhas com remoção dirigida (maior
intermediação primeiro) e aleatória de --k paradas. Grava as perdas do ranking e as duas
curvas de eficiência num JSON em benchmarks/resultados/. Custo dominante: (c + 1) * s
Dijkstras do ranking mais 2 (k + 1) s das curvas, s = --amostra, c = candidatos; cada
Dijkstra no G_P real leva cerca de 0,14 s.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import date
from pathlib import Path

from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_gp
from transporte.simulacao.falhas import (
    candidatos_criticidade,
    indexar_linhas,
    ranking_criticidade,
    sequencia_aleatoria,
    sequencia_dirigida,
    simular_falhas,
)
from transporte.util.medicao import medir

SEMENTE = 2026


def _sha256(caminho: Path) -> str | None:
    if caminho.is_dir():  # rede de teste em pasta, usada para validar o script
        return None
    h = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _descrever(rede, falha) -> dict:
    if falha.paradas:
        p = falha.paradas[0]
        return {"tipo": "parada", "id": p, "nome": rede.paradas[p].nome}
    linha = falha.linhas[0]
    return {"tipo": "linha", "id": linha, "nome": rede.linhas[linha].nome}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("caminho", type=Path)
    parser.add_argument("--paradas", type=int, default=10)
    parser.add_argument("--linhas", type=int, default=20)
    parser.add_argument("--amostra", type=int, default=30)
    parser.add_argument("--amostra-intermediacao", type=int, default=100)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--repeticoes", type=int, default=1)
    parser.add_argument("--saida", type=Path, default=None)
    args = parser.parse_args()

    rede = ler(args.caminho)
    visao = construir_gp(rede)
    g = visao.grafo
    indice = indexar_linhas(rede)
    argumentos = (
        f"--paradas {args.paradas} --linhas {args.linhas} --amostra {args.amostra} "
        f"--amostra-intermediacao {args.amostra_intermediacao} --k {args.k} "
        f"--repeticoes {args.repeticoes}"
    )
    resultado: dict = {
        "comando": "python benchmarks/medir_falhas_extensoes.py "
        + str(args.caminho).replace("\\", "/") + " " + argumentos,
        "feed": {"caminho": str(args.caminho).replace("\\", "/"),
                 "sha256": _sha256(args.caminho)},
        "maquina": {
            "plataforma": platform.platform(),
            "processador": platform.processor(),
            "python": platform.python_version(),
        },
        "rede": {"dia": str(rede.dia), "paradas": len(rede.paradas),
                 "linhas": len(rede.linhas)},
        "G_P": {"V": g.num_vertices(), "E": g.num_arestas()},
        "semente": SEMENTE,
        "parametros": vars(args) | {"caminho": str(args.caminho), "saida": None},
    }
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

    # F-RES-2: candidatos e ranking.
    candidatos = candidatos_criticidade(
        visao, args.paradas, indice, args.linhas, args.amostra_intermediacao, SEMENTE
    )
    t_cand = medir(candidatos_criticidade, visao, args.paradas, indice, args.linhas,
                   args.amostra_intermediacao, SEMENTE, repeticoes=args.repeticoes)
    ranking = ranking_criticidade(visao, candidatos, indice, args.amostra, SEMENTE)
    t_rank = medir(ranking_criticidade, visao, candidatos, indice, args.amostra, SEMENTE,
                   repeticoes=args.repeticoes)
    resultado["ranking"] = {
        "candidatos": len(candidatos),
        "tempo_candidatos": t_cand.formatar(),
        "tempo_ranking": t_rank.formatar(),
        "itens": [
            _descrever(rede, r.falha) | {
                "perda_eficiencia": r.perda_eficiencia,
                "desconectadas": len(r.paradas_desconectadas),
                "isoladas": len(r.paradas_isoladas),
            }
            for r in ranking
        ],
    }
    print("ranking:", json.dumps(resultado["ranking"], ensure_ascii=False)[:2000])

    # F-RES-OPC: remoção dirigida contra aleatória.
    dirigida = sequencia_dirigida(visao, args.k, args.amostra_intermediacao, SEMENTE)
    aleatoria = sequencia_aleatoria(visao, args.k, SEMENTE)
    curvas = {}
    for nome, falhas in (("dirigida", dirigida), ("aleatoria", aleatoria)):
        passos = simular_falhas(visao, falhas, indice, args.amostra, SEMENTE)
        t = medir(simular_falhas, visao, falhas, indice, args.amostra, SEMENTE,
                  repeticoes=args.repeticoes)
        curvas[nome] = {
            "paradas": [f.paradas[0] for f in falhas],
            "perda_por_passo": [p.perda_eficiencia for p in passos],
            "desconectadas_por_passo": [len(p.paradas_desconectadas) for p in passos],
            "componentes_por_passo": [len(p.componentes_depois) for p in passos],
            "tempo": t.formatar(),
        }
        print(nome, json.dumps(curvas[nome], ensure_ascii=False))
    resultado["sequencias"] = curvas

    saida = args.saida or Path("benchmarks/resultados") / f"falhas-extensoes-{date.today()}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(resultado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("gravado em", saida)


if __name__ == "__main__":
    main()
