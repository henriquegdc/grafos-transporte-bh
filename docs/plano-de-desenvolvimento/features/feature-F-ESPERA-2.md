# F-ESPERA-2 · Quadro de horários e Monte Carlo

**Dono:** Miguel (@Miguelgdn1) · **Issue:** #14 · **Visão:** G_T · **Classe:** desejável.
Depende de F-ESPERA. RF-ESP-04 e RF-ESP-05 em `docs/fontes/REQUISITOS.md`.
Prazo do plano de finalização: 20/11/2026.

## Retomada

Em 20/11, Miguel retomou M1 na branch `feat/F-ESPERA-2-horarios`, sobre a main
`1b4edcf`. O modo **Quadro de horários** passou no AppTest com a rede de teste
e em uma consulta funcional com o mapa no GTFS de BH. A medição final foi executada em sequência. O próximo passo é a revisão do PR e a integração em main. O arquivo local `plano.md`
fica fora do commit.

## Objetivo e critérios de aceite

- [x] RF-ESP-04. Simular o trajeto pelo quadro de horários, com mapa e decomposição.
- [x] RF-ESP-05. Sortear saídas e mostrar distribuições de tempo total e de espera, com contagem de saídas sem trajeto.

## Status

| Camada | Situação em 20/11 | Evidência |
|---|---|---|
| Modelo e algoritmo | Implementados na branch | `modelo/horarios.py`, `algoritmos/chegada_mais_cedo.py` |
| Interface | Validada | Página Espera, modo Quadro de horários, comparação H/2 e histogramas |
| Testes | Validados | Gabarito, dez redes com oráculo NetworkX, bordas e AppTest |
| Desempenho | Concluído | JSON do feed de BH com cinco repetições |
| Guia e relatório | Escritos, aguardam revisão | Guia §5.2 e §10, `relatorio/secoes/F-ESPERA-2.tex` |
| Vídeo | Roteiro pronto | Gravação prevista para 20/11 |
| Integração | Pendente | Revisão de Miguel, commit, PR e aprovação |

## Especificação e dependências

Contrato implementado. Todos os horários são segundos desde o início do dia de serviço.

- `construir_gt(rede, params=None) -> VisaoGT`: reaproveita o grafo próprio e a construção das caminhadas de G_P. Cada posição servida do padrão mantém seu quadro por ID de aresta, inclusive se o padrão revisitar a mesma parada.
- `chegada_mais_cedo(gt, origem, destino, saida_s) -> Trajeto | None`: devolve trechos no contrato de F-ROTA. Sem caminho devolve `None`, origem igual ao destino dá duração zero e ID ausente levanta `KeyError`.
- `monte_carlo(gt, origem, destino, inicio_s, fim_s, amostras, semente) -> list[Amostra]`: guarda saída, total e espera de cada sorteio. Uma saída inalcançável tem durações ausentes.

## Como funciona e por quê

O leitor já expande as frequências do dia carregado. Para cada segmento, G_T
ordena os eventos de viagem por partida. Uma varredura de trás para frente
descarta uma partida se houver outra posterior com chegada estritamente melhor.
Quem chega antes ao ponto pode esperar e usar a mesma opção disponível a quem
chega depois. Esse requisito FIFO permite fechar uma parada pelo menor horário
no heap. Cada relaxamento busca a primeira partida ainda alcançável no quadro
filtrado ou soma o tempo fixo de caminhada. A reconstrução usa a identidade da
viagem expandida para distinguir permanecer no veículo de trocar de ônibus.

Para V paradas, E arestas, k eventos no maior quadro, N eventos ao todo e L
posições dos padrões, o índice custa O(V+E+L+N log(k+1)) em tempo esperado
com a grade espacial, cuja vizinhança pode exigir O(V²) comparações. Seu espaço
é O(V+E+L+N). Uma consulta faz até E relaxamentos e inserções preguiçosas no
heap; custa O((V+E) log(E+2) + E log(k+1)) e usa O(V+E) de espaço auxiliar.
O Monte Carlo faz S consultas com o índice pronto e usa O(S+V+E) de espaço
auxiliar. A janela inclui o início e exclui o fim. A cobertura acompanha os
histogramas porque as saídas sem caminho também são resultados do sorteio.

O modelo usa um horário programado por parada, sem distinguir a permanência
no ponto, e admite transferência imediata. O dia de serviço pode passar de
24h, mas a consulta não carrega o serviço do dia seguinte.

Diagrama de atividade: [fonte](../../diagramas/atividade-quadro-horarios.puml) e
[imagem](../../diagramas/atividade-quadro-horarios.png).

## Perguntas de verificação

1. **É possível embarcar ao chegar no instante da partida?** Sim. A busca inclui a igualdade.
2. **Por que filtrar uma partida ultrapassada?** Quem poderia embarcar nela pode aguardar a posterior e chegar antes.
3. **Como interpretar o histograma se algumas saídas não atendem ao destino?** A distribuição descreve as saídas alcançáveis. A contagem informa quantas entraram nela.

## Resultados e reprodução

Na rede de teste, A → C às 08:01, sem caminhada, resultou em 19 min de espera
e 10 min de viagem, contra 10 min de espera por H/2. Gabarito, amostras e
tempos **da rede de teste** estão em
`benchmarks/resultados/quadro-horarios-rede-teste.json`. Comando a partir da raiz:

```sh
PYTHONPATH=src .venv/bin/python benchmarks/medir_quadro_horarios.py dados/rede-teste --origem A --destino C --saida-s 28860 --raio-m 0 --repeticoes 1
```

**Regerado em 20/11/2026 no feed oficial de 18/11** (SHA-256
`8cb0a498b90b227221d0234e3b6386a7dfbe375a2cb2e52e86238010be05f6d6`, serviço de 18/11/2026;
o JSON não grava o SHA, que fica registrado aqui), Intel Core i5-13600KF, Windows 11
(10.0.26200), Python 3.12.10. A consulta 14788851 → 14792190 às 08:00 retornou 23,67 min:
6,77 a pé, 1,87 de espera e 15,03 de ônibus, com 4 baldeações (uma delas com 0 s de espera,
porque G_T não tem tempo mínimo de transferência). A estimativa H/2 para o mesmo par e saída
retornou 40,24 min, com 15,34 de espera. G_T teve 9.660 vértices e 146.630 arestas. Os
valores do trajeto são os mesmos da medição anterior, no `bhtrans.zip` de 05/11 (serviço de
04/11, G_T com 9.659 vértices e 146.563 arestas). Esses valores descrevem o trajeto e o grafo. O desempenho foi medido em execução exclusiva com o mesmo par. Evidência funcional:
`benchmarks/resultados/quadro-horarios-consulta-bhtrans.json`. Para reproduzir:

```sh
PYTHONPATH=src .venv/bin/python benchmarks/medir_quadro_horarios.py dados/brutos/bhtrans.zip --origem 14788851 --destino 14792190 --amostras 1 --sem-medicao
```

**Medição final (vai para o relatório)** em 20/11, feed oficial de 18/11 (SHA-256 acima), Intel Core i5-13600KF e Python 3.12.10, com cinco repetições (média ± desvio amostral). Construção de G_T em 455,04 ± 13,09 ms, consulta em 11,10 ± 1,13 ms e Monte Carlo de 30 saídas (todas com caminho) em 383,22 ± 4,17 ms. Medição anterior, substituída: serviço de 04/11 em macOS arm64, Python 3.12.13; 318,55 ± 11,29 ms, 6,98 ± 1,28 ms e 279,31 ± 24,47 ms. JSON gravado em
`benchmarks/resultados/quadro-horarios-bhtrans.json`:

```sh
PYTHONPATH=src .venv/bin/python benchmarks/medir_quadro_horarios.py dados/brutos/bhtrans.zip --origem 14788851 --destino 14792190 --saida-s 28800
```

**Validação:** `sh .githooks/pre-commit` e `.venv/bin/python -m pytest -q`.
A suíte compara as chegadas para todos os pares em dez redes sem caminhada com
um grafo NetworkX expandido por evento, usando arestas de viagem e espera.
Há testes separados de caminhada fracionária, ultrapassagem, frequência,
viagem após meia-noite e ausência de caminho.

## Roteiro do vídeo (30 s)

- **0–10 s:** abrir Espera → Quadro de horários. Selecionar o par do feed real acima, às 08h, e simular.
- **10–20 s:** apontar no mapa onde ocorre uma troca. Mostrar o tempo total e a espera, depois ler a estimativa H/2 para a mesma saída.
- **20–30 s:** mostrar a janela e os dois histogramas. Explicar que perder uma partida muda a espera e que os sorteios usam o horário programado.

## Definition of Done e pendências

- [x] Contratos, código, docstrings, testes e hook.
- [x] Interface com mapa, validação no feed real, guia, relatório, diagrama e roteiro.
- [x] Medição final serial no GTFS de BH, JSON e registro dos tempos.
- [ ] Revisão do conteúdo pelo dono e PR para main com aprovação de outro integrante.
- [ ] Gravação do trecho do vídeo.

## Timeline

- 29/10/2026: feature criada e atribuída a Miguel.
- 11/11/2026: adiada para priorizar F-ESPERA e P0-DADOS.
- 20/11/2026: retomada pelo plano de finalização. Implementados índice temporal, consulta, Monte Carlo e interface. Consulta funcional em BH e validação automatizada concluídas. Medição final executada em sequência e registrada no JSON de BH.
