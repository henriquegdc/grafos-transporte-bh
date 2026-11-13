from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from transporte.grafo.grafo import Grafo
from transporte.interface import app

_RAIZ = Path(__file__).resolve().parents[2]


@dataclass
class Rede:
    paradas: dict[str, object]
    linhas: dict[str, object]
    padroes: dict[str, object]


def test_listar_fontes_encontra_zip_e_diretorios_gtfs(tmp_path: Path) -> None:
    raiz = tmp_path / "fontes"
    raiz.mkdir()
    (raiz / "feed.zip").write_bytes(b"")
    (raiz / "pasta-gtfs").mkdir()
    (raiz / "pasta-gtfs" / "stops.txt").write_text("stop_id,stop_name\n", encoding="utf-8")
    (raiz / "nao-e-gtfs").mkdir()

    fontes = app.listar_fontes((raiz,))

    assert fontes == tuple(
        sorted((raiz / "feed.zip", raiz / "pasta-gtfs"), key=lambda path: str(path).casefold())
    )


def test_listar_fontes_aceita_diretorio_gtfs_como_raiz(tmp_path: Path) -> None:
    (tmp_path / "stops.txt").write_text("stop_id,stop_name\n", encoding="utf-8")

    assert app.listar_fontes((tmp_path,)) == (tmp_path.resolve(),)


def test_entrada_real_inicia_sem_pythonpath() -> None:
    ambiente = os.environ.copy()
    ambiente.pop("PYTHONPATH", None)
    resultado = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from streamlit.testing.v1 import AppTest; "
                "app=AppTest.from_file('src/transporte/interface/app.py').run(); "
                "assert not app.exception, [e.message for e in app.exception]"
            ),
        ],
        cwd=_RAIZ,
        env=ambiente,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert resultado.returncode == 0, resultado.stdout + resultado.stderr


def test_resumo_rede_conta_campos_do_contrato() -> None:
    rede = Rede({"A": object(), "B": object()}, {"L1": object()}, {"P1": object(), "P2": object()})

    assert app.resumo_rede(rede) == {"paradas": 2, "linhas": 1, "padroes": 2}


def test_carregamento_em_cache_isola_cada_sessao(tmp_path: Path) -> None:
    origem = tmp_path / "feed.zip"
    origem.write_bytes(b"gtfs")
    grafo = Grafo()
    grafo.adicionar_vertice("A")
    rede = Rede({"A": ["parada"]}, {"grafo": grafo}, {})
    chamadas = 0

    def carregar(caminho: Path) -> Rede:
        nonlocal chamadas
        chamadas += 1
        assert caminho == origem
        return rede

    app._carregar_rede_em_cache.clear()

    primeira = app.carregar_rede(origem, carregar)
    segunda = app.carregar_rede(origem, carregar)
    primeira.paradas["A"].append("alteracao de outra sessao")
    primeira.linhas["grafo"].desativar_vertice(0)

    assert primeira is not segunda
    assert primeira.paradas is not segunda.paradas
    assert segunda.paradas == {"A": ["parada"]}
    assert segunda.linhas["grafo"].vertice_ativo(0)
    assert chamadas == 1


def test_identidade_fonte_muda_quando_arquivo_do_gtfs_muda(tmp_path: Path) -> None:
    (tmp_path / "stops.txt").write_text("stop_id\nA\n", encoding="utf-8")

    def carregar(_: Path) -> Rede:
        return Rede({}, {}, {})

    primeira = app._identidade_fonte(tmp_path, carregar)
    (tmp_path / "stops.txt").write_text("stop_id\nA\nB\n", encoding="utf-8")

    segunda = app._identidade_fonte(tmp_path, carregar)

    assert segunda != primeira


def test_pagina_chama_contrato_render_rede(monkeypatch) -> None:
    rede = Rede({}, {}, {})
    recebida = []
    pagina = SimpleNamespace(render=recebida.append)
    monkeypatch.setitem(app.PAGINAS, "Trajetos", "pagina_teste")
    monkeypatch.setattr(app.util, "find_spec", lambda _: object())
    monkeypatch.setattr(app, "import_module", lambda _: pagina)

    app._render_pagina("Trajetos", rede)

    assert recebida == [rede]
