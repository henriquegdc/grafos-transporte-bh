# P0-GRAFO · Núcleo de grafos, heap e buscas

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Thiago (@Thiagocs8) · **Issue:** #2 · **Visões do grafo:** todas (estrutura genérica)
**Depende de:** nada · **Bloqueia:** P0-MODELO e todas as features
**Prazo:** assinaturas 30/10; implementado 01/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-GRF-01, RF-GRF-02, RF-GRF-03, RF-GRF-08). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 16/11, Thiago, branch `feat/F-MET-pagina` (fechamento do DoD do núcleo junto com a F-MET).
- **Onde parou:** código na `main` desde o #35 e o #36 (aprovados pelo Henrique). Em 16/11: tempo medido no feed real (`benchmarks/medir_nucleo.py`, Dijkstra igual ao NetworkX em G_P e G_E), Como funciona e por quê com a justificativa das complexidades, perguntas de verificação, GUIA §4, diagrama de sequência do Dijkstra (fonte), parágrafo do núcleo na Implementação e algoritmos na Fundamentação do relatório, roteiro do vídeo.
- **Próximo passo:** aprovação e merge do PR #54 (`feat/F-MET-pagina`, Closes #2); gravar o trecho do vídeo (prazo dos trechos: 18/11, plano-de-projeto §14.4).
- **Arquivos tocados:** `benchmarks/medir_nucleo.py`, `benchmarks/resultados/nucleo-2026-11-16.json`, `docs/diagramas/sequencia-dijkstra.puml`, `docs/GUIA.md` (§4, §8 e §10), `relatorio/secoes/implementacao.tex`, `relatorio/secoes/fundamentacao.tex`, este arquivo. Código do núcleo sem mudança.
- **Como testar:** `pytest tests/grafo` (187 testes); `ruff check`. Medição: `python scripts/baixar_gtfs.py` e `python benchmarks/medir_nucleo.py dados/brutos/bhtrans.zip`.
- **Bloqueios:** nenhum.

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
| Modelo e dados | concluído | 16/11: buscas medidas em G_P e G_E do feed real |
| Interface | não aplicável | O núcleo não tem tela; é usado por todas as páginas (Trajetos, Espera, Centralidades...) |
| Testes | concluído | 05/11: 187 verdes. HeapMin (29: gabarito à mão e comparação com sorted); Grafo (57) e buscas (101): gabarito à mão, casos de borda e comparação com o NetworkX em grafos aleatórios com falhas |
| Desempenho (tempo medido) | concluído | 16/11: ver Resultados |
| Guia (explicação e quiz) | concluído | 16/11: Como funciona, perguntas e GUIA §4, §8 e §10 |
| Relatório | concluído | 16/11: núcleo na Implementação e algoritmos na Fundamentação (o relatório não tem seção por feature de fundação) |
| Vídeo | parcial | 16/11: roteiro escrito; falta gravar |

## Especificação
Contrato inicial em `docs/fontes/plano-de-projeto.md` §9. Publicar as assinaturas com o comentário `estado: planejado` antes de implementar; trocar para `implementado` quando os testes passarem.

Algoritmos previstos (docs/fontes/modelagem.md §3.5):
- Heap binário de mínimo · visão (estrutura) · O(log n) por inserção e extração · Usado por todos os Dijkstras; inserção preguiçosa em vez de diminuir chave
- BFS · visão G_L · O(V + E) · Mínimo de baldeações
- Dijkstra · visão G_E · O((V + E) log V) · Pesos não negativos

## Como funciona e por quê

**O problema.** Todas as features precisam de um grafo dirigido e ponderado, de caminhos mínimos (por tempo ou por número de arestas) e de "fechar" paradas ou trechos para simular falhas. O enunciado proíbe biblioteca de grafo em `src/` e o grupo decidiu não usar o `heapq`, então a estrutura, as buscas e a fila de prioridade são do projeto. O núcleo não conhece GTFS nem parada: trabalha com vértices `0..V-1`, e cada visão (G_P, G_E, G_L) guarda os mapas entre os ids do GTFS e os vértices.

**A estrutura (`grafo.py`).** Listas paralelas indexadas pelo id: `_rotulo[u]` e `_vertice_ativo[u]` para os vértices; `_origem[a]`, `_destino[a]`, `_peso[a]`, `_tipo[a]` e `_aresta_ativa[a]` para as arestas; e `_adj[u]`, a lista de adjacência, com os **ids** das arestas que saem de u. Guardar o id, e não o par (destino, peso), deixa peso, tipo e estado de cada aresta num lugar só e permite arestas paralelas (uma de viagem e uma de caminhada entre as mesmas paradas) com ids distintos. `vizinhos(u)` devolve `(destino, peso, id)` só das arestas utilizáveis: aresta, origem e destino ativos. Desativar é marcar um booleano, O(1); nada é removido e os ids continuam valendo, então a F-RES desliga uma parada, mede e religa, sem reconstruir o grafo (RF-GRF-03).

**O heap (`heap.py`).** Heap binário de mínimo numa lista: a raiz na posição 0, os filhos de i em 2i + 1 e 2i + 2, o pai em (i - 1) // 2. Inserir põe o par no fim e o sobe enquanto for menor que o pai; extrair tira a raiz, põe a última folha no lugar e a desce trocando pelo menor filho. Cada operação percorre no máximo a altura da árvore, log₂ n. Os pares são `(prioridade, item)` comparados como tuplas, então o empate sai pelo menor item (G6), o que deixa os caminhos de mesmo custo determinísticos.

**Dijkstra com inserção preguiçosa (`buscas.py`).** O Dijkstra clássico usa "diminuir chave": quando acha um caminho melhor até v, atualiza a prioridade de v dentro do heap, o que exige saber onde v está. Aqui não: insere `(nova distância, v)` de novo e, quando uma entrada antiga de v sai do heap depois, ela é descartada porque v já está fechado. Passo a passo (diagrama `docs/diagramas/sequencia-dijkstra.puml`):

1. `dist[origem] = 0`, insere a origem no heap.
2. Extrai o menor `(d, u)`. Se u já foi fechado, descarta (entrada desatualizada). Senão fecha u: `d` é a distância definitiva, porque os pesos são não negativos e qualquer outro caminho passa por um vértice com distância ≥ d.
3. Para cada vizinho `(v, peso, a)`: se `d + peso < dist[v]`, atualiza `dist[v]`, `pred[v] = u`, `pred_aresta[v] = a` e insere `(d + peso, v)`.
4. Com `destino`, para quando ele é fechado (a F-ROTA usa isso).

Exemplo: arestas 0→1 (4), 0→2 (1), 2→1 (2), 1→3 (1). O heap começa com (0, 0). Fecha 0 e insere (4, 1) e (1, 2). Fecha 2 (d = 1) e acha 0→2→1 com 3 < 4: insere (3, 1), sem tirar o (4, 1). Fecha 1 (d = 3) e insere (4, 3). Sai (4, 1): 1 já está fechado, descarta. Fecha 3 com d = 4. Caminho até 3, pelos predecessores: 0, 2, 1, 3.

O `Resultado` guarda `dist`, `pred` e `pred_aresta` (G1); `caminho` reconstrói os vértices e `caminho_arestas` as arestas, de que a F-ROTA tira o tipo de cada passo (embarque, viagem...). A BFS é a mesma ideia com fila: cada vértice entra uma vez, na primeira vez que é visto, e a distância conta arestas.

**Complexidade e por quê.** Grafo: espaço O(V + E); adicionar vértice ou aresta, desativar e reativar O(1) amortizado; `vizinhos(u)` O(grau(u)). BFS: O(V + E) de tempo, porque cada vértice entra na fila uma vez e cada aresta é olhada uma vez. Dijkstra: cada aresta relaxada com sucesso insere uma entrada, então o heap recebe no máximo E + 1 entradas e cada inserção ou extração custa O(log E). Como E ≤ V², log E ≤ 2 log V, e o total fica O((V + E) log V) de tempo e O(V + E) de espaço (as entradas repetidas). É o mesmo limite do Dijkstra com diminuir chave e heap binário, sem precisar de um índice de posição dentro do heap.

**Decisões e alternativas descartadas** (G1 a G6, aceitas pelo Henrique na revisão do #35):

- **Inserção preguiçosa, não diminuir chave:** mesmo O((V + E) log V), código menor e sem o mapa vértice → posição no heap; custa espaço O(E) em vez de O(V).
- **Pesos validados na inserção (G4):** peso negativo, infinito ou NaN levanta ValueError. Todo peso do projeto é tempo em segundos, e o Dijkstra só é correto com pesos ≥ 0.
- **Desativação por flag (G5), com reativação individual (G3):** "a parada fechou" vira um booleano; a F-RES-2 testa um candidato por vez e religa em O(1), sem reconstruir.
- **Acessores a mais (G2):** `num_vertices`, `aresta(a)`, `vertice_ativo` etc., para os consumidores não lerem atributos internos.
- **Empate pelo menor item (G6):** ordem determinística, que os testes com gabarito exigem.

**Limitações.** Pesos negativos não são aceitos (nenhum peso do projeto é negativo). O grafo não remove vértice nem aresta: um grafo muito alterado acumula entradas desativadas. Com `destino`, só a distância do destino é garantida; as dos vértices ainda abertos podem ser provisórias.

## Perguntas de verificação

1. **Por que o heap pode ter o mesmo vértice várias vezes, e por que isso não quebra o Dijkstra?** Porque, em vez de diminuir a chave, inserimos de novo com a distância menor. A entrada antiga sai depois, com distância maior, e é descartada porque o vértice já está fechado.
2. **Por que inserção preguiçosa continua O((V + E) log V)?** O heap recebe no máximo uma entrada por relaxamento bem-sucedido, O(E), e cada operação custa O(log E) ≤ O(2 log V).
3. **Por que a adjacência guarda o id da aresta, e não (destino, peso)?** Para ter peso, tipo e estado num lugar só, permitir arestas paralelas e devolver o id no caminho (a F-ROTA lê o tipo de cada passo).
4. **Como a F-RES "fecha" uma parada sem reconstruir o grafo?** Desativa o vértice (um booleano, O(1)); `vizinhos` deixa de devolver as arestas que tocam nele, e reativar volta exatamente ao estado anterior.
5. **Por que a distância de um vértice é definitiva quando ele sai do heap?** Com pesos não negativos, qualquer outro caminho até ele passa por um vértice ainda no heap, com distância maior ou igual.

## Critérios de aceite
- [x] RF-GRF-01: Estrutura própria de grafo dirigido e ponderado, com lista de adjacência (`grafo.py`; `tests/grafo/test_grafo.py`)
- [x] RF-GRF-02: BFS e Dijkstra genéricos, com reconstrução de caminho (`buscas.py`; `tests/grafo/test_buscas.py`, comparação com o NetworkX)
- [x] RF-GRF-03: Desativar e reativar vértices e arestas sem reconstruir o grafo (flags O(1) em `grafo.py`; testes de desativação em `test_grafo.py` e `test_buscas.py`)
- [x] RF-GRF-08: Fila de prioridade própria (heap binário de mínimo) usada pelos algoritmos de caminho mínimo (`heap.py`, usado por `dijkstra`; `tests/grafo/test_heap.py`)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [x] Código integrado na `main` por PR aprovado por outro integrante (PR #35, aprovado pelo Henrique em 05/11)
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde (16/11)
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (178 testes em 05/11)
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
- [x] Página ou bloco na interface funcionando com o dataset real: não aplicável, o núcleo não tem tela própria; todas as páginas o usam
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/` (`sequencia-dijkstra.puml` e `.png`, PlantUML 1.2026.9)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [x] O revisor do PR consegue explicar o que o código faz (Henrique, #35 e #36)
- [x] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação: para a fundação, o núcleo entra em `implementacao.tex` (resultado e limitação; a figura de componentes já está lá) e os algoritmos em `fundamentacao.tex`
- [x] Roteiro do vídeo escrito no arquivo da feature
- [ ] Arquivo da feature atualizado: retomada ("concluída"), status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | concluída em 05/11 |
| 2 | Algoritmo com testes de corretude | concluída em 05/11 (2a HeapMin, 2b Grafo, 2c buscas) |
| 3 | Integração com a visão do grafo e com os dados reais | concluída: usado pelos construtores desde o #38; medido no feed real em 16/11 |
| 4 | Página na interface | não aplicável (sem tela própria) |
| 5 | Tempo medido na rede real e complexidade justificada | concluída em 16/11 |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | concluída em 16/11 (PNG do diagrama em 18/11) |

## Resultados para o relatório
_Todo número vem com o comando que o gerou._

**Núcleo no feed real, 16/11/2026.** Comando: `python scripts/baixar_gtfs.py` (limite do curl aumentado para 900 s) e `python benchmarks/medir_nucleo.py dados/brutos/bhtrans.zip`; JSON em `benchmarks/resultados/nucleo-2026-11-16.json`. Feed: GTFS convencional da PBH baixado em 16/11/2026, SHA-256 `241f0bb2dbb80ca59de9a9e59eb1135f359537b5dee6199ce6c47323140c01c0`; serviço de 11/11/2026, 9.660 paradas. Máquina: notebook Samsung 750XGL, Intel Core 5 120U (10 núcleos, 12 threads), 15,7 GB, Windows 11, Python 3.12.14. Tempos com `medir`, n = 5; buscas completas (sem destino) a partir de 20 origens sorteadas com semente 2026; G_E do pico da manhã com as esperas da F-ESPERA.

| Medida | Resultado | Tempo |
|---|---|---|
| HeapMin | 100.000 inserções e 100.000 extrações | 1,463 s ± 0,216 s (cerca de 7 µs por operação) |
| Dijkstra em G_P (V = 9.660, E = 122.799) | alcança 9.657 vértices de cada origem; distâncias iguais às do NetworkX nas 20 origens | 249,5 ms por busca (20 buscas: 4,990 s ± 0,725 s) |
| BFS em G_P | | 102,1 ms por busca (20 buscas: 2,042 s ± 0,678 s) |
| Dijkstra em G_E, pico da manhã (V = 46.102, E = 209.025) | alcança de 36.149 a 36.258 vértices; distâncias iguais às do NetworkX | 776,8 ms por busca (20 buscas: 15,536 s ± 3,494 s) |
| BFS em G_E | | 233,6 ms por busca (20 buscas: 4,671 s ± 0,921 s) |

Leitura: de G_P para G_E, V cresce 4,8 vezes e E 1,7 vez, e o Dijkstra fica 3,1 vezes mais lento, coerente com O((V + E) log V). A consulta de trajeto da F-ROTA é bem mais rápida (75,8 ms em 05/11) porque para no destino. A BFS é 2 a 3 vezes mais rápida que o Dijkstra no mesmo grafo: não tem heap nem o fator log.

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

Rascunho de 16/11 (Thiago revisa e grava):

1. **Problema (20 s):** todas as perguntas da ferramenta viram caminho mínimo ou busca num grafo, e o trabalho não permite biblioteca de grafo nem o `heapq`: o grafo, o heap e as buscas são nossos.
2. **Na ferramenta (30 s):** o núcleo não tem tela; mostrar uma página que o usa (Trajetos ou Centralidades) e, no código, `vizinhos` e `desativar_vertice` (a F-RES fecha uma parada com um booleano).
3. **Como funciona (60 s):** lista de adjacência com ids de aresta; heap binário (sobe e desce, log n); Dijkstra com inserção preguiçosa no exemplo 0→1 (4), 0→2 (1), 2→1 (2), 1→3 (1): a entrada (4, 1) fica no heap e é descartada. Por que continua O((V + E) log V).
4. **Resultado e limitação (30 s):** no feed real, Dijkstra completo em 250 ms no G_P e 777 ms no G_E (46 mil vértices), igual ao NetworkX; heap com 100 mil operações em 1,5 s. Limitação: pesos negativos não são aceitos, e o grafo só desativa, nunca remove.

## Pendências
- ~~**Avisar o grupo dos acréscimos ao contrato do §9 (G1 a G3)**~~ **feito em 05/11/2026:** grupo avisado e acréscimos aceitos pelo Henrique na revisão do PR #35. Continua aberto, para decisão do grupo: o §9 do `plano-de-projeto.md` passar a apontar para `src/transporte/grafo/` como contrato vigente (o Henrique concorda; `docs/fontes/` não muda por conta própria).
- ~~**Confirmar com o Henrique (P0-MODELO)**~~ **confirmado em 05/11/2026 (revisão do PR #35):** `caminho_arestas` atende `VisaoGE.baldeacoes`; ele atualiza o `Resultado` no `classes.puml` e trata tempo negativo do GTFS no construtor antes de `adicionar_aresta` (pendências do P0-MODELO).
- ~~**PNG do diagrama**~~ **feito em 18/11:** `docs/diagramas/sequencia-dijkstra.png`, gerado com o PlantUML 1.2026.9.
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
### PR 05/11/2026: #36 aberto com os ajustes da revisão do #35.
### Sessão 16/11/2026: fechamento do DoD na branch `feat/F-MET-pagina`: tempo no feed real (Dijkstra igual ao NetworkX em G_P e G_E), Como funciona e por quê, perguntas, GUIA §4, diagrama de sequência do Dijkstra (fonte), núcleo na Implementação e algoritmos na Fundamentação do relatório, roteiro do vídeo.
### Sessão 18/11/2026: rebase do PR #54 sobre a `main` (revisão do Rafael); PNG do diagrama de sequência do Dijkstra gerado com o PlantUML 1.2026.9.
