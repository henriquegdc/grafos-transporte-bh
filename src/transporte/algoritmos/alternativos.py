"""k trajetos alternativos em G_E pelo algoritmo de Yen (F-ROTA-OPC, RF-ROT-05).

Yen lista os k caminhos sem ciclo de menor custo, em ordem crescente de custo. O primeiro
é o trajeto mais rápido. Para achar o i-ésimo, cada vértice do (i-1)-ésimo caminho vira, um
por vez, ponto de desvio: o trecho até ele (a raiz) é mantido, as arestas que os caminhos já
aceitos usam logo depois dessa mesma raiz são desativadas, os vértices da raiz (menos o
desvio) também, e uma busca do desvio ao destino completa o candidato. O melhor candidato
ainda não aceito vira o i-ésimo caminho.

Desativar e reativar usam a API de falhas do núcleo (RF-GRF-03). Só é reativado o que esta
função desativou, então falhas simuladas antes (F-RES) continuam valendo e o grafo volta
ao estado em que estava. As buscas de desvio usam o A* da F-ROTA-2 quando há coordenadas:
remover arestas não aumenta a velocidade de nenhuma aresta restante, então a heurística
continua consistente e o custo do desvio continua o ótimo.

Caminhos distintos são distintos em arestas de G_E: dois trajetos podem passar pelas mesmas
paradas e diferir na linha usada num trecho, ou num trecho a pé.

estado: implementado
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from transporte.algoritmos.a_estrela import _buscar, _trajeto
from transporte.grafo.buscas import INF
from transporte.grafo.heap import HeapMin

if TYPE_CHECKING:
    from collections.abc import Sequence

    from transporte.algoritmos.trajeto import Trajeto
    from transporte.modelo.visoes import VisaoGE


def _vertices(ge: VisaoGE, s: int, arestas: Sequence[int]) -> list[int]:
    """Vértices de um caminho a partir das arestas, com a origem. O(k)."""
    g = ge.grafo
    return [s, *(g.aresta(a)[1] for a in arestas)]


def trajetos_alternativos(
    ge: VisaoGE,
    origem: str,
    destino: str,
    k: int,
    coords: Sequence[tuple[float, float]] | None = None,
    vmax: float = INF,
) -> list[Trajeto]:
    """Até k trajetos sem ciclo de origem a destino, do mais rápido ao mais lento.

    Entradas:
        ge: G_E de uma faixa horária.
        origem, destino: ids de paradas do GTFS.
        k: número de trajetos pedidos (>= 1).
        coords, vmax: os de `a_estrela.coordenadas_ge` e `a_estrela.velocidade_maxima`;
            com eles os desvios usam A*, sem eles, Dijkstra. O resultado é o mesmo.
    Saída: lista com até k Trajetos, em ordem crescente de tempo total; menos que k se não
        houver mais caminhos sem ciclo; vazia se o destino é inalcançável. Empates de custo
        saem na ordem em que foram encontrados.
    Casos de borda: k < 1 levanta ValueError; parada inexistente levanta KeyError;
        origem == destino devolve só o trajeto vazio; o estado ativo de vértices e arestas
        é restaurado mesmo se a busca levantar exceção.
    Complexidade: tempo O(k · n · (V + E) log V), n = vértices do maior caminho aceito (uma
        busca por ponto de desvio); espaço O(V + E + k · n + C · n), C candidatos guardados.
    """
    if k < 1:
        raise ValueError(f"k deve ser >= 1, recebeu {k}")
    g = ge.grafo
    s = ge.vertice_da_parada[origem]
    t = ge.vertice_da_parada[destino]

    custo, arestas, _ = _buscar(ge, s, t, coords, vmax)
    if custo == INF:
        return []
    aceitos: list[tuple[float, list[int]]] = [(custo, arestas)]
    vistos = {tuple(arestas)}
    candidatos: list[tuple[float, list[int]]] = []
    fila = HeapMin()  # (custo, índice em candidatos)

    while len(aceitos) < k:
        anterior = aceitos[-1][1]
        vertices = _vertices(ge, s, anterior)
        custo_raiz = 0.0
        for i in range(len(anterior)):
            desvio = vertices[i]
            raiz = anterior[:i]
            desativadas: list[int] = []
            desativados: list[int] = []
            try:
                for _c, caminho in aceitos:
                    if len(caminho) > i and caminho[:i] == raiz:
                        a = caminho[i]
                        if g.aresta_ativa(a):
                            g.desativar_aresta(a)
                            desativadas.append(a)
                for v in vertices[:i]:
                    if g.vertice_ativo(v):
                        g.desativar_vertice(v)
                        desativados.append(v)
                custo_desvio, resto, _ = _buscar(ge, desvio, t, coords, vmax)
            finally:
                for a in desativadas:
                    g.reativar_aresta(a)
                for v in desativados:
                    g.reativar_vertice(v)
            if custo_desvio != INF:
                completo = raiz + resto
                chave = tuple(completo)
                if chave not in vistos:
                    vistos.add(chave)
                    candidatos.append((custo_raiz + custo_desvio, completo))
                    fila.inserir(custo_raiz + custo_desvio, len(candidatos) - 1)
            custo_raiz += g.aresta(anterior[i])[2]
        if fila.vazio():
            break
        _c, indice = fila.extrair_min()
        aceitos.append(candidatos[indice])

    return [_trajeto(ge, origem, destino, c, caminho) for c, caminho in aceitos]
