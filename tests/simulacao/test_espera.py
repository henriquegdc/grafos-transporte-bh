"""Gabaritos manuais e integração GTFS → espera → G_E → trajeto."""

from copy import deepcopy
from pathlib import Path

import pytest

from transporte.dados.leitor_gtfs import ler
from transporte.dados.modelo import Linha, Padrao, Parada, Rede
from transporte.modelo.construtores import construir_ge
from transporte.modelo.parametros import FaixaHoraria, Parametros
from transporte.modelo.visoes import EMBARQUE
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos, simular_trajeto

REDE_TESTE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"
SEM_CAMINHADA = Parametros(raio_caminhada_m=0)


@pytest.fixture
def rede():
    return ler(REDE_TESTE)


def test_gabarito_e_frequencias_expandidas_sem_duplicar(rede):
    original = deepcopy(rede)
    intervalos = estimar_intervalos(rede)
    por_linha = {(rede.padroes[p].linha_id, f): h for (p, f), h in intervalos.items()}
    assert por_linha == {("L1", "pico_manha"): 1200, ("L2", "entrepico"): 600}
    assert set(calcular_esperas(intervalos).values()) == {600, 300}
    assert rede == original


def test_ordena_deduplica_e_nao_conta_visitas_da_circular(rede):
    pid = next(p for p in rede.padroes if rede.padroes[p].linha_id == "L1")
    rede.padroes[pid] = Padrao(pid, "L1", ("A", "B", "A"))
    rede.viagens[pid] = [(30000, 30300, 30600), (28800, 29100, 29400)] * 2 + [()]
    assert estimar_intervalos(rede)[pid, "pico_manha"] == 1200


def test_padroes_da_mesma_linha_nao_sao_misturados(rede):
    pid = next(p for p in rede.padroes if rede.padroes[p].linha_id == "L1")
    rede.padroes["volta"] = Padrao("volta", "L1", ("C", "B", "A"))
    rede.viagens["volta"] = [(29000, 29300, 29600), (29600, 29900, 30200)]
    intervalos = estimar_intervalos(rede)
    assert intervalos[pid, "pico_manha"] == 1200
    assert intervalos["volta", "pico_manha"] == 600


def test_media_de_intervalos_irregulares(rede):
    pid = next(iter(rede.padroes))
    rede.viagens[pid] = [(25200,), (25800,), (27600,)]
    assert estimar_intervalos(rede)[pid, "pico_manha"] == 1200
    assert calcular_esperas(estimar_intervalos(rede))[pid, "pico_manha"] == 600


def test_limites_das_faixas_e_mais_de_24h(rede):
    pid = next(iter(rede.padroes))
    rede.viagens = {pid: [(21599,), (21600,), (22200,), (32400,), (33000,), (87000,), (87600,)]}
    params = Parametros(faixas=(*Parametros().faixas, FaixaHoraria("madrugada", 86400, 90000)))
    intervalos = estimar_intervalos(rede, params)
    assert intervalos == {
        (pid, "pico_manha"): 600,
        (pid, "entrepico"): 600,
        (pid, "madrugada"): 600,
    }


@pytest.mark.parametrize("partidas", [[], [()], [(28800,)], [(28800,), (28800,)]])
def test_sem_duas_partidas_distintas_omite_estimativa(rede, partidas):
    pid = next(iter(rede.padroes))
    rede.viagens = {pid: partidas}
    assert estimar_intervalos(rede) == {}


def test_rede_vazia():
    assert estimar_intervalos(Rede({}, {}, {}, {})) == {}
    assert calcular_esperas({}) == {}


@pytest.mark.parametrize("invalido", [-1, float("nan"), float("inf"), -float("inf")])
def test_espera_rejeita_intervalos_invalidos(invalido):
    with pytest.raises(ValueError, match="intervalo"):
        calcular_esperas({("p", "f"): invalido})


def test_calcular_esperas_aceita_zero_e_nao_muda_entrada():
    intervalos = {("p", "f"): 0, ("q", "f"): 1200}
    assert calcular_esperas(intervalos) == {("p", "f"): 0, ("q", "f"): 600}
    assert intervalos[("q", "f")] == 1200


def test_peso_de_embarque_recebe_espera_uma_vez(rede):
    esperas = calcular_esperas(estimar_intervalos(rede))
    ge = construir_ge(rede, "pico_manha", params=SEM_CAMINHADA, esperas=esperas)
    embarques = [
        ge.grafo.aresta(a)
        for a in range(ge.grafo.num_arestas())
        if ge.grafo.aresta(a)[3] == EMBARQUE
    ]
    assert len(embarques) == 2
    assert {a[2] for a in embarques} == {600}


def test_trajeto_direto_e_decomposicao_sem_caminhada(rede):
    t = simular_trajeto(rede, "A", "C", 8 * 3600, SEM_CAMINHADA)
    assert t.tempo_por_tipo() == {"caminhada": 0, "espera": 600, "viagem": 600}
    assert t.tempo_total_s == sum(t.tempo_por_tipo().values()) == 1200
    assert t.baldeacoes == 0


def test_frequencia_em_duas_subfaixas(rede):
    params = Parametros(
        raio_caminhada_m=0,
        faixas=(
            FaixaHoraria("a", 32400, 34200),
            FaixaHoraria("b", 34200, 36000),
        ),
    )
    for saida in (32400, 34200):
        t = simular_trajeto(rede, "A", "D", saida, params)
        assert t.tempo_por_tipo()["espera"] == 300
        assert t.tempo_total_s == 780


def test_fallback_com_uma_partida_e_faixa_fixa_ate_o_fim(rede):
    # 11/11 ativa somente EXTRA às 10h; viagem cruza o limite de uma faixa customizada.
    from datetime import date

    r = ler(REDE_TESTE, date(2026, 11, 11))
    params = Parametros(
        raio_caminhada_m=0, espera_padrao_s=123, faixas=(FaixaHoraria("curta", 36000, 36001),)
    )
    assert estimar_intervalos(r, params) == {}
    t = simular_trajeto(r, "A", "C", 36000, params)
    assert t.tempo_total_s == 723
    assert t.tempo_por_tipo()["espera"] == 123


def test_uma_baldeacao():
    paradas = {p: Parada(p, p, -19.9 + i / 100, -43.9) for i, p in enumerate("ABC")}
    r = Rede(
        paradas,
        {"L": Linha("L", "L", 3)},
        {
            "ida": Padrao("ida", "L", ("A", "B")),
            "volta": Padrao("volta", "L", ("B", "C")),
        },
        {},
        viagens={
            "ida": [(28800, 28900), (30000, 30100)],
            "volta": [(28800, 29000), (29400, 29600)],
        },
    )
    t = simular_trajeto(r, "A", "C", 28800, SEM_CAMINHADA)
    assert t.baldeacoes == 1
    assert t.tempo_por_tipo() == {"caminhada": 0, "espera": 900, "viagem": 300}
    assert t.tempo_total_s == 1200


def test_caminhada_e_origem_igual_destino(rede):
    t = simular_trajeto(rede, "A", "C", 28800)
    assert t.tempo_por_tipo()["caminhada"] > 0
    assert t.tempo_por_tipo()["espera"] == 0
    assert sum(t.tempo_por_tipo().values()) == pytest.approx(t.tempo_total_s)
    t = simular_trajeto(rede, "A", "A", 28800)
    assert (t.tempo_total_s, t.baldeacoes, t.trechos) == (0, 0, ())


def test_inalcancavel_e_parada_ausente(rede):
    assert simular_trajeto(rede, "C", "A", 28800, SEM_CAMINHADA) is None
    with pytest.raises(KeyError):
        simular_trajeto(rede, "A", "INEXISTENTE", 28800)


@pytest.mark.parametrize("saida", [0, 21599, 86400, 87000, -1])
def test_horario_fora_da_faixa_nao_e_normalizado(rede, saida):
    with pytest.raises(ValueError, match="fora das faixas"):
        simular_trajeto(rede, "A", "C", saida)


def test_simulacao_acima_de_24h_com_faixa_explicita(rede):
    params = Parametros(raio_caminhada_m=0, faixas=(FaixaHoraria("extra", 86400, 90000),))
    t = simular_trajeto(rede, "A", "C", 87000, params)
    assert t.tempo_total_s == 900
