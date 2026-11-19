# F-BALD-2 · Menos baldeações contra mais rápido

**Período:** 2 · Desejáveis (12/11 a 15/11) · **Classe:** desejável
**Dono:** Rafael (@Rafael-Fonseca1510) · **Issue:** #15 · **Visões do grafo:** G_L, G_E
**Depende de:** F-BALD (`menos_baldeacoes`, implementado), F-ROTA (`trajeto_mais_rapido`, implementado), F-ESPERA (`calcular_esperas`, implementado) · **Bloqueia:** F-BALD-OPC
**Prazo:** 15/11 (feita em 17/11, depois do congelamento, com exceção aprovada pelo grupo; ver `docs/GUIA.md` §8)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-BAL-03). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 19/11, Rafael, branch `feat/F-BALD-2-comparacao`, PR #55.
- **Onde parou:** etapas 1 a 6 feitas e revisadas: `comparar_baldeacoes` e `mais_rapido_com_limite`, 50 testes novos e 3 na página, bloco na página Baldeações, medição no feed real, diagrama, guia, seção do relatório e roteiro. Em 19/11: decisões C1 a C4 aceitas pelo Rafael e registradas no `docs/GUIA.md` §8, junto com a exceção ao congelamento aprovada pelo grupo; marcas de rascunho retiradas; branch refeita sobre a `main` com a F-RES (#53) e a F-MET (#54), com o `GUIA.md` na ordem §5.3, F-BALD-2, §5.4 e §5.6.
- **Próximo passo:** aprovação do PR #55 (revisão do Thiago) e merge com `Closes #15`. Depois, gravar o trecho do vídeo (roteiro abaixo) e combinar com o Henrique o `_trechos` da F-ROTA (ver Pendências).
- **Arquivos tocados:** `src/transporte/algoritmos/comparacao_baldeacoes.py`, `src/transporte/interface/paginas/baldeacoes.py`, `tests/algoritmos/test_comparacao_baldeacoes.py`, `tests/integracao/test_integracao_comparacao_baldeacoes_rede_teste.py`, `tests/interface/test_pagina_baldeacoes.py`, `benchmarks/medir_comparacao_baldeacoes.py`, `docs/diagramas/atividade-comparar-baldeacoes.{puml,png}`, `relatorio/secoes/F-BALD-2.tex`, `relatorio/secoes/F-BALD.tex` (uma frase), `docs/GUIA.md` (§5.3, §8 e §10), `docs/plano-de-desenvolvimento/features/feature-F-BALD.md` (pendência riscada), este arquivo.
- **Como testar:** `pytest tests/algoritmos/test_comparacao_baldeacoes.py tests/integracao/test_integracao_comparacao_baldeacoes_rede_teste.py tests/interface/test_pagina_baldeacoes.py`; `ruff check`. Medição: `PYTHONPATH=src python benchmarks/medir_comparacao_baldeacoes.py dados/brutos/bhtrans.zip`.
- **Bloqueios:** nenhum. O grupo aprovou a exceção ao congelamento de 15/11 para a F-BALD-2 (`docs/GUIA.md` §8).

## Objetivo
Menos baldeações contra mais rápido. Para quem prefere trocar menos de ônibus, mostra quanto tempo isso custa. Fecha:

- **RF-BAL-03** (D): Comparar o trajeto de menos baldeações com o mais rápido: tempo a mais contra baldeações evitadas

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | implementado | 17/11: `mais_rapido_com_limite` (Dijkstra com os embarques no estado) e `comparar_baldeacoes`, `estado: implementado` |
| Modelo e dados | implementado | 17/11: usa G_E (`construir_ge`, com as esperas da F-ESPERA) e G_L (`construir_gl`) da mesma faixa; integração com `dados/rede-teste` pelo `ler()` (5 testes) e com o feed real (Resultados) |
| Interface | implementado | 17/11: bloco "Menos baldeações contra mais rápido" na página Baldeações, numa faixa (3 testes, um com `AppTest`); conferido no feed real (Resultados) |
| Testes | implementado | 17/11: 45 testes do algoritmo (gabarito à mão, bordas, falhas e NetworkX num grafo em camadas em 15 redes aleatórias, 720 buscas) e 5 de integração |
| Desempenho (tempo medido) | implementado | 17/11: comparação em 212,9 ms por par em média (máximo 1.015,5 ms) e busca com limite em 304,9 ms nos 40 pares em que roda, no G_E do pico; ver Resultados |
| Guia (explicação e quiz) | implementado | 17/11: Como funciona e 5 perguntas, copiados para o `docs/GUIA.md` §5.3 e §10; revisados pelo Rafael em 19/11 |
| Relatório | implementado | 17/11: `relatorio/secoes/F-BALD-2.tex`, com resultado, complexidade e limitação; revisado pelo Rafael em 19/11 |
| Vídeo | em andamento | 17/11: roteiro abaixo; gravação no P3 |

## Especificação

`src/transporte/algoritmos/comparacao_baldeacoes.py`:

| Símbolo | Conteúdo |
|---|---|
| `mais_rapido_com_limite(ge, origem, destino, max_baldeacoes) -> Trajeto \| None` | Mais rápido no G_E com no máximo `max_baldeacoes` baldeações; devolve o `Trajeto` da F-ROTA. None se nenhum trajeto respeita o limite; KeyError para parada inexistente; ValueError para limite negativo; TypeError para limite que não é int. Tempo O((k + 2)(V + E) log((k + 2) V)); espaço O((k + 2)(V + E)) |
| `ComparacaoBaldeacoes(mais_rapido, menos_baldeacoes, rapido_com_menos_baldeacoes)` | `tempo_a_mais_s` (>= 0), `baldeacoes_evitadas` (>= 0), `tempo_por_baldeacao_evitada_s` (None se não evita nenhuma) |
| `comparar_baldeacoes(ge, gl, origem, destino) -> ComparacaoBaldeacoes \| None` | G_E e G_L da mesma faixa (senão ValueError); None se não há trajeto no G_E ou na G_L. Tempo: F-ROTA + F-BALD + o limite, quando roda |

`src/transporte/interface/paginas/baldeacoes.py` (acréscimos): `ge_da_faixa(rede, faixa, cache)`, `tabela_comparacao(rede, comparacao)` e o bloco da comparação no `render(rede)`.

Algoritmo: Dijkstra (HeapMin do núcleo) sobre os estados (vértice de G_E, embarques feitos), sem montar o grafo em camadas (decisão C2).

## Como funciona e por quê

**O problema.** A F-BALD diz o menor número k de baldeações entre duas paradas, mas não quanto tempo isso custa; a F-ROTA diz o trajeto mais rápido, que pode trocar de ônibus mais vezes. O RF-BAL-03 pede o meio-termo: o **tempo a mais** para fazer menos baldeações e quantas baldeações isso **evita**.

**As visões: G_L e G_E.** O k vem da G_L (F-BALD), porque é ela que a página mostra e é nela que o mínimo é exato pelas regras da F-BALD. O tempo vem do G_E (F-ROTA), o único com espera e viagem. Os dois são da mesma faixa (decisão B4 da F-BALD), e o G_E usa as esperas H/2 da F-ESPERA, as mesmas da página Espera (C4). Todo trajeto da G_L existe no G_E da mesma faixa, porque os dois usam o mesmo raio de caminhada e a mesma regra D10 para as linhas que circulam; o G_E ainda permite encadear caminhadas e seguir numa linha circular sem reembarcar. Por isso o mais rápido com até k baldeações sempre existe quando a F-BALD acha trajeto.

**Que tempo comparar (C1).** Entre os trajetos com k baldeações, a F-BALD escolhe por caminhada e tamanho da última perna (B5), sem olhar o tempo. Cronometrar esse trajeto inflaria o custo. O custo honesto é o do **mais rápido entre os de até k baldeações**. Exemplo (teste `test_escolhe_o_mais_rapido_entre_os_de_menos_baldeacoes`), com espera de 300 s em todo embarque e paradas A, B, C e D longe umas das outras: Q1 = A → B (60 s), Q2 = B → C (60 s), Q3 = C → D (60 s), R1 = A → C (1.000 s) e R3 = B → D (700 s). O mais rápido de A a D é Q1, Q2 e Q3: 3 × 300 + 180 = 1.080 s, com 2 baldeações. O mínimo é 1 baldeação, com Q1 + R3 (300 + 60 + 300 + 700 = 1.360 s) ou R1 + Q3 (300 + 1.000 + 300 + 60 = 1.660 s). O tempo a mais é 280 s para evitar 1 baldeação, não 580 s.

**Passo a passo** (`comparar_baldeacoes(ge, gl, origem, destino)`; diagrama de atividade em `docs/diagramas/atividade-comparar-baldeacoes.png`):

1. G_L e G_E de faixas diferentes (ou a G_L do dia inteiro) dão ValueError.
2. Roda a F-ROTA (mais rápido) e a F-BALD (mínimo k). Se um dos dois não acha trajeto, devolve None.
3. Se o mais rápido faz até k baldeações, ele mesmo é a resposta: tempo a mais 0, nada evitado.
4. Senão, `mais_rapido_com_limite(ge, origem, destino, k)`: um Dijkstra em que o estado é (vértice, embarques feitos). A aresta de embarque (parada → plataforma) leva de e para e + 1 embarques; as outras mantêm e; estado com mais de k + 1 embarques não existe. Ao tirar do heap o estado (u, e), ele é descartado se u já foi fechado com menos embarques; senão, u fica fechado com e embarques e as arestas dele são relaxadas.
5. Quando o destino é fechado, os trechos saem pela mesma reconstrução da F-ROTA, então se leem e se desenham igual.

**Por que é exato.** Sem o descarte, é o Dijkstra comum num grafo com k + 2 cópias do G_E, uma por número de embarques, ligadas só pelas arestas de embarque: o primeiro estado do destino que sai do heap é o de menor tempo com até k + 1 embarques. O descarte não perde nada: se u já foi fechado com e' < e embarques, isso aconteceu com tempo menor ou igual (o Dijkstra fecha em ordem de tempo), e tudo o que se faz a partir de (u, e) se faz a partir de (u, e') sem mais embarques. Os testes conferem o resultado contra o NetworkX num grafo em camadas explícito, montado à parte, em 15 redes aleatórias com caminhada e linhas circulares: 720 buscas, com limite de 0 a 3, sem divergência. No feed real, as 40 buscas com limite dos 200 pares sorteados também coincidiram com o NetworkX.

**Complexidade.** V e E do G_E, k o limite. Há (k + 2) V estados, e cada um relaxa as arestas do seu vértice: tempo O((k + 2)(V + E) log((k + 2) V)) no pior caso, com o heap binário do núcleo; espaço O((k + 2)(V + E)), pelos vetores dos estados e pelas entradas repetidas no heap (inserção preguiçosa). Na prática cada vértice fecha poucas vezes, por causa do descarte, e a busca para quando o destino fecha. A comparação inteira soma a F-ROTA (O((V + E) log V)), a F-BALD (O(r (V_L + E_L + T) + s)) e o limite, quando roda. No feed real (ver Resultados), no G_E do pico com V = 46.100 e E = 208.956, a comparação inteira levou 212,9 ms por par em média, e a busca com limite, nos 40 pares em que rodou, 304,9 ms.

**Decisões e alternativas descartadas** (C1 a C4, propostas em 17/11 e aceitas pelo Rafael em 19/11):

- **C1. O tempo do trajeto de menos baldeações é o do mais rápido no G_E com até k baldeações.** Alternativas: (a) cronometrar no G_E o trajeto que a F-BALD devolve, como sugeria a pendência da F-BALD, descartada porque o desempate da F-BALD (B5) não olha o tempo e inflaria o custo (no exemplo acima, 580 s em vez de 280 s); (b) penalidade fixa por baldeação no Dijkstra, descartada porque a modelagem não usa penalidade (docs/fontes/modelagem.md, "Penalidade fixa por baldeação: Nenhuma") e porque nenhuma penalidade garante chegar ao mínimo k.
- **C2. Dijkstra com o número de embarques no estado, com camadas implícitas e descarte de estado dominado.** Alternativas: (a) montar o G_E em k + 2 camadas a cada consulta, descartada por copiar centenas de milhares de arestas por consulta no feed real; (b) busca lexicográfica (baldeações, tempo) no G_E, descartada porque acharia o mínimo de baldeações do G_E, com caminhadas encadeadas, e não o da G_L que a página mostra.
- **C3. O limite k vem da G_L, mas a busca no G_E encadeia caminhadas, como a F-ROTA.** Se o mais rápido já faz até k baldeações, ele é a resposta. Assim os dois trajetos comparados seguem o mesmo modelo de tempo, e tempo a mais e baldeações evitadas nunca ficam negativos. Consequência: o mais rápido pode fazer **menos** baldeações que o k da G_L, andando mais de 300 m em caminhadas seguidas (teste `test_caminhadas_encadeadas_no_g_e_fazem_menos_que_o_minimo_da_g_l`); a página explica esse caso. Alternativa: restringir a caminhada a uma por vez no G_E, com mais um campo no estado, descartada porque mudaria o modelo de tempo da F-ROTA só para o trajeto limitado.
- **C4. Comparação só numa faixa, com o G_E montado com as esperas da F-ESPERA, num bloco da página Baldeações.** O tempo depende das esperas e das linhas que circulam na faixa; no "dia inteiro" a página pede uma faixa. As esperas H/2 são as da página Espera (`calcular_esperas(estimar_intervalos(rede, params))`), e não os 300 s fixos. O bloco fica na página Baldeações, logo abaixo do trajeto da F-BALD, em vez de uma página nova.

**Limitações.**

- Mostra um ponto da troca entre tempo e baldeações (com k baldeações), não todos os trajetos não dominados; isso é a F-BALD-OPC (RF-BAL-04). O `mais_rapido_com_limite` já serve de base para ela: chamado com k, k + 1, ..., dá a fronteira.
- Herda as limitações da F-ROTA (espera média H/2, faixa fixa pela saída, sem quadro de horários) e da F-BALD (caminhada em linha reta, só entre paradas).
- Pelo C3, o mais rápido pode fazer menos baldeações que o mínimo da G_L, e aí nada é evitado.
- As linhas do trajeto limitado podem diferir das do mapa da F-BALD, porque lá o critério é só o número de baldeações; a página avisa.
- Reaproveita `_trechos` da F-ROTA, que é privada (ver Pendências).

## Perguntas de verificação

1. **Por que o tempo do trajeto de menos baldeações não é o do trajeto que a F-BALD devolve?** Porque a F-BALD escolhe entre os de k baldeações sem olhar o tempo. O custo de evitar baldeações é o do mais rápido entre eles (C1).
2. **O que guarda o estado do Dijkstra da F-BALD-2?** O vértice do G_E e quantos embarques já foram feitos. Embarcar soma um; acima de k + 1 embarques o estado não existe.
3. **Quando um estado é descartado?** Quando o vértice já foi fechado com menos embarques: esse outro chegou antes, ou junto, e tudo o que se faz a partir do descartado se faz a partir dele.
4. **Por que as baldeações evitadas podem ser zero mesmo com o mais rápido fazendo baldeações?** Porque ele pode já ter o mínimo k, ou até menos que k, encadeando caminhadas no G_E (C3).
5. **Por que a comparação só aparece numa faixa?** Porque o tempo depende das esperas e das linhas que circulam na faixa, e o G_E existe só por faixa (C4).

## Critérios de aceite
- [x] RF-BAL-03: Comparar o trajeto de menos baldeações com o mais rápido: tempo a mais contra baldeações evitadas (17/11: `comparar_baldeacoes`, com o bloco na página Baldeações; 200 de 200 pares do feed real comparados, 0 divergências contra o NetworkX nas 40 buscas com limite)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante (exceção ao congelamento aprovada pelo grupo; PR #55 em revisão)
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde (17/11: 779 testes fora do OneDrive; ver Pendências)
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (17/11: 50 testes; NetworkX num grafo em camadas, porque ele não tem o Dijkstra com limite de embarques)
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature (17/11, em Como funciona)
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina (17/11)
- [x] Página ou bloco na interface funcionando com o dataset real (17/11: bloco na página Baldeações, conferido no feed real)
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/` (17/11: `atividade-comparar-baldeacoes`)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md` (17/11; revisadas em 19/11)
- [ ] O revisor do PR consegue explicar o que o código faz
- [x] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação (17/11: sem figura própria, ver Pendências)
- [x] Roteiro do vídeo escrito no arquivo da feature (17/11)
- [ ] Arquivo da feature atualizado: retomada ("concluída"), status, pendências e timeline (fecha com o merge)

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | concluída em 17/11: publicada e implementada na mesma sessão; nenhum outro integrante consome estas assinaturas (só a F-BALD-OPC, do Rafael) |
| 2 | Algoritmo com testes de corretude | concluída em 17/11: 45 testes |
| 3 | Integração com a visão do grafo e com os dados reais | concluída em 17/11: rede de teste (5 testes) e feed real |
| 4 | Página na interface | concluída em 17/11: bloco na página Baldeações |
| 5 | Tempo medido na rede real e complexidade justificada | concluída em 17/11 |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | concluída em 17/11; revisada pelo Rafael em 19/11 |

## Resultados para o relatório
_Todo número vem com o comando que o gerou._

**Comparação no feed real, 17/11/2026.** Comando: `PYTHONPATH=src python benchmarks/medir_comparacao_baldeacoes.py dados/brutos/bhtrans.zip`, na `feat/F-BALD-2-comparacao` (sem commit, sobre a `main` em `8138604`). Feed: o mesmo instantâneo da F-BALD, SHA-256 `459f3a5892e57d10b11f9a74c543ac16c22661867c7d2296352ec17338935707`; serviço de 04/11/2026, 9.659 paradas e 698 padrões. Máquina: Intel Core i5-1235U (10 núcleos, 12 threads), 15,7 GB, Windows 11, Python 3.12.10.

| Medida | Valor |
|---|---|
| Visões do pico da manhã | G_E (com as esperas H/2 da F-ESPERA): V = 46.100, E = 208.956; G_L: V = 501, E = 85.606 |
| Pares | 200 sorteados com a semente 2026, os mesmos da F-ROTA e da F-BALD |
| `comparar_baldeacoes`, cada par com `medir`, n = 3 | média 212,9 ms, mediana 157,4 ms, p95 633,9 ms, máximo 1.015,5 ms |
| Com comparação | 200 de 200 |
| Mais rápido já com até k baldeações | 160 de 200; em 36 deles, com menos baldeações que o mínimo da G_L, por caminhada encadeada (C3) |
| Busca com limite (`mais_rapido_com_limite`, `medir`, n = 3) | rodou em 40 pares: média 304,9 ms, mediana 329,9 ms, máximo 720,5 ms |
| Evitam baldeação | 40 de 200: 36 evitam 1 baldeação e 4 evitam 2 |
| Tempo a mais, nos 40 | mediana 1,5 min, média 2,8 min, máximo 14,5 min; 3 % do tempo do mais rápido, na mediana |
| Conferência com `nx.single_source_dijkstra_path_length` num grafo em camadas montado à parte | 0 divergências nas 40 buscas com limite |

Exemplos do mesmo comando, listados à parte com os mesmos pares (todos no pico da manhã):

- Par 18, Rua Curitiba 1026 (14788909) → Rua Gentil Portugal Do Brasil 54 (14791748): o mais rápido usa 3054 → 30 → 3053 em 44,2 min, com 2 baldeações; a 3053 direta leva 45,6 min. Evita 2 baldeações por 1,4 min.
- Par 125, Avenida Otacilio Negrao De Lima 2210 (14787137) → Rod Anel Rodoviario Celso Mello Azevedo 3258 (14784540): o mais rápido usa 67 → 8151 → 3050 em 59,4 min; com 1 baldeação, 5106 → 3050 em 73,9 min. Evitar 1 baldeação custa 14,5 min, o maior tempo a mais dos 200.
- Par 10, 14784277 → 14792298: o mínimo da G_L é 1 baldeação, e o mais rápido com até 1 (65 → 9501, 66,3 min) evita 2 das 3 do mais rápido (66,1 min) por 0,2 min.

**Página no feed real (`AppTest`), 17/11.** Par 18, faixa pico da manhã, sem exceção. Métricas: "Baldeações 0, Ônibus 1, Trechos a pé 1" (F-BALD) e "Tempo a mais 1.4 min, Baldeações evitadas 2, Por baldeação evitada 0.7 min" (F-BALD-2); tabela com os dois trajetos (44,2 e 45,6 min). A legenda informou "Comparação em 336 ms". Uma observação, não medição com `medir`: o rerun que monta a G_L e o G_E do pico levou 1,9 s, e o seguinte, com as duas prontas, 0,4 s.

Limitações observadas: o pior caso da comparação (1.015,5 ms) passa um pouco de 1 s, o limite que o RNF-05 fixa para a consulta de trajeto da F-ROTA; a média fica em 213 ms. Em 36 dos 200 pares o mais rápido faz menos baldeações que o mínimo da G_L, porque encadeia caminhadas (C3).

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

Pode entrar como continuação do trecho da F-BALD:

1. **Problema (20 s):** a página Baldeações diz o mínimo de trocas, mas quanto tempo isso custa? Quem quer trocar menos precisa saber o preço.
2. **Na ferramenta (40 s):** na mesma página, escolher a faixa pico da manhã. Mostrar o bloco "Menos baldeações contra mais rápido": tempo a mais, baldeações evitadas e a tabela com os dois trajetos (tempo a pé, espera, ônibus e linhas). Par sugerido: Rua Curitiba 1026 → Rua Gentil Portugal do Brasil 54. O mais rápido faz 3054 → 30 → 3053 em 44,2 min; a 3053 direta leva 45,6 min: evita 2 baldeações por 1,4 min.
3. **Como funciona (40 s):** o k vem da G_L; o tempo, do G_E. Não basta cronometrar o trajeto da F-BALD: o exemplo Q1 + R3 contra R1 + Q3 (280 s, não 580 s). O Dijkstra com os embarques no estado e o descarte dos dominados. Complexidade O((k + 2)(V + E) log((k + 2) V)).
4. **Resultado e limitação (30 s):** em 200 pares do pico da manhã, o mais rápido já tinha o mínimo de baldeações em 160; nos outros 40, evitar baldeação custou 1,5 min na mediana e até 14,5 min. A comparação leva 213 ms por par, conferida com o NetworkX. Limitação: um ponto da troca, não a fronteira inteira (F-BALD-OPC).

## Pendências
- ~~**Congelamento de 15/11 (grupo)**~~ **resolvido:** a F-BALD-2 foi feita em 17/11, depois do congelamento do código (plano-de-projeto §7.1 e §7.3). O grupo aprovou a exceção; registrada no `docs/GUIA.md` §8 em 19/11.
- ~~**Rafael (dono): revisar as decisões C1 a C4 e os rascunhos**~~ **resolvido em 19/11:** C1 a C4 aceitas sem mudança; Como funciona, perguntas, seção do relatório e roteiro revisados; marcas de rascunho retiradas.
- **F-ROTA (Henrique):** `comparacao_baldeacoes.py` importa `_trechos` de `algoritmos/trajeto.py`, que é privada, para os trechos saírem iguais aos da F-ROTA. Pedir ao Henrique para torná-la pública (por exemplo, `trechos_do_caminho(ge, arestas)`) ou registrar que o import é aceito, como a F-BALD faz com `_pares_caminhada` do P0-MODELO.
- **Figura do relatório:** a seção não tem figura própria (o orçamento da seção 7 é de 4 páginas para todas as features). Se o grupo quiser, uma captura do bloco da página no feed real.
- **Ambiente:** na pasta do OneDrive, `tests/interface/test_integracao_dados.py::test_app_test_carrega_o_feed_e_renderiza_o_widget_do_mapa` estoura os 30 s do `AppTest` também na `main` sem esta feature; fora do OneDrive a suíte inteira passa (779).

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Rafael.
### Sessão 17/11/2026: etapas 1 a 6 na `feat/F-BALD-2-comparacao`, a partir da `main` (`8138604`), por decisão do Rafael depois do congelamento de 15/11. `mais_rapido_com_limite` e `comparar_baldeacoes`, 50 testes (gabarito à mão, bordas, falhas, rede de teste e NetworkX num grafo em camadas), bloco na página Baldeações com 3 testes, `benchmarks/medir_comparacao_baldeacoes.py` no feed real, diagrama `atividade-comparar-baldeacoes`, `docs/GUIA.md` §5.3, §8 e §10, `relatorio/secoes/F-BALD-2.tex` e roteiro; decisões C1 a C4 propostas. Sem commit (o Rafael revisa e commita).
### Revisão 19/11/2026: ajustes da revisão do Thiago no PR #55. Decisões C1 a C4 aceitas pelo Rafael e exceção ao congelamento aprovada pelo grupo, as duas no `docs/GUIA.md` §8; marcas de rascunho retiradas do arquivo da feature, do `docs/GUIA.md` e do `relatorio/secoes/F-BALD-2.tex`; frase sobre o RNF-05 no relatório; branch refeita sobre a `main` (`2d68bd8`, com #53 e #54).
