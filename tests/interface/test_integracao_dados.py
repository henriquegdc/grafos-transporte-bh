"""Integração P0-DADOS → carregamento e mapa da interface."""

import os
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest
from streamlit.testing.v1 import AppTest

from transporte.dados.leitor_gtfs import ler
from transporte.interface import app
from transporte.interface.mapa import criar_mapa

FONTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"


def test_comando_documentado_importa_sem_pythonpath():
    ambiente = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    resultado = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from streamlit.testing.v1 import AppTest; "
                "at=AppTest.from_file('src/transporte/interface/app.py').run(); "
                "assert not at.exception, [e.message for e in at.exception]"
            ),
        ],
        env=ambiente,
        check=False,
        cwd=FONTE.parents[1],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


@pytest.mark.parametrize("zipado", [False, True])
def test_entrada_normal_carrega_gtfs_mostra_resumo_e_mapa(tmp_path, monkeypatch, zipado):
    origem = FONTE
    if zipado:
        origem = tmp_path / "rede.zip"
        with ZipFile(origem, "w") as arquivo:
            for caminho in FONTE.glob("*.txt"):
                arquivo.write(caminho, caminho.name)
    monkeypatch.setattr(app, "listar_fontes", lambda: (origem,))
    mapas = []
    monkeypatch.setattr(app, "render_mapa", lambda rede, **kw: mapas.append(criar_mapa(rede)))
    at = AppTest.from_string("from transporte.interface.app import main\nmain()")
    at.run()
    at.button[0].click().run()
    assert not at.exception
    assert [m.value for m in at.metric] == ["4", "2", "2"]
    assert at.session_state[app.CHAVE_REDE].dia == "2026-11-04"
    assert mapas and mapas[0].get_root().render()


def test_erro_de_gtfs_e_apresentado_sem_apagar_rede_anterior(tmp_path, monkeypatch):
    origem = tmp_path / "invalido.zip"
    origem.write_bytes(b"nao e zip")
    monkeypatch.setattr(app, "listar_fontes", lambda: (origem,))
    monkeypatch.setattr(app, "render_mapa", lambda *a, **kw: None)
    at = AppTest.from_string("from transporte.interface.app import main\nmain()")
    anterior = ler(FONTE)
    at.session_state[app.CHAVE_REDE] = anterior
    at.run().button[0].click().run()
    assert not at.exception
    assert "Não foi possível carregar" in at.error[0].value
    assert at.session_state[app.CHAVE_REDE] is anterior
