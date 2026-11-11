"""Trajeto com o menor número de baldeações entre duas paradas, sobre G_L (F-BALD).

RF-BAL-01: menor número de baldeações. RF-BAL-02: a sequência de linhas e as paradas de
troca, que a página Baldeações desenha no mapa.

**Por que não basta um BFS comum em G_L.** Os padrões têm sentido. Se o passageiro embarca
em P na 10ª parada, só pode descer de P da 11ª em diante; uma troca de P para Q na 3ª
parada de P existe em G_L, mas não serve a ele. Um BFS que só olha os vértices daria um
número de baldeações menor que o real (um limite inferior) e um trajeto impossível de fazer.

**BFS por camadas com índice de embarque.** A camada k guarda, para cada padrão alcançado
com k ônibus, a posição mais cedo em que dá para estar embarcado nele (o rótulo). A camada 1
sai das paradas a até o raio da origem; a camada k + 1 sai das arestas de G_L dos padrões
cujo rótulo melhorou na camada k, usando só as trocas que descem depois do embarque. Um
padrão pode voltar numa camada posterior se for alcançado numa posição mais cedo, porque
isso abre trocas que antes não serviam. A primeira camada em que algum padrão chega ao
destino (ou a uma parada a até o raio dele) dá o mínimo de ônibus; baldeações = ônibus - 1.
Sem a restrição de ordem, isto é exatamente o BFS do núcleo sobre G_L.

Notação: V e E de G_L (padrões e pares de padrões com troca), T trocas guardadas nas
arestas, r camadas percorridas (baldeações + 1, ou + 2 se o destino é inalcançável), s
paradas a até o raio da origem ou do destino.

estado: implementado
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

from transporte.algoritmos.trajeto import A_PE, ONIBUS
from transporte.modelo.visoes import VisaoGL


@dataclass(frozen=True)
class TrechoBaldeacao:
    """Parte do trajeto com um só modo.

    Atributos:
        tipo: A_PE ou ONIBUS (as mesmas constantes de algoritmos.trajeto).
        paradas: ids das paradas percorridas, da primeira à última (pelo menos duas).
        padrao: id do padrão no ônibus; None a pé.
    Espaço O(número de paradas do trecho).
    """

    tipo: str
    paradas: tuple[str, ...]
    padrao: str | None = None


@dataclass(frozen=True)
class TrajetoBaldeacoes:
    """Resultado de menos_baldeacoes.

    Atributos:
        origem, destino: ids das paradas.
        baldeacoes: ônibus usados - 1, ou 0 se não usa ônibus.
        trechos: na ordem do percurso. Ônibus seguidos são separados pela troca, a pé se as
            paradas de descida e de embarque forem diferentes. Vazio se origem == destino.
    """

    origem: str
    destino: str
    baldeacoes: int
    trechos: tuple[TrechoBaldeacao, ...]

    def padroes(self) -> list[str]:
        """Ids dos padrões usados, na ordem (a sequência de linhas). O(número de trechos)."""
        return [t.padrao for t in self.trechos if t.tipo == ONIBUS and t.padrao is not None]

    def trocas(self) -> list[tuple[str, str]]:
        """Paradas de troca, como (parada onde desce, parada onde embarca no próximo).

        As duas são iguais quando a troca é na mesma parada. Uma por baldeação.
        O(número de trechos).
        """
        onibus = [t for t in self.trechos if t.tipo == ONIBUS]
        return [(a.paradas[-1], b.paradas[0]) for a, b in pairwise(onibus)]


@dataclass(frozen=True)
class _Rotulo:
    """Estado de um padrão numa camada: embarcado na posição `embarque`, na parada que
    está nessa posição. `de` é None no primeiro ônibus (veio a pé da origem) ou
    (padrão anterior, índice do rótulo dele, posição onde desceu dele)."""

    camada: int
    embarque: int
    de: tuple[int, int, int] | None


def _trechos(
    gl: VisaoGL,
    origem: str,
    destino: str,
    pernas: list[tuple[int, int, int]],
) -> tuple[TrechoBaldeacao, ...]:
    """Pernas (padrão, posição de embarque, posição de descida) em trechos, com a pé entre
    elas quando as paradas diferem. O(paradas percorridas)."""
    trechos: list[TrechoBaldeacao] = []
    onde = origem
    for p, b, i in pernas:
        seq = gl.paradas_do_padrao[p]
        if seq[b] != onde:
            trechos.append(TrechoBaldeacao(A_PE, (onde, seq[b])))
        trechos.append(TrechoBaldeacao(ONIBUS, seq[b : i + 1], gl.padrao_do_vertice[p]))
        onde = seq[i]
    if onde != destino:
        trechos.append(TrechoBaldeacao(A_PE, (onde, destino)))
    return tuple(trechos)


def _primeiro_embarque_mais_perto(
    gl: VisaoGL, origem: str, perna: tuple[int, int, int]
) -> tuple[int, int, int]:
    """Troca o embarque da primeira perna pelo de menor caminhada desde a origem.

    A camada 1 guarda a posição de embarque mais cedo, que é o que importa para as trocas,
    mas pode estar mais longe da origem. Qualquer embarque no mesmo padrão antes da
    descida i serve ao resto do trajeto; entre eles, fica o de menor caminhada e, no
    empate, o mais tarde (menos paradas de ônibus). O(s), s = paradas a até o raio.
    """
    p, _b, i = perna
    melhor = None
    for y, d in gl.proximas[origem]:
        for q, j in gl.embarques.get(y, ()):
            if q == p and j < i and (melhor is None or (d, -j) < melhor):
                melhor = (d, -j)
    return (p, -melhor[1], i) if melhor is not None else perna


def menos_baldeacoes(gl: VisaoGL, origem: str, destino: str) -> TrajetoBaldeacoes | None:
    """Trajeto com o menor número de baldeações de origem a destino (RF-BAL-01).

    Caminhada: só entre paradas a até o raio de G_L e uma de cada vez (da origem até o
    primeiro embarque, entre a descida e o próximo embarque, e da última descida até o
    destino). Se o destino está a até o raio da origem, o trajeto é a pé, com 0 baldeações.

    Entradas:
        gl: G_L (construir_gl), de uma faixa ou do dia inteiro.
        origem, destino: ids de paradas do GTFS.
    Saída: TrajetoBaldeacoes com as baldeações e os trechos; None se o destino não é
        alcançável. Entre trajetos com o mesmo número de baldeações, prefere o que anda
        menos no fim e, depois, o de última perna mais curta; no primeiro ônibus, embarca
        no ponto mais perto da origem que ainda serve à primeira troca. Não minimiza o
        tempo (comparar com o mais rápido é a F-BALD-2).
    Casos de borda: origem == destino devolve 0 baldeações e nenhum trecho; parada
        inexistente levanta KeyError; padrões (vértices) e trocas (arestas) desativados
        são respeitados (F-RES); padrão circular só anda para a frente a partir da posição
        de embarque.
    Complexidade: tempo O(r (V + E + T) + s) no pior caso, porque cada camada só visita os
        padrões que melhoraram na anterior e as trocas das arestas deles, e para no
        primeiro desembarque já usado; espaço O(r V) para os rótulos de cada camada.
    """
    if origem not in gl.proximas:
        raise KeyError(origem)
    if destino not in gl.proximas:
        raise KeyError(destino)
    if origem == destino:
        return TrajetoBaldeacoes(origem, destino, 0, ())
    perto_destino = dict(gl.proximas[destino])
    if origem in perto_destino:
        return TrajetoBaldeacoes(origem, destino, 0, (TrechoBaldeacao(A_PE, (origem, destino)),))

    g = gl.grafo
    historico: list[list[_Rotulo]] = [[] for _ in range(g.num_vertices())]
    melhor: list[float] = [float("inf")] * g.num_vertices()

    # Camada 1: padrões que embarcam a até o raio da origem, na posição mais cedo.
    marcados: dict[int, _Rotulo] = {}
    for y, _d in gl.proximas[origem]:
        for p, j in gl.embarques.get(y, ()):
            if g.vertice_ativo(p) and (p not in marcados or j < marcados[p].embarque):
                marcados[p] = _Rotulo(1, j, None)

    camada = 1
    while marcados:
        for p, rotulo in marcados.items():
            historico[p].append(rotulo)
            melhor[p] = rotulo.embarque

        # Chegada: algum padrão que melhorou nesta camada desce a até o raio do destino.
        chegada = None  # (caminhada final, paradas na última perna, id do padrão, p, i)
        for p, rotulo in marcados.items():
            seq = gl.paradas_do_padrao[p]
            for i in range(rotulo.embarque + 1, len(seq)):
                d = perto_destino.get(seq[i])
                if d is not None:
                    chave = (d, i - rotulo.embarque, gl.padrao_do_vertice[p], p, i)
                    if chegada is None or chave < chegada:
                        chegada = chave
        if chegada is not None:
            *_, p, i = chegada
            pernas = []
            idx = len(historico[p]) - 1
            while True:
                rotulo = historico[p][idx]
                pernas.append((p, rotulo.embarque, i))
                if rotulo.de is None:
                    break
                p, idx, i = rotulo.de
            pernas.reverse()
            pernas[0] = _primeiro_embarque_mais_perto(gl, origem, pernas[0])
            return TrajetoBaldeacoes(
                origem, destino, camada - 1, _trechos(gl, origem, destino, pernas)
            )

        # Próxima camada: trocas que descem depois da posição de embarque.
        novos: dict[int, _Rotulo] = {}
        for p in sorted(marcados):
            b = melhor[p]
            idx = len(historico[p]) - 1
            for q, _peso, a in g.vizinhos(p):
                troca = None
                # Em ordem decrescente de i e de j: a última com i > b embarca mais cedo.
                for t in gl.transferencias[a]:
                    if t[0] <= b:
                        break
                    troca = t
                if troca is None:
                    continue
                i, _x, j, _y = troca
                if j < melhor[q] and (q not in novos or j < novos[q].embarque):
                    novos[q] = _Rotulo(camada + 1, j, (p, idx, i))
        marcados = novos
        camada += 1
    return None
