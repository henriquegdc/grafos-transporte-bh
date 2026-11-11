"""Página Baldeações: trajeto com menos baldeações entre duas paradas, no mapa (F-BALD).

RF-BAL-02: mostra a sequência de linhas e as paradas de troca. Segue o contrato da P0-UI,
`render(rede)`. A página monta a G_L uma vez por sessão, rede carregada e faixa (ou o dia
inteiro), roda `menos_baldeacoes` e mostra as baldeações, a tabela de trechos e o mapa:
cada ônibus numa cor, a pé em verde tracejado e um marcador laranja em cada troca.

estado: implementado
"""

from __future__ import annotations

from collections.abc import MutableMapping
from html import escape
from time import perf_counter

import folium
import streamlit as st
from streamlit_folium import st_folium

from transporte.algoritmos.baldeacoes import TrajetoBaldeacoes, menos_baldeacoes
from transporte.algoritmos.trajeto import A_PE, ONIBUS
from transporte.interface.mapa import criar_mapa
from transporte.interface.protocolos import RedeUI
from transporte.modelo.linhas import construir_gl
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import VisaoGL

CHAVE_GL = "f-bald-gl"
DIA_INTEIRO = "dia"
COR_A_PE = "#2ca02c"
COR_TROCA = "#ff7f0e"
CORES_ONIBUS = ("#1f77b4", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#17becf")
ROTULOS = {A_PE: "A pé", ONIBUS: "Ônibus"}


def gl_da_faixa(rede: RedeUI, faixa: str, cache: MutableMapping) -> VisaoGL:
    """G_L da faixa (ou do dia inteiro, com DIA_INTEIRO), montada uma vez por rede.

    `cache` é o `st.session_state` na página; a chave guarda `id(rede)` para descartar as
    G_L de uma rede anterior quando outra é carregada na mesma sessão. Tempo O(1) com a G_L
    pronta; a construção custa o de `construir_gl`.
    """
    guardado = cache.get(CHAVE_GL)
    if guardado is None or guardado["rede"] != id(rede):
        guardado = {"rede": id(rede), "gls": {}}
        cache[CHAVE_GL] = guardado
    if faixa not in guardado["gls"]:
        guardado["gls"][faixa] = construir_gl(
            rede, faixa=None if faixa == DIA_INTEIRO else faixa
        )
    return guardado["gls"][faixa]


def _nome(rede: RedeUI, parada_id: str) -> str:
    parada = rede.paradas[parada_id]
    return f"{getattr(parada, 'nome', '') or parada_id} ({parada_id})"


def linha_do_padrao(rede: RedeUI, padrao_id: str | None) -> str:
    """Nome da linha do padrão, ou o id da linha, ou o id do padrão; "" a pé. O(1)."""
    if padrao_id is None:
        return ""
    padrao = rede.padroes.get(padrao_id)
    if padrao is None:
        return padrao_id
    linha = rede.linhas.get(padrao.linha_id)
    return str(getattr(linha, "nome", None) or padrao.linha_id)


def tabela_trechos(rede: RedeUI, trajeto: TrajetoBaldeacoes) -> list[dict[str, str]]:
    """Linhas da tabela: trecho, modo, linha, de, para e número de paradas. O(k)."""
    return [
        {
            "Trecho": str(numero),
            "Modo": ROTULOS[t.tipo],
            "Linha": linha_do_padrao(rede, t.padrao),
            "De": _nome(rede, t.paradas[0]),
            "Para": _nome(rede, t.paradas[-1]),
            "Paradas": str(len(t.paradas) - 1),
        }
        for numero, t in enumerate(trajeto.trechos, start=1)
    ]


def resumo_linhas(rede: RedeUI, trajeto: TrajetoBaldeacoes) -> str:
    """Sequência de linhas, como "Linha 1 → Linha 2"; "a pé" se não usa ônibus. O(k)."""
    nomes = [linha_do_padrao(rede, p) for p in trajeto.padroes()]
    return " → ".join(nomes) if nomes else "a pé"


def mapa_trajeto(rede: RedeUI, trajeto: TrajetoBaldeacoes) -> folium.Map:
    """Mapa com um traço por trecho, um marcador por troca e os de origem e destino.

    Usa o mapa base da P0-UI sem a camada de paradas (os 9.659 marcadores do feed real
    pesam) e enquadra o trajeto. Tempo O(P + k), P paradas da rede (centro do mapa) e k
    paradas do trajeto.
    """
    mapa = criar_mapa(rede, mostrar_paradas=False)
    coordenada: dict[str, tuple[float, float]] = {}

    def ponto(parada_id: str) -> tuple[float, float]:
        if parada_id not in coordenada:
            parada = rede.paradas[parada_id]
            coordenada[parada_id] = (float(parada.lat), float(parada.lon))
        return coordenada[parada_id]

    ponto(trajeto.origem)
    ponto(trajeto.destino)
    cor_do_padrao: dict[str, str] = {}
    for numero, t in enumerate(trajeto.trechos, start=1):
        pontos = [ponto(p) for p in t.paradas]
        if t.tipo == A_PE:
            texto = f"{numero}. A pé de {_nome(rede, t.paradas[0])} a {_nome(rede, t.paradas[-1])}"
            estilo = {"color": COR_A_PE, "weight": 5, "dash_array": "8"}
        else:
            cor = cor_do_padrao.setdefault(
                t.padrao or "", CORES_ONIBUS[len(cor_do_padrao) % len(CORES_ONIBUS)]
            )
            texto = (
                f"{numero}. Ônibus, linha {linha_do_padrao(rede, t.padrao)}: "
                f"{len(t.paradas) - 1} parada(s)"
            )
            estilo = {"color": cor, "weight": 6}
        camada = folium.FeatureGroup(name=escape(texto))
        folium.PolyLine(pontos, tooltip=escape(texto), **estilo).add_to(camada)
        camada.add_to(mapa)

    for numero, (desce, embarca) in enumerate(trajeto.trocas(), start=1):
        texto = (
            f"Troca {numero}: desce em {_nome(rede, desce)}"
            if desce == embarca
            else f"Troca {numero}: desce em {_nome(rede, desce)}, anda até {_nome(rede, embarca)}"
        )
        folium.CircleMarker(
            ponto(desce),
            radius=9,
            color=COR_TROCA,
            fill=True,
            fill_opacity=0.9,
            tooltip=escape(texto),
        ).add_to(mapa)

    for parada_id, rotulo, cor, icone in (
        (trajeto.origem, "Origem", "green", "play"),
        (trajeto.destino, "Destino", "red", "stop"),
    ):
        folium.Marker(
            ponto(parada_id),
            tooltip=escape(f"{rotulo}: {_nome(rede, parada_id)}"),
            icon=folium.Icon(color=cor, icon=icone),
        ).add_to(mapa)

    latitudes = [lat for lat, _ in coordenada.values()]
    longitudes = [lon for _, lon in coordenada.values()]
    mapa.fit_bounds([[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]])
    _controle_de_camadas_por_ultimo(mapa)
    return mapa


def _controle_de_camadas_por_ultimo(mapa: folium.Map) -> None:
    """Move o LayerControl do mapa base para depois das camadas desta página.

    O folium escreve o JavaScript na ordem dos filhos do mapa. O criar_mapa da P0-UI já
    adiciona o LayerControl; as camadas acrescentadas depois dele seriam citadas pelo
    controle antes de existirem, e o Leaflet para com "Cannot read properties of undefined
    (reading 'setZIndex')", sem desenhar o trajeto. O(filhos do mapa).
    """
    for nome, filho in list(mapa._children.items()):
        if isinstance(filho, folium.LayerControl):
            del mapa._children[nome]
            mapa._children[nome] = filho


def _rotulo_faixa(params: Parametros, nome: str) -> str:
    if nome == DIA_INTEIRO:
        return "dia inteiro (todas as linhas do dia)"
    f = params.faixa(nome)
    return f"{f.nome} ({f.inicio_s // 3600:02d}h a {f.fim_s // 3600:02d}h)"


def render(rede: RedeUI) -> None:
    """Página Baldeações (contrato da P0-UI)."""
    st.header("Menos baldeações")
    if not rede.paradas:
        st.info("A rede carregada não tem paradas.")
        return
    params = Parametros()
    faixa = st.selectbox(
        "Linhas consideradas",
        [DIA_INTEIRO, *(f.nome for f in params.faixas)],
        format_func=lambda nome: _rotulo_faixa(params, nome),
        help="Numa faixa, só entram as linhas com partida nela, como no trajeto mais rápido.",
    )
    ids = sorted(rede.paradas, key=lambda p: (_nome(rede, p).casefold(), p))
    col_origem, col_destino = st.columns(2)
    origem = col_origem.selectbox(
        "Origem", ids, format_func=lambda p: _nome(rede, p), key="f-bald-origem"
    )
    destino = col_destino.selectbox(
        "Destino",
        ids,
        index=min(1, len(ids) - 1),
        format_func=lambda p: _nome(rede, p),
        key="f-bald-destino",
    )

    with st.spinner("Montando a G_L (padrões de linha e trocas)..."):
        gl = gl_da_faixa(rede, faixa, st.session_state)
    inicio = perf_counter()
    trajeto = menos_baldeacoes(gl, origem, destino)
    duracao = perf_counter() - inicio

    if trajeto is None:
        st.warning("Sem trajeto entre essas paradas com as linhas consideradas.")
        return
    colunas = st.columns(3)
    colunas[0].metric("Baldeações", trajeto.baldeacoes)
    colunas[1].metric("Ônibus", len(trajeto.padroes()))
    colunas[2].metric("Trechos a pé", sum(t.tipo == A_PE for t in trajeto.trechos))
    st.markdown(f"**Linhas:** {escape(resumo_linhas(rede, trajeto))}")
    st.caption(
        f"Consulta em {1e3 * duracao:.0f} ms na G_L com {gl.grafo.num_vertices()} padrões e "
        f"{gl.grafo.num_arestas()} pares com troca. Caminhada de até "
        f"{params.raio_caminhada_m:.0f} m em linha reta, uma por vez. Menor número de "
        "baldeações, não o menor tempo (compare com a página Trajetos)."
    )
    if not trajeto.trechos:
        st.info("Origem e destino são a mesma parada.")
        return
    st.dataframe(tabela_trechos(rede, trajeto), hide_index=True, width="stretch")
    st_folium(
        mapa_trajeto(rede, trajeto),
        height=500,
        use_container_width=True,
        key="mapa-baldeacoes",
        returned_objects=[],
    )
