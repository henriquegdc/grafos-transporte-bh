# P0-GRAFO · Núcleo de grafos, heap e buscas

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Thiago (@Thiagocs8) · **Issue:** #2 · **Visões do grafo:** todas (estrutura genérica)
**Depende de:** nada · **Bloqueia:** P0-MODELO e todas as features
**Prazo:** assinaturas 30/10; implementado 01/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-GRF-01, RF-GRF-02, RF-GRF-03, RF-GRF-08). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 05/11, Thiago, branch `fix/P0-GRAFO-ajustes-revisao` (ajustes pedidos na revisão do PR #35).
- **Onde parou:** etapas 1 e 2 concluídas e integradas na `main` pelo PR #35 (aprovado pelo Henrique em 05/11, squash `7b73a09`); decisões G1 a G6 aceitas. Ajustes da revisão feitos nesta branch: `caminho` e `caminho_arestas` passam a validar o destino (187 testes do núcleo verdes).
- **Próximo passo:** subir esta branch e abrir um PR curto para o Henrique (Refs #2). Em paralelo, começar a F-MET (graus e Brandes sobre o `Grafo` genérico não dependem do G_P). Itens do DoD para depois: etapa 5 (tempo medido com `medir` quando o G_P real existir) e etapa 6 (Como funciona e por quê com a justificativa das complexidades, perguntas de verificação, diagrama de sequência do Dijkstra, seção do relatório e roteiro do vídeo).
- **Arquivos tocados:** `src/transporte/grafo/{heap,grafo,buscas}.py`, `tests/grafo/{test_heap,test_grafo,test_buscas}.py`, este arquivo.
- **Como testar:** `PYTHONPATH=src .venv/Scripts/python -m pytest tests/grafo` (187 testes em 05/11); `ruff check src tests`.
- **Bloqueios:** nenhum. Ambiente local criado em 05/11 com `uv` (Python 3.12.14, pytest, networkx, ruff em `.venv`); o `PYTHONPATH=src` é necessário até a P0-REPO publicar a configuração do pytest.

## Objetivo
Núcleo de grafos, heap e buscas. Fecha:

- **RF-GRF-01** (E): Estrutura própria de grafo dirigido e ponderado, com lista de adjacência
- **RF-GRF-02** (E): BFS e Dijkstra genéricos, com reconstrução de caminho
- **RF-GRF-03** (E): Desativar e reativar vértices e arestas sem reconstruir o grafo
- **RF-GRF-08** (E): Fila de prioridade própria (heap binário de mínimo) usada pelos algoritmos de caminho mínimo

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 05/11: HeapMin, Grafo, bfs, dijkstra, caminho e caminho_arestas na `main` (PR #35); validação do destino na reconstrução em PR curto |
| Modelo e dados | não iniciado | |
| Interface | não iniciado | |
| Testes | concluído | 05/11: 187 verdes. HeapMin (29: gabarito à mão e comparação com sorted); Grafo (57) e buscas (101): gabarito à mão, casos de borda e comparação com o NetworkX em grafos aleatórios com falhas |
| Desempenho (tempo medido) | não iniciado | |
| Guia (explicação e quiz) | não iniciado | |
| Relatório | não iniciado | |
| Vídeo | não iniciado | |

## Especificação
Contrato inicial em `docs/fontes/plano-de-projeto.md` §9. Publicar as assinaturas com o comentário `estado: planejado` antes de implementar; trocar para `implementado` quando os testes passarem.

Algoritmos previstos (docs/fontes/modelagem.md §3.5):
- Heap binário de mínimo · visão (estrutura) · O(log n) por inserção e extração · Usado por todos os Dijkstras; inserção preguiçosa em vez de diminuir chave
- BFS · visão G_L · O(V + E) · Mínimo de baldeações
- Dijkstra · visão G_E · O((V + E) log V) · Pesos não negativos

## Como funciona e por quê
_A escrever a cada etapa concluída do plano de implementação, para um colega que não viu o código: o problema, a visão do grafo e por que ela, o algoritmo passo a passo com um exemplo pequeno, a complexidade com a justificativa, as decisões com as alternativas descartadas e as limitações._

## Perguntas de verificação
_3 a 5 perguntas que qualquer integrante deve saber responder, cada uma com a resposta curta._

## Critérios de aceite
- [x] RF-GRF-01: Estrutura própria de grafo dirigido e ponderado, com lista de adjacência (`grafo.py`; `tests/grafo/test_grafo.py`)
- [x] RF-GRF-02: BFS e Dijkstra genéricos, com reconstrução de caminho (`buscas.py`; `tests/grafo/test_buscas.py`, comparação com o NetworkX)
- [x] RF-GRF-03: Desativar e reativar vértices e arestas sem reconstruir o grafo (flags O(1) em `grafo.py`; testes de desativação em `test_grafo.py` e `test_buscas.py`)
- [x] RF-GRF-08: Fila de prioridade própria (heap binário de mínimo) usada pelos algoritmos de caminho mínimo (`heap.py`, usado por `dijkstra`; `tests/grafo/test_heap.py`)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [x] Código integrado na `main` por PR aprovado por outro integrante (PR #35, aprovado pelo Henrique em 05/11)
- [ ] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (178 testes em 05/11)
- [ ] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature (docstrings prontas; falta a justificativa em "Como funciona e por quê", etapa 6)
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
| 1 | Contrato (assinaturas com estado "planejado") | concluída em 05/11 |
| 2 | Algoritmo com testes de corretude | concluída em 05/11 (2a HeapMin, 2b Grafo, 2c buscas) |
| 3 | Integração com a visão do grafo e com os dados reais | |
| 4 | Página na interface | |
| 5 | Tempo medido na rede real e complexidade justificada | |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | |

## Resultados para o relatório
_Vazio até haver execução real. Todo número vem com o comando que o gerou._

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

## Pendências
- ~~**Avisar o grupo dos acréscimos ao contrato do §9 (G1 a G3)**~~ **feito em 05/11/2026:** grupo avisado e acréscimos aceitos pelo Henrique na revisão do PR #35. Continua aberto, para decisão do grupo: o §9 do `plano-de-projeto.md` passar a apontar para `src/transporte/grafo/` como contrato vigente (o Henrique concorda; `docs/fontes/` não muda por conta própria).
- ~~**Confirmar com o Henrique (P0-MODELO)**~~ **confirmado em 05/11/2026 (revisão do PR #35):** `caminho_arestas` atende `VisaoGE.baldeacoes`; ele atualiza o `Resultado` no `classes.puml` e trata tempo negativo do GTFS no construtor antes de `adicionar_aresta` (pendências do P0-MODELO).
- ~~**Ambiente local**~~ **resolvido em 05/11/2026:** Python 3.12.14 com pytest, networkx e ruff em `.venv`, criado com `uv`. O `requirements.txt`, a configuração do pytest e o hook continuam com a P0-REPO (Caio).

### ~~Decisões a tomar~~ Decididas em 05/11/2026: G1 a G6 propostas pelo Thiago e aceitas pelo Henrique na revisão do PR #35

- **G1. Resultado das buscas.** (a) `Resultado(origem, dist, pred, pred_aresta)` com `INF` e `SEM_PRED = -1`; (b) só `dist` e `pred`, como no diagrama. **Recomendo (a):** `pred` sozinho não distingue arestas paralelas nem diz o tipo do trecho, e `VisaoGE.baldeacoes` (P0-MODELO) recebe ids de aresta. Custa uma lista a mais, O(V).
- **G2. Acessores a mais no Grafo.** `num_vertices`, `num_arestas`, `rotulo`, `aresta(a) -> (origem, destino, peso, tipo)`, `vertice_ativo` e `aresta_ativa`. **Recomendo aceitar:** os consumidores precisam percorrer os vértices (Brandes, Tarjan, eficiência) e ler o tipo das arestas (baldeações), e sem isso cada um acessaria atributos internos.
- **G3. Reativação individual.** Acrescentar `reativar_vertice` e `reativar_aresta`, além do `reativar_tudo` do §9. **Recomendo aceitar:** o RF-GRF-03 pede "desativar e reativar vértices e arestas", e o ranking de criticidade (F-RES-2) desliga um candidato por vez; reativar tudo seria O(V + E) a cada candidato contra O(1).
- **G4. Pesos validados na inserção.** `adicionar_aresta` recusa peso negativo, infinito ou NaN (ValueError). **Recomendo aceitar:** todo peso do projeto é tempo em segundos, e o Dijkstra só é correto com pesos não negativos; validar na inserção custa O(1) e evita um erro silencioso dentro da busca.
- **G5. Semântica da desativação.** Vértice desativado some das buscas junto com as arestas que tocam nele, sem alterá-las; origem desativada não alcança nada, nem a si mesma. **Recomendo aceitar:** é o que "a parada fechou" significa para a F-RES, e reativar devolve o grafo exatamente ao estado anterior.
- **G6. Empates no heap.** Desempate pelo menor item. **Recomendo aceitar:** torna a ordem de extração e os caminhos de mesmo custo determinísticos, o que os testes com gabarito exigem.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Thiago.
### Sessão 05/11/2026: branch `feat/P0-GRAFO-nucleo`; contrato de `heap.py`, `grafo.py` e `buscas.py` publicado com estado: planejado (§9 mais os acréscimos G1 a G3); decisões G1 a G6 propostas.
### Sessão 05/11/2026: ambiente local com uv; etapa 2a, HeapMin implementado com 29 testes verdes.
### Sessão 05/11/2026: etapa 2b, Grafo implementado com 57 testes verdes (86 no total).
### Sessão 05/11/2026: etapa 2c, bfs, dijkstra, caminho e caminho_arestas implementados com 92 testes (178 no total); critérios de aceite RF-GRF-01, 02, 03 e 08 atendidos.
### PR 05/11/2026: branch `feat/P0-GRAFO-nucleo` subida para revisão do Henrique (Closes #2).
### Merge 05/11/2026: PR #35 aprovado pelo Henrique e integrado na `main` (squash `7b73a09`); decisões G1 a G6 aceitas.
### Sessão 05/11/2026: ajustes da revisão na branch `fix/P0-GRAFO-ajustes-revisao`: `caminho` e `caminho_arestas` validam o destino (destino negativo devolvia caminho errado sem erro); 9 testes novos, 187 no total.
