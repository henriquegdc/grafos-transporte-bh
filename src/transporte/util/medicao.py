"""Medição de tempo de execução (RF-AVA-01).

Toda feature mede o seu algoritmo na rede real com `medir` e registra no próprio arquivo
de feature a média, o desvio, o número de repetições, V, E e a máquina. A F-AVAL junta
esses números na tabela do relatório (RF-AVA-02).

Exemplo:
    >>> from transporte.util.medicao import medir
    >>> m = medir(sorted, [3, 1, 2], repeticoes=5)
    >>> m.repeticoes
    5

estado: implementado
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# Relógio usado pela medição. Fica numa variável do módulo para que os testes possam
# trocá-lo por um relógio falso, de valores conhecidos, sem mexer no módulo `time`.
_relogio: Callable[[], float] = time.perf_counter


@dataclass(frozen=True)
class Medicao:
    """Resultado de `medir`: média e desvio padrão amostral do tempo de N execuções.

    Atributos:
        media_s: tempo médio de uma execução, em segundos.
        desvio_s: desvio padrão amostral (divisor N - 1), em segundos; 0.0 quando N = 1.
        repeticoes: N, o número de execuções cronometradas.

    Espaço O(1).
    """

    media_s: float
    desvio_s: float
    repeticoes: int

    def formatar(self) -> str:
        """Texto curto para tabela ou interface, por exemplo "12.345 ms ± 0.678 ms (n=5)".

        Escolhe a unidade pela média: µs abaixo de 1 ms, ms abaixo de 1 s e s a partir
        daí; o desvio sai na mesma unidade da média.
        Complexidade: tempo O(1), espaço O(1).
        """
        if self.media_s < 1e-3:
            fator, unidade = 1e6, "µs"
        elif self.media_s < 1.0:
            fator, unidade = 1e3, "ms"
        else:
            fator, unidade = 1.0, "s"
        media = self.media_s * fator
        desvio = self.desvio_s * fator
        return f"{media:.3f} {unidade} ± {desvio:.3f} {unidade} (n={self.repeticoes})"


def medir(
    func: Callable[..., Any], *args: Any, repeticoes: int = 5, **kwargs: Any
) -> Medicao:
    """Executa `func(*args, **kwargs)` `repeticoes` vezes e devolve média e desvio do tempo.

    Cada execução é cronometrada isoladamente com `time.perf_counter`, o relógio
    monotônico de maior resolução do Python; só a chamada de `func` fica dentro do
    intervalo medido. O resultado de `func` é descartado: quem precisa dele chama a
    função mais uma vez, fora da medição.

    Entradas:
        func: a função a medir; deve ser determinística quanto ao trabalho feito, para
            que as repetições sejam comparáveis.
        *args, **kwargs: repassados a `func` sem alteração, iguais em todas as execuções.
        repeticoes: N, número de execuções cronometradas; inteiro >= 1. Só por nome,
            para não colidir com os argumentos posicionais de `func`.
    Saída: Medicao com a média e o desvio padrão amostral (divisor N - 1), em segundos.
    Casos de borda:
        repeticoes = 1 dá desvio 0.0 (não há dispersão a estimar com uma amostra);
        repeticoes < 1, ou não inteiro (inclusive bool), levanta ValueError ou TypeError
        antes de executar `func`; exceção levantada por `func` se propaga sem medição
        parcial; `func` que modifica os próprios argumentos recebe os mesmos objetos
        já modificados na repetição seguinte (copie antes, se isso importar).
    Complexidade: tempo O(N · T), em que T é o tempo de uma execução de `func`, mais
        O(N) para a média e o desvio; espaço O(N) para guardar os N tempos.
    """
    if isinstance(repeticoes, bool) or not isinstance(repeticoes, int):
        raise TypeError(f"repeticoes deve ser int, recebeu {type(repeticoes).__name__}")
    if repeticoes < 1:
        raise ValueError(f"repeticoes deve ser >= 1, recebeu {repeticoes}")

    tempos: list[float] = []
    for _ in range(repeticoes):
        inicio = _relogio()
        func(*args, **kwargs)
        fim = _relogio()
        tempos.append(fim - inicio)

    media = sum(tempos) / repeticoes
    if repeticoes == 1:
        desvio = 0.0
    else:
        desvio = math.sqrt(sum((t - media) ** 2 for t in tempos) / (repeticoes - 1))
    return Medicao(media_s=media, desvio_s=desvio, repeticoes=repeticoes)
