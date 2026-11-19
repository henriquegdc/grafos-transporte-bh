"""Página Baldeações: trajeto com menos baldeações entre duas paradas, no mapa (F-BALD).

RF-BAL-02: mostra a sequência de linhas e as paradas de troca. Segue o contrato da P0-UI,
`render(rede)`. A página monta a G_L uma vez por sessão, rede carregada e faixa (ou o dia
inteiro), roda `menos_baldeacoes` e mostra as baldeações, a tabela de trechos e o mapa:
cada ônibus numa cor, a pé em verde tracejado e um marcador laranja em cada troca.

RF-BAL-03 (F-BALD-2): numa faixa, compara com o trajeto mais rápido no G_E da mesma faixa
(com as esperas da F-ESPERA): tempo a mais contra baldeações evitadas.

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
from transporte.algoritmos.comparacao_baldeacoes import (
    ComparacaoBaldeacoes,
    comparar_baldeacoes,
)
from transporte.algoritmos.trajeto import A_PE, ESPERA, ONIBUS, Trajeto
from transporte.interface.mapa import atualizar_controle_camadas, criar_mapa
from transporte.interface.protocolos import RedeUI
from transporte.modelo.construtores import construir_ge
from transporte.modelo.linhas import construir_gl
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import VisaoGE, VisaoGL
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos

CHAVE_GL = "f-bald-gl"
CHAVE_GE = "f-bald-ge"
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


def ge_da_faixa(rede: RedeUI, faixa: str, cache: MutableMapping) -> VisaoGE:
    """G_E da faixa, com as esperas H/2 da F-ESPERA, montado uma vez por rede.

    Mesmo esquema de cache de gl_da_faixa (chave com `id(rede)`). Usa os mesmos
    Parametros da G_L, que comparar_baldeacoes exige. Tempo O(1) com o G_E pronto; a
    construção custa a estimativa de intervalos mais o `construir_ge`.
    """
    guardado = cache.get(CHAVE_GE)
    if guardado is None or guardado["rede"] != id(rede):
        guardado = {"rede": id(rede), "ges": {}}
        cache[CHAVE_GE] = guardado
    if faixa not in guardado["ges"]:
        params = Parametros()
        esperas = calcular_esperas(estimar_intervalos(rede, params))
        guardado["ges"][faixa] = construir_ge(rede, faixa, params=params, esperas=esperas)
    return guardado["ges"][faixa]


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


def _minutos(segundos: float) -> str:
    return f"{segundos / 60:.1f} min"


def _linhas_do_trajeto(rede: RedeUI, trajeto: Trajeto) -> str:
    nomes = [linha_do_padrao(rede, t.padrao) for t in trajeto.trechos if t.tipo == ONIBUS]
    return " → ".join(nomes) if nomes else "a pé"


def tabela_comparacao(rede: RedeUI, comparacao: ComparacaoBaldeacoes) -> list[dict[str, str]]:
    """Duas linhas, o mais rápido e o de menos baldeações, com tempos e linhas. O(k)."""
    k = comparacao.menos_baldeacoes.baldeacoes
    linhas = []
    for rotulo, t in (
        ("Mais rápido", comparacao.mais_rapido),
        (f"Mais rápido com até {k} baldeação(ões)", comparacao.rapido_com_menos_baldeacoes),
    ):
        partes = t.tempo_por_tipo()
        linhas.append(
            {
                "Trajeto": rotulo,
                "Tempo total": _minutos(t.tempo_total_s),
                "A pé": _minutos(partes[A_PE]),
                "Espera": _minutos(partes[ESPERA]),
                "Ônibus": _minutos(partes[ONIBUS]),
                "Baldeações": str(t.baldeacoes),
                "Linhas": _linhas_do_trajeto(rede, t),
            }
        )
    return linhas


def _render_comparacao(
    rede: RedeUI, faixa: str, gl: VisaoGL, origem: str, destino: str
) -> None:
    """Bloco da F-BALD-2 (RF-BAL-03): tempo a mais contra baldeações evitadas."""
    st.subheader("Menos baldeações contra mais rápido")
    if faixa == DIA_INTEIRO:
        st.info(
            "Escolha uma faixa horária em “Linhas consideradas” para comparar com o trajeto "
            "mais rápido: o tempo depende das esperas e das linhas que circulam na faixa."
        )
        return
    with st.spinner("Montando o G_E da faixa (paradas e plataformas)..."):
        ge = ge_da_faixa(rede, faixa, st.session_state)
    inicio = perf_counter()
    comparacao = comparar_baldeacoes(ge, gl, origem, destino)
    duracao = perf_counter() - inicio
    if comparacao is None:
        st.warning("Sem trajeto no G_E da faixa para comparar.")
        return

    colunas = st.columns(3)
    colunas[0].metric("Tempo a mais", _minutos(comparacao.tempo_a_mais_s))
    colunas[1].metric("Baldeações evitadas", comparacao.baldeacoes_evitadas)
    por_baldeacao = comparacao.tempo_por_baldeacao_evitada_s
    colunas[2].metric(
        "Por baldeação evitada", "—" if por_baldeacao is None else _minutos(por_baldeacao)
    )
    st.dataframe(tabela_comparacao(rede, comparacao), hide_index=True, width="stretch")
    if comparacao.baldeacoes_evitadas == 0:
        if comparacao.mais_rapido.baldeacoes < comparacao.menos_baldeacoes.baldeacoes:
            st.caption(
                "O mais rápido faz menos baldeações que o mínimo acima porque encadeia "
                "caminhadas; aqui em cima vale uma caminhada de até "
                f"{Parametros().raio_caminhada_m:.0f} m por vez."
            )
        else:
            st.caption("O mais rápido já tem o menor número de baldeações: nada a evitar.")
    st.caption(
        f"Comparação em {1e3 * duracao:.0f} ms no G_E da faixa com "
        f"{ge.grafo.num_vertices()} vértices e {ge.grafo.num_arestas()} arestas. As linhas "
        "do trajeto com menos baldeações podem diferir das do mapa: lá o critério é só o "
        "número de baldeações; aqui, o menor tempo com esse número."
    )


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
    # As camadas do trajeto entram depois do controle que o criar_mapa já pôs no mapa.
    atualizar_controle_camadas(mapa)
    return mapa


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
        "baldeações, não o menor tempo (a comparação com o mais rápido vem abaixo)."
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
    _render_comparacao(rede, faixa, gl, origem, destino)
