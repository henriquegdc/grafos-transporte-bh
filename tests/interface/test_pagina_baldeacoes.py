"""Testes da página Baldeações (F-BALD, RF-BAL-02): cache da G_L, tabela, resumo e mapa.

Rede mínima com os campos do contrato da interface e de RedeConstrutores. Paradas a 0,01
grau (1,1 km) umas das outras, sem caminhada: L1 = A -> B, L2 = B -> C, ambas às 07h.
"""

from __future__ import annotations

from dataclasses import dataclass

import folium
import pytest
from streamlit.testing.v1 import AppTest

from transporte.algoritmos.baldeacoes import menos_baldeacoes
from transporte.interface.paginas import baldeacoes

LAT0, LON0 = -19.92, -43.94
H7 = 7 * 3600


@dataclass(frozen=True)
class Parada:
    id: str
    nome: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Linha:
    id: str
    nome: str


@dataclass(frozen=True)
class Padrao:
    id: str
    linha_id: str
    paradas: tuple[str, ...]


@dataclass
class Rede:
    paradas: dict[str, Parada]
    linhas: dict[str, Linha]
    padroes: dict[str, Padrao]
    viagens: dict[str, list[list[int]]]


def _rede() -> Rede:
    paradas = {
        pid: Parada(pid, nome, LAT0 + k / 100, LON0)
        for k, (pid, nome) in enumerate((("A", "Origem"), ("B", "Troca"), ("C", "Destino")))
    }
    return Rede(
        paradas,
        {"L1": Linha("L1", "Linha 1"), "L2": Linha("L2", "Linha 2")},
        {"P1": Padrao("P1", "L1", ("A", "B")), "P2": Padrao("P2", "L2", ("B", "C"))},
        {"P1": [[H7, H7 + 300]], "P2": [[H7 + 600, H7 + 900]]},
    )


@pytest.fixture
def rede() -> Rede:
    return _rede()


def _descendentes(elemento) -> list:
    resultado = [elemento]
    for filho in getattr(elemento, "_children", {}).values():
        resultado.extend(_descendentes(filho))
    return resultado


def test_gl_monta_uma_vez_por_rede_e_faixa(rede: Rede) -> None:
    cache: dict = {}
    gl = baldeacoes.gl_da_faixa(rede, baldeacoes.DIA_INTEIRO, cache)
    assert gl.faixa is None
    assert baldeacoes.gl_da_faixa(rede, baldeacoes.DIA_INTEIRO, cache) is gl
    pico = baldeacoes.gl_da_faixa(rede, "pico_manha", cache)
    assert pico is not gl and pico.faixa == "pico_manha"
    outra = _rede()
    assert baldeacoes.gl_da_faixa(outra, "pico_manha", cache) is not pico
    assert set(cache[baldeacoes.CHAVE_GL]["gls"]) == {"pico_manha"}  # a rede anterior saiu


def test_tabela_e_resumo(rede: Rede) -> None:
    gl = baldeacoes.gl_da_faixa(rede, baldeacoes.DIA_INTEIRO, {})
    t = menos_baldeacoes(gl, "A", "C")
    assert baldeacoes.resumo_linhas(rede, t) == "Linha 1 → Linha 2"
    assert baldeacoes.tabela_trechos(rede, t) == [
        {
            "Trecho": "1",
            "Modo": "Ônibus",
            "Linha": "Linha 1",
            "De": "Origem (A)",
            "Para": "Troca (B)",
            "Paradas": "1",
        },
        {
            "Trecho": "2",
            "Modo": "Ônibus",
            "Linha": "Linha 2",
            "De": "Troca (B)",
            "Para": "Destino (C)",
            "Paradas": "1",
        },
    ]


def test_linha_do_padrao_cai_para_ids(rede: Rede) -> None:
    assert baldeacoes.linha_do_padrao(rede, None) == ""
    assert baldeacoes.linha_do_padrao(rede, "inexistente") == "inexistente"
    rede.linhas.pop("L1")
    assert baldeacoes.linha_do_padrao(rede, "P1") == "L1"


def test_mapa_tem_um_traco_por_trecho_e_um_marcador_por_troca(rede: Rede) -> None:
    gl = baldeacoes.gl_da_faixa(rede, baldeacoes.DIA_INTEIRO, {})
    t = menos_baldeacoes(gl, "A", "C")
    mapa = baldeacoes.mapa_trajeto(rede, t)
    elementos = _descendentes(mapa)
    linhas = [e for e in elementos if isinstance(e, folium.PolyLine)]
    trocas = [e for e in elementos if isinstance(e, folium.CircleMarker)]
    marcadores = [e for e in elementos if type(e) is folium.Marker]
    assert len(linhas) == 2
    assert len({e.options["color"] for e in linhas}) == 2  # uma cor por linha
    assert len(trocas) == 1
    assert trocas[0].location == [rede.paradas["B"].lat, rede.paradas["B"].lon]
    assert len(marcadores) == 2  # origem e destino
    html = mapa.get_root().render()
    assert "Troca 1: desce em Troca (B)" in html


def test_controle_de_camadas_vem_depois_das_camadas(rede: Rede) -> None:
    # Se o controle vier antes, ele cita camadas ainda não criadas e o Leaflet para com
    # "Cannot read properties of undefined (reading 'setZIndex')": o trajeto não aparece.
    gl = baldeacoes.gl_da_faixa(rede, baldeacoes.DIA_INTEIRO, {})
    mapa = baldeacoes.mapa_trajeto(rede, menos_baldeacoes(gl, "A", "C"))
    html = mapa.get_root().render()
    controle = html.index("L.control.layers(")
    camadas = [e.get_name() for e in _descendentes(mapa) if isinstance(e, folium.FeatureGroup)]
    assert camadas
    assert all(html.index(f"var {nome} = ") < controle for nome in camadas)


def _script_da_pagina(com_lenta: bool = False) -> None:
    # Roda dentro do AppTest: monta a rede e chama render, como o app.py faz. Com
    # `com_lenta`, acrescenta a linha direta LENTA A -> C (40 min) para a F-BALD-2.
    from dataclasses import dataclass

    from transporte.interface.paginas import baldeacoes

    @dataclass(frozen=True)
    class Parada:
        id: str
        nome: str
        lat: float
        lon: float

    @dataclass(frozen=True)
    class Linha:
        id: str
        nome: str

    @dataclass(frozen=True)
    class Padrao:
        id: str
        linha_id: str
        paradas: tuple

    @dataclass
    class Rede:
        paradas: dict
        linhas: dict
        padroes: dict
        viagens: dict

    h7 = 7 * 3600
    paradas = {
        pid: Parada(pid, nome, -19.92 + k / 100, -43.94)
        for k, (pid, nome) in enumerate((("A", "Origem"), ("B", "Troca"), ("C", "Destino")))
    }
    rede = Rede(
        paradas,
        {"L1": Linha("L1", "Linha 1"), "L2": Linha("L2", "Linha 2")},
        {"P1": Padrao("P1", "L1", ("A", "B")), "P2": Padrao("P2", "L2", ("B", "C"))},
        {"P1": [[h7, h7 + 300]], "P2": [[h7 + 600, h7 + 900]]},
    )
    if com_lenta:
        rede.linhas["L3"] = Linha("L3", "Linha Lenta")
        rede.padroes["LENTA"] = Padrao("LENTA", "L3", ("A", "C"))
        rede.viagens["LENTA"] = [[h7, h7 + 2400]]
    baldeacoes.render(rede)


def test_render_mostra_baldeacoes_e_sem_trajeto() -> None:
    app = AppTest.from_function(_script_da_pagina).run(timeout=30)
    assert not app.exception
    # Padrão: origem "Destino (C)" (ordem alfabética dos nomes) e destino "Origem (A)": não
    # há linha de C para A.
    assert app.warning and "Sem trajeto" in app.warning[0].value
    app.selectbox(key="f-bald-origem").set_value("A")
    app.selectbox(key="f-bald-destino").set_value("C")
    app.run(timeout=30)
    assert not app.exception
    metricas = {m.label: m.value for m in app.metric}
    assert metricas["Baldeações"] == "1" and metricas["Ônibus"] == "2"
    assert any("Linha 1 → Linha 2" in m.value for m in app.markdown)


# --- F-BALD-2 (RF-BAL-03): menos baldeações contra mais rápido -------------------------


def _rede_com_lenta() -> Rede:
    rede = _rede()
    rede.linhas["L3"] = Linha("L3", "Linha Lenta")
    rede.padroes["LENTA"] = Padrao("LENTA", "L3", ("A", "C"))
    rede.viagens["LENTA"] = [[H7, H7 + 2400]]
    return rede


def test_ge_monta_uma_vez_por_rede_e_faixa(rede: Rede) -> None:
    cache: dict = {}
    ge = baldeacoes.ge_da_faixa(rede, "pico_manha", cache)
    assert ge.faixa == "pico_manha"
    assert baldeacoes.ge_da_faixa(rede, "pico_manha", cache) is ge
    outra = _rede()
    assert baldeacoes.ge_da_faixa(outra, "pico_manha", cache) is not ge
    assert set(cache[baldeacoes.CHAVE_GE]["ges"]) == {"pico_manha"}


def test_tabela_comparacao() -> None:
    from transporte.algoritmos.comparacao_baldeacoes import comparar_baldeacoes

    rede = _rede_com_lenta()
    cache: dict = {}
    gl = baldeacoes.gl_da_faixa(rede, "pico_manha", cache)
    ge = baldeacoes.ge_da_faixa(rede, "pico_manha", cache)
    # Uma partida por padrão: espera provisória de 300 s (F-ESPERA). Mais rápido: L1 + L2 =
    # 300 + 300 + 300 + 300 = 1200 s. Com 0 baldeação: LENTA = 300 + 2400 = 2700 s.
    c = comparar_baldeacoes(ge, gl, "A", "C")
    assert (c.tempo_a_mais_s, c.baldeacoes_evitadas) == (1500.0, 1)
    assert baldeacoes.tabela_comparacao(rede, c) == [
        {
            "Trajeto": "Mais rápido",
            "Tempo total": "20.0 min",
            "A pé": "0.0 min",
            "Espera": "10.0 min",
            "Ônibus": "10.0 min",
            "Baldeações": "1",
            "Linhas": "Linha 1 → Linha 2",
        },
        {
            "Trajeto": "Mais rápido com até 0 baldeação(ões)",
            "Tempo total": "45.0 min",
            "A pé": "0.0 min",
            "Espera": "5.0 min",
            "Ônibus": "40.0 min",
            "Baldeações": "0",
            "Linhas": "Linha Lenta",
        },
    ]


def test_render_compara_so_numa_faixa() -> None:
    app = AppTest.from_function(_script_da_pagina, kwargs={"com_lenta": True})
    app.run(timeout=30)
    app.selectbox(key="f-bald-origem").set_value("A")
    app.selectbox(key="f-bald-destino").set_value("C")
    app.run(timeout=30)
    assert not app.exception
    # Dia inteiro (o padrão): sem G_E, a página pede uma faixa.
    assert any("Escolha uma faixa" in i.value for i in app.info)
    app.selectbox[0].set_value("pico_manha")
    app.run(timeout=30)
    assert not app.exception
    metricas = {m.label: m.value for m in app.metric}
    assert metricas["Baldeações"] == "0"  # F-BALD: a LENTA direta
    assert metricas["Tempo a mais"] == "25.0 min"
    assert metricas["Baldeações evitadas"] == "1"
    assert metricas["Por baldeação evitada"] == "25.0 min"
    assert len(app.dataframe) == 2  # trechos da F-BALD e a comparação
