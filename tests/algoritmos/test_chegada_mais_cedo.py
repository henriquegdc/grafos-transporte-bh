"""Gabarito da rede de teste e oráculo independente por eventos no tempo."""

from itertools import pairwise
from math import inf
from pathlib import Path
from random import Random

import networkx as nx
import pytest

from transporte.algoritmos.chegada_mais_cedo import chegada_mais_cedo, monte_carlo
from transporte.dados.leitor_gtfs import ler
from transporte.dados.modelo import Padrao, Parada, Rede
from transporte.modelo.horarios import construir_gt
from transporte.modelo.parametros import Parametros

FONTE = Path(__file__).resolve().parents[2] / "dados/rede-teste"
SEM_CAMINHADA = Parametros(raio_caminhada_m=0)


def test_gabarito_dia_de_servico_e_decomposicao():
    rede = ler(FONTE)
    gt = construir_gt(rede, SEM_CAMINHADA)
    trajeto = chegada_mais_cedo(gt, "A", "C", 8 * 3600 + 60)
    assert trajeto.tempo_total_s == 1740
    assert trajeto.tempo_por_tipo() == {"viagem": 600, "espera": 1140, "caminhada": 0}
    assert trajeto.baldeacoes == 0
    assert trajeto.trechos[-1].paradas == ("A", "B", "C")
    assert chegada_mais_cedo(gt, "A", "C", 87000).tempo_total_s == 600
    assert chegada_mais_cedo(gt, "A", "C", 87001) is None
    assert chegada_mais_cedo(gt, "A", "D", 9 * 3600 + 1).tempo_total_s == 599 + 480
    assert chegada_mais_cedo(gt, "A", "A", 0).trechos == ()
    with pytest.raises(KeyError):
        chegada_mais_cedo(gt, "A", "?", 0)
    with pytest.raises(ValueError):
        chegada_mais_cedo(gt, "A", "B", -1)
    a_pe = chegada_mais_cedo(construir_gt(rede), "C", "A", 90000)
    assert a_pe.tempo_por_tipo()["caminhada"] == a_pe.tempo_total_s > 0


def test_monte_carlo_conserva_inacessiveis_e_reproduz_sorteio():
    gt = construir_gt(ler(FONTE), SEM_CAMINHADA)
    args = (gt, "A", "C", 87000, 87002, 30, 42)
    resultado = monte_carlo(*args)
    assert resultado == monte_carlo(*args)
    assert {(a.saida_s, a.total_s, a.espera_s) for a in resultado} == {
        (87000, 600, 0),
        (87001, None, None),
    }
    with pytest.raises(ValueError):
        monte_carlo(gt, "A", "C", 10, 10, 1, 1)


def _rede(paradas, padroes, viagens):
    return Rede(
        {p: Parada(p, p, 0, i) for i, p in enumerate(paradas)},
        {},
        {p: Padrao(p, p, tuple(seq)) for p, seq in padroes.items()},
        {},
        viagens,
    )


def test_expresso_ultrapassa_e_troca_de_veiculo_no_mesmo_padrao():
    rede = _rede("ABC", {"L": "ABC"}, {"L": [(0, 8, 50), (3, 6, 40), (8, 9, 10)]})
    gt = construir_gt(rede, SEM_CAMINHADA)
    assert chegada_mais_cedo(gt, "A", "B", 0).tempo_total_s == 6
    t = chegada_mais_cedo(gt, "A", "C", 0)
    assert t.baldeacoes == 1
    assert t.tempo_por_tipo() == {"caminhada": 0, "viagem": 4, "espera": 6}


@pytest.mark.parametrize("semente", range(10))
def test_rede_aleatoria_contra_grafo_expandido(semente):
    rng = Random(semente)
    paradas = list("ABCDE")
    padroes = {str(p): rng.sample(paradas, 3) for p in range(6)}
    viagens = {}
    expandido = nx.DiGraph()
    instantes = {p: {0, 12, 24} for p in paradas}
    for padrao, seq in padroes.items():
        viagens[padrao] = []
        for _ in range(4):
            h = [rng.randrange(25)]
            for _ in seq[1:]:
                h.append(h[-1] + rng.randrange(8))
            viagens[padrao].append(tuple(h))
            for parada, t in zip(seq, h):
                instantes[parada].add(t)
            for (p, t), (q, u) in pairwise(zip(seq, h)):
                expandido.add_edge((p, t), (q, u), weight=u - t)
    for p, eventos in instantes.items():
        for t, u in pairwise(sorted(eventos)):
            expandido.add_edge((p, t), (p, u), weight=u - t)
    gt = construir_gt(_rede(paradas, padroes, viagens), SEM_CAMINHADA)
    for origem in paradas:
        for saida in (0, 12, 24):
            dist = nx.single_source_dijkstra_path_length(expandido, (origem, saida))
            for destino in paradas:
                esperado = min(dist.get((destino, t), inf) for t in instantes[destino])
                trajeto = chegada_mais_cedo(gt, origem, destino, saida)
                assert (trajeto.tempo_total_s if trajeto else inf) == esperado
                if trajeto:
                    assert sum(trajeto.tempo_por_tipo().values()) == esperado


def test_caminhada_fracionaria_decide_qual_onibus_alcanca():
    rede = _rede("ABC", {"L": "BC"}, {"L": [(90, 100), (100, 120)]})
    rede.paradas["B"] = Parada("B", "B", 0, 0.001)
    gt = construir_gt(rede, Parametros(raio_caminhada_m=200))
    t = chegada_mais_cedo(gt, "A", "C", 0)
    parcelas = t.tempo_por_tipo()
    assert 90 < parcelas["caminhada"] < 100
    assert parcelas["espera"] == pytest.approx(100 - parcelas["caminhada"])
    assert parcelas["viagem"] == 20
    assert t.tempo_total_s == 120


def test_circular_que_volta_ao_ponto_separa_espera_de_viagem():
    rede = _rede("ABCD", {"L": "ABCBD"}, {"L": [(1, 2, 3, 4, 5)]})
    trajeto = chegada_mais_cedo(construir_gt(rede, SEM_CAMINHADA), "A", "D", 1)
    assert trajeto.tempo_por_tipo() == {"espera": 2, "viagem": 2, "caminhada": 0}
    assert [t.paradas for t in trajeto.trechos if t.tipo == "viagem"] == [("A", "B"), ("B", "D")]
