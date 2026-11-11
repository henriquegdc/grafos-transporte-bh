"""Construtor da visão G_L · linhas (F-BALD, RF-GRF-06; docs/fontes/modelagem.md §3.4).

Um vértice por padrão de linha; aresta P -> Q quando dá para descer de P e embarcar em Q na
mesma parada ou em paradas a até o raio de caminhada. Lê da Rede os mesmos campos que os
construtores de G_P e G_E (`RedeConstrutores`) e reaproveita a grade espacial deles para
achar os pares de paradas próximas.

Notação das complexidades:
    V: paradas da Rede.     K: pares de paradas a até o raio.
    L: soma do número de paradas de cada padrão.
    C: trocas candidatas, isto é, soma, sobre cada parada x de desembarque de cada padrão,
       dos embarques nas paradas a até o raio de x. Na prática C ~ L * (vizinhas de uma
       parada) * (padrões que embarcam numa parada).

estado: implementado
"""

from __future__ import annotations

from transporte.grafo.grafo import Grafo
from transporte.modelo.construtores import (
    RedeConstrutores,
    _paradas_conhecidas,
    _pares_caminhada,
    _partidas_na_faixa,
)
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import BALDEACAO, Transferencia, VisaoGL


def _proximas(
    rede: RedeConstrutores, raio_m: float
) -> dict[str, tuple[tuple[str, float], ...]]:
    """Parada -> paradas a até raio_m, com a distância; a própria parada primeiro, com 0 m,
    e as demais em ordem crescente de distância. Tempo esperado O(V + K log K)."""
    paradas = list(rede.paradas.values())
    vizinhas: dict[str, list[tuple[str, float]]] = {p.id: [] for p in paradas}
    for i, j, d in _pares_caminhada(paradas, raio_m):
        vizinhas[paradas[i].id].append((paradas[j].id, d))
        vizinhas[paradas[j].id].append((paradas[i].id, d))
    return {
        pid: ((pid, 0.0), *sorted(lista, key=lambda par: (par[1], par[0])))
        for pid, lista in vizinhas.items()
    }


def _nao_dominadas(candidatas: list[tuple[int, int, float, str, str]]) -> tuple[Transferencia, ...]:
    """Fronteira de Pareto das trocas (i, j, distância, x, y) de uma aresta P -> Q.

    Ordena por desembarque decrescente (i), depois embarque crescente (j) e caminhada
    crescente, e guarda uma troca só se ela embarca mais cedo que todas as que descem mais
    tarde. Na saída, i decresce e j decresce junto: quem embarcou em P na posição b usa a
    última troca com i > b, que é a de menor j. Tempo O(c log c) para c candidatas.
    """
    candidatas.sort(key=lambda t: (-t[0], t[1], t[2]))
    fronteira: list[Transferencia] = []
    menor_j = None
    for i, j, _d, x, y in candidatas:
        if menor_j is None or j < menor_j:
            fronteira.append((i, x, j, y))
            menor_j = j
    return tuple(fronteira)


def construir_gl(
    rede: RedeConstrutores,
    params: Parametros | None = None,
    faixa: str | None = None,
) -> VisaoGL:
    """Constrói G_L: um vértice por padrão e uma aresta por par de padrões com troca.

    Entradas:
        rede: modelo normalizado (P0-DADOS), já recortado se for o caso.
        params: parâmetros da modelagem; usa o raio de caminhada. None usa os padrões.
        faixa: nome de uma faixa de params.faixas. Se informada, só entram os padrões com
            partida na faixa (alguma viagem cujo primeiro horário cai nela, a regra D10 do
            G_E), para a G_L concordar com o G_E da mesma faixa. None usa todos.
    Saída: VisaoGL. Os vértices seguem a ordem de rede.padroes.
    Arestas: P -> Q, peso 1 e tipo BALDEACAO, se existe uma parada x de P em posição
        i >= 1 e uma parada y de Q em posição j <= len(Q) - 2 com x == y ou a até o raio.
        A aresta guarda as trocas não dominadas (ver VisaoGL.transferencias).
    Casos de borda: padrão com menos de duas paradas fica fora (não leva a lugar nenhum);
        há laço P -> P quando dá para descer de P e embarcar nele de novo numa posição
        anterior, a pé ou na mesma parada de um padrão circular; o algoritmo só usa o laço
        se ele embarca mais cedo do que o passageiro já está; padrão circular tem uma
        entrada por ocorrência da parada;
        padrão com parada inexistente levanta KeyError; faixa inexistente levanta
        KeyError; rede vazia devolve grafo vazio.
    Complexidade: tempo O(V + K log K + L + C log C) esperado (grade espacial; O(V²) no pior
        caso da grade); espaço O(V + K + L + E + T), com T <= C trocas guardadas. As
        candidatas de um padrão são descartadas antes do próximo, então o pico extra é o
        das candidatas de um padrão só.
    """
    params = params or Parametros()
    f = params.faixa(faixa) if faixa is not None else None
    g = Grafo()
    visao = VisaoGL(grafo=g, nome="G_L", faixa=faixa)

    for padrao in rede.padroes.values():
        _paradas_conhecidas(rede, padrao)
        if len(padrao.paradas) < 2:
            continue
        if f is not None and not _partidas_na_faixa(
            rede.viagens.get(padrao.id, ()), f.inicio_s, f.fim_s
        ):
            continue
        v = g.adicionar_vertice(padrao.id)
        visao.vertice_do_padrao[padrao.id] = v
        visao.padrao_do_vertice.append(padrao.id)
        visao.paradas_do_padrao.append(tuple(padrao.paradas))

    embarques: dict[str, list[tuple[int, int]]] = {}
    for v, seq in enumerate(visao.paradas_do_padrao):
        for j in range(len(seq) - 1):
            embarques.setdefault(seq[j], []).append((v, j))
    visao.embarques = {pid: tuple(lista) for pid, lista in embarques.items()}
    visao.proximas = _proximas(rede, params.raio_caminhada_m)

    for p, seq in enumerate(visao.paradas_do_padrao):
        # Q -> trocas candidatas (i, j, distância, x, y) de P para Q.
        candidatas: dict[int, list[tuple[int, int, float, str, str]]] = {}
        for i in range(1, len(seq)):
            x = seq[i]
            for y, d in visao.proximas[x]:
                for q, j in visao.embarques.get(y, ()):
                    # q == p fica: descer, andar (ou esperar o próximo ônibus, num padrão
                    # circular) e pegar o mesmo padrão mais atrás é uma baldeação real.
                    candidatas.setdefault(q, []).append((i, j, d, x, y))
        for q in sorted(candidatas):
            g.adicionar_aresta(p, q, 1.0, BALDEACAO)
            visao.transferencias.append(_nao_dominadas(candidatas[q]))
    return visao
