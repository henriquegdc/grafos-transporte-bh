"""Roteamento dependente do horário e amostragem das saídas (F-ESPERA-2)."""

from dataclasses import dataclass
from math import inf, isfinite
from random import Random

from transporte.algoritmos.trajeto import A_PE, ESPERA, ONIBUS, Trajeto, Trecho
from transporte.grafo.heap import HeapMin
from transporte.modelo.horarios import VisaoGT


@dataclass(frozen=True)
class Passo:
    origem: int
    destino: int
    partida: float
    chegada: float
    veiculo: tuple[str, int] | None


def _trechos(gt: VisaoGT, passos: list[Passo], saida_s: float) -> tuple[Trecho, ...]:
    trechos = []
    instante = saida_s
    i = 0
    while i < len(passos):
        primeiro = passos[i]
        veiculo = primeiro.veiculo
        j = i + 1
        # Uma circular pode voltar à mesma parada mais tarde. O intervalo
        # entre os passos escolhidos é espera no ponto, mesmo no mesmo veículo.
        while (
            j < len(passos)
            and passos[j].veiculo == veiculo
            and passos[j].partida == passos[j - 1].chegada
        ):
            j += 1
        segmentos = passos[i:j]
        ultimo = segmentos[-1]
        i = j
        origem = gt.parada_do_vertice[primeiro.origem]
        padrao = veiculo[0] if veiculo else None
        if veiculo:
            trechos.append(Trecho(ESPERA, (origem,), primeiro.partida - instante, padrao))
        paradas = (origem, *(gt.parada_do_vertice[p.destino] for p in segmentos))
        trechos.append(
            Trecho(ONIBUS if veiculo else A_PE, paradas, ultimo.chegada - primeiro.partida, padrao)
        )
        instante = ultimo.chegada
    return tuple(trechos)


def chegada_mais_cedo(gt: VisaoGT, origem: str, destino: str, saida_s: float) -> Trajeto | None:
    """Devolve o Trajeto de menor chegada desde saida_s no dia de serviço de G_T.

    Dijkstra rotula instantes absolutos. Cada relaxamento consulta o próximo
    evento viável ou soma a caminhada. Parada ausente: KeyError; saída negativa
    ou não finita: ValueError; inalcançável: None; mesma parada: trajeto vazio.
    Com heap preguiçoso e arestas paralelas: tempo O((V+E) log(E+2) + E log(k+1))
    e espaço auxiliar O(V+E), com k horários no maior quadro.
    """
    origem_v = gt.vertice_da_parada[origem]
    destino_v = gt.vertice_da_parada[destino]
    if not isfinite(saida_s) or saida_s < 0:
        raise ValueError("A saída deve ser finita e não negativa.")
    chegadas = {origem_v: saida_s}
    anteriores: dict[int, Passo] = {}
    fila = HeapMin()
    fila.inserir(saida_s, origem_v)
    while not fila.vazio():
        instante, u = fila.extrair_min()
        if instante != chegadas[u]:
            continue
        if u == destino_v:
            break
        for v, peso, aresta in gt.grafo.vizinhos(u):
            quadro = gt.quadros.get(aresta)
            if quadro is None:
                partida, chegada, veiculo = instante, instante + peso, None
            else:
                evento = quadro.proximo(instante)
                if evento is None:
                    continue
                partida, chegada, viagem = evento
                veiculo = (quadro.padrao, viagem)
            if chegada < chegadas.get(v, inf):
                chegadas[v] = chegada
                anteriores[v] = Passo(u, v, partida, chegada, veiculo)
                fila.inserir(chegada, v)
    if destino_v not in chegadas:
        return None
    passos = []
    v = destino_v
    while v != origem_v:
        passo = anteriores[v]
        passos.append(passo)
        v = passo.origem
    passos.reverse()
    trechos = _trechos(gt, passos, saida_s)
    embarques = sum(t.tipo == ONIBUS for t in trechos)
    return Trajeto(origem, destino, chegadas[destino_v] - saida_s, max(0, embarques - 1), trechos)


@dataclass(frozen=True)
class Amostra:
    saida_s: int
    total_s: float | None
    espera_s: float | None


def monte_carlo(
    gt: VisaoGT, origem: str, destino: str, inicio_s: int, fim_s: int, amostras: int, semente: int
) -> list[Amostra]:
    """Sorteia S segundos uniformes em [inicio_s, fim_s) com reposição e semente local.

    Retorna cada saída, total e espera; uma saída sem caminho conserva dois None.
    Janela vazia, negativa ou S < 1: ValueError. Tempo O(S vezes uma consulta);
    espaço O(S+V+E), pois só uma consulta fica em memória por vez.
    """
    if inicio_s < 0 or fim_s <= inicio_s or amostras < 1:
        raise ValueError("Informe uma janela válida e pelo menos uma amostra.")
    sorteio = Random(semente)
    resultado = []
    for _ in range(amostras):
        saida = sorteio.randrange(inicio_s, fim_s)
        trajeto = chegada_mais_cedo(gt, origem, destino, saida)
        if trajeto is None:
            resultado.append(Amostra(saida, None, None))
        else:
            resultado.append(
                Amostra(saida, trajeto.tempo_total_s, trajeto.tempo_por_tipo()[ESPERA])
            )
    return resultado
