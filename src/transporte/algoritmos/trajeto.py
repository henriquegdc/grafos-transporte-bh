"""Trajeto mais rápido entre duas paradas sobre G_E (F-ROTA: RF-ROT-01).

Um único Dijkstra em G_E soma caminhada, espera, viagem e baldeações, porque trocar de
linha obriga a sair da plataforma e pagar um novo embarque (docs/fontes/modelagem.md §3.4).
Este módulo roda o Dijkstra do núcleo e traduz o caminho de arestas em trechos legíveis
(a pé, espera, linha usada), que a página de trajetos desenha no mapa (RF-ROT-02).

Notação: V = vértices de G_E (paradas + plataformas), E = arestas de G_E, k = arestas do
caminho.

estado: implementado
"""

from __future__ import annotations

from dataclasses import dataclass

from transporte.grafo.buscas import INF, caminho_arestas, dijkstra
from transporte.modelo.visoes import (
    CAMINHADA,
    DESEMBARQUE,
    EMBARQUE,
    VIAGEM,
    VisaoGE,
)

# Tipos de trecho. "espera" é o embarque visto pelo passageiro: o tempo parado na
# parada até o ônibus chegar.
A_PE = "caminhada"
ESPERA = "espera"
ONIBUS = "viagem"


@dataclass(frozen=True)
class Trecho:
    """Parte do trajeto com um só modo.

    Atributos:
        tipo: A_PE, ESPERA ou ONIBUS.
        paradas: ids das paradas percorridas, na ordem. A pé e de ônibus: da primeira à
            última parada do trecho (pelo menos duas); espera: só a parada onde se espera.
        tempo_s: duração do trecho, em segundos.
        padrao: id do padrão de linha na espera e no ônibus; None a pé.
    Espaço O(número de paradas do trecho).
    """

    tipo: str
    paradas: tuple[str, ...]
    tempo_s: float
    padrao: str | None = None


@dataclass(frozen=True)
class Trajeto:
    """Resultado de trajeto_mais_rapido.

    Atributos:
        origem, destino: ids das paradas.
        tempo_total_s: soma dos tempos dos trechos (o custo do Dijkstra).
        baldeacoes: embarques - 1, ou 0 se não embarca.
        trechos: na ordem do percurso; vazio se origem == destino.
    """

    origem: str
    destino: str
    tempo_total_s: float
    baldeacoes: int
    trechos: tuple[Trecho, ...]

    def tempo_por_tipo(self) -> dict[str, float]:
        """Tempo somado de cada tipo de trecho: {A_PE, ESPERA, ONIBUS} -> segundos.

        Decomposição pedida também pela F-ESPERA (RF-ESP-03). O(número de trechos).
        """
        soma = {A_PE: 0.0, ESPERA: 0.0, ONIBUS: 0.0}
        for t in self.trechos:
            soma[t.tipo] += t.tempo_s
        return soma


def _trechos(ge: VisaoGE, arestas: list[int]) -> list[Trecho]:
    """Agrupa as arestas do caminho em trechos.

    Caminhadas seguidas viram um trecho a pé só; embarque vira espera; viagens seguidas do
    mesmo padrão viram um trecho de ônibus, fechado pelo desembarque (peso 0, sem trecho).
    Complexidade: O(V) para inverter os mapas da visão, mais O(k).
    """
    g = ge.grafo
    parada_do_vertice = {v: p for p, v in ge.vertice_da_parada.items()}
    plataforma_do_vertice = {v: chave for chave, v in ge.plataforma.items()}

    trechos: list[Trecho] = []
    tipo = None  # tipo do trecho aberto: A_PE ou ONIBUS
    paradas: list[str] = []
    tempo = 0.0
    padrao = None

    def fechar() -> None:
        nonlocal tipo, paradas, tempo, padrao
        if tipo is not None:
            trechos.append(Trecho(tipo, tuple(paradas), tempo, padrao))
        tipo, paradas, tempo, padrao = None, [], 0.0, None

    for a in arestas:
        u, v, peso, tipo_aresta = g.aresta(a)
        if tipo_aresta == CAMINHADA:
            if tipo != A_PE:
                fechar()
                tipo, paradas = A_PE, [parada_do_vertice[u]]
            paradas.append(parada_do_vertice[v])
            tempo += peso
        elif tipo_aresta == EMBARQUE:
            fechar()
            parada, pad = plataforma_do_vertice[v]
            trechos.append(Trecho(ESPERA, (parada,), peso, pad))
        elif tipo_aresta == VIAGEM:
            parada_u, pad = plataforma_do_vertice[u]
            if tipo != ONIBUS:
                fechar()
                tipo, paradas, padrao = ONIBUS, [parada_u], pad
            paradas.append(plataforma_do_vertice[v][0])
            tempo += peso
        elif tipo_aresta == DESEMBARQUE:
            fechar()
        else:
            raise ValueError(
                f"aresta {a} com tipo desconhecido em G_E: {tipo_aresta!r}"
            )
    fechar()
    return trechos


def trajeto_mais_rapido(ge: VisaoGE, origem: str, destino: str) -> Trajeto | None:
    """Trajeto mais rápido de origem a destino em G_E (RF-ROT-01).

    Roda o Dijkstra do núcleo (HeapMin próprio) a partir do vértice da parada de origem,
    parando quando o destino é fechado, e reconstrói o caminho pelas arestas, o que
    distingue o padrão usado mesmo com plataformas paralelas.

    Entradas:
        ge: G_E de uma faixa horária (as esperas dependem da faixa).
        origem, destino: ids de paradas do GTFS.
    Saída: Trajeto com o tempo total, as baldeações e os trechos; None se o destino não é
        alcançável a partir da origem.
    Casos de borda: origem == destino devolve tempo 0 e nenhum trecho; parada inexistente
        levanta KeyError; vértices e arestas desativados (F-RES) são respeitados.
    Complexidade: tempo O((V + E) log V) do Dijkstra, mais O(V + k) da reconstrução;
        espaço O(V + E) no pior caso, pelas entradas do heap.
    """
    s = ge.vertice_da_parada[origem]
    t = ge.vertice_da_parada[destino]
    r = dijkstra(ge.grafo, s, t)
    if r.dist[t] == INF:
        return None
    arestas = caminho_arestas(r, t)
    return Trajeto(
        origem=origem,
        destino=destino,
        tempo_total_s=r.dist[t],
        baldeacoes=ge.baldeacoes(arestas),
        trechos=tuple(_trechos(ge, arestas)),
    )
