"""Testes da página Trajetos (F-ROTA, RF-ROT-02): cache do G_E, tabela e mapa.

Rede mínima com os campos do contrato da interface e de RedeConstrutores: três paradas em
linha (0,001 grau de latitude = 111 m), L1 = A -> B -> C partindo às 07h, e D a 111 m de C
só com caminhada. Espera provisória de 300 s.
"""

from __future__ import annotations

from dataclasses import dataclass

import folium
import pytest

from transporte.algoritmos.trajeto import A_PE, ESPERA, ONIBUS, trajeto_mais_rapido
from transporte.interface.paginas import trajetos

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
        pid: Parada(pid, nome, LAT0 + norte / 1000, LON0)
        for pid, nome, norte in (
            ("A", "Origem", 0),
            ("B", "Meio", 5),
            ("C", "Destino", 10),
            ("D", "Vizinha", 11),
        )
    }
    return Rede(
        paradas,
        {"L1": Linha("L1", "Linha 1")},
        {"P1": Padrao("P1", "L1", ("A", "B", "C"))},
        {"P1": [[H7, H7 + 600, H7 + 1200], [H7 + 900, H7 + 1500, H7 + 2100]]},
    )


@pytest.fixture
def rede() -> Rede:
    return _rede()


def _descendentes(elemento: folium.MacroElement) -> list[folium.MacroElement]:
    resultado = [elemento]
    for filho in getattr(elemento, "_children", {}).values():
        resultado.extend(_descendentes(filho))
    return resultado


def test_ge_da_faixa_monta_uma_vez_por_rede_e_faixa(rede: Rede) -> None:
    cache: dict = {}
    ge1 = trajetos.ge_da_faixa(rede, "pico_manha", cache)
    assert trajetos.ge_da_faixa(rede, "pico_manha", cache) is ge1
    assert trajetos.ge_da_faixa(rede, "entrepico", cache) is not ge1
    outra = _rede()
    assert trajetos.ge_da_faixa(outra, "pico_manha", cache) is not ge1
    assert set(cache[trajetos.CHAVE_GE]["ges"]) == {"pico_manha"}  # a rede anterior saiu


def test_tabela_trechos_mostra_modo_linha_e_tempo(rede: Rede) -> None:
    ge = trajetos.ge_da_faixa(rede, "pico_manha", {})
    trajeto = trajeto_mais_rapido(ge, "A", "D")
    assert trajeto is not None
    assert [t.tipo for t in trajeto.trechos] == [ESPERA, ONIBUS, A_PE]

    tabela = trajetos.tabela_trechos(rede, trajeto)

    assert [linha["Modo"] for linha in tabela] == ["Espera", "Ônibus", "A pé"]
    assert tabela[0] == {
        "Trecho": "1",
        "Modo": "Espera",
        "Linha": "Linha 1",
        "De": "Origem (A)",
        "Para": "Origem (A)",
        "Paradas": "0",
        "Tempo": "5.0 min",
    }
    assert tabela[1]["Linha"] == "Linha 1"
    assert tabela[1]["Paradas"] == "2"
    assert tabela[1]["Tempo"] == "20.0 min"
    assert tabela[2]["Linha"] == ""
    assert tabela[2]["De"] == "Destino (C)" and tabela[2]["Para"] == "Vizinha (D)"


def test_mapa_trajeto_desenha_um_traco_por_trecho(rede: Rede) -> None:
    ge = trajetos.ge_da_faixa(rede, "pico_manha", {})
    trajeto = trajeto_mais_rapido(ge, "A", "D")
    assert trajeto is not None

    mapa = trajetos.mapa_trajeto(rede, trajeto)

    elementos = _descendentes(mapa)
    polilinhas = [e for e in elementos if isinstance(e, folium.PolyLine)]
    assert len(polilinhas) == 2  # ônibus e a pé
    assert sum(isinstance(e, folium.CircleMarker) for e in elementos) == 1  # espera
    # CircleMarker herda de Marker; os marcadores de origem e destino são Marker puros.
    assert sum(type(e) is folium.Marker for e in elementos) == 2
    camadas = [e.layer_name for e in elementos if isinstance(e, folium.FeatureGroup)]
    assert camadas[0].startswith("1. Espera da linha Linha 1")
    assert camadas[1].startswith("2. Ônibus, linha Linha 1")
    assert camadas[2].startswith("3. A pé")


def test_mapa_trajeto_so_a_pe_e_sem_trechos(rede: Rede) -> None:
    ge = trajetos.ge_da_faixa(rede, "pico_manha", {})
    so_a_pe = trajeto_mais_rapido(ge, "C", "D")
    assert so_a_pe is not None and [t.tipo for t in so_a_pe.trechos] == [A_PE]
    elementos = _descendentes(trajetos.mapa_trajeto(rede, so_a_pe))
    assert sum(isinstance(e, folium.PolyLine) for e in elementos) == 1

    parado = trajeto_mais_rapido(ge, "A", "A")
    assert parado is not None and parado.trechos == ()
    elementos = _descendentes(trajetos.mapa_trajeto(rede, parado))
    assert sum(type(e) is folium.Marker for e in elementos) == 2
    assert trajetos.tabela_trechos(rede, parado) == []


def test_render_na_aplicacao_de_teste_do_streamlit(rede: Rede) -> None:
    from streamlit.testing.v1 import AppTest

    # O AppTest copia só o código-fonte da função; a rede entra por `args`.
    def pagina(rede_app) -> None:
        from transporte.interface.paginas import trajetos as pag

        pag.render(rede_app)

    app = AppTest.from_function(pagina, args=(rede,))
    app.run()
    assert not app.exception
    # Paradas em ordem de nome: Destino (C), Meio (B), Origem (A), Vizinha (D).
    assert app.selectbox[1].value == "C" and app.selectbox[2].value == "B"
    assert len(app.warning) == 1  # C -> B não tem trajeto: a L1 só vai de A para C
    assert not app.metric

    app.selectbox[1].select("A").run()
    app.selectbox[2].select("D").run()
    assert not app.exception
    # A -> D: espera 300 s + ônibus 1200 s + a pé C -> D (111,19 m / 1,2 m/s = 92,7 s).
    assert [m.value for m in app.metric] == ["26.5 min", "0", "1.5 min", "5.0 min", "20.0 min"]
    assert not app.warning
