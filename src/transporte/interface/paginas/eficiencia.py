"""Página de eficiência global e duração média de viagens. estado: implementado."""

from __future__ import annotations

import streamlit as st

from transporte.algoritmos.eficiencia import (
    Estimativa,
    estimar_eficiencia_global,
    tempo_medio_viagem,
)
from transporte.interface.protocolos import RedeUI
from transporte.modelo.construtores import construir_ge, construir_gp
from transporte.modelo.parametros import Parametros

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
    ge = construir_ge(rede, faixa, parametros)
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
        "A espera padrão de 300 s permanece até a integração da tabela da F-ESPERA."
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
    quantidade_paradas = len(rede.paradas)
    quantidade_pares = quantidade_paradas * max(0, quantidade_paradas - 1)
    if quantidade_paradas < 2:
        st.info("A rede precisa ter ao menos duas paradas para calcular as métricas.")
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
