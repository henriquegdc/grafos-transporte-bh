from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import folium
import pytest
from streamlit.testing.v1 import AppTest

from transporte.interface import app
from transporte.interface.mapa import criar_mapa

FONTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"
CODIGO_APP = "from transporte.interface.app import main\nmain()"


@pytest.mark.parametrize("zipado", [False, True])
def test_app_test_carrega_pasta_ou_zip_e_exibe_resumo_e_visoes(tmp_path, monkeypatch, zipado):
    origem = FONTE
    if zipado:
        origem = tmp_path / "rede.zip"
        with ZipFile(origem, "w") as arquivo:
            for caminho in FONTE.glob("*.txt"):
                arquivo.write(caminho, caminho.name)

    monkeypatch.setattr(app, "listar_fontes", lambda: (origem,))
    mapas = []
    monkeypatch.setattr(app, "render_mapa", lambda rede, **kw: mapas.append(criar_mapa(rede)))
    app._carregar_rede_em_cache.clear()

    teste = AppTest.from_string(CODIGO_APP).run()
    teste.button[0].click().run()

    assert not teste.exception
    metricas = {metrica.label: str(metrica.value) for metrica in teste.metric}
    assert metricas["Paradas"] == "4"
    assert metricas["Linhas"] == "2"
    assert metricas["Padrões"] == "2"
    assert teste.session_state[app.CHAVE_REDE].dia == "2026-11-04"
    assert metricas["G_P · vértices (V)"] == str(len(teste.session_state[app.CHAVE_REDE].paradas))
    assert metricas["G_P · arestas (E)"] == "13"
    assert metricas["G_E · vértices (V)"] == "9"
    assert metricas["G_E · arestas (E)"] == "18"
    assert mapas and any(
        isinstance(elemento, folium.LayerControl) for elemento in mapas[0]._children.values()
    )


def test_app_test_carrega_o_feed_e_renderiza_o_widget_do_mapa():
    app._carregar_rede_em_cache.clear()
    teste = AppTest.from_file(str(FONTE.parents[1] / "src/transporte/interface/app.py")).run(
        timeout=30
    )

    teste.button[0].click().run(timeout=30)

    assert not teste.exception
    assert teste.session_state[app.CHAVE_REDE].dia == "2026-11-04"
    assert {metrica.label for metrica in teste.metric} >= {
        "G_P · arestas (E)",
        "G_E · arestas (E)",
    }


def test_erro_ao_carregar_preserva_rede_anterior(tmp_path, monkeypatch):
    origem = tmp_path / "invalido.zip"
    origem.write_bytes(b"nao e zip")
    monkeypatch.setattr(app, "listar_fontes", lambda: (origem,))
    monkeypatch.setattr(app, "render_mapa", lambda *args, **kwargs: None)
    app._carregar_rede_em_cache.clear()
    anterior = app.ler(FONTE)

    teste = AppTest.from_string(CODIGO_APP)
    teste.session_state[app.CHAVE_REDE] = anterior
    teste.run().button[0].click().run()

    assert not teste.exception
    assert any("Não foi possível carregar" in alerta.value for alerta in teste.error)
    assert teste.session_state[app.CHAVE_REDE] is anterior


def test_abertura_de_pagina_sem_rede_carregada_informa_como_prosseguir():
    teste = AppTest.from_string(CODIGO_APP).run()

    teste.sidebar.radio[0].set_value("Trajetos").run()

    assert not teste.exception
    assert any("Carregue um conjunto de dados" in item.value for item in teste.info)


def test_pagina_nao_implementada_e_informada(monkeypatch):
    monkeypatch.setattr(app, "PAGINAS", {"Nova": "transporte.interface.paginas.nova"})
    monkeypatch.setattr(app.util, "find_spec", lambda _: None)
    rede = SimpleNamespace()
    teste = AppTest.from_string(CODIGO_APP)
    teste.session_state[app.CHAVE_REDE] = rede
    teste.run().sidebar.radio[0].set_value("Nova").run()

    assert not teste.exception
    assert any("ainda não foi implementada" in item.value for item in teste.info)


def test_modulo_sem_render_e_reportado(monkeypatch):
    monkeypatch.setattr(app, "PAGINAS", {"Teste": "transporte.interface.paginas.teste"})
    monkeypatch.setattr(app.util, "find_spec", lambda _: object())
    monkeypatch.setattr(app, "import_module", lambda _: SimpleNamespace())
    teste = AppTest.from_string(CODIGO_APP)
    teste.session_state[app.CHAVE_REDE] = SimpleNamespace()

    teste.run().sidebar.radio[0].set_value("Teste").run()

    assert any("precisa publicar render(rede)" in erro.message for erro in teste.exception)
