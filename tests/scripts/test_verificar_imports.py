"""Testes de scripts/verificar_imports.py (RNF-01)."""

from __future__ import annotations

from pathlib import Path

import pytest
import verificar_imports as vi


def _escrever(tmp_path: Path, codigo: str, nome: str = "modulo.py") -> Path:
    arquivo = tmp_path / nome
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(codigo, encoding="utf-8")
    return arquivo


@pytest.mark.parametrize(
    ("codigo", "esperado"),
    [
        ("import networkx\n", "networkx"),
        ("import networkx as nx\n", "networkx"),
        ("import networkx.algorithms.shortest_paths\n", "networkx"),
        ("from networkx import DiGraph\n", "networkx"),
        ("import igraph\n", "igraph"),
        ("from graph_tool.all import Graph\n", "graph_tool"),
        ("import rustworkx as rx\n", "rustworkx"),
        ("import osmnx\n", "osmnx"),
        ("import scipy.sparse.csgraph\n", "scipy.sparse.csgraph"),
        ("from scipy.sparse.csgraph import dijkstra\n", "scipy.sparse.csgraph"),
        ("from scipy.sparse import csgraph\n", "scipy.sparse.csgraph"),
        ("import heapq\n", "heapq"),
        ("from heapq import heappush\n", "heapq"),
        ("import os, heapq\n", "heapq"),
        ("import importlib\nimportlib.import_module('networkx')\n", "networkx"),
        ("__import__('heapq')\n", "heapq"),
        ("def f():\n    import networkx\n", "networkx"),
    ],
)
def test_detecta_import_proibido(tmp_path: Path, codigo: str, esperado: str) -> None:
    violacoes = vi.verificar_arquivo(_escrever(tmp_path, codigo))
    assert [v.modulo for v in violacoes] == [esperado]


@pytest.mark.parametrize(
    "codigo",
    [
        "import math\nfrom collections import deque\n",
        "import scipy\nimport scipy.sparse\n",  # scipy em si não é proibido
        "from scipy.sparse import csr_matrix\n",
        "import networkx_extra\n",  # prefixo parecido, outro pacote
        "from transporte.grafo import heap\nfrom transporte.grafo.heap import HeapMin\n",
        "from . import heap\nfrom .heap import HeapMin\n",  # relativo
        "texto = 'import networkx'\n",  # string, não import
        "import pandas as pd\n",
    ],
)
def test_aceita_import_permitido(tmp_path: Path, codigo: str) -> None:
    assert vi.verificar_arquivo(_escrever(tmp_path, codigo)) == []


def test_reporta_linha_correta(tmp_path: Path) -> None:
    arquivo = _escrever(tmp_path, "import math\n\n\nimport networkx\n")
    [violacao] = vi.verificar_arquivo(arquivo)
    assert violacao.linha == 4
    assert f"{arquivo}:4:" in violacao.formatar()


def test_um_import_com_dois_proibidos(tmp_path: Path) -> None:
    violacoes = vi.verificar_arquivo(_escrever(tmp_path, "import networkx, heapq\n"))
    assert sorted(v.modulo for v in violacoes) == ["heapq", "networkx"]


def test_varre_subdiretorios(tmp_path: Path) -> None:
    _escrever(tmp_path, "import math\n", "a/ok.py")
    _escrever(tmp_path, "import igraph\n", "a/b/ruim.py")
    violacoes = vi.verificar(tmp_path)
    assert [(v.arquivo.name, v.modulo) for v in violacoes] == [("ruim.py", "igraph")]


def test_main_codigos_de_saida(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    limpo = _escrever(tmp_path, "import math\n", "limpo/m.py").parent
    sujo = _escrever(tmp_path, "import networkx\n", "sujo/m.py").parent
    quebrado = _escrever(tmp_path, "def (:\n", "quebrado/m.py").parent

    assert vi.main([str(limpo)]) == 0
    assert vi.main([str(sujo)]) == 1
    assert "networkx" in capsys.readouterr().err
    assert vi.main([str(quebrado)]) == 2
    assert vi.main([str(tmp_path / "nao-existe")]) == 2


def test_src_do_projeto_esta_limpo() -> None:
    """O próprio src/ do repositório não pode ter import proibido."""
    assert vi.verificar(vi.RAIZ_PADRAO) == []
