"""Leitura de GTFS em pasta ou ZIP, sem biblioteca de grafos. estado: implementado.

Para R linhas de CSV e N horários, a leitura usa O(R + N log N) de tempo
(ordenação dos horários) e O(R + N) de espaço.
"""

from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from collections import defaultdict
from datetime import date, timedelta
from itertools import pairwise
from pathlib import Path

from transporte.dados.modelo import Frequencia, Linha, Padrao, Parada, Rede, Viagem

OBRIGATORIOS = ("stops.txt", "routes.txt", "trips.txt", "stop_times.txt")
TABELAS_PEQUENAS = (
    "stops.txt", "routes.txt", "trips.txt", "calendar.txt", "calendar_dates.txt",
    "frequencies.txt", "feed_info.txt",
)


def _tabelas(caminho: Path) -> dict[str, list[dict[str, str]]]:
    if caminho.is_dir():
        nomes = {p.name for p in caminho.iterdir() if p.is_file()}
        faltantes = set(OBRIGATORIOS) - nomes
        if faltantes:
            raise ValueError(f"arquivos GTFS ausentes: {', '.join(sorted(faltantes))}")
        return {
            nome: list(csv.DictReader(io.StringIO((caminho / nome).read_text(encoding="utf-8-sig"))))
            for nome in nomes if nome in TABELAS_PEQUENAS
        }
    if zipfile.is_zipfile(caminho):
        with zipfile.ZipFile(caminho) as arquivo:
            membros = {Path(nome).name: nome for nome in arquivo.namelist() if not nome.endswith("/")}
            faltantes = set(OBRIGATORIOS) - membros.keys()
            if faltantes:
                raise ValueError(f"arquivos GTFS ausentes: {', '.join(sorted(faltantes))}")
            return {
                nome: list(csv.DictReader(io.StringIO(arquivo.read(membro).decode("utf-8-sig"))))
                for nome, membro in membros.items() if nome in TABELAS_PEQUENAS
            }
    raise ValueError(f"GTFS deve ser uma pasta ou ZIP: {caminho}")


def _horarios_em_fluxo(caminho: Path):
    """Itera stop_times.txt sem descompactar todo o arquivo na memória."""
    if caminho.is_dir():
        with (caminho / "stop_times.txt").open(encoding="utf-8-sig", newline="") as arquivo:
            yield from csv.DictReader(arquivo)
    else:
        with zipfile.ZipFile(caminho) as zip_arquivo:
            membro = next(n for n in zip_arquivo.namelist() if Path(n).name == "stop_times.txt")
            with (
                zip_arquivo.open(membro) as bruto,
                io.TextIOWrapper(bruto, encoding="utf-8-sig", newline="") as arquivo,
            ):
                yield from csv.DictReader(arquivo)


def _data(valor: str) -> date:
    return date.fromisoformat(f"{valor[0:4]}-{valor[4:6]}-{valor[6:8]}")


def _horario(valor: str) -> int:
    partes = valor.split(":")
    if len(partes) != 3:
        raise ValueError(valor)
    horas, minutos, segundos = map(int, partes)
    if horas < 0 or not 0 <= minutos < 60 or not 0 <= segundos < 60:
        raise ValueError(valor)
    return 3600 * horas + 60 * minutos + segundos


def _servicos(tabelas: dict[str, list[dict[str, str]]], dia: date) -> set[str]:
    ativos = set()
    dias = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    for linha in tabelas.get("calendar.txt", []):
        try:
            if (
                _data(linha["start_date"]) <= dia <= _data(linha["end_date"])
                and linha[dias[dia.weekday()]] == "1"
            ):
                ativos.add(linha["service_id"])
        except (KeyError, ValueError):
            continue
    for linha in tabelas.get("calendar_dates.txt", []):
        try:
            if _data(linha["date"]) == dia:
                if linha["exception_type"] == "1":
                    ativos.add(linha["service_id"])
                elif linha["exception_type"] == "2":
                    ativos.discard(linha["service_id"])
        except (KeyError, ValueError):
            continue
    return ativos


def _quarta_feira(tabelas: dict[str, list[dict[str, str]]]) -> date:
    limites = []
    for linha in tabelas.get("calendar.txt", []):
        try:
            limites.extend((_data(linha["start_date"]), _data(linha["end_date"])))
        except (KeyError, ValueError):
            continue
    for linha in tabelas.get("calendar_dates.txt", []):
        try:
            limites.append(_data(linha["date"]))
        except (KeyError, ValueError):
            continue
    if not limites:
        raise ValueError("feed sem calendário ou datas de serviço válidas")
    versoes = tabelas.get("feed_info.txt", [])
    if versoes:
        try:
            versao = _data(versoes[0]["feed_version"][:8])
            candidata = versao - timedelta(days=(versao.weekday() - 2) % 7)
            if min(limites) <= candidata <= max(limites) and _servicos(tabelas, candidata):
                return candidata
        except (KeyError, ValueError):
            pass
    atual = min(limites)
    atual += timedelta(days=(2 - atual.weekday()) % 7)
    ultimo = max(limites)
    while atual <= ultimo:
        if _servicos(tabelas, atual):
            return atual
        atual += timedelta(days=7)
    raise ValueError("feed sem quarta-feira com serviço ativo")


def _montar(caminho: Path, tabelas: dict[str, list[dict[str, str]]], dia: date) -> Rede:
    erros: list[str] = []
    paradas: dict[str, Parada] = {}
    for linha in tabelas["stops.txt"]:
        ident = linha.get("stop_id", "")
        try:
            lat, lon = float(linha["stop_lat"]), float(linha["stop_lon"])
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                raise ValueError("fora da faixa geográfica")
            if not ident:
                raise ValueError("stop_id vazio")
            paradas[ident] = Parada(ident, linha.get("stop_name", ""), lat, lon)
        except (KeyError, TypeError, ValueError):
            erros.append(f"parada {ident or '<vazia>'}: coordenada ou id inválido")
    linhas: dict[str, Linha] = {}
    for linha in tabelas["routes.txt"]:
        ident = linha.get("route_id", "")
        try:
            if not ident:
                raise ValueError("route_id vazio")
            linhas[ident] = Linha(
                ident,
                linha.get("route_short_name") or linha.get("route_long_name") or ident,
                int(linha.get("route_type", "3")),
            )
        except ValueError:
            erros.append(f"linha {ident or '<vazia>'}: tipo ou id inválido")
    viagens_gtfs = {linha.get("trip_id", ""): linha for linha in tabelas["trips.txt"]}
    horarios: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    servicos = _servicos(tabelas, dia)
    viagens_ativas = {
        ident for ident, linha in viagens_gtfs.items() if linha.get("service_id") in servicos
    }
    viagens_invalidas: set[str] = set()
    for linha in _horarios_em_fluxo(caminho):
        viagem_id = linha.get("trip_id", "")
        if viagem_id not in viagens_ativas:
            continue
        try:
            horario = _horario(linha.get("departure_time") or linha.get("arrival_time") or "")
            indice = int(linha["stop_sequence"])
            parada_id = linha["stop_id"]
            if indice < 0 or parada_id not in paradas:
                raise ValueError("sequência ou parada inválida")
            horarios[viagem_id].append((indice, horario, parada_id))
        except (KeyError, TypeError, ValueError):
            erros.append(f"viagem {viagem_id}: horário, sequência ou parada inválida")
            viagens_invalidas.add(viagem_id)
    padroes: dict[str, Padrao] = {}
    viagens: dict[str, Viagem] = {}
    padrao_por_chave: dict[tuple[str, tuple[str, ...]], str] = {}
    for ident, linha in viagens_gtfs.items():
        if ident not in viagens_ativas:
            continue
        if not ident or linha.get("route_id") not in linhas:
            erros.append(f"viagem {ident or '<vazia>'}: linha inexistente")
            continue
        pontos = sorted(horarios.get(ident, []))
        if len(pontos) < 2:
            erros.append(f"viagem {ident}: sem pelo menos duas paradas válidas")
            continue
        if ident in viagens_invalidas:
            continue
        if len({p[0] for p in pontos}) != len(pontos) or any(
            atual[1] > seguinte[1] for atual, seguinte in pairwise(pontos)
        ):
            erros.append(f"viagem {ident}: sequência ou horários fora de ordem")
            continue
        if linha.get("service_id") not in servicos:
            continue
        sequencia = tuple(p[2] for p in pontos)
        chave = (linha["route_id"], sequencia)
        if chave not in padrao_por_chave:
            digest = hashlib.sha1("\0".join(sequencia).encode()).hexdigest()[:12]
            padrao_id = f"{chave[0]}:{digest}"
            padroes[padrao_id] = Padrao(padrao_id, chave[0], sequencia)
            padrao_por_chave[chave] = padrao_id
        viagens[ident] = Viagem(
            ident, padrao_por_chave[chave], linha["service_id"], tuple(p[1] for p in pontos)
        )
    frequencias: list[Frequencia] = []
    for linha in tabelas.get("frequencies.txt", []):
        ident = linha.get("trip_id", "")
        if ident not in viagens:
            continue
        try:
            inicio = _horario(linha["start_time"])
            fim = _horario(linha["end_time"])
            intervalo = int(linha["headway_secs"])
            if inicio >= fim or intervalo <= 0:
                raise ValueError("janela ou intervalo inválido")
            frequencias.append(Frequencia(ident, inicio, fim, intervalo))
        except (KeyError, TypeError, ValueError):
            erros.append(f"frequência da viagem {ident}: horário ou intervalo inválido")
    rede = Rede(paradas, linhas, padroes, {}, viagens, tuple(frequencias), dia.isoformat(), erros)
    rede.recalcular_partidas()
    return rede


def validar(caminho: str | Path) -> list[str]:
    """Devolve inconsistências do feed; arquivos obrigatórios ausentes viram erro.

    Complexidade: tempo O(R + N log N), espaço O(R + N).
    """
    try:
        tabelas = _tabelas(Path(caminho))
        return _montar(Path(caminho), tabelas, _quarta_feira(tabelas)).inconsistencias
    except (OSError, ValueError, UnicodeError, zipfile.BadZipFile) as exc:
        return [str(exc)]


def ler(caminho: str | Path, dia: date | None = None) -> Rede:
    """Carrega serviços do dia; padrão: primeira quarta-feira ativa do feed.

    Linhas defeituosas entram em Rede.inconsistencias e são ignoradas na rede.
    Complexidade: tempo O(R + N log N), espaço O(R + N).
    """
    tabelas = _tabelas(Path(caminho))
    return _montar(Path(caminho), tabelas, dia or _quarta_feira(tabelas))
