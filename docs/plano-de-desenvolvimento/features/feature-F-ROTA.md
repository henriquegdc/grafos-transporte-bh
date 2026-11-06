# F-ROTA · Trajeto mais rápido

**Período:** 1 · Essenciais (04/11 a 11/11) · **Classe:** prioritária
**Dono:** Henrique (@henriquegdc) · **Issue:** #7 · **Visões do grafo:** G_E
**Depende de:** P0-MODELO (G_E), P0-UI · **Bloqueia:** F-BALD-2 (função de trajeto até 08/11), F-ROTA-2
**Prazo:** 11/11 (checkpoint 07/11)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-ROT-01, RF-ROT-02). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 05/11, Henrique, branch `feat/F-ROTA-trajeto` (PR #39, sobre o #38): etapa 5, tempo medido no feed real com `benchmarks/medir_modelo_rota.py`, usando a `Rede` do PR #42 (P0-DADOS, em revisão); etapa 6 em rascunho (Como funciona, perguntas, diagrama de sequência, GUIA §5.1 e §10, roteiro do vídeo).
- **Onde parou:** etapas 1, 2 e 5 concluídas; etapa 6 com tudo menos a seção do relatório. `trajeto_mais_rapido` rodou em 200 consultas no G_E real (V = 46.100, E = 208.956): 75,8 ms por consulta em média, máximo 162,2 ms, 0 divergências com o NetworkX (ver Resultados). O X do RNF-05 está proposto como R4.
- **Próximo passo:** decidir R4 (X do RNF-05); conseguir 1 aprovação no PR #39 (a base vira `main` quando o #38 for integrado); avisar o Rafael (F-BALD-2) e o Miguel (F-ESPERA, RF-ESP-03) do contrato. Quando o #42 entrar: teste de integração com a rede de teste (etapa 3). Revisar o rascunho da etapa 6 (Henrique); seção do relatório quando houver os intervalos da F-ESPERA (tempo total e baldeações dependem deles). Etapa 4 (página com mapa, RF-ROT-02) quando o P0-UI publicar o contrato de página e o mapa.
- **Arquivos tocados:** `src/transporte/algoritmos/trajeto.py`, `tests/algoritmos/test_trajeto.py`, `benchmarks/medir_modelo_rota.py`, `docs/diagramas/sequencia-trajeto.{puml,png}`, `docs/GUIA.md` §5.1 e §10, este arquivo.
- **Como testar:** `PYTHONPATH=src python -m pytest tests/algoritmos/test_trajeto.py` (26 testes em 05/11); `ruff check src tests benchmarks`. Medição: `PYTHONPATH=src python benchmarks/medir_modelo_rota.py dados/brutos/bhtrans.zip` (precisa do PR #42 e do feed baixado por `scripts/baixar_gtfs.py`).
- **Bloqueios:** RF-ROT-02 depende do P0-UI (Arthur); teste de integração e merge do script de medição dependem do PR #42 (P0-DADOS, mudança pedida em 05/11); o merge depende do PR #38.

## Objetivo
Trajeto mais rápido. Fecha:

- **RF-ROT-01** (E): Calcular o trajeto mais rápido entre duas paradas, somando caminhada, espera, viagem e baldeações
- **RF-ROT-02** (E): Mostrar o trajeto no mapa, por trecho (a pé, espera, linha usada), com os tempos

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 05/11: `trajeto_mais_rapido` (Dijkstra do núcleo em G_E) e reconstrução em trechos |
| Modelo e dados | em andamento | 05/11: roda sobre o G_E do `construir_ge` (PR #38) montado da `Rede` real do PR #42; falta o teste de integração depois do merge do #42 |
| Interface | não iniciado | depende do contrato de página e do mapa (P0-UI) |
| Testes | concluído | 05/11: 26 verdes. Gabarito à mão (linha direta, baldeação, troca que vence a direta, espera longa que inverte a escolha, só a pé, caminhadas encadeadas, a pé nas pontas), bordas (origem = destino, inalcançável, parada inexistente, falha e reativação) e NetworkX em 15 redes aleatórias (300 consultas: 255 com trajeto, 116 com baldeação, 195 com caminhada). Mutação à mão: agrupar a pé, agrupar ônibus e o tempo total derrubam testes |
| Desempenho (tempo medido) | concluído | 05/11: 75,8 ms por consulta em média (máximo 162,2 ms) no G_E real do pico da manhã; ver Resultados. X do RNF-05 a decidir (R4) |
| Guia (explicação e quiz) | em andamento | 05/11: rascunho de Como funciona e 5 perguntas, copiado para o `docs/GUIA.md` §5.1 e §10; Henrique revisa |
| Relatório | não iniciado | espera os intervalos da F-ESPERA para ter resultado de tempo total e baldeações |
| Vídeo | em andamento | 05/11: rascunho do roteiro; a parte de interface espera o P0-UI |

## Especificação
`src/transporte/algoritmos/trajeto.py`:

| Símbolo | Conteúdo |
|---|---|
| `Trecho(tipo, paradas, tempo_s, padrao)` | Parte do trajeto com um só modo. `tipo` é `A_PE` ("caminhada"), `ESPERA` ("espera") ou `ONIBUS` ("viagem"); `paradas` da primeira à última (só uma na espera); `padrao` é None a pé |
| `Trajeto(origem, destino, tempo_total_s, baldeacoes, trechos)` | Resultado; `tempo_por_tipo()` soma o tempo de cada tipo (serve à F-ESPERA, RF-ESP-03) |
| `trajeto_mais_rapido(ge, origem, destino) -> Trajeto \| None` | Dijkstra do núcleo em G_E, com parada no destino; None se inalcançável; KeyError para parada inexistente. Tempo O((V + E) log V) + O(V + k) |

Algoritmos previstos (docs/fontes/modelagem.md §3.5):
- Dijkstra · visão G_E · O((V + E) log V) · Pesos não negativos

## Como funciona e por quê

**O problema.** Dadas duas paradas, achar o trajeto que chega mais cedo, em média, somando caminhada, espera e viagem, e dizer ao passageiro o que fazer em cada parte: andar até onde, esperar qual linha, descer onde.

**A visão: G_E.** Em G_P, ficar no ônibus e trocar de ônibus custam o mesmo, porque a aresta não sabe em que linha o passageiro está. Em G_E cada (parada, padrão) é uma plataforma; trocar de linha obriga a desembarcar, voltar à parada e pagar um novo embarque, que carrega a espera da nova linha (`docs/GUIA.md` §3). Por isso o problema vira um caminho mínimo comum: um único Dijkstra soma as quatro coisas, sem penalidade arbitrária por baldeação.

**Passo a passo** (`trajeto_mais_rapido(ge, origem, destino)`; diagrama de sequência em `docs/diagramas/sequencia-trajeto.png`):

1. Traduz as paradas em vértices de parada de G_E (`ge.vertice_da_parada`); parada inexistente dá KeyError.
2. Roda o `dijkstra` do núcleo (heap binário próprio, sem `heapq`) a partir da origem, parando quando o destino é fechado. Destino com distância infinita devolve None.
3. Reconstrói o caminho como lista de **arestas** (`caminho_arestas`), porque o tipo de cada passo (caminhada, embarque, viagem, desembarque) está na aresta.
4. Conta as baldeações: embarques menos um (`ge.baldeacoes`).
5. Agrupa as arestas em trechos: caminhadas seguidas viram um trecho a pé; embarque vira espera; viagens seguidas do mesmo padrão viram um trecho de ônibus, que o desembarque fecha (o desembarque pesa 0 e não vira trecho).

Exemplo (figura `ge-exemplo` do relatório, com pesos inventados para a conta): de A a C, L1 de A a B e L2 de B a C, espera de 300 s nas duas e viagens de 240 s e 180 s. O Dijkstra acha 300 + 240 + 0 + 300 + 180 = 1.020 s. Os trechos são: espera de L1 em A (300 s), ônibus L1 de A a B (240 s), espera de L2 em B (300 s) e ônibus L2 de B a C (180 s). São dois embarques, então uma baldeação. Se andar de A a C levasse menos de 1.020 s, o trajeto seria um trecho a pé só, com 0 baldeações.

**Por que parar no destino é correto.** Com pesos não negativos, quando o Dijkstra tira um vértice do heap, a distância dele já é a mínima. Ao fechar o destino, nada que ainda está no heap melhora essa distância, então continuar só gastaria tempo.

**Complexidade.** V e E de G_E, k arestas no caminho. O Dijkstra com heap binário e inserção preguiçosa insere no máximo uma entrada por relaxamento bem-sucedido, então o heap recebe O(V + E) entradas, cada uma custando O(log V): O((V + E) log V). Parar no destino não muda o pior caso, mas na prática fecha só os vértices mais próximos que ele. A reconstrução custa O(V) para inverter os mapas da visão e O(k) para percorrer o caminho. Espaço O(V + E), pelas entradas do heap. Medido em 05/11 no feed real (ver Resultados): G_E com V = 46.100 e E = 208.956, 75,8 ms por consulta em média e 162,2 ms no pior caso de 200 consultas.

**Decisões e alternativas descartadas** (R1 a R3, decididas em 05/11):

- **Função em `algoritmos/trajeto.py`, não método da visão (R1):** a visão fica só com estrutura, e o A\* (F-ROTA-2) e o Yen (F-ROTA-OPC) entram no mesmo módulo.
- **Trechos agrupados, não arestas cruas (R2):** é o que o RF-ROT-02 pede e o que a página desenha; as arestas continuam disponíveis por `caminho_arestas`.
- **Inalcançável devolve None (R3):** numa rede com falhas (F-RES) ou recortada, não haver trajeto é resultado normal, não erro.
- **Sem penalidade por baldeação:** a baldeação já custa a espera da nova linha. Quem quer menos baldeações usa a F-BALD, que compara com este trajeto.

**Limitações.**

- O tempo é o **esperado** para quem chega à parada num instante qualquer da faixa (espera H/2), não o de um horário de saída exato; não é um planejador de viagem em tempo real.
- Enquanto a F-ESPERA não publica os intervalos, toda espera é 300 s (D6). Com isso baldear sai barato: na medição de 05/11, 31 de 200 trajetos tinham 3 ou mais baldeações.
- Uma viagem que começa no fim de uma faixa e continua na seguinte só conta na faixa em que parte (D10).
- Caminhada em linha reta, sem ruas, até 300 m entre paradas; não há caminhada da origem do passageiro até a primeira parada.

## Perguntas de verificação

1. **Por que um único Dijkstra basta para somar caminhada, espera, viagem e baldeação?** Porque em G_E trocar de linha obriga a passar por uma aresta de embarque, que pesa a espera da nova linha; a baldeação vira custo comum do caminho.
2. **Por que o caminho é reconstruído por arestas e não por vértices?** Porque o tipo do passo (caminhada, embarque, viagem, desembarque) está na aresta; é dele que saem os trechos e a contagem de baldeações.
3. **Por que dá para parar o Dijkstra quando o destino sai do heap?** Com pesos não negativos, a distância de um vértice fechado é definitiva; o que resta no heap não melhora o destino.
4. **O tempo total é o horário de chegada de quem sai agora?** Não. É o tempo esperado para quem chega à parada num instante qualquer da faixa: a espera de cada embarque é H/2.
5. **O que acontece se não houver trajeto?** A função devolve None, e a página mostra "sem trajeto"; isso é normal com paradas ou linhas desativadas (F-RES).

## Critérios de aceite
- [x] RF-ROT-01: Calcular o trajeto mais rápido entre duas paradas, somando caminhada, espera, viagem e baldeações (05/11, sobre G_E montado à mão; no feed real, 200 de 200 consultas com trajeto e 0 divergências com o NetworkX)
- [ ] RF-ROT-02: Mostrar o trajeto no mapa, por trecho (a pé, espera, linha usada), com os tempos

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [ ] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [ ] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature (05/11, em Como funciona)
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina (05/11)
- [ ] Página ou bloco na interface funcionando com o dataset real
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/` (05/11: `sequencia-trajeto`)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md` (05/11, rascunho; Henrique revisa)
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação
- [ ] Roteiro do vídeo escrito no arquivo da feature
- [ ] Arquivo da feature atualizado: retomada ("concluída"), status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | concluída em 05/11 (publicada já implementada) |
| 2 | Algoritmo com testes de corretude | concluída em 05/11 |
| 3 | Integração com a visão do grafo e com os dados reais | em andamento: roda no feed real com a `Rede` do PR #42; falta o teste de integração na rede de teste, depois do merge do #42 |
| 4 | Página na interface | bloqueada: contrato de página e mapa (P0-UI) |
| 5 | Tempo medido na rede real e complexidade justificada | concluída em 05/11 (tempo em Resultados; complexidade em Como funciona) |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | em andamento: rascunho de 05/11 (Como funciona, perguntas, `sequencia-trajeto`, GUIA §5.1 e §10, roteiro); falta a seção do relatório e a revisão do Henrique |

## Resultados para o relatório
_Todo número vem com o comando que o gerou._

**Tempo de consulta, 05/11/2026.** Comando: `PYTHONPATH=src python benchmarks/medir_modelo_rota.py dados/brutos/bhtrans.zip`, sobre o código do PR #39 (`51545dc`) com a leitura do PR #42 (`77b0fbd`, ainda não integrado). Feed: GTFS convencional da PBH baixado em 05/11/2026, SHA-256 `623bdf422fb01e8c80373bf92d9cf261199cff213b9eaee9ff16a5610d8d2bd2` (o mesmo do arquivo da P0-DADOS), serviço de 04/11/2026: 9.659 paradas, 698 padrões, 24.503 viagens. Máquina: Intel Core i5-13600KF, 31,8 GB, Windows 11, Python 3.14.3.

| Medida | Valor |
|---|---|
| Visão | G_E do pico da manhã: V = 46.100, E = 208.956 |
| Consultas | 200 pares de paradas sorteados (semente 2026) |
| 200 consultas seguidas, `medir`, n = 5 | 15,169 s ± 0,420 s, ou 75,8 ms por consulta |
| Cada consulta isolada, `medir`, n = 3 | mediana 76,3 ms, p95 134,7 ms, máximo 162,2 ms |
| Com trajeto | 200 de 200 |
| Tempo total mediano | 55,2 min |
| Baldeações | 0: 27; 1: 75; 2: 67; 3 ou mais: 31 |
| Conferência com `nx.dijkstra_path_length` no mesmo grafo | 0 divergências em 200 |

Limitação: a espera nas arestas de embarque é a padrão de 300 s, porque a tabela de intervalos da F-ESPERA ainda não existe. Com espera fixa, baldear custa pouco, o que explica as 31 consultas com 3 ou mais baldeações; tempo total e baldeações não vão para o relatório antes de rodar com os intervalos reais. O tempo de consulta não depende disso.

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

Rascunho de 05/11 (Henrique revisa; a parte de interface espera o P0-UI):

1. **Problema (20 s):** de uma parada a outra em BH, qual o caminho que chega antes, contando a caminhada, a espera e a troca de ônibus?
2. **Na ferramenta (45 s):** escolher origem, destino e faixa; mostrar no mapa os trechos com cores por tipo e a lista "andar até X, esperar a linha Y, descer em Z" com os tempos; trocar a faixa e mostrar o trajeto mudar.
3. **Como funciona (45 s):** G_E de exemplo, por que trocar de linha passa pelo embarque; um Dijkstra só, parando no destino; a reconstrução em trechos. Complexidade O((V + E) log V).
4. **Resultado e limitação (30 s):** cerca de 76 ms por consulta na rede inteira (V = 46.100), conferido com o NetworkX em 200 consultas; limitação: o tempo é o esperado da faixa, não o de um horário de saída exato.

## Pendências
- **F-BALD-2 (Rafael):** a função de trajeto mais rápido era para 08/11. Avisar que o contrato está em `algoritmos/trajeto.py` (no PR da F-ROTA): `trajeto_mais_rapido(ge, origem, destino)` dá `tempo_total_s` e `baldeacoes` para comparar com o trajeto de menos baldeações.
- **F-ESPERA (Miguel):** o RF-ESP-03 decompõe o tempo em caminhada, espera e viagem; `Trajeto.tempo_por_tipo()` já faz isso para o horário médio da faixa.
- **RNF-05:** o X (segundos por consulta) devia ter sido fixado em 03/11; a primeira medição saiu em 05/11. Ver R4.
- **PR empilhado:** o #39 tem base `feat/P0-MODELO-construtores`; integrar o #38 primeiro.
- **Script de medição:** `benchmarks/medir_modelo_rota.py` importa `transporte.dados`, que chega com o PR #42; até lá só roda com o código do #42 junto. O import fica dentro de `main()` para o módulo continuar importável.
- **Espera real:** refazer a medição de tempo total e baldeações quando a F-ESPERA publicar os intervalos (ver limitação em Resultados).

### Decisão a tomar: R4, o X do RNF-05

- **R4.** Fixar X = 1 s por consulta de trajeto na rede completa de BH. **Recomendo:** a pior consulta medida levou 162,2 ms e a média 75,8 ms, o que deixa margem de cerca de 6 vezes para máquinas mais lentas e para a montagem dos trechos na página. A construção do G_E (cerca de 0,35 s) fica fora, porque a página monta a visão uma vez por faixa e reaproveita. Alternativa: X = 0,5 s, mais apertado (3 vezes o pior caso), com risco de falhar em notebook mais fraco.

### ~~Decisões a tomar~~ Decididas em 05/11/2026: R1 a R3 aceitas pela recomendação

- **R1. Onde mora o trajeto.** (a) `src/transporte/algoritmos/trajeto.py`, função sobre `VisaoGE`; (b) método de `VisaoGE`. **Recomendo (a):** segue o padrão da F-MET (`algoritmos/centralidade.py`), deixa a visão só com estrutura, e F-ROTA-2 (A*) e F-ROTA-OPC (Yen) entram no mesmo módulo.
- **R2. Formato do resultado.** Trechos agrupados (caminhadas seguidas viram um trecho; viagens seguidas do mesmo padrão viram um trecho de ônibus; embarque vira "espera"; desembarque, com peso 0, não aparece). Alternativa: devolver as arestas cruas. **Recomendo os trechos:** é o que o RF-ROT-02 pede ("por trecho: a pé, espera, linha usada") e o que a página desenha; as arestas continuam disponíveis por `caminho_arestas` para quem precisar.
- **R3. Inalcançável devolve None** em vez de levantar erro. **Recomendo:** é um resultado normal numa rede com falhas (F-RES) ou recortada, e a página só precisa mostrar "sem trajeto".

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Henrique.
### Sessão 05/11/2026: etapas 1 e 2 na branch `feat/F-ROTA-trajeto` (sobre o PR #38): `trajeto_mais_rapido`, `Trecho` e `Trajeto`; 26 testes, 269 na suíte; decisões R1 a R3 propostas.
### Decisão 05/11/2026: R1 a R3 aceitas pela recomendação.
### PR 05/11/2026: #39 aberto, empilhado sobre o #38.
### Sessão 05/11/2026: etapa 5 no feed real com a `Rede` do PR #42: 75,8 ms por consulta em média, máximo 162,2 ms, 0 divergências com o NetworkX em 200 consultas; `benchmarks/medir_modelo_rota.py`; R4 (X do RNF-05) proposta.
### Sessão 05/11/2026: etapa 6 em rascunho: Como funciona e por quê, 5 perguntas de verificação, diagrama `sequencia-trajeto`, `docs/GUIA.md` §5.1 e §10 e roteiro do vídeo.
