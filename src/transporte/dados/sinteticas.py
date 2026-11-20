"""Redes sintéticas de tamanho crescente para o estudo de escala (RF-DAD-05, F-AVAL-OPC).

Uma rede sintética é uma grade `lado x lado` de paradas perto do centro de BH, com uma linha
de ônibus reta em cada fileira e em cada coluna (ida e volta) e a caminhada que os
construtores já criam entre paradas próximas. Ela sai no mesmo formato da `Rede` de P0-DADOS
(paradas, linhas, padrões, viagens e partidas), então passa por `construir_gp` e
`construir_ge` sem nenhuma adaptação, e os algoritmos rodam exatamente como no feed real.

Por que uma grade: o tamanho cresce de forma controlada (V = lado², E de G_P cerca de 12 V
com os parâmetros padrão, perto das 12,7 arestas por parada do G_P real) e a estrutura
local é a mesma em todos os tamanhos. Assim, numa regressão do tempo contra V + E, a
inclinação mede o algoritmo, e não uma mudança de forma do grafo.

Com espaçamento de 200 m e o raio de caminhada padrão de 300 m, cada parada tem caminhada
para as 8 vizinhas da grade (200 m nas retas, 283 m nas diagonais). A semente controla um
pequeno deslocamento das coordenadas (que pode tirar ou pôr algumas diagonais no raio), o
tempo de cada trecho e os horários das viagens; mesma semente, mesma rede (RNF-07).

Notação: n = lado (paradas por fileira), V = n², T = viagens por padrão.

estado: implementado
"""

from __future__ import annotations

import math
import random

from transporte.dados.modelo import Linha, Padrao, Parada, Rede, Viagem

# Centro aproximado de BH (Praça Sete), só para as coordenadas parecerem reais no mapa.
_LAT0 = -19.9191
_LON0 = -43.9386
_METROS_POR_GRAU_LAT = 6_371_000.0 * math.pi / 180  # mesmo raio da haversine dos construtores
_TIPO_ONIBUS = 3  # route_type do GTFS para ônibus
_INICIO_S = 6 * 3600  # primeira partida às 06:00, dentro da faixa pico_manha

LADOS_PADRAO: tuple[int, ...] = (10, 15, 20, 30, 40, 55, 70, 85, 100)
"""Lados da grade usados pelo estudo de escala: V vai de 100 a 10.000 paradas, o que cobre
o tamanho do G_P real (9.660 paradas)."""


def gerar_rede_sintetica(
    lado: int,
    semente: int = 0,
    espacamento_m: float = 200.0,
    deslocamento_m: float = 10.0,
    viagens_por_padrao: int = 4,
    trecho_min_s: int = 60,
    trecho_max_s: int = 180,
    intervalo_min_s: int = 600,
    intervalo_max_s: int = 1200,
) -> Rede:
    """Gera uma rede sintética em grade com `lado * lado` paradas (RF-DAD-05).

    Entradas:
        lado: n, paradas por fileira e por coluna; inteiro >= 1.
        semente: semente do `random.Random` local (o estado global do `random` não muda).
        espacamento_m: distância entre paradas vizinhas da grade, em metros.
        deslocamento_m: cada coordenada recebe um ruído uniforme em [-d, d] metros.
        viagens_por_padrao: T, número de viagens de cada padrão (todas com o mesmo tempo
            por trecho, como um horário programado); inteiro >= 1.
        trecho_min_s, trecho_max_s: faixa do tempo de viagem sorteado para cada trecho.
        intervalo_min_s, intervalo_max_s: faixa do intervalo sorteado entre partidas.
    Saída: Rede com V = n² paradas ("S<i>_<j>"), 2n linhas ("F<i>" nas fileiras e "C<j>"
        nas colunas), dois padrões por linha ("<linha>-ida" e "<linha>-volta"), T viagens
        por padrão em `viagens_por_id` e `viagens`/`partidas` já calculados por
        `recalcular_partidas`. Com n = 1 não há trecho, então não há linha nem padrão.
    Casos de borda: lado < 1, viagens_por_padrao < 1, espaçamento <= 0, deslocamento < 0
        ou faixas invertidas levantam ValueError.
    Complexidade: tempo O(n² T) para criar as viagens (2n linhas, 2 padrões cada, T viagens
        de n horários) mais O(n² T log(n T)) da ordenação em `recalcular_partidas`;
        espaço O(n² T).
    """
    if lado < 1:
        raise ValueError(f"lado deve ser >= 1, recebeu {lado}")
    if viagens_por_padrao < 1:
        raise ValueError(f"viagens_por_padrao deve ser >= 1, recebeu {viagens_por_padrao}")
    if espacamento_m <= 0 or deslocamento_m < 0:
        raise ValueError("espacamento_m deve ser > 0 e deslocamento_m >= 0")
    if not 0 < trecho_min_s <= trecho_max_s or not 0 < intervalo_min_s <= intervalo_max_s:
        raise ValueError("faixas de tempo devem ser positivas e com mínimo <= máximo")

    sorteio = random.Random(semente)
    graus_lat = 1.0 / _METROS_POR_GRAU_LAT
    graus_lon = graus_lat / math.cos(math.radians(_LAT0))

    paradas: dict[str, Parada] = {}
    for i in range(lado):
        for j in range(lado):
            norte = i * espacamento_m + sorteio.uniform(-deslocamento_m, deslocamento_m)
            leste = j * espacamento_m + sorteio.uniform(-deslocamento_m, deslocamento_m)
            ident = _id_parada(i, j)
            paradas[ident] = Parada(
                ident, f"Sintética {i},{j}", _LAT0 + norte * graus_lat, _LON0 + leste * graus_lon
            )

    linhas: dict[str, Linha] = {}
    padroes: dict[str, Padrao] = {}
    viagens: dict[str, Viagem] = {}
    if lado >= 2:
        sequencias = [(f"F{i}", [_id_parada(i, j) for j in range(lado)]) for i in range(lado)]
        sequencias += [(f"C{j}", [_id_parada(i, j) for i in range(lado)]) for j in range(lado)]
        for linha_id, seq in sequencias:
            linhas[linha_id] = Linha(linha_id, f"Linha sintética {linha_id}", _TIPO_ONIBUS)
            for sentido, paradas_padrao in (("ida", seq), ("volta", seq[::-1])):
                padrao_id = f"{linha_id}-{sentido}"
                padroes[padrao_id] = Padrao(padrao_id, linha_id, tuple(paradas_padrao))
                trechos = [
                    sorteio.randint(trecho_min_s, trecho_max_s)
                    for _ in range(len(paradas_padrao) - 1)
                ]
                partida = _INICIO_S + sorteio.randint(0, intervalo_max_s)
                for k in range(viagens_por_padrao):
                    horarios = [partida]
                    for t in trechos:
                        horarios.append(horarios[-1] + t)
                    viagem_id = f"{padrao_id}-v{k}"
                    viagens[viagem_id] = Viagem(viagem_id, padrao_id, "SINT", tuple(horarios))
                    partida += sorteio.randint(intervalo_min_s, intervalo_max_s)

    rede = Rede(
        paradas=paradas,
        linhas=linhas,
        padroes=padroes,
        partidas={},
        viagens_por_id=viagens,
        dia=f"sintetica-{lado}x{lado}-s{semente}",
    )
    rede.recalcular_partidas()
    return rede


def redes_crescentes(
    lados: tuple[int, ...] = LADOS_PADRAO, semente: int = 0
) -> list[tuple[int, Rede]]:
    """Uma rede sintética por lado, na ordem dada, todas com a mesma semente.

    Saída: lista de (lado, Rede). Complexidade: a soma das de `gerar_rede_sintetica`.
    """
    return [(lado, gerar_rede_sintetica(lado, semente)) for lado in lados]


def _id_parada(i: int, j: int) -> str:
    return f"S{i}_{j}"
