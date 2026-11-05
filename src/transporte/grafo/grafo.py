"""Estrutura própria de grafo dirigido e ponderado (RF-GRF-01, RF-GRF-03).

Vértices e arestas são numerados a partir de 0, na ordem em que são adicionados, e os
seus atributos ficam em listas paralelas (docs/fontes/modelagem.md, "Representação no
núcleo"). Nada é removido: desativar só marca o vértice ou a aresta, e os ids continuam
valendo, o que permite a F-RES simular falhas e desfazê-las sem reconstruir o grafo.

Notação: V = número de vértices, E = número de arestas, grau(u) = arestas que saem de u.

estado: implementado
"""

from __future__ import annotations

import math


class Grafo:
    """Grafo dirigido e ponderado. Vértices 0..V-1, lista de adjacência. Espaço O(V + E).

    Arestas paralelas e laços são permitidos (cada uma tem o seu id). Pesos são números
    finitos e não negativos, porque no projeto todo peso é tempo em segundos e o Dijkstra
    exige pesos não negativos.

    Representação interna (listas paralelas, indexadas pelo id):
        _rotulo[u], _vertice_ativo[u]: atributos do vértice u.
        _adj[u]: ids das arestas que saem de u, na ordem de inserção.
        _origem[a], _destino[a], _peso[a], _tipo[a], _aresta_ativa[a]: atributos da
            aresta a.
    Guardar ids de aresta na adjacência, e não pares (destino, peso), deixa o peso e o
    estado de cada aresta num lugar só e permite arestas paralelas com ids distintos.
    """

    __slots__ = (
        "_adj",
        "_aresta_ativa",
        "_destino",
        "_origem",
        "_peso",
        "_rotulo",
        "_tipo",
        "_vertice_ativo",
    )

    def __init__(self) -> None:
        """Cria um grafo vazio. Complexidade: O(1)."""
        self._rotulo: list[str] = []
        self._vertice_ativo: list[bool] = []
        self._adj: list[list[int]] = []
        self._origem: list[int] = []
        self._destino: list[int] = []
        self._peso: list[float] = []
        self._tipo: list[str] = []
        self._aresta_ativa: list[bool] = []

    # --- validação ----------------------------------------------------------------------

    def _checar_vertice(self, u: int) -> None:
        # Sem esta checagem, um id negativo indexaria a lista de trás para frente.
        if not 0 <= u < len(self._rotulo):
            raise IndexError(f"vértice inexistente: {u}")

    def _checar_aresta(self, a: int) -> None:
        if not 0 <= a < len(self._origem):
            raise IndexError(f"aresta inexistente: {a}")

    # --- construção ---------------------------------------------------------------------

    def adicionar_vertice(self, rotulo: str) -> int:
        """Adiciona um vértice ativo e devolve o seu id (o próximo inteiro livre).

        Entrada: rótulo livre, usado só para exibição (ex.: id da parada no GTFS).
        Complexidade: tempo O(1) amortizado; espaço O(1).
        """
        self._rotulo.append(rotulo)
        self._vertice_ativo.append(True)
        self._adj.append([])
        return len(self._rotulo) - 1

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
        self._checar_vertice(u)
        self._checar_vertice(v)
        peso = float(peso)
        # isfinite é falso para inf e NaN; NaN também falharia em qualquer comparação.
        if not math.isfinite(peso) or peso < 0:
            raise ValueError(f"peso deve ser finito e >= 0, recebido {peso}")
        a = len(self._origem)
        self._origem.append(u)
        self._destino.append(v)
        self._peso.append(peso)
        self._tipo.append(tipo)
        self._aresta_ativa.append(True)
        self._adj[u].append(a)
        return a

    # --- consulta -----------------------------------------------------------------------

    def num_vertices(self) -> int:
        """Total de vértices, ativos ou não (os ids vão de 0 a este valor - 1). O(1)."""
        return len(self._rotulo)

    def num_arestas(self) -> int:
        """Total de arestas, ativas ou não (os ids vão de 0 a este valor - 1). O(1)."""
        return len(self._origem)

    def rotulo(self, u: int) -> str:
        """Rótulo do vértice u. Vértice inexistente levanta IndexError. O(1)."""
        self._checar_vertice(u)
        return self._rotulo[u]

    def aresta(self, a: int) -> tuple[int, int, float, str]:
        """Dados da aresta a: (origem, destino, peso, tipo), esteja ela ativa ou não.

        Usada, por exemplo, para contar embarques num caminho de G_E.
        Casos de borda: aresta inexistente levanta IndexError.
        Complexidade: O(1).
        """
        self._checar_aresta(a)
        return self._origem[a], self._destino[a], self._peso[a], self._tipo[a]

    def vizinhos(self, u: int) -> list[tuple[int, float, int]]:
        """Arestas utilizáveis que saem de u, como (destino, peso, id da aresta).

        Uma aresta é utilizável se ela, a origem e o destino estão ativos. Vértice
        desativado não tem vizinhos. A ordem é a de inserção das arestas.
        Casos de borda: vértice inexistente levanta IndexError.
        Complexidade: tempo O(grau(u)); espaço O(grau(u)) para a lista devolvida.
        """
        self._checar_vertice(u)
        if not self._vertice_ativo[u]:
            return []
        destino = self._destino
        peso = self._peso
        aresta_ativa = self._aresta_ativa
        vertice_ativo = self._vertice_ativo
        return [
            (destino[a], peso[a], a)
            for a in self._adj[u]
            if aresta_ativa[a] and vertice_ativo[destino[a]]
        ]

    def vertice_ativo(self, u: int) -> bool:
        """True se o vértice u está ativo. O(1)."""
        self._checar_vertice(u)
        return self._vertice_ativo[u]

    def aresta_ativa(self, a: int) -> bool:
        """True se a aresta a está ativa (independe do estado das pontas). O(1)."""
        self._checar_aresta(a)
        return self._aresta_ativa[a]

    # --- falhas (RF-GRF-03) -------------------------------------------------------------

    def desativar_vertice(self, u: int) -> None:
        """Marca u como inativo: some das buscas, junto com as arestas que tocam nele.

        As arestas não são alteradas; voltam a valer quando u for reativado.
        Desativar o que já está inativo não faz nada. Complexidade: O(1).
        """
        self._checar_vertice(u)
        self._vertice_ativo[u] = False

    def desativar_aresta(self, a: int) -> None:
        """Marca a aresta a como inativa. Idempotente. Complexidade: O(1)."""
        self._checar_aresta(a)
        self._aresta_ativa[a] = False

    def reativar_vertice(self, u: int) -> None:
        """Desfaz desativar_vertice(u). Idempotente. Complexidade: O(1)."""
        self._checar_vertice(u)
        self._vertice_ativo[u] = True

    def reativar_aresta(self, a: int) -> None:
        """Desfaz desativar_aresta(a). Idempotente. Complexidade: O(1)."""
        self._checar_aresta(a)
        self._aresta_ativa[a] = True

    def reativar_tudo(self) -> None:
        """Reativa todos os vértices e arestas. Complexidade: O(V + E)."""
        self._vertice_ativo = [True] * len(self._rotulo)
        self._aresta_ativa = [True] * len(self._origem)

    # --- derivados ----------------------------------------------------------------------

    def reverso(self) -> Grafo:
        """Novo grafo com todas as arestas invertidas.

        Mantém os ids de vértices e de arestas (a aresta a: u -> v vira a: v -> u, com o
        mesmo peso e tipo), os rótulos e o estado ativo/inativo de cada um. Serve para
        buscas "até um destino", como Dijkstra a partir do destino. O novo grafo é
        independente: desativar algo nele não afeta o original.
        Complexidade: tempo e espaço O(V + E).
        """
        r = Grafo()
        r._rotulo = list(self._rotulo)
        r._vertice_ativo = list(self._vertice_ativo)
        r._origem = list(self._destino)
        r._destino = list(self._origem)
        r._peso = list(self._peso)
        r._tipo = list(self._tipo)
        r._aresta_ativa = list(self._aresta_ativa)
        r._adj = [[] for _ in self._rotulo]
        # Percorre as arestas em ordem de id, então cada lista de adjacência do reverso
        # também fica em ordem de inserção.
        for a, nova_origem in enumerate(r._origem):
            r._adj[nova_origem].append(a)
        return r

    def __repr__(self) -> str:
        return f"Grafo(V={self.num_vertices()}, E={self.num_arestas()})"
