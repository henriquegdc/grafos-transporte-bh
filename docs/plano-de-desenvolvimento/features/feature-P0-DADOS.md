# P0-DADOS · Leitura do GTFS, modelo normalizado e rede de teste

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Miguel (@Miguelgdn1) · **Issue:** #3 · **Visões do grafo:** não se aplica (modelo normalizado)
**Depende de:** nada · **Bloqueia:** P0-MODELO, P0-UI, F-ESPERA, F-BALD
**Prazo:** contrato 30/10; rede de teste 31/10; feed real 03/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-DAD-01, RF-DAD-02, RF-DAD-03, RF-DAD-04). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 05/11/2026, branch `feat/P0-DADOS-gtfs`.
- **Onde parou:** somente P0-DADOS nesta branch; revisão técnica do contrato e recorte no feed real feitos. PR e integração na interface pendentes.
- **Próximo passo:** Miguel alinhar com Henrique como G_E representará uma parada repetida no mesmo padrão; revisar as decisões rascunhadas no `docs/GUIA.md` e o relatório; validar a compilação LaTeX em ambiente com TeX; abrir o PR de P0-DADOS.
- **Arquivos tocados:** `src/transporte/dados/{modelo,leitor_gtfs}.py`, `scripts/baixar_gtfs.py`, `dados/rede-teste/`, `tests/dados/test_leitor_gtfs.py`, `docs/diagramas/atividade-p0-dados.{puml,png}`, `docs/GUIA.md`, `relatorio/secoes/dados.tex`, este arquivo.
- **Como testar:** `PYTHONPATH=src UV_CACHE_DIR=/private/tmp/grafos-uv-cache uv run --no-project --offline --with pytest --with ruff --with networkx python -m pytest -q`, `UV_CACHE_DIR=/private/tmp/grafos-uv-cache uv run --no-project --offline --with ruff ruff check .` e `plantuml -tpng -failfast2 docs/diagramas/atividade-p0-dados.puml`.
- **Bloqueios:** o contrato de `VisaoGE.plataforma[(parada, padrão)]` não distingue visitas repetidas à mesma parada; página com dados reais depende de P0-UI; hook e distribuição LaTeX não estão disponíveis nesta `main`; DoD exige PR aprovado.

## Objetivo
Leitura do GTFS, modelo normalizado e rede de teste. Fecha:

- **RF-DAD-01** (E): Ler um feed GTFS (paradas, linhas, viagens, horários, calendário) e convertê-lo no modelo normalizado
- **RF-DAD-02** (E): Validar o feed e relatar inconsistências (parada sem coordenada, horário inválido, viagem sem paradas)
- **RF-DAD-03** (E): Recortar a rede por região (retângulo de coordenadas) ou por conjunto de linhas
- **RF-DAD-04** (E): Fornecer uma rede de teste pequena, em formato GTFS, com respostas conhecidas

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | não aplicável | Esta feature fornece dados, não algoritmo de grafo |
| Modelo e dados | implementado | 05/11: GTFS pasta/ZIP, calendário, frequências, validação e recorte; feed real lido |
| Interface | não iniciado | Aguarda P0-UI |
| Testes | implementado | 05/11: gabarito manual, casos de borda e recorte real; suíte geral verde |
| Desempenho (tempo medido) | implementado | 05/11: leitura medida no feed real com `medir` |
| Guia (explicação e quiz) | parcial | Rascunho incorporado ao GUIA; Miguel precisa revisar as decisões e a explicação |
| Relatório | parcial | `relatorio/secoes/dados.tex` escrito com figura e medição; falta compilar e revisar |
| Vídeo | parcial | Roteiro específico abaixo; falta revisão e gravação |

## Especificação
Contrato inicial em `docs/fontes/plano-de-projeto.md` §9. Publicar as assinaturas com o comentário `estado: planejado` antes de implementar; trocar para `implementado` quando os testes passarem. Feed bruto em `dados/brutos/` (fora do Git, baixado por script); rede de teste em `dados/rede-teste/`.

Assinaturas publicadas e implementadas: `Parada`, `Linha`, `Padrao`, `Viagem`, `Frequencia`, `Rede.recortar(caixa, linhas)`, `ler(caminho, dia=None)` e `validar(caminho)`. `Rede.viagens` conserva a identidade e a sequência de horários de cada viagem para que P0-MODELO calcule tempos entre paradas; `Rede.partidas[(padrao, parada)]` mantém a interface prevista no plano. `caixa` usa `(lat_min, lon_min, lat_max, lon_max)`.

## Como funciona e por quê
O leitor transforma linhas, paradas e horários do GTFS em objetos sem construir grafo. Seleciona uma quarta-feira ativa (a mais próxima da versão do feed, quando informada), aplica o calendário e suas exceções, agrupa viagens da mesma linha que percorrem a mesma sequência exata de paradas e expande as partidas de `frequencies.txt`. Guarda os horários por viagem porque uma lista de partidas por parada sozinha não revela quais duas passagens pertencem ao mesmo ônibus. Horários acima de 24h representam viagens que continuam após a meia-noite; descartá-los apagaria serviço válido.

O recorte mantém somente linhas e paradas selecionadas. Se o corte separa dois trechos de um padrão, cria padrões distintos para evitar uma ligação direta inexistente. O leitor percorre as linhas do CSV em O(R + N log N) de tempo e O(R + N) de espaço, onde N inclui as partidas expandidas e a ordenação; `stop_times.txt` é processado em fluxo porque o feed real é grande. O recorte custa O(N log N + P + V) de tempo e O(N + P + V) de espaço. Linhas inválidas são relatadas e não entram na rede; a validação atual se concentra no dia escolhido, não em todos os serviços do calendário.

Revisão do contrato: `Rede.viagens[id].horarios` mantém a ordem posicional de `Padrao.paradas` e permite calcular a mediana do tempo entre paradas consecutivas exigida por P0-MODELO. `Rede.partidas[(padrão, parada)]` permanece disponível, mas reúne todas as visitas quando uma viagem passa mais de uma vez pelo mesmo `stop_id`. O contrato publicado de `VisaoGE.plataforma[(parada, padrão)]` também reúne essas posições; Henrique precisa decidir como representá-las antes de construir G_E, para não permitir atalhos indevidos.

## Perguntas de verificação
1. Por que `Rede` guarda os horários por viagem? Para relacionar passagens consecutivas do mesmo ônibus e calcular o tempo de viagem.
2. O que significa `24:10:00`? Dez minutos após a meia-noite do dia seguinte, ainda na mesma jornada GTFS.
3. Por que o recorte pode dividir um padrão? Para não criar uma aresta entre paradas separadas por um trecho removido.

## Critérios de aceite
- [x] RF-DAD-01: Ler um feed GTFS (paradas, linhas, viagens, horários, calendário) e convertê-lo no modelo normalizado
- [x] RF-DAD-02: Validar o feed e relatar inconsistências (parada sem coordenada, horário inválido, viagem sem paradas)
- [x] RF-DAD-03: Recortar a rede por região (retângulo de coordenadas) ou por conjunto de linhas
- [x] RF-DAD-04: Fornecer uma rede de teste pequena, em formato GTFS, com respostas conhecidas

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [ ] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde (`ruff` e pytest passaram; hook ainda não existe na `main`)
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação com NetworkX não se aplica à leitura de GTFS
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina (E não se aplica antes de construir grafo)
- [ ] Página ou bloco na interface funcionando com o dataset real
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/`
- [ ] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md` (rascunho incorporado; Miguel revisa)
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/dados.tex`, com figura, resultado e limitação (escrita; compilação e revisão pendentes)
- [ ] Roteiro do vídeo escrito no arquivo da feature (rascunho abaixo; Miguel revisa)
- [ ] Arquivo da feature atualizado: retomada ("concluída"), status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | feito; atualizado para implementado após testes |
| 2 | Algoritmo com testes de corretude | feito para leitura e recorte |
| 3 | Integração com a visão do grafo e com os dados reais | feed real lido; integração G_P/G_E depende de P0-MODELO |
| 4 | Página na interface | pendente de P0-UI |
| 5 | Tempo medido na rede real e complexidade justificada | feito |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | rascunhos preparados; falta revisão por Miguel e compilação do relatório |

## Resultados para o relatório
Execução de 05/11/2026 com `PYTHONPATH=src python3 -c 'from transporte.dados.leitor_gtfs import ler; r=ler("dados/brutos/bhtrans.zip"); print(r.dia,len(r.paradas),len(r.linhas),len(r.padroes),len(r.viagens),len(r.inconsistencias))'`: dia 04/11/2026; 9.659 paradas (V), 303 linhas, 698 padrões, 24.503 viagens e 0 inconsistências reportadas para o serviço selecionado. E não se aplica ao modelo de dados. Fonte: [GTFS convencional da PBH](https://ckan.pbh.gov.br/dataset/77764a7e-63fc-4111-ace3-fb7d3037953a/resource/f0fa78dc-74c3-49fa-8971-c310a76a07fa/download/gtfsfiles.zip); arquivo baixado em 05/11/2026, SHA-256 `623bdf422fb01e8c80373bf92d9cf261199cff213b9eaee9ff16a5610d8d2bd2` (metadados em `dados/brutos/bhtrans.json`, fora do Git).

Comando de medição: `PYTHONPATH=src python3 -c 'from transporte.dados.leitor_gtfs import ler; from transporte.util.medicao import medir; print(medir(ler,"dados/brutos/bhtrans.zip",repeticoes=3))'`. Média observada: 7,753 s; desvio amostral: 0,114 s; 3 repetições. Máquina: MacBook Air, Apple M4, 16 GB, arm64, Python 3.14.6.

Revisão do recorte real: `PYTHONPATH=src python3 -c 'from transporte.dados.leitor_gtfs import ler; r=ler("dados/brutos/bhtrans.zip"); ids=set(list(r.linhas)[:5]); c=r.recortar((-19.95,-43.98,-19.88,-43.88),ids); print(len(c.paradas),len(c.linhas),len(c.padroes),len(c.viagens))'` produziu 267 paradas, 5 linhas, 10 padrões e 507 viagens. As referências de padrões para linhas/paradas e de viagens para padrões foram verificadas como válidas na mesma execução.

## Roteiro do vídeo (2 a 2,5 min)
1. Mostrar o problema: o GTFS tem linhas, paradas, viagens e calendários em CSVs separados; a ferramenta precisa reuni-los sem perder a identidade de cada viagem.
2. Abrir a rede de teste e apontar os horários de uma viagem e a exceção em `calendar_dates.txt`. Mostrar no código como `ler` escolhe o dia e organiza `Rede`.
3. Mostrar a validação de uma parada sem coordenada e o recorte que não cria uma ligação direta A → C quando B fica fora.
4. Explicar que `stop_times.txt` é percorrido em fluxo, o custo O(R + N log N), o resultado medido no feed real e a limitação de validar apenas o serviço do dia escolhido. Encerrar com a integração às visões de grafo, sem afirmar que já está pronta.

## Pendências
- Miguel revisar o contrato da `Rede` com Henrique e integrar o modelo aos construtores G_P/G_E quando P0-MODELO estiver implementado.
- A execução de `PYTHONPATH=src python3 -c 'from transporte.dados.leitor_gtfs import ler; r=ler("dados/brutos/bhtrans.zip"); print(sum(len(p.paradas)!=len(set(p.paradas)) for p in r.padroes.values()))'` encontrou 387 padrões com `stop_id` repetido no feed real. O mapa de plataformas de P0-MODELO precisa de uma decisão sobre ocorrências repetidas; não alterar o arquivo da feature de Henrique nesta branch.
- Página da interface, hook, compilação e revisão do relatório, revisão por Miguel do guia e roteiro, e PR aprovado ainda necessários para o DoD.
- Decisões de 05/11 registradas como rascunho no `docs/GUIA.md` aguardam revisão de Miguel.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Miguel.
### Sessão 05/11/2026: contrato publicado, leitor e recorte implementados, rede de teste criada; GTFS convencional baixado e lido; pytest (214) e ruff verdes; tempos medidos no feed real. Aguardando revisão e integração.
### Sessão 05/11/2026: escopo da branch corrigido para conter apenas P0-DADOS; rascunho de F-ESPERA guardado fora do repositório. Diagrama UML gerado, guia e seção de dados do relatório preenchidos, roteiro específico rascunhado. Revisão do dono, LaTeX, interface e PR pendentes.
### Revisão 05/11/2026: contrato de G_P/G_E conferido sem alterar P0-MODELO; recorte por linha corrigido para remover paradas não atendidas e preservar inconsistências. Feed real revelou padrões com parada repetida, pendência de integração para Henrique. Testes e lint refeitos antes do commit.
