"""F-ESPERA: intervalos por padrão/faixa, espera H/2 e simulação em G_E.

As partidas já incluem a expansão de frequencies.txt feita pelo leitor. Usamos o
primeiro horário da viagem (D10), sem misturar padrões da mesma linha ou visitas
repetidas à mesma parada em linhas circulares. estado: implementado.
"""

from collections.abc import Mapping
from math import isfinite

from transporte.algoritmos.trajeto import Trajeto, trajeto_mais_rapido
from transporte.dados.modelo import Rede
from transporte.modelo.construtores import construir_ge
from transporte.modelo.parametros import Parametros


def estimar_intervalos(
    rede: Rede, params: Parametros | None = None
) -> dict[tuple[str, str], float]:
    """Média dos intervalos entre partidas distintas na faixa; segundos.

    As faixas usam [início, fim). Ordena e deduplica o primeiro horário de cada
    viagem; não altera a Rede. Menos de duas partidas: chave ausente, para o
    construtor aplicar espera_padrao_s quando houver serviço. Horários GTFS
    acima de 24h são preservados e exigem uma faixa que os contenha.
    Tempo O(PF + FN + N log N), espaço O(N + PF); N viagens, P padrões, F faixas.
    """
    params = params or Parametros()
    intervalos = {}
    for padrao_id in rede.padroes:
        partidas = sorted({h[0] for h in rede.viagens.get(padrao_id, ()) if h})
        for faixa in params.faixas:
            na_faixa = [t for t in partidas if faixa.contem(t)]
            if len(na_faixa) >= 2:
                # A soma das diferenças consecutivas é a última menos a primeira.
                intervalos[(padrao_id, faixa.nome)] = (na_faixa[-1] - na_faixa[0]) / (
                    len(na_faixa) - 1
                )
    return intervalos


def calcular_esperas(intervalos: Mapping[tuple[str, str], float]) -> dict[tuple[str, str], float]:
    """H/2 por chave, em segundos; recusa intervalo negativo, NaN ou infinito.

    Versão essencial: chegada ao acaso e intervalos regulares. Não aplica a
    correção de irregularidade E[H²]/(2 E[H]). Não altera a tabela recebida.
    Tempo e espaço O(número de estimativas).
    """
    esperas = {}
    for chave, intervalo in intervalos.items():
        if not isfinite(intervalo) or intervalo < 0:
            raise ValueError(f"intervalo deve ser finito e não negativo: {chave}")
        esperas[chave] = intervalo / 2
    return esperas


def simular_trajeto(
    rede: Rede, origem: str, destino: str, saida_s: int, params: Parametros | None = None
) -> Trajeto | None:
    """Seleciona faixa fixa pela saída e reutiliza construir_ge e F-ROTA.

    Fora das faixas: ValueError; parada ausente: KeyError; inalcançável: None.
    saida_s usa segundos desde 00:00, sem módulo de 24h. A faixa da saída
    permanece fixa mesmo se o trajeto cruzar outra faixa; não consulta a próxima
    partida do quadro de horários (G_T é F-ESPERA-2). O resultado de F-ROTA já
    fornece tempo_por_tipo() e os trechos, sem duplicar Dijkstra/reconstrução.
    Custo da estimativa + construção de G_E + Dijkstra O((V + E) log V).
    Espaço O(N + PF + V + E), incluindo estimativas, visão e heap do Dijkstra.
    """
    params = params or Parametros()
    faixa = next((f for f in params.faixas if f.contem(saida_s)), None)
    if faixa is None:
        raise ValueError("Horário de saída fora das faixas de serviço configuradas.")
    esperas = calcular_esperas(estimar_intervalos(rede, params))
    ge = construir_ge(rede, faixa.nome, params=params, esperas=esperas)
    return trajeto_mais_rapido(ge, origem, destino)
