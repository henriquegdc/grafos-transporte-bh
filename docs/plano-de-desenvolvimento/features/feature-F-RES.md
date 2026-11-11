# F-RES · Falhas e resiliência

**Período:** 1 · Essenciais (04/11 a 11/11) · **Classe:** prioritária
**Dono:** Caio (@CaioSResende) · **Issue:** #12 · **Visões do grafo:** G_P
**Depende de:** P0-GRAFO; eficiência de F-EFI · **Bloqueia:** F-RES-2
**Prazo:** 11/11 (checkpoint 07/11)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-RES-01, RF-RES-02, RF-RES-03). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 10/11/2026.
- **Onde parou:** etapas 1, 2, 3 e 5 feitas na branch `feat/F-RES-falhas`. `src/transporte/simulacao/falhas.py` (`estado: implementado`) tem o Tarjan iterativo, a eficiência global provisória, a falha de parada, trecho e linha, e `simular_falha`, que compara antes e depois e desfaz a falha. São 89 testes em `tests/simulacao/test_falhas.py`, com gabarito à mão, NetworkX e a rede de teste. Também há tempo medido no feed real (`benchmarks/medir_falhas.py`). O checkpoint de 07/11 não foi cumprido; a feature foi reduzida ao mínimo dos RFs (gatilho §7.3).
- **Próximo passo:** commitar, abrir o PR com `Closes #12` e pedir revisão. Combinar com o Arthur a troca da `eficiencia_global` provisória pela da F-EFI. Quando a P0-UI entrar, fazer a página Falhas (etapa 4). Depois, a etapa 6: revisar o rascunho de "Como funciona", diagrama UML, seção do relatório e roteiro do vídeo.
- **Arquivos tocados:** `src/transporte/simulacao/falhas.py`, `tests/simulacao/test_falhas.py`, `benchmarks/medir_falhas.py`, este arquivo.
- **Como testar:** `pytest tests/simulacao` (89 testes); `pytest` completo (603 em 10/11); `python benchmarks/medir_falhas.py` com o feed em `dados/brutos/bhtrans.zip` (baixar com `python scripts/baixar_gtfs.py`).
- **Bloqueios:** a página depende da P0-UI (Arthur, branch `feature/P0-UI` ainda sem PR na `main`); a eficiência oficial depende da F-EFI (Arthur, não iniciada).

## Objetivo
Falhas e resiliência. Fecha:

- **RF-RES-01** (E): Simular a remoção de uma parada, de um trecho ou de uma linha
- **RF-RES-02** (E): Calcular as componentes fortemente conexas antes e depois da falha e listar as paradas isoladas
- **RF-RES-03** (E): Calcular a perda de eficiência causada pela falha

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 10/11: Tarjan iterativo, falhas de parada, trecho e linha, `simular_falha`; eficiência provisória até a F-EFI |
| Modelo e dados | concluído | 10/11: roda sobre `construir_gp` e `ler`; `indexar_linhas` liga trechos a linhas; integração testada na rede de teste e medida no feed real |
| Interface | não iniciado | Depende da P0-UI (`app.py` e contrato de página) |
| Testes | concluído | 10/11: 89 testes (gabarito à mão, 40 grafos aleatórios contra o NetworkX no Tarjan, 15 na eficiência, rede de teste ponta a ponta) |
| Desempenho (tempo medido) | não iniciado | |
| Guia (explicação e quiz) | não iniciado | |
| Relatório | não iniciado | |
| Vídeo | não iniciado | |

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
| 1 | Contrato (assinaturas com estado "planejado") | feita em 10/11, junto com a etapa 2 (atraso) |
| 2 | Algoritmo com testes de corretude | feita em 10/11 |
| 3 | Integração com a visão do grafo e com os dados reais | feita em 10/11 (rede de teste e feed real) |
| 4 | Página na interface | bloqueada pela P0-UI |
| 5 | Tempo medido na rede real e complexidade justificada | feita em 10/11 (ver Resultados) |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | |

## Resultados para o relatório
_Vazio até haver execução real. Todo número vem com o comando que o gerou._

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

## Pendências
- **Checkpoint de 07/11 perdido.** Nada da F-RES existia em 07/11. Pelo gatilho do plano-de-projeto §7.3, a feature foi reduzida ao mínimo dos RFs: núcleo, testes e medição em 10/11. A página e a etapa 6 ficam como pendência.
- **Eficiência da F-EFI (Arthur):** `eficiencia_global` aqui é provisória. Quando a F-EFI publicar a dela, trocar e apagar esta. Combinar com o Arthur que a dela aceite `origens` e `n_referencia`, ou equivalente, porque a perda depende do mesmo denominador.
- **Página Falhas:** depende do `app.py` e do contrato de página da P0-UI.
- **Decisões a confirmar pelo Caio:** o denominador fixo na eficiência, as definições de isolada e desconectada e o trecho com um sentido só (ver Como funciona). Registrar no `docs/GUIA.md` §8 depois de confirmadas.
- **Etapa 6:** diagrama UML de sequência, seção `relatorio/secoes/F-RES.tex`, roteiro do vídeo e incorporação ao GUIA §5.6.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Caio.
### Núcleo 10/11/2026: checkpoint de 07/11 perdido, feature reduzida ao mínimo dos RFs. Tarjan iterativo, falhas de parada, trecho e linha e perda de eficiência (provisória) em `src/transporte/simulacao/falhas.py`, com 89 testes e medição no feed real. pytest com 603 verdes e hook verde. Branch `feat/F-RES-falhas`.
