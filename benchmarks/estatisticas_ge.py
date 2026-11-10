"""Contagens de P0-MODELO no feed real: arestas por tipo, piso de 1 s e padrões circulares.

Uso: PYTHONPATH=src python benchmarks/estatisticas_ge.py [dados/brutos/bhtrans.zip]

Precisa da leitura do GTFS (transporte.dados, P0-DADOS, PR #42) e do feed baixado por
scripts/baixar_gtfs.py. Não mede tempo: só conta, sobre G_P e sobre G_E do pico da manhã,
os números citados em "Resultados para o relatório" do arquivo da feature. Imprime também
o SHA-256 do feed, para amarrar os números ao arquivo lido.
"""

from __future__ import annotations

import hashlib
import sys
from itertools import pairwise
from pathlib import Path

from transporte.modelo.construtores import construir_ge, construir_gp
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import CAMINHADA, VIAGEM

FAIXA = "pico_manha"


def _por_tipo(grafo) -> tuple[dict[str, int], dict[str, int]]:
    """Total de arestas e de arestas no piso, por tipo. Tempo O(E)."""
    piso = Parametros().peso_minimo_s
    total: dict[str, int] = {}
    no_piso: dict[str, int] = {}
    for a in range(grafo.num_arestas()):
        _, _, peso, tipo = grafo.aresta(a)
        total[tipo] = total.get(tipo, 0) + 1
        if peso == piso:
            no_piso[tipo] = no_piso.get(tipo, 0) + 1
    return total, no_piso


def main(caminho: str) -> None:
    # Import local: transporte.dados chega com o PR #42 (P0-DADOS).
    from transporte.dados.leitor_gtfs import ler

    arquivo = Path(caminho)
    if arquivo.is_file():
        print("sha256", hashlib.sha256(arquivo.read_bytes()).hexdigest())
    rede = ler(arquivo)
    print(
        f"rede: dia={rede.dia} paradas={len(rede.paradas)} padroes={len(rede.padroes)} "
        f"viagens={len(rede.viagens_por_id)}"
    )

    # D8: o leitor descarta a viagem inteira quando os horários decrescem.
    fora_de_ordem = sum("fora de ordem" in erro for erro in rede.inconsistencias)
    print(
        f"inconsistencias do leitor: {len(rede.inconsistencias)}; "
        f"viagens descartadas por horario fora de ordem: {fora_de_ordem}"
    )

    circulares = sum(len(set(p.paradas)) < len(p.paradas) for p in rede.padroes.values())
    print(f"padroes com parada repetida (D11): {circulares}/{len(rede.padroes)}")

    zeros = sum(
        h1 == h0
        for viagens in rede.viagens.values()
        for horarios in viagens
        for h0, h1 in pairwise(horarios)
    )
    print(f"diferencas de 0 s entre paradas consecutivas, somadas sobre as viagens: {zeros}")

    em_padrao = {parada for p in rede.padroes.values() for parada in p.paradas}
    print(f"paradas fora de todo padrao do dia: {len(rede.paradas) - len(em_padrao)}")

    for nome, visao in (
        ("G_P", construir_gp(rede)),
        (f"G_E[{FAIXA}]", construir_ge(rede, FAIXA)),
    ):
        g = visao.grafo
        total, no_piso = _por_tipo(g)
        print(f"{nome}: V={g.num_vertices()} E={g.num_arestas()}")
        for tipo in sorted(total):
            print(f"  {tipo}: {total[tipo]}")
        for tipo in (VIAGEM, CAMINHADA):
            print(f"  no piso de 1 s, {tipo}: {no_piso.get(tipo, 0)}/{total.get(tipo, 0)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dados/brutos/bhtrans.zip")
