# F-MET · Centralidades

**Período:** 1 · Essenciais (04/11 a 11/11) · **Classe:** prioritária
**Dono:** Thiago (@Thiagocs8) · **Issue:** #10 · **Visões do grafo:** G_P
**Depende de:** G_P de P0-MODELO · **Bloqueia:** F-MET-2
**Prazo:** 11/11 (checkpoint 07/11)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-MET-01, RF-MET-02, RF-MET-03). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 16/11, Thiago, branch `feat/F-MET-pagina`.
- **Onde parou:** etapas 1 a 6 feitas. Algoritmos na `main` desde o #37; nesta branch: `estimar_intermediacao` (amostragem de origens com erro padrão, RNF-06, decisão M5), a página Centralidades (ranking, distribuição de graus e mapa de calor, RF-MET-03), a medição no feed real com o Brandes exato como referência (`benchmarks/medir_centralidade.py`), Como funciona, perguntas, GUIA §5.4, diagrama de atividade, seção do relatório e roteiro. 224 testes de centralidade e 10 da página.
- **Próximo passo:** revisão do PR desta branch por outro integrante (Refs #10). Depois do merge: gerar `docs/diagramas/atividade-intermediacao.png` com o PlantUML 1.2026.9, fazer a captura da página para a figura do relatório e gravar o trecho do vídeo.
- **Arquivos tocados:** `src/transporte/algoritmos/centralidade.py`, `src/transporte/interface/paginas/centralidades.py`, `tests/algoritmos/test_centralidade.py`, `tests/interface/test_pagina_centralidades.py`, `benchmarks/medir_centralidade.py`, `benchmarks/resultados/centralidade-2026-11-16.json`, `docs/diagramas/atividade-intermediacao.puml`, `docs/GUIA.md` (§5.4, §8 e §10), `relatorio/secoes/F-MET.tex`, `relatorio/secoes/fundamentacao.tex`, `relatorio/referencias.bib`, este arquivo.
- **Como testar:** `pytest tests/algoritmos/test_centralidade.py tests/interface/test_pagina_centralidades.py`; `ruff check`; `python scripts/verificar_imports.py`. Página: `streamlit run src/transporte/interface/app.py`, carregar a rede e abrir Centralidades. Medição: `python scripts/baixar_gtfs.py` e `python benchmarks/medir_centralidade.py dados/brutos/bhtrans.zip --exato` (o exato leva cerca de 45 min na primeira vez e fica em `dados/cache/`).
- **Bloqueios:** nenhum para o merge. O PNG do diagrama depende do jar do PlantUML, fora do Git.

## Objetivo
Centralidades. Fecha:

- **RF-MET-01** (E): Calcular o grau de entrada e de saída de cada parada e a distribuição de graus
- **RF-MET-02** (E): Calcular a intermediação (Brandes) de cada parada
- **RF-MET-03** (E): Mostrar o ranking das paradas mais centrais e um mapa de calor

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 05/11: graus, distribuição, Brandes (com e sem pesos, normalização opcional) e ranking; 16/11: `estimar_intermediacao` (RNF-06) |
| Modelo e dados | concluído | 16/11: G_P do feed real (V = 9.660, E = 122.799), Brandes exato como referência |
| Interface | concluído | 16/11: página Centralidades; conferida com o feed real pelo AppTest, sem exceção |
| Testes | concluído | 16/11: 224 de centralidade e 10 da página; 05/11: 190 verdes; gabarito à mão, casos de borda (paralelas, laços, peso 0, desativação, grafos triviais) e comparação com o NetworkX (graus, graus por tipo, intermediação com e sem pesos, normalizada ou não) em grafos aleatórios com falhas; teste de mutação: sem a contagem de caminhos empatados, 32 testes falham |
| Desempenho (tempo medido) | concluído | 16/11: ver Resultados |
| Guia (explicação e quiz) | concluído | 16/11: Como funciona, perguntas e GUIA §5.4, §8 e §10 |
| Relatório | parcial | 16/11: `relatorio/secoes/F-MET.tex` e algoritmos na Fundamentação; falta a captura da página para a figura |
| Vídeo | parcial | 16/11: roteiro escrito; falta gravar |

## Especificação
Contrato em `src/transporte/algoritmos/centralidade.py` (estado: planejado em 05/11):

```python
@dataclass
class Graus:
    entrada: list[int]
    saida: list[int]

def graus(g: Grafo, tipos: Collection[str] | None = None) -> Graus: ...                 # O(V + E)
def distribuicao_graus(g: Grafo, valores: list[int]) -> dict[int, int]: ...             # O(V + D log D)
def intermediacao(g: Grafo, ponderado: bool = True, normalizar: bool = False) -> list[float]: ...
    # ponderado O(V (V + E) log V); sem pesos O(V (V + E)); espaço O(V + E)
def ranking(g: Grafo, valores: list[float], k: int) -> list[tuple[int, float]]: ...     # O(V log V)

# Acrescentado em 16/11 (RNF-06; decisão M5):
@dataclass(frozen=True)
class EstimativaIntermediacao:
    valores: list[float]; erro_padrao: list[float]
    tamanho_amostra: int; tamanho_populacao: int; semente: int
    exata: bool  # propriedade: amostra cobre todas as origens

def estimar_intermediacao(g: Grafo, tamanho_amostra: int | None = None, semente: int = 0,
                          ponderado: bool = True, normalizar: bool = False
                          ) -> EstimativaIntermediacao: ...  # O(k (V + E) log V)
```

Todas respeitam vértices e arestas desativados (usam só `Grafo.vizinhos`), o que permite à F-RES recalcular centralidades após uma falha.

Página (`src/transporte/interface/paginas/centralidades.py`, contrato `render(rede)` da P0-UI): `gp_da_rede`, `calcular`, `tabela_ranking`, `intensidades` e `mapa_centralidades`.

Algoritmos previstos (docs/fontes/modelagem.md §3.5):
- Brandes (intermediação) · visão G_P · O(V (V + E) log V) · Ponderado; O(VE) sem pesos

## Como funciona e por quê

**O problema.** Quais paradas são mais importantes para a rede? Duas respostas: a parada com mais ligações (grau) e a parada por onde passam mais caminhos mínimos entre outras paradas (intermediação). A segunda acha os "gargalos": uma parada pode ter poucas linhas e mesmo assim ser o único jeito rápido de ir de uma região a outra.

**A visão: G_P.** Um vértice por parada; aresta de viagem para a parada seguinte de algum padrão, com o tempo mediano, e caminhada de até 300 m nos dois sentidos, com distância / 1,2 m/s (`docs/GUIA.md` §3). G_P, e não G_E, porque a pergunta é sobre a parada física: em G_E a mesma parada vira várias plataformas, uma por padrão, e a centralidade se espalharia entre elas. Sem espera nem horário, G_P é a rede estrutural.

**Graus (RF-MET-01).** `graus` percorre `vizinhos(u)` de cada vértice e soma 1 na saída de u e 1 na entrada do destino. Conta arestas, não vizinhos distintos (M1), com filtro opcional por tipo: na página, o padrão é contar só as de viagem, porque a caminhada liga todas as paradas vizinhas e inflaria o grau de qualquer ponto do centro. `distribuicao_graus` conta quantas paradas têm cada grau.

**Intermediação: Brandes (RF-MET-02).** bc(v) = soma, sobre os pares ordenados (s, t) com s ≠ v ≠ t, da fração dos caminhos mínimos de s a t que passam por v. Enumerar os pares custaria O(V³) só para listar; o Brandes faz, para cada origem s:

1. **Fase 1:** um Dijkstra (o mesmo HeapMin do núcleo) que, além da distância, conta σ[v], o número de caminhos mínimos de s a v, e guarda todos os predecessores de v nesses caminhos. Quando acha um caminho estritamente melhor, σ[v] = σ[u] e os predecessores são trocados; quando acha outro de mesmo custo, σ[v] += σ[u].
2. **Fase 2:** percorre os vértices do mais distante para o mais próximo e acumula a dependência δ[v] = Σ σ[v]/σ[w] · (1 + δ[w]) sobre os sucessores w. δ[v] é quanto v contribui para os caminhos que saem de s; bc[v] += δ[v].

Exemplo (o da fixture dos testes): 0→1→2→4 e 0→3→2, todos com peso 1. De 0 a 2 há dois caminhos mínimos, por 1 e por 3, então cada um ganha 1/2; de 0 a 4, idem, e 2 ganha 1; de 1 a 4 e de 3 a 4, o 2 ganha 1 cada. bc = [0, 1, 3, 1, 0].

**Amostragem (RNF-06; decisão M5).** O exato faz um Dijkstra por parada: no G_P real, cerca de 0,26 s por origem, ou 40 min no total, impraticável na página. `estimar_intermediacao(g, k, semente)` soma as dependências de só k origens sorteadas sem reposição e multiplica por N/k. Como cada origem tem a mesma chance de entrar, a média dessa estimativa sobre todas as amostras possíveis é exatamente o valor exato (não viesada; há teste que confere isso enumerando todas as amostras). Para informar o erro, guarda também a soma dos quadrados das dependências: o erro padrão de cada parada é N · s_v / √k · √((N − k)/N), com s_v o desvio amostral das k dependências e (N − k)/N a correção de população finita, que zera o erro quando k = N. É a amostragem de origens de Brandes e Pich (2007).

**Ranking e mapa (RF-MET-03).** `ranking` ordena por valor decrescente, empate pelo menor id. A página monta G_P uma vez por rede (guardado na sessão), calcula a métrica escolhida e mostra a tabela das k mais centrais (com ± erro padrão quando é amostra), a distribuição de graus e o mapa de calor. O mapa usa o componente da P0-UI; as intensidades são divididas pelo maior valor, porque o Leaflet.heat satura acima de 1 e a intermediação chega a milhões.

**Complexidade e por quê.** Graus: O(V + E), cada aresta vista uma vez. Distribuição: O(V + D log D), D graus distintos. Brandes exato ponderado: V Dijkstras, O(V (V + E) log V); sem pesos, BFS, O(V (V + E)). A fase 2 custa O(V + E) por origem (cada predecessor guardado é uma aresta). Espaço O(V + E): a adjacência simplificada é montada uma vez, e as listas de uma origem são descartadas antes da próxima. Amostrado com k origens: O(k (V + E) log V), k/N do exato. Ranking: O(V log V) pela ordenação.

**Decisões e alternativas descartadas** (M1 a M4 aceitas em 05/11; M5 em 16/11):

- **M1, grau conta arestas, com filtro por tipo:** é a definição de grau em multigrafo dirigido (a do NetworkX, o que permite comparar). Vizinhos distintos foi descartado.
- **M2, peso 0 é recusado na intermediação ponderada:** com peso 0 dois vértices empatam na distância e a contagem de caminhos sai errada. O Henrique pôs o piso de 1 s nas arestas do G_P (`Parametros.peso_minimo_s`). Descartados: desempatar pelo número de arestas e somar ε dentro do Brandes.
- **M3, caminhos como sequência de vértices:** aresta de viagem e de caminhada entre o mesmo par contam como uma ligação, com o menor peso, e laços são ignorados. Contar as duas daria peso extra ao par.
- **M4, normalização opcional, ligada na página:** o bruto ("quantos caminhos mínimos passam aqui") é mais fácil de explicar; o normalizado, dividido por (N − 1)(N − 2), fica em [0, 1] e compara redes de tamanhos diferentes (antes e depois de uma falha).
- **M5, amostragem por origens com erro padrão por parada:** descartados amostrar pares (s, t), que exigiria um Dijkstra por par para a mesma precisão, e o exato na página, que leva dezenas de minutos. O mesmo formato de estimativa (valor, erro padrão, amostra, população) da eficiência da F-EFI.

**Limitações.** G_P não tem espera nem horário: a centralidade é da rede estrutural, não do serviço numa faixa. A caminhada em linha reta de até 300 m liga paradas que podem estar separadas por uma avenida. A amostra muda o valor de cada parada (por isso a semente fixa e o erro padrão), e a estimativa é mais precisa para as paradas mais centrais do que para as de valor pequeno.

## Perguntas de verificação

1. **Por que a intermediação não é simplesmente contar, para cada par, se o caminho passa por v?** Porque são V² pares e pode haver vários caminhos mínimos por par; o Brandes acumula as dependências por origem, com um Dijkstra e uma passada de volta, em O(V (V + E) log V).
2. **O que é σ[v] e por que precisamos dele?** O número de caminhos mínimos de s a v. Ele diz que fração dos caminhos até w passa por cada predecessor v: σ[v]/σ[w].
3. **Por que o Brandes ponderado recusa peso 0?** Com peso 0, dois vértices ficam à mesma distância e um pode ser fechado antes de receber todos os caminhos do outro; a contagem σ sai errada. O G_P tem piso de 1 s.
4. **Por que a estimativa com k origens multiplica por N/k, e o que é o "±"?** A soma de k origens é, em média, k/N da soma de todas; multiplicar por N/k corrige. O "±" é o erro padrão: quanto a estimativa varia de uma amostra para outra.
5. **Por que G_P e não G_E?** A pergunta é sobre a parada física; em G_E cada parada vira várias plataformas, e a centralidade ficaria dividida entre elas.

## Critérios de aceite
- [x] RF-MET-01: Calcular o grau de entrada e de saída de cada parada e a distribuição de graus (`graus`, `distribuicao_graus`; comparação com o NetworkX)
- [x] RF-MET-02: Calcular a intermediação (Brandes) de cada parada (`intermediacao`; comparação com o NetworkX com e sem pesos)
- [x] RF-MET-03: Mostrar o ranking das paradas mais centrais e um mapa de calor (página Centralidades; `tests/interface/test_pagina_centralidades.py`; conferida no feed real em 16/11)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante (algoritmos no #37, aprovado; página e amostragem no PR da `feat/F-MET-pagina`)
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde (16/11; ver Pendências sobre um teste da `main` que depende do feed baixado)
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (224 de centralidade e 10 da página em 16/11)
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
- [x] Página ou bloco na interface funcionando com o dataset real
- [ ] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/` (fonte `atividade-intermediacao.puml` pronta; falta o PNG)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação (texto, resultado e limitação prontos; falta a captura da página para a figura)
- [x] Roteiro do vídeo escrito no arquivo da feature
- [ ] Arquivo da feature atualizado: retomada ("concluída"), status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | concluída em 05/11 |
| 2 | Algoritmo com testes de corretude | concluída em 05/11 |
| 3 | Integração com a visão do grafo e com os dados reais | concluída em 16/11 (G_P do feed real) |
| 4 | Página na interface | concluída em 16/11 |
| 5 | Tempo medido na rede real e complexidade justificada | concluída em 16/11 |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | concluída em 16/11, menos o PNG do diagrama e a captura da página |

## Resultados para o relatório
_Todo número vem com o comando que o gerou._

**Centralidades no G_P real, 16/11/2026.** Comando: `python scripts/baixar_gtfs.py` (com o limite do curl aumentado para 900 s; ver Pendências) e depois `python benchmarks/medir_centralidade.py dados/brutos/bhtrans.zip --exato`; JSON em `benchmarks/resultados/centralidade-2026-11-16.json`. Feed: GTFS convencional da PBH baixado em 16/11/2026 22:55 UTC, 49.869.783 bytes, SHA-256 `241f0bb2dbb80ca59de9a9e59eb1135f359537b5dee6199ce6c47323140c01c0` (diferente do de 11/11: a PBH atualizou o arquivo). Serviço de 11/11/2026: 9.660 paradas e 698 padrões. Máquina: notebook Samsung 750XGL, Intel Core 5 120U (10 núcleos, 12 threads), 15,7 GB, Windows 11, Python 3.12.14. Tempos com `medir`, n = 3, sem a leitura do GTFS nem a construção do G_P. Os tempos variam bastante nessa máquina (ver o desvio).

| Medida | Resultado | Tempo |
|---|---|---|
| G_P | V = 9.660, E = 122.799 | |
| Grau de saída só com viagem | máximo 20 (parada `14784108`, Av. Afonso Vaz de Melo 250); 7.271 paradas (75 %) com grau 1, 1.642 com grau 2 e 201 com grau 0 | `graus`: 149,3 ms ± 16,7 ms (todas as arestas: 97,9 ms ± 10,3 ms) |
| Intermediação exata (referência) | top 5: Av. Presidente Antônio Carlos (nºs 8271, 3835, 6519, 4303 e 7645); 6º a 10º: Anel Rodoviário. A primeira tem 11.309.544 (0,121 normalizada) | uma execução: 2.632,4 s (44 min), parte dela com outra suíte de testes rodando na máquina |

Intermediação amostrada (semente 2026) contra a exata. Erro relativo nas 100 paradas mais centrais da exata; cobertura = fração em que o exato cai em estimativa ± 2 erros padrão.

| k origens | Tempo (n = 3) | Top 10 em comum | Top 50 em comum | Erro relativo mediano (máximo), top 100 | Cobertura no top 100 | Cobertura em todas com bc > 0 |
|---|---|---|---|---|---|---|
| 25 | 5,19 s ± 0,48 s | 5 | 35 | 18,6 % (204 %) | 100 % | 45 % |
| 50 | 15,78 s ± 7,87 s | 9 | 37 | 12,2 % (52 %) | 97 % | 46 % |
| 100 | 23,02 s ± 2,13 s | 8 | 40 | 8,5 % (64 %) | 100 % | 51 % |
| 200 | 45,65 s ± 1,96 s | 8 | 43 | 6,1 % (35 %) | 100 % | 56 % |

Leitura: com 50 origens (o padrão da página, cerca de 0,5 % do custo do exato), 9 das 10 paradas mais centrais coincidem com as do exato, e o erro informado é confiável no ranking (97 % de cobertura no top 100). Nas paradas de valor pequeno, quase todas as k origens contribuem com 0: a variância observada fica baixa (erro padrão 0 em 16 % das paradas com bc > 0, com k = 50) e o "±" subestima o erro. Por isso a página mostra o erro só no ranking. As primeiras posições mudam de ordem entre amostras porque os valores são muito próximos (11,31, 11,30 e 11,29 milhões).

**Página no feed real, 16/11/2026** (pelo `AppTest`, sem exceção): abrir monta o G_P em 3,1 s; a intermediação com 50 origens respondeu em 14,1 s; com o grau de saída, o script da página leva 1,8 s (cálculo 0,17 s, mapa 0,31 s). O ranking com 50 origens começou por Av. Presidente Antônio Carlos 8271, a mesma primeira do exato.

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

Rascunho de 16/11 (Thiago revisa e grava):

1. **Problema (20 s):** quais paradas de BH mais importam para a rede? Não só as com mais linhas: as que ficam no meio dos caminhos mais rápidos entre bairros, os gargalos.
2. **Na ferramenta (45 s):** abrir Centralidades; grau de saída só com ônibus, a distribuição (75 % das paradas com grau 1) e a campeã com 20 ligações; trocar para intermediação com 50 origens, mostrar o ranking com o "±" e o mapa de calor concentrado na Av. Antônio Carlos e no Anel Rodoviário.
3. **Como funciona (45 s):** Brandes num exemplo de 5 vértices: um Dijkstra que conta os caminhos mínimos (σ) e a passada de volta acumulando dependências; O(V (V + E) log V). Por que amostrar: o exato levou 44 min; com k origens, N/k vezes a soma, não viesada, com erro padrão.
4. **Resultado e limitação (30 s):** com 50 origens (14 s na página), 9 das 10 primeiras iguais às do exato, erro mediano de 12 % no top 100; limitação: G_P não tem espera nem horário, e o "±" só é confiável nas paradas centrais.

## Pendências
- ~~**Peso 0 no G_P (Henrique, P0-MODELO)**~~ **resolvido em 05/11:** piso de 1 s nas arestas de G_P e G_E (`Parametros.peso_minimo_s`, GUIA §8).
- ~~**Página e mapa de calor (RF-MET-03)**~~ **feito em 16/11** (página Centralidades).
- **PNG do diagrama:** gerar `docs/diagramas/atividade-intermediacao.png` com o `plantuml-1.2026.9.jar` (fora do Git, `*.jar` no `.gitignore`).
- **Figura do relatório:** captura da página com o ranking e o mapa de calor no feed real, em `relatorio/figuras/`, no lugar do `\pendente` de `F-MET.tex`.
- **Teste da `main` que depende do feed (avisar Arthur e Miguel):** `tests/interface/test_integracao_dados.py::test_app_test_carrega_o_feed_e_renderiza_o_widget_do_mapa` clica no primeiro conjunto de dados da lista; com `dados/brutos/bhtrans.zip` baixado, ele vem antes de `dados/rede-teste`, o teste carrega o feed real (cerca de 54 s, acima do timeout de 30 s, e outro dia de serviço) e falha. Não é desta feature; sugestão: fixar `listar_fontes` na rede de teste, como os outros testes do arquivo.
- **Download do feed (Miguel):** `scripts/baixar_gtfs.py` usa `--max-time 120` no curl; em 16/11 foi preciso 900 s, como o Rafael já registrou em 11/11.
- **F-EFI (Arthur):** a `estimar_eficiencia_global` do #52 usa o mesmo formato de estimativa (valor, erro padrão, amostra, população); manter os dois alinhados.

### ~~Decisões a tomar~~ Decididas em 05/11/2026: M1 a M4 aceitas pelo Thiago pela recomendação

- **M1. O que o grau conta.** (a) arestas utilizáveis, com paralelas contando uma vez cada e laço contando 1 na entrada e 1 na saída, mais um filtro opcional `tipos`; (b) vizinhos distintos. **Recomendo (a):** é a definição usual de grau em multigrafo dirigido (a mesma do NetworkX, o que permite comparar). O filtro `tipos={"viagem"}` resolve o caso em que a caminhada infla o grau de paradas vizinhas.
- **M2. Peso 0 na intermediação ponderada.** O Brandes conta caminhos mínimos processando os vértices em ordem de distância; com aresta de peso 0, dois vértices empatam na distância e a ordem pode sair errada (e um ciclo de peso 0 dá infinitos caminhos mínimos). Opções: (a) recusar peso 0 com ValueError e pedir ao construtor do G_P um piso de 1 s; (b) desempatar pelo número de arestas (distância lexicográfica), o que muda a definição e deixa de bater com o NetworkX quando há empates de tempo; (c) somar um ε aos pesos 0 dentro do Brandes. **Recomendo (a):** mantém o Brandes clássico e comparável ao NetworkX, e 0 s entre duas paradas distintas é artefato de arredondamento, não tempo real.
- **M3. Caminhos como sequência de vértices.** Na intermediação, arestas paralelas viram uma só, com o menor peso, e laços são ignorados. **Recomendo aceitar:** no G_P, uma aresta de viagem e uma de caminhada entre o mesmo par são a mesma ligação entre paradas; contar as duas como caminhos distintos daria peso extra a esse par. É também o que o NetworkX faz em multigrafos.
- **M4. Normalização opcional.** `normalizar=True` divide por (n - 1)(n - 2), n = paradas ativas, o máximo num grafo dirigido. **Recomendo deixar desligada por padrão e ligar na interface:** o valor bruto ("em quantos caminhos mínimos a parada aparece") é mais fácil de explicar, e o normalizado permite comparar a rede antes e depois de uma falha (F-RES), quando n muda.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Thiago.
### Sessão 05/11/2026: branch `feat/F-MET-centralidades`; contrato de `centralidade.py` publicado com estado: planejado; decisões M1 a M4 propostas.
### Decisão 05/11/2026: M1 a M4 aceitas pela recomendação.
### Sessão 05/11/2026: etapa 2, graus, distribuição, Brandes e ranking implementados com 190 testes verdes; RF-MET-01 e RF-MET-02 atendidos.
### PR 05/11/2026: #37 aberto para revisão do Henrique (Refs #10).
### Sessão 16/11/2026: branch `feat/F-MET-pagina`. `estimar_intermediacao` (amostragem de origens com erro padrão, RNF-06, decisão M5) com 34 testes novos (224 no arquivo); página Centralidades (RF-MET-03) com 10 testes; medição no feed real com o Brandes exato como referência (44 min) e o erro das amostras; Como funciona, perguntas, GUIA, diagrama de atividade, seção do relatório e roteiro. F-MET-2 e F-MET-OPC cortadas pelo congelamento.
