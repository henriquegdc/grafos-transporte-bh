"""Aplicação Streamlit e ponto de integração das páginas. estado: implementado."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from copy import deepcopy
from hashlib import sha256
from importlib import import_module, util
from pathlib import Path
from zipfile import BadZipFile

# The documented command runs this file without installing the src-layout package.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from transporte.dados.leitor_gtfs import ler
from transporte.interface.mapa import render_mapa
from transporte.interface.protocolos import CarregadorRede, RedeUI
from transporte.modelo.construtores import construir_ge, construir_gp
from transporte.modelo.parametros import Parametros

TITULO = "Análise da rede de transporte de Belo Horizonte"
CHAVE_REDE = "rede-p0-ui"
CHAVE_RESUMO_VISOES = "resumo-visoes-p0-ui"
PAGINAS = {
    "Trajetos": "transporte.interface.paginas.trajetos",
    "Espera": "transporte.interface.paginas.espera",
    "Baldeações": "transporte.interface.paginas.baldeacoes",
    "Centralidades": "transporte.interface.paginas.centralidades",
    "Eficiência": "transporte.interface.paginas.eficiencia",
    "Falhas": "transporte.interface.paginas.falhas",
}
_RAIZ = Path(__file__).resolve().parents[3]
_FONTES_PADRAO = (_RAIZ / "dados" / "rede-teste", _RAIZ / "dados" / "brutos")


@st.cache_resource(show_spinner=False)
def _carregar_rede_em_cache(
    origem: str,
    identidade: str,
    _carregador: CarregadorRede,
) -> RedeUI:
    """Carrega uma fonte pelo loader de P0-DADOS e reutiliza seu resultado no cache.

    Entradas: origem da pasta/ZIP, identidade observável da fonte e loader.
    Saída: Rede compartilhada do cache; `carregar_rede` devolve uma cópia por sessão.
    Casos de borda: erros do loader são propagados, sem armazenar um resultado parcial.
    Complexidade: depende do loader apenas quando a chave ainda não está no cache.
    """
    del identidade
    return _carregador(Path(origem))


def listar_fontes(diretorios: Sequence[Path] = _FONTES_PADRAO) -> tuple[Path, ...]:
    """Descobre ZIPs e pastas GTFS na raiz ou um nível abaixo dos diretórios.

    Entradas: diretórios a consultar; diretórios ausentes são ignorados.
    Saída: caminhos absolutos únicos e ordenados, sem validar o conteúdo de ZIPs.
    Casos de borda: diretório sem `stops.txt`, arquivo não ZIP e diretório inexistente
        não são tratados como fontes; a validação GTFS é responsabilidade de P0-DADOS.
    Complexidade: O(D + Z), sendo D as entradas imediatas consultadas e Z os ZIPs
        encontrados; espaço O(Z + F), sendo F as pastas GTFS encontradas.
    """
    fontes: set[Path] = set()
    for diretorio in diretorios:
        if not diretorio.is_dir():
            continue
        if (diretorio / "stops.txt").is_file():
            fontes.add(diretorio.resolve())
        fontes.update(path.resolve() for path in diretorio.glob("*.zip") if path.is_file())
        fontes.update(
            path.resolve()
            for path in diretorio.iterdir()
            if path.is_dir() and (path / "stops.txt").is_file()
        )
    return tuple(sorted(fontes, key=lambda path: str(path).casefold()))


def resumo_rede(rede: RedeUI) -> dict[str, int]:
    """Conta paradas, linhas e padrões da rede normalizada.

    Entrada: Rede de P0-DADOS.
    Saída: contagens em um dicionário com as chaves `paradas`, `linhas` e `padroes`.
    Casos de borda: mapas vazios produzem contagens zero.
    Complexidade: tempo e espaço O(1).
    """
    return {
        "paradas": len(rede.paradas),
        "linhas": len(rede.linhas),
        "padroes": len(rede.padroes),
    }


def _identidade_fonte(origem: Path, carregador: CarregadorRede) -> str:
    arquivos = (
        (origem,)
        if origem.is_file()
        else tuple(sorted(path for path in origem.rglob("*") if path.is_file()))
    )
    digest = sha256()
    for arquivo in arquivos:
        estado = arquivo.stat()
        relativo = arquivo.name if origem.is_file() else str(arquivo.relative_to(origem))
        digest.update(f"{relativo}\0{estado.st_mtime_ns}\0{estado.st_size}\n".encode())
    return f"{id(carregador)}:{digest.hexdigest()}"


def carregar_rede(origem: Path, carregador: CarregadorRede) -> RedeUI:
    """Carrega uma pasta/ZIP GTFS pelo cache e isola o objeto entregue à sessão.

    Entradas: caminho de fonte descoberto por `listar_fontes` e loader de P0-DADOS.
    Saída: cópia profunda da Rede cacheada, independente de mutações em outras sessões.
    Casos de borda: falhas de leitura ou cópia são propagadas; a fonte é identificada
        pelos caminhos, tamanhos e tempos de modificação dos arquivos.
    Complexidade: O(F) para inspecionar metadados dos F arquivos e O(R) para copiar os
        R elementos da Rede; o parsing só ocorre quando há cache miss.
    """
    identidade = _identidade_fonte(origem, carregador)
    rede_compartilhada = _carregar_rede_em_cache(str(origem), identidade, carregador)
    return deepcopy(rede_compartilhada)


def _resumo_visoes(rede: RedeUI) -> tuple[dict[str, tuple[int, int]], str]:
    """Constrói G_P e G_E da faixa inicial e devolve seus totais V/E."""
    parametros = Parametros()
    faixa = parametros.faixas[0].nome
    gp = construir_gp(rede, parametros)
    ge = construir_ge(rede, faixa, parametros)
    return {
        "G_P": (gp.grafo.num_vertices(), gp.grafo.num_arestas()),
        "G_E": (ge.grafo.num_vertices(), ge.grafo.num_arestas()),
    }, faixa


def _render_inicio(carregador: CarregadorRede) -> None:
    st.header("Início")
    fontes = listar_fontes()
    if not fontes:
        st.info(
            "Nenhum GTFS foi encontrado em dados/rede-teste ou dados/brutos. "
            "Adicione uma rede GTFS para habilitar o carregamento."
        )
    else:
        fonte = st.selectbox(
            "Conjunto de dados",
            fontes,
            format_func=lambda path: (
                str(path.relative_to(_RAIZ)) if path.is_relative_to(_RAIZ) else str(path)
            ),
        )
        if st.button("Carregar rede", type="primary"):
            try:
                with st.spinner("Carregando e preparando as visões da rede..."):
                    nova_rede = carregar_rede(fonte, carregador)
                    resumo_visoes, faixa = _resumo_visoes(nova_rede)
            except (OSError, ValueError, UnicodeError, BadZipFile, KeyError) as erro:
                st.error(f"Não foi possível carregar a rede: {erro}")
            else:
                st.session_state[CHAVE_REDE] = nova_rede
                st.session_state[CHAVE_RESUMO_VISOES] = (resumo_visoes, faixa)

    rede = st.session_state.get(CHAVE_REDE)
    if rede is None:
        return

    resumo = resumo_rede(rede)
    st.subheader("Resumo da rede")
    colunas = st.columns(3)
    rotulos = {"paradas": "Paradas", "linhas": "Linhas", "padroes": "Padrões"}
    for coluna, (rotulo, quantidade) in zip(colunas, resumo.items(), strict=True):
        coluna.metric(rotulos[rotulo], quantidade)
    st.caption(f"Dia de serviço: {rede.dia or 'não informado'}")

    resumo_visoes = st.session_state.get(CHAVE_RESUMO_VISOES)
    if resumo_visoes is None:
        try:
            resumo_visoes = _resumo_visoes(rede)
        except (ValueError, KeyError) as erro:
            st.error(f"Não foi possível construir as visões da rede: {erro}")
            return
        st.session_state[CHAVE_RESUMO_VISOES] = resumo_visoes
    totais, faixa = resumo_visoes
    st.subheader("Visões do grafo")
    colunas = st.columns(2)
    for coluna, (nome, (vertices, arestas)) in zip(colunas, totais.items(), strict=True):
        coluna.metric(f"{nome} · vértices (V)", vertices)
        coluna.metric(f"{nome} · arestas (E)", arestas)
    st.caption(f"G_E exibido para a faixa {faixa}.")

    if rede.inconsistencias:
        st.warning(f"Foram encontradas {len(rede.inconsistencias)} inconsistências no GTFS.")
        with st.expander("Ver inconsistências"):
            for inconsistencia in rede.inconsistencias:
                st.write(inconsistencia)
    else:
        st.success("Nenhuma inconsistência encontrada no GTFS.")

    if rede.paradas:
        render_mapa(rede, mostrar_paradas=True, mostrar_linhas=True, chave="mapa-inicio")
    else:
        st.info("A rede carregada não contém paradas para exibir no mapa.")


def _render_pagina(nome: str, rede: RedeUI) -> None:
    modulo = PAGINAS[nome]
    if util.find_spec(modulo) is None:
        st.info(f"A página {nome} ainda não foi implementada.")
        return
    pagina = import_module(modulo)
    render = getattr(pagina, "render", None)
    if not callable(render):
        raise TypeError(f"O módulo {modulo} precisa publicar render(rede).")
    render(rede)


def main(carregador: CarregadorRede = ler) -> None:
    """Renderiza a aplicação Streamlit com o loader oficial de P0-DADOS.

    Entrada: loader que recebe um caminho de pasta/ZIP e devolve a Rede normalizada;
        `ler` é o padrão e outros loaders podem ser injetados em testes.
    Saída: None; configura a navegação, carrega a rede selecionada e despacha páginas
        pelo contrato `render(rede)`.
    Casos de borda: fonte ausente é informada; erro de carga mantém a Rede anterior;
        página ainda não criada exibe indisponibilidade e módulo sem `render` falha
        explicitamente com TypeError.
    Complexidade: depende do carregamento e da construção das visões na primeira carga;
        navegação subsequente reutiliza o estado de sessão.
    """
    st.set_page_config(page_title=TITULO, page_icon="🚌", layout="wide")
    st.title(TITULO)
    pagina = st.sidebar.radio("Navegação", ("Início", *PAGINAS))
    if pagina == "Início":
        _render_inicio(carregador)
        return

    rede = st.session_state.get(CHAVE_REDE)
    if rede is None:
        st.info("Carregue um conjunto de dados na página Início antes de abrir esta página.")
        return
    _render_pagina(pagina, rede)


if __name__ == "__main__":
    main()
