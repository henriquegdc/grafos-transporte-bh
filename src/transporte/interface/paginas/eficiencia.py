"""Página de eficiência global e duração média de viagens. estado: implementado."""

from __future__ import annotations

import streamlit as st

from transporte.algoritmos.eficiencia import (
    Estimativa,
    comparar_faixas,
    estimar_eficiencia_global,
    indices_desvio,
    medias_por_quadrante,
    tempo_medio_viagem,
)
from transporte.algoritmos.isocronas import isocrona
from transporte.interface.protocolos import RedeUI
from transporte.modelo.construtores import construir_ge, construir_gp
from transporte.modelo.parametros import Parametros
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos

_CHAVE_VISOES = "visoes-f-efi"
_CHAVE_RESULTADOS = "resultados-f-efi"
_SEMENTE_PADRAO = 2026


def _formatar_erro(estimativa: Estimativa, unidade: str) -> str:
    if estimativa.erro_padrao is None:
        erro = "não estimável com menos de duas observações"
    else:
        erro = f"erro padrão ± {estimativa.erro_padrao:.6g} {unidade}"
    return (
        f"Amostra: {estimativa.tamanho_amostra}; população: {estimativa.tamanho_populacao}; {erro}."
    )


def _formatar_tempo(segundos: float | None) -> str:
    if segundos is None:
        return "Sem par alcançável na amostra"
    return f"{segundos / 60:.2f} min ({segundos:.1f} s)"


def _obter_visoes(rede: RedeUI):
    cache = st.session_state.get(_CHAVE_VISOES)
    if cache is not None and cache[0] is rede:
        return cache[1], cache[2], cache[3]

    parametros = Parametros()
    faixa = parametros.faixas[0].nome
    gp = construir_gp(rede, parametros)
    esperas = calcular_esperas(estimar_intervalos(rede, parametros))
    ge = construir_ge(rede, faixa, parametros, esperas=esperas)
    st.session_state[_CHAVE_VISOES] = (rede, gp, ge, faixa)
    return gp, ge, faixa


def _mostrar_resultados(
    eficiencia: Estimativa,
    tempo: Estimativa,
    faixa: str,
) -> None:
    colunas = st.columns(2)
    valor_eficiencia = "—" if eficiencia.valor is None else f"{eficiencia.valor:.6g} 1/s"
    colunas[0].metric("Eficiência global (G_P)", valor_eficiencia)
    colunas[0].caption(_formatar_erro(eficiencia, "1/s"))
    colunas[1].metric("Tempo médio de viagem (G_E)", _formatar_tempo(tempo.valor))
    colunas[1].caption(
        _formatar_erro(tempo, "s") + f" Pares alcançáveis: {tempo.pares_alcancaveis}."
    )
    st.caption(
        "G_P mede eficiência estrutural com tempos medianos de viagem e caminhada. "
        f"G_E usa a faixa {faixa} e o custo total da F-ROTA (caminhada, espera e ônibus). "
        "As esperas são estimadas pela F-ESPERA."
    )


def render(rede: RedeUI) -> None:
    """Renderiza RF-EFI-01 e RF-EFI-02 pela interface `render(rede)`.

    Args:
        rede: rede normalizada compartilhada com as páginas da interface.
    Returns:
        None; apresenta controles, estimativas e eventuais mensagens no Streamlit.
    Casos de borda:
        Com menos de duas paradas, informa que não há pares OD e encerra sem calcular.
        Erros de chave ou valores inválidos durante a construção/cálculo são mostrados
        na página sem descartar a rede da sessão.
    Complexidade:
        As visões são construídas uma vez por identidade da rede na sessão. O custo
        dominante dos cálculos é O(V_P + s(V_P + E_P)log V_P + V_E +
        k(V_E + E_E)log V_E + m), para s origens, k origens distintas e m pares
        amostrados; o cache armazena as duas visões e resultados na sessão.

    Os grafos são guardados no estado da sessão junto da rede daquela sessão; assim,
    reruns da página reutilizam a construção sem compartilhar uma visão mutável entre
    sessões. As métricas só rodam após o envio do formulário.
    """
    st.header("Eficiência da rede")
    st.caption("Os cálculos podem levar algum tempo, especialmente com amostras maiores.")
    quantidade_paradas = len(rede.paradas)
    quantidade_pares = quantidade_paradas * max(0, quantidade_paradas - 1)
    if quantidade_paradas == 0:
        st.info("A rede precisa ter ao menos duas paradas para métricas entre pares.")
        return

    modo = st.radio(
        "Análise de eficiência",
        [
            "Métricas da rede",
            "Isócronas",
            "Índice de desvio",
            "Comparar faixas",
        ],
        horizontal=True,
    )
    if quantidade_paradas < 2 and modo != "Isócronas":
        st.info("A rede precisa ter ao menos duas paradas para calcular as métricas.")
        return
    if modo != "Métricas da rede":
        _mostrar_extensao(rede, modo, quantidade_pares)
        return

    with st.form("form-f-efi"):
        colunas = st.columns(2)
        amostra_origens = colunas[0].number_input(
            "Origens para eficiência global",
            min_value=1,
            max_value=quantidade_paradas,
            value=min(100, quantidade_paradas),
            step=1,
        )
        amostra_pares = colunas[1].number_input(
            "Pares OD para tempo médio",
            min_value=1,
            max_value=quantidade_pares,
            value=min(100, quantidade_pares),
            step=1,
        )
        semente = st.number_input(
            "Semente da amostragem",
            min_value=0,
            value=_SEMENTE_PADRAO,
            step=1,
        )
        calcular = st.form_submit_button("Calcular métricas", type="primary")

    cache_resultados = st.session_state.get(_CHAVE_RESULTADOS)
    parametros_amostra = (amostra_origens, amostra_pares, semente)
    cache_valido = (
        cache_resultados is not None
        and cache_resultados[0] is rede
        and cache_resultados[1] == parametros_amostra
    )
    if not calcular and not cache_valido:
        st.info("Configure as amostras e selecione “Calcular métricas”.")
        return
    if cache_valido and not calcular:
        _, _, eficiencia, tempo, faixa = cache_resultados
        _mostrar_resultados(eficiencia, tempo, faixa)
        return

    try:
        with st.spinner("Construindo as visões e calculando as métricas..."):
            gp, ge, faixa = _obter_visoes(rede)
            eficiencia = estimar_eficiencia_global(
                gp.grafo,
                tamanho_amostra=amostra_origens,
                semente=semente,
            )
            tempo = tempo_medio_viagem(
                ge,
                tamanho_amostra=amostra_pares,
                semente=semente,
            )
    except (KeyError, ValueError) as erro:
        st.error(f"Não foi possível calcular as métricas: {erro}")
        return

    st.session_state[_CHAVE_RESULTADOS] = (
        rede,
        parametros_amostra,
        eficiencia,
        tempo,
        faixa,
    )
    _mostrar_resultados(eficiencia, tempo, faixa)


_FAIXAS_MAPA = [
    (15, "#2c7bb6", "Até 15 min"),
    (30, "#31a354", "15–30 min"),
    (45, "#e68a00", "30–45 min"),
    (60, "#a83255", "45–60 min"),
]


def _mostrar_alcance(rede, tempos):
    pontos = []
    contagens = {rotulo: 0 for _, _, rotulo in _FAIXAS_MAPA}
    for parada, segundos in tempos.items():
        p = rede.paradas[parada]
        _, cor, rotulo = next(b for b in _FAIXAS_MAPA if segundos <= b[0] * 60)
        pontos.append({"latitude": p.lat, "longitude": p.lon, "cor": cor})
        contagens[rotulo] += 1
    st.metric("Paradas alcançadas", len(tempos))
    if pontos:
        st.map(pontos, latitude="latitude", longitude="longitude", color="cor", size=35)
    st.caption(
        " · ".join(
            f":{cor}[●] {rotulo} ({contagens[rotulo]})"
            for (_, _, rotulo), cor in zip(_FAIXAS_MAPA, ["blue", "green", "orange", "red"])
        )
    )
    st.dataframe([{"Parada": p, "Tempo (min)": t / 60} for p, t in tempos.items()], hide_index=True)


def _mostrar_desvios(desvios):
    validos = sorted((p for p in desvios if p.desvio is not None), key=lambda p: -p.desvio)
    sem_caminho = sum(p.tempo_s is None for p in desvios)
    st.caption(
        f"{len(validos)} de {len(desvios)} pares com índice definido · "
        f"{sem_caminho} sem caminho · {len(desvios) - len(validos) - sem_caminho} "
        "com distância direta zero."
    )
    if not validos:
        return
    st.subheader("Pares com maior desvio")
    st.dataframe(
        [
            {
                "Origem": p.origem,
                "Destino": p.destino,
                "Desvio (km/km)": p.desvio,
                "Tempo (min/km direto)": p.min_por_km,
                "Percurso (km)": p.percorrida_m / 1000,
                "Direta (km)": p.direta_m / 1000,
            }
            for p in validos
        ],
        hide_index=True,
    )
    st.subheader("Desvio médio por quadrante de origem")
    st.caption("Norte/sul e leste/oeste são definidos pelo centro do retângulo das paradas.")
    st.dataframe(
        [
            {"Quadrante": q, "Desvio médio (km/km)": media}
            for q, media in medias_por_quadrante(desvios).items()
        ],
        hide_index=True,
    )


def _mostrar_extensao(rede, modo, max_pares):
    params = Parametros()
    with st.form("analise-" + modo):
        if modo != "Comparar faixas":
            faixa = st.selectbox("Faixa de serviço", [f.nome for f in params.faixas])
        if modo == "Isócronas":
            origem = st.selectbox(
                "Parada de origem",
                list(rede.paradas),
                format_func=lambda p: f"{rede.paradas[p].nome} ({p})",
            )
            minutos = st.slider("Limite (min)", min_value=0, max_value=60, value=60)
            entradas = (modo, faixa, origem, minutos)
        else:
            n = st.number_input(
                "Pares de paradas",
                min_value=1,
                max_value=max_pares,
                value=min(12, max_pares),
                step=1,
            )
            semente = st.number_input("Semente", min_value=0, value=_SEMENTE_PADRAO, step=1)
            entradas = (modo, n, semente, faixa if modo == "Índice de desvio" else None)
        executar = st.form_submit_button("Calcular " + modo.lower())
    chave = "resultado-extensao-eficiencia"
    if executar:
        st.session_state.pop(chave, None)
        try:
            with st.spinner("Calculando a análise…"):
                if modo == "Comparar faixas":
                    resultado = comparar_faixas(rede, n, semente, params)
                else:
                    esperas = calcular_esperas(estimar_intervalos(rede, params))
                    ge = construir_ge(rede, faixa, params, esperas=esperas)
                    if modo == "Isócronas":
                        resultado = isocrona(ge, origem, minutos * 60)
                    else:
                        resultado = indices_desvio(rede, ge, n, semente)
            st.session_state[chave] = (rede, entradas, resultado)
        except (KeyError, ValueError) as erro:
            st.error(str(erro))
    cache = st.session_state.get(chave)
    if cache is None or cache[0] is not rede or cache[1] != entradas:
        return
    resultado = cache[2]
    if modo == "Isócronas":
        _mostrar_alcance(rede, resultado)
    elif modo == "Índice de desvio":
        _mostrar_desvios(resultado)
    else:
        tabela = [
            {
                "Faixa": r.faixa,
                "Alcançáveis": r.alcancaveis,
                "Pares": r.pares,
                "Eficiência (1/s)": r.eficiencia_por_s,
                "Erro padrão (1/s)": r.erro_eficiencia_por_s,
                "Erro padrão (min)": r.erro_tempo_medio_s / 60
                if r.erro_tempo_medio_s is not None
                else None,
                "Tempo médio (min)": r.tempo_medio_s / 60 if r.tempo_medio_s is not None else None,
            }
            for r in resultado
        ]
        st.caption(
            "A mesma amostra ordenada de paradas é usada em todas as faixas. "
            "O tempo médio considera os pares alcançáveis. Na eficiência, os demais somam zero."
        )
        st.dataframe(tabela, hide_index=True)
        st.bar_chart(tabela, x="Faixa", y="Tempo médio (min)")
