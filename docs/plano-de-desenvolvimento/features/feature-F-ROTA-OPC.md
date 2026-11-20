# F-ROTA-OPC · Trajetos alternativos (Yen)

**Período:** 2 · Desejáveis (12/11 a 15/11) · **Classe:** opcional
**Dono:** Henrique (@henriquegdc) · **Issue:** #19 · **Visões do grafo:** G_E
**Depende de:** F-ROTA · **Bloqueia:** nada
**Prazo:** 15/11, só se sobrar tempo

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-ROT-05). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 20/11/2026 (Henrique, com agente): ajustes da revisão do Rafael no PR #57.
- **Onde parou:** opção (a) da revisão feita: `alternativos_por_linhas` tira caminhos do Yen até k sequências de `linha_id` distintas ou 2·k caminhos (teto padrão, decisão do Henrique em 20/11, GUIA §8; começou com 4·k), e a página mostra um trajeto por sequência com a coluna "Variantes" (e, no modo de pontos, o tempo porta a porta e o acesso no mapa). Medido no feed real com a máquina livre (ver Resultados, 20/11): com 2·k, segunda sequência em 1 de 8 pares, a 2,1 a 2,3 vezes o tempo do Yen puro. O grupo suspendeu o congelamento em 20/11 (GUIA §8).
- **Próximo passo:** aprovação do PR #57 e merge; conferir a página no navegador.
- **Arquivos tocados:** `src/transporte/algoritmos/alternativos.py`, seção de alternativos em `src/transporte/interface/paginas/trajetos.py`, `tests/algoritmos/test_alternativos.py`, `tests/interface/test_pagina_trajetos.py`, `benchmarks/medir_rota_extensoes.py`, `benchmarks/medir_alternativos_linhas.py`.
- **Como testar:** `pytest tests/algoritmos/test_alternativos.py tests/interface/test_pagina_trajetos.py`; medições: `python benchmarks/medir_rota_extensoes.py dados/brutos/bhtrans.zip` e `python benchmarks/medir_alternativos_linhas.py dados/brutos/bhtrans.zip 8 5`.
- **Bloqueios:** nenhum.

## Objetivo
Trajetos alternativos (Yen). Fecha:

- **RF-ROT-05** (O): Listar k trajetos alternativos (Yen)

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | implementado | 18/11: `alternativos.py` (Yen com desvios em A*); 20/11: Yen como gerador e `alternativos_por_linhas` (filtro por sequência de linhas, teto padrão 2·k) |
| Modelo e dados | não aplicável | Usa o G_E do P0-MODELO e a API de falhas do núcleo, sem mudança |
| Interface | implementado | 18/11: seção sob demanda na página Trajetos, testada com AppTest; conferida no navegador pelo dono com o feed real em 18/11. 20/11: um trajeto por sequência de linhas, coluna "Variantes", porta a porta no modo de pontos (AppTest; falta conferir no navegador) |
| Testes | implementado | 18/11: gabarito à mão, bordas, restauração do estado e `nx.shortest_simple_paths` em 10 sementes; 20/11: filtro por linhas (variante da mesma linha, teto, fim dos caminhos, bordas, estado após parar no meio) |
| Desempenho (tempo medido) | concluído | 18/11: ver Resultados. 20/11: filtro com teto 2·k e Yen remedidos com a máquina livre |
| Guia (explicação e quiz) | concluído | 18/11: `docs/GUIA.md` §5.7.2 e §10 |
| Relatório | concluído | 18/11: parágrafo "Trajetos alternativos" em `relatorio/secoes/F-ROTA.tex`, para caber no orçamento de páginas |
| Vídeo | em andamento | 18/11: roteiro escrito; falta gravar |

## Especificação
`src/transporte/algoritmos/alternativos.py` (`estado: implementado`, 18/11; sem consumidor fora da F-ROTA):

| Símbolo | Conteúdo |
|---|---|
| `trajetos_alternativos(ge, origem, destino, k, coords=None, vmax=INF) -> list[Trajeto]` | Yen: até k trajetos sem ciclo, em ordem crescente de tempo; desvios com A* quando há `coords` e `vmax` (da F-ROTA-2), senão Dijkstra. Restaura o estado ativo do grafo (só reativa o que desativou). k < 1: ValueError; inalcançável: lista vazia. O(k · n · (V + E) log V), n = vértices do maior caminho aceito |

| `sequencia_de_linhas(trajeto, linha_do_padrao) -> tuple[str, ...]` | `linha_id` dos trechos de ônibus, na ordem (20/11). O(k) |
| `Alternativo(trajeto, linhas, variantes)` | Um trajeto por sequência de linhas e quantos caminhos do Yen a repetiram (20/11) |
| `alternativos_por_linhas(ge, origem, destino, k, linha_do_padrao, coords=None, vmax=INF, teto=None) -> list[Alternativo]` | Tira caminhos do Yen em ordem de custo até k sequências distintas ou `teto` caminhos (padrão 2·k); guarda o mais rápido de cada sequência. k < 1 ou teto < k: ValueError. O(teto · n · (V + E) log V) (20/11) |

Página: seção "Trajetos alternativos (Yen)" de `src/transporte/interface/paginas/trajetos.py`, sob demanda (botão), k de 2 a 5, com `alternativos_por_linhas` (20/11): tabela com uma linha por sequência de linhas e a coluna "Variantes"; no modo "Mapa ou coordenadas", também o tempo porta a porta e o acesso a pé no mapa.

Algoritmos previstos (docs/fontes/modelagem.md §3.5):
- Yen (k trajetos alternativos) · visão G_E · O(k V (V + E) log V) · Opcional

## Como funciona e por quê
_Rascunho de 18/11; o dono revisa._

**O problema.** O trajeto mais rápido nem sempre é o que a pessoa quer: pode ter uma baldeação a mais, ou uma linha que ela evita. A RF-ROT-05 pede listar os k trajetos de menor tempo, do mais rápido ao mais lento, para ela escolher.

**Visão do grafo: G_E**, a mesma da F-ROTA, para que o tempo de cada alternativa inclua espera, viagem e caminhada e seja comparável com o trajeto mais rápido.

**Yen, passo a passo.** O primeiro caminho é o mais rápido (A* da F-ROTA-2). Para achar o i-ésimo, percorre-se o (i-1)-ésimo vértice a vértice. Cada vértice vira, um por vez, ponto de desvio:

1. a raiz, o trecho da origem até o desvio, é mantida;
2. as arestas que os caminhos já aceitos usam logo depois dessa mesma raiz são desativadas, para forçar uma saída diferente;
3. os vértices da raiz, menos o desvio, também são desativados, para o caminho não voltar e formar ciclo;
4. uma busca do desvio ao destino completa o candidato (raiz + desvio);
5. tudo o que foi desativado é reativado.

Os candidatos ainda não aceitos ficam num `HeapMin` pelo custo, e o menor vira o i-ésimo caminho. Para quando há k caminhos ou acabam os candidatos.

Exemplo pequeno (o do teste, contado em paradas para simplificar): de A a C há dois caminhos sem ciclo, um com troca em B (800 s) e uma linha lenta direta (2.300 s). O primeiro é o de 800 s. No desvio em A, a saída que ele usa fica desativada, e a busca acha a linha lenta. Pedindo k = 5, a função devolve só os dois, porque não há outros.

**Complexidade.** Tempo O(k · n · (V + E) log V): k caminhos, até n desvios por caminho (n = vértices do maior caminho aceito) e uma busca de O((V + E) log V) por desvio. Espaço O(V + E + k · n + C · n), com C candidatos guardados. Por isso o tempo cresce com k e com o comprimento do trajeto, como mostra a medição.

**Decisões.**
- Desativar e reativar pela API de falhas do núcleo (RF-GRF-03), em vez de copiar o grafo a cada desvio. Uma cópia custaria O(V + E) por desvio.
- Só é reativado o que a própria função desativou, e em `finally`. Assim uma falha simulada antes, pela F-RES, continua valendo, e o grafo volta ao estado anterior mesmo se a busca levantar exceção.
- Desvios com A*. Remover arestas não aumenta a velocidade de nenhuma aresta restante, então a heurística continua consistente e o custo do desvio continua ótimo.
- Candidatos repetidos são descartados pela sequência de arestas.

**Filtro por sequência de linhas (20/11, revisão do #57).** Para o Yen, dois caminhos são distintos se diferem em uma aresta de G_E. No feed real, os 5 primeiros são quase sempre o mesmo trajeto: a troca uma parada antes ou depois onde duas linhas dividem o corredor, ou o mesmo trecho a pé encadeado por outra parada. Para quem usa a página, isso não é alternativa. `alternativos_por_linhas` consome o Yen como gerador, em ordem de custo, agrupa os caminhos pela sequência de `linha_id` dos trechos de ônibus e guarda o primeiro (o mais rápido) de cada grupo; para em k grupos ou em 2·k caminhos aceitos (teto padrão; 4·k na primeira versão), porque cada caminho a mais custa n buscas. O Yen virou gerador para poder parar no meio; o grafo está restaurado a cada caminho entregue.

**Limitações.**
- Mesmo com o filtro, o Yen enumera caminhos em ordem de custo, e há muitas variantes de custo quase igual antes da primeira linha diferente: no feed real, com k = 5, 20 caminhos (4·k) deram uma segunda sequência em 2 de 8 pares, e 10 caminhos (2·k) em 1 de 8. Um método que proíba a linha já usada (penalidade ou remoção das arestas da linha) acharia outras opções mais rápido, mas deixa de ser o Yen; fica como trabalho futuro.
- Leva segundos: Yen puro com mediana de 3,1 s com k = 3 e 4,3 s com k = 5, chegando a 32,7 s em trajetos longos (20/11, máquina livre); com o filtro, quando ele chega ao teto de 2·k caminhos, de 2,1 a 2,3 vezes o Yen puro, em 7 de 8 pares (ver Resultados). Por isso a página só calcula quando o usuário clica no botão.

## Perguntas de verificação
1. **O que o Yen devolve?** Até k caminhos sem ciclo, em ordem crescente de custo; o primeiro é o trajeto mais rápido.
2. **O que é o ponto de desvio?** Um vértice do caminho anterior. Mantém-se o trecho até ele (a raiz) e procura-se outra continuação até o destino, com as saídas já usadas desativadas.
3. **Por que desativar os vértices da raiz?** Para o novo caminho não voltar a eles e formar ciclo.
4. **Por que o Yen é muito mais lento que uma busca?** Faz uma busca por vértice do caminho anterior, para cada um dos k caminhos: O(k · n · (V + E) log V).
5. **Como o Yen não estraga uma falha simulada pela F-RES?** Ele só reativa o que ele mesmo desativou, num `finally`.

## Critérios de aceite
- [x] RF-ROT-05: Listar k trajetos alternativos (Yen) (18/11, conferido no navegador)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde (18/11; com o feed em `dados/brutos/`, `test_integracao_dados.py`, de outro dono, falha)
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (18/11, `nx.shortest_simple_paths` em 10 sementes)
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido na rede real, registrado no arquivo da feature com V, E e a máquina (18/11, com `perf_counter` por consulta no script: cada consulta leva segundos e a distribuição importa mais que a média)
- [x] Página ou bloco na interface funcionando com o dataset real (18/11)
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/` (18/11: `sequencia-trajetos-pagina.{puml,png}`, bloco "opt" do Yen)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md` (18/11, §5.7.2)
- [ ] O revisor do PR consegue explicar o que o código faz
- [x] Seção do relatório, com figura, resultado e limitação (18/11: dentro de `relatorio/secoes/F-ROTA.tex`, que tem a figura da página)
- [x] Roteiro do vídeo escrito no arquivo da feature (18/11)
- [ ] Arquivo da feature atualizado: retomada ("concluída"), status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | Pulada: sem consumidor fora da F-ROTA; publicado já como `implementado` (18/11) |
| 2 | Algoritmo com testes de corretude | Feita (18/11) |
| 3 | Integração com a visão do grafo e com os dados reais | Feita (18/11) |
| 4 | Página na interface | Feita (18/11): AppTest e conferência no navegador com o feed real |
| 5 | Tempo medido na rede real e complexidade justificada | Feita (18/11) |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | Feita (18/11) |

## Resultados para o relatório
_Todo número vem com o comando que o gerou._

**Yen no feed real, 18/11/2026.** Comando: `python benchmarks/medir_rota_extensoes.py dados/brutos/bhtrans.zip` (mesma execução, feed e máquina da F-ROTA-2: GTFS de 18/11/2026, SHA-256 `8cb0a498…f6d6`, Intel Core i5-13600KF, Python 3.12.10). G_E do pico da manhã com esperas, V = 46.102, E = 209.025; os 20 primeiros pares com trajeto da amostra de 200 (semente 2026); desvios com A*.

| k | Tempo por consulta, s (mediana / p95 / máximo) | Trajetos achados |
|---|---|---|
| 3 | 2,3 / 12,0 / 12,7 | 3 em todas |
| 5 | 4,6 / 21,5 / 25,4 | 5 em todas |

**Remedição, 20/11/2026, máquina livre.** Mesmo comando e amostra, no código de `2b92bc6` (com o conjunto de fechados no A*): k = 3, mediana 3,1 / p95 10,9 / máximo 20,3 s; k = 5, mediana 4,3 / p95 24,6 / máximo 32,7 s; 3 e 5 trajetos em todas as consultas.

Os custos saíram em ordem não decrescente em todas as consultas (com tolerância de 1e-6: dois caminhos de mesmo custo somados em ordens diferentes diferem em 1 ulp). O tempo cresce com k e com o comprimento do trajeto anterior (uma busca por vértice), como prevê O(k · n · (V + E) log V); por isso a página só calcula no botão. Limitação: alternativos distintos diferem em pelo menos uma aresta de G_E, e podem ser variações pequenas (outra parada para trocar, outro trecho a pé); ver a medição de 20/11 abaixo.

**Sequências de linhas distintas, 20/11/2026, teto 2·k (padrão atual), máquina livre.** Comando: `python benchmarks/medir_alternativos_linhas.py dados/brutos/bhtrans.zip 8 5`, no código de `2b92bc6`. Mesmo feed de 18/11 (SHA-256 `8cb0a498…f6d6`, serviço de 18/11/2026, 9.660 paradas, 698 padrões), mesma máquina, Python 3.12.10. G_E do pico da manhã com as esperas da F-ESPERA, V = 46.102, E = 209.025; 8 pares sorteados com semente 2026 (só os com trajeto); k = 5; desvios com A*; filtro com teto 2·k = 10 caminhos.

| Par (origem -> destino) | Yen puro: sequências em 5 caminhos | 1º - 5º (s) | Yen puro (s) | Filtro: sequências em 10 caminhos | Variantes | 1ª - última (s) | Filtro (s) |
|---|---|---|---|---|---|---|---|
| 14786076 -> 14789446 | 1 | 0 | 20,4 | 1 | 10 | 0 | 45,4 |
| 14792503 -> 14792658 | 1 | 2 | 14,3 | 1 | 10 | 0 | 32,7 |
| 14785800 -> 14787826 | 1 | 0 | 7,1 | 1 | 10 | 0 | 16,0 |
| 14793413 -> 14791137 | 1 | 0 | 0,8 | 1 | 10 | 0 | 1,7 |
| 17611464 -> 14793265 | 1 | 6 | 1,7 | 1 | 10 | 0 | 3,7 |
| 14792308 -> 32799627 | 1 | 10 | 0,1 | 1 | 10 | 0 | 0,3 |
| 14791479 -> 14788103 | 1 | 61 | 1,3 | 2 | 8, 2 | 95 | 2,9 |
| 14784128 -> 14785430 | 1 | 20 | 1,0 | 1 | 10 | 0 | 2,3 |
| **Total** | **8 sequências em 40 caminhos** | | | **9 sequências em 80 caminhos** | | | |

Leitura: o Yen puro deu uma só sequência de linhas nos 8 pares (8 distintas em 40 caminhos), como na amostra da revisão do Rafael; a diferença entre o 1º e o 5º foi de 0 a 61 s. Com teto de 10 caminhos, o filtro achou uma segunda sequência em 1 dos 8 pares; nos outros 7, os 10 primeiros caminhos são o mesmo trajeto, e a página diz isso (coluna "Variantes" e aviso de que não há k sequências). O filtro leva de 2,1 a 2,3 vezes o Yen puro nos 7 pares acima de 0,1 s; o pior par, 45,4 s.

**Primeira versão, teto 4·k = 20 caminhos, 20/11/2026** (mesmo comando, código de `3dab370`; rodou com a máquina carregada, por isso só as contagens e a razão entre os tempos da mesma execução valem): 10 sequências em 160 caminhos, segunda sequência em 2 dos 8 pares (14791479 -> 14788103 e 14784128 -> 14785430); filtro de 4,4 a 4,9 vezes o Yen puro, pior par 100,8 s. Pelo ganho quase nulo e pelo custo, o teto padrão passou a 2·k (decisão do Henrique, GUIA §8).

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

Rascunho de 18/11 (Henrique revisa):

1. **Problema (15 s):** o mais rápido pode ter uma troca a mais ou uma linha que a pessoa evita; ela quer ver as outras opções.
2. **Na ferramenta (35 s):** na página Trajetos, escolher k e clicar em "Listar trajetos alternativos"; mostrar a tabela em ordem de tempo e o mapa de um alternativo.
3. **Como funciona (50 s):** Yen: cada vértice do trajeto anterior vira desvio; mantém a raiz, desativa as saídas já usadas e os vértices da raiz, busca o resto com A* e reativa só o que desativou. O(k · n · (V + E) log V).
4. **Resultado e limitação (30 s):** mediana de 2,3 s com k = 3 e 4,6 s com k = 5, até 25 s; por isso só no botão. Limitação: no feed real os 5 primeiros caminhos do Yen usaram as mesmas linhas nos 8 pares medidos; a página agrupa por sequência de linhas, e mesmo com 10 caminhos só 1 dos 8 pares ganhou outra sequência.

## Pendências
- PR #57 (junto com F-ROTA e F-ROTA-2): revisão atendida em 20/11; falta aprovação e merge. ~~Avisar que é código novo depois do congelamento.~~ **resolvido em 20/11:** congelamento suspenso pelo grupo (GUIA §8).
- ~~Medição final de tempo do filtro com a máquina livre.~~ **feito em 20/11:** ver Resultados.
- ~~Decidir o teto do filtro.~~ **decidido em 20/11:** 2·k (GUIA §8).
- Conferir no navegador a seção nova (coluna "Variantes", porta a porta no modo de pontos).

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Henrique.
### Implementação 18/11/2026: Yen com desvios em A*, testes e seção na página Trajetos; medição no feed de 18/11.
### Sessão 18/11/2026: conferência no navegador pelo dono; GUIA §5.7.2 e §10, diagrama da página, seção no `F-ROTA.tex` e roteiro.
### Revisão 19/11/2026: Rafael mede o Yen no feed real (k = 5, 8 pares): os 5 caminhos usam a mesma sequência de linhas em todos os pares; sugere (a) filtrar por sequência de linhas ou (b) agrupar a tabela.
### Decisão 20/11/2026: o grupo suspende o congelamento; todas as desejáveis e opcionais entram (GUIA §8).
### Sessão 20/11/2026: opção (a): Yen como gerador, `alternativos_por_linhas` com teto 4·k, página com coluna "Variantes" e porta a porta no modo de pontos; testes; medição de sequências distintas no feed real (`medir_alternativos_linhas.py`); `F-ROTA.tex` com o número medido.
### Decisão 20/11/2026: teto padrão do filtro passa a 2·k (Henrique), porque 4·k quase não achava sequências novas e custava 4 a 5 vezes o Yen puro (GUIA §8).
### Sessão 20/11/2026: teto 2·k (`2b92bc6`); medições finais com a máquina livre; documentação atualizada.
