"""Componente reutilizável de mapa, caminhos e mapas de calor. estado: implementado."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from html import escape

import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

from transporte.interface.protocolos import RedeUI, TrajetoUI, TrechoUI


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
        raise ValueError(f"Coordenadas inválidas para a parada {parada_id}")
    return lat, lon


def _tempo_legivel(tempo_s: float) -> str:
    valor = float(tempo_s)
    if not math.isfinite(valor) or valor < 0:
        raise ValueError("A duração de um trecho deve ser finita e não negativa.")
    if valor >= 60 and valor.is_integer():
        minutos, segundos = divmod(int(valor), 60)
        return f"{minutos} min {segundos:02d} s"
    return f"{valor:g} s"


def _rotulo_trecho(rede: RedeUI, trecho: TrechoUI) -> tuple[str, str, str]:
    tipo = trecho.tipo
    tempo = _tempo_legivel(trecho.tempo_s)
    if tipo == "caminhada":
        return "A pé", "#228B22", tempo
    if tipo == "espera":
        padrao = rede.padroes.get(trecho.padrao) if trecho.padrao else None
        linha = rede.linhas.get(padrao.linha_id) if padrao else None
        nome = f" · {linha.nome}" if linha else ""
        return f"Espera{nome}", "#DAA520", tempo
    if tipo == "viagem":
        padrao = rede.padroes.get(trecho.padrao) if trecho.padrao else None
        linha = rede.linhas.get(padrao.linha_id) if padrao else None
        nome = f" · {linha.nome}" if linha else ""
        return f"Ônibus{nome}", "#1F77B4", tempo
    raise ValueError(f"Tipo de trecho não reconhecido: {tipo!r}")


def _adicionar_trajeto(mapa: folium.Map, rede: RedeUI, trajeto: TrajetoUI) -> None:
    for indice, trecho in enumerate(trajeto.trechos, start=1):
        if not trecho.paradas:
            raise ValueError(f"O trecho {indice} não contém paradas.")
        if trecho.tipo == "espera" and len(trecho.paradas) != 1:
            raise ValueError(f"O trecho de espera {indice} precisa de uma parada.")
        rotulo, cor, tempo = _rotulo_trecho(rede, trecho)
        pontos = [_coordenada(rede, parada_id) for parada_id in trecho.paradas]
        camada = folium.FeatureGroup(name=escape(f"{indice}. {rotulo} · {tempo}"))

        if trecho.tipo in ("caminhada", "viagem"):
            if len(pontos) < 2:
                raise ValueError(f"O trecho {indice} precisa de pelo menos duas paradas.")
            folium.PolyLine(
                pontos,
                color=cor,
                weight=6,
                tooltip=folium.Tooltip(escape(f"{rotulo} · {tempo}")),
            ).add_to(camada)
        elif trecho.tipo == "espera":
            folium.CircleMarker(
                pontos[0],
                radius=6,
                color=cor,
                fill=True,
                tooltip=folium.Tooltip(escape(f"{rotulo} · {tempo}")),
            ).add_to(camada)
        camada.add_to(mapa)

    marcadores = folium.FeatureGroup(name="Origem, destino e baldeações")
    folium.Marker(
        _coordenada(rede, trajeto.origem),
        tooltip="Origem",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(marcadores)
    folium.Marker(
        _coordenada(rede, trajeto.destino),
        tooltip="Destino",
        icon=folium.Icon(color="red", icon="stop"),
    ).add_to(marcadores)

    embarques = 0
    for trecho in trajeto.trechos:
        if trecho.tipo != "viagem":
            continue
        if embarques:
            parada = trecho.paradas[0]
            lat, lon = _coordenada(rede, parada)
            folium.CircleMarker(
                (lat, lon),
                radius=8,
                color="#FF8C00",
                fill=True,
                tooltip=folium.Tooltip("Baldeação"),
            ).add_to(marcadores)
        embarques += 1
    marcadores.add_to(mapa)


def criar_mapa(
    rede: RedeUI,
    *,
    mostrar_paradas: bool = True,
    mostrar_linhas: bool = False,
    caminhos: Sequence[Sequence[str]] = (),
    intensidades: Mapping[str, float] | None = None,
    trajeto: TrajetoUI | None = None,
    zoom_start: int = 12,
) -> folium.Map:
    """Monta as camadas Folium para paradas, padrões, caminhos e calor.

    Entradas: Rede e opções das camadas; `trajeto`, quando fornecido, usa o contrato
        estrutural de F-ROTA. `zoom_start` deve ser não negativo.
    Saída: Mapa Folium com uma camada por visualização e controle de camadas.
    Casos de borda: rede sem paradas, referências inexistentes, coordenadas inválidas,
        caminhos vazios e intensidades negativas ou não finitas levantam ValueError.
    Complexidade: tempo e espaço O(P + S + C + H + T), sendo P o número de paradas,
        S as paradas dos padrões, C as dos caminhos, H as intensidades e T as dos trechos.
    """
    if not rede.paradas:
        raise ValueError("Não é possível centralizar o mapa sem paradas.")
    if zoom_start < 0:
        raise ValueError("zoom_start deve ser não negativo.")

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
        camada = folium.FeatureGroup(name="Linhas e padrões")
        for padrao in rede.padroes.values():
            pontos = [_coordenada(rede, parada_id) for parada_id in padrao.paradas]
            if len(pontos) >= 2:
                folium.PolyLine(
                    pontos,
                    tooltip=escape(f"Linha {padrao.linha_id} · padrão {padrao.id}"),
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
                raise ValueError(f"Intensidade inválida para a parada {parada_id}")
            dados_calor.append((lat, lon, valor))
        if dados_calor:
            camada = folium.FeatureGroup(name="Mapa de calor")
            HeatMap(dados_calor).add_to(camada)
            camada.add_to(mapa)

    if trajeto is not None:
        _adicionar_trajeto(mapa, rede, trajeto)

    atualizar_controle_camadas(mapa)
    return mapa


def atualizar_controle_camadas(mapa: folium.Map) -> folium.LayerControl:
    """Garante o controle de camadas depois que uma página estende o mapa.

    Entrada: mapa existente, possivelmente estendido com `FeatureGroup` ou outras camadas.
    Saída: o controle existente ou um controle novo. O Folium coleta as camadas no momento
        de renderizar o mapa, então camadas adicionadas depois também aparecem nele.
    Casos de borda: chamadas repetidas não criam controles duplicados.
    Complexidade: O(C), C = elementos filhos diretos do mapa.
    """
    for elemento in mapa._children.values():
        if isinstance(elemento, folium.LayerControl):
            return elemento
    return folium.LayerControl(collapsed=False).add_to(mapa)


def render_mapa(
    rede: RedeUI,
    *,
    mostrar_paradas: bool = True,
    mostrar_linhas: bool = False,
    caminhos: Sequence[Sequence[str]] = (),
    intensidades: Mapping[str, float] | None = None,
    trajeto: TrajetoUI | None = None,
    altura: int = 600,
    chave: str = "mapa-rede",
) -> dict | None:
    """Renderiza mapa Folium no Streamlit para qualquer página da aplicação.

    Entradas: rede, camadas opcionais, altura positiva em pixels e chave única do widget.
        `trajeto` aceita os trechos publicados por F-ROTA; campos ausentes não são inferidos.
    Saída: dicionário de objetos retornados pelo widget (vazio por padrão), ou None.
    Casos de borda: altura não positiva e coordenadas/paradas inválidas levantam ValueError;
        cada chamada deve usar chave distinta na mesma página Streamlit.
    Complexidade: construção O(P + S + C + H + T), sendo T o total de paradas dos trechos;
        espaço O(P + S + C + H + T).
    """
    if altura <= 0:
        raise ValueError("altura deve ser positiva.")
    mapa = criar_mapa(
        rede,
        mostrar_paradas=mostrar_paradas,
        mostrar_linhas=mostrar_linhas,
        caminhos=caminhos,
        intensidades=intensidades,
        trajeto=trajeto,
    )
    return st_folium(
        mapa,
        height=altura,
        use_container_width=True,
        key=chave,
        returned_objects=[],
    )
