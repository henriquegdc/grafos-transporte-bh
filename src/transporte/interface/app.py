"""Aplicacao Streamlit e ponto de integracao das paginas do projeto."""

from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from hashlib import sha256
from importlib import import_module, util
from pathlib import Path

import streamlit as st

from transporte.interface.mapa import render_mapa
from transporte.interface.protocolos import CarregadorRede, RedeUI

TITULO = "Analise da rede de transporte de Belo Horizonte"
CHAVE_REDE = "rede-p0-ui"
PAGINAS = {
    "Trajetos": "transporte.interface.paginas.trajetos",
    "Espera": "transporte.interface.paginas.espera",
    "Baldeacoes": "transporte.interface.paginas.baldeacoes",
    "Centralidades": "transporte.interface.paginas.centralidades",
    "Eficiencia": "transporte.interface.paginas.eficiencia",
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
    """Carrega uma fonte uma vez por origem/versao usando o loader do P0-DADOS."""
    del identidade
    return _carregador(Path(origem))


def listar_fontes(diretorios: Sequence[Path] = _FONTES_PADRAO) -> tuple[Path, ...]:
    """Lista arquivos GTFS zip e diretorios com stops.txt nas pastas indicadas."""
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
    """Conta os elementos descritos no contrato normalizado de P0-DADOS."""
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
    """Carrega a fonte pelo cache e devolve uma copia isolada para a sessao."""
    identidade = _identidade_fonte(origem, carregador)
    rede_compartilhada = _carregar_rede_em_cache(str(origem), identidade, carregador)
    return deepcopy(rede_compartilhada)


def _render_inicio(carregador: CarregadorRede | None) -> None:
    st.title("Início")
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
            if carregador is None:
                st.warning(
                    "Carregamento bloqueado: P0-DADOS ainda nao publicou uma funcao "
                    "de carregamento. A interface ja aceita o contrato Rede do projeto."
                )
            else:
                st.session_state[CHAVE_REDE] = carregar_rede(fonte, carregador)

    rede = st.session_state.get(CHAVE_REDE)
    if rede is None:
        if carregador is None and fontes:
            st.caption("A integracao com o carregador depende da feature P0-DADOS.")
        return

    resumo = resumo_rede(rede)
    st.subheader("Resumo da rede")
    colunas = st.columns(3)
    for coluna, (rotulo, quantidade) in zip(colunas, resumo.items(), strict=True):
        coluna.metric(rotulo.capitalize(), quantidade)
    if rede.paradas:
        render_mapa(rede, mostrar_paradas=True, mostrar_linhas=True, chave="mapa-inicio")
    else:
        st.info("A rede carregada nao contem paradas para exibir no mapa.")


def _render_pagina(nome: str, rede: RedeUI) -> None:
    modulo = PAGINAS[nome]
    if util.find_spec(modulo) is None:
        st.info(f"A pagina {nome} ainda nao foi implementada.")
        return
    pagina = import_module(modulo)
    render = getattr(pagina, "render", None)
    if not callable(render):
        raise TypeError(f"O modulo {modulo} precisa publicar render(rede).")
    render(rede)


def main(carregador: CarregadorRede | None = None) -> None:
    """Renderiza a aplicacao; recebe o loader de P0-DADOS quando estiver disponivel."""
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
