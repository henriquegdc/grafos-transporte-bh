"""Página Falhas: falha única (F-RES), ranking (F-RES-2) e falhas múltiplas (F-RES-OPC).

Aba "Falha única", RF-RES-01 a RF-RES-03: escolhe a falha, roda `simular_falha` sobre G_P e
mostra as componentes fortemente conexas antes e depois, as paradas isoladas e
desconectadas e a perda de eficiência, com um mapa. Aba "Ranking", RF-RES-04: ordena as
paradas mais centrais e as linhas pela perda que causam. Aba "Falhas múltiplas", RF-RES-05:
falhas em sequência e remoção dirigida contra aleatória. A eficiência usa amostra de
origens com semente fixa: no feed real cada Dijkstra leva cerca de 0,14 s, então as abas
mostram o custo estimado antes de rodar e guardam os resultados na sessão.
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

from transporte.grafo.buscas import dijkstra
from transporte.interface.mapa import atualizar_controle_camadas, criar_mapa
from transporte.interface.protocolos import RedeUI
from transporte.modelo.construtores import construir_gp
from transporte.modelo.visoes import VIAGEM, VisaoGP
from transporte.simulacao.falhas import (
    Falha,
    ResultadoFalha,
    Trecho,
    candidatos_criticidade,
    indexar_linhas,
    ranking_criticidade,
    sequencia_aleatoria,
    sequencia_dirigida,
    simular_falha,
    simular_falhas,
)

TITULO = "Falhas"
CHAVE_GP = "f-res-gp"
CHAVE_RESULTADO = "f-res-resultado"
CHAVE_DIJKSTRA = "f-res-dijkstra"
CHAVE_RANKING = "f-res-2-ranking"
CHAVE_MULTIPLAS = "f-res-opc-multiplas"
SEMENTE = 2026
AMOSTRA_PADRAO = 30
RANKING_PARADAS = 10
RANKING_LINHAS = 10
RANKING_AMOSTRA = 20
AMOSTRA_INTERMEDIACAO = 50
COMPARACAO_K = 5
MODO_ESCOLHA = "Escolher falhas"
MODO_COMPARACAO = "Dirigida x aleatória"
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


def segundos_por_dijkstra(rede: RedeUI, visao: VisaoGP, cache: MutableMapping) -> float:
    """Tempo de um Dijkstra em G_P medido nesta rede, para estimar o custo antes de rodar.

    Mede uma vez por rede (a partir do vértice 0) e guarda em `cache` com `id(rede)`.
    Complexidade: O((V + E) log V) na primeira vez, O(1) depois.
    """
    guardado = cache.get(CHAVE_DIJKSTRA)
    if guardado is None or guardado[0] != id(rede):
        inicio = perf_counter()
        if visao.grafo.num_vertices():
            dijkstra(visao.grafo, 0)
        guardado = (id(rede), max(perf_counter() - inicio, 1e-6))
        cache[CHAVE_DIJKSTRA] = guardado
    return guardado[1]


def dijkstras_ranking(n_candidatos: int, amostra: int, amostra_intermediacao: int,
                      n_paradas: int) -> int:
    """Dijkstras do ranking: a intermediação (se há paradas) e c + 1 eficiências. O(1)."""
    brandes = amostra_intermediacao if n_paradas else 0
    return brandes + (n_candidatos + 1) * amostra if n_candidatos else 0


def tabela_ranking(rede: RedeUI, resultados: list[ResultadoFalha]) -> list[dict[str, object]]:
    """Linhas da tabela do ranking, na ordem recebida. O(c)."""
    linhas = []
    for posicao, r in enumerate(resultados, start=1):
        if r.falha.paradas:
            tipo, alvo = "Parada", _nome_parada(rede, r.falha.paradas[0])
        elif r.falha.linhas:
            tipo, alvo = "Linha", _nome_linha(rede, r.falha.linhas[0])
        else:
            tipo, alvo = "Outra", descrever(rede, r.falha)
        linhas.append({
            "Posição": posicao,
            "Tipo": tipo,
            "Sai de operação": alvo,
            "Perda de eficiência": f"{r.perda_eficiencia:.4%}",
            "Fora da rede principal": len(r.paradas_desconectadas),
            "Isoladas": len(r.paradas_isoladas),
        })
    return linhas


def curva_eficiencia(passos: list[ResultadoFalha]) -> list[float]:
    """Eficiência relativa (depois / antes) com 0, 1, ..., k falhas; começa em 1.0. O(k)."""
    return [1.0] + [1.0 - p.perda_eficiencia for p in passos]


def tabela_passos(rede: RedeUI, passos: list[ResultadoFalha]) -> list[dict[str, object]]:
    """Uma linha por passo da sequência, com as medidas acumuladas. O(k)."""
    return [
        {
            "Falhas": k,
            "Saiu agora": descrever(rede, p.falha),
            "Componentes": len(p.componentes_depois),
            "Isoladas": len(p.paradas_isoladas),
            "Fora da rede principal": len(p.paradas_desconectadas),
            "Perda de eficiência": f"{p.perda_eficiencia:.4%}",
        }
        for k, p in enumerate(passos, start=1)
    ]


def _guardado(chave: str, rede: RedeUI) -> dict:
    """Dicionário de resultados da sessão para a rede atual (parâmetros -> resultado)."""
    guardado = st.session_state.get(chave)
    if guardado is None or guardado[0] != id(rede):
        guardado = (id(rede), {})
        st.session_state[chave] = guardado
    return guardado[1]


def _estimativa(dijkstras: int, segundos: float) -> None:
    st.caption(
        f"Custo estimado: {dijkstras} Dijkstras, cerca de {dijkstras * segundos:.1f} s "
        f"({segundos * 1000:.1f} ms por Dijkstra, medido nesta rede). Resultados ficam "
        "guardados na sessão: repetir os mesmos parâmetros não recalcula."
    )


def _aba_ranking(rede: RedeUI, visao: VisaoGP, indice: dict[Trecho, set[str]]) -> None:
    """Aba Ranking (F-RES-2, RF-RES-04)."""
    n = visao.grafo.num_vertices()
    linhas = linhas_com_trecho(rede, indice)
    st.caption(
        "Simula, uma de cada vez, a falha das paradas de maior intermediação (F-MET) e das "
        "linhas, todas com as mesmas origens sorteadas, e ordena pela perda de eficiência."
    )
    colunas = st.columns(2)
    n_paradas = colunas[0].slider("Paradas candidatas (maior intermediação)", 0,
                                  max(1, min(n, 50)), min(RANKING_PARADAS, n))
    n_linhas = colunas[1].slider("Linhas candidatas (sorteadas)", 0, max(1, len(linhas)),
                                 min(RANKING_LINHAS, len(linhas)))
    colunas = st.columns(2)
    amostra = colunas[0].slider("Eficiência: origens sorteadas", 1, max(1, min(n, 200)),
                                min(RANKING_AMOSTRA, n), key="ranking-amostra")
    amostra_int = colunas[1].slider("Intermediação: origens sorteadas", 1,
                                    max(1, min(n, 500)), min(AMOSTRA_INTERMEDIACAO, n),
                                    key="ranking-amostra-int")
    total = n_paradas + n_linhas
    _estimativa(dijkstras_ranking(total, amostra, amostra_int, n_paradas),
                segundos_por_dijkstra(rede, visao, st.session_state))
    resultados = _guardado(CHAVE_RANKING, rede)
    parametros = (n_paradas, n_linhas, amostra, amostra_int)
    clicou = st.button("Calcular ranking", type="primary", disabled=total == 0)
    if clicou and parametros not in resultados:
        with st.spinner("Simulando cada candidato..."):
            inicio = perf_counter()
            candidatos = candidatos_criticidade(
                visao, n_paradas, indice, n_linhas, amostra_int, SEMENTE
            )
            ranking = ranking_criticidade(visao, candidatos, indice, amostra, SEMENTE)
            resultados[parametros] = (ranking, perf_counter() - inicio)
    if parametros not in resultados:
        st.info("Escolha os candidatos e clique em Calcular ranking.")
        return
    ranking, segundos = resultados[parametros]
    st.dataframe(tabela_ranking(rede, ranking), hide_index=True, width="stretch")
    st.caption(
        f"{len(ranking)} candidatos em {segundos:.1f} s; eficiência com {amostra} origens "
        f"(semente {SEMENTE}). Perdas amostradas de falhas que tiram paradas da rede "
        "principal variam com a amostra."
    )


def _aba_multiplas(rede: RedeUI, visao: VisaoGP, indice: dict[Trecho, set[str]]) -> None:
    """Aba Falhas múltiplas (F-RES-OPC, RF-RES-05)."""
    n = visao.grafo.num_vertices()
    st.caption(
        "Aplica as falhas uma depois da outra e mede a rede após cada uma (efeito "
        "acumulado), ou compara a remoção dirigida (maior intermediação primeiro) com a "
        "remoção aleatória."
    )
    modo = st.radio("Modo", [MODO_ESCOLHA, MODO_COMPARACAO], horizontal=True)
    amostra = st.slider("Eficiência: origens sorteadas", 1, max(1, min(n, 200)),
                        min(RANKING_AMOSTRA, n), key="multiplas-amostra")
    segundos = segundos_por_dijkstra(rede, visao, st.session_state)
    resultados = _guardado(CHAVE_MULTIPLAS, rede)
    if modo == MODO_ESCOLHA:
        paradas = st.multiselect(
            "Paradas, na ordem da falha", list(visao.parada_do_vertice),
            format_func=lambda p: _nome_parada(rede, p), key="multiplas-paradas",
        )
        linhas = st.multiselect(
            "Linhas, depois das paradas", linhas_com_trecho(rede, indice),
            format_func=lambda i: _nome_linha(rede, i), key="multiplas-linhas",
        )
        falhas = [Falha(paradas=(p,)) for p in paradas]
        falhas += [Falha(linhas=(linha,)) for linha in linhas]
        _estimativa((len(falhas) + 1) * amostra if falhas else 0, segundos)
        parametros = ("escolha", tuple(falhas), amostra)
        clicou = st.button("Simular sequência", type="primary", disabled=not falhas)
        if clicou and parametros not in resultados:
            with st.spinner("Simulando a sequência..."):
                resultados[parametros] = simular_falhas(visao, falhas, indice, amostra, SEMENTE)
        if parametros not in resultados:
            st.info("Escolha as paradas ou linhas e clique em Simular sequência.")
            return
        passos = resultados[parametros]
        st.line_chart(
            {"Falhas": list(range(len(passos) + 1)),
             "Eficiência relativa": curva_eficiencia(passos)},
            x="Falhas", y="Eficiência relativa",
        )
        st.dataframe(tabela_passos(rede, passos), hide_index=True, width="stretch")
        return

    colunas = st.columns(2)
    k = colunas[0].slider("Paradas removidas", 1, max(1, min(n, 30)), min(COMPARACAO_K, n))
    amostra_int = colunas[1].slider("Intermediação: origens sorteadas", 1,
                                    max(1, min(n, 500)), min(AMOSTRA_INTERMEDIACAO, n),
                                    key="multiplas-amostra-int")
    _estimativa(amostra_int + 2 * (k + 1) * amostra, segundos)
    parametros = ("comparacao", k, amostra, amostra_int)
    if st.button("Comparar remoções", type="primary") and parametros not in resultados:
        with st.spinner("Removendo paradas em sequência..."):
            dirigida = simular_falhas(
                visao, sequencia_dirigida(visao, k, amostra_int, SEMENTE), indice,
                amostra, SEMENTE,
            )
            aleatoria = simular_falhas(
                visao, sequencia_aleatoria(visao, k, SEMENTE), indice, amostra, SEMENTE
            )
            resultados[parametros] = (dirigida, aleatoria)
    if parametros not in resultados:
        st.info("Escolha quantas paradas remover e clique em Comparar remoções.")
        return
    dirigida, aleatoria = resultados[parametros]
    st.line_chart(
        {"Falhas": list(range(len(dirigida) + 1)),
         "Dirigida": curva_eficiencia(dirigida),
         "Aleatória": curva_eficiencia(aleatoria)},
        x="Falhas", y=["Dirigida", "Aleatória"],
    )
    st.caption(
        f"Eficiência depois / antes, com {amostra} origens (semente {SEMENTE}). Dirigida: "
        "paradas de maior intermediação primeiro, calculada uma vez na rede intacta. "
        f"Aleatória: paradas sorteadas com a semente {SEMENTE}."
    )


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
    unica, aba_ranking, multiplas = st.tabs(["Falha única", "Ranking", "Falhas múltiplas"])
    with unica:
        _aba_falha_unica(rede, visao, indice, proximas)
    with aba_ranking:
        _aba_ranking(rede, visao, indice)
    with multiplas:
        _aba_multiplas(rede, visao, indice)


def _aba_falha_unica(rede: RedeUI, visao: VisaoGP, indice: dict[Trecho, set[str]],
                     proximas: dict[str, list[str]]) -> None:
    """Aba Falha única (F-RES, RF-RES-01 a 03)."""
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
    if numeros["desconectadas"] and resultado.amostra is not None:
        st.warning(
            "A falha tirou paradas da rede principal: a perda amostrada varia muito com as "
            "origens sorteadas, porque salta quando uma dessas paradas cai na amostra. Use "
            "mais origens para um valor mais estável."
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
