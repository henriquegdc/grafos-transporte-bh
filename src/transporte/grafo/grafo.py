"""Estrutura própria de grafo dirigido e ponderado (RF-GRF-01, RF-GRF-03).

Vértices e arestas são numerados a partir de 0, na ordem em que são adicionados, e os
seus atributos ficam em listas paralelas (docs/fontes/modelagem.md, "Representação no
núcleo"). Nada é removido: desativar só marca o vértice ou a aresta, e os ids continuam
valendo, o que permite a F-RES simular falhas e desfazê-las sem reconstruir o grafo.

Notação: V = número de vértices, E = número de arestas, grau(u) = arestas que saem de u.

estado: planejado
"""

from __future__ import annotations


class Grafo:
    """Grafo dirigido e ponderado. Vértices 0..V-1, lista de adjacência. Espaço O(V + E).

    Arestas paralelas e laços são permitidos (cada uma tem o seu id). Pesos são números
    finitos e não negativos, porque no projeto todo peso é tempo em segundos e o Dijkstra
    exige pesos não negativos.
    """

    def __init__(self) -> None:
        """Cria um grafo vazio. Complexidade: O(1)."""
        raise NotImplementedError("estado: planejado")

    # --- construção ---------------------------------------------------------------------

    def adicionar_vertice(self, rotulo: str) -> int:
        """Adiciona um vértice ativo e devolve o seu id (o próximo inteiro livre).

        Entrada: rótulo livre, usado só para exibição (ex.: id da parada no GTFS).
        Complexidade: tempo O(1) amortizado; espaço O(1).
        """
        raise NotImplementedError("estado: planejado")

    def adicionar_aresta(self, u: int, v: int, peso: float, tipo: str = "") -> int:
        """Adiciona a aresta ativa u -> v e devolve o seu id (o próximo inteiro livre).

        Entradas:
            u, v: ids de vértices existentes.
            peso: número finito >= 0.
            tipo: rótulo livre da aresta (as visões usam "viagem", "caminhada", ...).
        Casos de borda: vértice inexistente levanta IndexError; peso negativo, infinito ou
            NaN levanta ValueError.
        Complexidade: tempo O(1) amortizado; espaço O(1).
        """
        raise NotImplementedError("estado: planejado")

    # --- consulta -----------------------------------------------------------------------

    def num_vertices(self) -> int:
        """Total de vértices, ativos ou não (os ids vão de 0 a este valor - 1). O(1)."""
        raise NotImplementedError("estado: planejado")

    def num_arestas(self) -> int:
        """Total de arestas, ativas ou não (os ids vão de 0 a este valor - 1). O(1)."""
        raise NotImplementedError("estado: planejado")

    def rotulo(self, u: int) -> str:
        """Rótulo do vértice u. Vértice inexistente levanta IndexError. O(1)."""
        raise NotImplementedError("estado: planejado")

    def aresta(self, a: int) -> tuple[int, int, float, str]:
        """Dados da aresta a: (origem, destino, peso, tipo), esteja ela ativa ou não.

        Usada, por exemplo, para contar embarques num caminho de G_E.
        Casos de borda: aresta inexistente levanta IndexError.
        Complexidade: O(1).
        """
        raise NotImplementedError("estado: planejado")

    def vizinhos(self, u: int) -> list[tuple[int, float, int]]:
        """Arestas utilizáveis que saem de u, como (destino, peso, id da aresta).

        Uma aresta é utilizável se ela, a origem e o destino estão ativos. Vértice
        desativado não tem vizinhos. A ordem é a de inserção das arestas.
        Casos de borda: vértice inexistente levanta IndexError.
        Complexidade: tempo O(grau(u)); espaço O(grau(u)) para a lista devolvida.
        """
        raise NotImplementedError("estado: planejado")

    def vertice_ativo(self, u: int) -> bool:
        """True se o vértice u está ativo. O(1)."""
        raise NotImplementedError("estado: planejado")

    def aresta_ativa(self, a: int) -> bool:
        """True se a aresta a está ativa (independe do estado das pontas). O(1)."""
        raise NotImplementedError("estado: planejado")

    # --- falhas (RF-GRF-03) -------------------------------------------------------------

    def desativar_vertice(self, u: int) -> None:
        """Marca u como inativo: some das buscas, junto com as arestas que tocam nele.

        As arestas não são alteradas; voltam a valer quando u for reativado.
        Desativar o que já está inativo não faz nada. Complexidade: O(1).
        """
        raise NotImplementedError("estado: planejado")

    def desativar_aresta(self, a: int) -> None:
        """Marca a aresta a como inativa. Idempotente. Complexidade: O(1)."""
        raise NotImplementedError("estado: planejado")

    def reativar_vertice(self, u: int) -> None:
        """Desfaz desativar_vertice(u). Idempotente. Complexidade: O(1)."""
        raise NotImplementedError("estado: planejado")

    def reativar_aresta(self, a: int) -> None:
        """Desfaz desativar_aresta(a). Idempotente. Complexidade: O(1)."""
        raise NotImplementedError("estado: planejado")

    def reativar_tudo(self) -> None:
        """Reativa todos os vértices e arestas. Complexidade: O(V + E)."""
        raise NotImplementedError("estado: planejado")

    # --- derivados ----------------------------------------------------------------------

    def reverso(self) -> Grafo:
        """Novo grafo com todas as arestas invertidas.

        Mantém os ids de vértices e de arestas (a aresta a: u -> v vira a: v -> u, com o
        mesmo peso e tipo), os rótulos e o estado ativo/inativo de cada um. Serve para
        buscas "até um destino", como Dijkstra a partir do destino.
        Complexidade: tempo e espaço O(V + E).
        """
        raise NotImplementedError("estado: planejado")
