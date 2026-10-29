# F-MET · Centralidades

**Período:** 1 · Essenciais (04/11 a 11/11) · **Classe:** prioritária
**Dono:** Thiago (@a-preencher) · **Issue:** a criar · **Visões do grafo:** G_P
**Depende de:** G_P de P0-MODELO · **Bloqueia:** F-MET-2
**Prazo:** 11/11 (checkpoint 07/11)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-MET-01, RF-MET-02, RF-MET-03). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** nenhuma (arquivo criado em 29/10).
- **Onde parou:** não iniciado.
- **Próximo passo:** calcular os graus de entrada e saída sobre G_P da rede de teste, com testes; depois, Brandes.
- **Arquivos tocados:** nenhum.
- **Como testar:** ainda não há testes.
- **Bloqueios:** depende de G_P de P0-MODELO; até lá, trabalhar contra as assinaturas publicadas e a rede de teste.

## Objetivo
Centralidades. Fecha:

- **RF-MET-01** (E): Calcular o grau de entrada e de saída de cada parada e a distribuição de graus
- **RF-MET-02** (E): Calcular a intermediação (Brandes) de cada parada
- **RF-MET-03** (E): Mostrar o ranking das paradas mais centrais e um mapa de calor

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
Assinaturas públicas: a definir na etapa 1 do plano de implementação e publicadas com `estado: planejado` antes de qualquer consumidor depender delas.

Algoritmos previstos (docs/fontes/modelagem.md §3.5):
- Brandes (intermediação) · visão G_P · O(V (V + E) log V) · Ponderado; O(VE) sem pesos

## Como funciona e por quê
_A escrever a cada etapa concluída do plano de implementação, para um colega que não viu o código: o problema, a visão do grafo e por que ela, o algoritmo passo a passo com um exemplo pequeno, a complexidade com a justificativa, as decisões com as alternativas descartadas e as limitações._

## Perguntas de verificação
_3 a 5 perguntas que qualquer integrante deve saber responder, cada uma com a resposta curta._

## Critérios de aceite
- [ ] RF-MET-01: Calcular o grau de entrada e de saída de cada parada e a distribuição de graus
- [ ] RF-MET-02: Calcular a intermediação (Brandes) de cada parada
- [ ] RF-MET-03: Mostrar o ranking das paradas mais centrais e um mapa de calor

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
### Dono 29/10/2026: feature atribuída a Thiago.
