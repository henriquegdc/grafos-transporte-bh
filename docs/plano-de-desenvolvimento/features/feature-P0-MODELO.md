# P0-MODELO · Modelagem, UML e construtores de G_P e G_E

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Henrique (@henriquegdc) · **Issue:** #4 · **Visões do grafo:** G_P, G_E
**Depende de:** contratos de P0-GRAFO e P0-DADOS · **Bloqueia:** F-ROTA, F-ESPERA, F-MET, F-EFI, F-RES
**Prazo:** assinaturas 31/10; G_P 02/11; G_E 03/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-GRF-04, RF-GRF-05, RF-GRF-07). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 05/11, Henrique, branch `feat/P0-MODELO-etapa1` (PR #41): revisão do PR #42 (P0-DADOS, mudança pedida) e etapa 5, construtores medidos no feed real com a `Rede` do #42 (`benchmarks/medir_modelo_rota.py`, no PR #39).
- **Onde parou:** etapa 2 concluída: `construir_gp`, `construir_ge`, `salvar`, `carregar` e `VisaoGE.baldeacoes` implementados com 33 testes (gabaritos à mão, bordas, grade espacial contra a busca ingênua, ida e volta do pickle); os três módulos com `estado: implementado`. Os construtores leem a Rede pelo protocolo `RedeConstrutores` (paradas, padrões e `viagens[padrão]`), porque o contrato da `Rede` (P0-DADOS) ainda não existe. Piso de 1 s (M2 da F-MET) aceito e registrado. A `Rede` do PR #42 atende o protocolo sem adaptador; no feed real, G_P sai em 0,31 s e G_E em cerca de 0,35 s por faixa (ver Resultados).
- **Próximo passo:** conseguir aprovação nos PRs #38, #40 e #41, nessa ordem; acompanhar a correção do item 1 no PR #42 (frequências em `Rede.viagens`); quando o #42 entrar, etapa 3 (teste de integração com a rede de teste do Miguel); combinar com o Thiago a seção Fundamentação (dona dupla). Depois: etapa 6. F-ROTA segue no PR #39.
- **Arquivos tocados:** `src/transporte/modelo/{parametros,visoes,construtores}.py`, `tests/modelo/{test_construtores,test_visoes}.py`, `docs/diagramas/{classes,classes-modelo,ge-exemplo}.{puml,png}`, `relatorio/secoes/{modelagem,introducao,plano}.tex`, `relatorio/figuras/{classes-modelo,ge-exemplo,casos-de-uso}.png`, `docs/diagramas/casos-de-uso.{puml,png}` (dpi 200), `README.md` §3, `docs/GUIA.md` §8, `docs/fontes/modelagem.md` §3.4 (piso), este arquivo.
- **Como testar:** `PYTHONPATH=src python -m pytest tests` (243 em 05/11, 33 de `tests/modelo`); `ruff check src tests`; diagramas: `java -jar plantuml-1.2026.9.jar -charset UTF-8 -tpng -failfast2 docs/diagramas/*.puml`.
- **Bloqueios:** a etapa 3 depende do merge do PR #42 (P0-DADOS, mudança pedida em 05/11).

## Objetivo
Modelagem, UML e construtores de G_P e G_E. Fecha:

- **RF-GRF-04** (E): Construir a visão G_P (paradas) a partir do modelo normalizado
- **RF-GRF-05** (E): Construir a visão G_E (parada × linha) com arestas de embarque, viagem, desembarque e caminhada
- **RF-GRF-07** (D): Salvar e carregar grafos construídos, para não reprocessar o GTFS a cada execução

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 05/11: construtores de G_P e G_E, grade espacial da caminhada, salvar e carregar, `baldeacoes` |
| Modelo e dados | em andamento | 05/11: a `Rede` do PR #42 atende o protocolo `RedeConstrutores` sem adaptador; G_P e G_E montados do feed real. Falta o teste de integração depois do merge do #42 |
| Interface | não iniciado | |
| Testes | em andamento | 05/11: 33 verdes (gabarito à mão, bordas, grade contra busca ingênua em 10 sementes, pickle); teste de mutação à mão: filtro de negativos, piso, deduplicação de embarque e de desembarque e folga da grade derrubam testes. Falta a rede de teste do Miguel |
| Desempenho (tempo medido) | concluído | 05/11: G_P 312,8 ms, G_E 342 a 365 ms por faixa no feed real; ver Resultados |
| Guia (explicação e quiz) | não iniciado | |
| Relatório | em andamento | 05/11: Etapa 1 v1 das seções do Henrique, compiladas com MiKTeX 25.12 sem erro nem referência indefinida: Introdução (cerca de 1,1 página, com o diagrama de casos de uso), Modelagem (cerca de 2,5) e Plano (cerca de 0,4); Introdução e Plano somam 1,5, o orçamento das duas. Falta a Fundamentação, com o Thiago |
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
- [x] RF-GRF-07: Salvar e carregar grafos construídos, para não reprocessar o GTFS a cada execução (05/11: `salvar` e `carregar` com pickle, testados)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [ ] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [ ] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente
- [ ] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina (05/11)
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
| 1 | Contrato (assinaturas com estado "planejado") | concluída (PR #33) |
| 2 | Algoritmo com testes de corretude | concluída em 05/11 |
| 3 | Integração com a visão do grafo e com os dados reais | em andamento: construtores rodam no feed real com a `Rede` do PR #42; falta o teste de integração na rede de teste, depois do merge do #42 |
| 4 | Página na interface | |
| 5 | Tempo medido na rede real e complexidade justificada | tempo medido em 05/11; a justificativa da complexidade entra no "Como funciona" (etapa 6) |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | |

## Resultados para o relatório
_Todo número vem com o comando que o gerou._

**Construção das visões, 05/11/2026.** Comando: `PYTHONPATH=src python benchmarks/medir_modelo_rota.py dados/brutos/bhtrans.zip` (script no PR #39), sobre os construtores do PR #38 com a leitura do PR #42 (`77b0fbd`, ainda não integrado). Feed: GTFS convencional da PBH baixado em 05/11/2026, SHA-256 `623bdf422fb01e8c80373bf92d9cf261199cff213b9eaee9ff16a5610d8d2bd2` (o mesmo do arquivo da P0-DADOS), serviço de 04/11/2026: 9.659 paradas, 698 padrões, 24.503 viagens. Máquina: Intel Core i5-13600KF, 31,8 GB, Windows 11, Python 3.14.3. Tempos com `medir`, n = 5; a leitura do GTFS não entra.

| Visão | V | E | Tempo |
|---|---|---|---|
| G_P | 9.659 | 122.732 | 312,8 ms ± 5,8 ms |
| G_E, pico da manhã | 46.100 | 208.956 | 341,9 ms ± 13,1 ms |
| G_E, entrepico | 46.100 | 207.205 | 365,0 ms ± 32,9 ms |
| G_E, pico da tarde | 46.100 | 208.550 | 346,3 ms ± 12,4 ms |
| G_E, noite | 46.100 | 206.868 | 361,8 ms ± 20,1 ms |

Do mesmo feed, numa checagem avulsa em 05/11 (script de revisão do PR #42, não versionado): no G_E do pico da manhã, 110.178 das 208.956 arestas são de caminhada, 36.385 de viagem, 36.121 de desembarque e 26.272 de embarque; 387 dos 698 padrões repetem alguma parada (D11); 1.949 trechos entre paradas consecutivas têm 0 s no GTFS e recebem o piso de 1 s; 189 paradas não estão em nenhum padrão do dia e ficam só com caminhada. Antes de ir para o relatório, refazer esses números com o script versionado.

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

## Pendências
- **Campos propostos no diagrama de classes que pertencem a contratos de outros donos:** `Linha(id, nome, tipo)` e `leitor_gtfs.ler/validar` (Miguel, P0-DADOS): confirmar quando ele publicar o contrato. ~~`Resultado(dist, pred)` (Thiago)~~ **feito em 05/11:** diagrama com `Resultado(origem, dist, pred, pred_aresta)` e `caminho_arestas`, como na `main`.
- **Plano de desenvolvimento (relatório):** o texto diz que o gancho de pre-commit barra biblioteca de grafo em `src/`; o gancho é da P0-REPO (Caio) e ainda não existe. Conferir antes da versão final.
- **Fundamentação (Thiago e Henrique):** combinar a divisão; a seção continua com `\pendente`.
- ~~**Rede (Miguel):** mandar o protocolo `RedeConstrutores`~~ **feito em 05/11:** o PR #42 publica `Rede.viagens[padrão]` no formato do protocolo; conferido no feed real sem adaptador.
- **Frequências na Rede (PR #42, item 1 da revisão):** viagem com `frequencies.txt` entra em `Rede.viagens` só como a de referência, e a D10 perde embarques (na rede de teste, L2 fica sem embarque na faixa 09:30 a 10:00). O feed real não tem `frequencies.txt`. Pedida mudança ao Miguel em 05/11; conferir a correção antes de aprovar.
- **D8 e o leitor do Miguel:** o leitor do PR #42 descarta a viagem inteira quando os horários decrescem (opção c da D8), então o filtro de negativos dos construtores só age em redes montadas por outro caminho. No feed real há 0 viagens nessa situação; sem efeito hoje, mas registrar na Modelagem se o grupo mantiver as duas regras.
- **Piso de 1 s (Thiago, F-MET):** responder no PR #37 que o piso entrou (`Parametros.peso_minimo_s`).
- **docs/fontes/modelagem.md §3.4:** acrescentada a regra do piso, decidida pelo Henrique em 05/11 (mesmo procedimento de D1 a D7: decisão no GUIA §8 e regra na fonte). Avisar o grupo no PR.
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

### ~~Decisões a tomar~~ Decididas em 05/11/2026: D8 a D11 aceitas pela recomendação; registradas no `docs/GUIA.md` §8 e no `docs/fontes/modelagem.md` §3.4

- **D8. Diferença de horário negativa entre paradas consecutivas.** (a) fica fora da mediana; trecho sem nenhuma diferença válida recebe o piso de 1 s; (b) levantar erro; (c) descartar a viagem inteira. **Recomendo (a):** é erro de cadastro isolado; erro derrubaria a construção da rede inteira, e descartar a viagem jogaria fora os outros trechos válidos dela. O trecho continua existindo porque está na sequência do padrão.
- **D9. Embarque e desembarque nas pontas do padrão.** Sem embarque na última parada e sem desembarque na primeira. **Recomendo:** essas arestas nunca estão num caminho útil e só aumentam o grafo.
- **D10. "Padrão com partida na faixa".** (a) alguma viagem tem o primeiro horário dentro da faixa; (b) alguma viagem passa pela parada dentro da faixa. **Recomendo (a)** por ser a definição de partida e casar com a tabela de intervalos de F-ESPERA, que é por (padrão, faixa). Limitação: ônibus que sai às 08h55 e passa numa parada às 09h20 não dá embarque nessa parada no entrepico.
- **D11. Linha circular (padrão que repete uma parada).** Uma plataforma só por (parada, padrão), com um embarque e um desembarque. **Recomendo:** é o que a chave do contrato `plataforma[(parada, padrão)]` já implica. Limitação: o passageiro pode "dar a volta" e seguir no início do padrão, o que nem sempre é possível na rede real.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Henrique.
### Mudança 29/10/2026: revisão do REQUISITOS.md dispensada (baseline v1.0 em 29/10); próximo passo passa a ser UML e assinaturas.
### Sessão 29/10/2026: rascunho dos diagramas UML globais (classes, componentes, casos de uso) em PlantUML, na branch `feat/P0-MODELO-uml`.
### Sessão 29/10/2026: assinaturas de parametros.py, visoes.py e construtores.py com estado: planejado; diagrama de classes sincronizado; decisões D1 a D7 propostas com recomendação.
### Decisão 29/10/2026: D1 a D7 aceitas pela recomendação; `dados/cache/` no .gitignore.
### PR 29/10/2026: #33 aberto (UML global, contrato dos construtores e decisões D1 a D7).
### Merge 05/11/2026: PR #33 integrado na `main`.
### Decisão 05/11/2026: piso de 1 s nas arestas de viagem e de caminhada (M2 da F-MET), aceito pelo Henrique; registrado no GUIA §8 e no modelagem.md §3.4.
### Sessão 05/11/2026: etapa 2 na branch `feat/P0-MODELO-construtores`: construtores de G_P e G_E, salvar, carregar e `baldeacoes` contra o protocolo `RedeConstrutores`; 33 testes, 243 na suíte; diagrama de classes com `Resultado` atualizado; decisões D8 a D11 propostas.
### PR 05/11/2026: #38 aberto (construtores, piso de 1 s e decisões D8 a D11 propostas).
### Sessão 05/11/2026: seção Modelagem do relatório (v1) na branch `feat/P0-MODELO-relatorio`; figuras `ge-exemplo` e `classes-modelo` em PlantUML.
### PR 05/11/2026: #40 aberto (seção Modelagem do relatório), empilhado sobre o #38.
### Decisão 05/11/2026: D8 a D11 aceitas pela recomendação.
### Sessão 05/11/2026: Etapa 1 v1 na branch `feat/P0-MODELO-etapa1`: Introdução e Plano no relatório, seção 3 do README com o diagrama de classes; diagrama de casos de uso a 200 dpi.
### PR 05/11/2026: #41 aberto (Introdução, Plano e README da Etapa 1), empilhado sobre o #40.
### Revisão 05/11/2026: PR #42 (P0-DADOS) revisado com mudança pedida (frequências fora de `Rede.viagens`); a `Rede` atende `RedeConstrutores` sem adaptador.
### Sessão 05/11/2026: etapa 5 no feed real com a `Rede` do PR #42: G_P em 312,8 ms (V = 9.659, E = 122.732), G_E em 342 a 365 ms por faixa (V = 46.100, E de 206.868 a 208.956).
