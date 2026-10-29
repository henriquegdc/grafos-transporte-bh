# P0-MODELO · Modelagem, UML e construtores de G_P e G_E

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Henrique (@henriquegdc) · **Issue:** #4 · **Visões do grafo:** G_P, G_E
**Depende de:** contratos de P0-GRAFO e P0-DADOS · **Bloqueia:** F-ROTA, F-ESPERA, F-MET, F-EFI, F-RES
**Prazo:** assinaturas 31/10; G_P 02/11; G_E 03/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-GRF-04, RF-GRF-05, RF-GRF-07). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 29/10, Henrique, branch `feat/P0-MODELO-uml`.
- **Onde parou:** três diagramas globais escritos e renderizados em PNG (classes, componentes e casos de uso), aguardando a revisão do Henrique; nada commitado ainda.
- **Próximo passo:** revisar os diagramas (pendências abaixo), commitar e abrir o PR; depois, escrever as assinaturas dos construtores em `src/transporte/modelo/` com `estado: planejado`, seguindo o diagrama de classes (prazo 31/10).
- **Arquivos tocados:** `docs/diagramas/{classes,componentes,casos-de-uso}.puml` e os `.png` gerados.
- **Como testar:** `java -jar plantuml-1.2026.9.jar -charset UTF-8 -tpng -failfast2 docs/diagramas/*.puml` gera as três imagens sem erro (layout smetana, dispensa Graphviz).
- **Bloqueios:** depende de contratos de P0-GRAFO e P0-DADOS; até lá, trabalhar contra as assinaturas publicadas e a rede de teste.

## Objetivo
Modelagem, UML e construtores de G_P e G_E. Fecha:

- **RF-GRF-04** (E): Construir a visão G_P (paradas) a partir do modelo normalizado
- **RF-GRF-05** (E): Construir a visão G_E (parada × linha) com arestas de embarque, viagem, desembarque e caminhada
- **RF-GRF-07** (D): Salvar e carregar grafos construídos, para não reprocessar o GTFS a cada execução

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | não iniciado | |
| Modelo e dados | em andamento | 29/10: diagramas UML globais em rascunho (`docs/diagramas/`); construtores não iniciados |
| Interface | não iniciado | |
| Testes | não iniciado | |
| Desempenho (tempo medido) | não iniciado | |
| Guia (explicação e quiz) | não iniciado | |
| Relatório | não iniciado | |
| Vídeo | não iniciado | |

## Especificação
Construtores de G_P e G_E a partir do modelo normalizado (`docs/fontes/modelagem.md` §3.4). Assinaturas públicas: a definir na etapa 1 do plano de implementação e publicadas com `estado: planejado` antes de qualquer consumidor depender delas.

## Como funciona e por quê
_A escrever a cada etapa concluída do plano de implementação, para um colega que não viu o código: o problema, a visão do grafo e por que ela, o algoritmo passo a passo com um exemplo pequeno, a complexidade com a justificativa, as decisões com as alternativas descartadas e as limitações._

## Perguntas de verificação
_3 a 5 perguntas que qualquer integrante deve saber responder, cada uma com a resposta curta._

## Critérios de aceite
- [ ] RF-GRF-04: Construir a visão G_P (paradas) a partir do modelo normalizado
- [ ] RF-GRF-05: Construir a visão G_E (parada × linha) com arestas de embarque, viagem, desembarque e caminhada
- [ ] RF-GRF-07: Salvar e carregar grafos construídos, para não reprocessar o GTFS a cada execução

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
- **Campos propostos no diagrama de classes que pertencem a contratos de outros donos:** `Linha(id, nome, tipo)` e `leitor_gtfs.ler/validar` (Miguel, P0-DADOS); `Resultado(dist, pred)` (Thiago, P0-GRAFO). Confirmar com eles quando publicarem os contratos em 30/10 e ajustar o diagrama.
- **Decisões de modelagem embutidas no diagrama, a registrar no `docs/GUIA.md` §8 se mantidas:** hierarquia `Visao` com uma subclasse por visão; `construir_ge` recebe a tabela de intervalos de F-ESPERA (espera constante até 06/11); salvar e carregar ficam nos construtores (RF-GRF-07).

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Henrique.
### Mudança 29/10/2026: revisão do REQUISITOS.md dispensada (baseline v1.0 em 29/10); próximo passo passa a ser UML e assinaturas.
### Sessão 29/10/2026: rascunho dos diagramas UML globais (classes, componentes, casos de uso) em PlantUML, na branch `feat/P0-MODELO-uml`.
