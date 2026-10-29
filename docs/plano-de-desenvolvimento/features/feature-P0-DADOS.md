# P0-DADOS · Leitura do GTFS, modelo normalizado e rede de teste

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Miguel (@a-preencher) · **Issue:** #3 · **Visões do grafo:** não se aplica (modelo normalizado)
**Depende de:** nada · **Bloqueia:** P0-MODELO, P0-UI, F-ESPERA, F-BALD
**Prazo:** contrato 30/10; rede de teste 31/10; feed real 03/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-DAD-01, RF-DAD-02, RF-DAD-03, RF-DAD-04). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** nenhuma (arquivo criado em 29/10).
- **Onde parou:** não iniciado.
- **Próximo passo:** publicar `src/transporte/dados/modelo.py` com as dataclasses e `estado: planejado`, e conferir a disponibilidade do GTFS da BHTrans no portal de dados abertos da PBH.
- **Arquivos tocados:** nenhum.
- **Como testar:** ainda não há testes.
- **Bloqueios:** nenhum.

## Objetivo
Leitura do GTFS, modelo normalizado e rede de teste. Fecha:

- **RF-DAD-01** (E): Ler um feed GTFS (paradas, linhas, viagens, horários, calendário) e convertê-lo no modelo normalizado
- **RF-DAD-02** (E): Validar o feed e relatar inconsistências (parada sem coordenada, horário inválido, viagem sem paradas)
- **RF-DAD-03** (E): Recortar a rede por região (retângulo de coordenadas) ou por conjunto de linhas
- **RF-DAD-04** (E): Fornecer uma rede de teste pequena, em formato GTFS, com respostas conhecidas

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
Contrato inicial em `docs/fontes/plano-de-projeto.md` §9. Publicar as assinaturas com o comentário `estado: planejado` antes de implementar; trocar para `implementado` quando os testes passarem. Feed bruto em `dados/brutos/` (fora do Git, baixado por script); rede de teste em `dados/rede-teste/`.

## Como funciona e por quê
_A escrever a cada etapa concluída do plano de implementação, para um colega que não viu o código: o problema, a visão do grafo e por que ela, o algoritmo passo a passo com um exemplo pequeno, a complexidade com a justificativa, as decisões com as alternativas descartadas e as limitações._

## Perguntas de verificação
_3 a 5 perguntas que qualquer integrante deve saber responder, cada uma com a resposta curta._

## Critérios de aceite
- [ ] RF-DAD-01: Ler um feed GTFS (paradas, linhas, viagens, horários, calendário) e convertê-lo no modelo normalizado
- [ ] RF-DAD-02: Validar o feed e relatar inconsistências (parada sem coordenada, horário inválido, viagem sem paradas)
- [ ] RF-DAD-03: Recortar a rede por região (retângulo de coordenadas) ou por conjunto de linhas
- [ ] RF-DAD-04: Fornecer uma rede de teste pequena, em formato GTFS, com respostas conhecidas

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
### Dono 29/10/2026: feature atribuída a Miguel.
