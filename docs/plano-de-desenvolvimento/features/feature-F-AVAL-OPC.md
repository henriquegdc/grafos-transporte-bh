# F-AVAL-OPC · Benchmark contra NetworkX, complexidade empírica e página Desempenho

**Período:** Etapa opcional (16/11 a 18/11; feita em 20/11) · **Classe:** opcional
**Dono:** Rafael (@Rafael-Fonseca1510); implementada por Henrique (@henriquegdc) em 20/11, pela redistribuição do `plano.md` (H6) · **Issue:** #26 · **Visões do grafo:** G_P
**Depende de:** P0-GRAFO, F-MET, F-RES (funções medidas) · **Bloqueia:** F-AVAL (tabela consolidada lê os mesmos JSON)
**Prazo:** 20/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-DAD-05, RF-AVA-03, RF-AVA-04, RF-AVA-05). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 20/11/2026, branch `feat/F-AVAL-OPC-benchmark` a partir da `main` (`1b4edcf`).
- **Onde parou:** código, testes, página e documentação prontos; **medição final pendente** (não rodada para não disputar CPU com as outras sessões).
- **Próximo passo:** rodar, nesta ordem, na raiz do repositório e com o `.venv` ativo:
  1. `PYTHONPATH=src python benchmarks/comparar_networkx.py --feed dados/brutos/bhtrans.zip` (feed real + sintéticas de lado 10, 30 e 60; 3 repetições; estimativa de alguns minutos).
  2. `PYTHONPATH=src python benchmarks/complexidade_empirica.py` (lados 10 a 100; Brandes exato até lado 40; grava também `relatorio/figuras/complexidade-empirica.png`).
  3. Commitar os dois JSON de `benchmarks/resultados/` e a figura; trocar os dois `\pendente` de `relatorio/secoes/avaliacao.tex` pela tabela e pelas inclinações; preencher "Resultados para o relatório" abaixo.
- **Arquivos tocados:** `src/transporte/dados/sinteticas.py`, `src/transporte/interface/paginas/desempenho.py`, `src/transporte/interface/app.py` (entrada "Desempenho" em `PAGINAS`), `benchmarks/avaliacao_comum.py`, `benchmarks/comparar_networkx.py`, `benchmarks/complexidade_empirica.py`, `tests/dados/test_sinteticas.py`, `tests/interface/test_pagina_desempenho.py`, `requirements.txt` (matplotlib), `relatorio/secoes/avaliacao.tex`, `docs/GUIA.md` (§7 e §10), este arquivo.
- **Como testar:** `pytest tests/dados/test_sinteticas.py tests/interface/test_pagina_desempenho.py`; validação rápida dos scripts: `PYTHONPATH=src python benchmarks/comparar_networkx.py --lados 5 12 --repeticoes 1 --origens 5 --origens-brandes 10 --limite-exato 100 --saida <tmp>.json` e `PYTHONPATH=src python benchmarks/complexidade_empirica.py --lados 5 10 20 --lados-brandes 5 8 --repeticoes 1 --saida <tmp>.json --figura <tmp>.png`.
- **Bloqueios:** nenhum. Proximidade (F-MET-2) e propagação de rótulos (F-MET-OPC) entram na comparação quando estiverem na `main` (ver "Pendências").

## Objetivo
Benchmark contra NetworkX, complexidade empírica e página Desempenho. Fecha:

- **RF-DAD-05** (O): Gerar redes sintéticas de tamanho crescente para o estudo de escala
- **RF-AVA-03** (O): Comparar o tempo dos nossos algoritmos com os equivalentes do NetworkX no mesmo grafo
- **RF-AVA-04** (O): Gerar os gráficos de complexidade empírica (tempo × tamanho, log-log)
- **RF-AVA-05** (O): Página "Desempenho" na interface

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 20/11: `gerar_rede_sintetica`, `redes_crescentes`; regressão log-log em `complexidade_empirica.py` |
| Modelo e dados | concluído | 20/11: rede sintética no formato da `Rede`, passa por `construir_gp` e `construir_ge` |
| Interface | concluído | 20/11: página "Desempenho" em `PAGINAS`, lê `benchmarks/resultados/` |
| Testes | concluído | 20/11: 13 testes do gerador, 4 da página (AppTest); pytest completo: 880 passaram |
| Desempenho (tempo medido) | pendente | scripts validados com tamanhos pequenos e no feed real com 2 origens (resultados iguais aos do NetworkX); medição final pendente |
| Guia (explicação e quiz) | concluído | 20/11: `docs/GUIA.md` §7 e §10 |
| Relatório | parcial | 20/11: texto em `avaliacao.tex`; tabela, inclinações e figura dependem da medição final |
| Vídeo | roteiro | roteiro de 30 s abaixo |

## Especificação
- `gerar_rede_sintetica(lado, semente=0, espacamento_m=200, deslocamento_m=10, viagens_por_padrao=4, trecho_min_s=60, trecho_max_s=180, intervalo_min_s=600, intervalo_max_s=1200) -> Rede` (estado: implementado).
- `redes_crescentes(lados=LADOS_PADRAO, semente=0) -> list[tuple[int, Rede]]`; `LADOS_PADRAO = (10, 15, 20, 30, 40, 55, 70, 85, 100)` (estado: implementado).
- `render(rede=None, diretorio=None)` em `interface/paginas/desempenho.py` (estado: implementado).
- O texto antigo dizia "só em benchmarks/ e tests/, sem tocar src/ (código congelado)". O congelamento foi suspenso em 20/11 (`plano.md` §1), e o `plano.md` H6 pede `src/transporte/dados/sinteticas.py` e a página em `src/`; nenhum dos dois importa biblioteca de grafo.

### Formato dos JSON
`benchmarks/resultados/comparacao-networkx-<data>.json`:
```text
{comando, data, maquina{plataforma, processador, python}, semente, repeticoes, networkx,
 feed{caminho, sha256}?,                       # só com --feed
 grafos: [{grafo, V, E, algoritmos: [{algoritmo, complexidade, escopo,
            nosso_media_s, nosso_desvio_s, nosso, networkx_media_s, networkx_desvio_s,
            networkx, razao_nosso_sobre_networkx, resultados_iguais}]}],
 todos_iguais}
```
`benchmarks/resultados/complexidade-<data>.json`:
```text
{comando, data, maquina, semente, grafo, figura,
 algoritmos: [{algoritmo, complexidade_teorica, inclinacao_teorica, inclinacao_medida,
               intercepto, r2, pontos: [{lado, V, E, V_mais_E, media_s, desvio_s,
                                         repeticoes, tempo}]}]}
```
Tempos em segundos (`*_media_s`, `*_desvio_s`) e o texto de `Medicao.formatar()`. A F-AVAL (H7) pode ler os mesmos campos.

## Como funciona e por quê
**Problema.** Mostrar que as nossas implementações estão certas e em que ordem de grandeza ficam em relação a uma biblioteca de referência, e que o tempo cresce como a complexidade declarada.

**Redes sintéticas.** Grade `n x n` de paradas a 200 m, uma linha reta por fileira e por coluna, ida e volta, 4 viagens por padrão. Com o raio de 300 m, cada parada caminha até as 8 vizinhas; o G_P fica com cerca de 12 arestas por parada (lado 100 com semente 1: V = 10.000, E = 117.748; G_P real: 12,7). A grade mantém a mesma forma local em todos os tamanhos, então a inclinação mede o algoritmo e não uma mudança de estrutura. Exemplo 2x2: 4 linhas x 2 sentidos = 8 arestas de viagem, 4 retas + 2 diagonais de caminhada nos dois sentidos = 12 (teste `test_gabarito_grade_2x2`). Complexidade do gerador: O(n² T log(n T)). Alternativa descartada: recortes crescentes do feed real (densidade muda do centro para a periferia e o tamanho máximo é o próprio feed).

**Comparação com o NetworkX.** O `Grafo` vira um `nx.DiGraph` uma vez, fora da medição, só com vértices ativos e arestas utilizáveis, laços fora e paralelas reduzidas à de menor peso (a simplificação M3 do nosso Brandes; não muda BFS, Dijkstra nem Tarjan). Cada algoritmo é uma `Comparacao(algoritmo, complexidade, escopo, nosso, networkx, iguais)`; o script mede `nosso(ctx)` e `networkx(ctx)` com `medir` e confere os resultados de uma execução extra:
- BFS e Dijkstra: mesmas 20 origens; distâncias iguais (tolerância 1e-6).
- Brandes: exato até `--limite-exato` (1.000) vértices; acima disso, mesmas k = 20 origens dos dois lados (`estimar_intermediacao` multiplicado por k/N contra `nx.betweenness_centrality_subset(sources=origens, targets=todos)`), que somam as mesmas dependências origem a origem.
- Tarjan: mesmo conjunto de componentes.
Ponto de extensão: proximidade e rótulos entram como novas entradas em `COMPARACOES`.

**Complexidade empírica.** Mínimos quadrados de `log10 t = a + b log10(V + E)`; b é o expoente empírico. Teórico: 1 para BFS e Tarjan, pouco acima de 1 para Dijkstra (log V), cerca de 2 para Brandes (V (V + E) ~ (V + E)² com E ∝ V). Na validação com tamanhos pequenos (lado até 30, Brandes até 12, 1 a 2 repetições, sem valor para o relatório) as inclinações saíram perto disso, o que só confirma que o script funciona.

**Página.** Lê o JSON mais recente de cada prefixo (ordem do nome, que termina na data) e mostra tabela da comparação, tabela das inclinações, gráfico log-log com `st.line_chart` e um seletor dos outros JSON. Não mede nada na interface, para não misturar o tempo do Streamlit e não travar a página.

**Limitações.** Tempo de parede depende da máquina e da carga; a razão nosso/NetworkX é mais estável que os absolutos. Em grafos pequenos o custo fixo das chamadas achata a inclinação. A rede sintética é mais regular que a real.

## Perguntas de verificação
1. **Por que o grafo do NetworkX é montado fora da medição?** O nosso também já está pronto quando o cronômetro começa.
2. **Por que o Brandes no feed real usa k origens?** O exato custa dezenas de minutos; com as mesmas origens, o `subset` do NetworkX soma as mesmas dependências que o nosso estimador antes do fator N/k.
3. **O que é a inclinação b?** O expoente de t ~ (V + E)^b: 1 é linear, 2 é quadrático.
4. **Por que uma grade e não recortes do feed?** Forma local constante; a inclinação mede o algoritmo.

## Critérios de aceite
- [x] RF-DAD-05: Gerar redes sintéticas de tamanho crescente para o estudo de escala (`transporte.dados.sinteticas`)
- [x] RF-AVA-03: Comparar o tempo dos nossos algoritmos com os equivalentes do NetworkX no mesmo grafo (`benchmarks/comparar_networkx.py`; números finais pendentes)
- [x] RF-AVA-04: Gerar os gráficos de complexidade empírica (tempo × tamanho, log-log) (`benchmarks/complexidade_empirica.py`; figura final pendente)
- [x] RF-AVA-05: Página "Desempenho" na interface

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [ ] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina (medição final pendente)
- [x] Página ou bloco na interface funcionando com o dataset real (lê os JSON; independe da rede carregada)
- [ ] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/` (não feito; baixa prioridade)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação (texto em `avaliacao.tex`; números e figura pendentes)
- [x] Roteiro do vídeo escrito no arquivo da feature
- [x] Arquivo da feature atualizado: retomada, status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | concluída 20/11 (direto como implementado) |
| 2 | Algoritmo com testes de corretude | concluída 20/11 |
| 3 | Integração com a visão do grafo e com os dados reais | concluída 20/11 (validação no feed real com 2 origens) |
| 4 | Página na interface | concluída 20/11 |
| 5 | Tempo medido na rede real e complexidade justificada | pendente (medição final) |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | concluída 20/11, exceto diagrama e números |

## Resultados para o relatório
_Medição final pendente: rodar os comandos da Retomada e colar aqui V, E, média ± desvio, razão e inclinações, com o comando e a máquina._

Validação de corretude (20/11/2026, sem valor de tempo para o relatório): `PYTHONPATH=src python benchmarks/comparar_networkx.py --feed .../dados/brutos/bhtrans.zip --lados --repeticoes 1 --origens 2 --origens-brandes 2` deu `todos_iguais: true` (BFS, Dijkstra, Brandes com 2 origens e Tarjan iguais aos do NetworkX no G_P real).

## Roteiro do vídeo (30 s)
1. (5 s) "Conferimos nossos algoritmos contra o NetworkX e medimos como o tempo cresce."
2. (10 s) Página Desempenho: tabela nosso x NetworkX com a coluna "Resultados iguais" toda em "sim" e a razão de tempo.
3. (10 s) Gráfico log-log nas redes sintéticas: BFS e Tarjan com inclinação perto de 1, Brandes perto de 2, como a complexidade teórica prevê.
4. (5 s) Limitação: tempo de parede depende da máquina; por isso mostramos a razão e a inclinação.

## Pendências
- Medição final (comandos na Retomada) e números em `avaliacao.tex` e aqui.
- Incluir proximidade (F-MET-2) e propagação de rótulos (F-MET-OPC) em `COMPARACOES` de `benchmarks/comparar_networkx.py` quando estiverem na `main`.
- Diagrama UML (opcional).

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Rafael.
### Sessão 20/11/2026: implementação por Henrique (plano.md H6) na `feat/F-AVAL-OPC-benchmark`: gerador sintético, dois scripts de benchmark, página Desempenho, testes, guia e relatório; medição final pendente.
