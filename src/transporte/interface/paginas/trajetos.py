"""Página Trajetos: trajeto mais rápido entre duas paradas, no mapa (F-ROTA, RF-ROT-02).

Segue o contrato da P0-UI, `render(rede)`. A página monta o G_E da faixa escolhida uma vez
por sessão e por rede carregada, roda `trajeto_mais_rapido` e mostra o tempo total, as
baldeações, o tempo por tipo, a tabela de trechos e o mapa com um traço por trecho: a pé em
verde tracejado, ônibus numa cor por padrão, espera como um círculo na parada.

A espera de embarque é a provisória de 300 s (D6) até a F-ESPERA publicar a tabela de
esperas; a página então passa a tabela a `construir_ge`.

estado: implementado
"""

from __future__ import annotations

from collections.abc import MutableMapping
from html import escape
from time import perf_counter

import folium
import streamlit as st
from streamlit_folium import st_folium

from transporte.algoritmos.trajeto import A_PE, ESPERA, ONIBUS, Trajeto, trajeto_mais_rapido
from transporte.interface.mapa import criar_mapa
from transporte.interface.protocolos import RedeUI
from transporte.modelo.construtores import construir_ge
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import VisaoGE

CHAVE_GE = "f-rota-ge"
LIMITE_RNF05_S = 1.0
COR_A_PE = "#2ca02c"
COR_ESPERA = "#ff7f0e"
CORES_ONIBUS = ("#1f77b4", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#17becf")
ROTULOS = {A_PE: "A pé", ESPERA: "Espera", ONIBUS: "Ônibus"}


def ge_da_faixa(rede: RedeUI, faixa: str, cache: MutableMapping) -> VisaoGE:
    """G_E da faixa, montado uma vez por rede carregada e guardado em `cache`.

    `cache` é o `st.session_state` na página; a chave guarda `id(rede)` para descartar os
    G_E de uma rede anterior quando outra é carregada na mesma sessão. Tempo O(1) com o
    G_E pronto; a construção custa o de `construir_ge`.
    """
    guardado = cache.get(CHAVE_GE)
    if guardado is None or guardado["rede"] != id(rede):
        guardado = {"rede": id(rede), "ges": {}}
        cache[CHAVE_GE] = guardado
    if faixa not in guardado["ges"]:
        guardado["ges"][faixa] = construir_ge(rede, faixa)
    return guardado["ges"][faixa]


def _nome(rede: RedeUI, parada_id: str) -> str:
    parada = rede.paradas[parada_id]
    return f"{getattr(parada, 'nome', '') or parada_id} ({parada_id})"


def _linha(rede: RedeUI, padrao_id: str | None) -> str:
    """Nome da linha do padrão, ou o id da linha, ou o id do padrão."""
    if padrao_id is None:
        return ""
    padrao = rede.padroes.get(padrao_id)
    if padrao is None:
        return padrao_id
    linha = rede.linhas.get(padrao.linha_id)
    return str(getattr(linha, "nome", None) or padrao.linha_id)


def _minutos(segundos: float) -> str:
    return f"{segundos / 60:.1f} min"


def tabela_trechos(rede: RedeUI, trajeto: Trajeto) -> list[dict[str, str]]:
    """Linhas da tabela de trechos: modo, linha, de, para, paradas e tempo. O(k)."""
    linhas = []
    for numero, trecho in enumerate(trajeto.trechos, start=1):
        linhas.append(
            {
                "Trecho": str(numero),
                "Modo": ROTULOS[trecho.tipo],
                "Linha": _linha(rede, trecho.padrao),
                "De": _nome(rede, trecho.paradas[0]),
                "Para": _nome(rede, trecho.paradas[-1]),
                "Paradas": str(max(len(trecho.paradas) - 1, 0)),
                "Tempo": _minutos(trecho.tempo_s),
            }
        )
    return linhas


def mapa_trajeto(rede: RedeUI, trajeto: Trajeto) -> folium.Map:
    """Mapa Folium com um traço por trecho e marcadores de origem e destino.

    Usa o mapa base da P0-UI sem a camada de paradas (os 9.659 marcadores do feed real
    levam dezenas de segundos) e enquadra o trajeto. Tempo O(P + k), com P paradas da rede
    (centro do mapa) e k paradas do trajeto.
    """
    mapa = criar_mapa(rede, mostrar_paradas=False)
    coordenada = {}

    def ponto(parada_id: str) -> tuple[float, float]:
        if parada_id not in coordenada:
            parada = rede.paradas[parada_id]
            coordenada[parada_id] = (float(parada.lat), float(parada.lon))
        return coordenada[parada_id]

    cor_do_padrao: dict[str, str] = {}
    for numero, trecho in enumerate(trajeto.trechos, start=1):
        tempo = _minutos(trecho.tempo_s)
        if trecho.tipo == ESPERA:
            texto = f"{numero}. Espera da linha {_linha(rede, trecho.padrao)}: {tempo}"
            camada = folium.FeatureGroup(name=escape(texto))
            folium.CircleMarker(
                ponto(trecho.paradas[0]),
                radius=9,
                color=COR_ESPERA,
                fill=True,
                fill_opacity=0.8,
                tooltip=escape(texto),
            ).add_to(camada)
        else:
            pontos = [ponto(p) for p in trecho.paradas]
            if trecho.tipo == A_PE:
                texto = f"{numero}. A pé: {tempo}"
                estilo = {"color": COR_A_PE, "weight": 5, "dash_array": "8"}
            else:
                cor = cor_do_padrao.setdefault(
                    trecho.padrao or "", CORES_ONIBUS[len(cor_do_padrao) % len(CORES_ONIBUS)]
                )
                texto = (
                    f"{numero}. Ônibus, linha {_linha(rede, trecho.padrao)}: {tempo}, "
                    f"{len(trecho.paradas) - 1} parada(s)"
                )
                estilo = {"color": cor, "weight": 6}
            camada = folium.FeatureGroup(name=escape(texto))
            folium.PolyLine(pontos, tooltip=escape(texto), **estilo).add_to(camada)
        camada.add_to(mapa)

    for parada_id, rotulo, icone in (
        (trajeto.origem, "Origem", "play"),
        (trajeto.destino, "Destino", "stop"),
    ):
        folium.Marker(
            ponto(parada_id),
            tooltip=escape(f"{rotulo}: {_nome(rede, parada_id)}"),
            icon=folium.Icon(color="green" if rotulo == "Origem" else "red", icon=icone),
        ).add_to(mapa)

    latitudes = [lat for lat, _ in coordenada.values()]
    longitudes = [lon for _, lon in coordenada.values()]
    mapa.fit_bounds([[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]])
    return mapa


def _rotulo_faixa(faixa) -> str:
    return f"{faixa.nome} ({faixa.inicio_s // 3600:02d}h a {faixa.fim_s // 3600:02d}h)"


def render(rede: RedeUI) -> None:
    """Página Trajetos (contrato da P0-UI)."""
    st.header("Trajeto mais rápido")
    if not rede.paradas:
        st.info("A rede carregada não tem paradas.")
        return
    params = Parametros()
    faixa = st.selectbox(
        "Faixa horária",
        [f.nome for f in params.faixas],
        format_func=lambda nome: _rotulo_faixa(params.faixa(nome)),
    )
    ids = sorted(rede.paradas, key=lambda p: (_nome(rede, p).casefold(), p))
    col_origem, col_destino = st.columns(2)
    origem = col_origem.selectbox("Origem", ids, format_func=lambda p: _nome(rede, p))
    destino = col_destino.selectbox(
        "Destino", ids, index=min(1, len(ids) - 1), format_func=lambda p: _nome(rede, p)
    )

    with st.spinner(f"Montando o G_E da faixa {faixa}..."):
        ge = ge_da_faixa(rede, faixa, st.session_state)
    inicio = perf_counter()
    trajeto = trajeto_mais_rapido(ge, origem, destino)
    duracao = perf_counter() - inicio

    if trajeto is None:
        st.warning("Sem trajeto entre essas paradas nesta faixa.")
        return
    por_tipo = trajeto.tempo_por_tipo()
    colunas = st.columns(5)
    colunas[0].metric("Tempo total", _minutos(trajeto.tempo_total_s))
    colunas[1].metric("Baldeações", trajeto.baldeacoes)
    colunas[2].metric("A pé", _minutos(por_tipo[A_PE]))
    colunas[3].metric("Espera", _minutos(por_tipo[ESPERA]))
    colunas[4].metric("Ônibus", _minutos(por_tipo[ONIBUS]))
    st.caption(
        f"Consulta em {1e3 * duracao:.0f} ms (RNF-05: até {LIMITE_RNF05_S:.0f} s). Espera de "
        f"{params.espera_padrao_s:.0f} s em todo embarque, provisória até a tabela da F-ESPERA; "
        "tempo esperado para quem chega à parada num instante qualquer da faixa."
    )
    if not trajeto.trechos:
        st.info("Origem e destino são a mesma parada.")
        return
    st.dataframe(tabela_trechos(rede, trajeto), hide_index=True, use_container_width=True)
    st_folium(
        mapa_trajeto(rede, trajeto),
        height=500,
        use_container_width=True,
        key="mapa-trajeto",
        returned_objects=[],
    )
