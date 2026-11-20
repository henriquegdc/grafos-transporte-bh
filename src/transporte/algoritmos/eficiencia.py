"""Métricas de eficiência global e de duração de viagens (F-EFI).

Eficiência estrutural opera sobre G_P. Tempos de viagem usam G_E e consideram apenas
pares de paradas, seguindo a duração total do caminho de F-ROTA.

estado: implementado
"""

from __future__ import annotations

import math
import random
from collections.abc import Iterable
from dataclasses import dataclass

from transporte.grafo.buscas import INF, dijkstra
from transporte.grafo.grafo import Grafo
from transporte.modelo.visoes import VisaoGE


@dataclass(frozen=True)
class Estimativa:
    """Valor de uma métrica e informação da amostragem.

    Atributos:
        valor: estimativa; None quando nenhuma viagem amostrada foi alcançável.
        erro_padrao: erro padrão da média; None quando não é estimável. Uma enumeração
            exata retorna 0.0; sem observações alcançáveis, não há estimativa.
        tamanho_amostra: origens ou pares sorteados, conforme a métrica.
        tamanho_populacao: número de origens ou de pares ordenados possíveis.
        pares_alcancaveis: viagens alcançáveis observadas; None para eficiência global.
    Espaço O(1).
    """

    valor: float | None
    erro_padrao: float | None
    tamanho_amostra: int
    tamanho_populacao: int
    pares_alcancaveis: int | None = None


def _inteiro_positivo(nome: str, valor: int) -> None:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TypeError(f"{nome} deve ser int, recebido {type(valor).__name__}")
    if valor < 1:
        raise ValueError(f"{nome} deve ser >= 1, recebido {valor}")


def _semente_valida(semente: int) -> None:
    if isinstance(semente, bool) or not isinstance(semente, int):
        raise TypeError(f"semente deve ser int, recebido {type(semente).__name__}")


def _validar_origens(g: Grafo, origens: Iterable[int]) -> list[int]:
    lista = list(origens)
    if len(lista) != len(set(lista)):
        raise ValueError("origens não pode conter vértices repetidos")
    for origem in lista:
        if isinstance(origem, bool) or not isinstance(origem, int):
            raise TypeError("cada origem deve ser um id de vértice inteiro")
        if not 0 <= origem < g.num_vertices():
            raise IndexError(f"vértice inexistente: {origem}")
    return lista


def _soma_reciprocos(g: Grafo, origem: int) -> float:
    """Soma 1/d da origem aos demais vértices alcançáveis. O(Dijkstra)."""
    if not g.vertice_ativo(origem):
        return 0.0
    distancias = dijkstra(g, origem).dist
    soma = 0.0
    for destino, distancia in enumerate(distancias):
        if destino == origem or distancia == INF:
            continue
        if distancia == 0:
            raise ValueError(
                f"distância 0 entre vértices distintos {origem} e {destino}: eficiência infinita"
            )
        soma += 1.0 / distancia
    return soma


def eficiencia_global(
    g: Grafo,
    origens: Iterable[int] | None = None,
    n_referencia: int | None = None,
) -> float:
    """Média de 1/d(i, j) sobre pares ordenados distintos, em um grafo ponderado.

    Compatível com o contrato provisório consumido pela F-RES. A feature usa G_P, cujos
    pesos têm piso positivo; não aplicar diretamente a todos os vértices de G_E, que
    contém arestas de desembarque com peso zero.

    Entradas:
        g: grafo direcionado com pesos não negativos.
        origens: conjunto sem repetição de fontes dos Dijkstras. None usa todas as origens
            ativas. Uma origem inativa contribui zero, mas permanece no denominador.
        n_referencia: população original de vértices usada no denominador; None usa o
            número de vértices ativos. Deve ser >= ao número de vértices ativos.
    Saída: soma de 1/d dividida por s * (n_referencia - 1), em 1/unidade do peso. Pares
        sem caminho somam zero. Menos de dois vértices, ou conjunto vazio de origens,
        devolve 0.0.
    Casos de borda: origem inválida levanta IndexError; origem repetida ou população
        menor que a quantidade de vértices ativos levanta ValueError; tipos inválidos
        levantam TypeError; distância zero entre vértices distintos levanta ValueError.
    Complexidade: tempo O(V + s (V + E) log V), com s buscas de Dijkstra; espaço
        O(V + E + s), incluindo a lista de origens.
    """
    ativos = sum(g.vertice_ativo(v) for v in range(g.num_vertices()))
    if n_referencia is None:
        n = ativos
    else:
        if isinstance(n_referencia, bool) or not isinstance(n_referencia, int):
            raise TypeError("n_referencia deve ser int")
        if n_referencia < ativos or n_referencia < 0:
            raise ValueError("n_referencia não pode ser menor que os vértices ativos")
        n = n_referencia

    lista = (
        [v for v in range(g.num_vertices()) if g.vertice_ativo(v)]
        if origens is None
        else _validar_origens(g, origens)
    )
    quantidade_origens = n if origens is None else len(lista)
    if n < 2 or quantidade_origens == 0:
        return 0.0

    soma = sum(_soma_reciprocos(g, origem) for origem in lista)
    return soma / (quantidade_origens * (n - 1))


def _erro_padrao(valores: list[float]) -> float | None:
    if len(valores) < 2:
        return None
    media = sum(valores) / len(valores)
    variancia = sum((valor - media) ** 2 for valor in valores) / (len(valores) - 1)
    return math.sqrt(variancia / len(valores))


def estimar_eficiencia_global(
    g: Grafo,
    tamanho_amostra: int | None = None,
    semente: int = 0,
) -> Estimativa:
    """Estima eficiência global amostrando origens uniformemente sem reposição.

    A contribuição de cada origem é a média de 1/d para todos os demais vértices,
    contando pares inalcançáveis como zero. O erro informado é o erro padrão amostral
    das contribuições por origem, com correção para população finita; com amostra exata,
    é zero.

    Entradas:
        g: G_P recomendado para a métrica estrutural.
        tamanho_amostra: número de origens sorteadas; None calcula todas as origens.
        semente: semente inteira para tornar a amostra reproduzível.
    Saída: Estimativa em 1/unidade do peso, com tamanho da amostra e população.
    Casos de borda: grafo com menos de dois vértices tem eficiência zero; tamanho
        inválido levanta ValueError ou TypeError; peso zero entre vértices distintos
        levanta ValueError.
    Complexidade: tempo O(V + s (V + E) log V), sendo s o número de origens avaliadas;
        espaço O(V + E + s).
    """
    _semente_valida(semente)
    vertices = [v for v in range(g.num_vertices()) if g.vertice_ativo(v)]
    populacao = len(vertices)
    if tamanho_amostra is None:
        amostra = vertices
        exata = True
    else:
        _inteiro_positivo("tamanho_amostra", tamanho_amostra)
        if tamanho_amostra > populacao:
            raise ValueError("tamanho_amostra não pode exceder o número de origens ativas")
        rng = random.Random(semente)
        amostra = rng.sample(vertices, tamanho_amostra)
        exata = tamanho_amostra == populacao

    if populacao < 2:
        return Estimativa(0.0, 0.0, len(amostra), populacao)

    contribuicoes = [_soma_reciprocos(g, origem) / (populacao - 1) for origem in amostra]
    valor = sum(contribuicoes) / len(contribuicoes)
    if exata:
        erro = 0.0
    else:
        erro_amostral = _erro_padrao(contribuicoes)
        erro = (
            None
            if erro_amostral is None
            else erro_amostral * math.sqrt((populacao - len(amostra)) / populacao)
        )
    return Estimativa(valor, erro, len(amostra), populacao)


def tempo_medio_viagem(
    ge: VisaoGE,
    tamanho_amostra: int,
    semente: int = 0,
) -> Estimativa:
    """Estima a duração média do caminho mais rápido entre pares de paradas em G_E.

    Cada par ordenado distinto é sorteado uniformemente sem reposição. Para cada origem
    sorteada, roda-se uma busca Dijkstra e consulta-se o custo total do caminho, com a
    semântica de `Trajeto.tempo_total_s` da F-ROTA: caminhada, espera esperada e viagem.
    Plataformas não entram na população; pares sem caminho são contados à parte, não como
    viagens de duração zero. O erro é o erro padrão amostral dos tempos alcançáveis;
    uma enumeração exata com pelo menos uma viagem alcançável tem erro zero.

    Entradas:
        ge: G_E de uma faixa horária.
        tamanho_amostra: número de pares OD sorteados; deve ser >= 1.
        semente: semente inteira para tornar os pares reproduzíveis.
    Saída: Estimativa em segundos; valor None se nenhum par sorteado for alcançável.
    Casos de borda: com menos de duas paradas ativas, devolve valor None e população zero;
        parâmetros inválidos levantam ValueError ou TypeError; em amostra incompleta com
        menos de duas viagens alcançáveis o erro padrão é None; sem viagens alcançáveis,
        valor e erro padrão são None.
    Complexidade: tempo O(V + k (V + E) log V + m), k origens distintas e m pares
        sorteados; espaço O(V + E + m).
    """
    _inteiro_positivo("tamanho_amostra", tamanho_amostra)
    _semente_valida(semente)
    g = ge.grafo
    paradas = [vertice for vertice in ge.vertice_da_parada.values() if g.vertice_ativo(vertice)]
    if len(paradas) < 2:
        return Estimativa(None, None, 0, 0, 0)

    populacao = len(paradas) * (len(paradas) - 1)
    if tamanho_amostra > populacao:
        raise ValueError("tamanho_amostra não pode exceder o número de pares OD possíveis")
    rng = random.Random(semente)
    destinos_por_origem: dict[int, list[int]] = {}
    for indice in rng.sample(range(populacao), tamanho_amostra):
        origem_indice, destino_indice = divmod(indice, len(paradas) - 1)
        if destino_indice >= origem_indice:
            destino_indice += 1
        origem = paradas[origem_indice]
        destino = paradas[destino_indice]
        destinos_por_origem.setdefault(origem, []).append(destino)

    tempos = []
    for origem, destinos in destinos_por_origem.items():
        distancias = dijkstra(g, origem).dist
        tempos.extend(distancias[destino] for destino in destinos if distancias[destino] != INF)

    valor = sum(tempos) / len(tempos) if tempos else None
    erro = 0.0 if tamanho_amostra == populacao and tempos else _erro_padrao(tempos)
    return Estimativa(valor, erro, tamanho_amostra, populacao, len(tempos))
