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

from dataclasses import replace
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
        pagina.calcular(visao, "pagerank")


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


def test_mais_centrais_gabarito_percentil():
    """Valores 1 a 20 (paradas p1..p20), fração 0,1: corte = 3º maior = 18; ficam 19 e 20."""
    intens = {f"p{i}": float(i) for i in range(1, 21)}
    assert pagina.mais_centrais(intens, 0.1) == {"p19": 19.0, "p20": 20.0}


def test_mais_centrais_empate_no_corte_sai():
    """Como no grau: muitos empatados no corte não entram, só os estritamente acima."""
    intens = {"a": 1.0, "b": 0.5, **{f"e{i}": 0.25 for i in range(18)}}
    # n = 20, posição 2 em ordem decrescente: 0,25; ficam só a e b.
    assert pagina.mais_centrais(intens, 0.1) == {"a": 1.0, "b": 0.5}


def test_mais_centrais_bordas():
    assert pagina.mais_centrais({}) == {}
    iguais = {"a": 0.5, "b": 0.5, "c": 0.5}
    assert pagina.mais_centrais(iguais) == iguais  # ninguém acima: ficam os empatados
    assert pagina.mais_centrais({"a": 1.0, "b": 0.5}) == {"a": 1.0}


def test_mapa_calor_so_com_as_mais_centrais_e_raio_menor(rede, visao):
    c = pagina.calcular(visao, pagina.SAIDA, so_viagem=True)  # A 2, B 1, C 0, D 0
    mapa = pagina.mapa_centralidades(rede, visao, c, 2)
    calor = [f for f in mapa._children.values() if type(f).__name__ == "HeatMap"]
    assert len(calor) == 1
    assert len(calor[0].data) == 1  # só A, a mais central
    assert calor[0].options["radius"] == pagina.RAIO_CALOR


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


# --- Proximidade (F-MET-2) e comunidades (F-MET-OPC) ----------------------------------
# Distâncias mínimas de G_P da rede de teste (todas por caminhada, mais curtas que a
# viagem): A: B 127, C 185, D 174 (soma 486); B: A, C, D 127 (381); C: A 185, B 127,
# D 254 por B (566); D: A 174, B 127, C 254 por B (555). Todas alcançam as outras 3:
# proximidade = 3 / soma.


def _caminhada(visao) -> dict[tuple[int, int], float]:
    """Peso de cada aresta de caminhada (os 127 s etc. acima são arredondados)."""
    g = visao.grafo
    pesos = {}
    for a in range(g.num_arestas()):
        u, v, peso, tipo = g.aresta(a)
        if tipo == "caminhada":
            pesos[(u, v)] = peso
    return pesos


def test_proximidade_exata_gabarito(visao):
    w = _caminhada(visao)
    a, b, c_, d = 0, 1, 2, 3
    somas = [
        w[a, b] + w[a, c_] + w[a, d],
        w[b, a] + w[b, c_] + w[b, d],
        w[c_, a] + w[c_, b] + w[c_, b] + w[b, d],
        w[d, a] + w[d, b] + w[d, b] + w[b, c_],
    ]
    c = pagina.calcular(visao, pagina.PROXIMIDADE, amostra=None)
    assert c.valores == pytest.approx([3 / s for s in somas])
    assert c.erros is None and "exata (4 origens)" in c.descricao


def test_proximidade_amostrada_descreve_amostra(visao):
    c = pagina.calcular(visao, pagina.PROXIMIDADE, amostra=2)
    assert "2 de 4 origens" in c.descricao


def test_tabela_ranking_proximidade(rede, visao):
    c = pagina.calcular(visao, pagina.PROXIMIDADE, amostra=None)
    linhas = pagina.tabela_ranking(rede, visao, c, 4)
    assert [linha["Parada"].split(" (")[1][0] for linha in linhas] == ["B", "A", "D", "C"]
    assert linhas[0]["Valor"] == round(c.valores[1], 6)


def test_comunidades_na_rede_de_teste(rede, visao):
    # A, B, C, D são todas vizinhas de B (não dirigido): uma comunidade só, Q = 0.
    c = pagina.calcular_comunidades(visao)
    assert c.comunidades.quantidade == 1 and c.comunidades.convergiu
    assert c.modularidade == pytest.approx(0.0)
    linhas = pagina.tabela_comunidades(rede, visao, c, 10)
    assert linhas == [
        {"Comunidade": 1, "Paradas": 4, "% das paradas": 100.0, "Exemplo": "Origem (A)"}
    ]


def test_mapa_comunidades_tem_uma_camada_por_comunidade(rede, visao):
    c = pagina.calcular_comunidades(visao)
    mapa = pagina.mapa_comunidades(rede, visao, c)
    html = mapa.get_root().render()
    assert "Comunidade 1 (4 paradas)" in html
    assert pagina.CORES_COMUNIDADES[0] in html
    assert type(list(mapa._children.values())[-1]).__name__ == "LayerControl"


def _abrir_centralidades(monkeypatch) -> AppTest:
    monkeypatch.setattr(app, "listar_fontes", lambda: (FONTE,))
    monkeypatch.setattr(app, "render_mapa", lambda *a, **kw: None)
    monkeypatch.setattr(pagina, "st_folium", lambda *a, **kw: None)
    at = AppTest.from_string("from transporte.interface.app import main\nmain()")
    at.run(timeout=30).button[0].click().run(timeout=30)
    at.sidebar.radio[0].set_value("Centralidades").run(timeout=30)
    return at


def _botao(at: AppTest, rotulo: str):
    return next(b for b in at.button if b.label == rotulo)


def test_shell_calcula_proximidade(monkeypatch):
    at = _abrir_centralidades(monkeypatch)
    metrica = next(r for r in at.radio if "Proximidade (Wasserman-Faust)" in r.options)
    metrica.set_value(pagina.PROXIMIDADE)
    _botao(at, "Calcular").click().run(timeout=30)
    assert not at.exception
    assert at.dataframe[0].value["Parada"].iloc[0] == "Meio (B)"
    assert any("Proximidade exata" in c.value for c in at.caption)


def test_shell_detecta_comunidades(monkeypatch):
    at = _abrir_centralidades(monkeypatch)
    _botao(at, "Detectar comunidades").click().run(timeout=30)
    assert not at.exception
    valores = {m.label: m.value for m in at.metric}
    assert valores["Comunidades"] == "1"
    assert valores["Modularidade"] == "0.000"
    assert at.dataframe[0].value["Paradas"].iloc[0] == 4

def test_proximidade_e_comunidades_em_rede_com_uma_parada(monkeypatch):
    monkeypatch.setattr(pagina, "st_folium", lambda *a, **kw: None)
    at = AppTest.from_string(
        "import streamlit as st\n"
        "from transporte.interface.paginas.centralidades import render\n"
        "render(st.session_state.rede)\n"
    )
    rede = ler(FONTE)
    at.session_state["rede"] = replace(
        rede, paradas={"A": rede.paradas["A"]}, padroes={}, viagens={}
    )
    at.run()
    assert not at.exception

    at.radio[0].set_value(pagina.PROXIMIDADE)
    _botao(at, "Calcular").click().run()
    assert not at.exception
    assert at.dataframe[0].value["Valor"].tolist() == [0.0]

    _botao(at, "Detectar comunidades").click().run()
    assert not at.exception
    assert at.dataframe[1].value["Paradas"].tolist() == [1]
