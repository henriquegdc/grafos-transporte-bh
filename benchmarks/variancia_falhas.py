"""Variação da perda de eficiência amostrada da F-RES numa falha de linha, no feed real.

Uso: python benchmarks/variancia_falhas.py [dados/brutos/bhtrans.zip] [--exata]

Simula a falha da linha 832 (`562146`, a que mais tira paradas da rede principal na
varredura de benchmarks/medir_falhas.py) com 30, 100 e 300 origens e várias sementes, e
imprime a perda de cada uma. Com --exata, também roda com todas as origens (cerca de 2 x
9.659 Dijkstras: dezenas de minutos). Mostra por que a perda amostrada de uma falha que
desconecta poucas paradas tem cauda pesada: a estimativa salta quando a amostra sorteia
uma das paradas desconectadas como origem.
"""

from __future__ import annotations

import sys
import time

from transporte.dados.leitor_gtfs import ler
from transporte.modelo.construtores import construir_gp
from transporte.simulacao.falhas import Falha, indexar_linhas, simular_falha

LINHA = "562146"
CASOS = [(30, s) for s in (2026, 1, 2, 3, 4)] + [(100, s) for s in (2026, 1, 2, 3, 4)] + [
    (300, s) for s in (1, 2)
]


def main(caminho: str, exata: bool) -> None:
    rede = ler(caminho)
    visao = construir_gp(rede)
    indice = indexar_linhas(rede)
    falha = Falha(linhas=(LINHA,))
    for amostra, semente in CASOS:
        r = simular_falha(visao, falha, indice, amostra=amostra, semente=semente)
        print(
            f"amostra={amostra} semente={semente} perda={r.perda_eficiencia:.4%} "
            f"desconectadas={len(r.paradas_desconectadas)}",
            flush=True,
        )
    if exata:
        inicio = time.perf_counter()
        r = simular_falha(visao, falha, indice, amostra=None)
        print(
            f"exata: antes={r.eficiencia_antes:.6e} depois={r.eficiencia_depois:.6e} "
            f"perda={r.perda_eficiencia:.4%} tempo={time.perf_counter() - inicio:.0f}s",
            flush=True,
        )


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--exata"]
    main(args[0] if args else "dados/brutos/bhtrans.zip", "--exata" in sys.argv)
