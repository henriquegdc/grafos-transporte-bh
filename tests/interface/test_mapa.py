from __future__ import annotations

from dataclasses import dataclass

import folium
import pytest
from folium.plugins import HeatMap, MarkerCluster

from transporte.interface.mapa import criar_mapa


@dataclass(frozen=True)
class Parada:
    id: str
    nome: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Padrao:
    id: str
    linha_id: str
    paradas: tuple[str, ...]


@dataclass
class Rede:
    paradas: dict[str, Parada]
    linhas: dict[str, object]
    padroes: dict[str, Padrao]


@pytest.fixture
def rede() -> Rede:
    paradas = {
        "A": Parada("A", "Estação Central", -19.9, -43.9),
        "B": Parada("B", "Praça Sete", -19.91, -43.92),
    }
    return Rede(paradas, {"L1": object()}, {"P1": Padrao("P1", "L1", ("A", "B"))})


def _descendentes(elemento: folium.MacroElement) -> list[folium.MacroElement]:
    resultado = [elemento]
    for filho in getattr(elemento, "_children", {}).values():
        resultado.extend(_descendentes(filho))
    return resultado


def test_criar_mapa_exibe_paradas_linhas_caminhos_e_calor(rede: Rede) -> None:
    mapa = criar_mapa(
        rede,
        mostrar_linhas=True,
        caminhos=(("A", "B"),),
        intensidades={"A": 0.8, "B": 0.2},
    )

    elementos = _descendentes(mapa)
    assert isinstance(mapa, folium.Map)
    assert any(isinstance(elemento, MarkerCluster) for elemento in elementos)
    assert sum(isinstance(elemento, folium.PolyLine) for elemento in elementos) == 2
    assert any(isinstance(elemento, HeatMap) for elemento in elementos)
    assert any(isinstance(elemento, folium.LayerControl) for elemento in elementos)


def test_criar_mapa_marca_caminho_de_uma_parada(rede: Rede) -> None:
    mapa = criar_mapa(rede, caminhos=(("A",),), mostrar_paradas=False)

    assert any(isinstance(elemento, folium.CircleMarker) for elemento in _descendentes(mapa))


def test_criar_mapa_rejeita_caminho_com_parada_ausente(rede: Rede) -> None:
    with pytest.raises(ValueError, match="parada inexistente"):
        criar_mapa(rede, caminhos=(("A", "C"),))


def test_criar_mapa_rejeita_coordenada_invalida(rede: Rede) -> None:
    rede.paradas["B"] = Parada("B", "Invalida", 91.0, 0.0)

    with pytest.raises(ValueError, match="Coordenadas invalidas"):
        criar_mapa(rede)


def test_criar_mapa_rejeita_intensidade_negativa(rede: Rede) -> None:
    with pytest.raises(ValueError, match="Intensidade invalida"):
        criar_mapa(rede, intensidades={"A": -1.0})


def test_criar_mapa_rejeita_rede_sem_paradas() -> None:
    with pytest.raises(ValueError, match="sem paradas"):
        criar_mapa(Rede({}, {}, {}))
