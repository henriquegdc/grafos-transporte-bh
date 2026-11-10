"""Contratos estruturais usados pela interface sem depender do loader GTFS."""

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
    """Campos do Padrao publicados no contrato de P0-DADOS."""

    id: str
    linha_id: str
    paradas: Sequence[str]


class RedeUI(Protocol):
    """Parte do contrato de Rede consumida pela interface."""

    paradas: Mapping[str, ParadaUI]
    linhas: Mapping[str, object]
    padroes: Mapping[str, PadraoUI]


CarregadorRede = Callable[[Path], RedeUI]
