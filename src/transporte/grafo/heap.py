"""Fila de prioridade própria: heap binário de mínimo (RF-GRF-08).

Usada por todos os Dijkstras do projeto no lugar de `heapq`, que não pode ser usado.
Não há operação de diminuir chave: os algoritmos usam inserção preguiçosa (inserem de novo
com a prioridade menor e descartam, na extração, a entrada desatualizada).

estado: planejado
"""

from __future__ import annotations


class HeapMin:
    """Heap binário de mínimo sobre uma lista de pares (prioridade, item).

    A raiz fica na posição 0; os filhos da posição i ficam em 2i + 1 e 2i + 2.
    Empates de prioridade são desfeitos pelo menor item, o que torna a ordem de extração
    determinística (os testes dependem disso).

    Espaço O(n), n = número de entradas no heap.
    """

    def __init__(self) -> None:
        """Cria um heap vazio. Complexidade: O(1)."""
        raise NotImplementedError("estado: planejado")

    def inserir(self, prioridade: float, item: int) -> None:
        """Insere o par (prioridade, item); o mesmo item pode entrar mais de uma vez.

        Complexidade: tempo O(log n) (sobe no máximo a altura da árvore); espaço O(1)
        amortizado.
        """
        raise NotImplementedError("estado: planejado")

    def extrair_min(self) -> tuple[float, int]:
        """Remove e devolve o par de menor prioridade (empate: menor item).

        Casos de borda: heap vazio levanta IndexError.
        Complexidade: tempo O(log n) (desce no máximo a altura da árvore); espaço O(1).
        """
        raise NotImplementedError("estado: planejado")

    def vazio(self) -> bool:
        """True se não há entradas. Complexidade: O(1)."""
        raise NotImplementedError("estado: planejado")

    def __len__(self) -> int:
        """Número de entradas, contando repetições do mesmo item. Complexidade: O(1)."""
        raise NotImplementedError("estado: planejado")
