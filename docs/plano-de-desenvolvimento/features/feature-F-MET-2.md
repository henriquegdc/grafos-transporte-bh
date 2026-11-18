# F-MET-2 · Proximidade e intermediação amostrada

**Período:** 2 · Desejáveis (12/11 a 15/11) · **Classe:** desejável
**Dono:** Thiago (@Thiagocs8) · **Issue:** #16 · **Visões do grafo:** G_P
**Depende de:** F-MET · **Bloqueia:** nada
**Prazo:** 15/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-MET-04, RF-MET-05). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 16/11, Thiago (decisão de escopo; nenhum código desta feature).
- **Onde parou:** **cortada pelo congelamento de 15/11** (plano-de-projeto §7.1: depois do congelamento, só correção). O RF-MET-05 (intermediação por amostragem e erro contra a exata) foi atendido dentro da F-MET, porque o RNF-06 exige amostragem nas métricas de todos os pares: `estimar_intermediacao` em `src/transporte/algoritmos/centralidade.py` e a comparação com a exata em `benchmarks/medir_centralidade.py` (resultados no arquivo da F-MET). O RF-MET-04 (proximidade) não foi feito.
- **Próximo passo:** nenhum neste ciclo. Se o grupo reabrir o escopo, a proximidade reaproveita o Dijkstra por origem do Brandes (mesma amostragem de origens).
- **Arquivos tocados:** nenhum além deste arquivo.
- **Como testar:** os testes da amostragem estão em `tests/algoritmos/test_centralidade.py` (F-MET).
- **Bloqueios:** congelamento do código em 15/11.

## Objetivo
Proximidade e intermediação amostrada. Fecha:

- **RF-MET-04** (D): Calcular a proximidade (closeness) de cada parada
- **RF-MET-05** (D): Calcular a intermediação por amostragem e medir o erro contra a exata

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | cortado | 16/11: congelamento; RF-MET-05 atendido pela F-MET (`estimar_intermediacao`), RF-MET-04 não feito |
| Modelo e dados | não aplicável | feature cortada pelo congelamento (16/11) |
| Interface | não aplicável | feature cortada pelo congelamento (16/11) |
| Testes | não aplicável | feature cortada pelo congelamento (16/11) |
| Desempenho (tempo medido) | não aplicável | feature cortada pelo congelamento (16/11) |
| Guia (explicação e quiz) | não aplicável | feature cortada pelo congelamento (16/11) |
| Relatório | não aplicável | feature cortada pelo congelamento (16/11) |
| Vídeo | não aplicável | feature cortada pelo congelamento (16/11) |

## Especificação
Assinaturas públicas: a definir na etapa 1 do plano de implementação e publicadas com `estado: planejado` antes de qualquer consumidor depender delas.

Algoritmos previstos (docs/fontes/modelagem.md §3.5):
- Proximidade (closeness) · visão G_P · O(V (V + E) log V) · Uma execução de Dijkstra por vértice
- Intermediação amostrada · visão G_P · O(s (V + E) log V) · s fontes; erro medido contra a exata

## Como funciona e por quê
_A escrever a cada etapa concluída do plano de implementação, para um colega que não viu o código: o problema, a visão do grafo e por que ela, o algoritmo passo a passo com um exemplo pequeno, a complexidade com a justificativa, as decisões com as alternativas descartadas e as limitações._

## Perguntas de verificação
_3 a 5 perguntas que qualquer integrante deve saber responder, cada uma com a resposta curta._

## Critérios de aceite
- [ ] RF-MET-04: Calcular a proximidade (closeness) de cada parada (não feito: cortado pelo congelamento)
- [x] RF-MET-05: Calcular a intermediação por amostragem e medir o erro contra a exata (atendido pela F-MET: `estimar_intermediacao` e `benchmarks/medir_centralidade.py --exato`; resultados no arquivo da F-MET)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

**Não aplicável: feature cortada pelo congelamento de 15/11** (ver Retomada); os itens abaixo ficam em aberto de propósito.

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
### Corte 16/11/2026: feature cortada pelo congelamento de 15/11; RF-MET-05 entregue pela F-MET (amostragem com erro, RNF-06); RF-MET-04 (proximidade) não feito.
