# P0-DADOS · Leitura do GTFS, modelo normalizado e rede de teste

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Miguel (@Miguelgdn1) · **Issue:** #3 · **Visões do grafo:** não se aplica (modelo normalizado)
**Depende de:** nada · **Bloqueia:** P0-MODELO, P0-UI, F-ESPERA, F-BALD
**Prazo:** contrato 30/10; rede de teste 31/10; feed real 03/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-DAD-01, RF-DAD-02, RF-DAD-03, RF-DAD-04). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada

- **Última sessão:** 15/11/2026, revisão do feedback do PR #50 na branch `feat/P0-DADOS-integracao` (`a8bec84`), sincronizada com sua origem.
- **Onde parou:** PR #50 aberto; documentação corrigida e referência da figura de sequência alinhada. Correções prontas; Miguel autorizou commit e push desta branch separadamente do #51, sem merge.
- **Próximo passo:** integrar primeiro o #45 preservando a autoria de Arthur; depois reorganizar o #50 sobre a main, mantendo apenas a integração e documentação de P0-DADOS. Miguel revisa guia, relatório e roteiro; Henrique precisa registrar aprovação do leitor no #42 ou explicitamente no #50.
- **Arquivos tocados:** este arquivo e `relatorio/secoes/dados.tex`.
- **Como testar:** `.venv/bin/python -m pytest -q`; `sh .githooks/pre-commit`; `git diff --check`.
- **Bloqueios:** #45 ainda aberto; o commit do #50 ainda inclui arquivos de Arthur. Rebase de autoria depende dessa integração e não foi realizado nesta sessão sem autorização para commits/merge. #42 continua com CHANGES_REQUESTED e #50 sem aprovação formal. DoD permanece aberto.

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
| Interface | implementado | 11/11: carregamento normal com ler; pasta/ZIP e mapa verificados; feed completo validado com AppTest |
| Testes | implementado | 15/11: suíte da branch de integração validada; resultado final registrado abaixo |
| Desempenho (tempo medido) | implementado | 05/11: leitura medida no feed real com `medir` |
| Guia (explicação e quiz) | parcial | Rascunho incorporado ao GUIA; Miguel precisa revisar as decisões e a explicação |
| Relatório | parcial | 11/11: Tectonic compilou; figura resumida para legibilidade; Miguel revisa o texto |
| Vídeo | parcial | Roteiro específico abaixo; falta revisão e gravação |

## Especificação
Contrato inicial em `docs/fontes/plano-de-projeto.md` §9. Publicar as assinaturas com o comentário `estado: planejado` antes de implementar; trocar para `implementado` quando os testes passarem. Feed bruto em `dados/brutos/` (fora do Git, baixado por script); rede de teste em `dados/rede-teste/`.

Assinaturas publicadas e implementadas: `Parada`, `Linha`, `Padrao`, `Viagem`, `Frequencia`, `Rede.recortar(caixa, linhas)`, `ler(caminho, dia=None)` e `validar(caminho)`. `Rede.viagens[padrão]` reúne as sequências de horários por viagem exigidas por `RedeConstrutores` no PR #38; `Rede.viagens_por_id[id]` conserva a identidade GTFS de cada viagem. `Rede.partidas[(padrao, parada)]` mantém a interface prevista no plano. `caixa` usa `(lat_min, lon_min, lat_max, lon_max)`.

## Como funciona e por quê
O leitor transforma linhas, paradas e horários do GTFS em objetos sem construir grafo. Seleciona uma quarta-feira ativa (a mais próxima da versão do feed, quando informada), aplica o calendário e suas exceções, agrupa viagens da mesma linha que percorrem a mesma sequência exata de paradas e expande as partidas de `frequencies.txt`. Guarda os horários por viagem porque uma lista de partidas por parada sozinha não revela quais duas passagens pertencem ao mesmo ônibus. Horários acima de 24h representam viagens que continuam após a meia-noite; descartá-los apagaria serviço válido.

O recorte mantém somente linhas e paradas selecionadas. Se o corte separa dois trechos de um padrão, cria padrões distintos para evitar uma ligação direta inexistente; se trechos da mesma linha terminam com a mesma sequência de paradas, reúne suas viagens no mesmo padrão. O leitor percorre as linhas do CSV em O(R + N log N) de tempo e O(R + N) de espaço, onde N inclui as partidas expandidas e a ordenação; `stop_times.txt` é processado em fluxo porque o feed real é grande. O recorte custa O(N log N + P + V) de tempo e O(N + P + V) de espaço. Linhas inválidas são relatadas e não entram na rede; a validação atual se concentra no dia escolhido, não em todos os serviços do calendário.

Revisão do contrato: cada sequência em `Rede.viagens[padrão]` mantém a ordem posicional de `Padrao.paradas` e permite calcular a mediana do tempo entre paradas consecutivas exigida por P0-MODELO. Para uma viagem com frequência, cada partida gera uma sequência deslocada; a viagem de referência não entra de novo. `Rede.partidas[(padrão, parada)]` permanece disponível, mas reúne todas as visitas quando uma viagem passa mais de uma vez pelo mesmo `stop_id`. O PR #38 registra a D11, aceita em 05/11: uma plataforma por par `(parada, padrão)` para linhas circulares; PR #38 integrado na main em `d4a696b`.

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

- [ ] Código integrado na `main` por PR aprovado por outro integrante (merge do #42 confirmado em `fbb330d`; aprovação formal posterior à revisão CHANGES_REQUESTED não localizada)
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde (ver validação final desta branch abaixo; hook executado manualmente, bit executável ainda pendente em P0-REPO)
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação com NetworkX não se aplica à leitura de GTFS
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina (E não se aplica antes de construir grafo)
- [x] Página ou bloco na interface funcionando com o dataset real (11/11: carregamento e mapa pela entrada normal em AppTest; implementação no commit `a8bec84` do PR #50)
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/`
- [ ] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md` (rascunho incorporado; Miguel revisa)
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/dados.tex`, com figura, resultado e limitação (compilada com Tectonic em 11/11; revisão por Miguel pendente)
- [ ] Roteiro do vídeo escrito no arquivo da feature (rascunho abaixo; Miguel revisa)
- [ ] Arquivo da feature atualizado: retomada ("concluída"), status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | feito; atualizado para implementado após testes |
| 2 | Algoritmo com testes de corretude | feito para leitura e recorte |
| 3 | Integração com a visão do grafo e com os dados reais | feed e construtores integrados; F-ESPERA permanece na branch própria do PR #51 |
| 4 | Página na interface | entrada normal funcional localmente, com shell/mapa reaproveitados do #45 |
| 5 | Tempo medido na rede real e complexidade justificada | feito |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | rascunhos preparados e relatório compilado; revisão por Miguel pendente |

## Resultados para o relatório
Execução de 05/11/2026 com `PYTHONPATH=src python3 -c 'from transporte.dados.leitor_gtfs import ler; r=ler("dados/brutos/bhtrans.zip"); print(r.dia,len(r.paradas),len(r.linhas),len(r.padroes),len(r.viagens_por_id),len(r.inconsistencias))'`: dia 04/11/2026; 9.659 paradas (V), 303 linhas, 698 padrões, 24.503 viagens e 0 inconsistências reportadas para o serviço selecionado. E não se aplica ao modelo de dados. Fonte: [GTFS convencional da PBH](https://ckan.pbh.gov.br/dataset/77764a7e-63fc-4111-ace3-fb7d3037953a/resource/f0fa78dc-74c3-49fa-8971-c310a76a07fa/download/gtfsfiles.zip); arquivo baixado em 05/11/2026, SHA-256 `623bdf422fb01e8c80373bf92d9cf261199cff213b9eaee9ff16a5610d8d2bd2` (metadados em `dados/brutos/bhtrans.json`, fora do Git).

Comando de medição: `PYTHONPATH=src python3 -c 'from transporte.dados.leitor_gtfs import ler; from transporte.util.medicao import medir; print(medir(ler,"dados/brutos/bhtrans.zip",repeticoes=3))'`. Média observada: 7,753 s; desvio amostral: 0,114 s; 3 repetições. Máquina: MacBook Air, Apple M4, 16 GB, arm64, Python 3.14.6.

Revisão do recorte real: `PYTHONPATH=src python3 -c 'from transporte.dados.leitor_gtfs import ler; r=ler("dados/brutos/bhtrans.zip"); ids=set(list(r.linhas)[:5]); c=r.recortar((-19.95,-43.98,-19.88,-43.88),ids); print(len(c.paradas),len(c.linhas),len(c.padroes),len(c.viagens_por_id))'` produziu 267 paradas, 5 linhas, 10 padrões e 507 viagens. As referências de padrões para linhas/paradas e de viagens para padrões foram verificadas como válidas na mesma execução.

Integração local com o código do PR #38, sem alterar sua branch: após carregar o mesmo recorte, `construir_gp(c)` produziu V=267 e E=1.458; `construir_ge(c,"pico_manha")` produziu V=559 e E=2.037. O comando usado foi `PYTHONPATH=/private/tmp/grafos-pr38-integration/src python3 -c 'from transporte.dados.leitor_gtfs import ler; from transporte.modelo.construtores import construir_gp, construir_ge; r=ler("dados/brutos/bhtrans.zip"); ids=set(list(r.linhas)[:5]); c=r.recortar((-19.95,-43.98,-19.88,-43.88),ids); gp=construir_gp(c); ge=construir_ge(c,"pico_manha"); print(gp.grafo.num_vertices(),gp.grafo.num_arestas(),ge.grafo.num_vertices(),ge.grafo.num_arestas())'`.

## Roteiro do vídeo (2 a 2,5 min)
1. Mostrar o problema: o GTFS tem linhas, paradas, viagens e calendários em CSVs separados; a ferramenta precisa reuni-los sem perder a identidade de cada viagem.
2. Abrir a rede de teste e apontar os horários de uma viagem e a exceção em `calendar_dates.txt`. Mostrar no código como `ler` escolhe o dia e organiza `Rede`.
3. Mostrar a validação de uma parada sem coordenada e o recorte que não cria uma ligação direta A → C quando B fica fora.
4. Explicar que `stop_times.txt` é percorrido em fluxo, o custo O(R + N log N), o resultado medido no feed real e a limitação de validar apenas o serviço do dia escolhido. Encerrar com a integração às visões de grafo, sem afirmar que já está pronta.

## Pendências

- ~~Aguardar merge do #42 e #38.~~ Integrados na main (`fbb330d` e `d4a696b`); retomada antiga corrigida nesta sessão.
- ~~Conectar o leitor à interface.~~ Feito localmente com shell/mapa/protocolos do #45, idênticos no #49; AppTest de pasta/ZIP e do feed completo passou. Publicado no PR #50; revisão e integração pendentes.
- ~~Compilar o relatório e conferir a figura de dados.~~ Compilado com Tectonic 0.17.0; figura de sequência resumida substitui a atividade muito estreita no relatório. Atividade completa continua nos diagramas. Revisão visual final registrada no fechamento.
- Aprovação formal do #42 não localizada: API retornou CHANGES_REQUESTED de Henrique e comentário posterior de Miguel com as correções. Não inferir aprovação a partir do merge.
- Miguel revisar guia, decisões de 05/11, seção Dados e roteiro e gravar o vídeo. Rascunhos não são revisão humana.
- PR #50 aberto. A revisão apontou código de Arthur no commit de Miguel: aguardar integração do #45 e reorganizar a branch antes do merge. Commit e push desta branch autorizados por Miguel; merge e comentários remotos não autorizados.
- Sugestões opcionais de recorte e seleção do dia na Início não implementadas: ampliam o escopo da integração. Bit executável do hook pertence a P0-REPO e deve ser corrigido em PR separado; nenhuma mensagem enviada ao responsável.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Miguel.
### Sessão 05/11/2026: contrato publicado, leitor e recorte implementados, rede de teste criada; GTFS convencional baixado e lido; pytest (214, ainda incluindo o rascunho de F-ESPERA) e ruff verdes; tempos medidos no feed real. Aguardando revisão e integração.
### Sessão 05/11/2026: escopo da branch corrigido para conter apenas P0-DADOS; rascunho de F-ESPERA guardado fora do repositório. Diagrama UML gerado, guia e seção de dados do relatório preenchidos, roteiro específico rascunhado. Revisão do dono, LaTeX, interface e PR pendentes.
### Revisão 05/11/2026: contrato de G_P/G_E conferido sem alterar P0-MODELO; recorte por linha corrigido para remover paradas não atendidas e preservar inconsistências. Feed real revelou padrões com parada repetida, pendência de integração para Henrique. Testes e lint refeitos antes do commit.
### Revisão 05/11/2026: PRs #38 a #41 examinados. `Rede.viagens` alinhada ao protocolo de P0-MODELO, com `viagens_por_id` mantendo identidade GTFS; integração local com G_P/G_E do PR #38 passou na rede de teste e no recorte real. D11 trata a parada repetida na branch de Henrique, ainda aberta. Na branch só de P0-DADOS, 211 testes e ruff verdes.
### Revisão 08/11/2026: branch rebaseada sobre `origin/main` (`604b70b`), preservando as decisões de P0-DADOS e a atualização do relatório final em `docs/GUIA.md`. Expansão de frequências em `Rede.viagens`, recorte de dois trechos e reunião de padrões equivalentes corrigidos; 442 testes, ruff e hook verdes. Com os construtores atuais do PR #38 em cópia temporária, G_P construiu 4 vértices e 13 arestas na rede pequena; G_E mostrou embarque na L2 nas faixas 09:00–09:30 e 09:30–10:00. Feed real original: 9.659 paradas, 303 linhas, 698 padrões e 24.503 viagens; recorte: 267 paradas, 5 linhas, 10 padrões e 507 viagens, com referências válidas. `latexmk` não disponível neste ambiente. Miguel autorizou publicar as correções no PR #42.

### Sessão 11/11/2026: repositório sincronizado; merge do #42 confirmado, sem aprovação formal posterior localizada. UI reaproveitada do #45/#49 e conectada a ler; falhas de leitura preservam a rede anterior. Corrigido import da entrada direta sem PYTHONPATH. Pasta, ZIP e feed real validados com Streamlit AppTest. Relatório compilado com Tectonic portátil; figura resumida adicionada para legibilidade. Integração posteriormente separada em `feat/P0-DADOS-integracao` e publicada no commit `a8bec84`, PR #50; a sobreposição de autoria com #45 permanece pendente.

Validação real de 11/11: AppTest executou a entrada normal com `dados/brutos/bhtrans.zip`, mostrando 9.659 paradas, 303 linhas e 698 padrões, sem exceção. Os testes versionados em tests/interface/test_integracao_dados.py reproduzem a integração com o feed pequeno.

### Fechamento 11/11/2026: Suíte conjunta com F-ESPERA validada com Python 3.12.13 e requirements.txt (não representa a contagem desta branch); hook (imports e ruff) verde após ordenar imports e explicitar check=False no teste de subprocesso. .venv local criada e hook configurado. PDF compilado com Tectonic 0.17.0, páginas de Dados/Espera renderizadas e inspecionadas; figuras legíveis e sem sobreposição. Prévia em relatorio/build/main.pdf (ignorada pelo Git). O relatório global ainda tem 9 páginas e seções do grupo pendentes, portanto não é a versão final de entrega. Nenhuma fonte ou feature de outro dono foi editada. Miguel revisa; PR #50 posteriormente aberto, aprovação permanece pendente.

### Separação de branches 11/11/2026: Miguel autorizou commits e push das duas branches, sem abrir PR. Testes de P0-DADOS separados em test_integracao_dados.py para validar esta branch sem depender de Espera. A branch F-ESPERA será derivada desta integração, mantendo um commit por feature e a dependência explícita.

### Validação da branch separada 11/11/2026: Suíte sem os arquivos de F-ESPERA validada (contagem consolidada na validação final abaixo); hook verde e diff sem erros de espaços. Commit/push autorizados para feat/P0-DADOS-integracao, sem abertura de PR. Revisão humana e aprovação continuam pendentes.

### Revisão do PR #50 · 15/11/2026
Descrição e comentário geral de Rafael lidos integralmente; API sem comentários inline ou revisões formais no #50. Corrigidos Retomada, DoD e timeline desatualizados e o rótulo da figura para `fig:sequencia-dados`. Removida daqui a validação de Espera: a consulta e as métricas já constam em `feature-F-ESPERA.md` na branch `feat/F-ESPERA-simulacao` (PR #51), sem necessidade de duplicá-las ou alterar essa feature nesta branch.

Decisão: preservar comportamento e escopo; nenhuma alteração no leitor, shell ou mapa é exigida pelos itens objetivos de código do feedback. A autoria não se corrige apagando arquivos da interface: o #45 precisa entrar primeiro. Aprovação formal, revisão humana do guia/quiz/relatório/roteiro, gravação e conclusão após merge permanecem pendentes; não foram marcadas como atendidas por inferência.

Validação final desta branch em 15/11/2026: `.venv/bin/python -m pytest -q` → **530 passed in 2.30s**, Python 3.12.13; `sh .githooks/pre-commit` → imports permitidos e Ruff sem erros; `git diff --check` → sem erros. Referência e label da figura conferidos em conjunto; não houve recompilação LaTeX nesta sessão (`tectonic` indisponível no PATH). Nenhuma alteração de código executável, commit, push ou operação remota de escrita.

### Publicação das correções · 15/11/2026
Miguel autorizou commit e push separados dos PRs #50 e #51. Preservado o escopo de documentação; bloqueios de autoria e aprovação continuam abertos. A restrição anterior a commits/push foi substituída por essa autorização; nenhum merge será realizado.

Verificação antes da publicação: projeto LaTeX compilado com sucesso pelo compilador integrado do editor, a partir da seção alterada.
