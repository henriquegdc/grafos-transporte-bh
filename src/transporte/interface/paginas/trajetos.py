"""Página Trajetos: trajeto mais rápido entre dois pontos, no mapa (F-ROTA e extensões).

Segue o contrato da P0-UI, `render(rede)`. A página monta o G_E uma vez por sessão, rede
carregada e faixa, com as esperas estimadas pela F-ESPERA (H/2 por padrão e faixa).

- RF-ROT-01 e RF-ROT-02 (F-ROTA): `trajeto_mais_rapido` e o trajeto no mapa, por trecho
  (a pé, espera, linha usada), com os tempos.
- RF-ROT-03 (F-ROTA-2): origem e destino por clique no mapa ou por coordenadas, cada ponto
  ligado à parada mais próxima; a caminhada até ela entra no tempo porta a porta.
- RF-ROT-04 (F-ROTA-2): a mesma consulta com A* e Dijkstra, com vértices expandidos e tempo,
  guardada na sessão por consulta.
- RF-ROT-05 (F-ROTA-OPC): até k trajetos alternativos pelo Yen, um por sequência de linhas,
  sob demanda (é a consulta cara).

estado: implementado
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from html import escape
from time import perf_counter

import folium
import streamlit as st
from streamlit_folium import st_folium

from transporte.algoritmos.a_estrela import (
    Comparacao,
    comparar,
    coordenadas_ge,
    parada_mais_proxima,
    velocidade_maxima,
)
from transporte.algoritmos.alternativos import Alternativo, alternativos_por_linhas
from transporte.algoritmos.trajeto import A_PE, ESPERA, ONIBUS, Trajeto, trajeto_mais_rapido
from transporte.grafo.buscas import INF
from transporte.interface.mapa import atualizar_controle_camadas, criar_mapa
from transporte.interface.protocolos import RedeUI
from transporte.modelo.construtores import construir_ge
from transporte.modelo.parametros import Parametros
from transporte.modelo.visoes import VisaoGE
from transporte.simulacao.espera import calcular_esperas, estimar_intervalos

CHAVE_GE = "f-rota-ge"
CHAVE_CLIQUE = "f-rota-ultimo-clique"
CHAVE_ALTERNATIVOS = "f-rota-alternativos"
CHAVE_COMPARACAO = "f-rota-comparacao"
MODO_LISTA = "Lista de paradas"
MODO_PONTO = "Mapa ou coordenadas"
ORIGEM, DESTINO = "origem", "destino"
ROTULOS = {A_PE: "A pé", ESPERA: "Espera", ONIBUS: "Ônibus"}
K_MAXIMO = 5


@dataclass(frozen=True)
class GEPreparado:
    """G_E de uma faixa com o que o A* precisa: coordenadas por vértice e vmax (m/s)."""

    ge: VisaoGE
    coords: list[tuple[float, float]]
    vmax: float


@dataclass(frozen=True)
class Ponto:
    """Ponto escolhido no mapa ou por coordenadas, ligado à parada mais próxima."""

    lat: float
    lon: float
    parada: str
    distancia_m: float
    caminhada_s: float


def ge_da_faixa(rede: RedeUI, faixa: str, params: Parametros, cache: MutableMapping) -> GEPreparado:
    """G_E da faixa com as esperas da F-ESPERA, montado uma vez por rede e faixa.

    `cache` é o `st.session_state` na página; a chave guarda `id(rede)` para descartar os
    G_E de uma rede anterior quando outra é carregada na mesma sessão. Tempo O(1) com o G_E
    pronto; senão o de `estimar_intervalos` (uma vez por rede), o de `construir_ge` e O(V + E)
    das coordenadas e da velocidade máxima.
    """
    guardado = cache.get(CHAVE_GE)
    if guardado is None or guardado["rede"] != id(rede):
        esperas = calcular_esperas(estimar_intervalos(rede, params))
        guardado = {"rede": id(rede), "esperas": esperas, "ges": {}}
        cache[CHAVE_GE] = guardado
    if faixa not in guardado["ges"]:
        ge = construir_ge(rede, faixa, params, guardado["esperas"])
        coords = coordenadas_ge(ge, rede.paradas)
        guardado["ges"][faixa] = GEPreparado(ge, coords, velocidade_maxima(ge, coords))
    return guardado["ges"][faixa]


def _nome(rede: RedeUI, parada_id: str) -> str:
    parada = rede.paradas[parada_id]
    return f"{getattr(parada, 'nome', '') or parada_id} ({parada_id})"


def _linha(rede: RedeUI, padrao_id: str | None) -> str:
    """Nome da linha do padrão, ou o id da linha, ou o id do padrão; "" a pé. O(1)."""
    if padrao_id is None:
        return ""
    padrao = rede.padroes.get(padrao_id)
    if padrao is None:
        return padrao_id
    linha = rede.linhas.get(padrao.linha_id)
    return str(getattr(linha, "nome", None) or padrao.linha_id)


def minutos(segundos: float) -> str:
    """Duração como "12 min 05 s" (arredondada ao segundo). O(1)."""
    m, s = divmod(round(segundos), 60)
    return f"{m} min {s:02d} s"


def tabela_trechos(rede: RedeUI, trajeto: Trajeto) -> list[dict[str, str]]:
    """Linhas da tabela: trecho, modo, linha, de, para, paradas e tempo. O(k)."""
    return [
        {
            "Trecho": str(numero),
            "Modo": ROTULOS[t.tipo],
            "Linha": _linha(rede, t.padrao),
            "De": _nome(rede, t.paradas[0]),
            "Para": _nome(rede, t.paradas[-1]),
            "Paradas": "" if t.tipo == ESPERA else str(len(t.paradas) - 1),
            "Tempo": minutos(t.tempo_s),
        }
        for numero, t in enumerate(trajeto.trechos, start=1)
    ]


def tabela_comparacao(c: Comparacao) -> list[dict[str, str]]:
    """Linhas da comparação de RF-ROT-04: algoritmo, expandidos, tempo e custo. O(1)."""
    linhas = []
    for nome, busca in (("Dijkstra", c.dijkstra), ("A*", c.a_estrela)):
        custo = busca.trajeto.tempo_total_s if busca.trajeto else None
        linhas.append(
            {
                "Algoritmo": nome,
                "Vértices expandidos": str(busca.expandidos),
                "Tempo da busca": f"{1e3 * busca.tempo_s:.1f} ms",
                "Tempo do trajeto": "sem trajeto" if custo is None else minutos(custo),
            }
        )
    return linhas


def resumo_linhas(rede: RedeUI, trajeto: Trajeto) -> str:
    """Sequência das linhas usadas, como "Linha 1 → Linha 2"; "a pé" sem ônibus. O(k)."""
    nomes = [_linha(rede, t.padrao) for t in trajeto.trechos if t.tipo == ONIBUS]
    return " → ".join(nomes) if nomes else "a pé"


def tabela_alternativos(
    rede: RedeUI, alternativos: list[Alternativo], acesso_s: float | None = None
) -> list[dict[str, str]]:
    """Uma linha por sequência de linhas: posição, tempo, baldeações, linhas, a pé e variantes.

    Com `acesso_s` (modo "Mapa ou coordenadas"), acrescenta o tempo porta a porta, que soma a
    caminhada dos pontos às paradas; "Tempo total" é sempre entre as paradas. O(k·n).
    """
    linhas = []
    for i, alt in enumerate(alternativos, start=1):
        t = alt.trajeto
        linha = {"Trajeto": str(i), "Tempo total": minutos(t.tempo_total_s)}
        if acesso_s is not None:
            linha["Tempo porta a porta"] = minutos(t.tempo_total_s + acesso_s)
        linha |= {
            "Baldeações": str(t.baldeacoes),
            "Linhas": resumo_linhas(rede, t),
            "A pé": minutos(t.tempo_por_tipo()[A_PE]),
            "Variantes": str(alt.variantes),
        }
        linhas.append(linha)
    return linhas


def ligar_ponto(rede: RedeUI, lat: float, lon: float, params: Parametros) -> Ponto:
    """Liga o ponto à parada mais próxima em linha reta (RF-ROT-03). Tempo O(V)."""
    parada, distancia = parada_mais_proxima(rede.paradas, lat, lon)
    return Ponto(lat, lon, parada, distancia, distancia / params.velocidade_caminhada_ms)


def longe_da_rede(ponto: Ponto, params: Parametros) -> bool:
    """True se o ponto está além do raio de caminhada da sua parada mais próxima. O(1)."""
    return ponto.distancia_m > params.raio_caminhada_m


def _chaves(alvo: str) -> tuple[str, str]:
    return f"f-rota-lat-{alvo}", f"f-rota-lon-{alvo}"


def aplicar_clique(estado: MutableMapping, clique: Mapping | None, alvo: str) -> bool:
    """Copia um clique novo do mapa para as coordenadas do alvo (origem ou destino).

    O `st_folium` devolve o último clique em toda execução, não só na do clique; por isso o
    último clique aplicado fica guardado e um clique repetido não sobrescreve coordenadas
    digitadas depois dele. Precisa rodar antes de criar os campos de coordenada, porque o
    Streamlit não deixa mudar o valor de um campo já criado na execução.
    Saída: True se aplicou. O(1).
    """
    if not clique or "lat" not in clique or "lng" not in clique:
        return False
    ponto = (float(clique["lat"]), float(clique["lng"]))
    if estado.get(CHAVE_CLIQUE) == ponto:
        return False
    estado[CHAVE_CLIQUE] = ponto
    chave_lat, chave_lon = _chaves(alvo)
    estado[chave_lat], estado[chave_lon] = ponto
    return True


def mapa_trajeto(rede: RedeUI, trajeto: Trajeto, pontos: tuple[Ponto, ...] = ()) -> folium.Map:
    """Mapa base da P0-UI com o trajeto por trecho, enquadrado nas paradas do trajeto.

    Com pontos escolhidos no mapa (RF-ROT-03), desenha cada ponto e a caminhada em linha
    reta até a sua parada. Sem a camada de paradas (os 9.659 marcadores do feed real pesam).
    Tempo O(P + k), P paradas da rede (centro do mapa) e k paradas do trajeto.
    """
    mapa = criar_mapa(rede, mostrar_paradas=False, trajeto=trajeto)
    paradas = {trajeto.origem, trajeto.destino, *(p for t in trajeto.trechos for p in t.paradas)}
    latitudes = [float(rede.paradas[p].lat) for p in paradas]
    longitudes = [float(rede.paradas[p].lon) for p in paradas]
    if pontos:
        camada = folium.FeatureGroup(name="Pontos escolhidos e acesso a pé")
        for rotulo, ponto in zip(("Origem", "Destino"), pontos, strict=False):
            parada = rede.paradas[ponto.parada]
            texto = escape(
                f"{rotulo} escolhida: {ponto.distancia_m:.0f} m a pé até "
                f"{_nome(rede, ponto.parada)} ({minutos(ponto.caminhada_s)})"
            )
            folium.CircleMarker(
                (ponto.lat, ponto.lon), radius=6, color="#444444", fill=True, tooltip=texto
            ).add_to(camada)
            folium.PolyLine(
                [(ponto.lat, ponto.lon), (float(parada.lat), float(parada.lon))],
                color="#444444",
                weight=3,
                dash_array="6",
                tooltip=texto,
            ).add_to(camada)
            latitudes.append(ponto.lat)
            longitudes.append(ponto.lon)
        camada.add_to(mapa)
    mapa.fit_bounds([[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]])
    atualizar_controle_camadas(mapa)
    return mapa


def _mapa_de_escolha(rede: RedeUI, pontos: Mapping[str, Ponto]) -> folium.Map:
    """Mapa para clicar: só os pontos atuais e as suas paradas, sem o trajeto. O(P)."""
    mapa = criar_mapa(rede, mostrar_paradas=False)
    for alvo, cor in ((ORIGEM, "green"), (DESTINO, "red")):
        ponto = pontos[alvo]
        parada = rede.paradas[ponto.parada]
        folium.Marker(
            (ponto.lat, ponto.lon),
            tooltip=escape(f"{alvo.capitalize()}: {ponto.lat:.5f}, {ponto.lon:.5f}"),
            icon=folium.Icon(color=cor),
        ).add_to(mapa)
        folium.CircleMarker(
            (float(parada.lat), float(parada.lon)),
            radius=5,
            color=cor,
            tooltip=escape(f"Parada mais próxima: {_nome(rede, ponto.parada)}"),
        ).add_to(mapa)
    atualizar_controle_camadas(mapa)
    return mapa


def _rotulo_faixa(params: Parametros, nome: str) -> str:
    f = params.faixa(nome)
    return f"{f.nome} ({f.inicio_s // 3600:02d}h a {f.fim_s // 3600:02d}h)"


def _escolher_paradas(rede: RedeUI) -> tuple[str, str]:
    ids = sorted(rede.paradas, key=lambda p: (_nome(rede, p).casefold(), p))
    col_origem, col_destino = st.columns(2)
    origem = col_origem.selectbox(
        "Origem", ids, format_func=lambda p: _nome(rede, p), key="f-rota-origem"
    )
    destino = col_destino.selectbox(
        "Destino",
        ids,
        index=min(1, len(ids) - 1),
        format_func=lambda p: _nome(rede, p),
        key="f-rota-destino",
    )
    return origem, destino


def _escolher_pontos(rede: RedeUI, params: Parametros) -> tuple[Ponto, Ponto]:
    """Clique no mapa e campos de coordenada (RF-ROT-03). O(P) por execução."""
    ids = sorted(rede.paradas, key=lambda p: (_nome(rede, p).casefold(), p))
    for alvo, indice in ((ORIGEM, 0), (DESTINO, min(1, len(ids) - 1))):
        chave_lat, chave_lon = _chaves(alvo)
        if chave_lat not in st.session_state:
            parada = rede.paradas[ids[indice]]
            st.session_state[chave_lat] = float(parada.lat)
            st.session_state[chave_lon] = float(parada.lon)

    alvo = st.radio(
        "O próximo clique no mapa define",
        (ORIGEM, DESTINO),
        format_func=str.capitalize,
        horizontal=True,
        key="f-rota-alvo-clique",
    )
    atuais = {
        a: ligar_ponto(
            rede, st.session_state[_chaves(a)[0]], st.session_state[_chaves(a)[1]], params
        )
        for a in (ORIGEM, DESTINO)
    }
    retorno = st_folium(
        _mapa_de_escolha(rede, atuais),
        height=350,
        use_container_width=True,
        key="mapa-escolha-trajetos",
        returned_objects=["last_clicked"],
    )
    if aplicar_clique(st.session_state, (retorno or {}).get("last_clicked"), alvo):
        st.rerun()

    pontos = []
    for coluna, alvo_campo in zip(st.columns(2), (ORIGEM, DESTINO), strict=True):
        chave_lat, chave_lon = _chaves(alvo_campo)
        coluna.number_input(f"Latitude da {alvo_campo}", key=chave_lat, format="%.6f", step=1e-4)
        coluna.number_input(f"Longitude da {alvo_campo}", key=chave_lon, format="%.6f", step=1e-4)
        ponto = ligar_ponto(rede, st.session_state[chave_lat], st.session_state[chave_lon], params)
        coluna.caption(
            f"Parada mais próxima: {_nome(rede, ponto.parada)}, a {ponto.distancia_m:.0f} m "
            f"({minutos(ponto.caminhada_s)} a pé, em linha reta)."
        )
        if longe_da_rede(ponto, params):
            coluna.warning(
                f"A {alvo_campo} está a {ponto.distancia_m:.0f} m da parada mais próxima, "
                f"mais que o raio de caminhada ({params.raio_caminhada_m:.0f} m): o ponto "
                "pode estar fora da rede, e a caminhada até a parada entra inteira no tempo "
                "porta a porta."
            )
        pontos.append(ponto)
    return pontos[0], pontos[1]


def comparacao_em_cache(
    rede: RedeUI,
    preparado: GEPreparado,
    faixa: str,
    origem: str,
    destino: str,
    cache: MutableMapping,
) -> Comparacao:
    """Dijkstra × A* da consulta, calculado só quando a consulta muda (RF-ROT-04).

    `cache` é o `st.session_state`; a chave (id(rede), faixa, origem, destino) evita refazer
    as duas buscas a cada interação com a página (k, rádio, mapa). O(1) com a consulta
    guardada; senão o das duas buscas.
    """
    consulta = (id(rede), faixa, origem, destino)
    guardado = cache.get(CHAVE_COMPARACAO)
    if guardado is None or guardado[0] != consulta:
        guardado = (
            consulta,
            comparar(preparado.ge, preparado.coords, preparado.vmax, origem, destino),
        )
        cache[CHAVE_COMPARACAO] = guardado
    return guardado[1]


def _mostrar_alternativos(
    rede: RedeUI,
    preparado: GEPreparado,
    faixa: str,
    origem: str,
    destino: str,
    pontos: tuple[Ponto, ...] = (),
) -> None:
    """Seção do Yen (RF-ROT-05): roda só no botão e guarda o resultado da consulta.

    Mostra um trajeto por sequência de linhas (`alternativos_por_linhas`, teto de 2 · k
    caminhos do Yen), com quantas variantes de cada uma o Yen achou.
    """
    st.subheader("Trajetos alternativos (Yen)")
    k = st.number_input(
        "Quantos trajetos (k)", min_value=2, max_value=K_MAXIMO, value=3, key="f-rota-k"
    )
    consulta = (id(rede), faixa, origem, destino, int(k))
    if st.button("Listar trajetos alternativos", key="f-rota-yen"):
        linha_do_padrao = {pid: p.linha_id for pid, p in rede.padroes.items()}
        inicio = perf_counter()
        with st.spinner("Calculando os trajetos alternativos..."):
            alternativos = alternativos_por_linhas(
                preparado.ge,
                origem,
                destino,
                int(k),
                linha_do_padrao,
                preparado.coords,
                preparado.vmax,
            )
        st.session_state[CHAVE_ALTERNATIVOS] = (consulta, alternativos, perf_counter() - inicio)
    guardado = st.session_state.get(CHAVE_ALTERNATIVOS)
    if guardado is None or guardado[0] != consulta:
        st.caption(
            "Lista até k trajetos com sequências de linhas distintas, do mais rápido ao mais "
            "lento, pelo Yen. Faz uma busca por vértice do trajeto anterior, por isso só roda "
            "no botão: na rede inteira de BH, pode levar dezenas de segundos em trajetos longos."
        )
        return
    _consulta, alternativos, duracao = guardado
    caminhos = sum(a.variantes for a in alternativos)
    texto = (
        f"{len(alternativos)} sequência(s) de linhas em {duracao:.2f} s, entre {caminhos} "
        'caminho(s) do Yen. "Variantes" conta os caminhos com as mesmas linhas, que só '
        "mudam onde trocar ou o trecho a pé; a tabela mostra o mais rápido de cada uma."
    )
    if 0 < len(alternativos) < int(k):
        texto += (
            f" Não há {int(k)} sequências distintas entre os {caminhos} primeiros caminhos: "
            f"os outros são variantes do mesmo trajeto."
        )
    acesso = sum(p.caminhada_s for p in pontos) if pontos else None
    if acesso is not None:
        texto += (
            ' "Tempo total" é entre as paradas; "Tempo porta a porta" soma a caminhada '
            "dos pontos escolhidos às paradas."
        )
    st.caption(texto)
    st.dataframe(tabela_alternativos(rede, alternativos, acesso), hide_index=True, width="stretch")
    trajetos = [a.trajeto for a in alternativos]
    if len(trajetos) > 1:
        escolhido = st.selectbox(
            "Trajeto no mapa",
            range(len(trajetos)),
            format_func=lambda i: f"Trajeto {i + 1} ({minutos(trajetos[i].tempo_total_s)})",
            key="f-rota-alternativo-mapa",
        )
        st_folium(
            mapa_trajeto(rede, trajetos[escolhido], pontos),
            height=450,
            use_container_width=True,
            key="mapa-alternativos",
            returned_objects=[],
        )


def render(rede: RedeUI) -> None:
    """Página Trajetos (contrato da P0-UI)."""
    st.header("Trajeto mais rápido")
    if not rede.paradas:
        st.info("A rede carregada não tem paradas.")
        return
    params = Parametros()
    faixa = st.selectbox(
        "Faixa horária",
        [f.nome for f in params.faixas],
        format_func=lambda nome: _rotulo_faixa(params, nome),
        help="Só entram as linhas com partida na faixa; a espera de cada linha é H/2.",
    )
    modo = st.radio(
        "Origem e destino", (MODO_LISTA, MODO_PONTO), horizontal=True, key="f-rota-modo"
    )
    pontos: tuple[Ponto, ...] = ()
    if modo == MODO_LISTA:
        origem, destino = _escolher_paradas(rede)
    else:
        pontos = _escolher_pontos(rede, params)
        origem, destino = pontos[0].parada, pontos[1].parada

    with st.spinner("Montando o G_E da faixa (paradas e plataformas)..."):
        preparado = ge_da_faixa(rede, faixa, params, st.session_state)
    ge = preparado.ge
    inicio = perf_counter()
    trajeto = trajeto_mais_rapido(ge, origem, destino)
    duracao = perf_counter() - inicio

    if trajeto is None:
        st.warning("Sem trajeto entre essas paradas nesta faixa horária.")
        return
    parcelas = trajeto.tempo_por_tipo()
    acesso = sum(p.caminhada_s for p in pontos)
    colunas = st.columns(5)
    colunas[0].metric("Tempo total", minutos(trajeto.tempo_total_s))
    colunas[1].metric("A pé", minutos(parcelas[A_PE]))
    colunas[2].metric("Espera", minutos(parcelas[ESPERA]))
    colunas[3].metric("Ônibus", minutos(parcelas[ONIBUS]))
    colunas[4].metric("Baldeações", trajeto.baldeacoes)
    if pontos:
        st.metric(
            "Tempo porta a porta",
            minutos(trajeto.tempo_total_s + acesso),
            help="Tempo entre as paradas mais a caminhada em linha reta de cada ponto à sua parada.",
        )
    st.caption(
        f"Dijkstra em {1e3 * duracao:.0f} ms no G_E com {ge.grafo.num_vertices()} vértices e "
        f"{ge.grafo.num_arestas()} arestas. Caminhada de até {params.raio_caminhada_m:.0f} m "
        f"em linha reta a {params.velocidade_caminhada_ms:g} m/s; espera média H/2 da linha "
        "na faixa (horários programados, não a próxima partida exata)."
    )
    if not trajeto.trechos:
        st.info("Origem e destino são a mesma parada.")
        return
    st.dataframe(tabela_trechos(rede, trajeto), hide_index=True, width="stretch")
    st_folium(
        mapa_trajeto(rede, trajeto, pontos),
        height=500,
        use_container_width=True,
        key="mapa-trajetos",
        returned_objects=[],
    )
    st.caption("Cada trecho é uma camada do mapa, com o tempo no nome e na dica do traço.")

    st.subheader("Dijkstra × A*")
    c = comparacao_em_cache(rede, preparado, faixa, origem, destino, st.session_state)
    st.dataframe(tabela_comparacao(c), hide_index=True, width="stretch")
    if preparado.vmax == INF:
        st.caption("O G_E não tem aresta que mude de lugar: a heurística é 0 e o A* é o Dijkstra.")
    else:
        st.caption(
            f"Mesma busca para os dois, com o heap próprio; o A* soma ao custo a distância em "
            f"linha reta até o destino dividida por {preparado.vmax:.1f} m/s, a maior "
            "velocidade entre as arestas do G_E. Por isso não superestima, e os dois acham o "
            "mesmo tempo."
        )
    _mostrar_alternativos(rede, preparado, faixa, origem, destino, pontos)
