"""Página Centralidades: ranking das paradas mais centrais e mapa de calor (F-MET,
F-MET-2) e comunidades (F-MET-OPC).

RF-MET-03: mostra o ranking e o mapa de calor das centralidades de RF-MET-01 (graus),
RF-MET-02 (intermediação de Brandes) e RF-MET-04 (proximidade de Wasserman e Faust) sobre
G_P. Intermediação e proximidade usam amostragem de origens (RNF-06): o exato no feed real
leva dezenas de minutos. A aba Comunidades (RF-MET-06) roda a propagação de rótulos e
mostra o mapa colorido por comunidade e a modularidade. Segue o contrato `render(rede)` da
P0-UI.

estado: implementado
"""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
from html import escape
from time import perf_counter

import folium
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium

from transporte.algoritmos.centralidade import (
    distribuicao_graus,
    estimar_intermediacao,
    graus,
    proximidade,
    ranking,
)
from transporte.algoritmos.comunidades import (
    SEM_COMUNIDADE,
    Comunidades,
    modularidade,
    propagar_rotulos,
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
PROXIMIDADE = "proximidade"
SAIDA = "saida"
ENTRADA = "entrada"
METRICAS = {
    INTERMEDIACAO: "Intermediação (Brandes)",
    PROXIMIDADE: "Proximidade (Wasserman-Faust)",
    SAIDA: "Grau de saída",
    ENTRADA: "Grau de entrada",
}
CHAVE_COMUNIDADES = "f-met-opc-comunidades"
COMUNIDADES_NO_MAPA = 10
# Cores das maiores comunidades no mapa (paleta categórica "tab10"); as demais ficam cinza.
CORES_COMUNIDADES = (
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
)
COR_OUTRAS = "#b0b0b0"
COR_TOP = "#d62728"
# Mapa de calor: só a fração mais central das paradas, com raio menor que o padrão do
# Leaflet.heat (25 px). O Leaflet.heat soma a opacidade das paradas vizinhas; com as
# 9.660 paradas do feed real e os valores padrão, o mapa inteiro satura (conferido em
# 18/11 na captura da página).
FRACAO_CALOR = 0.10
RAIO_CALOR = 12
DESFOQUE_CALOR = 10
OPACIDADE_MINIMA_CALOR = 0.25


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
        amostra: origens sorteadas na intermediação e na proximidade; None usa todas
            (exato).
    Saída: Calculo; intermediação e proximidade em [0, 1] (decisão M4; Wasserman-Faust).
    Casos de borda: métrica desconhecida levanta ValueError.
    Complexidade: graus O(V + E); intermediação e proximidade O(k (V + E) log V) com k
        origens.
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
    if metrica == PROXIMIDADE:
        valores = proximidade(g, tamanho_amostra=amostra, semente=SEMENTE)
        segundos = perf_counter() - inicio
        ativos = sum(1 for v in range(g.num_vertices()) if g.vertice_ativo(v))
        if amostra is None or amostra >= ativos:
            origem = f"exata ({ativos} origens)"
        else:
            origem = f"estimada com {amostra} de {ativos} origens (semente {SEMENTE})"
        descricao = (
            f"Proximidade {origem}, por tempo de viagem, no sentido de saída (da parada "
            "para as outras), com a correção de Wasserman e Faust para quem não alcança "
            "toda a rede."
        )
        return Calculo(metrica, valores, None, descricao, segundos)
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
            "Valor": int(valor) if calculo.metrica in (SAIDA, ENTRADA) else round(valor, 6),
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


def mais_centrais(intens: dict[str, float], fracao: float = FRACAO_CALOR) -> dict[str, float]:
    """Só as paradas com valor acima do percentil (1 - fracao) das intensidades dadas.

    Corte = o valor na posição floor(n * fracao) da lista em ordem decrescente; ficam as
    paradas estritamente acima dele (empates no corte saem, para o grau, cheio de empates,
    não trazer metade da rede). Se nenhuma ficar acima (todos iguais, ou rede pequena),
    ficam as que empatam com o corte.
    Exemplo: valores 1 a 20 e fracao 0,1: corte = 18, ficam 19 e 20.
    Complexidade: tempo O(n log n), pela ordenação; espaço O(n).
    """
    if not intens:
        return {}
    valores = sorted(intens.values(), reverse=True)
    corte = valores[min(len(valores) - 1, int(len(valores) * fracao))]
    acima = {p: v for p, v in intens.items() if v > corte}
    return acima or {p: v for p, v in intens.items() if v >= corte}


def mapa_centralidades(
    rede: RedeUI, visao: VisaoGP, calculo: Calculo, k: int
) -> folium.Map:
    """Mapa de calor das paradas mais centrais e um marcador em cada uma das k primeiras.

    Usa o mapa base da P0-UI sem a camada de paradas (os marcadores das 9.660 paradas do
    feed real pesam) e acrescenta a própria camada de calor, com as `mais_centrais` e os
    parâmetros FRACAO_CALOR, RAIO_CALOR etc.: com todas as paradas e o raio padrão o calor
    satura (ver as constantes). O(V log V + k).
    """
    mapa = criar_mapa(rede, mostrar_paradas=False)
    pontos = [
        (float(rede.paradas[p].lat), float(rede.paradas[p].lon), v)
        for p, v in mais_centrais(intensidades(visao, calculo.valores)).items()
    ]
    if pontos:
        HeatMap(
            pontos,
            name="Mapa de calor",
            radius=RAIO_CALOR,
            blur=DESFOQUE_CALOR,
            min_opacity=OPACIDADE_MINIMA_CALOR,
        ).add_to(mapa)
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


# --- Comunidades (F-MET-OPC, RF-MET-06) -----------------------------------------------


@dataclass(frozen=True)
class CalculoComunidades:
    """Comunidades mostradas na página. Espaço O(V).

    Atributos:
        comunidades: partição da propagação de rótulos.
        modularidade: Q da partição (G_P não dirigido, sem pesos).
        segundos: tempo da propagação e da modularidade, sem a construção de G_P.
    """

    comunidades: Comunidades
    modularidade: float
    segundos: float


def calcular_comunidades(visao: VisaoGP, semente: int = SEMENTE) -> CalculoComunidades:
    """Propagação de rótulos em G_P e modularidade da partição.

    Complexidade: O(V + E log E) da vizinhança mais O(V + E) por iteração.
    """
    inicio = perf_counter()
    c = propagar_rotulos(visao.grafo, semente=semente)
    q = modularidade(visao.grafo, c.rotulos)
    return CalculoComunidades(c, q, perf_counter() - inicio)


def maiores_comunidades(c: Comunidades, k: int) -> list[tuple[int, int]]:
    """As k maiores comunidades: pares (comunidade, tamanho), do maior para o menor;
    empate pelo menor id. O(C log C), C = número de comunidades."""
    pares = list(enumerate(c.tamanhos()))
    pares.sort(key=lambda par: (-par[1], par[0]))
    return pares[: max(0, k)]


def tabela_comunidades(
    rede: RedeUI, visao: VisaoGP, calculo: CalculoComunidades, k: int
) -> list[dict[str, object]]:
    """Linhas da tabela das k maiores comunidades: tamanho e uma parada de exemplo (a de
    menor vértice). O(V + C log C)."""
    exemplo: dict[int, int] = {}
    for v, r in enumerate(calculo.comunidades.rotulos):
        if r != SEM_COMUNIDADE and r not in exemplo:
            exemplo[r] = v
    total = sum(calculo.comunidades.tamanhos()) or 1
    return [
        {
            "Comunidade": posicao,
            "Paradas": tamanho,
            "% das paradas": round(100 * tamanho / total, 1),
            "Exemplo": _nome(rede, visao.parada_do_vertice[exemplo[c]]),
        }
        for posicao, (c, tamanho) in enumerate(maiores_comunidades(calculo.comunidades, k),
                                              start=1)
    ]


def mapa_comunidades(
    rede: RedeUI, visao: VisaoGP, calculo: CalculoComunidades, k: int = COMUNIDADES_NO_MAPA
) -> folium.Map:
    """Mapa com as paradas das k maiores comunidades, uma cor e uma camada por comunidade.

    As demais ficam fora do mapa: desenhar as 9.660 paradas do feed real pesa no navegador
    (mesmo motivo de `mapa_centralidades`). O(V + C log C).
    """
    mapa = criar_mapa(rede, mostrar_paradas=False)
    maiores = maiores_comunidades(calculo.comunidades, min(k, len(CORES_COMUNIDADES)))
    camadas: dict[int, folium.FeatureGroup] = {}
    cores: dict[int, str] = {}
    for posicao, (c, tamanho) in enumerate(maiores, start=1):
        camadas[c] = folium.FeatureGroup(name=f"Comunidade {posicao} ({tamanho} paradas)")
        cores[c] = CORES_COMUNIDADES[posicao - 1]
    for v, c in enumerate(calculo.comunidades.rotulos):
        if c not in camadas:
            continue
        parada_id = visao.parada_do_vertice[v]
        parada = rede.paradas[parada_id]
        folium.CircleMarker(
            (float(parada.lat), float(parada.lon)),
            radius=3,
            color=cores[c],
            fill=True,
            fill_opacity=0.8,
            weight=1,
            tooltip=escape(_nome(rede, parada_id)),
        ).add_to(camadas[c])
    for camada in camadas.values():
        camada.add_to(mapa)
    atualizar_controle_camadas(mapa)
    return mapa


def _render_comunidades(rede: RedeUI, visao: VisaoGP) -> None:
    st.caption(
        "Propagação de rótulos em G_P sem sentido nem peso: cada parada adota o rótulo mais "
        "comum entre as vizinhas até nada mudar. Modularidade: quanto as ligações dentro "
        "das comunidades passam do esperado ao acaso (0 = nada, até 1)."
    )
    with st.form("f-met-opc-form"):
        semente = st.number_input("Semente da ordem de visita", value=SEMENTE, step=1)
        enviado = st.form_submit_button("Detectar comunidades", type="primary")
    if enviado:
        with st.spinner("Propagando rótulos..."):
            novo = calcular_comunidades(visao, int(semente))
        st.session_state[CHAVE_COMUNIDADES] = (id(rede), novo)
    guardado = st.session_state.get(CHAVE_COMUNIDADES)
    if guardado is None or guardado[0] != id(rede):
        st.info("Clique em Detectar comunidades.")
        return
    calculo: CalculoComunidades = guardado[1]
    c = calculo.comunidades
    colunas = st.columns(4)
    colunas[0].metric("Comunidades", c.quantidade)
    colunas[1].metric("Modularidade", f"{calculo.modularidade:.3f}")
    colunas[2].metric("Iterações", c.iteracoes)
    colunas[3].metric("Tempo do cálculo", f"{calculo.segundos:.2f} s")
    if not c.convergiu:
        st.warning(f"Parou no limite de {c.iteracoes} iterações sem estabilizar.")
    st.subheader("Maiores comunidades")
    st.dataframe(
        tabela_comunidades(rede, visao, calculo, COMUNIDADES_NO_MAPA),
        hide_index=True,
        width="stretch",
    )
    st.subheader("Mapa por comunidade")
    st.caption(f"Paradas das {COMUNIDADES_NO_MAPA} maiores comunidades, uma cor por comunidade.")
    st_folium(
        mapa_comunidades(rede, visao, calculo),
        height=550,
        use_container_width=True,
        key="mapa-comunidades",
        returned_objects=[],
    )


def render(rede: RedeUI) -> None:
    """Página Centralidades (contrato da P0-UI)."""
    st.title(TITULO)
    st.caption(
        "Centralidade das paradas em G_P (parada → próxima parada de ônibus e caminhada de "
        "até 300 m). Grau: quantas ligações saem ou chegam. Intermediação: em que fração "
        "dos caminhos mínimos entre pares de paradas a parada está no meio. Proximidade: "
        "quão perto, em tempo, a parada está das outras que alcança."
    )
    if not rede.paradas:
        st.info("A rede carregada não tem paradas.")
        return
    with st.spinner("Montando G_P..."):
        visao = gp_da_rede(rede, st.session_state)
    aba_metricas, aba_comunidades = st.tabs(["Centralidades", "Comunidades"])
    with aba_metricas:
        _render_metricas(rede, visao)
    with aba_comunidades:
        _render_comunidades(rede, visao)


def _render_metricas(rede: RedeUI, visao: VisaoGP) -> None:
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
        if n == 1:
            amostra = k = 1
        else:
            amostra = st.slider(
                "Intermediação e proximidade: origens sorteadas",
                min_value=1,
                max_value=min(n, 500),
                value=min(AMOSTRA_PADRAO, n),
                help=(
                    "O cálculo exato roda um Dijkstra por parada. Na intermediação "
                    "amostrada, a tabela mostra o erro padrão da estimativa."
                ),
            )
            k = st.slider("Paradas no ranking", min_value=1, max_value=min(n, 50),
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
    st.subheader(f"Ranking: {METRICAS[calculo.metrica]}")
    st.dataframe(tabela_ranking(rede, visao, calculo, k), hide_index=True, width="stretch")
    if calculo.distribuicao is not None:
        st.subheader("Distribuição de graus")
        st.bar_chart(
            {"Paradas": dict(calculo.distribuicao)},
            x_label="Grau",
            y_label="Paradas",
        )
    st.subheader("Mapa de calor")
    st.caption(
        f"Calor das {FRACAO_CALOR:.0%} paradas mais centrais (com todas, o mapa satura); "
        f"círculos vermelhos: as {k} primeiras do ranking."
    )
    st_folium(
        mapa_centralidades(rede, visao, calculo, k),
        height=550,
        use_container_width=True,
        key="mapa-centralidades",
        returned_objects=[],
    )
