# P0-REPO · Repositório, hook, README de instalação e Kanban

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Caio (@a-preencher) · **Issue:** a criar · **Visões do grafo:** não se aplica
**Depende de:** nada · **Bloqueia:** todas (hook e proteção da `main`)
**Prazo:** 30/10

> Fonte de verdade: docs/fontes/REQUISITOS.md (RNF-01, RNF-02, RNF-07, RNF-09). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** nenhuma (arquivo criado em 29/10).
- **Onde parou:** não iniciado.
- **Próximo passo:** escrever `scripts/verificar_imports.py` (lê os imports de `src/` com o módulo `ast` e falha se aparecer networkx, igraph, graph_tool, rustworkx, scipy.sparse.csgraph ou osmnx) e `.githooks/pre-commit` chamando o script e `ruff check`.
- **Arquivos tocados:** nenhum.
- **Como testar:** ainda não há testes.
- **Bloqueios:** nenhum.

## Objetivo
Repositório, hook, README de instalação e Kanban. Fecha:

- **RNF-01** (E): Nenhum módulo em `src/` importa biblioteca de grafo (networkx, igraph, graph_tool, rustworkx, scipy.sparse.csgraph, osmnx)
- **RNF-02** (E): A `main` só recebe PR revisado e aprovado por outro integrante, com hook e pytest verdes
- **RNF-07** (E): Reprodutibilidade: versões fixadas, dataset com data e origem registradas, script de download, sementes fixas
- **RNF-09** (E): Toda feature tem "Como funciona e por quê" e perguntas de verificação incorporadas ao `docs/GUIA.md`

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | não iniciado | |
| Modelo e dados | não iniciado | |
| Interface | não iniciado | |
| Testes | não iniciado | |
| Desempenho (tempo medido) | não iniciado | |
| Guia (explicação e quiz) | não iniciado | |
| Relatório | não iniciado | |
| Vídeo | não iniciado | |

## Especificação
Hook em `.githooks/pre-commit`, ativado com `git config core.hooksPath .githooks`. `requirements.txt` com versões fixadas (Python 3.12, streamlit, streamlit-folium, folium, pandas, pytest, ruff; networkx só para `tests/` e `benchmarks/`). Proteção da `main` com 1 aprovação. README de instalação (`docs/fontes/plano-de-projeto.md` §14.2, item 5).

## Como funciona e por quê
_A escrever a cada etapa concluída do plano de implementação, para um colega que não viu o código: o problema, a visão do grafo e por que ela, o algoritmo passo a passo com um exemplo pequeno, a complexidade com a justificativa, as decisões com as alternativas descartadas e as limitações._

## Perguntas de verificação
_3 a 5 perguntas que qualquer integrante deve saber responder, cada uma com a resposta curta._

## Critérios de aceite
- [ ] RNF-01: Nenhum módulo em `src/` importa biblioteca de grafo (networkx, igraph, graph_tool, rustworkx, scipy.sparse.csgraph, osmnx)
- [ ] RNF-02: A `main` só recebe PR revisado e aprovado por outro integrante, com hook e pytest verdes
- [ ] RNF-07: Reprodutibilidade: versões fixadas, dataset com data e origem registradas, script de download, sementes fixas
- [ ] RNF-09: Toda feature tem "Como funciona e por quê" e perguntas de verificação incorporadas ao `docs/GUIA.md`

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
| 1 | Contrato (assinaturas com estado "planejado") | |
| 2 | Algoritmo com testes de corretude | |
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
- Nenhuma.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Caio.
