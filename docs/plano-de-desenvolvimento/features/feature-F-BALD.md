# F-BALD · Menos baldeações

**Período:** 1 · Essenciais (04/11 a 11/11) · **Classe:** prioritária
**Dono:** Rafael (@Rafael-Fonseca1510) · **Issue:** #9 · **Visões do grafo:** G_L
**Depende de:** P0-DADOS (na `main`, #42), P0-GRAFO (na `main`, #35), P0-UI (página: PR #45, aberto) · **Bloqueia:** F-BALD-2
**Prazo:** 11/11 (checkpoint 07/11)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-GRF-06, RF-BAL-01, RF-BAL-02). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 11/11, Rafael, branches `feat/F-BALD-linhas` (núcleo, testes, medição e documentação) e `feat/F-BALD-pagina` (página, sobre a anterior e com o P0-UI #45 por merge).
- **Onde parou:** etapas 1 a 3, 5 e 6 concluídas; etapa 4 pronta na `feat/F-BALD-pagina`, que espera o #45. `construir_gl` e `menos_baldeacoes` passam em 52 testes (566 na suíte) e batem com o NetworkX em 200 de 200 consultas no feed real; 36,7 ms por consulta (ver Resultados). Decisões B1 a B7 propostas, e falta o Rafael aceitar. Seção do relatório compilando (`relatorio/secoes/F-BALD.tex`).
- **Próximo passo:** revisar as decisões B1 a B7 e o "Como funciona". Depois, abrir o PR da `feat/F-BALD-linhas` para a `main` com `Closes #9`. Quando o #45 (P0-UI) entrar, atualizar a `feat/F-BALD-pagina` com a `main` e abrir o PR da página. Avisar o Arthur e o Henrique das pendências (controle de camadas do mapa e texto da G_L na modelagem).
- **Arquivos tocados:** `src/transporte/modelo/visoes.py` (`VisaoGL`, `BALDEACAO`), `src/transporte/modelo/linhas.py`, `src/transporte/algoritmos/baldeacoes.py`, `src/transporte/interface/paginas/baldeacoes.py` (só na branch da página), `tests/modelo/test_linhas.py`, `tests/algoritmos/test_baldeacoes.py`, `tests/integracao/test_integracao_baldeacoes_rede_teste.py`, `tests/interface/test_pagina_baldeacoes.py` (só na branch da página), `benchmarks/medir_baldeacoes.py`, `docs/diagramas/atividade-menos-baldeacoes.{puml,png}`, `relatorio/secoes/F-BALD.tex`, `relatorio/figuras/baldeacoes-mapa.jpg`, `docs/GUIA.md` (§5.3, §8 e §10), este arquivo.
- **Como testar:** `pytest tests/modelo/test_linhas.py tests/algoritmos/test_baldeacoes.py tests/integracao/test_integracao_baldeacoes_rede_teste.py` (52 testes); `ruff check`. Página, na `feat/F-BALD-pagina`: `pytest tests/interface/test_pagina_baldeacoes.py` (6 testes). Medição: `PYTHONPATH=src python benchmarks/medir_baldeacoes.py dados/brutos/bhtrans.zip` (cerca de 8 min, quase tudo na conferência com o NetworkX).
- **Bloqueios:** a página depende do #45 (P0-UI). O `streamlit run` do #45 ainda não recebe o `ler()`, então a página só foi exercitada no feed real pelo `AppTest` (ver Pendências).

## Objetivo
Menos baldeações. Fecha:

- **RF-GRF-06** (E): Construir a visão G_L (linhas)
- **RF-BAL-01** (E): Calcular o trajeto com o menor número de baldeações entre duas paradas
- **RF-BAL-02** (E): Mostrar a sequência de linhas e as paradas de troca no mapa

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 11/11: `menos_baldeacoes` (BFS por camadas sobre a G_L, com a posição de embarque como rótulo), `estado: implementado` |
| Modelo e dados | concluído | 11/11: `construir_gl` e `VisaoGL`; integração com `dados/rede-teste` pelo `ler()` (5 testes) e com o feed real (Resultados) |
| Interface | em andamento | 11/11: página `Baldeações` na `feat/F-BALD-pagina` (6 testes; roda no feed real pelo `AppTest`, consulta em 22 ms); espera o #45 entrar na `main` |
| Testes | concluído | 11/11: 52 testes. Gabarito à mão (linha direta, troca na mesma parada e a pé, a pé nas pontas, ordem dentro do padrão, padrão que melhora numa camada posterior, laço, circular, desempates), bordas (origem = destino, destino perto, inalcançável, parada sem padrão, parada inexistente, falhas e reativação) e NetworkX num grafo de estados em 12 redes aleatórias (480 consultas). Fora da suíte, 12.000 consultas em 400 redes com 0 divergências |
| Desempenho (tempo medido) | concluído | 11/11: 36,7 ms por consulta (máximo 172,9 ms) e G_L do pico em 3,1 s no feed real; ver Resultados |
| Guia (explicação e quiz) | em andamento | 11/11: Como funciona e 5 perguntas, copiados para o `docs/GUIA.md` §5.3 e §10; falta a revisão do Rafael |
| Relatório | concluído | 11/11: `relatorio/secoes/F-BALD.tex` com figura (mapa real), resultado, complexidade e limitação; compilado com MiKTeX sem erro (cerca de 0,7 página) |
| Vídeo | em andamento | 11/11: roteiro abaixo; gravação no P3 |

## Especificação

`src/transporte/modelo/visoes.py` (acréscimo da F-BALD):

| Símbolo | Conteúdo |
|---|---|
| `BALDEACAO` | Tipo das arestas de G_L (`"baldeacao"`) |
| `Transferencia` | `(i, x, j, y)`: desce de P na posição i (parada x), embarca em Q na posição j (parada y) |
| `VisaoGL(Visao)` | `vertice_do_padrao`, `padrao_do_vertice`, `paradas_do_padrao`, `transferencias[aresta]` (trocas não dominadas, i e j decrescentes), `proximas[parada]` (paradas a até o raio, a própria primeiro), `embarques[parada]` (vértice, posição), `faixa` |

`src/transporte/modelo/linhas.py`:

| Símbolo | Conteúdo |
|---|---|
| `construir_gl(rede, params=None, faixa=None) -> VisaoGL` | Um vértice por padrão com 2 ou mais paradas; aresta P -> Q (peso 1) quando dá para descer de P (posição ≥ 1) e embarcar em Q (posição ≤ penúltima) na mesma parada ou a até o raio; laço P -> P permitido. Com `faixa`, só os padrões com partida nela (D10). Tempo O(V + K log K + L + C) esperado; espaço O(V + K + L + E + T) |

`src/transporte/algoritmos/baldeacoes.py`:

| Símbolo | Conteúdo |
|---|---|
| `TrechoBaldeacao(tipo, paradas, padrao)` | `tipo` é `A_PE` ou `ONIBUS` (constantes de `algoritmos.trajeto`); `padrao` é None a pé |
| `TrajetoBaldeacoes(origem, destino, baldeacoes, trechos)` | `padroes()` dá a sequência de linhas; `trocas()` dá (onde desce, onde embarca) por baldeação |
| `menos_baldeacoes(gl, origem, destino) -> TrajetoBaldeacoes \| None` | None se inalcançável; KeyError para parada inexistente. Tempo O(r (V + E + T) + s); espaço O(r V) |

`src/transporte/interface/paginas/baldeacoes.py` (branch da página): `render(rede)`, `gl_da_faixa(rede, faixa, cache)`, `tabela_trechos`, `resumo_linhas`, `mapa_trajeto`.

Algoritmos previstos (docs/fontes/modelagem.md §3.5):
- BFS · visão G_L · O(V + E) · Mínimo de baldeações. Implementado como BFS por camadas com a posição de embarque no rótulo (decisão B1): O(r (V + E + T)).

## Como funciona e por quê

**O problema.** Dadas duas paradas, achar o trajeto que usa o menor número de ônibus (baldeações = ônibus − 1) e mostrar a sequência de linhas e onde trocar. Não é o mais rápido: quem odeia baldear aceita andar mais de ônibus. A comparação com o mais rápido é a F-BALD-2.

**A visão: G_L.** O número de baldeações não depende de quantas paradas o ônibus percorre, só de quantas vezes se troca de linha. Por isso a visão tem **um vértice por padrão** de linha (linha + sequência exata de paradas, D1) e uma aresta P → Q quando dá para descer de P e embarcar em Q, na mesma parada ou em paradas a até 300 m (o raio de caminhada). Com 698 padrões no feed real contra 46.100 vértices do G_E, cada camada da busca é um ônibus a mais.

A aresta é **dirigida** e cada uma guarda **onde** a troca acontece. Um padrão tem sentido: não se desce na primeira parada nem se embarca na última, e quem está em P só pode descer depois de onde embarcou. Exemplo (teste `test_ordem_dentro_do_padrao_importa`): P1 = S → B → A → E, P2 = B → D, P3 = E → B. Existe a aresta P1 → P2 (desce em B, posição 1). Um BFS comum diria que de A a D basta 1 baldeação (P1 e depois P2). Mas quem embarca em P1 em A (posição 2) já passou de B. O certo é P1 até E, P3 de volta a B e P2 até D: 2 baldeações. No feed real, o BFS comum erraria para menos em 14 de 200 pares.

**Trocas não dominadas.** Uma aresta P → Q pode ter muitas trocas possíveis. A troca (i, j), descer na posição i de P e embarcar na posição j de Q, domina outra se desce mais tarde (serve a mais gente que já está em P) e embarca mais cedo (deixa mais trocas disponíveis em Q). A aresta guarda só a fronteira, com i e j decrescentes. Quem embarcou em P na posição b usa a última troca com i > b, que é a de menor j. No feed real ficam 215.050 trocas em 85.606 arestas (cerca de 2,5 por aresta).

**Passo a passo** (`menos_baldeacoes(gl, origem, destino)`; diagrama de atividade em `docs/diagramas/atividade-menos-baldeacoes.png`):

1. Parada inexistente dá KeyError; origem = destino devolve 0 baldeações; destino a até 300 m da origem devolve o trajeto a pé.
2. **Camada 1:** cada padrão ativo que embarca numa parada a até 300 m da origem recebe como rótulo a posição de embarque mais cedo.
3. Se algum padrão que melhorou nesta camada desce a até 300 m do destino depois do embarque, essa é a resposta. Ônibus = número da camada, baldeações = camada − 1. Entre as chegadas da camada, fica a de menor caminhada no fim e, depois, a de última perna mais curta.
4. **Próxima camada:** para cada padrão que melhorou, olha as arestas ativas dele e, em cada uma, a troca que desce depois do embarque e embarca mais cedo em Q. Q melhora se essa posição é mais cedo que a de qualquer camada anterior. Um padrão pode, então, **voltar** numa camada posterior, embarcado numa posição mais cedo, o que abre trocas que antes não serviam (teste `test_padrao_alcancado_de_novo_em_posicao_mais_cedo`).
5. Sem nenhum padrão melhorado, não há trajeto: devolve None.
6. Reconstrução: cada rótulo guarda o padrão anterior e onde desceu dele. O primeiro embarque troca para o ponto mais perto da origem que ainda serve à primeira troca. Saem os trechos de ônibus e os trechos a pé (entre a descida e o próximo embarque, quando as paradas diferem).

Sem a restrição de ordem dentro do padrão, os passos 2 a 5 são exatamente o BFS do núcleo sobre G_L.

**Por que é exato.** Depois da camada k, o rótulo de cada padrão é a posição mais cedo em que dá para estar nele usando até k ônibus. Na camada k + 1, um padrão só pode melhorar a partir de um padrão que melhorou na camada k: se o rótulo de P não mudou, as trocas de P já foram usadas na camada anterior. Então a primeira camada que chega ao destino dá o mínimo de ônibus. Os testes conferem isso contra o NetworkX num grafo de estados escrito à parte (chegou à parada, pronto para embarcar, embarcou, a bordo), com peso 1 no embarque: 0 divergências em 480 consultas da suíte, 12.000 fora dela e 200 no feed real.

**Complexidade.** V e E de G_L, T trocas guardadas, r camadas (baldeações + 1, ou + 2 sem trajeto), s paradas a até 300 m da origem e do destino. Cada camada percorre só os padrões que melhoraram na anterior e, de cada um, as arestas e as trocas, parando na primeira troca que já não serve: O(V + E + T) por camada, O(r (V + E + T) + s) no total. Espaço O(r V) para os rótulos de todas as camadas, que a reconstrução usa. A construção da G_L custa O(V + K log K + L + C) esperado: a grade espacial do P0-MODELO para os K pares a até 300 m, e uma passada sobre as C trocas candidatas, da última posição de descida para a primeira, que já monta a fronteira sem ordenar. No feed real (ver Resultados): 36,7 ms por consulta e 3,1 s para montar a G_L do pico da manhã.

**Decisões e alternativas descartadas** (B1 a B7, propostas em 11/11; o Rafael confirma):

- **B1. BFS por camadas com a posição de embarque, sobre a G_L dirigida com as trocas na aresta.** Alternativas: (a) BFS comum na G_L, descartado porque dá só um limite inferior e trajetos impossíveis (14 de 200 pares no feed real); (b) BFS 0-1 no G_E, com peso 1 no embarque. A (b) é exata, mas não constrói a G_L que o RF-GRF-06 pede, roda sobre um grafo com 46.100 vértices em vez de 501 e permite encadear caminhadas.
- **B2. Laço P → P.** Descer, andar até 300 m e pegar o mesmo padrão mais atrás (ou esperar o próximo ônibus de um padrão circular) é outro embarque, então conta como baldeação. Sem o laço, o NetworkX achou trajetos com um ônibus a menos que os nossos.
- **B3. Caminhada de até 300 m, uma por vez** (até o primeiro embarque, em cada troca, do último desembarque ao destino), sempre entre paradas. Por quê: é a ligação que a modelagem define para G_L ("paradas a distância de caminhada"). Encadear caminhadas tornaria a distância a pé ilimitada. Destino a até 300 m da origem é a pé, com 0 baldeações.
- **B4. G_L do dia por padrão, ou de uma faixa** (`faixa=`), com a regra D10 do G_E (padrão com partida na faixa). A faixa deixa a F-BALD-2 comparar com o G_E da mesma faixa sem usar uma linha que não circula nela.
- **B5. Desempate:** menos caminhada no fim, depois a última perna mais curta e, no primeiro ônibus, o ponto de embarque mais perto da origem. Não minimiza o tempo (é a F-BALD-2) nem o total de paradas.
- **B6. Onde mora o código:** `VisaoGL` em `visoes.py`, como as outras visões. `construir_gl` fica num módulo próprio (`modelo/linhas.py`), para não disputar o `construtores.py` com o P0-MODELO, e reaproveita a grade espacial e a regra D10 de lá. O algoritmo fica em `algoritmos/baldeacoes.py`, no padrão da R1 da F-ROTA. Os trechos usam as constantes `A_PE` e `ONIBUS` da F-ROTA, para as páginas desenharem igual.
- **B7. Página numa branch própria** (`feat/F-BALD-pagina`, com o #45 por merge), como a F-ROTA fez. Assim o PR do núcleo não espera o P0-UI.

**Limitações.**

- O critério é só o número de baldeações. O trajeto pode ser bem mais lento que o mais rápido e passar por muitas paradas.
- A G_L ignora horários, exceto no filtro por faixa: não vê espera, frequência nem se o ônibus da troca já passou.
- Caminhada em linha reta, uma por vez, até 300 m e só entre paradas.
- Paradas desativadas (F-RES) não são vértices da G_L. Uma falha de parada precisa reconstruir a G_L sem ela. Falha de linha é desativar o vértice do padrão.
- Montar a G_L custa de 3 a 4,5 s no feed real; a página monta uma vez por faixa e guarda na sessão.

## Perguntas de verificação

1. **Por que a G_L tem um vértice por padrão, e não por parada?** Porque baldeação é troca de linha: com um vértice por padrão, cada camada da busca em largura é um ônibus a mais, e o número de paradas percorridas não importa.
2. **Por que um BFS comum sobre a G_L não basta?** Porque os padrões têm sentido: quem embarca em P numa posição só pode descer depois dela. O BFS comum usaria trocas que ficaram para trás e daria um limite inferior (no feed real, menos baldeações que o possível em 14 de 200 pares).
3. **O que é uma troca não dominada?** Numa aresta P → Q, uma troca que nenhuma outra supera ao mesmo tempo descendo mais tarde em P e embarcando mais cedo em Q. Só essas ficam na aresta, porque servem a todo passageiro que as outras serviriam.
4. **Por que um padrão pode voltar numa camada posterior?** Porque pode ser alcançado depois numa posição mais cedo. Embarcar antes abre trocas que, da posição anterior, não serviam.
5. **O trajeto devolvido é o mais rápido entre os de menos baldeações?** Não. O critério é só o número de baldeações, com desempate pela caminhada e pelo tamanho da última perna. O tempo a mais em relação ao mais rápido é a F-BALD-2.

## Critérios de aceite
- [x] RF-GRF-06: Construir a visão G_L (linhas) (11/11: `construir_gl`; no feed real, V = 698 e E = 149.551 no dia, V = 501 e E = 85.606 no pico da manhã)
- [x] RF-BAL-01: Calcular o trajeto com o menor número de baldeações entre duas paradas (11/11: 200 de 200 consultas no feed real com 0 divergências contra o NetworkX)
- [ ] RF-BAL-02: Mostrar a sequência de linhas e as paradas de troca no mapa (11/11: página pronta na `feat/F-BALD-pagina`, conferida no feed real pelo `AppTest` e na figura do relatório; marcar quando estiver na `main`, depois do #45)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde (11/11: 566 na `feat/F-BALD-linhas`, 584 na `feat/F-BALD-pagina`)
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (11/11: 52 testes; NetworkX num grafo de estados, porque ele não tem um equivalente direto do mínimo de baldeações)
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature (11/11, em Como funciona)
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina (11/11)
- [ ] Página ou bloco na interface funcionando com o dataset real (11/11: funciona pelo `AppTest` no feed real; falta entrar na `main` com o #45, e o `streamlit run` do #45 passar o `ler()`)
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/` (11/11: `atividade-menos-baldeacoes`)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md` (11/11; falta a revisão do Rafael)
- [ ] O revisor do PR consegue explicar o que o código faz
- [x] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação (11/11)
- [x] Roteiro do vídeo escrito no arquivo da feature (11/11)
- [ ] Arquivo da feature atualizado: retomada ("concluída"), status, pendências e timeline (fecha com o merge)

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | concluída em 11/11 (publicado já implementado, como na F-ROTA: ninguém consome a G_L antes da F-BALD-2, que é do mesmo dono) |
| 2 | Algoritmo com testes de corretude | concluída em 11/11 |
| 3 | Integração com a visão do grafo e com os dados reais | concluída em 11/11 (rede de teste pelo `ler()` e feed real) |
| 4 | Página na interface | pronta em 11/11 na `feat/F-BALD-pagina`; espera o #45 (P0-UI) |
| 5 | Tempo medido na rede real e complexidade justificada | concluída em 11/11 |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | concluída em 11/11 (rascunho; Rafael revisa) |

## Resultados para o relatório
_Todo número vem com o comando que o gerou._

**Construção e consulta, 11/11/2026.** Comando: `PYTHONPATH=src python benchmarks/medir_baldeacoes.py dados/brutos/bhtrans.zip`, na `feat/F-BALD-linhas` (`150fc07`). Feed: GTFS convencional da PBH baixado em 11/11/2026 por `scripts/baixar_gtfs.py` (com o limite do curl aumentado, ver Pendências), SHA-256 `459f3a5892e57d10b11f9a74c543ac16c22661867c7d2296352ec17338935707`, 49.867.199 bytes. Serviço de 04/11/2026: 9.659 paradas, 698 padrões e 24.503 viagens, os mesmos números do instantâneo de 05/11 usado pela F-ROTA, que tinha outro SHA-256. Máquina: Intel Core i5-1235U, 15,7 GB, Windows 11, Python 3.12.10.

| Medida | Valor |
|---|---|
| G_L do dia | V = 698, E = 149.551, 372.165 trocas guardadas; `construir_gl` 4,516 s ± 0,140 s (n = 5) |
| G_L do pico da manhã | V = 501, E = 85.606, 215.050 trocas guardadas; `construir_gl` 3,092 s ± 0,020 s (n = 5) |
| Consultas | 200 pares de paradas sorteados (semente 2026, os mesmos pares da F-ROTA), na G_L do pico da manhã |
| 200 consultas seguidas, `medir`, n = 5 | 7,335 s ± 0,171 s, ou 36,7 ms por consulta |
| Cada consulta isolada, `medir`, n = 3 | mediana 13,9 ms, p95 151,7 ms, máximo 172,9 ms |
| Com trajeto | 200 de 200; nenhum só a pé; 180 com alguma troca a pé |
| Baldeações | 0: 16; 1: 101; 2: 78; 3: 5; 4 ou mais: 0 |
| Conferência com `nx.dijkstra_path_length` num grafo de estados (peso 1 no embarque) | 0 divergências em 200 |
| BFS comum sobre a G_L, ignorando a ordem dentro do padrão | menos baldeações que o possível em 14 de 200 |

Outras duas execuções do mesmo comando no mesmo dia, uma antes da otimização da construção (`8f7b078`) e outra com a máquina ocupada, deram 38,8 e 39,0 ms por consulta, com as mesmas contagens. Antes da otimização, `construir_gl` do dia levava 7,698 s ± 0,105 s.

**Figura.** `relatorio/figuras/baldeacoes-mapa.jpg`: mapa da página (`mapa_trajeto`, na `feat/F-BALD-pagina` em `9ac437b`) para o primeiro dos 200 pares, de 14786076 a 14789446, na G_L do pico da manhã: 2 baldeações, linhas 342 → 6350 → 643, trocas a pé nas estações Barreiro (15140079 → 15140126) e Pampulha (15252281 → 15258309). Captura do HTML do folium com o Chrome sem janela (`--headless=new --window-size=900,1000`), com o controle de camadas recolhido, recortada na região do trajeto.

**Página no feed real (AppTest), 11/11.** Mesmo par: dia inteiro e pico da manhã sem exceção; consulta em 22 ms na G_L do pico; métricas "Baldeações 2, Ônibus 3, Trechos a pé 4".

Limitação observada: a G_L não vê horários. As 101 consultas com 1 baldeação podem ter, no G_E, um trajeto mais rápido com mais trocas. Essa comparação é a F-BALD-2.

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

Rascunho de 11/11 (Rafael revisa):

1. **Problema (20 s):** muita gente prefere um trajeto com menos trocas de ônibus, mesmo que demore mais. Entre duas paradas de BH, qual o mínimo de baldeações, e onde trocar?
2. **Na ferramenta (45 s):** página Baldeações, origem no Barreiro e destino na Pampulha, pico da manhã. Mostrar as métricas (2 baldeações, 3 ônibus), a sequência 342 → 6350 → 643, a tabela de trechos e, no mapa, uma cor por linha, a caminhada tracejada e os círculos laranja nas trocas. Trocar para "dia inteiro" e mostrar que o trajeto pode mudar.
3. **Como funciona (45 s):** a G_L, um vértice por padrão; por que o BFS comum erra (o exemplo S-B-A-E: a troca em B ficou para trás); as camadas com a posição de embarque; as trocas não dominadas na aresta. Complexidade O(r (V + E + T)).
4. **Resultado e limitação (30 s):** 36,7 ms por consulta na rede inteira, conferido com o NetworkX em 200 pares; o BFS comum erraria em 14. Limitação: conta trocas, não tempo; quanto custa a mais é a F-BALD-2.

## Pendências
- **Rafael (dono):** revisar e aceitar (ou mudar) as decisões B1 a B7 e o rascunho do Como funciona; só então as linhas do `docs/GUIA.md` §8 perdem o "(rascunho para Rafael revisar)".
- **P0-UI (Arthur), mapa:** `criar_mapa` já adiciona o `folium.LayerControl`. Camadas que uma página acrescenta depois são citadas pelo controle antes de existirem no JavaScript, e o Leaflet para com "Cannot read properties of undefined (reading 'setZIndex')", sem desenhar o trajeto. A página Baldeações contorna isso movendo o controle para o fim (`_controle_de_camadas_por_ultimo`, com teste). A página Trajetos da `feat/F-ROTA-pagina` (`f2d409f`) tem o mesmo problema, conferido em 11/11 renderizando o `mapa_trajeto` dela: o controle sai antes das camadas no HTML. Avisar o Henrique. Sugestão ao Arthur: `criar_mapa(..., controle_de_camadas=False)` ou uma função que a página chama por último.
- **P0-UI (Arthur), carregador:** no #45, `streamlit run src/transporte/interface/app.py` chama `main()` sem carregador e o botão "Carregar rede" avisa que está bloqueado; a `main` já tem o `ler()` do #42. Até isso mudar, nenhuma página roda pelo comando do AGENTS.md.
- **P0-MODELO e modelagem (Henrique):** `docs/fontes/modelagem.md` §3.4 descreve a G_L como "ligação quando duas linhas compartilham parada ... sem peso", e o `relatorio/secoes/modelagem.tex` diz que a G_L "reduz a pergunta das baldeações a uma busca em largura entre padrões". A implementação é dirigida e guarda a posição das trocas, porque o BFS comum só dá limite inferior (B1). Proposta de texto para a tabela: "P → Q quando dá para descer de P e embarcar em Q na mesma parada ou a até R; a aresta guarda as posições da troca". Não alterei as fontes (AGENTS.md §1).
- **P0-DADOS (Miguel):** `scripts/baixar_gtfs.py` falhou em 11/11 com o curl no limite de 120 s (`exit status 28`) e funcionou com 900 s. Sugerir um limite maior, ou um parâmetro. O instantâneo de 11/11 tem SHA-256 diferente do de 05/11, mas as mesmas contagens.
- **F-BALD-2 (Rafael):** `TrajetoBaldeacoes` não tem tempo. Para o RF-BAL-03, somar no G_E da mesma faixa (`construir_gl(rede, faixa=...)`) a espera do embarque e as viagens de cada perna, e comparar com `trajeto_mais_rapido`.
- **Contrato publicado:** avisar o grupo que `VisaoGL` e `BALDEACAO` entraram em `visoes.py`, sem mudar nada do que já existia.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Rafael.
### Sessão 11/11/2026: etapas 1 a 3 na `feat/F-BALD-linhas`: `VisaoGL`, `construir_gl` e `menos_baldeacoes`, com 52 testes (gabarito à mão, rede de teste e NetworkX num grafo de estados). A comparação com o NetworkX achou o caso do laço P → P (B2); 12.000 consultas em redes aleatórias sem divergência.
### Sessão 11/11/2026: etapa 5 no feed real: 36,7 ms por consulta, máximo 172,9 ms, 0 divergências em 200; construção otimizada de 7,7 s para 4,5 s (dia); `benchmarks/medir_baldeacoes.py`.
### Sessão 11/11/2026: etapa 4 na `feat/F-BALD-pagina` (com o #45 por merge): página Baldeações e correção do controle de camadas do mapa; conferida no feed real pelo `AppTest`.
### Sessão 11/11/2026: etapa 6: Como funciona, 5 perguntas, diagrama `atividade-menos-baldeacoes`, `docs/GUIA.md` §5.3, §8 e §10, `relatorio/secoes/F-BALD.tex` com figura do mapa real, roteiro do vídeo; decisões B1 a B7 propostas.
