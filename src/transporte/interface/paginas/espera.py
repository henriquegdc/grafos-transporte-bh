"""Página de F-ESPERA, conforme contrato render(rede) de P0-UI."""

from datetime import time

import streamlit as st

from transporte.algoritmos.chegada_mais_cedo import chegada_mais_cedo, monte_carlo
from transporte.dados.modelo import Rede
from transporte.interface.mapa import render_mapa
from transporte.modelo.horarios import construir_gt
from transporte.modelo.parametros import Parametros
from transporte.simulacao.espera import (
    calcular_esperas,
    estimar_intervalos,
    sensibilidade_intervalo,
    simular_trajeto,
)

TITULO = "Espera"
_RESULTADO = "espera-resultado"


def _mostrar_sensibilidade(rede):
    if not rede.linhas:
        st.info("A rede não contém linhas.")
        return
    with st.form("sensibilidade"):
        linha = st.selectbox(
            "Linha", sorted(rede.linhas), format_func=lambda i: f"{rede.linhas[i].nome} ({i})"
        )
        faixa = st.selectbox("Faixa horária", [f.nome for f in Parametros().faixas])
        fator = st.number_input("Multiplicador do intervalo", min_value=0.01, value=2.0)
        pares = st.number_input("Pares origem–destino", min_value=1, max_value=100, value=10)
        semente = st.number_input("Semente da amostra", value=42)
        executar = st.form_submit_button("Comparar cenários")
    if executar:
        st.session_state.pop("sensibilidade-resultado", None)
        try:
            r = sensibilidade_intervalo(rede, linha, faixa, fator, pares, semente)
        except ValueError as exc:
            st.info(str(exc))
            return
        st.session_state["sensibilidade-resultado"] = (rede, r)
    resultado = st.session_state.get("sensibilidade-resultado")
    if resultado and resultado[0] is rede:
        r = resultado[1]
        st.metric("Pares cujo tempo mudou", f"{r['mudaram']} de {len(r['pares'])}")
        st.caption("Origens sorteadas entre as paradas da linha; destinos em toda a rede.")
        st.caption("Espera H/2 dos padrões com intervalo estimável (minutos).")
        st.dataframe(
            [{"Padrão": p, "Antes": a / 60, "Depois": b / 60} for p, a, b in r["esperas"]],
            hide_index=True,
        )
        st.caption("Tempo total por par (minutos). Uma célula vazia indica destino inalcançável.")
        st.dataframe(
            [
                {
                    "Origem": o,
                    "Destino": d,
                    "Antes": a / 60 if a is not None else None,
                    "Depois": b / 60 if b is not None else None,
                }
                for o, d, a, b in r["pares"]
            ],
            hide_index=True,
        )


def _tabela_intervalos(rede, params, intervalos):
    """Linhas por padrão/faixa, incluindo ausência de serviço e fallback. O(PF + FN)."""
    esperas = calcular_esperas(intervalos)
    tabela = []
    for pid, padrao in rede.padroes.items():
        partidas = {h[0] for h in rede.viagens.get(pid, ()) if h}
        for faixa in params.faixas:
            n = sum(faixa.contem(t) for t in partidas)
            chave = (pid, faixa.nome)
            tabela.append(
                {
                    "Linha": rede.linhas[padrao.linha_id].nome,
                    "Padrão": pid,
                    "Faixa": faixa.nome,
                    "Partidas distintas": n,
                    "Intervalo (min)": intervalos[chave] / 60 if chave in intervalos else None,
                    "Espera (min)": esperas.get(chave, params.espera_padrao_s) / 60 if n else None,
                    "Estimativa": (
                        "H/2"
                        if chave in esperas
                        else "Provisória: uma partida"
                        if n
                        else "Sem serviço"
                    ),
                }
            )
    return tabela


def render(rede: Rede) -> None:
    """Exibe estimativas e simula trajeto usando a faixa da saída.

    Estimativa/tabela: O(PF + FN + N log N); simulação: estimativa + construção
    de G_E + Dijkstra. O mapa só recebe as paradas do trajeto para manter a leitura.
    """
    st.title(TITULO)
    if st.checkbox("Simular alteração do intervalo de uma linha"):
        _mostrar_sensibilidade(rede)
        return
    if not rede.paradas:
        st.info("A rede não contém paradas para simular um trajeto.")
        return

    params = Parametros()
    modo = st.radio("Modelo de espera", ["Estimativa H/2", "Quadro de horários"], horizontal=True)
    temporal = modo == "Quadro de horários"
    if temporal:
        st.caption("G_T consulta as partidas programadas no dia de serviço carregado.")
    else:
        st.caption("A espera média H/2 usa a faixa da saída durante todo o trajeto.")
        intervalos = estimar_intervalos(rede, params)
        st.subheader("Intervalos e esperas por linha e padrão")
        faixa = st.selectbox("Faixa da tabela", [f.nome for f in params.faixas])
        tabela = _tabela_intervalos(rede, params, intervalos)
        st.dataframe([r for r in tabela if r["Faixa"] == faixa], hide_index=True, width="stretch")
        st.caption(
            "Com uma partida distinta, a espera é provisória (5 min). "
            "Sem partidas, não há embarque nesse padrão."
        )
    ids = list(rede.paradas)

    def rotulo(pid):
        return f"{rede.paradas[pid].nome} ({pid})"

    with st.form("simular-espera"):
        origem = st.selectbox("Origem", ids, format_func=rotulo)
        destino = st.selectbox("Destino", ids, index=min(1, len(ids) - 1), format_func=rotulo)
        saida = st.time_input("Horário de saída", value=time(8, 0))
        if temporal:
            dias = st.number_input("Dias após o início do serviço (GTFS)", min_value=0, value=0)
            janela = st.number_input(
                "Janela Monte Carlo a partir da saída (min)", min_value=1, value=20
            )
            n = st.number_input("Amostras", min_value=1, max_value=1000, value=30)
            semente = st.number_input("Semente", value=42)
        executar = st.form_submit_button("Simular trajeto")
    if executar:
        st.session_state.pop(_RESULTADO, None)
        try:
            saida_s = saida.hour * 3600 + saida.minute * 60 + saida.second
            if temporal:
                saida_s += dias * 86400
            faixa_saida = next((f.nome for f in params.faixas if f.contem(saida_s)), None)
            with st.spinner("Calculando o trajeto…"):
                estimativa = None
                amostras = []
                if temporal:
                    cache = st.session_state.get("espera-gt")
                    if cache is None or cache[0] is not rede:
                        cache = (rede, construir_gt(rede, params))
                        st.session_state["espera-gt"] = cache
                    gt = cache[1]
                    trajeto = chegada_mais_cedo(gt, origem, destino, saida_s)
                    amostras = monte_carlo(
                        gt, origem, destino, saida_s, saida_s + janela * 60, n, semente
                    )
                    if faixa_saida:
                        estimativa = simular_trajeto(rede, origem, destino, saida_s, params)
                else:
                    trajeto = simular_trajeto(rede, origem, destino, saida_s, params)
            st.session_state[_RESULTADO] = (rede, modo, faixa_saida, trajeto, estimativa, amostras)
        except (KeyError, ValueError) as erro:
            st.error(str(erro))

    resultado = st.session_state.get(_RESULTADO)
    if resultado is None or resultado[0] is not rede or resultado[1] != modo:
        return
    _, _, faixa_saida, trajeto, estimativa, amostras = resultado
    if temporal:
        _mostrar_amostras(amostras)
        if estimativa:
            espera = estimativa.tempo_por_tipo()["espera"]
            st.caption(
                f"Estimativa H/2 para a saída consultada ({faixa_saida}): "
                f"{espera / 60:.2f} min de espera e {estimativa.tempo_total_s / 60:.2f} "
                "min de tempo total."
            )
        else:
            st.caption("Estimativa H/2 indisponível para o par e a faixa da saída.")
    if trajeto is None:
        st.warning("Não há trajeto entre as paradas para a saída selecionada.")
        return

    st.subheader("Resultado da simulação")
    st.caption(f"{modo} · Baldeações: {trajeto.baldeacoes}")
    parcelas = trajeto.tempo_por_tipo()
    colunas = st.columns(4)
    for coluna, (nome, segundos) in zip(
        colunas,
        (
            ("Total", trajeto.tempo_total_s),
            ("Caminhada", parcelas["caminhada"]),
            ("Espera", parcelas["espera"]),
            ("Viagem", parcelas["viagem"]),
        ),
        strict=True,
    ):
        coluna.metric(nome, f"{segundos / 60:.2f} min")

    linhas = []
    for trecho in trajeto.trechos:
        linha = rede.linhas[rede.padroes[trecho.padrao].linha_id].nome if trecho.padrao else "—"
        linhas.append(
            {
                "Trecho": trecho.tipo,
                "Linha": linha,
                "Paradas": " → ".join(trecho.paradas),
                "Tempo (min)": trecho.tempo_s / 60,
            }
        )
    if linhas:
        st.dataframe(linhas, hide_index=True, width="stretch")
    else:
        st.info("Origem e destino são a mesma parada; tempo total zero.")
    caminhos = tuple(t.paradas for t in trajeto.trechos) or ((trajeto.origem,),)
    paradas_usadas = {p for caminho in caminhos for p in caminho}
    # Projeção apenas para exibição: não recorta nem recalcula os dados da simulação.
    rede_mapa = Rede({p: rede.paradas[p] for p in paradas_usadas}, rede.linhas, rede.padroes, {})
    render_mapa(rede_mapa, trajeto=trajeto, chave="mapa-espera")


def _mostrar_amostras(amostras):
    dados = []
    for a in amostras:
        if a.total_s is not None:
            dados.extend(
                [
                    {"Parcela": "Total", "Minutos": a.total_s / 60},
                    {"Parcela": "Espera", "Minutos": a.espera_s / 60},
                ]
            )
    st.subheader("Distribuição das saídas sorteadas")
    st.caption(f"{len(dados) // 2} de {len(amostras)} saídas com trajeto.")
    if dados:
        st.vega_lite_chart(
            spec={
                "data": {"values": dados},
                "mark": "bar",
                "encoding": {
                    "x": {"field": "Minutos", "type": "quantitative", "bin": True},
                    "y": {"aggregate": "count", "title": "Saídas"},
                    "row": {"field": "Parcela", "type": "nominal", "title": None},
                },
            }
        )
