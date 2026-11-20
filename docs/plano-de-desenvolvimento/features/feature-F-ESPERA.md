# F-ESPERA · Espera e simulação de trajeto

**Período:** 1 · Essenciais (04/11 a 11/11) · **Classe:** prioritária
**Dono:** Miguel (@Miguelgdn1) · **Issue:** #8 · **Visões do grafo:** G_E
**Depende de:** P0-DADOS, P0-MODELO · **Bloqueia:** F-ESPERA-2; tabela de esperas para P0-MODELO/F-ROTA (marco original 06/11; disponível localmente em 11/11)
**Prazo:** 11/11 (checkpoint 07/11)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-ESP-01, RF-ESP-02, RF-ESP-03). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada

**Entrega técnica e documental concluída.** O [#51](https://github.com/henriquegdc/grafos-transporte-bh/pull/51) recebeu aprovação do Thiago e entrou na main em `cbb1f90`. A regra H/2 e as parcelas foram conferidas com o código, os testes, o guia §5.2 e o resultado de `benchmarks/resultados/espera-2026-11-11.json`. Para reproduzir: `python -m pytest tests/simulacao/test_espera.py tests/interface/test_pagina_espera.py`. Próximo passo pessoal: gravar o modo por faixa.

## Objetivo
Espera e simulação de trajeto. Fecha:

- **RF-ESP-01** (E): Estimar o intervalo entre partidas de cada linha por faixa horária, a partir dos horários ou do `frequencies.txt`
- **RF-ESP-02** (E): Calcular a espera esperada de cada embarque e aplicá-la às arestas de embarque de G_E
- **RF-ESP-03** (E): Simular um trajeto para um horário de saída, decompondo o tempo total em caminhada, espera e viagem

## Status

| Camada | Status | Observação |
|---|---|---|
| Núcleo (algoritmo) | concluído | Intervalos, H/2 e simulação reutilizando F-ROTA |
| Modelo e dados | concluído | Frequências já expandidas; contrato `esperas` de P0-MODELO |
| Interface | concluído | Página render(rede), tabela e decomposição; feed completo validado sem exceção com AppTest |
| Testes | concluído | Gabaritos, bordas, AppTest e entrada normal sem PYTHONPATH; suíte final registrada no fechamento |
| Desempenho (tempo medido) | concluído | JSON e comando em Resultados |
| Guia (explicação e quiz) | concluído | Guia §5.2 e §10 conferidos com as regras de embarque e de estimativa por faixa. |
| Relatório | concluído | Seção com fluxograma, medição identificada e limitação de H/2. |
| Vídeo | roteiro concluído | Gravação pelo integrante no vídeo do grupo. |

## Especificação

Contrato em `src/transporte/simulacao/espera.py`, publicado nesta sessão com `estado: planejado` antes dos consumidores e atualizado para `implementado` após os testes:

- `estimar_intervalos(rede: Rede, params: Parametros | None = None) -> dict[tuple[str, str], float]`: H em segundos por `(padrão, faixa)`.
- `calcular_esperas(intervalos: Mapping[tuple[str, str], float]) -> dict[tuple[str, str], float]`: H/2; recusa negativo, NaN e infinito; zero é válido.
- `simular_trajeto(rede: Rede, origem: str, destino: str, saida_s: int, params: Parametros | None = None) -> Trajeto | None`: faixa fixa pela saída, esperas aplicadas sem transformação pelo construtor.
- `interface/paginas/espera.py`: `TITULO` e `render(rede)` conforme P0-UI. Mantém o resultado em reruns e não exibe resultado de outro dataset.

Uso pelos consumidores de G_E (mesmos `params` na estimativa e no construtor):

```python
esperas = calcular_esperas(estimar_intervalos(rede, params))
ge = construir_ge(rede, faixa, params=params, esperas=esperas)
```

A tabela contém segundos de espera, sem nova divisão por dois. Esse contrato alimenta a simulação e a página Eficiência. A página Trajetos usa a mesma tabela no PR #57.

Decisões de implementação E1–E4 aprovadas no plano por Miguel: partidas distintas por padrão e primeiro horário (D10); com menos de duas partidas, estimativa ausente e fallback do construtor; faixa fixa sem módulo de 24h; reutilizar F-ROTA e mapa do #45. Não alteram as fontes. Opcionais e Monte Carlo ficam fora desta entrega.

## Como funciona e por quê

A F-ESPERA usa o primeiro horário de cada viagem expandida em `Rede.viagens[padrão]`, como a D10 de P0-MODELO. Para cada padrão, ordena e deduplica partidas; em cada faixa `[início, fim)`, estima a média das diferenças consecutivas como `(última - primeira)/(n - 1)`. Não reúne sentidos ou variantes diferentes da mesma linha, nem conta de novo as frequências ou visitas de uma circular à mesma parada.

Com duas ou mais partidas distintas, publica H e calcula H/2. Com uma partida, omite a chave e o construtor usa `Parametros.espera_padrao_s` (300 s por padrão); a página identifica o valor como provisório. Sem partida, o construtor não cria embarque. A tabela `esperas[(padrão, faixa)]` já contém segundos de espera: G_E não deve dividir de novo por dois.

`simular_trajeto` escolhe a faixa pela saída, constrói G_E com as esperas e reutiliza `trajeto_mais_rapido` e `Trajeto.tempo_por_tipo()`. Cada troca paga outra espera; continuar no mesmo ônibus não. Horário fora das faixas gera ValueError, parada inexistente KeyError, e destino inalcançável retorna None. Horários acima de 24h não são normalizados: exigem uma faixa explícita que os contenha. A página padrão usa as quatro faixas de 06h a 24h.

Para N viagens, P padrões e F faixas: deduplicação e ordenação custam O(N log N), filtragem por faixa O(FN + PF); espaço O(N + PF). Simular acrescenta a construção de G_E e o Dijkstra O((V + E) log V), com espaço O(N + PF + V + E). A tabela da página custa O(PF + FN). O mapa recebe apenas as paradas do trajeto, sem alterar a rede original.

Limitações: espera H/2 supõe chegada ao acaso e intervalos regulares. Com intervalos irregulares, E[H²]/(2 E[H]) pode ser maior; a versão essencial não aplica essa correção. A faixa da saída vale para o percurso inteiro, inclusive após cruzar outra faixa. Não há consulta à próxima partida exata nem Monte Carlo. A regra D10 pode omitir serviço em parada intermediária quando a viagem começou em outra faixa. As limitações de linhas circulares e da caminhada em linha reta de G_E permanecem.

## Perguntas de verificação

1. **Por que usar o primeiro horário da viagem?** Para respeitar a mesma regra D10 que decide se há embarque em G_E; visitas repetidas de uma circular não são novas saídas.
2. **Por que o construtor recebe espera e não intervalo?** Porque H/2 é calculado por F-ESPERA e deve ser aplicado apenas uma vez.
3. **Uma partida permite estimar H?** Não. Usa-se a espera provisória identificada na tela; sem partida não há embarque.
4. **A saída às 08h59 usa a faixa seguinte durante a viagem?** Não: a versão essencial mantém a faixa da saída fixa; partidas exatas são da extensão G_T.
5. **H/2 vale para intervalos muito irregulares?** É a aproximação essencial; a espera com chegadas ao acaso seria E[H²]/(2 E[H]).

## Critérios de aceite
- [x] RF-ESP-01: Estimar o intervalo entre partidas de cada linha por faixa horária, a partir dos horários ou do `frequencies.txt`
- [x] RF-ESP-02: Calcular a espera esperada de cada embarque e aplicá-la às arestas de embarque de G_E
- [x] RF-ESP-03: Simular um trajeto para um horário de saída, decompondo o tempo total em caminhada, espera e viagem

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [x] Código integrado e revisado por outro integrante (ver Retomada).
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
- [x] Página ou bloco na interface funcionando com o dataset real
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/`
- [x] "Como funciona e por quê" e quiz incorporados ao guia e conferidos com a implementação.
- [ ] O revisor do PR consegue explicar o que o código faz
- [x] Seção do relatório em `relatorio/secoes/F-ESPERA.tex` com figura de atividade, resultados e limitações.
- [x] Roteiro escrito para a gravação do dono.
- [x] Arquivo atualizado com retomada, status, pendências e timeline.

## Plano de implementação

| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato com estado planejado | publicado localmente antes dos consumidores; implementado após testes |
| 2 | Algoritmo com testes de corretude | implementado e testado |
| 3 | Integração G_E e dados reais | executada com feed real; JSON versionado |
| 4 | Página na interface | implementada e validada com AppTest |
| 5 | Medição e complexidade | feitas, com comando, desvio e feed identificados |
| 6 | Guia, quiz, UML, relatório e roteiro | guia, quiz, UML, relatório e roteiro conferidos; gravação no vídeo do grupo |

## Resultados para o relatório

Execução em 11/11/2026, Python 3.12.13, macOS 26.6.2 arm64, na máquina desta sessão. Feed local baixado em 05/11, SHA-256 `623bdf422fb01e8c80373bf92d9cf261199cff213b9eaee9ff16a5610d8d2bd2`; dia 2026-11-04. Comando reproduzível com o ambiente do README:

```sh
source .venv/bin/activate
PYTHONPATH=src python benchmarks/medir_espera.py dados/brutos/bhtrans.zip
```

Saída completa versionada em `benchmarks/resultados/espera-2026-11-11.json`. Dependências fixadas de `requirements.txt` instaladas no ambiente temporário. A leitura fica fora dos tempos abaixo. São 5 repetições de cada chamada com `medir`; médias e desvios amostrais:

| Operação | Média (ms) | Desvio (ms) |
|---|---:|---:|
| `estimar_intervalos` | 5.309 | 0.751 |
| `calcular_esperas` | 0.096 | 0.005 |
| `construir_ge` | 226.463 | 11.113 |
| `consultar_ge_pronto` | 12.441 | 0.424 |
| `simular_trajeto_completo` | 248.724 | 8.640 |

G_E do pico da manhã: V=46100, E=208956. Consulta reprodutível 14788851 → 14792190, saída às 08h: total 2414.593 s; caminhada 583.354 s, espera 920.238 s, viagem 911.000 s. É uma consulta, não uma garantia de pior caso da rede.

| Faixa | Padrões com serviço | Com estimativa | Provisórios |
|---|---:|---:|---:|
| pico_manha | 501 | 481 | 20 |
| entrepico | 458 | 447 | 11 |
| pico_tarde | 494 | 477 | 17 |
| noite | 462 | 437 | 25 |

Validação da interface: testes Streamlit AppTest com pasta e ZIP, isolamento de sessões, erro de leitura, tabela, simulação, rerun e troca de dataset. Feed completo também validado sem exceção: 698 linhas na tabela do pico e métricas 40,24 min (total), 9,72 min (caminhada), 15,34 min (espera), 15,18 min (viagem).

## Roteiro do vídeo (2 a 2,5 min)

1. Abrir a rede pequena na página Início, mostrar o dia do serviço e entrar em Espera.
2. Mostrar os intervalos e distinguir H/2, espera provisória e ausência de serviço. Explicar o gabarito de L1 e L2.
3. Escolher origem, destino e saída, executar a simulação e mostrar os tempos de caminhada, espera e viagem e o mapa. Na rede pequena, caminhada pode vencer o ônibus: isso é resultado do raio de caminhada, não erro na espera.
4. Explicar primeiro horário → partidas distintas → H → H/2 → embarque em G_E → Dijkstra já existente. Apontar diagrama e complexidade.
5. Mostrar o resultado real com comando, feed e máquina registrados. Encerrar com faixa fixa, horários programados e aproximação H/2 para intervalos regulares. Miguel revisa e grava o trecho de 2 a 2,5 minutos.

## Pendências

- Gravar o trecho pelo roteiro. A medição histórica de 11/11 contém plataforma e arquitetura; chip e RAM não foram registrados naquela execução. A simulação programada e a sensibilidade são acompanhadas em suas próprias features.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Miguel.

### Sessão 11/11/2026: main sincronizada em fbb330d; contrato, núcleo de F-ESPERA, página, testes e benchmark implementados. Reutilizados shell/mapa do #45, idênticos no #49, conectando ler na entrada normal. E1–E4 seguem o plano aprovado. Textos e resultados rascunhados para Miguel revisar; sem commits ou mensagens a colegas.

### Validação 11/11/2026: gabaritos e fluxo real passaram. Comando normal da interface verificado em subprocesso sem PYTHONPATH. Relatório compilado com Tectonic; limitações de H/2 e faixa fixa descritas. Aprovação do PR, revisão humana dos textos e gravação permanecem pendentes.

### Fechamento 11/11/2026: 563 testes passaram na suíte completa com Python 3.12.13 e requirements.txt; hook (imports e ruff) verde após ordenar imports e explicitar check=False no teste de subprocesso. .venv local criada e hook configurado. PDF compilado com Tectonic 0.17.0, páginas de Dados/Espera renderizadas e inspecionadas; figuras legíveis e sem sobreposição. Prévia em relatorio/build/main.pdf (ignorada pelo Git). O relatório global ainda tem 9 páginas e seções do grupo pendentes, portanto não é a versão final de entrega. Nenhuma fonte ou feature de outro dono foi editada. Miguel revisa e commita; PR e aprovação permanecem pendentes.

### Separação de branches 11/11/2026: integração P0-DADOS/UI publicada em a8bec84, sem PR. F-ESPERA baseada nesse commit; testes da página em test_pagina_espera.py, sem misturar o escopo com test_integracao_dados.py. Commit/push de Espera autorizados, sem trailers de atribuição; PR não será aberto. O hook é verificado manualmente com sh .githooks/pre-commit, pois o arquivo versionado não tem bit executável.

### Validação da branch separada 11/11/2026: 565 testes passaram após separar carregamento e página de Espera (530 da base P0-DADOS/UI e 35 de Espera). Hook executado manualmente e diff sem erros. Commit/push autorizados para feat/F-ESPERA-simulacao, sem abrir PR; revisão humana e integração futuras.

### Revisão do PR #51 · 15/11/2026
Feedback integral analisado: sem revisões formais ou threads inline. Corrigidos separadores decimais e escopo da medição no relatório, explicitado padrão/sentido e documentado contrato para consumidores de G_E. Comando temporário substituído pelo ambiente padrão. Consulta 14788851 → 14792190 e validação da página já constam em Resultados; não duplicadas. Não foi introduzido cache: a medição de 248,7 ms corresponde à função completa, sem renderização da interface. JSON histórico preservado; identificação completa da máquina ainda requer confirmação. Autoria, integração com Trajetos e mapa e tarefas humanas permanecem pendentes. Miguel autorizou publicação separada das correções, sem merge.

Validação nesta sessão: 565 testes passaram em 2,38 s com Python 3.12.13; Ruff e verificação de imports sem erros. Execução no worktree com o Python da `.venv` do checkout principal, preservando as correções do #50.

Verificação antes da publicação: projeto LaTeX compilado com sucesso pelo compilador integrado do editor, a partir da seção alterada.

### Rebase independente do #50 · 16/11/2026
Retirado a8bec84 da ancestralidade própria com rebase --onto origin/main a8bec84; os commits c688f46 e c4b01cf foram reaplicados sem conflito. A base 6b44827 já contém a interface e o mapa corrigidos pelo #45. Decisão: manter somente o escopo de Espera e retirar a dependência do #50 da descrição do PR. Backups locais preservam o histórico anterior. Melhorias indicadas por Rafael para depois do merge e tarefas humanas seguem nas pendências; não houve alteração de features de outros donos.

Validação após rebase: Python 3.12 da .venv do checkout principal, -m pytest -q → 668 passed in 2.84s. O hook sem a .venv no PATH encontrou Python global sem Ruff; repetido com o ambiente do projeto, passou com imports e Ruff verdes. git diff --check sem erros.

### Fechamento documental de 20/11/2026
Aprovação e merge do #51 confirmados. Explicação de H/2, regra de faixa fixa, quiz e seção do relatório conferidos com o código e o JSON.
