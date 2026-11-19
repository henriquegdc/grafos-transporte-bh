"""Menos baldeações contra mais rápido (F-BALD-2, RF-BAL-03).

A F-BALD acha o menor número de baldeações k na G_L, que não tem tempo. A F-ROTA acha o
trajeto mais rápido no G_E, sem olhar as baldeações. Para dizer quanto tempo custa evitar
baldeações, este módulo procura no mesmo G_E o trajeto mais rápido entre os que fazem no
máximo k baldeações e compara com o mais rápido: tempo a mais contra baldeações evitadas.

**Dijkstra com o número de embarques no estado.** O estado é (vértice de G_E, embarques
feitos). Embarcar (aresta parada -> plataforma) passa de e para e + 1 embarques; as outras
arestas mantêm e. Estados com mais de k + 1 embarques não existem. Um estado (v, e) é
dominado quando v já foi fechado com menos embarques: como o Dijkstra fecha em ordem de
tempo, esse outro chegou antes (ou junto) e com menos embarques, e tudo o que se faz a
partir de (v, e) se faz a partir dele. Por isso cada vértice é fechado no máximo k + 2
vezes, e quase sempre menos.

**Por que no G_E e não na G_L.** A G_L não tem tempo. Todo trajeto da G_L existe no G_E da
mesma faixa (mesmo raio de caminhada e mesma regra D10 para os padrões que circulam), então
o mais rápido com até k baldeações sempre existe quando a F-BALD acha um trajeto.

Notação: V e E de G_E, k = limite de baldeações (k + 2 camadas de embarques, de 0 a k + 1).

estado: implementado
"""

from __future__ import annotations

from dataclasses import dataclass

from transporte.algoritmos.baldeacoes import TrajetoBaldeacoes, menos_baldeacoes
from transporte.algoritmos.trajeto import Trajeto, _trechos, trajeto_mais_rapido
from transporte.grafo.buscas import INF
from transporte.grafo.heap import HeapMin
from transporte.modelo.visoes import VisaoGE, VisaoGL

_SEM = -1


def mais_rapido_com_limite(
    ge: VisaoGE, origem: str, destino: str, max_baldeacoes: int
) -> Trajeto | None:
    """Trajeto mais rápido de origem a destino em G_E com no máximo `max_baldeacoes`.

    Dijkstra sobre os estados (vértice, embarques feitos), com o HeapMin do núcleo e sem
    montar o grafo em camadas: as camadas ficam implícitas no índice do estado. Os trechos
    saem da mesma reconstrução da F-ROTA, então se leem e se desenham igual.

    Entradas:
        ge: G_E de uma faixa horária.
        origem, destino: ids de paradas do GTFS.
        max_baldeacoes: inteiro >= 0. Com 0, só vale a pé ou um ônibus.
    Saída: Trajeto (o mesmo tipo da F-ROTA) com baldeacoes <= max_baldeacoes, ou None se
        nenhum trajeto respeita o limite. Com limite >= baldeações do mais rápido, o tempo
        é o de trajeto_mais_rapido.
    Casos de borda: origem == destino devolve tempo 0 e nenhum trecho; parada inexistente
        levanta KeyError; limite negativo levanta ValueError e limite que não é int (ou é
        bool) levanta TypeError; vértices e arestas desativados (F-RES) são respeitados;
        empates de tempo saem com menos embarques primeiro no mesmo vértice.
    Complexidade: tempo O((k + 2)(V + E) log((k + 2) V)) no pior caso, porque há (k + 2) V
        estados e cada um relaxa as arestas do seu vértice; espaço O((k + 2)(V + E)), pelos
        vetores dos estados e pelas entradas repetidas no heap.
    """
    if isinstance(max_baldeacoes, bool) or not isinstance(max_baldeacoes, int):
        raise TypeError(
            f"max_baldeacoes deve ser int, recebido {type(max_baldeacoes).__name__}"
        )
    if max_baldeacoes < 0:
        raise ValueError(f"max_baldeacoes deve ser >= 0, recebido {max_baldeacoes}")
    s = ge.vertice_da_parada[origem]
    t = ge.vertice_da_parada[destino]
    g = ge.grafo
    if not g.vertice_ativo(s):
        return None

    camadas = max_baldeacoes + 2  # embarques de 0 a max_baldeacoes + 1
    n = g.num_vertices()
    # Pela definição de G_E, a única aresta de parada para plataforma é o EMBARQUE.
    eh_parada = [False] * n
    for v in ge.vertice_da_parada.values():
        eh_parada[v] = True

    dist = [INF] * (n * camadas)
    pred_estado = [_SEM] * (n * camadas)
    pred_aresta = [_SEM] * (n * camadas)
    # Menor número de embarques com que cada vértice já foi fechado (camadas = nenhum).
    menor_fechado = [camadas] * n

    inicio = s * camadas
    dist[inicio] = 0.0
    heap = HeapMin()
    heap.inserir(0.0, inicio)
    final = _SEM
    while not heap.vazio():
        d, x = heap.extrair_min()
        u, e = divmod(x, camadas)
        if e >= menor_fechado[u]:
            continue  # dominado ou entrada desatualizada da inserção preguiçosa
        menor_fechado[u] = e
        if u == t:
            final = x
            break
        for v, peso, a in g.vizinhos(u):
            e2 = e + 1 if eh_parada[u] and not eh_parada[v] else e
            if e2 >= menor_fechado[v]:
                continue  # passa do limite (menor_fechado começa em camadas) ou é dominado
            y = v * camadas + e2
            nova = d + peso
            if nova < dist[y]:
                dist[y] = nova
                pred_estado[y] = x
                pred_aresta[y] = a
                heap.inserir(nova, y)

    if final == _SEM:
        return None
    arestas = []
    x = final
    while x != inicio:
        arestas.append(pred_aresta[x])
        x = pred_estado[x]
    arestas.reverse()
    return Trajeto(
        origem=origem,
        destino=destino,
        tempo_total_s=dist[final],
        baldeacoes=ge.baldeacoes(arestas),
        trechos=tuple(_trechos(ge, arestas)),
    )


@dataclass(frozen=True)
class ComparacaoBaldeacoes:
    """Resultado de comparar_baldeacoes.

    Atributos:
        mais_rapido: trajeto da F-ROTA no G_E.
        menos_baldeacoes: trajeto da F-BALD na G_L; dá o mínimo k e a sequência de linhas
            pelo critério só de baldeações (sem tempo).
        rapido_com_menos_baldeacoes: o mais rápido no G_E com no máximo k baldeações. É o
            próprio mais_rapido quando ele já faz até k baldeações.
    Espaço O(número de trechos dos três trajetos).
    """

    mais_rapido: Trajeto
    menos_baldeacoes: TrajetoBaldeacoes
    rapido_com_menos_baldeacoes: Trajeto

    @property
    def tempo_a_mais_s(self) -> float:
        """Segundos a mais para fazer menos baldeações (>= 0). O(1)."""
        a_mais = self.rapido_com_menos_baldeacoes.tempo_total_s - self.mais_rapido.tempo_total_s
        return max(0.0, a_mais)  # só arredondamento de float daria negativo

    @property
    def baldeacoes_evitadas(self) -> int:
        """Baldeações do mais rápido menos as do mais rápido com até k (>= 0). O(1)."""
        return self.mais_rapido.baldeacoes - self.rapido_com_menos_baldeacoes.baldeacoes

    @property
    def tempo_por_baldeacao_evitada_s(self) -> float | None:
        """Tempo a mais dividido pelas baldeações evitadas; None se não evita nenhuma. O(1)."""
        if self.baldeacoes_evitadas == 0:
            return None
        return self.tempo_a_mais_s / self.baldeacoes_evitadas


def comparar_baldeacoes(
    ge: VisaoGE, gl: VisaoGL, origem: str, destino: str
) -> ComparacaoBaldeacoes | None:
    """Compara o trajeto de menos baldeações com o mais rápido (RF-BAL-03).

    Roda a F-ROTA (mais rápido no G_E) e a F-BALD (mínimo k de baldeações na G_L). Se o
    mais rápido já faz até k baldeações, não há o que evitar e ele mesmo é a resposta;
    senão, procura no G_E o mais rápido com até k baldeações (mais_rapido_com_limite).

    Entradas:
        ge, gl: G_E e G_L da mesma faixa, montadas da mesma rede com os mesmos Parametros
            (construir_ge(rede, faixa, params, esperas) e construir_gl(rede, params, faixa)).
        origem, destino: ids de paradas do GTFS.
    Saída: ComparacaoBaldeacoes, com tempo_a_mais_s e baldeacoes_evitadas; None se o
        destino não é alcançável no G_E ou na G_L.
    Casos de borda: origem == destino compara dois trajetos vazios (0 s, 0 baldeações);
        parada inexistente levanta KeyError; G_L do dia inteiro (faixa None) ou de outra
        faixa levanta ValueError, porque as linhas que circulam mudam com a faixa. O mais
        rápido pode fazer menos baldeações que o k da G_L, porque no G_E as caminhadas se
        encadeiam e na G_L é uma de até 300 m por vez (decisão B3 da F-BALD); aí ele é a
        resposta e nada é evitado. Se a G_L acha trajeto e o G_E com limite k não, as duas
        visões não vêm da mesma rede e parâmetros: levanta ValueError.
    Complexidade: a soma das três buscas. Tempo O((V + E) log V) da F-ROTA, mais
        O(r (V_L + E_L + T) + s) da F-BALD, mais O((k + 2)(V + E) log((k + 2) V)) do limite
        quando ele roda; espaço O((k + 2)(V + E) + r V_L).
    """
    if gl.faixa != ge.faixa:
        raise ValueError(
            f"G_L ({gl.faixa or 'dia inteiro'}) e G_E ({ge.faixa}) precisam ser da mesma faixa"
        )
    rapido = trajeto_mais_rapido(ge, origem, destino)
    menos = menos_baldeacoes(gl, origem, destino)
    if rapido is None or menos is None:
        return None
    if rapido.baldeacoes <= menos.baldeacoes:
        return ComparacaoBaldeacoes(rapido, menos, rapido)
    restrito = mais_rapido_com_limite(ge, origem, destino, menos.baldeacoes)
    if restrito is None:
        raise ValueError(
            "a G_L tem trajeto com "
            f"{menos.baldeacoes} baldeação(ões) e o G_E não: as visões não vêm da mesma rede"
        )
    return ComparacaoBaldeacoes(rapido, menos, restrito)
