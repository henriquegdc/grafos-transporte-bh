from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from transporte.dados.modelo import Linha, Padrao, Parada, Rede
from transporte.modelo.visoes import EMBARQUE


def _rede() -> Rede:
    paradas = {
        "A": Parada("A", "A", -19.92, -43.94),
        "B": Parada("B", "B", -19.90, -43.94),
        "C": Parada("C", "C", -19.88, -43.94),
    }
    linhas = {"L1": Linha("L1", "Linha 1", 3)}
    padroes = {
        "P1": Padrao("P1", "L1", ("A", "B")),
        "P2": Padrao("P2", "L1", ("B", "C")),
    }
    viagens = {
        "P1": [(7 * 3600, 7 * 3600 + 120), (7 * 3600 + 200, 7 * 3600 + 320)],
        "P2": [(7 * 3600, 7 * 3600 + 180), (7 * 3600 + 300, 7 * 3600 + 480)],
    }
    return Rede(
        paradas=paradas,
        linhas=linhas,
        padroes=padroes,
        partidas={},
        viagens=viagens,
    )


def test_pagina_exibe_metricas_e_informacao_da_amostra() -> None:
    codigo = (
        "import streamlit as st\n"
        "from transporte.interface.paginas.eficiencia import render\n"
        "render(st.session_state['rede'])"
    )
    teste = AppTest.from_string(codigo)
    teste.session_state["rede"] = _rede()

    teste.run()
    teste.button[0].click().run()

    assert not teste.exception
    metricas = {metrica.label: metrica.value for metrica in teste.metric}
    assert metricas["Eficiência global (G_P)"] != "—"
    assert "min" in metricas["Tempo médio de viagem (G_E)"]
    assert any("Amostra:" in legenda.value for legenda in teste.caption)
    assert any("podem levar algum tempo" in legenda.value for legenda in teste.caption)
    _, _, ge, _ = teste.session_state["visoes-f-efi"]
    embarques = [
        ge.grafo.aresta(a)
        for _, _, a in ge.grafo.vizinhos(ge.vertice_da_parada["A"])
        if ge.grafo.aresta(a)[3] == EMBARQUE
    ]
    assert any(aresta[2] == pytest.approx(100) for aresta in embarques)


def test_pagina_rejeita_rede_com_menos_de_duas_paradas() -> None:
    codigo = (
        "import streamlit as st\n"
        "from transporte.interface.paginas.eficiencia import render\n"
        "render(st.session_state['rede'])"
    )
    rede = _rede()
    rede.paradas.pop("C")
    rede.paradas.pop("B")
    teste = AppTest.from_string(codigo)
    teste.session_state["rede"] = rede

    teste.run()

    assert not teste.exception
    assert any("ao menos duas paradas" in item.value for item in teste.info)
