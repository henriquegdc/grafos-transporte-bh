# F-ROTA-OPC · Trajetos alternativos (Yen)

**Período:** 2 · Desejáveis (12/11 a 15/11) · **Classe:** opcional
**Dono:** Henrique (@henriquegdc) · **Issue:** #19 · **Visões do grafo:** G_E
**Depende de:** F-ROTA · **Bloqueia:** nada
**Prazo:** 15/11, só se sobrar tempo

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-ROT-05). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 18/11/2026 (Henrique, com agente).
- **Onde parou:** código, testes e medição prontos na branch `feat/F-ROTA-pagina`, ainda sem commit. Começou depois do congelamento de 15/11 (o dono decidiu fazer mesmo assim).
- **Próximo passo:** revisão do PR (junto com F-ROTA e F-ROTA-2) e merge; gerar o PNG de `docs/diagramas/sequencia-trajetos-pagina.puml`. GUIA §5.7.2, seção no `relatorio/secoes/F-ROTA.tex` e roteiro feitos em 18/11.
- **Arquivos tocados:** `src/transporte/algoritmos/alternativos.py`, seção de alternativos em `src/transporte/interface/paginas/trajetos.py`, `tests/algoritmos/test_alternativos.py`, `benchmarks/medir_rota_extensoes.py`.
- **Como testar:** `pytest tests/algoritmos/test_alternativos.py tests/interface/test_pagina_trajetos.py`; medição: `python benchmarks/medir_rota_extensoes.py dados/brutos/bhtrans.zip`.
- **Bloqueios:** nenhum.

## Objetivo
Trajetos alternativos (Yen). Fecha:

- **RF-ROT-05** (O): Listar k trajetos alternativos (Yen)

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | implementado | 18/11: `alternativos.py` (Yen com desvios em A*); sem commit |
| Modelo e dados | não aplicável | Usa o G_E do P0-MODELO e a API de falhas do núcleo, sem mudança |
| Interface | implementado | 18/11: seção sob demanda na página Trajetos, testada com AppTest; conferida no navegador pelo dono com o feed real em 18/11 |
| Testes | implementado | 18/11: gabarito à mão, bordas, restauração do estado e `nx.shortest_simple_paths` em 10 sementes |
| Desempenho (tempo medido) | concluído | 18/11: ver Resultados |
| Guia (explicação e quiz) | concluído | 18/11: `docs/GUIA.md` §5.7.2 e §10 |
| Relatório | concluído | 18/11: parágrafo "Trajetos alternativos" em `relatorio/secoes/F-ROTA.tex`, para caber no orçamento de páginas |
| Vídeo | em andamento | 18/11: roteiro escrito; falta gravar |

## Especificação
`src/transporte/algoritmos/alternativos.py` (`estado: implementado`, 18/11; sem consumidor fora da F-ROTA):

| Símbolo | Conteúdo |
|---|---|
| `trajetos_alternativos(ge, origem, destino, k, coords=None, vmax=INF) -> list[Trajeto]` | Yen: até k trajetos sem ciclo, em ordem crescente de tempo; desvios com A* quando há `coords` e `vmax` (da F-ROTA-2), senão Dijkstra. Restaura o estado ativo do grafo (só reativa o que desativou). k < 1: ValueError; inalcançável: lista vazia. O(k · n · (V + E) log V), n = vértices do maior caminho aceito |

Página: seção "Trajetos alternativos (Yen)" de `src/transporte/interface/paginas/trajetos.py`, sob demanda (botão), k de 2 a 5, com tabela e mapa do trajeto escolhido.

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

**Limitações.**
- Dois alternativos são distintos se diferem em pelo menos uma aresta de G_E. Podem ser variações pequenas do mesmo trajeto, como trocar de linha numa parada vizinha ou fazer outro trecho a pé. Falta um filtro de diferença mínima.
- Leva segundos: mediana de 2,3 s com k = 3 e 4,6 s com k = 5, chegando a 25 s em trajetos longos. Por isso a página só calcula quando o usuário clica no botão.

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
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/` (18/11: `sequencia-trajetos-pagina.puml`, bloco "opt" do Yen; PNG pendente)
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
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | Feita (18/11); falta só o PNG do diagrama |

## Resultados para o relatório
_Todo número vem com o comando que o gerou._

**Yen no feed real, 18/11/2026.** Comando: `python benchmarks/medir_rota_extensoes.py dados/brutos/bhtrans.zip` (mesma execução, feed e máquina da F-ROTA-2: GTFS de 18/11/2026, SHA-256 `8cb0a498…f6d6`, Intel Core i5-13600KF, Python 3.12.10). G_E do pico da manhã com esperas, V = 46.102, E = 209.025; os 20 primeiros pares com trajeto da amostra de 200 (semente 2026); desvios com A*.

| k | Tempo por consulta, s (mediana / p95 / máximo) | Trajetos achados |
|---|---|---|
| 3 | 2,3 / 12,0 / 12,7 | 3 em todas |
| 5 | 4,6 / 21,5 / 25,4 | 5 em todas |

Os custos saíram em ordem não decrescente em todas as consultas (com tolerância de 1e-6: dois caminhos de mesmo custo somados em ordens diferentes diferem em 1 ulp). O tempo cresce com k e com o comprimento do trajeto anterior (uma busca por vértice), como prevê O(k · n · (V + E) log V); por isso a página só calcula no botão. Limitação: alternativos distintos diferem em pelo menos uma aresta de G_E, e podem ser variações pequenas (outra parada para trocar, outro trecho a pé); falta filtrar por diferença mínima.

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

Rascunho de 18/11 (Henrique revisa):

1. **Problema (15 s):** o mais rápido pode ter uma troca a mais ou uma linha que a pessoa evita; ela quer ver as outras opções.
2. **Na ferramenta (35 s):** na página Trajetos, escolher k e clicar em "Listar trajetos alternativos"; mostrar a tabela em ordem de tempo e o mapa de um alternativo.
3. **Como funciona (50 s):** Yen: cada vértice do trajeto anterior vira desvio; mantém a raiz, desativa as saídas já usadas e os vértices da raiz, busca o resto com A* e reativa só o que desativou. O(k · n · (V + E) log V).
4. **Resultado e limitação (30 s):** mediana de 2,3 s com k = 3 e 4,6 s com k = 5, até 25 s; por isso só no botão. Limitação: alternativos podem ser variações pequenas do mesmo trajeto.

## Pendências
- PNG do diagrama `sequencia-trajetos-pagina`.
- PR (junto com F-ROTA e F-ROTA-2), avisando o grupo de que é código novo depois do congelamento de 15/11.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Henrique.
### Implementação 18/11/2026: Yen com desvios em A*, testes e seção na página Trajetos; medição no feed de 18/11.
### Sessão 18/11/2026: conferência no navegador pelo dono; GUIA §5.7.2 e §10, diagrama da página, seção no `F-ROTA.tex` e roteiro.
