"""Medições reproduzíveis de F-ESPERA, separando GTFS, estimativa, construção e consulta.

Uso: PYTHONPATH=src python benchmarks/medir_espera.py dados/brutos/bhtrans.zip
Saída JSON; não baixa nem modifica o feed. Tempos com transporte.util.medicao.medir.
"""

import argparse
import hashlib
import json
import platform
import subprocess
from dataclasses import asdict
from pathlib import Path

from transporte.algoritmos.trajeto import trajeto_mais_rapido
from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_ge
from transporte.modelo.parametros import Parametros
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos, simular_trajeto
from transporte.util.medicao import medir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("caminho", type=Path)
    parser.add_argument("--repeticoes", type=int, default=5)
    args = parser.parse_args()
    rede = ler(args.caminho)
    intervalos = estimar_intervalos(rede)
    esperas = calcular_esperas(intervalos)
    faixa = "pico_manha"
    padrao = max(
        (p for pid, p in rede.padroes.items() if (pid, faixa) in esperas),
        key=lambda p: (len(p.paradas), p.id),
    )
    origem = padrao.paradas[0]
    inicio = rede.paradas[origem]
    # O último ponto de uma circular pode estar ao lado do primeiro.
    destino = max(
        padrao.paradas,
        key=lambda p: (
            (rede.paradas[p].lat - inicio.lat) ** 2 + (rede.paradas[p].lon - inicio.lon) ** 2
        ),
    )
    ge = construir_ge(rede, faixa, esperas=esperas)
    trajeto = trajeto_mais_rapido(ge, origem, destino)
    tempos = {
        "estimar_intervalos": medir(estimar_intervalos, rede, repeticoes=args.repeticoes),
        "calcular_esperas": medir(calcular_esperas, intervalos, repeticoes=args.repeticoes),
        "construir_ge": medir(
            construir_ge, rede, faixa, esperas=esperas, repeticoes=args.repeticoes
        ),
        "consultar_ge_pronto": medir(
            trajeto_mais_rapido, ge, origem, destino, repeticoes=args.repeticoes
        ),
        "simular_trajeto_completo": medir(
            simular_trajeto, rede, origem, destino, 28800, repeticoes=args.repeticoes
        ),
    }
    por_faixa = {}
    for f in Parametros().faixas:
        ativos = sum(
            any(h and f.contem(h[0]) for h in rede.viagens.get(pid, ())) for pid in rede.padroes
        )
        estimados = sum(chave[1] == f.nome for chave in intervalos)
        por_faixa[f.nome] = {
            "padroes_com_servico": ativos,
            "estimados": estimados,
            "fallback": ativos - estimados,
        }
    chip = ""
    if platform.system() == "Darwin":
        chip = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    with args.caminho.open("rb") as feed:
        sha256 = hashlib.file_digest(feed, "sha256").hexdigest()
    resultado = {
        "feed": str(args.caminho),
        "sha256": sha256,
        "maquina": {
            "plataforma": platform.platform(),
            "python": platform.python_version(),
            "processador": chip or platform.processor(),
        },
        "rede": {
            "dia": rede.dia,
            "paradas": len(rede.paradas),
            "linhas": len(rede.linhas),
            "padroes": len(rede.padroes),
            "viagens": len(rede.viagens_por_id),
            "inconsistencias": len(rede.inconsistencias),
        },
        "faixa": faixa,
        "V": ge.grafo.num_vertices(),
        "E": ge.grafo.num_arestas(),
        "cobertura": por_faixa,
        "consulta": {
            "origem": origem,
            "destino": destino,
            "saida_s": 28800,
            "total_s": trajeto.tempo_total_s if trajeto else None,
            "parcelas_s": trajeto.tempo_por_tipo() if trajeto else None,
        },
        "tempos": {nome: asdict(m) for nome, m in tempos.items()},
    }
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
