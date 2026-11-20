"""Página Falhas (F-RES) na rede de teste.

Gabarito à mão de G_P da rede de teste (paradas A, B, C, D; vértices 0 a 3), o mesmo do
teste da página Centralidades:
    viagem: A -> B (300 s, linha L1), B -> C (300 s, L1), A -> D (480 s, L2);
    caminhada nos dois sentidos: A-B 127 s, B-C 127 s, B-D 127 s, A-D 174 s, A-C 185 s.
A caminhada liga todas as paradas, então G_P é uma componente só e nenhuma falha isolada
desconecta parada nesta rede. Os casos com paradas isoladas e desconectadas no mapa usam um
ResultadoFalha montado à mão.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from transporte.dados.leitor_gtfs import ler
from transporte.interface import app
from transporte.interface.paginas import falhas as pagina
from transporte.simulacao.falhas import Falha, ResultadoFalha

FONTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"


@pytest.fixture(scope="module")
def rede():
    return ler(FONTE)


@pytest.fixture(scope="module")
def preparado(rede):
    return pagina.preparar(rede, {})


def test_seguintes_gabarito(preparado):
    _visao, _indice, proximas = preparado
    assert proximas == {"A": ["B", "D"], "B": ["C"]}


def test_preparar_reaproveita_e_troca_com_a_rede(rede):
    cache: dict = {}
    primeiro = pagina.preparar(rede, cache)
    assert pagina.preparar(rede, cache)[0] is primeiro[0]
    assert pagina.preparar(ler(FONTE), cache)[0] is not primeiro[0]


def test_linhas_com_trecho_e_nomes(rede, preparado):
    _visao, indice, _proximas = preparado
    assert pagina.linhas_com_trecho(rede, indice) == ["L1", "L2"]
    texto = pagina.descrever(rede, Falha(paradas=("B",), trechos=(("A", "D"),), linhas=("L1",)))
    assert texto == (
        "parada Meio (B), trecho Origem (A) → Desvio (D), linha Linha 1 (L1)"
    )
    assert pagina.descrever(rede, Falha()) == "nenhuma"


def test_remover_parada_do_meio(preparado):
    # Sem B, C -> D passa a ir por A a pé: 185 + 174 = 359 s, contra 254 s por B.
    visao, indice, _ = preparado
    resultado, segundos = pagina.simular(visao, Falha(paradas=("B",)), indice, amostra=None)
    numeros = pagina.resumo(resultado)
    assert numeros["componentes_antes"] == numeros["componentes_depois"] == 1
    assert (numeros["maior_antes"], numeros["maior_depois"]) == (4, 3)
    assert numeros["isoladas"] == numeros["desconectadas"] == 0
    assert numeros["perda"] > 0
    assert segundos >= 0


def test_remover_linha_que_a_caminhada_cobre_nao_perde_nada(preparado):
    # A L2 só tem o trecho A -> D (480 s); a caminhada A -> D leva 174 s, então nenhuma
    # distância muda e a perda é exatamente 0.
    visao, indice, _ = preparado
    resultado, _ = pagina.simular(visao, Falha(linhas=("L2",)), indice, amostra=None)
    assert resultado.perda_eficiencia == 0.0
    assert len(resultado.arestas_desativadas) == 1


def _resultado_a_mao(visao) -> ResultadoFalha:
    """B removida e o trecho A -> D fora; C isolada e D fora da rede principal."""
    a_d = next(
        a for a in range(visao.grafo.num_arestas())
        if visao.grafo.aresta(a)[:2] == (0, 3) and visao.grafo.aresta(a)[3] == "viagem"
    )
    return ResultadoFalha(
        falha=Falha(paradas=("B",), trechos=(("A", "D"),)),
        componentes_antes=[[0, 1, 2, 3]],
        componentes_depois=[[2], [3, 0]],
        paradas_isoladas=["C"],
        paradas_desconectadas=["C"],
        eficiencia_antes=1.0,
        eficiencia_depois=0.5,
        perda_eficiencia=0.5,
        vertices_desativados=[1],
        arestas_desativadas=[a_d],
    )


def test_tabela_afetadas(rede, preparado):
    r = _resultado_a_mao(preparado[0])
    assert pagina.tabela_afetadas(rede, r) == [
        {"Parada": "Destino (C)", "Situação": "isolada"}
    ]
    r.paradas_desconectadas = ["C", "D"]
    assert pagina.tabela_afetadas(rede, r)[1] == {
        "Parada": "Desvio (D)", "Situação": "fora da rede principal"
    }


def test_mapa_tem_camadas_e_controle_por_ultimo(rede, preparado):
    visao = preparado[0]
    r = _resultado_a_mao(visao)
    r.paradas_desconectadas = ["C", "D"]
    mapa = pagina.mapa_falha(rede, visao, r)
    html = mapa.get_root().render()
    assert "Removida: Meio (B)" in html
    assert "Trecho removido: Origem (A) → Desvio (D)" in html
    assert "Isolada: Destino (C)" in html
    assert "Fora da rede principal: Desvio (D)" in html
    nomes = {getattr(f, "layer_name", None) for f in mapa._children.values()}
    assert {"Removido pela falha", "Isoladas", "Fora da rede principal"} <= nomes
    assert type(list(mapa._children.values())[-1]).__name__ == "LayerControl"


def test_shell_abre_falhas_e_simula(monkeypatch):
    monkeypatch.setattr(app, "listar_fontes", lambda: (FONTE,))
    monkeypatch.setattr(app, "render_mapa", lambda *a, **kw: None)
    monkeypatch.setattr(pagina, "st_folium", lambda *a, **kw: None)
    at = AppTest.from_string("from transporte.interface.app import main\nmain()")
    at.run(timeout=30).button[0].click().run(timeout=30)
    at.sidebar.radio[0].set_value("Falhas").run(timeout=30)
    assert not at.exception
    assert any(t.value == "Falhas" for t in at.title)
    assert any("Simular falha" in i.value for i in at.info)

    at.multiselect[0].set_value(["B"]).run(timeout=30)
    [botao] = [b for b in at.button if b.label == "Simular falha"]
    botao.click().run(timeout=30)
    assert not at.exception
    rotulos = {m.label: m.value for m in at.metric}
    assert rotulos["Componentes fortemente conexas"] == "1"
    assert rotulos["Maior componente (paradas)"] == "3"
    assert rotulos["Paradas isoladas"] == "0"
    assert any("Nenhuma parada perdeu" in s.value for s in at.success)


# --- F-RES-2 e F-RES-OPC -----------------------------------------------------------------


def test_tabela_ranking_e_curva(rede, preparado):
    visao, _indice, _ = preparado
    r = _resultado_a_mao(visao)
    linha = Falha(linhas=("L1",))
    tabela = pagina.tabela_ranking(rede, [r, replace(r, falha=linha, perda_eficiencia=0.25)])
    assert tabela[0]["Tipo"] == "Parada" and tabela[0]["Sai de operação"] == "Meio (B)"
    assert tabela[0]["Perda de eficiência"] == "50.0000%"
    assert tabela[1]["Tipo"] == "Linha" and tabela[1]["Posição"] == 2
    assert pagina.curva_eficiencia([r, replace(r, perda_eficiencia=0.75)]) == [1.0, 0.5, 0.25]
    assert pagina.curva_eficiencia([]) == [1.0]
    passos = pagina.tabela_passos(rede, [r])
    assert passos[0]["Falhas"] == 1 and passos[0]["Isoladas"] == 1


def test_custo_estimado():
    # 3 candidatos, 10 origens: 4 eficiências de 10 Dijkstras, mais 50 do Brandes.
    assert pagina.dijkstras_ranking(3, 10, 50, n_paradas=2) == 90
    assert pagina.dijkstras_ranking(3, 10, 50, n_paradas=0) == 40
    assert pagina.dijkstras_ranking(0, 10, 50, n_paradas=0) == 0


def test_segundos_por_dijkstra_em_cache(rede, preparado):
    cache: dict = {}
    t = pagina.segundos_por_dijkstra(rede, preparado[0], cache)
    assert t > 0
    assert pagina.segundos_por_dijkstra(rede, preparado[0], cache) == t


def _abrir_falhas(monkeypatch) -> AppTest:
    monkeypatch.setattr(app, "listar_fontes", lambda: (FONTE,))
    monkeypatch.setattr(app, "render_mapa", lambda *a, **kw: None)
    monkeypatch.setattr(pagina, "st_folium", lambda *a, **kw: None)
    at = AppTest.from_string("from transporte.interface.app import main\nmain()")
    at.run(timeout=30).button[0].click().run(timeout=30)
    at.sidebar.radio[0].set_value("Falhas").run(timeout=30)
    assert not at.exception
    return at


def test_aba_ranking(monkeypatch):
    at = _abrir_falhas(monkeypatch)
    assert [t.label for t in at.tabs] == ["Falha única", "Ranking", "Falhas múltiplas"]
    assert any("Custo estimado" in c.value for c in at.caption)
    [botao] = [b for b in at.button if b.label == "Calcular ranking"]
    botao.click().run(timeout=30)
    assert not at.exception
    tabela = at.dataframe[0].value
    # 4 paradas (todas, rede de teste) e 2 linhas; B, o meio, lidera.
    assert len(tabela) == 6
    assert tabela.iloc[0]["Sai de operação"] == "Meio (B)"
    perdas = [float(p.rstrip("%")) for p in tabela["Perda de eficiência"]]
    assert perdas == sorted(perdas, reverse=True)


def test_aba_falhas_multiplas(monkeypatch):
    at = _abrir_falhas(monkeypatch)
    at.multiselect(key="multiplas-paradas").set_value(["B", "C"]).run(timeout=30)
    [botao] = [b for b in at.button if b.label == "Simular sequência"]
    botao.click().run(timeout=30)
    assert not at.exception
    tabela = at.dataframe[0].value
    assert list(tabela["Falhas"]) == [1, 2]
    assert len(at.get("vega_lite_chart")) == 1

    [modo] = [r for r in at.radio if r.label == "Modo"]
    modo.set_value(pagina.MODO_COMPARACAO).run(timeout=30)
    [botao] = [b for b in at.button if b.label == "Comparar remoções"]
    botao.click().run(timeout=30)
    assert not at.exception
    assert len(at.get("vega_lite_chart")) == 1
