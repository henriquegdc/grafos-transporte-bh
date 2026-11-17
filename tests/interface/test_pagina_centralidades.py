"""Página Centralidades (F-MET, RF-MET-03) na rede de teste.

Gabarito à mão de G_P da rede de teste (paradas A, B, C, D; vértices 0 a 3):
    viagem: A -> B (300 s), B -> C (300 s), A -> D (480 s);
    caminhada nos dois sentidos: A-B 127 s, B-C 127 s, B-D 127 s, A-D 174 s, A-C 185 s.
    Grau de saída só com viagem: A 2, B 1, C 0, D 0.
    Intermediação por tempo: só B fica no meio de caminhos mínimos, em C -> D
    (C-B-D, 254 s, contra C-A-D, 359 s) e em D -> C; bc = [0, 2, 0, 0], normalizada
    2 / ((4 - 1)(4 - 2)) = 1/3.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from transporte.dados.leitor_gtfs import ler
from transporte.interface import app
from transporte.interface.paginas import centralidades as pagina
from transporte.modelo.construtores import construir_gp

FONTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"


@pytest.fixture(scope="module")
def rede():
    return ler(FONTE)


@pytest.fixture(scope="module")
def visao(rede):
    return construir_gp(rede)


def test_intermediacao_exata_normalizada_gabarito(visao):
    c = pagina.calcular(visao, pagina.INTERMEDIACAO, amostra=None)
    assert c.valores == pytest.approx([0, 1 / 3, 0, 0])
    assert c.erros is None
    assert "exata" in c.descricao


def test_intermediacao_amostrada_tem_erro(visao):
    c = pagina.calcular(visao, pagina.INTERMEDIACAO, amostra=2)
    assert c.erros is not None and len(c.erros) == 4
    assert "2 de 4 origens" in c.descricao


def test_grau_de_saida_so_viagem_gabarito(visao):
    c = pagina.calcular(visao, pagina.SAIDA, so_viagem=True)
    assert c.valores == [2, 1, 0, 0]
    assert c.distribuicao == {0: 2, 1: 1, 2: 1}


def test_grau_de_saida_com_caminhada(visao):
    c = pagina.calcular(visao, pagina.SAIDA, so_viagem=False)
    assert c.valores == [5, 4, 2, 2]


def test_metrica_desconhecida(visao):
    with pytest.raises(ValueError):
        pagina.calcular(visao, "proximidade")


def test_tabela_ranking_ordena_e_mostra_erro(rede, visao):
    exata = pagina.calcular(visao, pagina.INTERMEDIACAO, amostra=None)
    linhas = pagina.tabela_ranking(rede, visao, exata, 2)
    assert [linha["Parada"] for linha in linhas] == ["Meio (B)", "Origem (A)"]
    assert linhas[0]["Posição"] == 1 and "± erro padrão" not in linhas[0]
    amostrada = pagina.calcular(visao, pagina.INTERMEDIACAO, amostra=2)
    assert "± erro padrão" in pagina.tabela_ranking(rede, visao, amostrada, 1)[0]


def test_intensidades_normalizadas_pelo_maior(visao):
    graus = pagina.calcular(visao, pagina.SAIDA, so_viagem=True)
    assert pagina.intensidades(visao, graus.valores) == {"A": 1.0, "B": 0.5}
    assert pagina.intensidades(visao, [0.0] * 4) == {}


def test_mapa_tem_calor_top_e_controle_por_ultimo(rede, visao):
    c = pagina.calcular(visao, pagina.SAIDA, so_viagem=True)
    mapa = pagina.mapa_centralidades(rede, visao, c, 2)
    html = mapa.get_root().render()
    assert "heatLayer" in html
    assert "1º Origem (A)" in html and "2º Meio (B)" in html
    filhos = list(mapa._children.values())
    assert type(filhos[-1]).__name__ == "LayerControl"


def test_gp_da_rede_reaproveita_e_troca_com_a_rede(rede):
    cache: dict = {}
    primeiro = pagina.gp_da_rede(rede, cache)
    assert pagina.gp_da_rede(rede, cache) is primeiro
    outra = ler(FONTE)
    assert pagina.gp_da_rede(outra, cache) is not primeiro


def test_shell_abre_centralidades_e_calcula(monkeypatch):
    monkeypatch.setattr(app, "listar_fontes", lambda: (FONTE,))
    monkeypatch.setattr(app, "render_mapa", lambda *a, **kw: None)
    monkeypatch.setattr(pagina, "st_folium", lambda *a, **kw: None)
    at = AppTest.from_string("from transporte.interface.app import main\nmain()")
    at.run(timeout=30).button[0].click().run(timeout=30)
    at.sidebar.radio[0].set_value("Centralidades").run(timeout=30)
    assert not at.exception
    assert any(t.value == "Centralidades" for t in at.title)
    assert any("Calcular" in i.value for i in at.info)

    at.button[0].click().run(timeout=30)
    assert not at.exception
    tabela = at.dataframe[0].value
    assert tabela["Parada"].iloc[0] == "Meio (B)"
    assert "± erro padrão" not in tabela.columns  # 4 origens: o padrão cobre todas (exato)
