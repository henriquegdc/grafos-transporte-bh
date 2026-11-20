"""Verificações de alcance, desvios geográficos e comparação com amostra pareada."""

from math import inf, nan
from random import Random

import networkx as nx
import pytest

from transporte.algoritmos.eficiencia import (
    comparar_faixas,
    indices_desvio,
    medias_por_quadrante,
    sortear_pares,
)
from transporte.algoritmos.isocronas import isocrona
from transporte.dados.modelo import Linha, Padrao, Parada, Rede
from transporte.grafo.grafo import Grafo
from transporte.modelo.construtores import construir_ge
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import VisaoGE


def _rede():
    # A->C só via B (dois lados de um triângulo retângulo, perto do Equador).
    paradas = {
        p: Parada(p, p, lat, lon)
        for p, lat, lon in [("A", 0, 0), ("B", 0, 0.01), ("C", 0.01, 0.01), ("D", 0.01, 0.01)]
    }
    viagens = [(t, t + 60, t + 120) for t in (21600, 21720, 36000, 36600)]
    return Rede(
        paradas,
        {"L": Linha("L", "L", 3)},
        {"P": Padrao("P", "L", ("A", "B", "C"))},
        {},
        {"P": viagens},
    )


def test_desvio_e_medias():
    rede = _rede()
    ge = construir_ge(rede, "pico_manha", esperas={("P", "pico_manha"): 60})
    resultado = indices_desvio(rede, ge, 12, 42)
    pares = {(p.origem, p.destino): p for p in resultado}
    ac = pares["A", "C"]
    assert ac.desvio == pytest.approx(2**0.5, rel=1e-6)
    assert ac.min_por_km == pytest.approx(3 / 1.57253, rel=1e-4)
    assert ac.tempo_s == 180
    assert pares["C", "A"].desvio is None
    assert pares["C", "D"].tempo_s == 1
    assert pares["C", "D"].desvio is None
    assert medias_por_quadrante(resultado)["SO"] == pytest.approx((1 + 2 * 2**0.5) / 3)
    assert isocrona(ge, "A", 120) == {"A": 0, "B": 120}
    assert isocrona(ge, "A", 0) == {"A": 0}
    ge.grafo.desativar_vertice(ge.vertice_da_parada["A"])
    assert isocrona(ge, "A", 180) == {}
    with pytest.raises(KeyError):
        isocrona(ge, "?", 10)
    for limite in (-1, inf, nan):
        with pytest.raises(ValueError):
            isocrona(ge, "A", limite)


@pytest.mark.parametrize("semente", range(10))
def test_isocrona_oraculo_networkx(semente):
    rng = Random(semente)
    g = Grafo()
    nxg = nx.MultiDiGraph()
    paradas = {str(i): g.adicionar_vertice(str(i)) for i in range(8)}
    ge = VisaoGE(g, "G_E", vertice_da_parada=paradas)
    for i in range(8, 14):
        g.adicionar_vertice(f"plataforma-{i}")
    nxg.add_nodes_from(range(14))
    for _ in range(60):
        u, v = rng.sample(range(14), 2)
        peso = rng.randrange(9)
        g.adicionar_aresta(u, v, peso)
        nxg.add_edge(u, v, weight=peso)
    for limite in (0, 5, 9, 30):
        dist, _ = nx.single_source_dijkstra(nxg, 0, cutoff=limite)
        assert isocrona(ge, "0", limite) == {p: dist[v] for p, v in paradas.items() if v in dist}


def test_comparar_faixas_gabarito_mesmos_pares_com_desconexao():
    rede = _rede()
    rede.paradas.pop("D")
    res = comparar_faixas(rede, 6, 22, Parametros(raio_caminhada_m=0))
    manha, entrepico, tarde, noite = res
    assert manha.erro_tempo_medio_s == manha.erro_eficiencia_por_s == 0.0
    assert noite.erro_tempo_medio_s is None
    assert noite.erro_eficiencia_por_s == 0.0
    parcial = comparar_faixas(rede, 5, 22, Parametros(raio_caminhada_m=0))[0]
    assert parcial.erro_tempo_medio_s is not None
    assert parcial.erro_eficiencia_por_s > 0
    assert manha.pares == entrepico.pares == 6
    assert manha.alcancaveis == entrepico.alcancaveis == 3
    assert manha.tempo_medio_s == pytest.approx((120 + 180 + 120) / 3)
    assert manha.eficiencia_por_s == pytest.approx((2 / 120 + 1 / 180) / 6)
    assert entrepico.tempo_medio_s == pytest.approx((360 + 420 + 360) / 3)
    assert entrepico.eficiencia_por_s < manha.eficiencia_por_s
    assert tarde.tempo_medio_s is noite.tempo_medio_s is None
    assert tarde.eficiencia_por_s == noite.eficiencia_por_s == 0
    assert sortear_pares(list(rede.paradas), 4, 17) == sortear_pares(list(rede.paradas), 4, 17)
    with pytest.raises(ValueError):
        comparar_faixas(rede, 7)
    assert all(
        r.pares == 0 and r.eficiencia_por_s is None
        for r in comparar_faixas(Rede({}, {}, {}, {}), 1)
    )
