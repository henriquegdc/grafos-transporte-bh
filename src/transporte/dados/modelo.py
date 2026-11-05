"""Modelo normalizado do GTFS. estado: implementado.

N é o total de horários e partidas expandidas, P o de padrões e V o de paradas.
A Rede usa O(N + P + V) de espaço.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Parada:
    id: str
    nome: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Linha:
    id: str
    nome: str
    tipo: int


@dataclass(frozen=True)
class Padrao:
    id: str
    linha_id: str
    paradas: tuple[str, ...]


@dataclass(frozen=True)
class Viagem:
    id: str
    padrao_id: str
    servico_id: str
    horarios: tuple[int, ...]


@dataclass(frozen=True)
class Frequencia:
    viagem_id: str
    inicio_s: int
    fim_s: int
    intervalo_s: int


@dataclass
class Rede:
    paradas: dict[str, Parada]
    linhas: dict[str, Linha]
    padroes: dict[str, Padrao]
    partidas: dict[tuple[str, str], list[int]]
    viagens: dict[str, list[tuple[int, ...]]] = field(default_factory=dict)
    viagens_por_id: dict[str, Viagem] = field(default_factory=dict)
    frequencias: tuple[Frequencia, ...] = ()
    dia: str = ""
    inconsistencias: list[str] = field(default_factory=list)

    def recortar(
        self,
        caixa: tuple[float, float, float, float] | None = None,
        linhas: set[str] | None = None,
    ) -> Rede:
        """Recorta por (lat mínima, lon mínima, lat máxima, lon máxima) e/ou ids de linha.

        Trechos separados pelo corte recebem padrões distintos para não inventar uma
        viagem direta entre paradas que não eram consecutivas no GTFS.
        Complexidade: tempo O(N log N + P + V); espaço O(N + P + V).
        """
        if caixa is not None:
            sul, oeste, norte, leste = caixa
            if sul > norte or oeste > leste:
                raise ValueError("caixa inválida: mínimos devem preceder máximos")
        linhas_novas = {
            ident: linha
            for ident, linha in self.linhas.items()
            if linhas is None or ident in linhas
        }
        paradas_atendidas = (
            {
                parada_id
                for padrao in self.padroes.values()
                if padrao.linha_id in linhas_novas
                for parada_id in padrao.paradas
            }
            if linhas is not None else None
        )
        paradas = {
            ident: parada
            for ident, parada in self.paradas.items()
            if (paradas_atendidas is None or ident in paradas_atendidas)
            and (
                caixa is None
                or (caixa[0] <= parada.lat <= caixa[2] and caixa[1] <= parada.lon <= caixa[3])
            )
        }
        padroes: dict[str, Padrao] = {}
        viagens: dict[str, Viagem] = {}
        frequencias: list[Frequencia] = []
        freq_por_viagem: dict[str, list[Frequencia]] = {}
        for freq in self.frequencias:
            freq_por_viagem.setdefault(freq.viagem_id, []).append(freq)
        viagens_por_padrao: dict[str, list[Viagem]] = {}
        for viagem in self.viagens_por_id.values():
            viagens_por_padrao.setdefault(viagem.padrao_id, []).append(viagem)
        for padrao in self.padroes.values():
            if padrao.linha_id not in linhas_novas:
                continue
            grupos: list[tuple[int, ...]] = []
            atual: list[int] = []
            for indice, parada_id in enumerate(padrao.paradas):
                if parada_id in paradas:
                    atual.append(indice)
                elif atual:
                    grupos.append(tuple(atual))
                    atual = []
            if atual:
                grupos.append(tuple(atual))
            grupos = [grupo for grupo in grupos if len(grupo) >= 2]
            for numero, grupo in enumerate(grupos):
                novo_id = padrao.id if len(grupos) == 1 else f"{padrao.id}#trecho{numero}"
                padroes[novo_id] = Padrao(
                    novo_id, padrao.linha_id, tuple(padrao.paradas[i] for i in grupo)
                )
                for viagem in viagens_por_padrao.get(padrao.id, []):
                    viagem_id = viagem.id if len(grupos) == 1 else f"{viagem.id}#trecho{numero}"
                    viagens[viagem_id] = Viagem(
                        viagem_id,
                        novo_id,
                        viagem.servico_id,
                        tuple(viagem.horarios[i] for i in grupo),
                    )
                    for freq in freq_por_viagem.get(viagem.id, []):
                        deslocamento = viagem.horarios[grupo[0]] - viagem.horarios[0]
                        frequencias.append(
                            Frequencia(
                                viagem_id,
                                freq.inicio_s + deslocamento,
                                freq.fim_s + deslocamento,
                                freq.intervalo_s,
                            )
                        )
        rede = Rede(
            paradas=paradas,
            linhas=linhas_novas,
            padroes=padroes,
            partidas={},
            viagens_por_id=viagens,
            frequencias=tuple(frequencias),
            dia=self.dia,
            inconsistencias=self.inconsistencias.copy(),
        )
        rede.recalcular_partidas()
        return rede

    def recalcular_partidas(self) -> None:
        """Reconstrói viagens por padrão e partidas. Tempo O(N log N), espaço O(N)."""
        self.partidas = {}
        self.viagens = {}
        freq_por_viagem: dict[str, list[Frequencia]] = {}
        for freq in self.frequencias:
            freq_por_viagem.setdefault(freq.viagem_id, []).append(freq)
        for viagem in self.viagens_por_id.values():
            padrao = self.padroes[viagem.padrao_id]
            self.viagens.setdefault(padrao.id, []).append(viagem.horarios)
            frequencias = freq_por_viagem.get(viagem.id)
            if frequencias:
                for freq in frequencias:
                    for partida in range(freq.inicio_s, freq.fim_s, freq.intervalo_s):
                        for parada_id, horario in zip(padrao.paradas, viagem.horarios):
                            chave = (padrao.id, parada_id)
                            self.partidas.setdefault(chave, []).append(
                                partida + horario - viagem.horarios[0]
                            )
            else:
                for parada_id, horario in zip(padrao.paradas, viagem.horarios):
                    self.partidas.setdefault((padrao.id, parada_id), []).append(horario)
        for horarios in self.partidas.values():
            horarios.sort()
