# P0-MODELO · Modelagem, UML e construtores de G_P e G_E

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Henrique (@henriquegdc) · **Issue:** #4 · **Visões do grafo:** G_P, G_E
**Depende de:** contratos de P0-GRAFO e P0-DADOS · **Bloqueia:** F-ROTA, F-ESPERA, F-MET, F-EFI, F-RES
**Prazo:** assinaturas 31/10; G_P 02/11; G_E 03/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-GRF-04, RF-GRF-05, RF-GRF-07). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 09/11, Henrique, branches `feat/P0-MODELO-construtores` (#38), `feat/P0-MODELO-relatorio` (#40) e `feat/P0-MODELO-etapa1` (#41): ajustes da revisão do Rafael de 09/11 nos três PRs; branches atualizadas com a `main` por merge; #38, #40 e #41 integrados na `main` nessa ordem, sem aprovação formal no GitHub (revisão do Rafael em comentário; merge decidido pelo Henrique).
- **Onde parou:** etapas 2 e 5 concluídas; etapa 6 com tudo menos a seção do relatório com resultado. Etapa 2: `construir_gp`, `construir_ge`, `salvar`, `carregar` e `VisaoGE.baldeacoes` na `main`, com 46 testes em `tests/modelo` (gabaritos à mão, bordas, grade espacial contra a busca ingênua, ida e volta do pickle); os três módulos com `estado: implementado`. Os construtores leem a Rede pelo protocolo `RedeConstrutores` (paradas, padrões e `viagens[padrão]`); `construir_ge` recebe `esperas[(padrão, faixa)]`, não `intervalos`. Piso de 1 s (M2 da F-MET) aceito e registrado. A `Rede` do PR #42 atende o protocolo sem adaptador; no feed real, G_P sai em 0,31 s e G_E em cerca de 0,35 s por faixa (ver Resultados).
- **Próximo passo:** revisar de novo o PR #42: o Miguel publicou as correções em 08/11 (`d7f0c3e`) e pediu nova revisão. Quando o #42 entrar, etapa 3: teste de integração lendo `dados/rede-teste/` com o `ler()` e conferindo o G_E contra o `GABARITO.md`. Responder ao Thiago que o piso de 1 s entrou (`Parametros.peso_minimo_s`). Versionar a checagem avulsa de Resultados em `benchmarks/` e pôr na Modelagem do relatório o parágrafo de resultado (tempos e tamanhos do G_P e do G_E). Combinar com o Thiago a seção Fundamentação (dona dupla); revisar o rascunho da etapa 6 (Henrique).
- **Arquivos tocados:** `src/transporte/modelo/{parametros,visoes,construtores}.py`, `tests/modelo/{test_construtores,test_visoes}.py`, `docs/diagramas/{classes,classes-modelo,ge-exemplo,atividade-construir-ge}.{puml,png}`, `relatorio/secoes/{modelagem,introducao,plano}.tex`, `relatorio/figuras/{classes-modelo,ge-exemplo,casos-de-uso}.png`, `docs/diagramas/casos-de-uso.{puml,png}` (dpi 200), `README.md` §3, `docs/GUIA.md` §3, §8 e §10, `docs/fontes/modelagem.md` §3.4 (piso e espera provisória), este arquivo.
- **Como testar:** `python -m pytest` (502 em 09/11, 46 de `tests/modelo`); `ruff check`; `python scripts/verificar_imports.py`; diagramas: `java -jar plantuml-1.2026.9.jar -charset UTF-8 -tpng -failfast2 docs/diagramas/*.puml`, copiando para `relatorio/figuras/` os que o relatório usa.
- **Bloqueios:** a etapa 3 depende do merge do PR #42 (P0-DADOS: correções publicadas em 08/11, aguardando nova revisão).

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
| Testes | em andamento | 09/11: 46 verdes em `tests/modelo` (40 dos construtores, 6 das visões): gabarito à mão, bordas, grade contra busca ingênua em 10 sementes, pickle; teste de mutação à mão (05/11): filtro de negativos, piso, deduplicação de embarque e de desembarque e folga da grade derrubam testes. Falta a rede de teste do Miguel |
| Desempenho (tempo medido) | concluído | 05/11: G_P 312,8 ms, G_E 342 a 365 ms por faixa no feed real; ver Resultados |
| Guia (explicação e quiz) | em andamento | 05/11: rascunho de Como funciona e 5 perguntas, copiado para o `docs/GUIA.md` §3 e §10; Henrique revisa |
| Relatório | em andamento | 05/11: Etapa 1 v1 das seções do Henrique, compiladas com MiKTeX 25.12 sem erro nem referência indefinida: Introdução (cerca de 1,1 página, com o diagrama de casos de uso), Modelagem (cerca de 2,5) e Plano (cerca de 0,4); Introdução e Plano somam 1,5, o orçamento das duas. 09/11: ajustes da revisão (Figura 3 na largura do texto e com `esperas`; Plano cita o `heapq` e a NetworkX nos scripts de medição), não compilados nesta sessão porque a máquina não tinha LaTeX; conferir no próximo `latexmk`. Falta a Fundamentação, com o Thiago |
| Vídeo | em andamento | 05/11: rascunho do roteiro; a parte de interface espera o P0-UI |

## Especificação
Construtores de G_P e G_E a partir do modelo normalizado (`docs/fontes/modelagem.md` §3.4). Contrato publicado com `estado: planejado`; o diagrama de classes (`docs/diagramas/classes.png`) mostra as mesmas assinaturas.

| Arquivo | Conteúdo público |
|---|---|
| `src/transporte/modelo/parametros.py` | `FaixaHoraria(nome, inicio_s, fim_s)`, `Parametros(raio_caminhada_m=300, velocidade_caminhada_ms=1.2, espera_padrao_s=300, peso_minimo_s=1, faixas)` |
| `src/transporte/modelo/visoes.py` | `Visao(grafo, nome)`, `VisaoGP`, `VisaoGE` (com `baldeacoes`), constantes de tipo de aresta `VIAGEM`, `CAMINHADA`, `EMBARQUE`, `DESEMBARQUE` |
| `src/transporte/modelo/construtores.py` | `construir_gp(rede, params)`, `construir_ge(rede, faixa, params, esperas)`, `salvar(visao, caminho)`, `carregar(caminho)` |

Complexidade (V paradas, L plataformas, N horários, K pares a até o raio), como nas docstrings: `construir_gp` em O(V + K + N log N) esperado; `construir_ge` em O(V + K + L + N log N) esperado. O V² aparece só no pior caso, com todas as paradas na mesma célula da grade espacial.

## Como funciona e por quê

**O problema.** O GTFS descreve a rede como tabelas: paradas com coordenadas, viagens e o horário de cada viagem em cada parada. Os algoritmos das features precisam de um grafo dirigido e ponderado. Os construtores fazem essa passagem, a partir da `Rede` normalizada da P0-DADOS, para duas visões: G_P (paradas) e G_E (parada × linha). G_L e G_T são de outros donos.

**O que os construtores leem.** Só três coisas da `Rede`, descritas no protocolo `RedeConstrutores`: `paradas` (id, lat, lon), `padroes` (id e sequência de paradas) e `viagens[padrão]`, uma lista de horários por viagem, alinhada com a sequência do padrão. Um padrão é uma linha mais uma sequência exata de paradas (D1). A identidade da viagem importa: para saber quanto o ônibus leva de A a B, é preciso subtrair horários **do mesmo ônibus**, e uma lista de partidas por parada não diz qual horário de B pertence a qual horário de A.

**G_P, passo a passo.**

1. Um vértice por parada, na ordem de `rede.paradas`.
2. Para cada padrão e cada par de paradas consecutivas (a, b), junta as diferenças `horário[b] − horário[a]` de todas as viagens do padrão. Trechos iguais de padrões diferentes vão para a mesma lista; diferenças negativas ficam de fora (D8).
3. Uma aresta VIAGEM a → b por trecho, com peso = mediana da lista (D2) e piso de 1 s. Lista vazia (só havia negativas) dá o piso.
4. Arestas CAMINHADA nos dois sentidos entre paradas a até 300 m, com peso = distância / 1,2 m/s e o mesmo piso.

Exemplo: três viagens levam 300, 360 e 300 s de A a B; a aresta A → B pesa 300 s. Se uma viagem tivesse −500 s (erro de cadastro), a mediana de 60 e 80 seria 70. Duas paradas a 240 m ganham caminhada de 200 s em cada sentido.

**G_E, passo a passo.** Em G_P, continuar no mesmo ônibus e trocar de ônibus custam o mesmo, porque a aresta não sabe em que linha o passageiro está. G_E separa as linhas em **plataformas**, um vértice por (parada, padrão), ligado à parada por embarque e desembarque. Para trocar de linha é preciso desembarcar (0 s), voltar à parada e embarcar de novo, pagando a espera da nova linha (figura `docs/diagramas/ge-exemplo.png`). O diagrama de atividade está em `docs/diagramas/atividade-construir-ge.png`.

1. Um vértice por parada; depois, padrão a padrão, um vértice de plataforma por (parada, padrão), criado uma vez só mesmo que o padrão repita a parada (D11).
2. Se alguma viagem do padrão parte (primeiro horário) dentro da faixa (D10), cria EMBARQUE parada → plataforma em todas as paradas menos a última (D9). Peso: a espera de `esperas[(padrão, faixa)]`, calculada pela F-ESPERA e aplicada sem transformação (H/2 na versão essencial), ou 300 s enquanto a tabela não existe (D6). Até 05/11 o construtor recebia o intervalo H e dividia por 2; a troca deixa a fórmula inteira com a F-ESPERA (GUIA §8).
3. VIAGEM plataforma → plataforma seguinte, com a mediana das diferenças daquele padrão e o piso.
4. DESEMBARQUE plataforma → parada, peso 0, em todas as paradas menos a primeira (D9).
5. CAMINHADA entre paradas, como em G_P.

Com isso, um único Dijkstra soma caminhada, espera, viagem e baldeações, sem penalidade arbitrária por baldeação: ela já custa a espera da nova linha. O número de baldeações de um caminho é o número de arestas de embarque menos um (`VisaoGE.baldeacoes`).

**Caminhada sem O(V²).** Comparar todas as paradas entre si dá 9.659² ≈ 93 milhões de distâncias na rede de BH. A grade espacial projeta as coordenadas em metros e põe cada parada numa célula de lado igual ao raio; duas paradas a até 300 m estão sempre em células vizinhas, então cada parada só é comparada com as 9 células em volta. A projeção usa o cosseno da maior latitude, que encolhe as distâncias leste-oeste, e a célula tem 0,1% de folga; assim nenhum par dentro do raio escapa. Um teste compara a grade com a busca ingênua em 10 redes aleatórias.

**Complexidade.** V paradas, L plataformas (soma dos tamanhos dos padrões), N horários (soma, sobre as viagens, do número de paradas) e K pares a até o raio.

- G_P: O(V) para os vértices; cada horário entra em no máximo uma diferença, então juntar as listas custa O(N) e as medianas, que ordenam, O(N log N); a grade custa O(V + K) esperado, porque cada célula tem um número limitado de paradas quando a densidade é limitada. Total O(V + K + N log N); espaço O(V + E). No pior caso, todas as paradas na mesma célula, a grade degenera em O(V²).
- G_E: o mesmo, mais O(L) plataformas e no máximo 3 arestas por plataforma, e O(viagens) por padrão para testar a faixa. Total O(V + K + L + N log N).
- `salvar` e `carregar`: O(V + E).

Medido em 05/11 no feed real (ver Resultados): G_P com 9.659 vértices e 122.732 arestas em 312,8 ms; G_E com 46.100 vértices e cerca de 208 mil arestas em 342 a 365 ms por faixa.

**Decisões e alternativas descartadas.** Estão na tabela do `docs/GUIA.md` §8 (D1 a D11 e o piso). As que mais mudam o resultado:

- **Mediana, não média (D2):** um horário cadastrado errado desloca a média, mas quase não move a mediana.
- **Piso de 1 s (M2):** o GTFS arredonda horários, e no feed real há 1.949 diferenças de 0 s entre paradas consecutivas de uma mesma viagem, e 43 arestas de viagem do G_P terminam no piso (mediana de até 1 s). Peso 0 entre paradas distintas não é tempo real e quebra a contagem de caminhos mínimos do Brandes (F-MET). O desembarque continua com 0, porque desembarcar não leva tempo e não cria empate entre caminhos.
- **G_E por faixa:** a espera muda ao longo do dia, então cada faixa tem seu G_E. Alternativa descartada: um G_E só, com a espera média do dia, que esconderia a diferença entre pico e entrepico (pergunta 2).
- **Salvar com pickle (D7):** uma linha de código; o arquivo é cache local da ferramenta e nunca vem de fora, que é o único caso em que pickle é inseguro.

**Limitações.**

- O tempo de viagem de um trecho é um só para o dia todo (D2); o trânsito do pico não aparece.
- Ônibus que sai às 08h55 e passa numa parada às 09h20 não dá embarque nela no entrepico (D10).
- Numa linha circular, o passageiro pode "dar a volta" e seguir no início do padrão (D11); no feed real, 387 dos 698 padrões repetem alguma parada.
- Cada variante de itinerário é um padrão com espera própria (D1), o que superestima a espera de quem aceitaria qualquer variante da mesma linha.
- Caminhada em linha reta, sem ruas.

## Perguntas de verificação

1. **Por que G_E tem vértices de plataforma?** Para que trocar de linha custe alguma coisa: a aresta de G_P não sabe em que linha o passageiro está. Em G_E, trocar obriga a desembarcar, voltar à parada e pagar um novo embarque, que carrega a espera da nova linha.
2. **Como se conta o número de baldeações de um trajeto em G_E?** Embarques no caminho menos um (`VisaoGE.baldeacoes`); um trajeto só a pé tem 0.
3. **Por que o tempo entre paradas é a mediana, e o que acontece com uma diferença negativa?** A mediana resiste a horários errados de cadastro. Diferença negativa fica fora; se não sobrar nenhuma, o trecho recebe o piso de 1 s, porque ele existe na sequência do padrão (D8).
4. **Por que montar a caminhada não custa O(V²)?** A grade espacial põe cada parada numa célula do tamanho do raio, e cada parada só é comparada com as 9 células vizinhas: O(V + K) esperado.
5. **Por que viagem e caminhada têm piso de 1 s, mas o desembarque fica com 0?** Peso 0 entre paradas distintas é artefato do arredondamento do GTFS e cria empates que quebram a contagem de caminhos do Brandes. Desembarcar não leva tempo e só liga a plataforma à própria parada.

## Critérios de aceite
- [ ] RF-GRF-04: Construir a visão G_P (paradas) a partir do modelo normalizado
- [ ] RF-GRF-05: Construir a visão G_E (parada × linha) com arestas de embarque, viagem, desembarque e caminhada
- [x] RF-GRF-07: Salvar e carregar grafos construídos, para não reprocessar o GTFS a cada execução (05/11: `salvar` e `carregar` com pickle, testados)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante (09/11: #38, #40 e #41 integrados, mas sem aprovação formal no GitHub; a revisão do Rafael ficou em comentário)
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde (09/11: 502 na suíte)
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (não há equivalente no NetworkX para a construção; a grade é comparada com a busca ingênua)
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature (05/11, em Como funciona)
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina (05/11)
- [ ] Página ou bloco na interface funcionando com o dataset real
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/` (05/11: `atividade-construir-ge`)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md` (05/11, rascunho; Henrique revisa)
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
| 5 | Tempo medido na rede real e complexidade justificada | concluída em 05/11 (tempo em Resultados; complexidade em Como funciona) |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | em andamento: rascunho de 05/11 (Como funciona, perguntas, `atividade-construir-ge`, GUIA §3 e §10, roteiro); falta o parágrafo de resultado na Modelagem do relatório e a revisão do Henrique |

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

Do mesmo feed, numa checagem avulsa em 05/11 (script de revisão do PR #42, não versionado): no G_E do pico da manhã, 110.178 das 208.956 arestas são de caminhada, 36.385 de viagem, 36.121 de desembarque e 26.272 de embarque; 387 dos 698 padrões repetem alguma parada (D11); há 1.949 diferenças de 0 s entre paradas consecutivas de uma mesma viagem (contadas por viagem); ficam no piso de 1 s 43 das 12.554 arestas de viagem do G_P e 181 das 36.385 do G_E do pico da manhã, e nenhuma de caminhada; 189 paradas não estão em nenhum padrão do dia e ficam só com caminhada. Antes de ir para o relatório, refazer esses números com o script versionado.

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

Rascunho de 05/11 (Henrique revisa; a parte de interface espera o P0-UI):

1. **Problema (25 s):** o GTFS é tabela, os algoritmos precisam de grafo. Mostrar `stop_times.txt` ao lado do G_E de exemplo (`ge-exemplo.png`): as mesmas viagens viram vértices e arestas.
2. **Na ferramenta (35 s):** escolher a faixa horária e mostrar no mapa as paradas e as arestas de caminhada de um bairro; trocar de faixa e mostrar um padrão que deixa de ter embarque.
3. **Como funciona (50 s):** plataforma por (parada, padrão) e por que baldear custa a espera; mediana das viagens com o piso de 1 s; grade espacial da caminhada em vez de comparar todos os pares. Complexidade: O(V + K + L + N log N).
4. **Resultado e limitação (30 s):** feed real em cerca de 0,3 s por visão (V = 46.100 no G_E); limitações: um tempo de viagem para o dia todo e a regra de partida na faixa (D10).

## Pendências
- **Campos propostos no diagrama de classes que pertencem a contratos de outros donos:** `Linha(id, nome, tipo)` e `leitor_gtfs.ler/validar` (Miguel, P0-DADOS): confirmar quando ele publicar o contrato. ~~`Resultado(dist, pred)` (Thiago)~~ **feito em 05/11:** diagrama com `Resultado(origem, dist, pred, pred_aresta)` e `caminho_arestas`, como na `main`.
- ~~**Plano de desenvolvimento (relatório):** o texto diz que o gancho de pre-commit barra biblioteca de grafo em `src/`; o gancho é da P0-REPO (Caio) e ainda não existe. Conferir antes da versão final.~~ **feito em 09/11:** o hook do #43 existe e barra bibliotecas de grafo e o `heapq` em `src/`; o texto cita os dois.
- **Fundamentação (Thiago e Henrique):** combinar a divisão; a seção continua com `\pendente`.
- ~~**Rede (Miguel):** mandar o protocolo `RedeConstrutores`~~ **feito em 05/11:** o PR #42 publica `Rede.viagens[padrão]` no formato do protocolo; conferido no feed real sem adaptador.
- **Frequências na Rede (PR #42, item 1 da revisão):** viagem com `frequencies.txt` entra em `Rede.viagens` só como a de referência, e a D10 perde embarques (na rede de teste, L2 fica sem embarque na faixa 09:30 a 10:00). O feed real não tem `frequencies.txt`. Pedida mudança ao Miguel em 05/11; correção publicada em 08/11 (`d7f0c3e`); conferir na nova revisão antes de aprovar.
- **D8 e o leitor do Miguel:** o leitor do PR #42 descarta a viagem inteira quando os horários decrescem (opção c da D8), então o filtro de negativos dos construtores só age em redes montadas por outro caminho. No feed real há 0 viagens nessa situação; sem efeito hoje, mas registrar na Modelagem se o grupo mantiver as duas regras.
- **Piso de 1 s (Thiago, F-MET):** responder ao Thiago que o piso entrou (`Parametros.peso_minimo_s`). Na aprovação do #37 (05/11) a resposta ficou para depois do registro no P0-MODELO, e o #37 já foi integrado; ainda não respondido.
- ~~**docs/fontes/modelagem.md §3.4:** acrescentada a regra do piso, decidida pelo Henrique em 05/11 (mesmo procedimento de D1 a D7: decisão no GUIA §8 e regra na fonte). Avisar o grupo no PR.~~ **feito:** aviso ao grupo na descrição do #38. Em 09/11 a linha "Espera provisória" passou a citar a tabela de esperas da F-ESPERA, a pedido do revisor do #38.
- **Checagem avulsa de Resultados:** os números de arestas por tipo, padrões circulares e arestas no piso vieram de um script não versionado. Passar o script para `benchmarks/` (por exemplo, `benchmarks/estatisticas_ge.py`) e refazer os números com o comando registrado antes de levá-los ao relatório (opcional da revisão do #41).
- **Figuras do relatório (opcionais da revisão do #40 e do #41):** Figura 1 (casos de uso) a 0,85 da largura, conferindo no PDF se a Introdução continua em 1 página; Figura 2 (`ge-exemplo`) em duas linhas, L1 em cima e L2 embaixo, para os rótulos das arestas crescerem.
- **Figura 3 (`classes-modelo`) no PDF:** o PNG de 09/11 tem 2.506 px de largura a 200 dpi e fonte 14; na largura do texto (15 cm) a letra sai com cerca de 6,6 pt (estimativa pela escala, sem compilar). Conferir no próximo `latexmk`; se ficar pequena, estreitar o desenho (pacote `dados` abaixo de `modelo`) ou enxugar o recorte.
- ~~**Decisões de modelagem embutidas no diagrama**~~ **decidido em 29/10/2026:** mantidas e registradas no `docs/GUIA.md` §8. Texto original: hierarquia `Visao` com uma subclasse por visão; `construir_ge` recebe a tabela de intervalos de F-ESPERA (espera constante até 06/11); salvar e carregar ficam nos construtores (RF-GRF-07).
- ~~**Contrato da Rede (Miguel):** `partidas[(padrão, parada)] -> list[int]` perde a identidade da viagem. Para calcular o tempo entre paradas consecutivas (D2) é preciso saber qual horário da parada seguinte pertence à mesma viagem. Pedir ao Miguel que a Rede guarde as viagens (por exemplo `viagens[padrão] -> list[list[int]]`, uma lista de horários por viagem, na ordem das paradas) ou garanta o mesmo número e a mesma ordem de horários em todas as paradas do padrão.~~ **feito:** o #42 implementa `viagens[padrão]` nesse formato.

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
### Sessão 05/11/2026: etapa 6 em rascunho: Como funciona e por quê, 5 perguntas de verificação, diagrama `atividade-construir-ge`, `docs/GUIA.md` §3 e §10 e roteiro do vídeo; arestas no piso de 1 s contadas no feed real (43 de 12.554 de viagem no G_P).
### Contrato 05/11/2026: `construir_ge` passa a receber `esperas[(padrão, faixa)]` (a espera já calculada pela F-ESPERA) em vez de `intervalos` (H, dividido por 2 no construtor), para a F-ESPERA aplicar a fórmula de intervalo irregular (RF-ESP-02); decisão do Henrique, registrada no GUIA §8; falta avisar o Miguel (F-ESPERA).
### Aviso 05/11/2026: Miguel avisado na descrição do #38 de que `construir_ge` recebe `esperas`, não `intervalos`.
### Revisão 09/11/2026: Rafael revisa #38, #40 e #41 em comentário: código pronto; pede corrigir a espera provisória da `modelagem.md`, os diagramas que ainda mostravam `intervalos`, a legibilidade da Figura 3, duas frases do Plano, este arquivo e as descrições, e atualizar as branches com a `main`.
### Decisão 09/11/2026: na revisão do #38, o grupo (pelo Rafael) dá como aprovados o piso de 1 s e as decisões D8 a D11.
### Merge 09/11/2026: PR #38 integrado na `main` (`d4a696b`), sem aprovação formal no GitHub (decisão do Henrique).
### Sessão 09/11/2026: ajustes da revisão: `modelagem.md` §3.4 com a tabela de esperas; `construir_ge` confere as paradas antes de ignorar padrão de uma parada (mais 1 teste); `classes-modelo` e `atividade-construir-ge` com `esperas`; Figura 3 na largura do texto; Plano com o `heapq` e a NetworkX nos scripts de medição; GUIA §10 em ordem de seção; #40 e #41 atualizados com a `main` por merge; 502 testes na suíte, hook verde.
### Sessão 09/11/2026: `classes-modelo.png` (duas cópias) e `atividade-construir-ge.png` regenerados com o PlantUML 1.2026.9, agora com `esperas`; base do #40 e do #41 trocada para a `main`; descrições atualizadas.
### Merge 09/11/2026: PRs #40 e #41 integrados na `main`, nessa ordem, sem aprovação formal no GitHub (decisão do Henrique).
