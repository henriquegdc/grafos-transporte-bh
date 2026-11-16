"""Contratos estruturais consumidos pela interface. estado: implementado."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Protocol


class ParadaUI(Protocol):
    """Campos da Parada publicados no contrato de P0-DADOS."""

    id: str
    nome: str
    lat: float
    lon: float


class PadraoUI(Protocol):
    """Campos do padrão publicados no contrato de P0-DADOS."""

    id: str
    linha_id: str
    paradas: Sequence[str]


class LinhaUI(Protocol):
    """Campos da Linha necessários para rotular trechos de ônibus no mapa."""

    id: str
    nome: str


class TrechoUI(Protocol):
    """Campos de um trecho retornado por F-ROTA e exibido no mapa."""

    tipo: str
    paradas: Sequence[str]
    tempo_s: float
    padrao: str | None


class TrajetoUI(Protocol):
    """Resultado de trajeto com endpoints e trechos em ordem."""

    origem: str
    destino: str
    trechos: Sequence[TrechoUI]


class RedeUI(Protocol):
    """Parte do contrato de Rede consumida pela interface."""

    paradas: Mapping[str, ParadaUI]
    linhas: Mapping[str, LinhaUI]
    padroes: Mapping[str, PadraoUI]
    viagens: Mapping[str, Sequence[Sequence[int]]]
    dia: str
    inconsistencias: Sequence[str]


CarregadorRede = Callable[[Path], RedeUI]
