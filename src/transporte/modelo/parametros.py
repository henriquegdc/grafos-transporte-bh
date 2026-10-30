"""Parâmetros da modelagem (docs/fontes/modelagem.md §3.4).

estado: planejado
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FaixaHoraria:
    """Intervalo do dia usado para estimar o intervalo entre partidas e a espera.

    Atributos:
        nome: identificador curto da faixa, por exemplo "pico_manha".
        inicio_s: início em segundos desde 00:00, inclusivo.
        fim_s: fim em segundos desde 00:00, exclusivo. Pode passar de 86400,
            porque o GTFS admite horários acima de 24:00:00.

    Espaço O(1).
    """

    nome: str
    inicio_s: int
    fim_s: int

    def contem(self, instante_s: int) -> bool:
        """Diz se o instante (segundos desde 00:00) cai nesta faixa. O(1)."""
        return self.inicio_s <= instante_s < self.fim_s


def _faixas_padrao() -> tuple[FaixaHoraria, ...]:
    # Proposta pendente de decisão (feature-P0-MODELO.md, Pendências); horários fora
    # destas faixas não entram na estimativa de intervalos.
    return (
        FaixaHoraria("pico_manha", 6 * 3600, 9 * 3600),
        FaixaHoraria("entrepico", 9 * 3600, 16 * 3600),
        FaixaHoraria("pico_tarde", 16 * 3600, 19 * 3600),
        FaixaHoraria("noite", 19 * 3600, 24 * 3600),
    )


@dataclass(frozen=True)
class Parametros:
    """Parâmetros que os construtores de visões usam.

    Atributos:
        raio_caminhada_m: distância máxima, em linha reta, de uma aresta de caminhada.
        velocidade_caminhada_ms: velocidade a pé usada no peso da caminhada.
        espera_padrao_s: espera usada nas arestas de embarque enquanto a tabela de
            intervalos de F-ESPERA não existe (proposta pendente de decisão).
        faixas: faixas horárias do dia.

    Valores fixados em 29/10 (docs/GUIA.md §8). Espaço O(número de faixas).
    """

    raio_caminhada_m: float = 300.0
    velocidade_caminhada_ms: float = 1.2
    espera_padrao_s: float = 300.0
    faixas: tuple[FaixaHoraria, ...] = field(default_factory=_faixas_padrao)

    def faixa(self, nome: str) -> FaixaHoraria:
        """Devolve a faixa com esse nome; KeyError se não existir. O(número de faixas)."""
        for f in self.faixas:
            if f.nome == nome:
                return f
        raise KeyError(nome)
