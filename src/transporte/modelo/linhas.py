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


def _trocas_nao_dominadas(
    seq: tuple[str, ...],
    proximas: dict[str, tuple[tuple[str, float], ...]],
    embarques: dict[str, tuple[tuple[int, int], ...]],
) -> dict[int, list[Transferencia]]:
    """Para um padrão P (paradas `seq`): Q -> trocas não dominadas de P para Q.

    Percorre as posições de descida i de P da última para a segunda. Em cada i, acha para
    cada Q o embarque mais cedo j (no empate, a menor caminhada, porque `proximas` vem em
    ordem de distância) e guarda a troca só se j é menor que o de todas as trocas já
    guardadas, que descem mais tarde. Assim a fronteira de Pareto sai pronta, com i e j
    decrescentes, sem juntar e ordenar as candidatas: quem embarcou em P na posição b usa a
    última troca com i > b, que é a de menor j.
    Complexidade: tempo O(c) para as c candidatas de P; espaço O(número de Q + guardadas).
    """
    fronteira: dict[int, list[Transferencia]] = {}
    menor_j: dict[int, int] = {}
    for i in range(len(seq) - 1, 0, -1):
        x = seq[i]
        nesta: dict[int, tuple[int, str]] = {}  # Q -> (j, y) do melhor embarque desta descida
        for y, _d in proximas[x]:
            for q, j in embarques.get(y, ()):
                atual = nesta.get(q)
                if atual is None or j < atual[0]:
                    nesta[q] = (j, y)
        for q, (j, y) in nesta.items():
            if q not in menor_j or j < menor_j[q]:
                menor_j[q] = j
                fronteira.setdefault(q, []).append((i, x, j, y))
    return fronteira


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
    Complexidade: tempo O(V + K log K + L + C) esperado (grade espacial; O(V²) no pior
        caso da grade); espaço O(V + K + L + E + T), com T <= C trocas guardadas. As
        candidatas não são guardadas: cada uma é comparada e descartada na hora.
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
        # Q == P fica: descer, andar (ou esperar o próximo ônibus, num padrão circular) e
        # pegar o mesmo padrão mais atrás é uma baldeação real.
        fronteira = _trocas_nao_dominadas(seq, visao.proximas, visao.embarques)
        for q in sorted(fronteira):
            g.adicionar_aresta(p, q, 1.0, BALDEACAO)
            visao.transferencias.append(tuple(fronteira[q]))
    return visao
