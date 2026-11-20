"""Página Desempenho (RF-AVA-05, F-AVAL-OPC), contrato render(rede) de P0-UI.

A página não mede nada: só lê os JSON que os scripts de `benchmarks/` gravaram em
`benchmarks/resultados/` e os mostra. Medir dentro da interface misturaria o tempo do
algoritmo com o do Streamlit e travaria a página por minutos; os números exibidos são
exatamente os do relatório, com o comando que os gerou.

Lê o JSON mais recente (pelo nome, que termina na data) de cada prefixo:
    comparacao-networkx-*.json  (benchmarks/comparar_networkx.py, RF-AVA-03)
    complexidade-*.json         (benchmarks/complexidade_empirica.py, RF-AVA-04)
e lista os demais JSON da pasta para consulta. Arquivo ausente ou inválido vira aviso,
nunca erro.

estado: implementado
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import streamlit as st

TITULO = "Desempenho"
DIRETORIO_PADRAO = Path(__file__).resolve().parents[4] / "benchmarks" / "resultados"
PREFIXO_COMPARACAO = "comparacao-networkx-"
PREFIXO_COMPLEXIDADE = "complexidade-"


def _ler(caminho: Path) -> dict | None:
    """Conteúdo do JSON, ou None se não abrir ou não for um objeto. O(tamanho do arquivo)."""
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dados if isinstance(dados, dict) else None


def ultimo_json(diretorio: Path, prefixo: str) -> tuple[Path, dict] | None:
    """O JSON válido mais recente com o prefixo (ordem do nome, que termina em AAAA-MM-DD).

    Saída: (caminho, conteúdo) ou None se a pasta não existe ou nenhum arquivo é válido.
    Complexidade: O(F log F + tamanho dos arquivos lidos), F = arquivos com o prefixo.
    """
    if not diretorio.is_dir():
        return None
    for caminho in sorted(diretorio.glob(f"{prefixo}*.json"), reverse=True):
        dados = _ler(caminho)
        if dados is not None:
            return caminho, dados
    return None


def tabela_comparacao(dados: dict) -> list[dict]:
    """Uma linha por (grafo, algoritmo) do JSON de comparar_networkx. O(linhas)."""
    linhas = []
    for bloco in dados.get("grafos", []):
        for alg in bloco.get("algoritmos", []):
            razao = alg.get("razao_nosso_sobre_networkx")
            linhas.append({
                "Grafo": bloco.get("grafo"),
                "V": bloco.get("V"),
                "E": bloco.get("E"),
                "Algoritmo": alg.get("algoritmo"),
                "Escopo": alg.get("escopo"),
                "Nosso": alg.get("nosso"),
                "NetworkX": alg.get("networkx"),
                "Nosso / NetworkX": round(razao, 2) if isinstance(razao, int | float) else None,
                "Resultados iguais": "sim" if alg.get("resultados_iguais") else "não",
            })
    return linhas


def tabela_inclinacoes(dados: dict) -> list[dict]:
    """Inclinação medida x teórica por algoritmo, do JSON de complexidade_empirica. O(A)."""
    linhas = []
    for alg in dados.get("algoritmos", []):
        medida = alg.get("inclinacao_medida")
        r2 = alg.get("r2")
        linhas.append({
            "Algoritmo": alg.get("algoritmo"),
            "Complexidade teórica": alg.get("complexidade_teorica"),
            "Inclinação teórica": alg.get("inclinacao_teorica"),
            "Inclinação medida": round(medida, 2) if medida is not None else None,
            "R²": round(r2, 3) if r2 is not None else None,
            "Tamanhos": len(alg.get("pontos", [])),
        })
    return linhas


def pontos_loglog(dados: dict) -> list[dict]:
    """Pontos (log10(V + E), log10(tempo)) em formato longo, um por algoritmo e tamanho.

    Pontos com tempo ou tamanho não positivo ficam fora (não têm logaritmo). O(pontos).
    """
    pontos = []
    for alg in dados.get("algoritmos", []):
        for p in alg.get("pontos", []):
            x, t = p.get("V_mais_E"), p.get("media_s")
            if isinstance(x, int | float) and isinstance(t, int | float) and x > 0 and t > 0:
                pontos.append({
                    "log10(V + E)": math.log10(x),
                    "log10(tempo em s)": math.log10(t),
                    "Algoritmo": alg.get("algoritmo"),
                })
    return pontos


def _origem(caminho: Path, dados: dict) -> None:
    maquina = dados.get("maquina", {})
    st.caption(
        f"Arquivo: {caminho.name} · comando: `{dados.get('comando', '?')}` · "
        f"máquina: {maquina.get('processador', '?')}, Python {maquina.get('python', '?')}"
    )


def render(rede: object = None, diretorio: Path | None = None) -> None:
    """Mostra as tabelas e o gráfico dos JSON de benchmarks/resultados/.

    Entradas: rede (não usada; a página segue o contrato render(rede)) e a pasta dos
        resultados (None usa benchmarks/resultados/ do repositório).
    Casos de borda: pasta ausente, JSON ausente ou inválido viram aviso.
    Complexidade: O(tamanho dos JSON lidos).
    """
    del rede
    diretorio = diretorio or DIRETORIO_PADRAO
    st.title(TITULO)
    st.caption(
        "Tempos medidos fora da interface pelos scripts de benchmarks/, com a função medir "
        "(média ± desvio de N execuções). Tempo de parede só é comparável na mesma máquina."
    )

    st.subheader("Comparação com o NetworkX (RF-AVA-03)")
    comparacao = ultimo_json(diretorio, PREFIXO_COMPARACAO)
    if comparacao is None:
        st.info(
            "Nenhum resultado de comparação encontrado. Rode "
            "`python benchmarks/comparar_networkx.py --feed dados/brutos/bhtrans.zip`."
        )
    else:
        caminho, dados = comparacao
        _origem(caminho, dados)
        st.dataframe(tabela_comparacao(dados), hide_index=True, width="stretch")
        if dados.get("todos_iguais"):
            st.success("Todos os resultados coincidem com os do NetworkX.")
        else:
            st.warning("Há resultados diferentes dos do NetworkX; veja a coluna da tabela.")

    st.subheader("Complexidade empírica (RF-AVA-04)")
    complexidade = ultimo_json(diretorio, PREFIXO_COMPLEXIDADE)
    if complexidade is None:
        st.info(
            "Nenhum resultado de complexidade encontrado. Rode "
            "`python benchmarks/complexidade_empirica.py`."
        )
    else:
        caminho, dados = complexidade
        _origem(caminho, dados)
        st.dataframe(tabela_inclinacoes(dados), hide_index=True, width="stretch")
        pontos = pontos_loglog(dados)
        if pontos:
            st.line_chart(
                pontos, x="log10(V + E)", y="log10(tempo em s)", color="Algoritmo"
            )
            st.caption(
                "Em log-log, t ~ (V + E)^b vira uma reta de inclinação b: b = 1 é linear, "
                "b = 2 é quadrático. Redes sintéticas em grade (RF-DAD-05)."
            )

    st.subheader("Outras medições")
    outros = (
        sorted(
            p for p in diretorio.glob("*.json")
            if not p.name.startswith((PREFIXO_COMPARACAO, PREFIXO_COMPLEXIDADE))
        )
        if diretorio.is_dir() else []
    )
    if not outros:
        st.info("Nenhum outro JSON em benchmarks/resultados/.")
        return
    escolhido = st.selectbox("Arquivo", outros, format_func=lambda p: p.name)
    dados = _ler(escolhido)
    if dados is None:
        st.warning(f"{escolhido.name} não é um JSON válido.")
    else:
        st.json(dados, expanded=1)
