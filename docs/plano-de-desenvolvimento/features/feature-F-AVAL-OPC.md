# F-AVAL-OPC · Benchmark contra NetworkX, complexidade empírica e página Desempenho

**Período:** Etapa opcional (16/11 a 18/11) · **Classe:** opcional
**Dono:** Rafael (@a-preencher) · **Issue:** #26 · **Visões do grafo:** todas
**Depende de:** todas as essenciais e desejáveis com DoD cumprido em 15/11 · **Bloqueia:** nada
**Prazo:** 18/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-DAD-05, RF-AVA-03, RF-AVA-04, RF-AVA-05). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** nenhuma (arquivo criado em 29/10).
- **Onde parou:** não iniciado.
- **Próximo passo:** aguardar todas as essenciais e desejáveis com DoD cumprido em 15/11. Não iniciar antes disso; quando liberar, publicar as assinaturas (etapa 1 do plano de implementação).
- **Arquivos tocados:** nenhum.
- **Como testar:** ainda não há testes.
- **Bloqueios:** depende de todas as essenciais e desejáveis com DoD cumprido em 15/11.

## Objetivo
Benchmark contra NetworkX, complexidade empírica e página Desempenho. Fecha:

- **RF-DAD-05** (O): Gerar redes sintéticas de tamanho crescente para o estudo de escala
- **RF-AVA-03** (O): Comparar o tempo dos nossos algoritmos com os equivalentes do NetworkX no mesmo grafo
- **RF-AVA-04** (O): Gerar os gráficos de complexidade empírica (tempo × tamanho, log-log)
- **RF-AVA-05** (O): Página "Desempenho" na interface

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
Só em `benchmarks/` e `tests/`, sem tocar `src/` (código congelado). Ver `docs/fontes/modelagem.md` §3.7, etapa opcional.

## Como funciona e por quê
_A escrever a cada etapa concluída do plano de implementação, para um colega que não viu o código: o problema, a visão do grafo e por que ela, o algoritmo passo a passo com um exemplo pequeno, a complexidade com a justificativa, as decisões com as alternativas descartadas e as limitações._

## Perguntas de verificação
_3 a 5 perguntas que qualquer integrante deve saber responder, cada uma com a resposta curta._

## Critérios de aceite
- [ ] RF-DAD-05: Gerar redes sintéticas de tamanho crescente para o estudo de escala
- [ ] RF-AVA-03: Comparar o tempo dos nossos algoritmos com os equivalentes do NetworkX no mesmo grafo
- [ ] RF-AVA-04: Gerar os gráficos de complexidade empírica (tempo × tamanho, log-log)
- [ ] RF-AVA-05: Página "Desempenho" na interface

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
### Dono 29/10/2026: feature atribuída a Rafael.
