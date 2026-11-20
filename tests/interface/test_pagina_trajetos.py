"""Testes da página Trajetos (F-ROTA, RF-ROT-02): cache do G_E, tabela, mapa e render.

Usa a `dados/rede-teste/` lida por `ler()`, com as paradas afastadas 0,01 grau (1,1 km)
umas das outras para obrigar o ônibus: no pico da manhã, A -> C pela L1 tem 600 s de espera
(partidas a cada 1200 s, espera H/2) e 600 s de viagem; a L2 só parte a partir das 09h.
"""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import folium
import pytest
from streamlit.testing.v1 import AppTest

from transporte.algoritmos.alternativos import Alternativo
from transporte.algoritmos.trajeto import trajeto_mais_rapido
from transporte.dados.leitor_gtfs import ler
from transporte.dados.modelo import Parada
from transporte.interface import app
from transporte.interface.paginas import trajetos
from transporte.modelo.parametros import Parametros

FONTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"


def _rede_afastada():
    rede = ler(FONTE)
    rede.paradas = {
        pid: Parada(pid, p.nome, -19.9 + k / 100, -43.9)
        for k, (pid, p) in enumerate(rede.paradas.items())
    }
    return rede


@pytest.fixture
def rede():
    return _rede_afastada()


def _trajeto_a_c(rede):
    preparado = trajetos.ge_da_faixa(rede, "pico_manha", Parametros(), {})
    return trajeto_mais_rapido(preparado.ge, "A", "C")


def _descendentes(elemento) -> list:
    resultado = [elemento]
    for filho in getattr(elemento, "_children", {}).values():
        resultado.extend(_descendentes(filho))
    return resultado


def test_ge_monta_uma_vez_por_rede_e_faixa(rede) -> None:
    cache: dict = {}
    params = Parametros()
    ge = trajetos.ge_da_faixa(rede, "pico_manha", params, cache)
    assert trajetos.ge_da_faixa(rede, "pico_manha", params, cache) is ge
    assert len(ge.coords) == ge.ge.grafo.num_vertices() and ge.vmax > 0
    entrepico = trajetos.ge_da_faixa(rede, "entrepico", params, cache)
    assert entrepico is not ge and entrepico.ge.faixa == "entrepico"
    outra = _rede_afastada()
    assert trajetos.ge_da_faixa(outra, "entrepico", params, cache) is not entrepico
    assert set(cache[trajetos.CHAVE_GE]["ges"]) == {"entrepico"}  # a rede anterior saiu


def test_ge_usa_a_espera_da_f_espera(rede) -> None:
    # Sem as esperas da F-ESPERA o embarque valeria a espera padrão (300 s), não H/2 = 600 s.
    t = _trajeto_a_c(rede)
    assert t.tempo_total_s == 1200


def test_tabela_por_trecho(rede) -> None:
    assert trajetos.tabela_trechos(rede, _trajeto_a_c(rede)) == [
        {
            "Trecho": "1",
            "Modo": "Espera",
            "Linha": "Linha 1",
            "De": "Origem (A)",
            "Para": "Origem (A)",
            "Paradas": "",
            "Tempo": "10 min 00 s",
        },
        {
            "Trecho": "2",
            "Modo": "Ônibus",
            "Linha": "Linha 1",
            "De": "Origem (A)",
            "Para": "Destino (C)",
            "Paradas": "2",
            "Tempo": "10 min 00 s",
        },
    ]


@pytest.mark.parametrize(
    ("segundos", "texto"),
    [(0, "0 min 00 s"), (59.6, "1 min 00 s"), (185.3, "3 min 05 s"), (3725, "62 min 05 s")],
)
def test_minutos(segundos, texto) -> None:
    assert trajetos.minutos(segundos) == texto


def test_mapa_tem_espera_onibus_origem_e_destino(rede) -> None:
    mapa = trajetos.mapa_trajeto(rede, _trajeto_a_c(rede))
    elementos = _descendentes(mapa)
    assert len([e for e in elementos if isinstance(e, folium.PolyLine)]) == 1  # o ônibus
    assert len([e for e in elementos if isinstance(e, folium.CircleMarker)]) == 1  # a espera
    assert len([e for e in elementos if type(e) is folium.Marker]) == 2  # origem e destino
    html = mapa.get_root().render()
    assert "Ônibus · Linha 1 · 10 min 00 s" in html
    # Controle de camadas depois de todas as camadas (ver mapa.atualizar_controle_camadas).
    controle = html.index("L.control.layers(")
    camadas = [e.get_name() for e in elementos if isinstance(e, folium.FeatureGroup)]
    assert camadas and all(html.index(f"var {nome} = ") < controle for nome in camadas)
    # Enquadra A e C, não a rede inteira (D fica em -19,87).
    (ajuste,) = [e for e in elementos if type(e).__name__ == "FitBounds"]
    assert ajuste.bounds == [[-19.9, -43.9], [-19.88, -43.9]]


@pytest.fixture
def pagina():
    at = AppTest.from_string(
        "import streamlit as st\n"
        "from transporte.interface.paginas.trajetos import render\n"
        "render(st.session_state['rede'])"
    )
    at.session_state["rede"] = _rede_afastada()
    return at.run(timeout=30)


def test_render_sem_trajeto_e_com_trajeto(pagina) -> None:
    assert not pagina.exception
    # Padrão: origem "Destino (C)" e destino "Desvio (D)" (ordem dos nomes): sem ligação.
    assert pagina.warning and "Sem trajeto" in pagina.warning[0].value
    pagina.selectbox(key="f-rota-origem").set_value("A")
    pagina.selectbox(key="f-rota-destino").set_value("C")
    pagina.run(timeout=30)
    assert not pagina.exception
    metricas = {m.label: m.value for m in pagina.metric}
    assert metricas == {
        "Tempo total": "20 min 00 s",
        "A pé": "0 min 00 s",
        "Espera": "10 min 00 s",
        "Ônibus": "10 min 00 s",
        "Baldeações": "0",
    }
    assert len(pagina.dataframe[0].value) == 2


def test_render_mesma_parada(pagina) -> None:
    pagina.selectbox(key="f-rota-origem").set_value("A")
    pagina.selectbox(key="f-rota-destino").set_value("A")
    pagina.run(timeout=30)
    assert not pagina.exception
    assert any("mesma parada" in i.value for i in pagina.info)


def test_render_compara_dijkstra_e_a_estrela(pagina) -> None:
    pagina.selectbox(key="f-rota-origem").set_value("A")
    pagina.selectbox(key="f-rota-destino").set_value("C")
    pagina.run(timeout=30)
    comparacao = pagina.dataframe[1].value
    assert list(comparacao["Algoritmo"]) == ["Dijkstra", "A*"]
    assert list(comparacao["Tempo do trajeto"]) == ["20 min 00 s", "20 min 00 s"]
    assert int(comparacao["Vértices expandidos"][1]) <= int(comparacao["Vértices expandidos"][0])


def test_render_lista_alternativos_no_botao(pagina) -> None:
    pagina.selectbox(key="f-rota-origem").set_value("A")
    pagina.selectbox(key="f-rota-destino").set_value("C")
    pagina.run(timeout=30)
    assert len(pagina.dataframe) == 2  # trechos e comparação; o Yen espera o botão
    pagina.button(key="f-rota-yen").click().run(timeout=30)
    assert not pagina.exception
    alternativos = pagina.dataframe[2].value
    # Sem caminhada (paradas a 1,1 km), só a L1 liga A a C: um trajeto só.
    assert list(alternativos["Tempo total"]) == ["20 min 00 s"]
    assert list(alternativos["Linhas"]) == ["Linha 1"]
    assert list(alternativos["Variantes"]) == ["1"]
    assert "Tempo porta a porta" not in alternativos.columns
    # Mudar a consulta esconde o resultado antigo.
    pagina.selectbox(key="f-rota-destino").set_value("B")
    pagina.run(timeout=30)
    assert len(pagina.dataframe) == 2


def test_render_por_coordenadas_liga_as_paradas_e_soma_o_acesso(pagina) -> None:
    pagina.radio(key="f-rota-modo").set_value(trajetos.MODO_PONTO).run(timeout=30)
    assert not pagina.exception
    # 0,001 grau ao sul de A (111 m) e 0,001 grau ao norte de C.
    pagina.number_input(key="f-rota-lat-origem").set_value(-19.901)
    pagina.number_input(key="f-rota-lon-origem").set_value(-43.9)
    pagina.number_input(key="f-rota-lat-destino").set_value(-19.879)
    pagina.number_input(key="f-rota-lon-destino").set_value(-43.9)
    pagina.run(timeout=30)
    assert not pagina.exception
    metricas = {m.label: m.value for m in pagina.metric}
    assert metricas["Tempo total"] == "20 min 00 s"
    # 1200 s entre as paradas + 2 x 111,19 m / 1,2 m/s (92,7 s cada) = 1385 s.
    assert metricas["Tempo porta a porta"] == "23 min 05 s"
    assert any("Origem (A), a 111 m" in c.value for c in pagina.caption)


def test_aplicar_clique_so_uma_vez() -> None:
    estado: dict = {}
    assert not trajetos.aplicar_clique(estado, None, trajetos.ORIGEM)
    assert trajetos.aplicar_clique(estado, {"lat": -19.9, "lng": -43.9}, trajetos.DESTINO)
    assert (estado["f-rota-lat-destino"], estado["f-rota-lon-destino"]) == (-19.9, -43.9)
    estado["f-rota-lat-destino"] = -19.95  # digitado depois do clique
    assert not trajetos.aplicar_clique(estado, {"lat": -19.9, "lng": -43.9}, trajetos.DESTINO)
    assert estado["f-rota-lat-destino"] == -19.95


def test_ligar_ponto_e_mapa_com_acesso(rede) -> None:
    params = Parametros()
    ponto = trajetos.ligar_ponto(rede, -19.901, -43.9, params)
    assert ponto.parada == "A"
    assert ponto.caminhada_s == pytest.approx(ponto.distancia_m / params.velocidade_caminhada_ms)
    destino = trajetos.ligar_ponto(rede, -19.879, -43.9, params)
    mapa = trajetos.mapa_trajeto(rede, _trajeto_a_c(rede), (ponto, destino))
    elementos = _descendentes(mapa)
    # O ônibus e as duas caminhadas de acesso.
    assert len([e for e in elementos if isinstance(e, folium.PolyLine)]) == 3
    (ajuste,) = [e for e in elementos if type(e).__name__ == "FitBounds"]
    assert ajuste.bounds == [[-19.901, -43.9], [-19.879, -43.9]]


def test_tabela_alternativos(rede) -> None:
    alt = Alternativo(_trajeto_a_c(rede), ("L1",), 3)
    assert trajetos.tabela_alternativos(rede, [alt]) == [
        {
            "Trajeto": "1",
            "Tempo total": "20 min 00 s",
            "Baldeações": "0",
            "Linhas": "Linha 1",
            "A pé": "0 min 00 s",
            "Variantes": "3",
        }
    ]
    (com_acesso,) = trajetos.tabela_alternativos(rede, [alt], acesso_s=65)
    assert com_acesso["Tempo total"] == "20 min 00 s"
    assert com_acesso["Tempo porta a porta"] == "21 min 05 s"


def test_comparacao_guardada_por_consulta(rede, monkeypatch) -> None:
    preparado = trajetos.ge_da_faixa(rede, "pico_manha", Parametros(), {})
    chamadas = []
    original = trajetos.comparar

    def contar(*args):
        chamadas.append(args[-2:])
        return original(*args)

    monkeypatch.setattr(trajetos, "comparar", contar)
    cache: dict = {}
    c = trajetos.comparacao_em_cache(rede, preparado, "pico_manha", "A", "C", cache)
    assert trajetos.comparacao_em_cache(rede, preparado, "pico_manha", "A", "C", cache) is c
    trajetos.comparacao_em_cache(rede, preparado, "pico_manha", "A", "B", cache)
    assert chamadas == [("A", "C"), ("A", "B")]


def test_longe_da_rede(rede) -> None:
    params = Parametros()
    assert not trajetos.longe_da_rede(trajetos.ligar_ponto(rede, -19.901, -43.9, params), params)
    # 0,01 grau a oeste de A: cerca de 1 km, além do raio de caminhada.
    assert trajetos.longe_da_rede(trajetos.ligar_ponto(rede, -19.9, -43.91, params), params)


def test_render_avisa_ponto_longe_e_alternativos_porta_a_porta(pagina) -> None:
    pagina.radio(key="f-rota-modo").set_value(trajetos.MODO_PONTO).run(timeout=30)
    pagina.number_input(key="f-rota-lat-origem").set_value(-19.9)
    pagina.number_input(key="f-rota-lon-origem").set_value(-43.91)
    pagina.number_input(key="f-rota-lat-destino").set_value(-19.879)
    pagina.number_input(key="f-rota-lon-destino").set_value(-43.9)
    pagina.run(timeout=30)
    assert not pagina.exception
    assert any("origem está a" in w.value for w in pagina.warning)
    pagina.button(key="f-rota-yen").click().run(timeout=30)
    assert not pagina.exception
    alternativos = pagina.dataframe[2].value
    assert list(alternativos["Tempo total"]) == ["20 min 00 s"]
    assert "Tempo porta a porta" in alternativos.columns


@pytest.mark.parametrize("zipado", [False, True])
def test_shell_abre_trajetos_apos_carregar_dataset(tmp_path, monkeypatch, zipado) -> None:
    origem = FONTE
    if zipado:
        origem = tmp_path / "rede.zip"
        with ZipFile(origem, "w") as arquivo:
            for caminho in FONTE.glob("*.txt"):
                arquivo.write(caminho, caminho.name)
    monkeypatch.setattr(app, "listar_fontes", lambda: (origem,))
    monkeypatch.setattr(app, "render_mapa", lambda *a, **kw: None)
    at = AppTest.from_string("from transporte.interface.app import main\nmain()")
    at.run(timeout=30).button[0].click().run(timeout=30)
    at.sidebar.radio[0].set_value("Trajetos").run(timeout=30)
    assert not at.exception
    assert any(h.value == "Trajeto mais rápido" for h in at.header)
    assert not any("ainda não foi implementada" in i.value for i in at.info)
