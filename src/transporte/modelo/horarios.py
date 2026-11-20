"""G_T sobre as paradas e viagens do dia de serviço (RF-ESP-04)."""

from bisect import bisect_left
from dataclasses import dataclass, field
from itertools import pairwise

from transporte.grafo.grafo import Grafo
from transporte.modelo.construtores import RedeConstrutores, _adicionar_caminhada
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import VIAGEM, Visao


@dataclass
class Quadro:
    """Eventos (partida, chegada, índice da viagem no padrão), em ordem de partida."""

    padrao: str
    eventos: list[tuple[int, int, int]]

    def proximo(self, instante: float) -> tuple[int, int, int] | None:
        """Primeira partida viável da tabela filtrada ou None. O(log k), espaço O(1)."""
        i = bisect_left(self.eventos, (instante,))
        return self.eventos[i] if i < len(self.eventos) else None


@dataclass
class VisaoGT(Visao):
    vertice_da_parada: dict[str, int] = field(default_factory=dict)
    parada_do_vertice: list[str] = field(default_factory=list)
    quadros: dict[int, Quadro] = field(default_factory=dict)


def construir_gt(rede: RedeConstrutores, params: Parametros | None = None) -> VisaoGT:
    """Indexa a Rede normalizada, com os mesmos parâmetros de caminhada de G_P.

    Devolve uma aresta temporal por segmento servido de cada padrão. Seu peso
    estático é zero e a consulta usa o quadro da aresta. Preserva horas >24 e
    viagens de duração zero. Sem viagens, ainda se pode caminhar. Em caso de
    ultrapassagem elimina partidas cuja chegada outra partida posterior melhora.
    Para N eventos, L posições dos padrões, k eventos no maior segmento e K pares
    a pé: tempo esperado O(V+L+K+N log(k+1)), pior caso espacial da grade O(V²)
    comparações. Espaço O(V+L+K+N).
    """
    gt = VisaoGT(Grafo(), "G_T")
    paradas = list(rede.paradas.values())
    for parada in paradas:
        gt.vertice_da_parada[parada.id] = gt.grafo.adicionar_vertice(parada.id)
        gt.parada_do_vertice.append(parada.id)
    for padrao in rede.padroes.values():
        vertices = [gt.vertice_da_parada[p] for p in padrao.paradas]
        viagens = rede.viagens.get(padrao.id, ())
        for i, (u, v) in enumerate(pairwise(vertices)):
            if u == v or not viagens:
                continue
            eventos = sorted((h[i], h[i + 1], j) for j, h in enumerate(viagens))
            # Varre de trás para frente: ao chegar antes, pode-se esperar pelo expresso.
            melhores = []
            for evento in reversed(eventos):
                if not melhores or evento[1] <= melhores[-1][1]:
                    melhores.append(evento)
            melhores.reverse()
            aresta = gt.grafo.adicionar_aresta(u, v, 0, VIAGEM)
            gt.quadros[aresta] = Quadro(padrao.id, melhores)
    _adicionar_caminhada(gt.grafo, paradas, range(len(paradas)), params or Parametros())
    return gt
