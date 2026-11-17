"""Página Centralidades: ranking das paradas mais centrais e mapa de calor (F-MET).

RF-MET-03: mostra o ranking e o mapa de calor das centralidades de RF-MET-01 (graus) e
RF-MET-02 (intermediação de Brandes) sobre G_P. A intermediação usa amostragem de origens
com erro padrão (RNF-06): o exato no feed real leva dezenas de minutos. Segue o contrato
`render(rede)` da P0-UI.

estado: implementado
"""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
from html import escape
from time import perf_counter

import folium
import streamlit as st
from streamlit_folium import st_folium

from transporte.algoritmos.centralidade import (
    distribuicao_graus,
    estimar_intermediacao,
    graus,
    ranking,
)
from transporte.interface.mapa import atualizar_controle_camadas, criar_mapa
from transporte.interface.protocolos import RedeUI
from transporte.modelo.construtores import construir_gp
from transporte.modelo.visoes import VIAGEM, VisaoGP

TITULO = "Centralidades"
CHAVE_GP = "f-met-gp"
CHAVE_RESULTADO = "f-met-resultado"
SEMENTE = 2026
AMOSTRA_PADRAO = 50
INTERMEDIACAO = "intermediacao"
SAIDA = "saida"
ENTRADA = "entrada"
METRICAS = {
    INTERMEDIACAO: "Intermediação (Brandes)",
    SAIDA: "Grau de saída",
    ENTRADA: "Grau de entrada",
}
COR_TOP = "#d62728"


@dataclass(frozen=True)
class Calculo:
    """Resultado mostrado na página. Espaço O(V).

    Atributos:
        metrica: INTERMEDIACAO, SAIDA ou ENTRADA.
        valores: valor por vértice de G_P.
        erros: erro padrão por vértice (intermediação amostrada) ou None.
        descricao: o que foi calculado, para a legenda.
        segundos: tempo do cálculo, sem a construção de G_P.
        distribuicao: grau -> número de paradas (só nos graus).
    """

    metrica: str
    valores: list[float]
    erros: list[float] | None
    descricao: str
    segundos: float
    distribuicao: dict[int, int] | None = None


def gp_da_rede(rede: RedeUI, cache: MutableMapping) -> VisaoGP:
    """G_P da rede carregada, construído uma vez por rede e guardado em `cache`.

    `cache` é o `st.session_state`; a chave guarda `id(rede)` para descartar o G_P de uma
    rede anterior. Tempo O(1) com o G_P pronto; a construção custa o de `construir_gp`.
    """
    guardado = cache.get(CHAVE_GP)
    if guardado is None or guardado[0] != id(rede):
        guardado = (id(rede), construir_gp(rede))
        cache[CHAVE_GP] = guardado
    return guardado[1]


def calcular(
    visao: VisaoGP,
    metrica: str,
    *,
    so_viagem: bool = True,
    ponderado: bool = True,
    amostra: int | None = AMOSTRA_PADRAO,
) -> Calculo:
    """Calcula a métrica escolhida sobre G_P.

    Entradas:
        metrica: INTERMEDIACAO, SAIDA ou ENTRADA.
        so_viagem: nos graus, conta só arestas de viagem (decisão M1: a caminhada de até
            300 m liga paradas vizinhas e inflaria o grau).
        ponderado: na intermediação, caminhos mínimos por tempo (True) ou por número de
            trechos (False).
        amostra: origens sorteadas na intermediação; None usa todas (exato).
    Saída: Calculo; a intermediação sai normalizada em [0, 1] (decisão M4).
    Casos de borda: métrica desconhecida levanta ValueError.
    Complexidade: graus O(V + E); intermediação O(k (V + E) log V) com k origens.
    """
    g = visao.grafo
    inicio = perf_counter()
    if metrica == INTERMEDIACAO:
        est = estimar_intermediacao(
            g, amostra, semente=SEMENTE, ponderado=ponderado, normalizar=True
        )
        segundos = perf_counter() - inicio
        base = "tempo de viagem" if ponderado else "número de trechos"
        if est.exata:
            descricao = f"Intermediação exata ({est.tamanho_populacao} origens), por {base}."
        else:
            descricao = (
                f"Intermediação estimada com {est.tamanho_amostra} de "
                f"{est.tamanho_populacao} origens (semente {SEMENTE}), por {base}; "
                "± é o erro padrão."
            )
        return Calculo(metrica, est.valores, None if est.exata else est.erro_padrao,
                       descricao, segundos)
    if metrica not in (SAIDA, ENTRADA):
        raise ValueError(f"métrica desconhecida: {metrica}")
    r = graus(g, tipos={VIAGEM} if so_viagem else None)
    lista = r.saida if metrica == SAIDA else r.entrada
    segundos = perf_counter() - inicio
    arestas = "só trechos de ônibus" if so_viagem else "ônibus e caminhada"
    return Calculo(
        metrica,
        [float(x) for x in lista],
        None,
        f"{METRICAS[metrica]} contando {arestas}.",
        segundos,
        distribuicao_graus(g, lista),
    )


def _nome(rede: RedeUI, parada_id: str) -> str:
    parada = rede.paradas[parada_id]
    return f"{getattr(parada, 'nome', '') or parada_id} ({parada_id})"


def tabela_ranking(
    rede: RedeUI, visao: VisaoGP, calculo: Calculo, k: int
) -> list[dict[str, object]]:
    """As k paradas mais centrais, em ordem decrescente, com o erro se houver. O(V log V)."""
    linhas: list[dict[str, object]] = []
    for posicao, (v, valor) in enumerate(ranking(visao.grafo, calculo.valores, k), start=1):
        linha: dict[str, object] = {
            "Posição": posicao,
            "Parada": _nome(rede, visao.parada_do_vertice[v]),
            "Valor": int(valor) if calculo.metrica != INTERMEDIACAO else round(valor, 6),
        }
        if calculo.erros is not None:
            linha["± erro padrão"] = round(calculo.erros[v], 6)
        linhas.append(linha)
    return linhas


def intensidades(visao: VisaoGP, valores: list[float]) -> dict[str, float]:
    """Parada -> valor / maior valor, em [0, 1], só das paradas com valor > 0.

    O Leaflet.heat satura acima de 1; sem normalizar, a intermediação (valores grandes)
    pintaria o mapa inteiro com a cor máxima. O(V).
    """
    maior = max(valores, default=0.0)
    if maior <= 0:
        return {}
    return {
        visao.parada_do_vertice[v]: x / maior
        for v, x in enumerate(valores)
        if x > 0 and visao.grafo.vertice_ativo(v)
    }


def mapa_centralidades(
    rede: RedeUI, visao: VisaoGP, calculo: Calculo, k: int
) -> folium.Map:
    """Mapa de calor da métrica e um marcador numerado em cada uma das k mais centrais.

    Sem a camada de paradas (os marcadores das 9.660 paradas do feed real pesam). O(V + k).
    """
    mapa = criar_mapa(
        rede, mostrar_paradas=False, intensidades=intensidades(visao, calculo.valores)
    )
    camada = folium.FeatureGroup(name=f"Top {k}")
    for posicao, (v, valor) in enumerate(ranking(visao.grafo, calculo.valores, k), start=1):
        parada_id = visao.parada_do_vertice[v]
        parada = rede.paradas[parada_id]
        texto = escape(f"{posicao}º {_nome(rede, parada_id)}: {valor:.6g}")
        folium.CircleMarker(
            (float(parada.lat), float(parada.lon)),
            radius=8,
            color=COR_TOP,
            fill=True,
            fill_opacity=0.9,
            tooltip=texto,
        ).add_to(camada)
    camada.add_to(mapa)
    atualizar_controle_camadas(mapa)
    return mapa


def render(rede: RedeUI) -> None:
    """Página Centralidades (contrato da P0-UI)."""
    st.title(TITULO)
    st.caption(
        "Centralidade das paradas em G_P (parada → próxima parada de ônibus e caminhada de "
        "até 300 m). Grau: quantas ligações saem ou chegam. Intermediação: em que fração "
        "dos caminhos mínimos entre pares de paradas a parada está no meio."
    )
    if not rede.paradas:
        st.info("A rede carregada não tem paradas.")
        return
    with st.spinner("Montando G_P..."):
        visao = gp_da_rede(rede, st.session_state)
    g = visao.grafo
    n = g.num_vertices()

    with st.form("f-met-form"):
        metrica = st.radio(
            "Métrica", list(METRICAS), format_func=METRICAS.__getitem__, horizontal=True
        )
        col1, col2 = st.columns(2)
        so_viagem = col1.checkbox(
            "Graus: só trechos de ônibus", value=True,
            help="Sem a caminhada, que liga paradas vizinhas e inflaria o grau.",
        )
        ponderado = col2.checkbox(
            "Intermediação: caminhos mínimos por tempo", value=True,
            help="Desmarcado, conta o número de trechos.",
        )
        amostra = st.slider(
            "Intermediação: origens sorteadas",
            min_value=1,
            max_value=max(1, min(n, 500)),
            value=min(AMOSTRA_PADRAO, n),
            help=(
                "O exato roda um Dijkstra a partir de cada parada. Com k origens custa k/N do "
                "exato, e a tabela mostra o erro padrão de cada estimativa."
            ),
        )
        k = st.slider("Paradas no ranking", min_value=1, max_value=max(1, min(n, 50)),
                      value=min(10, n))
        enviado = st.form_submit_button("Calcular", type="primary")

    if enviado:
        with st.spinner(f"Calculando {METRICAS[metrica].lower()}..."):
            novo = calcular(
                visao, metrica, so_viagem=so_viagem, ponderado=ponderado, amostra=amostra
            )
        # O resultado fica na sessão para sobreviver aos reruns do Streamlit; a chave
        # id(rede) descarta o de uma rede carregada antes.
        st.session_state[CHAVE_RESULTADO] = (id(rede), novo)
    guardado = st.session_state.get(CHAVE_RESULTADO)
    if guardado is None or guardado[0] != id(rede):
        st.info("Escolha a métrica e clique em Calcular.")
        return
    calculo: Calculo = guardado[1]

    colunas = st.columns(3)
    colunas[0].metric("Paradas (V)", n)
    colunas[1].metric("Ligações (E)", g.num_arestas())
    colunas[2].metric("Tempo do cálculo", f"{calculo.segundos:.2f} s")
    st.caption(calculo.descricao)
    st.subheader(f"Ranking: {METRICAS[calculo.metrica].lower()}")
    st.dataframe(tabela_ranking(rede, visao, calculo, k), hide_index=True, width="stretch")
    if calculo.distribuicao is not None:
        st.subheader("Distribuição de graus")
        st.bar_chart(
            {"Paradas": dict(calculo.distribuicao)},
            x_label="Grau",
            y_label="Paradas",
        )
    st.subheader("Mapa de calor")
    st_folium(
        mapa_centralidades(rede, visao, calculo, k),
        height=550,
        use_container_width=True,
        key="mapa-centralidades",
        returned_objects=[],
    )
