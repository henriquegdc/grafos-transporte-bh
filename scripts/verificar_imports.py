"""Verifica que nenhum módulo de `src/` importa biblioteca de grafo (RNF-01).

Lê cada arquivo `.py` com o módulo `ast` (sem executar o código) e falha se encontrar
um import proibido. Cobre `import x`, `from x import y`, imports relativos ignorados e as
formas dinâmicas `importlib.import_module("x")` e `__import__("x")` com nome literal.

Proibidos (AGENTS.md §3 e plano-de-projeto §10):
- bibliotecas de grafo: networkx, igraph, graph_tool, rustworkx, scipy.sparse.csgraph, osmnx;
- heapq: a fila de prioridade é a própria (`transporte.grafo.heap`).

Uso:
    python scripts/verificar_imports.py            # verifica src/
    python scripts/verificar_imports.py caminho/   # verifica outro diretório ou arquivo

Saída 0 se limpo; 1 se houver import proibido; 2 se um arquivo não puder ser lido.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

PROIBIDOS: dict[str, str] = {
    "networkx": "biblioteca de grafo",
    "igraph": "biblioteca de grafo",
    "graph_tool": "biblioteca de grafo",
    "rustworkx": "biblioteca de grafo",
    "scipy.sparse.csgraph": "biblioteca de grafo",
    "osmnx": "biblioteca de grafo",
    "heapq": "fila de prioridade pronta; use transporte.grafo.heap",
}

RAIZ_PADRAO = Path(__file__).resolve().parent.parent / "src"


@dataclass(frozen=True)
class Violacao:
    arquivo: Path
    linha: int
    modulo: str
    motivo: str

    def formatar(self) -> str:
        return f"{self.arquivo}:{self.linha}: import proibido '{self.modulo}' ({self.motivo})"


def _proibido(modulo: str) -> str | None:
    """Devolve o nome proibido que `modulo` importa, ou None.

    Casa o nome exato e qualquer submódulo (`networkx.algorithms` casa `networkx`).
    """
    for nome in PROIBIDOS:
        if modulo == nome or modulo.startswith(nome + "."):
            return nome
    return None


def _modulos_importados(arvore: ast.AST) -> list[tuple[int, str]]:
    """Lista (linha, nome completo) de tudo que a árvore importa."""
    encontrados: list[tuple[int, str]] = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for alias in no.names:
                encontrados.append((no.lineno, alias.name))
        elif isinstance(no, ast.ImportFrom):
            if no.level > 0 or no.module is None:
                continue  # import relativo: é código do próprio projeto
            encontrados.append((no.lineno, no.module))
            # `from scipy.sparse import csgraph` importa scipy.sparse.csgraph
            for alias in no.names:
                encontrados.append((no.lineno, f"{no.module}.{alias.name}"))
        elif (
            isinstance(no, ast.Call)
            and _e_import_dinamico(no.func)
            and no.args
            and isinstance(no.args[0], ast.Constant)
            and isinstance(no.args[0].value, str)
        ):
            encontrados.append((no.lineno, no.args[0].value))
    return encontrados


def _e_import_dinamico(func: ast.expr) -> bool:
    if isinstance(func, ast.Name):
        return func.id in {"__import__", "import_module"}
    if isinstance(func, ast.Attribute):
        return func.attr == "import_module"
    return False


def verificar_arquivo(arquivo: Path) -> list[Violacao]:
    """Devolve as violações de um arquivo. Levanta SyntaxError/OSError se não ler."""
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"), filename=str(arquivo))
    violacoes: list[Violacao] = []
    vistos: set[tuple[int, str]] = set()
    for linha, modulo in _modulos_importados(arvore):
        nome = _proibido(modulo)
        if nome is not None and (linha, nome) not in vistos:
            vistos.add((linha, nome))
            violacoes.append(Violacao(arquivo, linha, nome, PROIBIDOS[nome]))
    return violacoes


def verificar(raiz: Path) -> list[Violacao]:
    """Verifica um arquivo `.py` ou todos os `.py` sob um diretório."""
    arquivos = [raiz] if raiz.is_file() else sorted(raiz.rglob("*.py"))
    violacoes: list[Violacao] = []
    for arquivo in arquivos:
        violacoes.extend(verificar_arquivo(arquivo))
    return violacoes


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    raizes = [Path(a) for a in args] or [RAIZ_PADRAO]
    violacoes: list[Violacao] = []
    for raiz in raizes:
        if not raiz.exists():
            print(f"verificar_imports: caminho não existe: {raiz}", file=sys.stderr)
            return 2
        try:
            violacoes.extend(verificar(raiz))
        except (SyntaxError, OSError, UnicodeDecodeError) as erro:
            print(f"verificar_imports: não foi possível ler: {erro}", file=sys.stderr)
            return 2
    for v in violacoes:
        print(v.formatar(), file=sys.stderr)
    if violacoes:
        print(
            f"verificar_imports: {len(violacoes)} import(s) proibido(s). "
            "NetworkX e afins só em tests/ e benchmarks/ (AGENTS.md §3).",
            file=sys.stderr,
        )
        return 1
    print("verificar_imports: nenhum import proibido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
