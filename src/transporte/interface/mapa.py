"""Componente reutilizavel de mapa da rede, caminhos e mapas de calor."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from html import escape

import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

from transporte.interface.protocolos import RedeUI


def _coordenada(rede: RedeUI, parada_id: str) -> tuple[float, float]:
    try:
        parada = rede.paradas[parada_id]
    except KeyError as erro:
        raise ValueError(f"A rede referencia uma parada inexistente: {parada_id}") from erro
    lat, lon = float(parada.lat), float(parada.lon)
    if (
        not math.isfinite(lat)
        or not math.isfinite(lon)
        or not -90 <= lat <= 90
        or not -180 <= lon <= 180
    ):
        raise ValueError(f"Coordenadas invalidas para a parada {parada_id}")
    return lat, lon


def criar_mapa(
    rede: RedeUI,
    *,
    mostrar_paradas: bool = True,
    mostrar_linhas: bool = False,
    caminhos: Sequence[Sequence[str]] = (),
    intensidades: Mapping[str, float] | None = None,
    zoom_start: int = 12,
) -> folium.Map:
    """Monta as camadas Folium para paradas, padroes, caminhos e calor.

    Complexidade: O(P + S + C + H), sendo P o numero de paradas, S a soma de
    paradas nos padroes exibidos, C a soma de pontos nos caminhos e H o numero
    de paradas com intensidade. O mapa e os marcadores ocupam O(P + S + C + H).
    """
    if not rede.paradas:
        raise ValueError("Nao e possivel centralizar o mapa sem paradas.")
    if zoom_start < 0:
        raise ValueError("zoom_start deve ser nao negativo.")

    coordenadas = {parada_id: _coordenada(rede, parada_id) for parada_id in rede.paradas}
    centro = (
        sum(lat for lat, _ in coordenadas.values()) / len(coordenadas),
        sum(lon for _, lon in coordenadas.values()) / len(coordenadas),
    )
    mapa = folium.Map(location=centro, zoom_start=zoom_start, control_scale=True)

    if mostrar_paradas:
        camada = folium.FeatureGroup(name="Paradas")
        cluster = MarkerCluster()
        for parada_id, parada in rede.paradas.items():
            lat, lon = coordenadas[parada_id]
            titulo = escape(f"{parada.nome} ({parada_id})")
            folium.Marker(
                location=(lat, lon),
                tooltip=folium.Tooltip(titulo),
                popup=folium.Popup(titulo),
            ).add_to(cluster)
        cluster.add_to(camada)
        camada.add_to(mapa)

    if mostrar_linhas:
        camada = folium.FeatureGroup(name="Linhas e padroes")
        for padrao in rede.padroes.values():
            pontos = [_coordenada(rede, parada_id) for parada_id in padrao.paradas]
            if len(pontos) >= 2:
                folium.PolyLine(
                    pontos,
                    tooltip=escape(f"Linha {padrao.linha_id} · padrao {padrao.id}"),
                ).add_to(camada)
        camada.add_to(mapa)

    for indice, caminho in enumerate(caminhos, start=1):
        if not caminho:
            raise ValueError("Um caminho precisa conter ao menos uma parada.")
        pontos = [_coordenada(rede, parada_id) for parada_id in caminho]
        camada = folium.FeatureGroup(name=f"Caminho {indice}")
        if len(pontos) == 1:
            folium.CircleMarker(pontos[0], radius=7, color="#d62728").add_to(camada)
        else:
            folium.PolyLine(pontos, color="#d62728", weight=5, tooltip=f"Caminho {indice}").add_to(
                camada
            )
        camada.add_to(mapa)

    if intensidades is not None:
        dados_calor = []
        for parada_id, intensidade in intensidades.items():
            lat, lon = _coordenada(rede, parada_id)
            valor = float(intensidade)
            if not math.isfinite(valor) or valor < 0:
                raise ValueError(f"Intensidade invalida para a parada {parada_id}")
            dados_calor.append((lat, lon, valor))
        if dados_calor:
            camada = folium.FeatureGroup(name="Mapa de calor")
            HeatMap(dados_calor).add_to(camada)
            camada.add_to(mapa)

    folium.LayerControl(collapsed=False).add_to(mapa)
    return mapa


def render_mapa(
    rede: RedeUI,
    *,
    mostrar_paradas: bool = True,
    mostrar_linhas: bool = False,
    caminhos: Sequence[Sequence[str]] = (),
    intensidades: Mapping[str, float] | None = None,
    altura: int = 600,
    chave: str = "mapa-rede",
) -> dict | None:
    """Desenha no Streamlit um mapa Folium reutilizavel pelas paginas."""
    if altura <= 0:
        raise ValueError("altura deve ser positiva.")
    mapa = criar_mapa(
        rede,
        mostrar_paradas=mostrar_paradas,
        mostrar_linhas=mostrar_linhas,
        caminhos=caminhos,
        intensidades=intensidades,
    )
    return st_folium(mapa, height=altura, use_container_width=True, key=chave)
