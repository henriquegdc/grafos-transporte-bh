"""Fluxo da página F-ESPERA e sua integração com o shell."""

from datetime import time
from pathlib import Path
from zipfile import ZipFile

import pytest
from streamlit.testing.v1 import AppTest

from transporte.dados.leitor_gtfs import ler
from transporte.dados.modelo import Parada
from transporte.interface import app
from transporte.interface.paginas import espera
from transporte.modelo.parametros import Parametros
from transporte.simulacao.espera import estimar_intervalos

FONTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"


@pytest.mark.parametrize("zipado", [False, True])
def test_shell_abre_espera_apos_carregar_dataset(tmp_path, monkeypatch, zipado):
    origem = FONTE
    if zipado:
        origem = tmp_path / "rede.zip"
        with ZipFile(origem, "w") as arquivo:
            for caminho in FONTE.glob("*.txt"):
                arquivo.write(caminho, caminho.name)
    monkeypatch.setattr(app, "listar_fontes", lambda: (origem,))
    monkeypatch.setattr(app, "render_mapa", lambda *a, **kw: None)
    at = AppTest.from_string("from transporte.interface.app import main\nmain()")
    at.run().button[0].click().run()
    at.sidebar.radio[0].set_value("Espera").run()
    assert not at.exception
    assert any(t.value == "Espera" for t in at.title)
    assert len(at.dataframe[0].value) == 2


def test_tabela_distingue_h2_fallback_e_sem_servico():
    rede = ler(FONTE)
    pid = next(p for p in rede.padroes if rede.padroes[p].linha_id == "L1")
    rede.viagens[pid] = [(28800, 29100, 29400)]
    tabela = espera._tabela_intervalos(rede, Parametros(), estimar_intervalos(rede))
    l1 = next(r for r in tabela if r["Padrão"] == pid and r["Faixa"] == "pico_manha")
    assert (l1["Intervalo (min)"], l1["Espera (min)"], l1["Estimativa"]) == (
        None,
        5,
        "Provisória: uma partida",
    )
    assert any(r["Estimativa"] == "Sem serviço" and r["Espera (min)"] is None for r in tabela)
    assert any(r["Estimativa"] == "H/2" and r["Espera (min)"] == 5 for r in tabela)


@pytest.fixture
def pagina(monkeypatch):
    monkeypatch.setattr(espera, "render_mapa", lambda *a, **kw: None)
    rede = ler(FONTE)
    # Paradas separadas para obrigar o ônibus e permitir conferir a espera na tela.
    rede.paradas = {p: Parada(p, p, -19.9 + i / 100, -43.9) for i, p in enumerate(rede.paradas)}
    at = AppTest.from_string(
        "import streamlit as st\n"
        "from transporte.interface.paginas.espera import render\n"
        "render(st.session_state['rede'])"
    )
    at.session_state["rede"] = rede
    return at.run()


def test_pagina_simula_decompoe_e_preserva_resultado_em_rerun(pagina):
    pagina.selectbox[2].set_value("C")
    pagina.button[0].click().run()
    assert not pagina.exception
    assert [m.value for m in pagina.metric] == ["20.00 min", "0.00 min", "10.00 min", "10.00 min"]
    pagina.run()
    assert len(pagina.metric) == 4
    # Troca do dataset não pode deixar resultado da rede anterior na tela.
    pagina.session_state["rede"] = ler(FONTE)
    pagina.run()
    assert not pagina.metric


def test_pagina_horario_invalido_limpa_resultado(pagina):
    pagina.button[0].click().run()
    assert pagina.metric
    pagina.time_input[0].set_value(time(3, 0))
    pagina.button[0].click().run()
    assert not pagina.exception
    assert "fora das faixas" in pagina.error[0].value
    assert not pagina.metric


def test_pagina_inalcancavel(pagina):
    pagina.selectbox[1].set_value("C")
    pagina.selectbox[2].set_value("A")
    pagina.button[0].click().run()
    assert not pagina.exception
    assert "Não há trajeto" in pagina.warning[0].value


def test_pagina_origem_igual_destino(pagina):
    pagina.selectbox[2].set_value("A")
    pagina.button[0].click().run()
    assert not pagina.exception
    assert [m.value for m in pagina.metric] == ["0.00 min"] * 4
