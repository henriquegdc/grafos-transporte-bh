"""Página Desempenho (RF-AVA-05, F-AVAL-OPC): lê os JSON de benchmarks/resultados/."""

from __future__ import annotations

import json
import math
from pathlib import Path

from streamlit.testing.v1 import AppTest

from transporte.interface import app
from transporte.interface.paginas.desempenho import (
    pontos_loglog,
    tabela_comparacao,
    tabela_inclinacoes,
    ultimo_json,
)

COMPARACAO = {
    "comando": "python benchmarks/comparar_networkx.py --lados 5",
    "maquina": {"processador": "cpu", "python": "3.12"},
    "todos_iguais": True,
    "grafos": [{
        "grafo": "G_P sintética 5x5", "V": 25, "E": 260,
        "algoritmos": [{
            "algoritmo": "BFS", "escopo": "5 origens", "nosso": "1 ms", "networkx": "2 ms",
            "razao_nosso_sobre_networkx": 0.5, "resultados_iguais": True,
        }],
    }],
}
COMPLEXIDADE = {
    "comando": "python benchmarks/complexidade_empirica.py",
    "maquina": {"processador": "cpu", "python": "3.12"},
    "algoritmos": [{
        "algoritmo": "BFS", "complexidade_teorica": "O(V + E)", "inclinacao_teorica": 1.0,
        "inclinacao_medida": 1.0123, "r2": 0.9991,
        "pontos": [
            {"V_mais_E": 100, "media_s": 0.001},
            {"V_mais_E": 1000, "media_s": 0.01},
            {"V_mais_E": 0, "media_s": 0.01},
        ],
    }],
}

_CODIGO = (
    "from pathlib import Path\n"
    "import streamlit as st\n"
    "from transporte.interface.paginas.desempenho import render\n"
    "render(None, Path(st.session_state['dir']))\n"
)


def _gravar(pasta: Path, nome: str, dados: object) -> None:
    (pasta / nome).write_text(json.dumps(dados), encoding="utf-8")


def test_funcoes_puras(tmp_path: Path) -> None:
    _gravar(tmp_path, "comparacao-networkx-2026-11-01.json", {"grafos": []})
    _gravar(tmp_path, "comparacao-networkx-2026-11-20.json", COMPARACAO)
    (tmp_path / "comparacao-networkx-2026-11-30.json").write_text("{quebrado", encoding="utf-8")
    caminho, dados = ultimo_json(tmp_path, "comparacao-networkx-")
    # O de 30/11 é inválido e é pulado; fica o mais recente válido.
    assert caminho.name == "comparacao-networkx-2026-11-20.json"
    linhas = tabela_comparacao(dados)
    assert linhas[0]["Nosso / NetworkX"] == 0.5 and linhas[0]["Resultados iguais"] == "sim"
    assert tabela_inclinacoes(COMPLEXIDADE)[0]["Inclinação medida"] == 1.01
    pontos = pontos_loglog(COMPLEXIDADE)
    assert len(pontos) == 2  # o de tamanho 0 fica fora
    assert math.isclose(pontos[1]["log10(V + E)"], 3.0)
    assert math.isclose(pontos[1]["log10(tempo em s)"], -2.0)
    assert ultimo_json(tmp_path / "nao-existe", "x") is None


def test_pagina_com_resultados(tmp_path: Path) -> None:
    _gravar(tmp_path, "comparacao-networkx-2026-11-20.json", COMPARACAO)
    _gravar(tmp_path, "complexidade-2026-11-20.json", COMPLEXIDADE)
    _gravar(tmp_path, "nucleo-2026-11-16.json", {"V": 1})
    at = AppTest.from_string(_CODIGO)
    at.session_state["dir"] = str(tmp_path)
    at.run(timeout=30)
    assert not at.exception
    assert any(t.value == "Desempenho" for t in at.title)
    assert len(at.dataframe) == 2
    assert any("coincidem" in s.value for s in at.success)
    assert at.selectbox[0].options == ["nucleo-2026-11-16.json"]
    assert len(at.get("vega_lite_chart")) == 1  # st.line_chart


def test_pagina_ignora_resultados_com_estrutura_invalida(tmp_path: Path) -> None:
    _gravar(tmp_path, "comparacao-networkx-2026-11-20.json", COMPARACAO)
    _gravar(tmp_path, "comparacao-networkx-2026-11-21.json", {"grafos": [None]})
    _gravar(tmp_path, "complexidade-2026-11-20.json", COMPLEXIDADE)
    _gravar(tmp_path, "complexidade-2026-11-21.json", {"algoritmos": [{"pontos": None}]})
    at = AppTest.from_string(_CODIGO)
    at.session_state["dir"] = str(tmp_path)
    at.run(timeout=30)
    assert not at.exception
    assert len(at.dataframe) == 2
    assert sum("2026-11-20.json" in c.value for c in at.caption) == 2


def test_pagina_sem_resultados(tmp_path: Path) -> None:
    at = AppTest.from_string(_CODIGO)
    at.session_state["dir"] = str(tmp_path / "vazia")
    at.run(timeout=30)
    assert not at.exception
    assert len(at.info) == 3
    assert not at.dataframe


def test_pagina_registrada_no_app() -> None:
    assert app.PAGINAS["Desempenho"] == "transporte.interface.paginas.desempenho"
