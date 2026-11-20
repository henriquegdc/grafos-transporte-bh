# Roteiro do vídeo (ENT-VIDEO)

Item H9 do `plano.md`; formato do plano de projeto §14.4. Gravação em 20/11/2026, à noite, com o
app rodando sobre o `main`. Duração alvo: **15 min 15 s** (exigido: 12 a 18 min).

As cenas usam o roteiro e os resultados dos arquivos em
`docs/plano-de-desenvolvimento/features/`. Cada resultado informa o feed da medição.

- As cenas 7, 8, 18 e 19 dependem dos PRs [#67](https://github.com/henriquegdc/grafos-transporte-bh/pull/67), [#69](https://github.com/henriquegdc/grafos-transporte-bh/pull/69) e
  [#70](https://github.com/henriquegdc/grafos-transporte-bh/pull/70). Grave cada cena só quando a opção correspondente estiver disponível
  na `main`. Se as quatro forem omitidas, o roteiro dura **13 min 15 s**. Ajuste os tempos
  de início na montagem.
- O app grava sobre o feed de 18/11 (`dados/brutos/bhtrans.zip`, SHA-256 `8cb0a498…f6d6`).
  Medições feitas em feeds anteriores (05/11, 11/11, 16/11) podem mostrar outro valor na tela.
  Nesses casos, a fala cita o número do arquivo da feature como "medido no relatório" e não
  lê o valor da tela como se fosse o mesmo.
- Quem fala é o dono da feature (AGENTS.md §0). Extensões feitas em 20/11 por Henrique ou
  Miguel ficam com o dono da feature-mãe.

## Visão geral

| Cena | Início | Duração | Quem | Feature | Página |
|---|---|---|---|---|---|
| 1 | 00:00 | 0:40 | Miguel | Abertura: problema e dados (P0-DADOS) | Início |
| 2 | 00:40 | 0:45 | Henrique | Modelagem: G_P, G_E, G_L, G_T (P0-MODELO) | Início + diagrama |
| 3 | 01:25 | 1:00 | Henrique | F-ROTA, trajeto mais rápido | Trajetos |
| 4 | 02:25 | 0:35 | Henrique | F-ROTA-2, ponto no mapa e A* | Trajetos |
| 5 | 03:00 | 0:30 | Henrique | F-ROTA-OPC, alternativos (Yen) | Trajetos |
| 6 | 03:30 | 1:00 | Miguel | F-ESPERA, espera H/2 | Espera |
| 7 | 04:30 | 0:35 | Miguel | F-ESPERA-2, quadro de horários e Monte Carlo | Espera |
| 8 | 05:05 | 0:25 | Miguel | F-ESPERA-OPC, sensibilidade ao intervalo | Espera |
| 9 | 05:30 | 0:55 | Rafael | F-BALD, menos baldeações | Baldeações |
| 10 | 06:25 | 0:35 | Rafael | F-BALD-2, quanto custa trocar menos | Baldeações |
| 11 | 07:00 | 0:25 | Rafael | F-BALD-OPC, trajetos não dominados | Baldeações |
| 12 | 07:25 | 0:30 | Thiago | P0-GRAFO, grafo, heap e Dijkstra próprios | código |
| 13 | 07:55 | 0:55 | Thiago | F-MET, grau e intermediação | Centralidades |
| 14 | 08:50 | 0:25 | Thiago | F-MET-2, proximidade | Centralidades |
| 15 | 09:15 | 0:25 | Thiago | F-MET-OPC, comunidades | Centralidades, aba Comunidades |
| 16 | 09:40 | 0:20 | Arthur | P0-UI, como a interface se organiza | Início |
| 17 | 10:00 | 0:50 | Arthur | F-EFI, eficiência e tempo médio | Eficiência |
| 18 | 10:50 | 0:35 | Arthur | F-EFI-2, isócronas e índice de desvio | Eficiência |
| 19 | 11:25 | 0:25 | Arthur | F-EFI-OPC, pico contra fora do pico | Eficiência |
| 20 | 11:50 | 1:00 | Caio | F-RES, falha de parada e de linha | Falhas, aba Falha única |
| 21 | 12:50 | 0:30 | Caio | F-RES-2, ranking de criticidade | Falhas, aba Ranking |
| 22 | 13:20 | 0:30 | Caio | F-RES-OPC, falhas múltiplas | Falhas, aba Falhas múltiplas |
| 23 | 13:50 | 0:50 | Rafael | Desempenho e NetworkX (P0-AVAL, F-AVAL, F-AVAL-OPC) | Desempenho |
| 24 | 14:40 | 0:35 | Caio e Rafael | Garantias e limitações; encerramento | Início |
| | **15:15** | | | | |

Tempo por pessoa: Henrique 2:50, Miguel 2:40, Rafael 2:45 (mais a parte dele na cena 24),
Thiago 2:15, Arthur 2:10, Caio 2:00 (mais a parte dele na cena 24). Todos falam.

## Abertura

### Cena 1 · 00:00 · 0:40 · Miguel · problema e dados

- **Tela:** página Início com `dados/brutos/bhtrans.zip` já carregado; resumo (dia de serviço,
  paradas, linhas, padrões, viagens) e o mapa.
- **Fala:**
  - Pergunta do trabalho: como é andar de ônibus em BH? Seis perguntas: trajeto mais rápido,
    espera, baldeações, paradas importantes, eficiência e falhas.
  - Dado: GTFS da PBH, CSVs separados (linhas, paradas, viagens, horários, calendário). O leitor
    escolhe um dia de serviço e junta tudo sem perder a identidade de cada viagem;
    `stop_times.txt` é lido em fluxo, O(R + N log N).
  - Regra do trabalho: grafo, heap e algoritmos são nossos; nenhuma biblioteca de grafo em `src/`.
- **Números:** 9.660 paradas, 303 linhas, 698 padrões, 24.503 viagens (feed de 18/11, F-EFI).
  Leitura do feed em 7,8 s (7,753 s ± 0,114 s, feed de 05/11, P0-DADOS).
- **Limitação:** só o serviço do dia escolhido é validado.

### Cena 2 · 00:40 · 0:45 · Henrique · modelagem em quatro visões

- **Tela:** `docs/diagramas/ge-exemplo.png` ao lado do mapa da Início; trocar a faixa horária e
  mostrar as camadas.
- **Fala:**
  - O GTFS é tabela, os algoritmos precisam de grafo. Quatro visões do mesmo dado:
    - G_P: vértice = parada; arestas de viagem (tempo mediano, piso de 1 s) e de caminhada.
      Centralidades, eficiência e falhas.
    - G_E: plataforma por (parada, padrão); baldear passa pelo embarque, que custa a espera.
      Trajeto mais rápido.
    - G_L: um vértice por padrão de linha. Menos baldeações.
    - G_T: quadro de horários, a aresta guarda os horários. Chegada mais cedo.
  - Caminhada por grade espacial, sem comparar todos os pares. Construção O(V + K + L + N log N).
- **Números:** G_P com V = 9.660 e E = 122.799; G_E do pico da manhã com V = 46.102 e
  E = 209.025 (feed de 18/11, F-ROTA). Cerca de 0,3 s por visão (G_E do pico em
  341,9 ms ± 13,1 ms, feed de 05/11, P0-MODELO). G_L do pico com V = 501 e E = 85.606 (feed de
  11/11, F-BALD). Após o merge da F-ESPERA-2, citar também
  G_T com 9.659 vértices e 146.563 arestas (feed de 05/11, F-ESPERA-2).
- **Limitação:** um tempo de viagem para o dia todo; a partida conta na faixa em que ocorre (D10).

## Pergunta 1 · Qual o trajeto mais rápido? (Henrique)

### Cena 3 · 01:25 · 1:00 · F-ROTA

- **Tela:** Trajetos; faixa "pico da manhã"; modo lista; origem 14789899 (Avenida Afonso Pena
  1421), destino 14790311 (Avenida Vilarinho 1300). Mostrar as métricas (total, a pé, espera,
  ônibus, baldeações), a tabela de trechos e o mapa com uma camada por trecho. Trocar a faixa para
  "entrepico" e mostrar o trajeto mudar.
- **Fala:**
  - Problema: de uma parada a outra, qual caminho chega antes contando caminhada, espera e troca?
  - Um Dijkstra só no G_E, parando no destino; trocar de linha passa pelo embarque e paga a
    espera; reconstrução em trechos. O((V + E) log V).
- **Números:** este par, 50 min 09 s entre as paradas, linhas 4103 e 63, 1 baldeação (feed de
  18/11). 65,9 ms por consulta em 200 pares; 0 divergências com o NetworkX em 200; tempo mediano
  de 61,1 min (feed de 18/11).
- **Limitação:** o tempo é o esperado da faixa (espera H/2), não o de um horário de saída exato.

### Cena 4 · 02:25 · 0:35 · F-ROTA-2

- **Tela:** Trajetos, modo "Mapa ou coordenadas", pico da manhã: clicar na origem
  (-19,9245; -43,9352) e no destino (-19,8157; -43,9542). Mostrar as paradas mais próximas, a
  caminhada, o tempo porta a porta e abrir a tabela "Dijkstra × A*".
- **Fala:**
  - O passageiro clica onde está e onde quer ir; a ferramenta acha a parada mais próxima.
  - A*: f = g + h, h = distância em linha reta / velocidade máxima; h nunca passa do custo real,
    logo o trajeto é o ótimo.
- **Números:** paradas a 68 m e 28 m; 51 min 29 s porta a porta (feed de 18/11). A* com o mesmo
  custo do Dijkstra em 200 de 200, mas expande 99,7% dos vértices (mediana) e é mais lento
  (81,0 contra 64,1 ms, medianas da medição de 20/11): trechos de 1 s no GTFS dão velocidade máxima de 1.258 m/s, e a
  h não vê as esperas.
- **Limitação:** velocidade realista podaria mais, mas perderia a garantia de ótimo.

### Cena 5 · 03:00 · 0:30 · F-ROTA-OPC

- **Tela:** Trajetos, pico da manhã, origem 14791479, destino 14788103, k = 5. Acione
  "Listar trajetos alternativos" antes de gravar. Mostre a coluna "Variantes" e escolha
  a segunda sequência em "Trajeto no mapa", se ela aparecer no feed carregado.
- **Fala:**
  - O mais rápido pode ter uma troca a mais ou uma linha que a pessoa evita.
  - Yen: cada vértice do trajeto anterior vira desvio; desativa as saídas já usadas, busca o resto
    com A* e reativa. O(k · n · (V + E) log V); por isso só no botão.
- **Números (feed de 18/11, medição de 20/11):** Yen puro com medianas de 3,1 s para k = 3
  e 4,3 s para k = 5, com máximo de 32,7 s. Para k = 5, o filtro examinou até dez caminhos
  por par e encontrou uma segunda sequência em um dos oito pares, o da demonstração.
- **Limitação:** o teto da busca pode deixar outras sequências de fora.

## Pergunta 2 · Quanto se espera? (Miguel)

### Cena 6 · 03:30 · 1:00 · F-ESPERA

- **Tela:** Espera; "Faixa da tabela" = pico_manha; tabela de intervalos por linha e padrão
  (H/2, provisória, sem serviço). Origem 14788851, destino 14792190, saída 08:00; simular e
  mostrar caminhada, espera, viagem e o mapa.
- **Fala:**
  - Primeiro horário, partidas distintas, intervalo H, espera H/2, que vira o custo do embarque
    no G_E; o trajeto usa o Dijkstra que já existe. Diagrama `atividade-espera.png`.
  - Espera provisória quando a linha tem poucas partidas na faixa.
- **Números:** nesse par, 40,24 min no total, 15,34 min de espera (feed de 05/11, F-ESPERA). No
  pico da manhã, 501 padrões com serviço, 481 com estimativa e 20 provisórios (feed de 05/11).
  `simular_trajeto_completo` em 248,7 ms.
- **Limitação:** faixa fixa, horários programados; H/2 só vale para intervalos regulares.

### Cena 7 · 04:30 · 0:35 · F-ESPERA-2

- **Tela:** Espera, modo "Quadro de horários"; mesmo par, 08:00; simular; apontar a troca no mapa;
  mostrar total e espera ao lado da estimativa H/2; mostrar a janela e os dois histogramas do Monte
  Carlo.
- **Fala:**
  - G_T guarda os horários de cada trecho; chegada mais cedo é um Dijkstra cujo rótulo é o
    instante de chegada, com busca binária da próxima partida (rede FIFO).
  - Monte Carlo: sorteia horários de saída numa janela e mostra a distribuição do total e da
    espera. Perder uma partida muda a espera.
- **Números (feed de 05/11, serviço de 04/11):** 23,67 min pelo quadro e 40,24 min por H/2,
  com esperas de 1,87 e 15,34 min. Médias em macOS, medidas em 20/11
  na F-ESPERA-2: consulta em 6,98 ms, G_T em 318,55 ms e 30 sorteios em 279,31 ms.
- **Limitação:** horário programado, não o real do ônibus.

### Cena 8 · 05:05 · 0:25 · F-ESPERA-OPC

- **Tela:** Espera, "Simular alteração do intervalo de uma linha". Use a linha 561787,
  pico da manhã, multiplicador 2, dez pares e semente 42. Clique em "Comparar cenários"
  e mostre as tabelas com as esperas e os tempos por par.
- **Fala:**
  - E se a linha passar com metade da frequência? O intervalo da linha muda na tabela antes de
    calcular as esperas e montar o G_E; os pares são recalculados.
  - Dobrar o intervalo dobra a espera estimada dos padrões afetados. O melhor tempo de um
    par pode ficar igual se houver um trajeto com o mesmo custo que dispense esses padrões.
- **Números (serviço de 04/11):** a espera no padrão passou de 566,67 s a 1.133,33 s.
  A comparação completa levou 1,504 s em média.

## Pergunta 3 · Como trocar menos de ônibus? (Rafael)

### Cena 9 · 05:30 · 0:55 · F-BALD

- **Tela:** Baldeações; "Linhas consideradas" = pico da manhã; origem 14786076 (Barreiro),
  destino 14789446 (Pampulha). Métricas, sequência de linhas, tabela de trechos e mapa (uma cor
  por linha, caminhada tracejada, círculos laranja nas trocas). Trocar para "dia inteiro".
- **Fala:**
  - Muita gente prefere menos trocas, mesmo demorando mais.
  - G_L, um vértice por padrão; o BFS comum erra porque a troca pode ficar "para trás" no padrão
    (exemplo S-B-A-E); camadas com a posição de embarque. O(r (V + E + T)).
- **Números:** nesse par, 2 baldeações, linhas 342 → 6350 → 643 (feed de 11/11; conferir na tela
  com o feed de 18/11 antes de dizer). 36,7 ms por consulta; 0 divergências com o NetworkX em
  200 pares; o BFS comum daria menos baldeações que o possível em 14 de 200 (feed de 11/11).
- **Limitação:** conta trocas, não tempo.

### Cena 10 · 06:25 · 0:35 · F-BALD-2

- **Tela:** Baldeações, pico da manhã; origem 14788909 (Rua Curitiba 1026), destino 14791748
  (Rua Gentil Portugal do Brasil 54). Bloco "Menos baldeações contra mais rápido": tempo a mais,
  baldeações evitadas e a tabela com os dois trajetos.
- **Fala:**
  - Quanto custa trocar menos? O k vem da G_L, o tempo do G_E; Dijkstra com o número de
    embarques no estado. O((k + 2)(V + E) log((k + 2) V)).
- **Números:** nesse par, o mais rápido faz 3054 → 30 → 3053 em 44,2 min; a 3053 direta leva
  45,6 min: evita 2 baldeações por 1,4 min (feed de 11/11; conferir na tela). Em 200 pares, o mais
  rápido já tinha o mínimo em 160; nos outros 40, evitar custou 1,5 min na mediana e até
  14,5 min; 213 ms por par.
- **Limitação:** mostra dois pontos, não a fronteira inteira; isso é a cena seguinte.

### Cena 11 · 07:00 · 0:25 · F-BALD-OPC

- **Tela:** Baldeações, pico da manhã; origem 14791366, destino 14793436; tabela "Trajetos não
  dominados"; trocar o trajeto em "Trajeto no mapa" e mostrar o mapa mudar.
- **Fala:**
  - Não precisa escolher só entre os extremos. Para cada k até as baldeações do mais rápido,
    Dijkstra com limite; guarda só quem reduz o tempo: a fronteira de Pareto.
    O(B² (V + E) log(BV)).
- **Números:** 0 a 4 baldeações, tempo caindo de 151,4 para 98,5 min (feed de 18/11). 164,6 ms
  por par em média; 170 de 200 pares com mais de um ponto na fronteira.

## Pergunta 4 · Quais paradas mais importam? (Thiago)

### Cena 12 · 07:25 · 0:30 · P0-GRAFO

- **Tela:** código: `vizinhos` e `desativar_vertice` do grafo, o `HeapMin` e o diagrama
  `sequencia-dijkstra.png`.
- **Fala:**
  - Toda pergunta vira busca num grafo; grafo, heap binário e buscas são nossos (sem `heapq`).
  - Dijkstra com inserção preguiçosa: no exemplo 0→1 (4), 0→2 (1), 2→1 (2), 1→3 (1), a entrada
    (4, 1) fica no heap e é descartada; continua O((V + E) log V).
- **Números:** Dijkstra completo em 249,5 ms no G_P e 776,8 ms no G_E, distâncias iguais às do
  NetworkX; heap com 100 mil inserções e 100 mil extrações em 1,463 s (feed de 16/11).
- **Limitação:** sem pesos negativos; o grafo desativa, não remove.

### Cena 13 · 07:55 · 0:55 · F-MET

- **Tela:** Centralidades, aba Centralidades; métrica grau de saída (só ônibus) e a distribuição
  de graus; depois intermediação com "origens sorteadas" = 50; ranking com o "±" e o mapa de calor.
- **Fala:**
  - Não só as paradas com mais linhas: as que ficam no meio dos caminhos mais rápidos.
  - Brandes: um Dijkstra que conta os caminhos mínimos e a volta acumulando dependências;
    O(V (V + E) log V). O exato levou 44 min, então amostramos k origens (N/k vezes a soma, não
    viesada, com erro padrão).
- **Números (feed de 16/11):** 75% das paradas com grau 1; máximo 20 ligações (Av. Afonso Vaz de
  Melo 250). Com 50 origens, 14 s na página, 9 das 10 primeiras iguais às do exato, erro mediano
  de 12% no top 100; a primeira é a Av. Presidente Antônio Carlos 8271, como no exato.
- **Limitação:** G_P sem espera nem horário; o "±" só é confiável nas paradas centrais.

### Cena 14 · 08:50 · 0:25 · F-MET-2

- **Tela:** Centralidades, métrica Proximidade, 50 origens; ranking e mapa de calor.
- **Fala:**
  - Proximidade: quão rápido saio desta parada para o resto da cidade. Um Dijkstra por origem;
    a rede não é fortemente conexa, então Wasserman e Faust, que pune quem alcança só parte dela.
- **Números (feed de 18/11):** com 50 origens, 2,2 s (2,183 s ± 0,013 s); as cinco primeiras na
  Av. Presidente Antônio Carlos (561, 583, 584, 582 e 955). Igual ao NetworkX em 15 grafos
  aleatórios (tolerância 1e-12).

### Cena 15 · 09:15 · 0:25 · F-MET-OPC

- **Tela:** Centralidades, aba Comunidades, semente 2026, "Detectar comunidades": número de
  comunidades, modularidade, tabela "Maiores comunidades" e o mapa colorido.
- **Fala:**
  - Propagação de rótulos: cada parada adota o rótulo mais comum entre as vizinhas até nada mudar.
    A modularidade, nossa, mede a qualidade.
- **Números (feed de 18/11):** 604 comunidades em 11 iterações, modularidade 0,8062, igual à do
  NetworkX para a mesma partição; 140 ms. Entre as sementes 2026 e 2030, de 587 a 608 comunidades.

## Pergunta 5 · A rede é eficiente? (Arthur)

### Cena 16 · 09:40 · 0:20 · P0-UI

- **Tela:** Início: escolher a fonte (`dados/rede-teste/` ou `dados/brutos/`), carregar, resumo,
  inconsistências, V e E das visões e as camadas do mapa.
- **Fala:**
  - Pasta e ZIP usam o mesmo `ler`; a rede fica em cache por sessão; cada página publica
    `render(rede)`. Um erro de leitura preserva a rede anterior.
- **Números:** nenhum (o carregamento no feed real não foi medido).

### Cena 17 · 10:00 · 0:50 · F-EFI

- **Tela:** Eficiência; "Origens para eficiência global" = 100, "Pares OD para tempo médio" =
  100, semente 2026; "Calcular métricas" (já calculado antes). Erro padrão e pares alcançáveis.
- **Fala:**
  - Eficiência global: média de 1/d entre paradas no G_P; tempo médio no G_E com caminhada,
    espera e ônibus. Um Dijkstra por origem sorteada, sem busca por par.
- **Números (feed de 18/11):** eficiência 5,884 × 10⁻⁴ s⁻¹, erro padrão 1,20 × 10⁻⁵, com 100
  origens; 8,7 s para a eficiência e 26,3 s para o tempo médio de 100 pares (Ryzen 7 7730U).
- **Limitação:** depende da amostra e da semente; a espera do G_E é a H/2 da F-ESPERA.

### Cena 18 · 10:50 · 0:35 · F-EFI-2

- **Tela:** Eficiência, modo "Isócronas", parada 14788851 no pico da manhã. Compare os
  alcances ao calcular com os limites de 15 e 60 min. Abra "Índice de desvio" com 12 pares
  e mostre a tabela "Pares com maior desvio".
- **Fala:**
  - Isócrona: Dijkstra no G_E com limite T a partir da parada. Índice de desvio: distância na
    rede dividida pela distância em linha reta (e tempo por km em linha reta).
- **Números (serviço de 04/11):** em 15 e 60 min, 68 e 4.120 paradas alcançadas.
  A isócrona de 60 min levou 39,99 ms em média. Na amostra de 12 pares, o maior desvio
  foi 2,215 km/km (14793286 → 14785528).

### Cena 19 · 11:25 · 0:25 · F-EFI-OPC

- **Tela:** Eficiência, modo "Comparar faixas", 12 pares, semente 2026. Mostre a eficiência
  na tabela e o tempo médio nas barras.
- **Fala:**
  - A amostra de pares é a mesma nas quatro faixas. O serviço e a espera variam por faixa.
  - A eficiência atribui zero aos pares inalcançáveis. O tempo médio considera os alcançáveis.
- **Números (serviço de 04/11):** os 12 pares foram alcançáveis em todas as faixas.
  A média foi de 57,48 min no pico da manhã e 62,36 min à noite.

## Pergunta 6 · E se algo falhar? (Caio)

### Cena 20 · 11:50 · 1:00 · F-RES

- **Tela:** Falhas, aba "Falha única": parada 14784108 (mais saídas de viagem), simular; depois a
  linha 832 (`562146`), simular: componentes antes e depois, paradas fora da rede principal no
  mapa, perda de eficiência e o aviso de perda amostrada.
- **Fala:**
  - A falha não reconstrói o grafo: desliga vértices e arestas e religa no fim.
  - Componentes fortemente conexas com Tarjan iterativo, O(V + E): no G_P a DFS chega a 4.657
    níveis, e o Python para em 1.000. Eficiência com um Dijkstra por origem, O(s (V + E) log V).
- **Números (feed de 11/11):** parada 14784108, 0 paradas desconectadas, perda de 0,0357%. Linha
  832: 33 paradas fora da rede principal; perda exata de 0,5040%; amostrada variou de 0,24% a
  2,99% conforme a semente, por isso a página avisa.
- **Limitação:** perda estrutural no G_P (sem espera nem horário), não tempo porta a porta.

### Cena 21 · 12:50 · 0:30 · F-RES-2

- **Tela:** Falhas, aba "Ranking": paradas candidatas 10, linhas candidatas 20, eficiência 30
  origens, intermediação 100 origens; custo estimado; "Calcular ranking" (já calculado antes).
- **Fala:**
  - Candidatos: paradas de maior intermediação e linhas sorteadas; todos com as mesmas origens.
    Custo de (c + 1) eficiências.
- **Números (feed de 18/11):** 1.º lugar, parada 36020152 (Rua Deputado Salim Nacur 173), perda
  de 1,107%; linha mais crítica 9550, em 5.º, 0,398%. A parada de maior intermediação (Av.
  Amazonas 322) causa só 0,139%: centralidade não é criticidade. Ranking em 38,9 s.
- **Limitação:** a intermediação é filtro; parada que corta um ramal pode ficar de fora.

### Cena 22 · 13:20 · 0:30 · F-RES-OPC

- **Tela:** Falhas, aba "Falhas múltiplas", modo "Dirigida x aleatória": paradas removidas 10,
  eficiência 30 origens, intermediação 100; "Comparar remoções" (já calculado antes); gráfico.
- **Fala:**
  - Falhas em sequência; o estado final é igual a tirar tudo de uma vez. A dirigida tira primeiro
    a de maior intermediação.
- **Números (feed de 18/11):** após 10 remoções, perda de 1,734% na dirigida contra 0,245% na
  aleatória; nenhuma parada desconectada.
- **Limitação:** a dirigida usa a intermediação da rede intacta, sem recalcular.

## Fechamento

### Cena 23 · 13:50 · 0:50 · Rafael · desempenho e NetworkX

- **Tela:** página Desempenho: tabela "Comparação com o NetworkX" (coluna "Resultados iguais"
  toda "sim", razão de tempo) e gráfico log-log da complexidade empírica. Mostre a tabela
  consolidada do relatório se a F-AVAL ([#25](https://github.com/henriquegdc/grafos-transporte-bh/issues/25)) estiver disponível.
- **Fala:**
  - `medir`: N execuções com `perf_counter`, só a chamada dentro do cronômetro; média e desvio
    amostral. Cada número vem com V, E e máquina.
  - Conferimos BFS, Dijkstra, Brandes e Tarjan contra o NetworkX no mesmo grafo; nas redes
    sintéticas, a inclinação do log-log segue a complexidade teórica.
- **Números (F-AVAL-OPC, medição de 20/11):** G_P real, 20 origens. Dijkstra em 769,6 ms
  no projeto e 574,6 ms no NetworkX (razão 1,34). Brandes em 864 ms e 1.036 ms (razão 0,83).
  Os resultados coincidiram. Inclinações nas redes sintéticas: BFS 1,01, Dijkstra 1,06,
  Tarjan 1,10 e Brandes 2,04.
- **Limitação:** tempo de parede depende da máquina; por isso razão e inclinação.

### Cena 24 · 14:40 · 0:35 · Caio (0:10) e Rafael (0:25) · garantias e limitações

- **Tela:** README ou terminal com `python scripts/verificar_imports.py`; depois a Início.
- **Fala (Caio):** o hook de pre-commit roda `verificar_imports.py` e bloqueia biblioteca de grafo
  em `src/`; NetworkX só em `tests/` e `benchmarks/`.
- **Fala (Rafael):**
  - Um dia de serviço e horários programados; espera H/2 por faixa (o quadro de horários da
    F-ESPERA-2 mostra quanto isso erra).
  - G_P sem espera: centralidade e falhas são estruturais.
  - Amostragem com erro medido (intermediação, eficiência, perda de falhas).
  - A* quase não poda neste feed; alternativos do Yen tendem a variar pouco.
  - Encerramento: link do repositório e nomes dos seis.

## Checklist antes de gravar

1. **Código:** atualizar a `main` e rodar `pytest`. Conferir Trajetos e Desempenho no menu
   e verificar quais cenas das extensões de Espera e Eficiência já podem ser gravadas.
2. **Feed:** `dados/brutos/bhtrans.zip` de 18/11, SHA-256 `8cb0a498b90b227221d0234e3b6386a7dfbe375a2cb2e52e86238010be05f6d6`
   (`dados/brutos/bhtrans.json`). Não baixar outro antes de gravar.
3. **App:** `.venv` ativo; `streamlit run src/transporte/interface/app.py`; carregar o feed na
   Início e esperar o resumo.
4. **Cache aquecido** (na mesma sessão do navegador que vai gravar, porque os resultados ficam na
   sessão):
   - Trajetos: par da cena 5, k = 5, "Listar trajetos alternativos".
   - Centralidades: intermediação e proximidade com 50 origens; Comunidades com semente 2026.
   - Eficiência: 100 origens, 100 pares, semente 2026 (cerca de 35 s).
   - Falhas: Ranking (10, 20, 30, 100; cerca de 40 s) e Dirigida x aleatória (10, 30, 100).
     A falha única da linha 832 e da parada 14784108 leva dezenas de segundos: rodar ao vivo e
     cortar a espera na edição.
5. **Conferir na tela, antes de falar:** pares das cenas 9 e 10 (medidos no feed de 11/11) e os
   valores da F-ESPERA e F-ESPERA-2 (feed de 05/11). Se a tela mostrar outro valor, falar o da tela
   como "no feed de hoje" e o do arquivo como "medido no relatório", ou trocar o par.
6. **Extensões:** conferir os valores na tela para as cenas 7, 8, 18 e 19. Os exemplos de
   Espera e Eficiência foram medidos com serviço de 04/11. Verificar se a tabela consolidada
   está no relatório antes de incluir essa tela na cena 23.
7. **Tela:** 1920 × 1080, zoom do navegador em 110% a 125%, barra lateral do Streamlit visível,
   tema claro, notificações desligadas, outras abas fechadas.
8. **Gravação:** OBS (ou Xbox Game Bar, Win + Alt + R) com microfone testado; 30 fps; um arquivo
   por cena, nome `cena-NN-nome.mp4`.

## Como gravar

Recomendação: **por cena**, e montar depois. Motivos: as consultas lentas podem ser cortadas sem
regravar, um erro custa só a cena, cada pessoa grava o seu trecho quando terminar (plano §6, C4)
e a soma dos tempos é ajustada na montagem para ficar entre 12 e 18 min. Gravação contínua só
compensa se todos estiverem juntos e o cache estiver todo aquecido, e qualquer erro obriga a
recomeçar.

Na montagem: ordem da tabela da visão geral; legenda com o nome de quem fala no início de cada
bloco; conferir a duração final (alvo 15 min) antes de publicar.
