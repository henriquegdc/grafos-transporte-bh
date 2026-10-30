# P0-MODELO · Modelagem, UML e construtores de G_P e G_E

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Henrique (@henriquegdc) · **Issue:** #4 · **Visões do grafo:** G_P, G_E
**Depende de:** contratos de P0-GRAFO e P0-DADOS · **Bloqueia:** F-ROTA, F-ESPERA, F-MET, F-EFI, F-RES
**Prazo:** assinaturas 31/10; G_P 02/11; G_E 03/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-GRF-04, RF-GRF-05, RF-GRF-07). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 29/10, Henrique, branch `feat/P0-MODELO` (um PR só, no fim da feature).
- **Onde parou:** diagramas UML globais e contrato dos construtores prontos; decisões D1 a D7 registradas; PR #33 aberto para a `main`, aguardando 1 aprovação.
- **Próximo passo:** conseguir 1 aprovação no PR #33; combinar com o Miguel o contrato da `Rede` (pendência abaixo) e, com ele, a rede de teste com G_P e G_E esperados calculados à mão; depois, implementar `construir_gp` com testes (G_P até 02/11).
- **Arquivos tocados:** `docs/diagramas/*`, `src/transporte/modelo/{parametros,visoes,construtores}.py`.
- **Como testar:** `PYTHONPATH=src python -c "import transporte.modelo.construtores"` importa sem erro; diagramas: `java -jar plantuml-1.2026.9.jar -charset UTF-8 -tpng -failfast2 docs/diagramas/*.puml`. Ainda não há pytest (as funções são só contrato).
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
| Modelo e dados | em andamento | 29/10: diagramas UML globais prontos; assinaturas dos construtores com `estado: planejado`; implementação depende da rede de teste (31/10) e do núcleo (01/11) |
| Interface | não iniciado | |
| Testes | não iniciado | |
| Desempenho (tempo medido) | não iniciado | |
| Guia (explicação e quiz) | não iniciado | |
| Relatório | não iniciado | |
| Vídeo | não iniciado | |

## Especificação
Construtores de G_P e G_E a partir do modelo normalizado (`docs/fontes/modelagem.md` §3.4). Contrato publicado com `estado: planejado`; o diagrama de classes (`docs/diagramas/classes.png`) mostra as mesmas assinaturas.

| Arquivo | Conteúdo público |
|---|---|
| `src/transporte/modelo/parametros.py` | `FaixaHoraria(nome, inicio_s, fim_s)`, `Parametros(raio_caminhada_m=300, velocidade_caminhada_ms=1.2, espera_padrao_s=300, faixas)` |
| `src/transporte/modelo/visoes.py` | `Visao(grafo, nome)`, `VisaoGP`, `VisaoGE` (com `baldeacoes`), constantes de tipo de aresta `VIAGEM`, `CAMINHADA`, `EMBARQUE`, `DESEMBARQUE` |
| `src/transporte/modelo/construtores.py` | `construir_gp(rede, params)`, `construir_ge(rede, faixa, params, intervalos)`, `salvar(visao, caminho)`, `carregar(caminho)` |

Complexidade (V paradas, L plataformas, N horários, K pares a até o raio): `construir_gp` em O(V² + N log N); `construir_ge` em O(V² + L + N log N); o V² cai para O(V + K) com grade espacial.

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
- ~~**Decisões de modelagem embutidas no diagrama**~~ **decidido em 29/10/2026:** mantidas e registradas no `docs/GUIA.md` §8. Texto original: hierarquia `Visao` com uma subclasse por visão; `construir_ge` recebe a tabela de intervalos de F-ESPERA (espera constante até 06/11); salvar e carregar ficam nos construtores (RF-GRF-07).
- **Contrato da Rede (Miguel):** `partidas[(padrão, parada)] -> list[int]` perde a identidade da viagem. Para calcular o tempo entre paradas consecutivas (D2) é preciso saber qual horário da parada seguinte pertence à mesma viagem. Pedir ao Miguel que a Rede guarde as viagens (por exemplo `viagens[padrão] -> list[list[int]]`, uma lista de horários por viagem, na ordem das paradas) ou garanta o mesmo número e a mesma ordem de horários em todas as paradas do padrão.

### ~~Decisões a tomar~~ Decididas em 29/10/2026: todas pela recomendação; registradas no `docs/GUIA.md` §8 e no `docs/fontes/modelagem.md` §3.4

- **D1. O que é um padrão.** (a) linha + sentido (`direction_id`); (b) linha + sequência exata de paradas. **Recomendo (b):** o G_E encadeia plataformas numa sequência fixa, e variantes de itinerário da mesma linha (trajeto encurtado, desvio) quebrariam esse encadeamento em (a). Efeito colateral: cada variante tem menos partidas que a linha inteira, então a espera por padrão pode sair maior que a real para quem aceita qualquer variante; registrar como limitação.
- **D2. Tempo de viagem entre paradas consecutivas.** (a) mediana das diferenças entre as viagens do padrão no dia típico; (b) média; (c) mediana por faixa horária. **Recomendo (a):** robusta a horários com erro de cadastro e simples; variação do tempo de viagem ao longo do dia vira limitação. Depende do contrato da Rede acima.
- **D3. Mesma parada física com dois `stop_id` (um por sentido).** (a) manter separadas, ligadas por caminhada; (b) fundir por `parent_station` ou proximidade. **Recomendo (a):** fiel ao GTFS e a caminhada (raio de 300 m) já liga as duas; fundir altera os dados do Miguel e esconde a travessia da rua. Efeito: a centralidade de um ponto fica dividida entre dois vértices; F-MET pode somar por `parent_station` só na exibição.
- **D4. Dia típico.** (a) uma data fixa (uma quarta-feira dentro da vigência do feed), com os `service_id` ativos nela segundo `calendar.txt` e `calendar_dates.txt`; (b) "dia útil genérico", isto é, serviços com segunda a sexta = 1. **Recomendo (a):** trata as exceções do `calendar_dates.txt` e é reprodutível. É o parâmetro `dia` de `leitor_gtfs.ler` (Miguel).
- **D5. Faixas horárias.** Proposta: pico da manhã 06h a 09h, entrepico 09h a 16h, pico da tarde 16h a 19h, noite 19h a 24h; madrugada (0h a 6h) fora. **Recomendo aceitar:** na madrugada há poucas partidas e intervalos muito longos, que distorceriam as médias.
- **D6. Espera provisória.** Até a tabela de intervalos de F-ESPERA (06/11), todo embarque usa `espera_padrao_s = 300` (5 min). Alternativa: estimar H/2 dentro do construtor, o que duplicaria o trabalho de F-ESPERA. **Recomendo os 300 s provisórios.** Padrão sem partida na faixa não recebe aresta de embarque.
- **D7. Formato de salvar e carregar.** (a) pickle; (b) JSON. **Recomendo (a):** uma linha de código e rápido; o arquivo é cache local gerado pela própria ferramenta, fora do Git (`dados/cache/`), e nunca é lido de fonte externa, que é o único caso em que pickle é inseguro.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Henrique.
### Mudança 29/10/2026: revisão do REQUISITOS.md dispensada (baseline v1.0 em 29/10); próximo passo passa a ser UML e assinaturas.
### Sessão 29/10/2026: rascunho dos diagramas UML globais (classes, componentes, casos de uso) em PlantUML, na branch `feat/P0-MODELO-uml`.
### Sessão 29/10/2026: assinaturas de parametros.py, visoes.py e construtores.py com estado: planejado; diagrama de classes sincronizado; decisões D1 a D7 propostas com recomendação.
### Decisão 29/10/2026: D1 a D7 aceitas pela recomendação; `dados/cache/` no .gitignore.
### PR 29/10/2026: #33 aberto (UML global, contrato dos construtores e decisões D1 a D7).
