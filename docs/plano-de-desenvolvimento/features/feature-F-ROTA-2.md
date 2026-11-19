# F-ROTA-2 · A* e origem e destino no mapa

**Período:** 2 · Desejáveis (12/11 a 15/11) · **Classe:** desejável
**Dono:** Henrique (@henriquegdc) · **Issue:** #13 · **Visões do grafo:** G_E
**Depende de:** F-ROTA · **Bloqueia:** nada
**Prazo:** 15/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-ROT-03, RF-ROT-04). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 18/11/2026 (Henrique, com agente).
- **Onde parou:** código, testes e medições prontos na branch `feat/F-ROTA-trajetos` (PR #57), ainda sem commit; decisão do A* registrada em Resultados. Começou depois do congelamento de 15/11 (o dono decidiu fazer mesmo assim).
- **Próximo passo:** revisão do PR (junto com F-ROTA e F-ROTA-OPC) e merge; gerar o PNG de `docs/diagramas/sequencia-trajetos-pagina.puml`. GUIA §5.7.1, seção no `relatorio/secoes/F-ROTA.tex` e roteiro feitos em 18/11.
- **Arquivos tocados:** `src/transporte/algoritmos/a_estrela.py`, `src/transporte/interface/paginas/trajetos.py`, `tests/algoritmos/test_a_estrela.py`, `tests/interface/test_pagina_trajetos.py`, `benchmarks/medir_rota_extensoes.py`.
- **Como testar:** `pytest tests/algoritmos/test_a_estrela.py tests/interface/test_pagina_trajetos.py`; medição: `python benchmarks/medir_rota_extensoes.py dados/brutos/bhtrans.zip`; navegador: `streamlit run src/transporte/interface/app.py`, página Trajetos.
- **Bloqueios:** nenhum.

## Objetivo
A* e origem e destino no mapa. Fecha:

- **RF-ROT-03** (D): Escolher origem e destino no mapa ou por coordenadas, ligando cada ponto à parada mais próxima
- **RF-ROT-04** (D): Calcular o trajeto com A* e comparar com o Dijkstra (vértices expandidos e tempo)

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | implementado | 18/11: `a_estrela.py` (A*, Dijkstra contado, parada mais próxima); sem commit |
| Modelo e dados | não aplicável | Usa o G_E do P0-MODELO com as esperas da F-ESPERA, sem mudança no modelo |
| Interface | implementado | 18/11: modo "Mapa ou coordenadas" e tabela "Dijkstra × A*" na página Trajetos, testados com AppTest; conferidos no navegador pelo dono com o feed real em 18/11 |
| Testes | implementado | 18/11: gabarito à mão, consistência da heurística e NetworkX em 15 sementes; suíte verde, exceto `test_integracao_dados` com o feed presente (teste de outro dono) |
| Desempenho (tempo medido) | concluído | 18/11: ver Resultados |
| Guia (explicação e quiz) | concluído | 18/11: `docs/GUIA.md` §5.7.1, §8 (decisão do A*) e §10 |
| Relatório | concluído | 18/11: parágrafo "Ponto no mapa e A*" em `relatorio/secoes/F-ROTA.tex`, para caber no orçamento de páginas |
| Vídeo | em andamento | 18/11: roteiro escrito; falta gravar |

## Especificação
`src/transporte/algoritmos/a_estrela.py` (`estado: implementado`, 18/11; sem consumidor fora da F-ROTA):

| Símbolo | Conteúdo |
|---|---|
| `coordenadas_ge(ge, paradas) -> list[(lat, lon)]` | Coordenadas por vértice de G_E; a plataforma usa as da sua parada. O(V) |
| `velocidade_maxima(ge, coords) -> float` | Maior distância / peso (m/s) entre as arestas de viagem e caminhada; INF se nenhuma muda de lugar. O(E) |
| `Busca(trajeto, expandidos, tempo_s)` | Resultado de uma busca contada |
| `Comparacao(dijkstra, a_estrela)` | As duas buscas na mesma consulta |
| `trajeto_a_estrela(ge, coords, vmax, origem, destino) -> Busca` | A*; mesmo custo do `trajeto_mais_rapido`. O((V + E) log V) no pior caso |
| `dijkstra_contado(ge, origem, destino) -> Busca` | A mesma busca com h = 0, para a comparação |
| `comparar(ge, coords, vmax, origem, destino) -> Comparacao` | RF-ROT-04 |
| `parada_mais_proxima(paradas, lat, lon) -> (id, metros)` | RF-ROT-03; varredura linear O(V), empate pelo menor id |

Página: `src/transporte/interface/paginas/trajetos.py` (compartilhada com F-ROTA e F-ROTA-OPC): modo "Mapa ou coordenadas" (clique ou campos de latitude e longitude, parada mais próxima e tempo porta a porta) e a tabela "Dijkstra × A*".

Algoritmos previstos (docs/fontes/modelagem.md §3.5):
- A* com heurística geográfica · visão G_E · O((V + E) log V) no pior caso · Admissível com a velocidade máxima da rede; expande menos vértices

## Como funciona e por quê
_Rascunho de 18/11; o dono revisa._

**O problema.** Duas coisas: escolher origem e destino em qualquer ponto do mapa, não só numa lista de paradas (RF-ROT-03), e calcular o trajeto com A* comparando com o Dijkstra em vértices expandidos e tempo (RF-ROT-04).

**Visão do grafo: G_E**, a mesma da F-ROTA. O custo de um trajeto em G_E já inclui a espera no ponto, a viagem e a caminhada, e a comparação só é justa se os dois algoritmos rodam no mesmo grafo e devolvem o mesmo custo.

**Ponto no mapa até a parada.** `parada_mais_proxima` percorre as 9.660 paradas e devolve a de menor distância haversine (empate pelo menor id). A caminhada do ponto até ela é a distância em linha reta dividida pela velocidade de caminhada dos parâmetros, e entra só no "Tempo porta a porta". Uma varredura linear basta: é uma consulta por clique e leva 4,90 ms. Uma k-d tree seria mais rápida por consulta, mas exigiria uma estrutura nova sem ganho perceptível.

**A\*, passo a passo.** É o Dijkstra com um "senso de direção". O Dijkstra fecha vértices em ordem de g(v), o custo já percorrido. O A* fecha em ordem de f(v) = g(v) + h(v), em que h(v) estima o que falta até o destino. Aqui:

- h(v) = distância em linha reta de v ao destino / vmax;
- vmax = maior distância / peso entre as arestas de viagem e caminhada de G_E (`velocidade_maxima`), com folga de 1e-9 para arredondamento;
- a plataforma usa as coordenadas da sua parada, então embarque e desembarque não mudam de lugar.

Com h = 0 a mesma função é o Dijkstra; é assim que `dijkstra_contado` mede a comparação.

Exemplo pequeno, hipotético (não é medição): destino 10 km ao norte, vmax = 10 m/s. O vértice N, 1 km ao norte, tem g = 200 s e f = 200 + 900 = 1.100 s. O vértice S, 1 km ao sul, tem g = 150 s e f = 150 + 1.100 = 1.250 s. O Dijkstra expande S antes, porque 150 < 200; o A* expande N antes, porque S afasta do destino.

**Por que o resultado é o ótimo.** A heurística é consistente: para toda aresta (u, v) de peso w, h(u) ≤ w + h(v). Vale porque d(u, t) ≤ d(u, v) + d(v, t) (desigualdade triangular) e d(u, v) / w ≤ vmax (definição de vmax). Consistente implica admissível, ou seja, h nunca passa do custo real, e o A* nunca descarta o caminho ótimo. Os testes conferem a consistência aresta por aresta e o custo contra o NetworkX.

**Detalhes da implementação.** Usa o `HeapMin` próprio com inserção preguiçosa: em vez de diminuir a chave, insere de novo e descarta a entrada desatualizada ao extrair. A busca para quando o destino sai da fila. O teste de entrada desatualizada tem tolerância relativa, para que o arredondamento da haversine não descarte uma entrada válida.

**Complexidade.** Tempo O((V + E) log V) no pior caso: cada aresta gera no máximo uma inserção, e com até E entradas na fila cada operação custa O(log E) = O(log V). Espaço O(V + E). Com h = 0 é exatamente o Dijkstra. O ganho do A* não muda a ordem de grandeza: ele só reduz quantos vértices são expandidos, e isso depende de quão apertada é a h.

**Decisões.** vmax calculado do próprio grafo, para garantir a admissibilidade em qualquer feed, em vez de uma constante. Manter o A* admissível mesmo com ganho baixo (decisão de 18/11, com as alternativas em Resultados).

**Limitações.**
- No feed real o A* expande 99,7% dos vértices do Dijkstra e fica mais lento. Duas causas: trechos com o mesmo horário no GTFS (piso de 1 s) dão um vmax de 1.258 m/s, e a h não enxerga as esperas, que são boa parte do custo.
- O ponto é ligado só à parada mais próxima, em linha reta. Uma parada um pouco mais longe pode dar um trajeto melhor, e a caminhada real segue as ruas.

## Perguntas de verificação
1. **Qual a diferença entre o A\* e o Dijkstra?** O Dijkstra escolhe o próximo vértice por g(v); o A* por g(v) + h(v), uma estimativa do que falta. Com h = 0 os dois são iguais.
2. **Por que o A\* devolve o mesmo custo do Dijkstra?** Porque a h é consistente (h(u) ≤ w + h(v) em toda aresta), logo nunca superestima o custo restante.
3. **Por que a h usa a velocidade máxima da rede, e não uma velocidade típica?** Com uma velocidade menor que a de alguma aresta, a h passaria do custo real naquela aresta e o A* poderia devolver um trajeto pior.
4. **Por que o A\* quase não ganhou no feed de BH?** O vmax de 1.258 m/s, vindo de trechos de 1 s no GTFS, deixa a h muito pequena, e ela não conta as esperas. Ele expande quase tudo e ainda paga a haversine.
5. **Como um clique no mapa vira origem do trajeto?** `parada_mais_proxima` acha a parada de menor distância em O(V); a caminhada até ela entra só no tempo porta a porta.

## Critérios de aceite
- [x] RF-ROT-03: Escolher origem e destino no mapa ou por coordenadas, ligando cada ponto à parada mais próxima (18/11, conferido no navegador)
- [x] RF-ROT-04: Calcular o trajeto com A* e comparar com o Dijkstra (vértices expandidos e tempo) (18/11, mesmo custo em 200 de 200 pares no feed real)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde (18/11; com o feed em `dados/brutos/`, `test_integracao_dados.py`, de outro dono, falha)
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (18/11, NetworkX em 15 sementes)
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido na rede real, registrado no arquivo da feature com V, E e a máquina (18/11, com `perf_counter` por consulta no script, como a comparação pede expandidos e tempo da mesma execução)
- [x] Página ou bloco na interface funcionando com o dataset real (18/11)
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/` (18/11: `sequencia-trajetos-pagina.puml`, compartilhado com F-ROTA e F-ROTA-OPC; PNG pendente)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md` (18/11, §5.7.1)
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

**A* contra Dijkstra e parada mais próxima, 18/11/2026.** Comando: `python benchmarks/medir_rota_extensoes.py dados/brutos/bhtrans.zip`, sobre a `main` em `11be1a2` mais a branch `feat/F-ROTA-trajetos` (PR #57). Feed: GTFS da PBH baixado em 18/11/2026, SHA-256 `8cb0a498b90b227221d0234e3b6386a7dfbe375a2cb2e52e86238010be05f6d6`, serviço de 18/11/2026: 9.660 paradas, 698 padrões. Máquina: Intel Core i5-13600KF, 31,8 GB, Windows 11, Python 3.12.10. G_E do pico da manhã com as esperas da F-ESPERA: V = 46.102, E = 209.025; 200 pares sorteados (semente 2026), todos com trajeto.

| Medida | Dijkstra | A* (vmax = 1.258,2 m/s, admissível) | A*, experimento sem as arestas no piso (vmax = 43,4 m/s) |
|---|---|---|---|
| Vértices expandidos (mediana / p95 / máximo) | 17.010 / 32.840 / 35.544 | 16.949 / 32.810 / 35.538 | |
| Expandidos do A* em % do Dijkstra (mediana / p95 / máximo) | | 99,7 / 99,9 / 100,0 | 90,1 / 97,4 / 99,5 |
| Tempo da busca, ms (mediana / p95 / máximo) | 72,3 / 136,4 / 158,3 | 90,8 / 168,5 / 182,4 | 79,8 / 163,7 / 192,3 |
| Trajetos com custo diferente do Dijkstra | | 0 em 200 | 0 em 200 (sem garantia) |

Por que o ganho é pequeno (diagnóstico com um script avulso sobre o mesmo G_E): das 36.386 arestas de viagem, 181 estão no piso de 1 s (decisão M2), porque o GTFS dá o mesmo horário a duas paradas seguidas, e uma delas cobre 1.258 m; é ela que fixa o vmax admissível. Sem as arestas no piso, o vmax ainda é 43,4 m/s, enquanto a mediana das arestas de viagem é 5,6 m/s e o quantil 99% é 7,0 m/s. E, mais importante, a heurística só enxerga deslocamento: o custo em G_E inclui as esperas de embarque (H/2), e o trajeto mediano leva 61 min. A cota d / vmax fica muito abaixo do custo real e quase não poda. O A* ainda paga uma haversine por vértice descoberto, por isso fica mais lento que o Dijkstra.

**Decisão (Henrique, 18/11/2026): manter o A* admissível em `src/` e relatar a comparação como resultado; o experimento fica só no script de medição.** Por quê: a RF-ROT-04 pede comparar A* e Dijkstra, e a comparação só vale se os dois devolvem o ótimo. Alternativas descartadas:
- vmax realista (por exemplo, 7 m/s): fica abaixo da velocidade aparente de cerca de 1% das arestas e tira a garantia de ótimo; o 0 em 200 do experimento é amostra, não prova;
- somar à cota a espera mínima de embarque: só vale para vértices de parada, que ainda vão embarcar, e o ganho previsto é pequeno perto da complexidade;
- interpolar por distância os horários repetidos no GTFS, no P0-MODELO: é o conserto certo do dado, mas muda a decisão M2 e os números das outras features depois do congelamento de 15/11. O efeito no trajeto é pequeno (inferência pelo mecanismo, não medida): o tempo do trecho de 1 s fica somado ao trecho vizinho, então quem atravessa os dois no mesmo ônibus paga o tempo certo, e o erro só aparece para quem embarca ou desembarca entre eles (181 de 36.386 arestas de viagem). Fica registrado como trabalho futuro;
- ALT (A* com pontos de referência e desigualdade triangular): enxergaria as esperas, mas é um algoritmo novo, fora do prazo.

| Medida | Valor |
|---|---|
| `parada_mais_proxima`, 1.000 pontos sorteados na caixa das paradas | 4,90 ms por ponto |
| Distância até a parada mais próxima (mediana / p95 / máximo) | 271,6 / 4.570,5 / 9.226,1 m (a caixa inclui áreas sem paradas) |

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

Rascunho de 18/11 (Henrique revisa):

1. **Problema (20 s):** o passageiro não sabe o código da parada; quer clicar onde está e onde quer ir. E o A* promete achar o mesmo trajeto olhando menos o mapa.
2. **Na ferramenta (40 s):** página Trajetos, modo "Mapa ou coordenadas": clicar na origem e no destino, mostrar a parada mais próxima de cada um, a caminhada e o tempo porta a porta; abrir a tabela "Dijkstra × A*".
3. **Como funciona (50 s):** f = g + h, com h = distância em linha reta / velocidade máxima; o exemplo de N e S; por que h nunca passa do custo real (desigualdade triangular), logo o trajeto é o ótimo. O((V + E) log V).
4. **Resultado e limitação (30 s):** mesmo custo do Dijkstra em 200 de 200 pares, mas 99,7% dos vértices expandidos e mais lento: trechos de 1 s no GTFS dão velocidade máxima de 1.258 m/s, e a h não vê as esperas. Uma velocidade realista podaria mais, mas perderia a garantia de ótimo.

## Pendências
- PNG do diagrama `sequencia-trajetos-pagina`.
- PR (junto com F-ROTA e F-ROTA-OPC), avisando o grupo de que é código novo depois do congelamento de 15/11.
- Trabalho futuro, fora deste trabalho: interpolar no P0-MODELO os horários repetidos do GTFS, o que baixaria o vmax e daria ganho real ao A*.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Henrique.
### Implementação 18/11/2026: A*, Dijkstra contado e parada mais próxima, com testes e página; medição no feed de 18/11.
### Decisão 18/11/2026: A* admissível mantido, ganho baixo relatado como resultado (alternativas em Resultados).
### Sessão 18/11/2026: conferência no navegador pelo dono; GUIA §5.7.1, §8 e §10, diagrama da página, seção no `F-ROTA.tex` e roteiro.
