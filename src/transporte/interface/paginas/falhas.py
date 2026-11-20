"""Página Falhas: simula a saída de uma parada, de um trecho ou de uma linha (F-RES).

RF-RES-01 a RF-RES-03 na interface: escolhe a falha, roda `simular_falha` sobre G_P e mostra
as componentes fortemente conexas antes e depois, as paradas isoladas e desconectadas e a
perda de eficiência, com um mapa. A eficiência usa amostra de origens com semente fixa:
no feed real cada Dijkstra leva cerca de 0,14 s e a simulação roda dois por origem.
Segue o contrato `render(rede)` da P0-UI.

estado: implementado
"""

from __future__ import annotations

from collections.abc import MutableMapping
from html import escape
from time import perf_counter

import folium
import streamlit as st
from streamlit_folium import st_folium

from transporte.interface.mapa import atualizar_controle_camadas, criar_mapa
from transporte.interface.protocolos import RedeUI
from transporte.modelo.construtores import construir_gp
from transporte.modelo.visoes import VIAGEM, VisaoGP
from transporte.simulacao.falhas import (
    Falha,
    ResultadoFalha,
    Trecho,
    indexar_linhas,
    simular_falha,
)

TITULO = "Falhas"
CHAVE_GP = "f-res-gp"
CHAVE_RESULTADO = "f-res-resultado"
SEMENTE = 2026
AMOSTRA_PADRAO = 30
PARADA = "parada"
TRECHO = "trecho"
LINHA = "linha"
TIPOS = {PARADA: "Parada", TRECHO: "Trecho", LINHA: "Linha"}
COR_REMOVIDO = "#000000"
COR_ISOLADA = "#d62728"
COR_DESCONECTADA = "#ff7f0e"


def preparar(
    rede: RedeUI, cache: MutableMapping
) -> tuple[VisaoGP, dict[Trecho, set[str]], dict[str, list[str]]]:
    """G_P, o índice trecho -> linhas e o mapa parada -> próximas paradas de ônibus.

    Construídos uma vez por rede e guardados em `cache` (o `st.session_state`) com
    `id(rede)`, que descarta o que foi montado para uma rede anterior.
    Complexidade: O(1) com tudo pronto; a primeira vez custa `construir_gp` mais O(K + E).
    """
    guardado = cache.get(CHAVE_GP)
    if guardado is None or guardado[0] != id(rede):
        visao = construir_gp(rede)
        guardado = (id(rede), visao, indexar_linhas(rede), seguintes(visao))
        cache[CHAVE_GP] = guardado
    return guardado[1], guardado[2], guardado[3]


def seguintes(visao: VisaoGP) -> dict[str, list[str]]:
    """Parada -> paradas alcançáveis por uma aresta de viagem, em ordem. O(E log E)."""
    g = visao.grafo
    nomes = visao.parada_do_vertice
    saida: dict[str, set[str]] = {}
    for a in range(g.num_arestas()):
        u, v, _peso, tipo = g.aresta(a)
        if tipo == VIAGEM:
            saida.setdefault(nomes[u], set()).add(nomes[v])
    return {p: sorted(destinos) for p, destinos in saida.items()}


def linhas_com_trecho(rede: RedeUI, indice: dict[Trecho, set[str]]) -> list[str]:
    """Ids das linhas que têm ao menos um trecho em G_P, na ordem do nome. O(K + L log L)."""
    ids = set().union(*indice.values()) if indice else set()
    return sorted(ids, key=lambda i: (_nome_linha(rede, i), i))


def _nome_parada(rede: RedeUI, parada_id: str) -> str:
    parada = rede.paradas.get(parada_id)
    nome = getattr(parada, "nome", "") if parada is not None else ""
    return f"{nome or parada_id} ({parada_id})"


def _nome_linha(rede: RedeUI, linha_id: str) -> str:
    linha = getattr(rede, "linhas", {}).get(linha_id)
    nome = getattr(linha, "nome", "") if linha is not None else ""
    return f"{nome} ({linha_id})" if nome else linha_id


def descrever(rede: RedeUI, falha: Falha) -> str:
    """Texto curto da falha, para a legenda do resultado. O(tamanho da falha)."""
    partes = [f"parada {_nome_parada(rede, p)}" for p in falha.paradas]
    partes += [
        f"trecho {_nome_parada(rede, a)} → {_nome_parada(rede, b)}" for a, b in falha.trechos
    ]
    partes += [f"linha {_nome_linha(rede, linha)}" for linha in falha.linhas]
    return ", ".join(partes) or "nenhuma"


def resumo(resultado: ResultadoFalha) -> dict[str, object]:
    """Números do antes e depois mostrados nos cartões da página. O(C), C = componentes."""

    def maior(componentes: list[list[int]]) -> int:
        return max((len(c) for c in componentes), default=0)

    return {
        "componentes_antes": len(resultado.componentes_antes),
        "componentes_depois": len(resultado.componentes_depois),
        "maior_antes": maior(resultado.componentes_antes),
        "maior_depois": maior(resultado.componentes_depois),
        "isoladas": len(resultado.paradas_isoladas),
        "desconectadas": len(resultado.paradas_desconectadas),
        "perda": resultado.perda_eficiencia,
    }


def tabela_afetadas(rede: RedeUI, resultado: ResultadoFalha) -> list[dict[str, str]]:
    """Paradas desconectadas pela falha, marcando quais ficaram isoladas. O(D log D)."""
    isoladas = set(resultado.paradas_isoladas)
    afetadas = sorted(set(resultado.paradas_desconectadas) | isoladas)
    return [
        {
            "Parada": _nome_parada(rede, p),
            "Situação": "isolada" if p in isoladas else "fora da rede principal",
        }
        for p in afetadas
    ]


def _marcar(camada: folium.FeatureGroup, rede: RedeUI, parada_id: str, cor: str,
            texto: str) -> None:
    parada = rede.paradas[parada_id]
    folium.CircleMarker(
        (float(parada.lat), float(parada.lon)),
        radius=7,
        color=cor,
        fill=True,
        fill_opacity=0.9,
        tooltip=escape(f"{texto}: {_nome_parada(rede, parada_id)}"),
    ).add_to(camada)


def mapa_falha(rede: RedeUI, visao: VisaoGP, resultado: ResultadoFalha) -> folium.Map:
    """Mapa com o que a falha removeu e as paradas que ela isolou ou desconectou.

    Usa o mapa base da P0-UI sem a camada de todas as paradas (pesa no feed real) e
    acrescenta três camadas: removidos (preto), isoladas (vermelho) e desconectadas
    (laranja). Complexidade: O(R + D), R = itens removidos, D = paradas afetadas.
    """
    mapa = criar_mapa(rede, mostrar_paradas=False)
    nomes = visao.parada_do_vertice
    removidos = folium.FeatureGroup(name="Removido pela falha")
    for v in resultado.vertices_desativados:
        _marcar(removidos, rede, nomes[v], COR_REMOVIDO, "Removida")
    for a in resultado.arestas_desativadas:
        u, v, _peso, _tipo = visao.grafo.aresta(a)
        pontos = [
            (float(rede.paradas[nomes[x]].lat), float(rede.paradas[nomes[x]].lon))
            for x in (u, v)
        ]
        folium.PolyLine(
            pontos,
            color=COR_REMOVIDO,
            weight=4,
            dash_array="6 6",
            tooltip=escape(
                f"Trecho removido: {_nome_parada(rede, nomes[u])} → "
                f"{_nome_parada(rede, nomes[v])}"
            ),
        ).add_to(removidos)
    removidos.add_to(mapa)

    isoladas = set(resultado.paradas_isoladas)
    camada_isoladas = folium.FeatureGroup(name="Isoladas")
    camada_desconectadas = folium.FeatureGroup(name="Fora da rede principal")
    for p in sorted(set(resultado.paradas_desconectadas) | isoladas):
        if p in isoladas:
            _marcar(camada_isoladas, rede, p, COR_ISOLADA, "Isolada")
        else:
            _marcar(camada_desconectadas, rede, p, COR_DESCONECTADA, "Fora da rede principal")
    camada_isoladas.add_to(mapa)
    camada_desconectadas.add_to(mapa)
    atualizar_controle_camadas(mapa)
    return mapa


def simular(
    visao: VisaoGP,
    falha: Falha,
    indice: dict[Trecho, set[str]],
    amostra: int | None = AMOSTRA_PADRAO,
) -> tuple[ResultadoFalha, float]:
    """Roda `simular_falha` com a semente da página e devolve o resultado e os segundos.

    Complexidade: a de `simular_falha`, O(s (V + E) log V) com s origens.
    """
    inicio = perf_counter()
    resultado = simular_falha(visao, falha, indice, amostra=amostra, semente=SEMENTE)
    return resultado, perf_counter() - inicio


def _escolher_falha(rede: RedeUI, visao: VisaoGP, indice: dict[Trecho, set[str]],
                    proximas: dict[str, list[str]]) -> Falha | None:
    """Widgets de escolha da falha; devolve None enquanto a escolha está incompleta."""
    tipo = st.radio("O que sai de operação", list(TIPOS), format_func=TIPOS.__getitem__,
                    horizontal=True)
    paradas = list(visao.parada_do_vertice)
    if tipo == PARADA:
        escolhidas = st.multiselect(
            "Paradas", paradas, format_func=lambda p: _nome_parada(rede, p),
            help="A parada sai com todas as ligações dela: ônibus e caminhada.",
        )
        return Falha(paradas=tuple(escolhidas)) if escolhidas else None
    if tipo == TRECHO:
        origens = [p for p in paradas if p in proximas]
        if not origens:
            st.info("A rede não tem trechos de ônibus.")
            return None
        a = st.selectbox("Parada de origem do trecho", origens,
                         format_func=lambda p: _nome_parada(rede, p))
        b = st.selectbox("Próxima parada", proximas[a],
                         format_func=lambda p: _nome_parada(rede, p),
                         help="Sai só o sentido origem → próxima; a caminhada continua.")
        return Falha(trechos=((a, b),))
    linhas = linhas_com_trecho(rede, indice)
    escolhidas = st.multiselect(
        "Linhas", linhas, format_func=lambda i: _nome_linha(rede, i),
        help="Saem só os trechos que nenhuma outra linha percorre; as paradas continuam.",
    )
    return Falha(linhas=tuple(escolhidas)) if escolhidas else None


def render(rede: RedeUI) -> None:
    """Página Falhas (contrato da P0-UI)."""
    st.title(TITULO)
    st.caption(
        "Simula a saída de operação de paradas, de um trecho ou de linhas em G_P (parada → "
        "próxima parada de ônibus e caminhada de até 300 m) e compara a rede antes e depois: "
        "quem perde a ida e a volta para o resto da rede e quanto a rede fica mais lenta."
    )
    if not rede.paradas:
        st.info("A rede carregada não tem paradas.")
        return
    with st.spinner("Montando G_P..."):
        visao, indice, proximas = preparar(rede, st.session_state)
    n = visao.grafo.num_vertices()

    falha = _escolher_falha(rede, visao, indice, proximas)
    amostra = st.slider(
        "Eficiência: origens sorteadas",
        min_value=1,
        max_value=max(1, min(n, 200)),
        value=min(AMOSTRA_PADRAO, n),
        help=(
            "A eficiência roda um Dijkstra por origem, antes e depois da falha. No feed real "
            "cada um leva cerca de 0,14 s. As mesmas origens (semente fixa) valem nos dois."
        ),
    )
    if st.button("Simular falha", type="primary", disabled=falha is None):
        with st.spinner("Simulando: componentes e eficiência antes e depois..."):
            resultado, segundos = simular(visao, falha, indice, amostra)
        # O resultado fica na sessão para sobreviver aos reruns do Streamlit; a chave
        # id(rede) descarta o de uma rede carregada antes.
        st.session_state[CHAVE_RESULTADO] = (id(rede), resultado, segundos)
    guardado = st.session_state.get(CHAVE_RESULTADO)
    if guardado is None or guardado[0] != id(rede):
        st.info("Escolha o que sai de operação e clique em Simular falha.")
        return
    resultado, segundos = guardado[1], guardado[2]
    numeros = resumo(resultado)

    st.subheader("Resultado")
    st.caption(f"Falha: {descrever(rede, resultado.falha)}.")
    linha1 = st.columns(3)
    linha1[0].metric(
        "Componentes fortemente conexas",
        numeros["componentes_depois"],
        delta=numeros["componentes_depois"] - numeros["componentes_antes"],
        delta_color="inverse",
    )
    linha1[1].metric(
        "Maior componente (paradas)",
        numeros["maior_depois"],
        delta=numeros["maior_depois"] - numeros["maior_antes"],
    )
    linha1[2].metric("Perda de eficiência", f"{numeros['perda']:.4%}")
    linha2 = st.columns(3)
    linha2[0].metric("Paradas isoladas", numeros["isoladas"])
    linha2[1].metric("Fora da rede principal", numeros["desconectadas"])
    linha2[2].metric("Tempo da simulação", f"{segundos:.1f} s")
    origens = "todas as paradas" if resultado.amostra is None else (
        f"{resultado.amostra} origens sorteadas (semente {SEMENTE})"
    )
    st.caption(
        f"Eficiência global: {resultado.eficiencia_antes:.4e} → "
        f"{resultado.eficiencia_depois:.4e} s⁻¹, com {origens} e o mesmo denominador antes e "
        "depois. Isolada: ficou sozinha na sua componente. Fora da rede principal: saiu da "
        "maior componente."
    )
    afetadas = tabela_afetadas(rede, resultado)
    if afetadas:
        st.dataframe(afetadas, hide_index=True, width="stretch")
    else:
        st.success("Nenhuma parada perdeu a ida e a volta para a rede principal.")
    st.subheader("Mapa")
    st.caption(
        "Preto: o que a falha removeu (trechos tracejados). Vermelho: paradas isoladas. "
        "Laranja: paradas fora da rede principal."
    )
    st_folium(
        mapa_falha(rede, visao, resultado),
        height=550,
        use_container_width=True,
        key="mapa-falhas",
        returned_objects=[],
    )
