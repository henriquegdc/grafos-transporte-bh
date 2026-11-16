from __future__ import annotations

from dataclasses import dataclass

import folium
import pytest
from folium.plugins import HeatMap, MarkerCluster

import transporte.interface.mapa as modulo_mapa
from transporte.interface.mapa import atualizar_controle_camadas, criar_mapa


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


@dataclass(frozen=True)
class Linha:
    id: str
    nome: str


@dataclass(frozen=True)
class Trecho:
    tipo: str
    paradas: tuple[str, ...]
    tempo_s: float
    padrao: str | None = None


@dataclass(frozen=True)
class Trajeto:
    origem: str
    destino: str
    trechos: tuple[Trecho, ...]


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

    with pytest.raises(ValueError, match="Coordenadas inválidas"):
        criar_mapa(rede)


def test_criar_mapa_rejeita_intensidade_negativa(rede: Rede) -> None:
    with pytest.raises(ValueError, match="Intensidade inválida"):
        criar_mapa(rede, intensidades={"A": -1.0})


def test_criar_mapa_rejeita_rede_sem_paradas() -> None:
    with pytest.raises(ValueError, match="sem paradas"):
        criar_mapa(Rede({}, {}, {}))


def test_controle_camadas_inclui_camada_adicionada_depois_da_criacao(rede: Rede) -> None:
    mapa = criar_mapa(rede, mostrar_paradas=False)
    camada = folium.FeatureGroup(name="Camada da página").add_to(mapa)

    controle = atualizar_controle_camadas(mapa)
    html = mapa.get_root().render()

    assert camada.layer_name in controle.overlays
    assert sum(isinstance(item, folium.LayerControl) for item in mapa._children.values()) == 1
    # O JS precisa declarar a camada antes que o controle a referencie; senão o Leaflet
    # recebe undefined e o script do mapa falha no navegador.
    declaracao = html.index(f"var {camada.get_name()} =")
    assert declaracao < html.index("L.control.layers")
    assert declaracao < html.index(f"{camada.get_name()},")


def test_controle_camadas_repetido_continua_depois_de_todas_as_camadas(rede: Rede) -> None:
    mapa = criar_mapa(rede, mostrar_paradas=False)
    primeira = folium.FeatureGroup(name="Primeira").add_to(mapa)
    atualizar_controle_camadas(mapa)
    segunda = folium.FeatureGroup(name="Segunda").add_to(mapa)

    controle = atualizar_controle_camadas(mapa)
    html = mapa.get_root().render()

    assert list(mapa._children.values())[-1] is controle
    assert sum(isinstance(item, folium.LayerControl) for item in mapa._children.values()) == 1
    for camada in (primeira, segunda):
        assert html.index(f"var {camada.get_name()} =") < html.index("L.control.layers")


def test_criar_mapa_mostra_trechos_e_marcadores_do_trajeto(rede: Rede) -> None:
    rede.linhas = {"L1": Linha("L1", "Linha & 1"), "L2": Linha("L2", "Linha 2")}
    rede.padroes = {
        "P1": Padrao("P1", "L1", ("A", "B")),
        "P2": Padrao("P2", "L2", ("A", "B")),
    }
    trajeto = Trajeto(
        "A",
        "A",
        (
            Trecho("espera", ("A",), 300, "P1"),
            Trecho("viagem", ("A", "B"), 300, "P1"),
            Trecho("caminhada", ("B", "A"), 70),
            Trecho("espera", ("A",), 60, "P2"),
            Trecho("viagem", ("A", "B"), 120, "P2"),
        ),
    )

    mapa = criar_mapa(rede, mostrar_paradas=False, trajeto=trajeto)
    elementos = _descendentes(mapa)
    html = mapa.get_root().render()

    linhas = [elemento for elemento in elementos if isinstance(elemento, folium.PolyLine)]
    assert len(linhas) == 3
    assert [linha.options["color"] for linha in linhas] == ["#1F77B4", "#228B22", "#1F77B4"]
    assert sum(isinstance(elemento, folium.CircleMarker) for elemento in elementos) == 3
    assert sum(type(elemento) is folium.Marker for elemento in elementos) == 2
    assert "Ônibus · Linha &amp; 1" in html
    assert "Baldeação" in html
    assert "Origem" in html and "Destino" in html


def test_criar_mapa_rejeita_trecho_de_espera_com_mais_de_uma_parada(rede: Rede) -> None:
    trajeto = Trajeto(
        "A",
        "B",
        (Trecho("espera", ("A", "B"), 60, "P1"),),
    )

    with pytest.raises(ValueError, match="precisa de uma parada"):
        criar_mapa(rede, trajeto=trajeto)


def test_render_mapa_solicita_lista_vazia_de_objetos_retornados(monkeypatch, rede: Rede) -> None:
    argumentos = {}
    monkeypatch.setattr(modulo_mapa, "st_folium", lambda _mapa, **kwargs: argumentos.update(kwargs))

    modulo_mapa.render_mapa(rede)

    assert argumentos["returned_objects"] == []
