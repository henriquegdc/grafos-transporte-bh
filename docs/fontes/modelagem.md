# Modelagem · Análise de redes de transporte público

**Versão:** 0.1 · **Integrador:** Henrique; cada dono escreve a parte da sua feature

> Como o problema vira grafo. Em conflito, perde para `docs/fontes/REQUISITOS.md`.
> O porquê de cada decisão está em `docs/GUIA.md` §8.
> A numeração das seções segue `docs/fontes/plano-de-projeto.md`, para que as referências cruzadas continuem válidas.

### 3.2 Stack

**Decisão.** Python 3.12, fixado no repositório. Streamlit para a interface, com mapa em folium (via `streamlit-folium`). pandas só para ler os CSV do GTFS. pytest para testes e ruff para lint. Fila de prioridade (heap binário) própria, sem `heapq`. NetworkX só em `tests/` (comparação de resultado) e em `benchmarks/`.

**Justificativa.**

- Uma linguagem para os seis, inclusive na interface. Ninguém espera outra pessoa para ver a própria feature na tela.
- GTFS é um conjunto de CSV; Python lê e limpa isso com pouco código.
- Streamlit entrega interface gráfica com mapa sem código de frontend, e o enunciado pede uma "interface mínima de uso".
- O `heapq` não é biblioteca de grafo, mas é uma estrutura pronta no coração do Dijkstra. Escrever o heap custa cerca de 50 linhas e elimina qualquer dúvida sobre a regra.
- A comparação com NetworkX, se for feita, roda no mesmo runtime.
- Alternativas descartadas: Java roda mais rápido, mas a interface custa mais; C++ tem o mesmo problema, com produtividade menor.

**Consequências aceitas.**

- Python é mais lento. Neutralização: recorte da rede por região ou por linhas, amostragem nas métricas de todos os pares (com o erro medido) e estruturas indexadas por inteiros.
- O limite de recursão do Python obriga a escrever DFS e Tarjan de forma iterativa.

### 3.3 Dados

O formato padrão de dados de transporte público é o GTFS: um `.zip` de arquivos CSV com paradas (`stops.txt`), linhas (`routes.txt`), viagens (`trips.txt`), horários de passagem (`stop_times.txt`) e calendário (`calendar.txt`), e opcionalmente frequências (`frequencies.txt`) e traçados (`shapes.txt`).

**Decisão.** GTFS dos ônibus de Belo Horizonte (BHTrans), no portal de dados abertos da PBH, com recorte por região ou por linhas. Reserva: rede de teste feita à mão, em formato GTFS, com respostas conhecidas. Miguel confirma a disponibilidade e a qualidade do feed até 31/10; se o feed não servir, a reserva é um dataset de metrô ou trem do Kaggle que tenha horários.

**Conferências do feed:** ter horários (`stop_times.txt` ou `frequencies.txt`); ter coordenadas; tamanho viável em Python, com recorte se preciso; licença que permita uso acadêmico.

**Armadilhas conhecidas do GTFS:** horários acima de `24:00:00` são válidos (viagem que passa da meia-noite); a mesma parada física pode aparecer duas vezes, uma por sentido; o calendário define quais viagens valem em cada dia, então a análise fixa um dia típico (dia útil).

### 3.4 Modelagem: visões do mesmo dado

O GTFS vira primeiro um **modelo normalizado**: paradas, linhas, padrões (a sequência de paradas de uma linha num sentido), viagens, horários e intervalos. Dele saem as visões de grafo, cada uma escolhida pela pergunta que responde. Usar mais de uma visão é parte do argumento de modelagem do relatório: o modelo certo depende da pergunta.

| Visão | Vértices | Arestas e pesos | Responde |
|---|---|---|---|
| **G_P · paradas** | Paradas | Dirigidas: parada seguinte em alguma viagem (peso: tempo mediano de viagem); caminhada entre paradas a até R metros (peso: distância dividida pela velocidade de caminhada) | Centralidades (F-MET), eficiência estrutural (F-EFI), falhas (F-RES) |
| **G_E · parada × linha** | Um nó por parada e um nó de plataforma por par (parada, padrão de linha) | Embarque: da parada à plataforma (peso: espera esperada); viagem: da plataforma à seguinte do mesmo padrão (peso: tempo de viagem); desembarque: da plataforma à parada (peso 0); caminhada: de parada a parada | Trajeto mais rápido (F-ROTA), espera (F-ESPERA), tempos origem-destino (F-EFI) |
| **G_L · linhas** | Padrões de linha | Ligação quando duas linhas compartilham parada ou têm paradas a distância de caminhada; sem peso | Mínimo de baldeações por BFS (F-BALD) |
| **G_T · dependente do horário** (extensão) | Paradas | Cada aresta de viagem guarda a lista de partidas; o custo depende do instante de chegada (espera até a próxima partida, mais a viagem) | Simulação com quadro de horários (F-ESPERA-2) |

**Por que G_E existe.** Em G_P, continuar no mesmo ônibus e trocar de ônibus numa parada custam o mesmo, porque a aresta não sabe em qual linha o passageiro está. G_E separa as linhas em nós de plataforma: trocar de linha obriga a passar pelo nó da parada e a pagar uma nova aresta de embarque, que carrega a espera. Assim um único Dijkstra soma caminhada, espera, viagem e baldeação, e o número de baldeações é o número de embarques menos um.

**Espera esperada.** Com o passageiro chegando ao acaso e intervalo regular H, a espera média é H/2. Com intervalos irregulares, a espera média é E[H²] / (2 E[H]), maior que H/2 (paradoxo da inspeção). A versão essencial usa H/2 por faixa horária; a diferença entre os dois valores é um resultado a discutir no relatório.

**Por que G_T funciona com Dijkstra.** A rede é FIFO: sair mais tarde de uma parada nunca faz chegar mais cedo pela mesma aresta. Com essa propriedade, o Dijkstra de chegada mais cedo continua correto.

**Parâmetros (fixados em 29/10; registrados em `modelagem.md`):**

| Parâmetro | Valor | Por quê |
|---|---|---|
| Raio de caminhada R | 300 m | Distância curta o bastante para uma baldeação a pé plausível, sem ligar paradas distantes |
| Velocidade de caminhada | 1,2 m/s | Velocidade média de pedestre usada com frequência em estudos de acessibilidade |
| Faixas horárias | Pico da manhã, entrepico, pico da tarde e noite | Separam os regimes de intervalo que mais mudam a espera |
| Penalidade fixa por baldeação | Nenhuma | A espera da nova linha já pesa a baldeação; uma penalidade extra seria arbitrária |

Mudar um parâmetro depois exige linha no registro de decisões do `docs/GUIA.md`, com o motivo.

**Representação no núcleo.** Grafo dirigido e ponderado, com vértices numerados de 0 a n-1 e lista de adjacência. Os atributos de vértice e de aresta ficam em estruturas paralelas. Espaço O(V + E). Vértices e arestas podem ser desativados sem reconstruir o grafo, o que F-RES usa para simular falhas.

### 3.5 Algoritmos e complexidade

Todos os algoritmos são implementados pelo grupo. As complexidades consideram o heap binário próprio.

| Algoritmo | Feature | Visão | Tempo | Observação |
|---|---|---|---|---|
| Heap binário de mínimo | P0-GRAFO | (estrutura) | O(log n) por inserção e extração | Usado por todos os Dijkstras; inserção preguiçosa em vez de diminuir chave |
| BFS | P0-GRAFO, F-BALD | G_L | O(V + E) | Mínimo de baldeações |
| Dijkstra | P0-GRAFO, F-ROTA | G_E | O((V + E) log V) | Pesos não negativos |
| A* com heurística geográfica | F-ROTA-2 | G_E | O((V + E) log V) no pior caso | Admissível com a velocidade máxima da rede; expande menos vértices |
| Dijkstra de chegada mais cedo | F-ESPERA-2 | G_T | O((V + E) log V + E log k) | k: maior número de partidas numa aresta (busca binária) |
| Monte Carlo de horários de saída | F-ESPERA-2 | G_T | O(S × custo de uma consulta) | S amostras, semente fixa |
| Brandes (intermediação) | F-MET | G_P | O(V (V + E) log V) | Ponderado; O(VE) sem pesos |
| Proximidade (closeness) | F-MET-2 | G_P | O(V (V + E) log V) | Uma execução de Dijkstra por vértice |
| Intermediação amostrada | F-MET-2 | G_P | O(s (V + E) log V) | s fontes; erro medido contra a exata |
| Eficiência global | F-EFI | G_E ou G_P | O(V (V + E) log V) exata; O(s (V + E) log V) amostrada | Média de 1/d; par sem caminho soma 0, então funciona com grafo desconexo |
| Isócronas | F-EFI-2 | G_E | O((V' + E') log V') | Dijkstra com limite T; V' e E' são a parte alcançada |
| Tarjan iterativo (componentes fortemente conexas) | F-RES | G_P | O(V + E) | Iterativo por causa do limite de recursão |
| Ranking de criticidade | F-RES-2 | G_P | O(c × custo da eficiência) | c candidatos, com amostragem |
| Yen (k trajetos alternativos) | F-ROTA-OPC | G_E | O(k V (V + E) log V) | Opcional |
| Propagação de rótulos (comunidades) | F-MET-OPC | G_P | O(E) por iteração | Opcional |

### 3.6 Interface

Aplicação Streamlit com várias páginas:

- **Início** (Arthur): escolha do conjunto de dados, resumo da rede (paradas, linhas e arestas por visão) e mapa.
- **Uma página por feature**, escrita pelo dono: Trajetos (Henrique), Espera (Miguel), Baldeações (Rafael), Centralidades (Thiago), Eficiência (Arthur) e Falhas (Caio). A página Desempenho só existe se a etapa opcional de benchmark for feita.
- **Componente de mapa** (Arthur): desenha paradas, linhas, caminhos e mapas de calor; todas as páginas usam o mesmo.

Cada página segue o contrato de `docs/fontes/plano-de-projeto.md` §9: um módulo com uma função `render(rede)`. A rede é carregada uma vez e fica em cache.

### 3.7 Avaliação

**Corretude (obrigatória).** Dois tipos de teste automático, com pytest:

- **Gabarito à mão.** Grafos pequenos cuja resposta foi calculada no papel, com casos de borda: grafo desconexo, empate, aresta de peso zero, origem igual ao destino. Exemplo: num grafo de 5 vértices, o Dijkstra de A a E deve dar 7 pelo caminho A, C, E. Também propriedades verificáveis: BFS e Dijkstra com pesos 1 dão as mesmas distâncias; remover uma aresta nunca diminui uma distância.
- **Comparação de resultado com NetworkX.** O teste sorteia grafos aleatórios com semente fixa, monta o mesmo grafo no nosso núcleo e no NetworkX, roda os dois algoritmos e confere se as respostas coincidem. O NetworkX serve só de gabarito automático: fica em `tests/`, nunca em `src/`, e não participa da ferramenta. O resultado precisa ser igual; o tempo não importa aqui.

**Desempenho (obrigatório, mínimo).**

- Complexidade teórica de tempo e de espaço de cada algoritmo, na docstring e justificada no arquivo da feature.
- Tempo medido na rede real: média de 5 execuções com a função `medir` (`docs/fontes/plano-de-projeto.md` §9), registrada no arquivo da feature com o tamanho da rede (V e E) e a máquina usada. Esses números alimentam a seção de avaliação de desempenho do relatório.

**Etapa opcional: benchmark.** Só entra se, em 15/11, todas as features essenciais e desejáveis cumpriram o Definition of Done. Janela de 16/11 a 18/11, conduzida por Rafael, só em `benchmarks/` e `tests/`, sem tocar `src/`:

- Comparação de tempo com o NetworkX no mesmo grafo e na mesma máquina. O nosso pode ser mais rápido ou mais lento; o que se reporta é o resultado, com a explicação.
- Complexidade empírica: tempo em função de V + E em redes sintéticas de tamanho crescente, em escala log-log, com a inclinação comparada à complexidade teórica.
- Página Desempenho na interface.

**Limitações a discutir.** Horários programados, não tempo real; espera de H/2 supõe passageiro chegando ao acaso; sem capacidade dos veículos; sem demanda real (pares origem-destino sorteados de forma uniforme); caminhada em linha reta.

### 3.8 Diagramas UML

Fontes PlantUML em `docs/diagramas/`. Globais (classes, componentes e casos de uso) até 03/11; um por feature (sequência ou atividade) no Definition of Done.

## Timeline

### Criação 29/10/2026: gerado a partir do plano de desenvolvimento aprovado pelo grupo.
