"""Fila de prioridade própria: heap binário de mínimo (RF-GRF-08).

Usada por todos os Dijkstras do projeto no lugar do heap da biblioteca padrão, que o
trabalho proíbe (fila de prioridade tem de ser própria).
Não há operação de diminuir chave: os algoritmos usam inserção preguiçosa (inserem de novo
com a prioridade menor e descartam, na extração, a entrada desatualizada).

estado: implementado
"""

from __future__ import annotations


class HeapMin:
    """Heap binário de mínimo sobre uma lista de pares (prioridade, item).

    A raiz fica na posição 0; os filhos da posição i ficam em 2i + 1 e 2i + 2, e o pai em
    (i - 1) // 2. Invariante: nenhum par é menor que o do seu pai, logo a raiz é o mínimo.
    Empates de prioridade são desfeitos pelo menor item, o que torna a ordem de extração
    determinística (os testes dependem disso). Os pares são comparados como tuplas, o que
    já faz exatamente isso.

    Espaço O(n), n = número de entradas no heap.
    """

    __slots__ = ("_dados",)

    def __init__(self) -> None:
        """Cria um heap vazio. Complexidade: O(1)."""
        self._dados: list[tuple[float, int]] = []

    def inserir(self, prioridade: float, item: int) -> None:
        """Insere o par (prioridade, item); o mesmo item pode entrar mais de uma vez.

        Coloca o par no fim da lista (a próxima folha livre) e o sobe enquanto for menor
        que o pai.
        Complexidade: tempo O(log n) (sobe no máximo a altura da árvore); espaço O(1)
        amortizado.
        """
        dados = self._dados
        novo = (prioridade, item)
        dados.append(novo)
        i = len(dados) - 1
        # Em vez de trocar a cada nível, desce os pais maiores e grava o novo uma vez só.
        while i > 0:
            pai = (i - 1) >> 1
            if novo < dados[pai]:
                dados[i] = dados[pai]
                i = pai
            else:
                break
        dados[i] = novo

    def extrair_min(self) -> tuple[float, int]:
        """Remove e devolve o par de menor prioridade (empate: menor item).

        Guarda a raiz, move a última folha para a raiz e a desce, trocando-a com o menor
        dos filhos, até que nenhum filho seja menor que ela.
        Casos de borda: heap vazio levanta IndexError.
        Complexidade: tempo O(log n) (desce no máximo a altura da árvore); espaço O(1).
        """
        dados = self._dados
        if not dados:
            raise IndexError("extrair_min de heap vazio")
        ultimo = dados.pop()
        if not dados:
            return ultimo
        minimo = dados[0]
        n = len(dados)
        i = 0
        while True:
            filho = 2 * i + 1
            if filho >= n:
                break
            direito = filho + 1
            if direito < n and dados[direito] < dados[filho]:
                filho = direito
            if dados[filho] < ultimo:
                dados[i] = dados[filho]
                i = filho
            else:
                break
        dados[i] = ultimo
        return minimo

    def vazio(self) -> bool:
        """True se não há entradas. Complexidade: O(1)."""
        return not self._dados

    def __len__(self) -> int:
        """Número de entradas, contando repetições do mesmo item. Complexidade: O(1)."""
        return len(self._dados)
