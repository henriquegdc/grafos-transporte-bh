# F-ROTA · Trajeto mais rápido

**Período:** 1 · Essenciais (04/11 a 11/11) · **Classe:** prioritária
**Dono:** Henrique (@henriquegdc) · **Issue:** #7 · **Visões do grafo:** G_E
**Depende de:** P0-MODELO (G_E), P0-UI · **Bloqueia:** F-BALD-2 (função de trajeto até 08/11), F-ROTA-2
**Prazo:** 11/11 (checkpoint 07/11)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-ROT-01, RF-ROT-02). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 05/11, Henrique, branch `feat/F-ROTA-trajeto` (PR #39, sobre o #38): etapa 5, tempo medido no feed real com `benchmarks/medir_modelo_rota.py`, usando a `Rede` do PR #42 (P0-DADOS, em revisão).
- **Onde parou:** etapas 1, 2 e 5 concluídas. `trajeto_mais_rapido` rodou em 200 consultas no G_E real (V = 46.100, E = 208.956): 75,8 ms por consulta em média, máximo 162,2 ms, 0 divergências com o NetworkX (ver Resultados). O X do RNF-05 está proposto como R4.
- **Próximo passo:** decidir R4 (X do RNF-05); conseguir 1 aprovação no PR #39 (a base vira `main` quando o #38 for integrado); avisar o Rafael (F-BALD-2) e o Miguel (F-ESPERA, RF-ESP-03) do contrato. Quando o #42 entrar: teste de integração com a rede de teste (etapa 3). Depois: etapa 6 e etapa 4 (página com mapa, RF-ROT-02) quando o P0-UI publicar o contrato de página e o mapa.
- **Arquivos tocados:** `src/transporte/algoritmos/trajeto.py`, `tests/algoritmos/test_trajeto.py`, `benchmarks/medir_modelo_rota.py`, este arquivo.
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
| Guia (explicação e quiz) | não iniciado | |
| Relatório | não iniciado | |
| Vídeo | não iniciado | |

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
_A escrever a cada etapa concluída do plano de implementação, para um colega que não viu o código: o problema, a visão do grafo e por que ela, o algoritmo passo a passo com um exemplo pequeno, a complexidade com a justificativa, as decisões com as alternativas descartadas e as limitações._

## Perguntas de verificação
_3 a 5 perguntas que qualquer integrante deve saber responder, cada uma com a resposta curta._

## Critérios de aceite
- [x] RF-ROT-01: Calcular o trajeto mais rápido entre duas paradas, somando caminhada, espera, viagem e baldeações (05/11, sobre G_E montado à mão; no feed real, 200 de 200 consultas com trajeto e 0 divergências com o NetworkX)
- [ ] RF-ROT-02: Mostrar o trajeto no mapa, por trecho (a pé, espera, linha usada), com os tempos

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [ ] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [ ] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente
- [ ] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina (05/11)
- [ ] Página ou bloco na interface funcionando com o dataset real
- [ ] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/`
- [ ] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
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
| 5 | Tempo medido na rede real e complexidade justificada | tempo medido em 05/11; a justificativa da complexidade entra no "Como funciona" (etapa 6) |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | |

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
