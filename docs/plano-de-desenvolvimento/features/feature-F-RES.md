# F-RES · Falhas e resiliência

**Período:** 1 · Essenciais (04/11 a 11/11) · **Classe:** prioritária
**Dono:** Caio (@CaioSResende) · **Issue:** #12 · **Visões do grafo:** G_P
**Depende de:** P0-GRAFO; eficiência de F-EFI · **Bloqueia:** F-RES-2
**Prazo:** 11/11 (checkpoint 07/11)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-RES-01, RF-RES-02, RF-RES-03). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada

**Relatório e página concluídos.** O [#61](https://github.com/henriquegdc/grafos-transporte-bh/pull/61), aprovado pelo Henrique, integrou a página Falhas e a figura `falhas-linha-832.png`. A figura apresenta uma amostra e a legenda distingue a perda exata. O relatório e a subseção do guia usam a eficiência de F-EFI. Para validar a página: `python -m pytest tests/interface/test_pagina_falhas.py`. Próximo passo: gravar o trecho pelo roteiro.

## Objetivo
Falhas e resiliência. Fecha:

- **RF-RES-01** (E): Simular a remoção de uma parada, de um trecho ou de uma linha
- **RF-RES-02** (E): Calcular as componentes fortemente conexas antes e depois da falha e listar as paradas isoladas
- **RF-RES-03** (E): Calcular a perda de eficiência causada pela falha

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | Tarjan iterativo, falhas e eficiência compartilhada com F-EFI desde #61. |
| Modelo e dados | concluído | 10/11: roda sobre `construir_gp` e `ler`; `indexar_linhas` liga trechos a linhas; integração testada na rede de teste e medida no feed real |
| Interface | concluído | 19/11: página Falhas (parada, trecho ou linhas; cartões antes e depois, tabela e mapa); 8 testes, inclusive o shell da P0-UI; conferida no feed real (13 s por simulação com 30 origens) |
| Testes | concluído | 10/11: 89 testes (gabarito à mão, 40 grafos aleatórios contra o NetworkX no Tarjan, 15 na eficiência, rede de teste ponta a ponta) |
| Desempenho (tempo medido) | concluído | 10/11: `benchmarks/medir_falhas.py` no feed real (ver Resultados) |
| Guia (explicação e quiz) | concluído | 16/11: GUIA §5.6 e §10; 17/11: as 3 decisões no GUIA §8 |
| Relatório | concluído | Figura da remoção da linha 832 conferida em `relatorio/secoes/F-RES.tex`, com legenda, resultado e limitação. |
| Vídeo | em andamento | Roteiro (rascunho) abaixo |

## Especificação
Assinaturas públicas em `src/transporte/simulacao/falhas.py` (`estado: implementado`):

- `componentes_fortes(g: Grafo) -> list[list[int]]`: Tarjan iterativo; O(V + E).
- `eficiencia_global(g, origens=None, n_referencia=None) -> float`: **provisória**, até a F-EFI publicar a dela; O(s (V + E) log V).
- `indexar_linhas(rede) -> dict[(parada, parada), set[linha]]`: O(K).
- `Falha(paradas=(), trechos=(), linhas=())`: o que sai de operação.
- `aplicar_falha(visao, falha, linhas_do_trecho=None) -> (vertices, arestas)` e `desfazer_falha(visao, vertices, arestas)`: para a F-RES-OPC (falhas em sequência).
- `simular_falha(visao, falha, linhas_do_trecho=None, amostra=None, semente=0) -> ResultadoFalha`: componentes antes e depois, `paradas_isoladas`, `paradas_desconectadas`, eficiência antes e depois e `perda_eficiencia`.

Algoritmos previstos (docs/fontes/modelagem.md §3.5):
- Tarjan iterativo (componentes fortemente conexas) · visão G_P · O(V + E) · Iterativo por causa do limite de recursão

## Como funciona e por quê
_Rascunho do agente em 10/11; o Caio revisa._

**O problema.** O que acontece com a rede quando uma parada fecha, um trecho é interditado ou uma linha para? Queremos saber quem fica sem acesso e quanto a rede perde em rapidez.

**A visão: G_P.** Um vértice por parada e arestas dirigidas de viagem (parada seguinte de alguma linha, com o tempo mediano) e de caminhada (até 300 m, nos dois sentidos). É a visão em que "parada" e "trecho" são vértice e aresta, então a falha é só desligar o que sai.

**Como a falha é aplicada.** O núcleo (P0-GRAFO) desativa vértices e arestas sem apagar nada. Parada: desativa o vértice, e com ele saem todas as arestas que o tocam. Trecho (a, b): desativa a aresta de viagem a -> b, só nesse sentido; a caminhada continua. Linha: o G_P junta numa aresta só o trecho usado por várias linhas, então só saem os trechos que **nenhuma outra linha** usa. Para saber isso, `indexar_linhas` monta uma vez o mapa trecho -> linhas a partir dos padrões. A simulação desfaz a falha no fim, religando só o que ela desligou, então o mesmo G_P serve para a próxima.

**Componentes fortemente conexas (Tarjan).** Duas paradas estão na mesma componente se dá para ir de uma à outra **e voltar**. O Tarjan faz uma DFS e guarda, para cada vértice, a ordem de descoberta (`indice`) e o menor índice que a subárvore dele alcança com uma aresta de volta (`low`). Quando `low[v] == indice[v]`, v é a raiz de uma componente, e tudo que está acima dele na pilha é a componente. Exemplo: 0 -> 1 -> 2 -> 0 e 2 -> 3. A DFS desce 0, 1, 2, 3. O vértice 3 não tem saída, então `low[3] = indice[3]` e {3} sai sozinho. Em 2, a aresta 2 -> 0 dá `low[2] = 0`; a volta propaga `low = 0` até 0, que fecha {0, 1, 2}. **Por que iterativo:** a versão recursiva usa uma chamada por vértice do caminho da DFS, e no G_P real esse caminho passa do limite de recursão do Python (1.000). Aqui a pilha de chamadas é uma lista; o teste com um caminho de 50.000 vértices garante isso. O(V + E): cada vértice é descoberto uma vez e cada aresta é olhada uma vez.

**Paradas isoladas e desconectadas.** *Isolada* é a parada que, depois da falha, ficou sozinha na sua componente e não estava sozinha antes: não consegue mais ir a lugar nenhum e voltar. *Desconectada* é a que estava na maior componente (a rede principal) e saiu dela. Separei as duas porque "saiu da maior" fica ambíguo quando duas componentes empatam de tamanho.

**Perda de eficiência.** Eficiência global = média de 1/d(i, j) sobre os pares ordenados, com d em segundos; par sem caminho soma 0, então funciona com a rede partida. Perda = (antes - depois) / antes. Com amostra, as mesmas s origens sorteadas (semente fixa) valem antes e depois. O(s (V + E) log V): um Dijkstra por origem.

**Decisões.**
- **Mesmo denominador antes e depois** (n de antes da falha). Se renormalizasse pelo n de depois, remover uma parada mal conectada poderia *aumentar* a eficiência, porque os pares ruins dela sairiam da média. Com o mesmo n, os pares da parada removida contam 0 e a perda nunca é negativa. Alternativa descartada: n de depois.
- **Eficiência provisória dentro da F-RES.** A F-EFI ainda não publicou a dela. A daqui segue a definição de `docs/fontes/modelagem.md` §3.5 e sai quando a da F-EFI existir.
- **Trecho remove um sentido só**, porque interdição costuma ser de uma mão, e a volta é outro trecho.

**Limitações.** G_P usa o tempo mediano e não considera espera nem horário: a perda mede a rede estrutural, não o tempo porta a porta. A eficiência exata no G_P real custa um Dijkstra por parada (cerca de 9,7 mil); a interface usa amostra.

## Perguntas de verificação
1. **Por que o Tarjan é iterativo?** Porque a recursão vai tão fundo quanto o caminho da DFS, e no G_P real isso passa do limite de recursão do Python.
2. **Remover uma linha remove as paradas dela?** Não. Saem só os trechos de viagem que nenhuma outra linha usa; as paradas continuam, porque outras linhas e a caminhada as atendem.
3. **Qual a diferença entre parada isolada e desconectada?** Isolada ficou sozinha na componente (não vai e volta de nenhuma outra). Desconectada saiu da maior componente, mas pode estar num grupo pequeno com outras.
4. **Por que a eficiência depois da falha usa o n de antes?** Para que remover parada nunca aumente a eficiência: os pares da parada removida contam 0 em vez de sumir da média.
5. **Por que a simulação não estraga o G_P para a próxima consulta?** Ela só desativa, e no fim religa exatamente o que desligou, inclusive se der erro.

## Critérios de aceite
- [x] RF-RES-01: Simular a remoção de uma parada, de um trecho ou de uma linha
- [x] RF-RES-02: Calcular as componentes fortemente conexas antes e depois da falha e listar as paradas isoladas
- [x] RF-RES-03: Calcular a perda de eficiência causada pela falha

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [x] Código integrado pelos PRs #47 e #61; #61 aprovado pelo Henrique.
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
- [x] Página ou bloco na interface funcionando com o dataset real
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/`
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [x] Seção F-RES com captura da linha 832, perda e limitação da amostragem.
- [x] Roteiro do vídeo escrito no arquivo da feature
- [x] Arquivo atualizado com retomada, status, pendências e timeline.

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | feita em 10/11, junto com a etapa 2 (atraso) |
| 2 | Algoritmo com testes de corretude | feita em 10/11 |
| 3 | Integração com a visão do grafo e com os dados reais | feita em 10/11 (rede de teste e feed real) |
| 4 | Página na interface | feita em 19/11 (exceção ao congelamento) |
| 5 | Tempo medido na rede real e complexidade justificada | feita em 10/11 (ver Resultados) |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | |

## Resultados para o relatório
_Todo número vem com o comando que o gerou._

**Falhas no G_P real, 10/11/2026.** Comando: `python scripts/baixar_gtfs.py` e depois `python benchmarks/medir_falhas.py` (`AMOSTRA = 100`, `SEMENTE = 2026`, `REPETICOES = 3`). Feed: GTFS convencional da PBH baixado em 11/11/2026 00:02 UTC, SHA-256 `459f3a5892e57d10b11f9a74c543ac16c22661867c7d2296352ec17338935707` (diferente do de 05/11 da P0-DADOS: a PBH atualizou o arquivo). Serviço de 04/11/2026: 9.659 paradas, 303 linhas, 698 padrões. Máquina: notebook Intel Core i5-1235U, 15,7 GB, Windows 11, Python 3.14.4. Tempos com `medir`, n = 3; a leitura do GTFS e a construção do G_P não entram.

| Medida | Resultado | Tempo |
|---|---|---|
| G_P | V = 9.659, E = 122.732 | |
| Componentes fortemente conexas | 4: a maior com 9.656 paradas e 3 unitárias; iguais ao NetworkX | Tarjan: 148,6 ms ± 51,1 ms |
| Profundidade máxima da DFS | 4.657 níveis (limite de recursão do Python: 1.000) | |
| Eficiência global (100 origens) | 6,139 × 10⁻⁴ s⁻¹ | 10,5 s ± 3,1 s |
| Falha da parada `14784108` (mais saídas de viagem: 20) | componentes 4 -> 4; 0 isoladas; 0 desconectadas; perda de 0,0357 % | `simular_falha`: 25,5 s ± 7,3 s |
| Falha da linha `562003` (mais trechos exclusivos: 92) | componentes 4 -> 4; 0 isoladas; 0 desconectadas; perda de 0,0709 % | `simular_falha`: 18,4 s ± 1,0 s |

**Leitura.** A rede é muito redundante no G_P: tirar a parada com mais saídas ou a linha com mais trechos exclusivos não desconecta ninguém e custa menos de 0,1 % de eficiência. A causa provável são as arestas de caminhada de até 300 m, que contornam quase toda falha isolada. Isso ainda não foi medido; para medir, repetir sem caminhada. O tempo é dominado pelos Dijkstras da eficiência (2 × 100 por simulação). O Tarjan custa menos de 1 % disso. A variação chega a ± 30 % com n = 3; a hipótese é variação de frequência do processador do notebook, mas isso não foi verificado.

**Nova medição, 19/11/2026.** Mesmo comando, feed, máquina e parâmetros da de 10/11, já com a `eficiencia_global` da F-EFI e com a varredura de linhas acrescentada ao script.

| Medida | Resultado | Tempo |
|---|---|---|
| Componentes, profundidade da DFS | iguais a 10/11 (4 componentes; 4.657 níveis) | Tarjan: 224,1 ms ± 69,9 ms |
| Eficiência global (100 origens) | 6,139 × 10⁻⁴ s⁻¹, igual à provisória | 17,1 s ± 1,0 s |
| Falha da parada `14784108` | perda de 0,0357 %, igual | `simular_falha`: 30,9 s ± 4,1 s |
| Falha da linha `562003` | perda de 0,0709 %, igual | `simular_falha`: 38,0 s ± 4,5 s |
| Cada uma das 291 linhas com trecho, uma por vez (só Tarjan) | 17 tiram alguma parada da maior componente; as que mais tiram: 832 (33), 9030 (21) e 3302A (12) | |
| Falha da linha 832 (`562146`), 100 origens, semente 2026 | 0 isoladas; 33 fora da rede principal; perda de 0,9420 % (amostra de sorte: ver abaixo) | |

Os tempos subiram de 20 % a 110 % em relação a 10/11 com o mesmo código de Dijkstra; a variação entre execuções no notebook já era alta (± 30 %).

**Variação da amostra e valor exato da linha 832, 19/11/2026.** Comando: `python benchmarks/variancia_falhas.py --exata` (as execuções de 19/11 rodaram o mesmo código, chamando `construir_gp`, `indexar_linhas` e `simular_falha` direto; o script versiona essas chamadas). Mesmo feed e máquina.

| Origens | Perda por semente (2026, 1, 2, 3, 4) |
|---|---|
| 30 | 0,2230 % · 2,9855 % · 0,2809 % · 0,2863 % · 0,2511 % |
| 100 | 0,9420 % · 1,7565 % · 0,2594 % · 0,2551 % · 0,2371 % |
| 300 (sementes 1 e 2) | 0,7652 % · 0,7444 % |
| Todas (9.659), exata | **0,5040 %** (eficiência 6,208544 × 10⁻⁴ -> 6,177254 × 10⁻⁴ s⁻¹), em 1.330 s |

**Leitura.** A perda amostrada de uma falha que desconecta poucas paradas tem cauda pesada. Sem nenhuma das 33 paradas desconectadas na amostra, ela fica perto de 0,25 %; quando uma delas é sorteada como origem, a contribuição dela despenca e a estimativa salta para 1 % a 3 %. O valor de 0,94 % de 19/11 era uma dessas amostras. Por isso o relatório usa o exato, e a página avisa quando a falha desconecta paradas e a perda é amostrada.

## Roteiro do vídeo (2 a 2,5 min)
_Rascunho do agente em 10/11; o Caio revisa e ajusta à fala dele. Números só depois de conferidos em Resultados._

1. **O problema (20 s).** "Se a parada mais movimentada de BH fecha, ou uma linha para, quem fica sem ônibus? E quanto a rede inteira fica mais lenta?" Mostrar o mapa com a rede.
2. **Funcionando (50 s).** Na página Falhas, escolher a parada com mais saídas e simular. Mostrar o número de componentes antes e depois, as paradas isoladas no mapa e a perda de eficiência. Repetir com uma linha e comentar que só os trechos exclusivos dela saem, porque os trechos compartilhados continuam com as outras linhas. Se a página não existir na gravação, rodar `python benchmarks/medir_falhas.py` no terminal.
3. **Algoritmo e complexidade (50 s).** A falha não reconstrói o grafo: só desliga vértices e arestas e religa no fim. Componentes fortemente conexas com o Tarjan, O(V + E). Mostrar `indice` e `low` no exemplo de 4 vértices do "Como funciona". É iterativo porque, no G_P real, a DFS chega a 4.657 níveis e o Python para em 1.000. Eficiência: média de 1/d, um Dijkstra por origem, O(s (V + E) log V), por isso a amostra com semente fixa.
4. **Resultado e limitação (20 s).** Citar a perda medida para a parada e para a linha (Resultados). Limitação: o G_P usa o tempo mediano, sem espera nem horário, então a perda é estrutural, não o tempo porta a porta. A eficiência vem da função compartilhada com F-EFI.

## Pendências

- Gravar a demonstração da linha 832 usando o resultado exato e a estimativa identificados no relatório.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Caio.
### Núcleo 10/11/2026: checkpoint de 07/11 perdido, feature reduzida ao mínimo dos RFs. Tarjan iterativo, falhas de parada, trecho e linha e perda de eficiência (provisória) em `src/transporte/simulacao/falhas.py`, com 89 testes e medição no feed real. pytest com 603 verdes e hook verde. Branch `feat/F-RES-falhas`.
### Merge 12/11/2026: PR #47 integrado na `main` (`eb3c123`).
### Guia 16/11/2026: "Como funciona" e perguntas no `docs/GUIA.md` (§5.6 e §10). Página Falhas desbloqueada pela P0-UI (#45), mas sujeita à exceção ao congelamento.
### Revisão 17/11/2026: PR #53 rebaseado sobre a `main` com a F-BALD (#48 e #49); decisões no GUIA §8; pendências e DoD atualizados; prazo do vídeo corrigido para 18/11.
### Página 19/11/2026: página Falhas e troca pela eficiência da F-EFI na branch `feat/F-RES-pagina`; varredura das 291 linhas no feed real; conclusão do relatório (seção 9) escrita.
### Exata 19/11/2026: perda exata da linha 832 (0,504 %), variação da amostra medida (`benchmarks/variancia_falhas.py`), aviso na página, figura no relatório e PNG do diagrama regenerado.

### Fechamento documental de 20/11/2026
Confirmada a figura da linha 832 e seu uso na seção F-RES integrada pelo #61.
