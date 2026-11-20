"""Tabela consolidada de complexidade e tempos (F-AVAL, RF-AVA-02).

Lê os JSON de ``benchmarks/resultados/`` e gera ``relatorio/secoes/tabela-desempenho.tex``:
algoritmo, feature, visão, complexidade teórica, |V|, |E| e tempo médio ± desvio amostral,
agrupados por máquina e feed. Tempo de parede só é comparável dentro do mesmo grupo.

Os JSON têm formatos diferentes (cada feature gravou o seu), então cada arquivo tem um
extrator próprio. Algumas medições foram registradas só no arquivo da feature, sem JSON
versionado (F-ROTA, F-ROTA-2, F-ROTA-OPC, F-BALD, F-BALD-2, F-EFI, F-RES); elas entram pela
lista ``REGISTRADAS_NA_FEATURE``, copiadas da seção Resultados com a fonte indicada, e são
marcadas com † na tabela. Nenhum número é inventado: o que o JSON ou a feature não traz
(desvio, máquina) sai como "--" ou "não registrada".

Uso, a partir da raiz do repositório:

    python benchmarks/consolidar.py

Complexidades: docstrings das funções medidas e docs/fontes/modelagem.md §3.5.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "benchmarks" / "resultados"
SAIDA = RAIZ / "relatorio" / "secoes" / "tabela-desempenho.tex"

# Processador do JSON -> nome registrado nos arquivos de feature da mesma máquina.
MAQUINAS = {
    "Intel64 Family 6 Model 183": "Intel Core i5-13600KF (Windows 11)",
    "Intel64 Family 6 Model 186": "Intel Core 5 120U (Windows 11)",
    "macOS": "Apple M4 (macOS arm64)",
}

# Prefixo do SHA-256 do bhtrans.zip -> descrição do feed (arquivos P0-DADOS, F-BALD, F-ROTA).
FEEDS = {
    "8cb0a498": "feed baixado em 18/11, serviço de 18/11",
    "241f0bb2": "feed de 11/11 (SHA 241f0bb2), serviço de 11/11",
    "459f3a58": "feed baixado em 11/11, serviço de 04/11",
    "623bdf42": "feed baixado em 05/11, serviço de 04/11",
}

ORDEM_GRUPOS = [
    "Intel Core i5-13600KF (Windows 11)",
    "Intel Core 5 120U (Windows 11)",
    "Intel Core i5-1235U (Windows 11)",
    "AMD Ryzen 7 7730U (Windows 11)",
    "Apple M4 (macOS arm64)",
]


@dataclass
class Linha:
    algoritmo: str
    feature: str
    visao: str
    complexidade: str
    v: int | None
    e: int | None
    media_s: float | None
    desvio_s: float | None
    n: int | None
    maquina: str
    feed: str
    nota: str = ""
    da_feature: bool = False


_UNIDADE = {"s": 1.0, "ms": 1e-3, "µs": 1e-6, "us": 1e-6}
_TEMPO = re.compile(r"([\d.]+)\s*(s|ms|µs|us)\s*±\s*([\d.]+)\s*(s|ms|µs|us)\s*\(n=(\d+)\)")


def ler_tempo(texto: str) -> tuple[float, float, int]:
    """'2.183 s ± 0.013 s (n=3)' -> (2.183, 0.013, 3), em segundos."""
    m = _TEMPO.search(texto)
    if not m:
        raise ValueError(f"tempo ilegível: {texto!r}")
    return (
        float(m.group(1)) * _UNIDADE[m.group(2)],
        float(m.group(3)) * _UNIDADE[m.group(4)],
        int(m.group(5)),
    )


def de_dict(d: dict) -> tuple[float, float, int]:
    return d["media_s"], d["desvio_s"], d["repeticoes"]


def maquina(dados: dict) -> str:
    m = dados.get("maquina")
    texto = json.dumps(m) if m is not None else ""
    for chave, nome in MAQUINAS.items():
        if chave in texto:
            return nome
    return "não registrada"


# JSON sem SHA cujo arquivo de feature registra o SHA do feed usado.
SHA_NA_FEATURE = {
    "metricas-extensoes-": "8cb0a498",  # feature-F-MET-2.md e feature-F-MET-OPC.md
}


def feed(dados: dict, nome: str = "") -> str:
    f = dados.get("feed")
    sha = dados.get("sha256") or (f.get("sha256") if isinstance(f, dict) else None)
    for prefixo, sha_feature in SHA_NA_FEATURE.items():
        if not sha and nome.startswith(prefixo):
            sha = sha_feature
    if sha:
        return FEEDS.get(sha[:8], f"feed SHA {sha[:8]}")
    dia = dados.get("dia") or dados.get("rede", {}).get("dia")
    if dia:
        _, m, d = dia.split("-")
        return f"serviço de {d}/{m}, SHA não registrado"
    return "feed não registrado"


def ler(nome: str) -> dict | None:
    caminho = RESULTADOS / nome
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))


def linha(dados: dict, *args, **kw) -> Linha:
    return Linha(*args, maquina=maquina(dados), feed=feed(dados, dados.get("_arquivo", "")), **kw)


# ---------------------------------------------------------------- extratores por arquivo


def de_comparacao_networkx(d: dict) -> list[Linha]:
    real = next(g for g in d["grafos"] if "feed real" in g["grafo"])
    nomes = {
        "BFS": ("BFS, 20 origens", "P0-GRAFO", "$O(V + E)$ por origem"),
        "Dijkstra": ("Dijkstra, 20 origens", "P0-GRAFO", "$O((V + E)\\log V)$ por origem"),
        "Brandes": ("Brandes, 20 origens", "F-MET", "$O(k(V + E)\\log V)$"),
        "Tarjan": ("Tarjan iterativo", "F-RES", "$O(V + E)$"),
    }
    saida = []
    for a in real["algoritmos"]:
        chave = next(k for k in nomes if a["algoritmo"].startswith(k))
        rot, feat, comp = nomes[chave]
        saida.append(
            linha(
                d,
                rot,
                feat,
                "$G_P$",
                comp,
                real["V"],
                real["E"],
                a["nosso_media_s"],
                a["nosso_desvio_s"],
                d["repeticoes"],
            )
        )
    return saida


def de_metricas_extensoes(d: dict) -> list[Linha]:
    v, e = d["G_P"]["V"], d["G_P"]["E"]
    m, s, n = ler_tempo(d["proximidade_amostrada"]["50"]["tempo"])
    c = d["comunidades"]
    mr, sr, nr = ler_tempo(c["tempo_propagacao"])
    return [
        linha(
            d, "Proximidade, $k = 50$", "F-MET-2", "$G_P$", "$O(k(V + E)\\log V)$", v, e, m, s, n
        ),
        linha(
            d,
            f"Propagação de rótulos ({c['iteracoes']} it.)",
            "F-MET-OPC",
            "$G_P$",
            "$O(V + E)$ por iteração",
            v,
            e,
            mr,
            sr,
            nr,
        ),
    ]


def de_nao_dominados(d: dict) -> list[Linha]:
    t = d["tempo_por_par_ms"]
    return [
        linha(
            d,
            "Fronteira de Pareto, por par",
            "F-BALD-OPC",
            "$G_E$",
            "$O(B^2(V + E)\\log(BV))$",
            d["ge"]["V"],
            d["ge"]["E"],
            t["media"] / 1000,
            None,
            d["pares"],
            nota="méd.",
        )
    ]


def de_falhas_extensoes(d: dict) -> list[Linha]:
    v, e = d["G_P"]["V"], d["G_P"]["E"]
    r = d["ranking"]
    mr, sr, nr = ler_tempo(r["tempo_ranking"])
    ms, ss, ns = ler_tempo(d["sequencias"]["dirigida"]["tempo"])
    k = d["parametros"]["k"]
    return [
        linha(
            d,
            f"Ranking, {r['candidatos']} candidatos",
            "F-RES-2",
            "$G_P$",
            "$O((c + 1)s(V + E)\\log V)$",
            v,
            e,
            mr,
            sr,
            nr,
        ),
        linha(
            d,
            f"Falhas em sequência, {k} passos",
            "F-RES-OPC",
            "$G_P$",
            "$O((k + 1)s(V + E)\\log V)$",
            v,
            e,
            ms,
            ss,
            ns,
        ),
    ]


def de_centralidade(d: dict) -> list[Linha]:
    v, e = d["G_P"]["V"], d["G_P"]["E"]
    mg, sg, ng = ler_tempo(d["graus"]["tempo_todas"])
    ma, sa, na = ler_tempo(d["amostras"]["50"]["tempo"])
    return [
        linha(d, "Graus de entrada e saída", "F-MET", "$G_P$", "$O(V + E)$", v, e, mg, sg, ng),
        linha(
            d,
            "Brandes amostrado, $k = 50$",
            "F-MET",
            "$G_P$",
            "$O(k(V + E)\\log V)$",
            v,
            e,
            ma,
            sa,
            na,
        ),
        linha(
            d,
            "Brandes exato",
            "F-MET",
            "$G_P$",
            "$O(V(V + E)\\log V)$",
            v,
            e,
            d["exato"]["segundos_uma_execucao"],
            None,
            1,
        ),
    ]


def de_nucleo(d: dict) -> list[Linha]:
    ge = next(x for x in d["visoes"] if x["visao"].startswith("G_E"))
    m, s, n = ler_tempo(ge["dijkstra_20_origens"])
    mh, sh, nh = ler_tempo(d["heap_100k_inserir_e_extrair"])
    return [
        linha(
            d,
            "Dijkstra, 20 origens",
            "P0-GRAFO",
            "$G_E$",
            "$O((V + E)\\log V)$ por origem",
            ge["V"],
            ge["E"],
            m,
            s,
            n,
        ),
        linha(
            d,
            "Heap: $10^5$ inserções e extrações",
            "P0-GRAFO",
            "--",
            "$O(n\\log n)$",
            None,
            None,
            mh,
            sh,
            nh,
        ),
    ]


def de_espera(d: dict) -> list[Linha]:
    t = d["tempos"]
    return [
        linha(
            d,
            "Simulação de trajeto completa",
            "F-ESPERA",
            "$G_E$",
            "$O(N\\log N + PF + FN) + O((V + E)\\log V)$",
            d["V"],
            d["E"],
            *de_dict(t["simular_trajeto_completo"]),
        )
    ]


def de_quadro_horarios(d: dict) -> list[Linha]:
    t = d["tempos"]
    n_mc = len(d.get("amostras", []))
    return [
        linha(
            d,
            "Construção de $G_T$",
            "F-ESPERA-2",
            "$G_T$",
            "$O(V + L + K + N\\log(k + 1))$",
            d["V"],
            d["E"],
            *de_dict(t["construir_gt"]),
        ),
        linha(
            d,
            "Chegada mais cedo",
            "F-ESPERA-2",
            "$G_T$",
            "$O((V + E)\\log E + E\\log(k + 1))$",
            d["V"],
            d["E"],
            *de_dict(t["chegada_mais_cedo"]),
        ),
        linha(
            d,
            f"Monte Carlo, {n_mc} saídas",
            "F-ESPERA-2",
            "$G_T$",
            "$S$ consultas",
            d["V"],
            d["E"],
            *de_dict(t["monte_carlo"]),
        ),
    ]


def de_sensibilidade(d: dict) -> list[Linha]:
    n_pares = len(d["pares"])
    return [
        linha(
            d,
            f"Sensibilidade, {n_pares} pares",
            "F-ESPERA-OPC",
            "$G_E$",
            "$O(n(V + E)\\log V)$",
            d["V"],
            d["E"],
            *de_dict(d["tempos"]["sensibilidade_intervalo"]),
        )
    ]


def de_efi_2(d: dict) -> list[Linha]:
    m = d["medicoes"]
    return [
        linha(
            d,
            "Isócrona, 60 min",
            "F-EFI-2",
            "$G_E$",
            "$O((V' + E')\\log E')$",
            d["V"],
            d["E"],
            *de_dict(m["isocrona"]),
        ),
        linha(
            d,
            f"Índice de desvio, {d['pares']} pares",
            "F-EFI-2",
            "$G_E$",
            "$O(m(V + E)\\log E)$",
            d["V"],
            d["E"],
            *de_dict(m["indices_desvio"]),
        ),
    ]


def de_efi_opc(d: dict) -> list[Linha]:
    f = d["faixas"][0]
    return [
        linha(
            d,
            f"Comparação de 4 faixas, {d['pares']} pares",
            "F-EFI-OPC",
            "$G_E$",
            "$O(F(k(V + E)\\log E))$",
            f["vertices"],
            f["arestas"],
            *de_dict(d["medicoes"]["comparar_faixas"]),
        )
    ]


EXTRATORES = {
    "comparacao-networkx-": de_comparacao_networkx,
    "metricas-extensoes-": de_metricas_extensoes,
    "nao-dominados-": de_nao_dominados,
    "falhas-extensoes-": de_falhas_extensoes,
    "centralidade-": de_centralidade,
    "nucleo-": de_nucleo,
    "espera-": de_espera,
    "quadro-horarios-bhtrans": de_quadro_horarios,
    "sensibilidade-": de_sensibilidade,
    "f-efi-2-": de_efi_2,
    "f-efi-opc-": de_efi_opc,
}

# Medições sem JSON versionado, copiadas da seção Resultados do arquivo de feature indicado.
_I5_13600 = "Intel Core i5-13600KF (Windows 11)"
_I5_1235 = "Intel Core i5-1235U (Windows 11)"
REGISTRADAS_NA_FEATURE = [
    Linha(
        "Dijkstra, 200 consultas",
        "F-ROTA",
        "$G_E$",
        "$O((V + E)\\log V)$",
        46102,
        209025,
        13.177,
        0.106,
        5,
        _I5_13600,
        FEEDS["8cb0a498"],
        da_feature=True,
    ),
    Linha(
        "A*, por busca",
        "F-ROTA-2",
        "$G_E$",
        "$O((V + E)\\log V)$",
        46102,
        209025,
        0.0810,
        None,
        200,
        _I5_13600,
        FEEDS["8cb0a498"],
        nota="med.",
        da_feature=True,
    ),
    Linha(
        "Yen, $k = 5$, por consulta",
        "F-ROTA-OPC",
        "$G_E$",
        "$O(k\\,n(V + E)\\log V)$",
        46102,
        209025,
        4.3,
        None,
        20,
        _I5_13600,
        FEEDS["8cb0a498"],
        nota="med.",
        da_feature=True,
    ),
    Linha(
        "Construção de $G_L$ (pico)",
        "F-BALD",
        "$G_L$",
        "$O(V + K\\log K + L + C)$",
        501,
        85606,
        3.092,
        0.020,
        5,
        _I5_1235,
        FEEDS["459f3a58"],
        da_feature=True,
    ),
    Linha(
        "BFS por camadas, 200 consultas",
        "F-BALD",
        "$G_L$",
        "$O(r(V + E + T))$",
        501,
        85606,
        7.335,
        0.171,
        5,
        _I5_1235,
        FEEDS["459f3a58"],
        da_feature=True,
    ),
    Linha(
        "Comparação com limite, por par",
        "F-BALD-2",
        "$G_E$",
        "$O((k + 2)(V + E)\\log((k + 2)V))$",
        46100,
        208956,
        0.2129,
        None,
        200,
        _I5_1235,
        FEEDS["459f3a58"],
        nota="méd.",
        da_feature=True,
    ),
    Linha(
        "Tarjan iterativo",
        "F-RES",
        "$G_P$",
        "$O(V + E)$",
        9659,
        122732,
        0.2241,
        0.0699,
        3,
        _I5_1235,
        FEEDS["459f3a58"],
        da_feature=True,
    ),
    Linha(
        "Falha de uma linha, $s = 100$",
        "F-RES",
        "$G_P$",
        "$O(s(V + E)\\log V)$",
        9659,
        122732,
        38.0,
        4.5,
        3,
        _I5_1235,
        FEEDS["459f3a58"],
        da_feature=True,
    ),
    Linha(
        "Eficiência global, $s = 100$",
        "F-EFI",
        "$G_P$",
        "$O(V + s(V + E)\\log V)$",
        9660,
        122799,
        8.696,
        0.130,
        3,
        "AMD Ryzen 7 7730U (Windows 11)",
        FEEDS["8cb0a498"],
        da_feature=True,
    ),
    Linha(
        "Tempo médio de viagem, 100 pares",
        "F-EFI",
        "$G_E$",
        "$O(V + k(V + E)\\log V + m)$",
        46102,
        209025,
        26.321,
        0.125,
        3,
        "AMD Ryzen 7 7730U (Windows 11)",
        FEEDS["8cb0a498"],
        da_feature=True,
    ),
]


# Linhas que o relatório já mostra em outro lugar, omitidas para a tabela caber em meia
# página: (algoritmo, máquina) -> onde está.
OMITIDAS = {
    ("Brandes amostrado, $k = 50$", "Intel Core 5 120U (Windows 11)"): "sec:F-MET",
    ("Dijkstra, 20 origens", "Intel Core 5 120U (Windows 11)"): "sec:impl",
    ("Tarjan iterativo", _I5_1235): "sec:F-RES",
}


def coletar() -> list[Linha]:
    linhas = list(REGISTRADAS_NA_FEATURE)
    for caminho in sorted(RESULTADOS.glob("*.json")):
        for prefixo, extrator in EXTRATORES.items():
            if caminho.name.startswith(prefixo):
                dados = json.loads(caminho.read_text(encoding="utf-8"))
                dados["_arquivo"] = caminho.name
                linhas.extend(extrator(dados))
                break
    return [li for li in linhas if (li.algoritmo, li.maquina) not in OMITIDAS]


# ---------------------------------------------------------------- LaTeX


def fmt_num(x: float, casas: int) -> str:
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", "{.}")


def fmt_tempo(media: float | None, desvio: float | None) -> str:
    if media is None:
        return "--"
    if media >= 1:
        un, f = "s", 1.0
    else:
        un, f = "ms", 1e3
    m = media * f
    casas = 0 if m >= 100 else (1 if m >= 10 else 2)
    if desvio is None:
        return f"{fmt_num(m, casas)} {un}"
    return f"{fmt_num(m, casas)} $\\pm$ {fmt_num(desvio * f, casas)} {un}"


def fmt_int(x: int | None) -> str:
    return "--" if x is None else fmt_num(x, 0)


def gerar(linhas: list[Linha]) -> str:
    grupos: dict[tuple[str, str], list[Linha]] = {}
    for li in linhas:
        grupos.setdefault((li.maquina, li.feed), []).append(li)

    def ordem(chave: tuple[str, str]) -> tuple[int, str]:
        m = chave[0]
        return (ORDEM_GRUPOS.index(m) if m in ORDEM_GRUPOS else len(ORDEM_GRUPOS), chave[1])

    out = [
        "% Gerado por benchmarks/consolidar.py a partir de benchmarks/resultados/*.json e da",
        "% seção Resultados dos arquivos de feature (marcados com \\dag). Não editar à mão.",
        "\\begin{table}[htbp]",
        "\\centering",
        (
            "\\caption{Complexidade teórica e tempo medido com \\texttt{medir}, por máquina e "
            "feed: média $\\pm$ desvio amostral de $n$ execuções, ou só a média (méd.) ou a "
            "mediana (med.) de $n$ consultas quando a fonte não traz o desvio. $\\dag$: número "
            "registrado só no arquivo da feature, sem JSON. Tempos de grupos diferentes não "
            "são comparáveis entre si.}"
        ),
        "\\label{tab:desempenho}",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3pt}",
        (
            "\\begin{tabularx}{\\textwidth}{@{}>{\\raggedright\\arraybackslash}p{3.7cm} l l "
            ">{\\raggedright\\arraybackslash}X r r r r@{}}"
        ),
        "\\toprule",
        "Algoritmo e escopo & Feature & Visão & Complexidade & $|V|$ & $|E|$ & Tempo & $n$ \\\\",
        "\\midrule",
    ]
    for chave in sorted(grupos, key=ordem):
        maq, fd = chave
        out.append(f"\\multicolumn{{8}}{{@{{}}l}}{{\\textit{{{maq}; {fd}}}}} \\\\")
        for li in grupos[chave]:
            nome = li.algoritmo + (" $\\dag$" if li.da_feature else "")
            desvio = None if li.n == 1 else li.desvio_s
            tempo = fmt_tempo(li.media_s, desvio)
            if li.nota:
                tempo += f" ({li.nota})"
            n = "--" if li.n is None else str(li.n)
            out.append(
                f"{nome} & {li.feature} & {li.visao} & {li.complexidade} & {fmt_int(li.v)} & "
                f"{fmt_int(li.e)} & {tempo} & {n} \\\\"
            )
    out += ["\\bottomrule", "\\end{tabularx}", "\\end{table}", ""]
    return "\n".join(out)


def main() -> None:
    linhas = coletar()
    SAIDA.write_text(gerar(linhas), encoding="utf-8")
    print(f"{len(linhas)} linhas em {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
