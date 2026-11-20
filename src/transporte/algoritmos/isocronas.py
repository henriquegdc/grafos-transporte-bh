"""Paradas acessíveis em um orçamento de tempo no G_E (RF-EFI-03)."""

from math import inf, isfinite

from transporte.grafo.heap import HeapMin
from transporte.modelo.visoes import VisaoGE


def isocrona(ge: VisaoGE, origem: str, limite_s: float) -> dict[str, float]:
    """Devolve o tempo mínimo em segundos para cada parada alcançada até limite_s.

    O Dijkstra inclui plataformas nos caminhos e só publica paradas. A própria
    origem ativa entra com zero. Origem inexistente gera KeyError, desativada
    devolve {}, limite negativo ou não finito gera ValueError. Com V' vértices
    visitados e E' arestas examinadas, tempo O((V'+E') log(E'+2)) e espaço
    O(V'+E') pelas entradas preguiçosas no heap. Não percorre a rede inteira.
    """
    if not isfinite(limite_s) or limite_s < 0:
        raise ValueError("O limite de tempo deve ser finito e não negativo.")
    origem_v = ge.vertice_da_parada[origem]
    g = ge.grafo
    if not g.vertice_ativo(origem_v):
        return {}
    dist = {origem_v: 0.0}
    alcancadas = {}
    fila = HeapMin()
    fila.inserir(0.0, origem_v)
    while not fila.vazio():
        tempo, u = fila.extrair_min()
        if tempo != dist[u]:
            continue
        rotulo = g.rotulo(u)
        if ge.vertice_da_parada.get(rotulo) == u:
            alcancadas[rotulo] = tempo
        for v, peso, _ in g.vizinhos(u):
            novo = tempo + peso
            if novo <= limite_s and novo < dist.get(v, inf):
                dist[v] = novo
                fila.inserir(novo, v)
    return alcancadas
