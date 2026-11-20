"""Funções compartilhadas pelos benchmarks da F-AVAL-OPC (comparar_networkx.py e
complexidade_empirica.py). NetworkX é permitido aqui (benchmarks/), nunca em src/."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import networkx as nx

from transporte.grafo.grafo import Grafo


def maquina() -> dict:
    """Plataforma, processador e versão do Python, no formato dos outros JSON."""
    return {
        "plataforma": platform.platform(),
        "processador": platform.processor(),
        "python": platform.python_version(),
    }


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def para_networkx(g: Grafo) -> nx.DiGraph:
    """Copia o Grafo do núcleo num nx.DiGraph com o atributo "weight".

    Só vértices ativos e arestas utilizáveis (as de Grafo.vizinhos). Arestas paralelas
    viram uma só, com o menor peso, e laços são descartados: é a mesma simplificação que o
    nosso Brandes faz (decisão M3 da F-MET) e não muda BFS, Dijkstra nem Tarjan.
    O(V + E).
    """
    ref = nx.DiGraph()
    ref.add_nodes_from(v for v in range(g.num_vertices()) if g.vertice_ativo(v))
    for u in ref.nodes:
        for v, peso, _a in g.vizinhos(u):
            if v == u:
                continue
            if not ref.has_edge(u, v) or peso < ref[u][v]["weight"]:
                ref.add_edge(u, v, weight=peso)
    return ref


def gravar_json(resultado: dict, saida: Path) -> None:
    texto = json.dumps(resultado, indent=2, ensure_ascii=False)
    print(texto)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(texto + "\n", encoding="utf-8")
    print("gravado em", saida)
