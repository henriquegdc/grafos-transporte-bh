# F-ROTA · Trajeto mais rápido

**Período:** 1 · Essenciais (04/11 a 11/11) · **Classe:** prioritária
**Dono:** Henrique (@henriquegdc) · **Issue:** #7 · **Visões do grafo:** G_E
**Depende de:** P0-MODELO (G_E), P0-UI · **Bloqueia:** F-BALD-2 (função de trajeto até 08/11), F-ROTA-2
**Prazo:** 11/11 (checkpoint 07/11)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-ROT-01, RF-ROT-02). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 05/11, Henrique, branch `feat/F-ROTA-trajeto`, criada em cima de `feat/P0-MODELO-construtores` (PR #38), porque usa `construir_ge` e `baldeacoes`.
- **Onde parou:** etapas 1 e 2 concluídas: `src/transporte/algoritmos/trajeto.py` com `Trecho`, `Trajeto` e `trajeto_mais_rapido` (`estado: implementado`), 26 testes verdes (gabarito à mão, bordas, falhas e comparação com o NetworkX em 15 redes aleatórias). RF-ROT-01 atendido sobre G_E montado à mão.
- **Próximo passo:** conseguir 1 aprovação no PR #39 (empilhado sobre o #38; a base vira `main` quando o #38 for integrado); avisar o Rafael (F-BALD-2) e o Miguel (F-ESPERA, RF-ESP-03) do contrato. Depois: etapa 4 (página de trajetos com mapa, RF-ROT-02) quando o P0-UI publicar o contrato de página e o mapa; etapas 3 e 5 quando a `Rede` existir (P0-DADOS), fixando o X do RNF-05 com a primeira medição.
- **Arquivos tocados:** `src/transporte/algoritmos/trajeto.py`, `tests/algoritmos/test_trajeto.py`, este arquivo.
- **Como testar:** `PYTHONPATH=src python -m pytest tests/algoritmos/test_trajeto.py` (26 testes em 05/11); `ruff check src tests`.
- **Bloqueios:** RF-ROT-02 depende do P0-UI (Arthur); dados reais e tempo medido dependem do P0-DADOS (Miguel, não iniciado); o merge depende do PR #38.

## Objetivo
Trajeto mais rápido. Fecha:

- **RF-ROT-01** (E): Calcular o trajeto mais rápido entre duas paradas, somando caminhada, espera, viagem e baldeações
- **RF-ROT-02** (E): Mostrar o trajeto no mapa, por trecho (a pé, espera, linha usada), com os tempos

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 05/11: `trajeto_mais_rapido` (Dijkstra do núcleo em G_E) e reconstrução em trechos |
| Modelo e dados | em andamento | 05/11: roda sobre o G_E do `construir_ge` (PR #38); falta a `Rede` real |
| Interface | não iniciado | depende do contrato de página e do mapa (P0-UI) |
| Testes | concluído | 05/11: 26 verdes. Gabarito à mão (linha direta, baldeação, troca que vence a direta, espera longa que inverte a escolha, só a pé, caminhadas encadeadas, a pé nas pontas), bordas (origem = destino, inalcançável, parada inexistente, falha e reativação) e NetworkX em 15 redes aleatórias (300 consultas: 255 com trajeto, 116 com baldeação, 195 com caminhada). Mutação à mão: agrupar a pé, agrupar ônibus e o tempo total derrubam testes |
| Desempenho (tempo medido) | não iniciado | |
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
- [x] RF-ROT-01: Calcular o trajeto mais rápido entre duas paradas, somando caminhada, espera, viagem e baldeações (05/11, sobre G_E montado à mão; falta rodar com a rede real)
- [ ] RF-ROT-02: Mostrar o trajeto no mapa, por trecho (a pé, espera, linha usada), com os tempos

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [ ] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [ ] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente
- [ ] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [ ] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
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
| 3 | Integração com a visão do grafo e com os dados reais | G_E pronto (PR #38); falta a `Rede` (P0-DADOS) |
| 4 | Página na interface | bloqueada: contrato de página e mapa (P0-UI) |
| 5 | Tempo medido na rede real e complexidade justificada | |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | |

## Resultados para o relatório
_Vazio até haver execução real. Todo número vem com o comando que o gerou._

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

## Pendências
- **F-BALD-2 (Rafael):** a função de trajeto mais rápido era para 08/11. Avisar que o contrato está em `algoritmos/trajeto.py` (no PR da F-ROTA): `trajeto_mais_rapido(ge, origem, destino)` dá `tempo_total_s` e `baldeacoes` para comparar com o trajeto de menos baldeações.
- **F-ESPERA (Miguel):** o RF-ESP-03 decompõe o tempo em caminhada, espera e viagem; `Trajeto.tempo_por_tipo()` já faz isso para o horário médio da faixa.
- **RNF-05:** o X (segundos por consulta) devia ter sido fixado em 03/11 depois da primeira medição, que ainda não existe (sem `Rede`). Fixar na etapa 5.
- **PR empilhado:** o #39 tem base `feat/P0-MODELO-construtores`; integrar o #38 primeiro.

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
