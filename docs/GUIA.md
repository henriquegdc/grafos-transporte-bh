# Guia do projeto · Análise de redes de transporte público

Para quem não escreveu o código. Explica como a ferramenta funciona e por que foi feita assim.
Não cria requisito: explica o que docs/fontes/ decide. Integrador: Caio.

## 1. Visão geral
O problema, as seis perguntas, o caminho do dado: GTFS -> modelo normalizado -> visões do grafo
-> algoritmos -> interface. Um diagrama de componentes.

## 2. Dados e GTFS (Miguel)

O GTFS é um conjunto de CSVs. `stops.txt` identifica paradas e coordenadas;
`routes.txt`, as linhas; `trips.txt`, as viagens; `stop_times.txt`, a sequência de
paradas e horários de cada viagem. `calendar.txt` e `calendar_dates.txt` dizem quais
serviços circulam na data escolhida; `frequencies.txt`, quando existe, fornece partidas
por intervalo. O leitor aceita pasta ou ZIP e escolhe uma quarta-feira ativa dentro da
vigência do feed quando o usuário não passa uma data.

O fluxo é: validar os arquivos necessários, selecionar os serviços ativos, percorrer
`stop_times.txt` em fluxo, agrupar viagens da mesma linha com a mesma sequência exata
de paradas e construir a `Rede`. Cada parada mantém o seu `stop_id`, inclusive quando
dois sentidos usam pontos próximos. A rede guarda partidas por padrão/parada,
`viagens[padrão]` com as sequências de horários alinhadas à sequência de paradas e
`viagens_por_id` para conservar os identificadores GTFS. Assim o construtor calcula a
diferença entre paradas consecutivas do mesmo ônibus; uma lista de horários por parada
perderia essa relação. Uma viagem definida por `frequencies.txt` gera uma sequência
em `viagens[padrão]` para cada partida da janela, sem contar a viagem de referência
uma segunda vez. Isso permite que o G_E encontre partidas em todas as faixas do dia.

Horários como `24:10:00` são válidos: representam 00:10 do dia seguinte dentro da
mesma jornada de serviço. Linhas inválidas são relatadas em `Rede.inconsistencias` e
não entram no modelo. O recorte aceita uma caixa de coordenadas e/ou ids de linhas;
ao selecionar linhas, remove também as paradas que nenhuma delas atende.
Quando o corte remove uma parada no meio de um padrão, os trechos restantes ficam
separados para não inventar um percurso direto. Trechos que resultem na mesma linha e
sequência de paradas são reunidos em um padrão, com todas as viagens preservadas;
assim a espera não é calculada separadamente para duas plataformas equivalentes.
O arquivo GTFS bruto e seu registro
de origem, data e SHA-256 ficam em `dados/brutos/`, fora do Git; a rede pequena com
gabarito manual fica em `dados/rede-teste/`.

Escolhemos processar `stop_times.txt` em fluxo porque o feed real descompactado é
grande. O modelo normalizado preserva a informação necessária às visões G_P e G_E,
sem acoplar a leitura aos algoritmos de grafo. A validação atual cobre os serviços
do dia selecionado; uma auditoria de todos os dias do calendário exigiria outra
passagem pelos dados. A explicação do fluxo aparece no diagrama
`docs/diagramas/atividade-p0-dados.png`.

## 3. Modelagem e visões do grafo (Henrique)
G_P, G_E, G_L e G_T: o que é vértice, o que é aresta, que pergunta cada uma responde e por quê.
Espera esperada e paradoxo da inspeção. Parâmetros e seus motivos.

### Construtores de G_P e G_E (P0-MODELO)

Os construtores, em `src/transporte/modelo/construtores.py`, transformam a `Rede` normalizada
da P0-DADOS nas duas visões usadas por F-ROTA, F-ESPERA, F-MET, F-EFI e F-RES. Eles leem só
três campos da `Rede` (protocolo `RedeConstrutores`): `paradas`, `padroes` e `viagens[padrão]`,
que dá os horários de cada viagem na ordem das paradas. A identidade da viagem importa: o tempo
de A a B sai da subtração de horários **do mesmo ônibus**.

```python
from transporte.modelo.construtores import construir_gp, construir_ge

gp = construir_gp(rede)                 # VisaoGP: um vértice por parada
ge = construir_ge(rede, "pico_manha")   # VisaoGE: paradas + plataformas, para uma faixa
ge.vertice_da_parada["A"]; ge.plataforma[("A", padrao_id)]
```

**G_P.** Um vértice por parada. Uma aresta VIAGEM a → b para cada par de paradas
consecutivas em algum padrão, com peso igual à mediana das diferenças de horário de todas as
viagens que passam por ali (D2). Arestas CAMINHADA nos dois sentidos entre paradas a até 300 m,
com peso distância / 1,2 m/s. Exemplo: viagens de 300, 360 e 300 s de A a B dão 300 s; se uma
tivesse −500 s (erro de cadastro), ela ficaria fora e a mediana de 60 e 80 seria 70 (D8).

**G_E.** Em G_P, continuar no ônibus e trocar de ônibus custam o mesmo. G_E cria uma
**plataforma** por (parada, padrão): para trocar de linha é preciso desembarcar (0 s), voltar à
parada e embarcar de novo, pagando a espera da nova linha (figura `docs/diagramas/ge-exemplo.png`;
passo a passo em `docs/diagramas/atividade-construir-ge.png`).

1. EMBARQUE parada → plataforma, com peso igual à espera da tabela `esperas` da F-ESPERA para
   (padrão, faixa), aplicada como veio (H/2 na versão essencial; 300 s enquanto a tabela não
   existe), só se alguma viagem do padrão parte na faixa (D10) e nunca na última parada (D9).
2. VIAGEM plataforma → plataforma seguinte, com a mediana daquele padrão.
3. DESEMBARQUE plataforma → parada, peso 0, nunca na primeira parada (D9).
4. CAMINHADA como em G_P.

Assim um único Dijkstra soma caminhada, espera, viagem e baldeações, e as baldeações de um
caminho são os embarques menos um (`VisaoGE.baldeacoes`). Uma linha circular usa uma plataforma
só por parada (D11).

**Caminhada sem O(V²).** Comparar as 9.659 paradas de BH duas a duas daria cerca de 93 milhões
de distâncias. A grade espacial põe cada parada numa célula do tamanho do raio e só compara
paradas de células vizinhas (9 por parada). A projeção usa o cosseno da maior latitude e a
célula tem 0,1% de folga, para nenhum par dentro do raio escapar; um teste confere a grade
contra a busca ingênua em 10 redes aleatórias.

**Complexidade.** Com V paradas, L plataformas, N horários e K pares a até o raio: G_P em
O(V + K + N log N) esperado (cada horário entra em uma diferença; as medianas ordenam), G_E em
O(V + K + L + N log N); O(V²) no pior caso da grade, com tudo numa célula. No feed real
(05/11, `feature-P0-MODELO.md`), G_P com 9.659 vértices e 122.732 arestas sai em 312,8 ms, e
G_E com 46.100 vértices e cerca de 208 mil arestas em 342 a 365 ms por faixa.

Por quê:

- **Mediana:** um horário errado desloca a média, quase não move a mediana.
- **Piso de 1 s em viagem e caminhada:** o GTFS arredonda horários (39 arestas de viagem do G_P
  terminam no piso, no feed de 09/11); peso 0 entre paradas distintas quebra a contagem de caminhos do Brandes.
  O desembarque fica com 0, porque não leva tempo e só liga a plataforma à própria parada.
- **Um G_E por faixa:** a espera muda ao longo do dia; um G_E só, com a espera média do dia,
  esconderia a diferença entre pico e entrepico.
- **pickle em `salvar` e `carregar` (D7):** o arquivo é cache local da ferramenta, nunca vem
  de fora.

Limitações: um tempo de viagem por trecho para o dia todo; ônibus que sai às 08h55 não dá
embarque às 09h20 no entrepico (D10); numa linha circular dá para "dar a volta" (D11); cada
variante de itinerário tem espera própria (D1); caminhada em linha reta, sem ruas.

## 4. Núcleo do grafo e heap (Thiago)
Lista de adjacência, desativação de vértices e arestas, heap binário, BFS e Dijkstra,
inserção preguiçosa, complexidades.

## 5. Features
Uma subseção por feature, copiada e ajustada de "Como funciona e por quê" do arquivo da feature:
5.1 Trajeto mais rápido · 5.2 Espera · 5.3 Baldeações · 5.4 Centralidades · 5.5 Eficiência ·
5.6 Falhas · 5.7 Desejáveis e opcionais que foram feitas.

### 5.1 Trajeto mais rápido (F-ROTA)

Dadas duas paradas, `trajeto_mais_rapido` acha o trajeto que chega mais cedo em média, somando
caminhada, espera e viagem, e diz o que fazer em cada parte.

```python
from transporte.algoritmos.trajeto import trajeto_mais_rapido

ge = construir_ge(rede, "pico_manha")
t = trajeto_mais_rapido(ge, "A", "C")   # None se não houver trajeto
t.tempo_total_s, t.baldeacoes, t.trechos, t.tempo_por_tipo()
```

Em G_E, trocar de linha obriga a desembarcar, voltar à parada e pagar um novo embarque, que
carrega a espera da nova linha (seção 3). Por isso basta um Dijkstra, sem penalidade arbitrária
por baldeação. Passo a passo (`docs/diagramas/sequencia-trajeto.png`):

1. Traduz as paradas em vértices de G_E; parada inexistente dá KeyError.
2. Roda o `dijkstra` do núcleo a partir da origem, parando quando o destino sai do heap. Com
   pesos não negativos, a distância de um vértice fechado é definitiva. Destino inalcançável
   devolve None.
3. Reconstrói o caminho por **arestas** (`caminho_arestas`), porque o tipo de cada passo está
   na aresta.
4. Baldeações = embarques − 1.
5. Agrupa em trechos: caminhadas seguidas viram um trecho a pé; embarque vira espera; viagens
   seguidas do mesmo padrão viram um trecho de ônibus, fechado pelo desembarque.

Exemplo, com pesos inventados: de A a C, L1 de A a B e L2 de B a C, espera de 300 s nas duas e
viagens de 240 e 180 s. Total 300 + 240 + 0 + 300 + 180 = 1.020 s, em quatro trechos (espera
L1, ônibus L1, espera L2, ônibus L2) e uma baldeação. Se andar de A a C levasse menos, o
trajeto seria um trecho a pé só.

**Complexidade.** O((V + E) log V) do Dijkstra com heap binário e inserção preguiçosa (O(V + E)
entradas no heap, cada uma O(log V)), mais O(V + k) da reconstrução; espaço O(V + E). No feed
real com as esperas da F-ESPERA (18/11, `feature-F-ROTA.md`), no G_E com V = 46.102 e
E = 209.025: 65,9 ms por consulta em média e 129,6 ms no pior caso de 200 consultas, tempo
mediano de 61,1 min e 0 divergências contra o NetworkX.

**A página Trajetos** (`interface/paginas/trajetos.py`, `docs/diagramas/sequencia-trajetos-pagina.puml`)
monta o G_E de cada faixa uma vez por sessão, com as esperas da F-ESPERA, e mostra as métricas
(tempo total, a pé, espera, ônibus, baldeações), a tabela de trechos e o mapa com cada trecho
numa camada. A origem e o destino vêm de uma lista de paradas ou de um ponto no mapa (F-ROTA-2,
seção 5.7); a mesma página compara Dijkstra e A\* e lista os alternativos do Yen.

Por quê: função em `algoritmos/` e não método da visão, para o A\* e o Yen entrarem no mesmo
módulo (R1); trechos em vez de arestas cruas, porque é o que a página desenha (R2); None em vez
de erro, porque não haver trajeto é normal numa rede com falhas (R3).

Limitações: o tempo é o esperado para quem chega à parada num instante qualquer da faixa (espera
H/2), não o de um horário de saída exato; caminhada em linha reta. Com a espera fixa de 300 s
de antes da F-ESPERA, baldear saía barato (31 de 200 trajetos com 3 ou mais baldeações em 05/11);
com H/2 de cada linha, caíram para 16 de 200.

### 5.2 Espera e simulação por faixa (F-ESPERA)

A F-ESPERA usa o primeiro horário de cada viagem expandida em `Rede.viagens[padrão]`, como a D10 de P0-MODELO. Para cada padrão, ordena e deduplica partidas; em cada faixa `[início, fim)`, estima a média das diferenças consecutivas como `(última - primeira)/(n - 1)`. Não reúne sentidos ou variantes diferentes da mesma linha, nem conta de novo as frequências ou visitas de uma circular à mesma parada.

Com duas ou mais partidas distintas, publica H e calcula H/2. Com uma partida, omite a chave e o construtor usa `Parametros.espera_padrao_s` (300 s por padrão); a página identifica o valor como provisório. Sem partida, o construtor não cria embarque. A tabela `esperas[(padrão, faixa)]` já contém segundos de espera: G_E não deve dividir de novo por dois.

`simular_trajeto` escolhe a faixa pela saída, constrói G_E com as esperas e reutiliza `trajeto_mais_rapido` e `Trajeto.tempo_por_tipo()`. Cada troca paga outra espera; continuar no mesmo ônibus não. Horário fora das faixas gera ValueError, parada inexistente KeyError, e destino inalcançável retorna None. Horários acima de 24h não são normalizados: exigem uma faixa explícita que os contenha. A página padrão usa as quatro faixas de 06h a 24h.

Para N viagens, P padrões e F faixas: deduplicação e ordenação custam O(N log N), filtragem por faixa O(FN + PF); espaço O(N + PF). Simular acrescenta a construção de G_E e o Dijkstra O((V + E) log V), com espaço O(N + PF + V + E). A tabela da página custa O(PF + FN). O mapa recebe apenas as paradas do trajeto, sem alterar a rede original.

Limitações: espera H/2 supõe chegada ao acaso e intervalos regulares. Com intervalos irregulares, E[H²]/(2 E[H]) pode ser maior; a versão essencial não aplica essa correção. A faixa da saída vale para o percurso inteiro, inclusive após cruzar outra faixa. Não há consulta à próxima partida exata nem Monte Carlo. A regra D10 pode omitir serviço em parada intermediária quando a viagem começou em outra faixa. As limitações de linhas circulares e da caminhada em linha reta de G_E permanecem.

### 5.3 Menos baldeações (F-BALD)

Dadas duas paradas, `menos_baldeacoes` acha o trajeto com o menor número de ônibus
(baldeações = ônibus − 1) e diz em que linhas ir e onde trocar. Não é o mais rápido; quanto
tempo custa a mais é a F-BALD-2.

```python
from transporte.modelo.linhas import construir_gl
from transporte.algoritmos.baldeacoes import menos_baldeacoes

gl = construir_gl(rede, faixa="pico_manha")   # ou faixa=None: todas as linhas do dia
t = menos_baldeacoes(gl, "A", "D")            # None se não houver trajeto
t.baldeacoes, t.padroes(), t.trocas(), t.trechos
```

**A visão G_L.** Um vértice por padrão de linha e uma aresta P → Q quando dá para descer de P
e embarcar em Q na mesma parada ou a até 300 m. Cada camada de uma busca em largura é um ônibus
a mais. A aresta é dirigida (não se desce na primeira parada nem se embarca na última) e guarda
**onde** a troca acontece: a posição de descida em P e a de embarque em Q, só das trocas não
dominadas (ninguém desce mais tarde e embarca mais cedo ao mesmo tempo). Também há laço P → P:
descer, andar e pegar o mesmo padrão mais atrás é uma baldeação.

**Por que não um BFS comum.** Os padrões têm sentido. Com P1 = S → B → A → E, P2 = B → D e
P3 = E → B, existe a aresta P1 → P2 (troca em B), e um BFS comum diria 1 baldeação de A a D.
Mas quem embarca em P1 em A já passou de B: o certo é P1 até E, P3 de volta a B e P2 até D,
2 baldeações. No feed real, o BFS comum erraria para menos em 14 de 200 pares.

Passo a passo (`docs/diagramas/atividade-menos-baldeacoes.png`):

1. Destino a até 300 m da origem: a pé, 0 baldeações.
2. Camada 1: cada padrão que embarca a até 300 m da origem recebe como rótulo a posição de
   embarque mais cedo.
3. Se um padrão que melhorou nesta camada desce a até 300 m do destino depois do embarque, pronto:
   baldeações = camada − 1.
4. Próxima camada: das arestas dos padrões que melhoraram, a troca que desce depois do embarque e
   embarca mais cedo no vizinho. Um padrão pode voltar numa camada posterior, embarcado mais cedo,
   o que abre trocas que antes não serviam.
5. Nenhum padrão melhorou: não há trajeto (None).

**Complexidade.** O(r (V + E + T)) por consulta, com V e E da G_L, T trocas guardadas e
r camadas (baldeações + 1), porque cada camada só percorre os padrões que melhoraram na anterior.
No feed real (11/11, `feature-F-BALD.md`), a G_L do pico da manhã tem V = 501 e E = 85.606, é
montada em 3,1 s, e a consulta leva 36,7 ms em média (máximo 172,9 ms em 200 pares), com
0 divergências contra o NetworkX num grafo de estados independente.

Por quê: G_L dirigida com as trocas na aresta, e não BFS comum (limite inferior) nem BFS 0-1 no
G_E (não constrói a G_L e roda num grafo de 46.100 vértices) (B1); laço P → P (B2); caminhada de
até 300 m, uma por vez (B3); G_L do dia ou de uma faixa, com a regra D10 (B4).

Limitações: conta trocas, não tempo; a G_L não vê horários, a não ser no filtro por faixa;
caminhada em linha reta, uma por vez, só entre paradas; falha de parada exige reconstruir a G_L.

### 5.6 Falhas e resiliência (F-RES)

A F-RES responde o que acontece quando uma parada fecha, um trecho é interditado ou uma linha para: quem fica sem acesso e quanto a rede perde em rapidez. Usa G_P, onde "parada" e "trecho" já são vértice e aresta.

```python
from transporte.modelo.construtores import construir_gp
from transporte.simulacao.falhas import Falha, indexar_linhas, simular_falha

gp = construir_gp(rede)
indice = indexar_linhas(rede)  # uma vez por rede
r = simular_falha(gp, Falha(linhas=("562003",)), indice, amostra=100, semente=2026)
r.paradas_isoladas, r.perda_eficiencia
```

**A falha não reconstrói o grafo.** O núcleo desativa vértices e arestas sem apagar nada. Parada: desativa o vértice, e com ele saem todas as arestas que o tocam. Trecho (a, b): desativa a aresta de viagem a -> b, só nesse sentido; a caminhada continua. Linha: G_P junta numa aresta só o trecho que várias linhas usam, então só saem os trechos que nenhuma outra linha usa. `indexar_linhas` monta o mapa trecho -> linhas a partir dos padrões. A simulação valida tudo antes de desligar qualquer coisa e, no fim, religa só o que ela desligou, inclusive se der erro; o mesmo G_P serve para a próxima consulta.

**Componentes fortemente conexas (Tarjan).** Duas paradas estão na mesma componente se dá para ir de uma à outra e voltar. A DFS guarda, para cada vértice, a ordem de descoberta (`indice`) e o menor índice que a subárvore alcança voltando por uma aresta (`low`). Quando `low[v] == indice[v]`, v é a raiz de uma componente, e tudo acima dele na pilha é a componente. Exemplo: 0 -> 1 -> 2 -> 0 e 2 -> 3. A DFS desce 0, 1, 2, 3; o 3 não tem saída e {3} sai sozinho; em 2, a aresta 2 -> 0 dá `low[2] = 0`, que sobe até o 0 e fecha {0, 1, 2}. A versão é iterativa porque, no G_P real, a DFS chega a 4.657 níveis e o Python para em 1.000 de recursão. O(V + E).

**Isoladas, desconectadas e perda.** Isolada é a parada que ficou sozinha na componente depois da falha e não estava antes. Desconectada é a que saiu da maior componente (empate: a primeira na ordem do Tarjan). Eficiência global = média de 1/d sobre os pares ordenados, com par sem caminho somando 0; perda = (antes - depois) / antes. O denominador é o n de antes da falha: com o n de depois, remover uma parada mal conectada poderia aumentar a eficiência. Com amostra, as mesmas s origens sorteadas valem antes e depois. O(s (V + E) log V), um Dijkstra por origem.

**No feed real** (10/11, `benchmarks/medir_falhas.py`): G_P com V = 9.659 e E = 122.732 tem 4 componentes, uma com 9.656 paradas e 3 unitárias, iguais às do NetworkX; o Tarjan leva cerca de 150 ms. Tirar a parada com mais saídas ou a linha com mais trechos exclusivos não isola ninguém e custa menos de 0,1 % de eficiência; cada simulação com 100 origens leva de 18 a 26 s.

Limitações: G_P usa o tempo mediano, sem espera nem horário, então a perda é estrutural, não o tempo porta a porta. A hipótese para as perdas pequenas é que a caminhada de 300 m contorna as falhas, mas isso não foi medido. A `eficiencia_global` daqui é provisória até a da F-EFI entrar, que tem a mesma assinatura.

### 5.7 Desejáveis e opcionais

#### 5.7.1 A\* e ponto no mapa (F-ROTA-2)

Escolher origem e destino em qualquer ponto do mapa (RF-ROT-03) e calcular o trajeto com A\*,
comparando com o Dijkstra em vértices expandidos e tempo (RF-ROT-04). Mesma visão G_E da F-ROTA:
a comparação só é justa no mesmo grafo e com o mesmo custo.

```python
from transporte.algoritmos.a_estrela import (
    comparar, coordenadas_ge, parada_mais_proxima, velocidade_maxima)

coords = coordenadas_ge(ge, rede.paradas)      # O(V), uma vez por G_E
vmax = velocidade_maxima(ge, coords)           # O(E), uma vez por G_E
parada, metros = parada_mais_proxima(rede.paradas, -19.9245, -43.9352)
c = comparar(ge, coords, vmax, origem, destino)
c.dijkstra.expandidos, c.a_estrela.expandidos, c.a_estrela.trajeto
```

**Ponto no mapa.** `parada_mais_proxima` percorre as paradas e devolve a de menor distância
haversine (empate pelo menor id), em O(V): 4,90 ms por ponto no feed real. A caminhada até ela,
em linha reta a 1,2 m/s, entra só no "Tempo porta a porta". Uma k-d tree seria mais rápida, mas é
uma consulta por clique.

**A\*.** O Dijkstra fecha vértices em ordem de g(v), o custo já percorrido; o A\* em ordem de
f(v) = g(v) + h(v), em que h(v) estima o que falta. Aqui h(v) = distância em linha reta até o
destino / vmax, e vmax é a maior distância / peso entre as arestas de viagem e caminhada. A
plataforma usa as coordenadas da sua parada. Com h = 0 a mesma função é o Dijkstra
(`dijkstra_contado`). Exemplo hipotético: destino 10 km ao norte, vmax = 10 m/s; N, 1 km ao norte,
com g = 200 s, tem f = 1.100 s; S, 1 km ao sul, com g = 150 s, tem f = 1.250 s. O Dijkstra expande
S antes, o A\* expande N.

**Por que dá o ótimo.** A h é consistente: h(u) ≤ w + h(v) em toda aresta, porque
d(u, t) ≤ d(u, v) + d(v, t) e d(u, v) / w ≤ vmax. Logo nunca superestima o custo restante.
O((V + E) log V) no pior caso, como o Dijkstra; o A\* só reduz quantos vértices expande.

**No feed real** (18/11, `benchmarks/medir_rota_extensoes.py`, 200 pares): o A\* expandiu 99,7%
dos vértices do Dijkstra (mediana) e levou 90,8 ms contra 72,3 ms, com o mesmo custo nos 200.
Duas causas: 181 trechos com o mesmo horário no GTFS ficam no piso de 1 s (M2), e um deles cobre
1.258 m, então vmax = 1.258 m/s e a h fica minúscula; e a h não enxerga as esperas. Por isso o A\*
paga uma haversine por vértice sem podar quase nada.

Por quê: vmax calculado do próprio grafo, para ser admissível em qualquer feed; A\* admissível
mantido mesmo com ganho baixo (seção 8, 18/11), porque uma velocidade realista tiraria a garantia
de ótimo da comparação.

Limitações: ganho quase nulo no feed de BH; o ponto é ligado só à parada mais próxima, em linha reta.

#### 5.7.2 Trajetos alternativos (F-ROTA-OPC)

Listar os k trajetos de menor tempo, do mais rápido ao mais lento (RF-ROT-05).

```python
from transporte.algoritmos.alternativos import trajetos_alternativos

ts = trajetos_alternativos(ge, origem, destino, 3, coords, vmax)   # lista de Trajeto
```

**Yen.** O primeiro é o trajeto mais rápido. Para o i-ésimo, cada vértice do (i-1)-ésimo vira,
um por vez, ponto de desvio: mantém a raiz (da origem até ele), desativa as arestas que os
caminhos aceitos usam logo depois da mesma raiz e os vértices da raiz menos o desvio (sem
ciclo), roda um A\* do desvio ao destino e reativa tudo. Os candidatos ficam num `HeapMin`, e o
menor vira o próximo caminho. Exemplo (o do teste): de A a C há a troca em B (800 s) e a linha
lenta (2.300 s); com k = 5 a função devolve só esses dois.

O(k · n · (V + E) log V), n = vértices do maior caminho aceito: uma busca por desvio. No feed real
(18/11, 20 pares): mediana de 2,3 s com k = 3 e 4,6 s com k = 5, até 25,4 s; por isso a página só
calcula no botão.

Por quê: desativar pela API de falhas do núcleo em vez de copiar o grafo (O(V + E) por desvio);
reativar só o que a função desativou, num `finally`, para não desfazer uma falha da F-RES; A\* nos
desvios, porque remover arestas não aumenta a velocidade de nenhuma restante e a h continua
consistente.

Limitações: alternativos diferem em pelo menos uma aresta de G_E e podem ser variações pequenas do
mesmo trajeto; falta um filtro de diferença mínima.

## 6. Interface (Arthur)

A aplicação Streamlit fica em `src/transporte/interface/app.py`. A navegação tem uma página
inicial e entradas para cada feature; quando o módulo de uma página existe, a aplicação chama
seu contrato `render(rede)`. Enquanto uma página ainda não foi criada, ela aparece como
indisponível sem impedir a navegação.

O mapa reutilizável de `src/transporte/interface/mapa.py` recebe a `Rede` normalizada: mostra
paradas agrupadas, padrões como linhas, caminhos como polilinhas e intensidades como mapa de
calor. Cada visualização fica em uma camada Folium que pode ser ligada ou desligada. As páginas
podem chamar `render_mapa` com apenas as camadas de que precisam. Para um resultado de F-ROTA,
`trajeto` permite desenhar cada trecho a pé, de espera ou de ônibus com rótulo e cor; marcadores
identificam origem, destino e baldeações a partir dos trechos de ônibus no resultado.

A página inicial procura arquivos GTFS `.zip` e diretórios com `stops.txt` em
`dados/rede-teste/` e `dados/brutos/`. O botão de carga chama `transporte.dados.leitor_gtfs.ler`,
que aceita uma pasta ou ZIP e devolve a `Rede` normalizada de P0-DADOS. A interface apresenta o
dia de serviço, quantidades de paradas/linhas/padrões, totais V/E de G_P e G_E (na faixa
`pico_manha`) e inconsistências do leitor. O objeto carregado fica em `st.cache_resource`,
indexado pela origem e pelos metadados dos arquivos; cada sessão recebe uma cópia profunda para
que simulações mutáveis não alterem a rede de outras sessões. Um erro de carga é mostrado sem
substituir a rede anterior.

## 7. Como testamos e medimos (Rafael)
Gabarito à mão, comparação de resultado com NetworkX, medição de tempo.

### Medição de tempo (P0-AVAL)

Todo tempo do projeto sai de uma função só, `medir`, em `src/transporte/util/medicao.py`. Se
cada um medisse do seu jeito, com uma execução, com `time.time()` ou contando a leitura do GTFS,
a tabela de desempenho do relatório misturaria números incomparáveis.

```python
from transporte.util.medicao import medir

m = medir(sorted, list(range(100_000, 0, -1)), repeticoes=10)
m.formatar()   # "855.140 µs ± 60.252 µs (n=10)", medido em 03/11 (feature-P0-AVAL.md)
m.media_s      # em segundos, para a tabela da F-AVAL
```

Numa feature, passe o algoritmo e o grafo já construído, por exemplo
`medir(dijkstra, visao.grafo, origem)`.

Como funciona:

1. Valida `repeticoes` (inteiro ≥ 1) **antes** de rodar o algoritmo.
2. Executa `func(*args, **kwargs)` N vezes. Cada execução é cronometrada sozinha com
   `time.perf_counter`, e só a chamada fica entre as duas leituras do relógio.
3. Devolve uma `Medicao` imutável com a média e o desvio padrão amostral (divisor N − 1; com
   N = 1, o desvio é 0).

Exemplo: execuções de 1 s, 2 s e 3 s dão média 2 s e desvio raiz((1 + 0 + 1) / 2) = 1 s.
Complexidade O(N · T) de tempo, em que T é uma execução de `func`, e O(N) de espaço.

Por quê:

- **`perf_counter`:** é monotônico e o de maior resolução (100 ns na máquina do Rafael).
  `time.time()` segue o relógio do sistema, que pode ser acertado no meio da medição.
- **N − 1:** as N execuções são uma amostra, e N − 1 corrige o viés do desvio.
- **N = 5 por padrão:** dá a dispersão com custo baixo; para algo de microssegundos, suba N.
- **Sem aquecimento nem descarte de outliers:** mantém o número honesto e o contrato simples.

Regras de uso:

- Meça só o algoritmo. Construa o grafo antes e passe-o como argumento.
- Registre no arquivo da feature a média, o desvio, N, |V|, |E|, a máquina e o comando.
- Se `func` altera os próprios argumentos, copie-os antes, porque as N execuções recebem os
  mesmos objetos.

Limitações: mede tempo de parede, que depende da máquina e do que mais estiver rodando; não mede
memória. O custo fixo de uma medição é de cerca de 0,08 µs, desprezível para algoritmos de grafo.
Os testes trocam `medicao._relogio` por um relógio falso de leituras conhecidas, o que permite
um gabarito exato para média e desvio sem depender da velocidade da máquina.

## 8. Registro de decisões

Lugar canônico de toda decisão do grupo. Nova decisão: uma linha aqui e a mudança na fonte, no mesmo commit.
As referências "seção N" apontam para `docs/fontes/plano-de-projeto.md` ou para os documentos indicados nele.

| Data | Decisão | Por quê | Alternativa descartada |
|---|---|---|---|
| 29/10 | Método enxuto, sem plantão, ata, reunião semanal nem controle de mudança formal | Trabalho de 1 mês; o custo desses rituais só se paga em projetos longos | Manter o método do TI5 inteiro |
| 29/10 | Sem CI/CD e sem releases | Não há deploy nem versão publicada; a regra crítica fica no hook e na revisão | GitHub Actions com checks obrigatórios |
| 29/10 | Hook de pre-commit com verificação de imports e ruff | A regra que zera a nota não pode depender só de atenção | Só revisão humana |
| 29/10 | PR com 1 aprovação de outro integrante | Evita `main` quebrada e obriga uma segunda pessoa a entender cada código | Commit direto na `main` |
| 29/10 | Python 3.12 e Streamlit | Uma linguagem para todos, interface sem frontend separado | Java ou C++ com frontend à parte |
| 29/10 | Heap binário próprio, sem `heapq` | Elimina a dúvida sobre "estrutura pronta" no centro do Dijkstra, com custo baixo | Usar `heapq` |
| 29/10 | pandas só para ler CSV | Não cria nem processa grafo | Leitura manual dos CSV |
| 29/10 | GTFS da BHTrans | Rede real, com horários, conhecida pela banca | Dataset de metrô do Kaggle, muitas vezes sem horários |
| 29/10 | R = 300 m, 1,2 m/s, 4 faixas, sem penalidade por baldeação | Ver seção 3.4 | Valores ajustados depois, sem registro |
| 29/10 | NetworkX permitido em `tests/` para comparar resultados e em `benchmarks/` | Comparar resultado não é a ferramenta usando a biblioteca; o grupo assume essa interpretação do enunciado | Só gabarito à mão |
| 29/10 | Desempenho obrigatório: complexidade teórica e tempo medido; benchmark contra NetworkX opcional, só depois de tudo pronto | O enunciado pede complexidade e avaliação de desempenho; a comparação completa não cabe no prazo antes das features | Benchmark como item do DoD |
| 29/10 | Etapa 1 como seções do relatório e no README | Tudo é entregue junto; evita escrever o mesmo texto duas vezes | Documento separado |
| 29/10 | Vídeo por link no Canvas | Sem limite de tamanho de arquivo | Arquivo de vídeo no `.zip` |
| 29/10 | Repositório público | Decisão do grupo; o risco está na seção 15 | Privado até a entrega |
| 29/10 | Relatório editado no repositório | Commits individuais no relatório contam | Só Overleaf |
| 29/10 | `docs/GUIA.md` global e "Como funciona e por quê" e perguntas de verificação em cada feature | Todos precisam dominar o trabalho inteiro, inclusive o que foi feito com IA | Só documentação por feature |
| 29/10 | Congelamento em 15/11 | A semana de 16/11 é do TI5 | Congelar em 18/11 |
| 29/10 | Nomes: Thiago, Miguel, Henrique, Arthur, Caio e Rafael nas frentes A a F | Ver seção 6.2 | |
| 29/10 | Henrique fica com a frente C (modelagem e trajeto mais rápido), o caminho crítico | Pedido dele; a frente alimenta 5 das 6 features essenciais e concentra o que é avaliado na Etapa 1 | Henrique em dados e espera |
| 29/10 | `REQUISITOS.md` em baseline (v1.0) sem revisão separada | Os RFs são cópia exata do plano que o grupo já aprovou; revisar de novo seria repetir o ok. Discordância posterior vira pendência e decisão | Revisão por todos até 02/11 e baseline em 03/11 |
| 29/10 | Apresentações a partir de 24/11 | Informado pelo professor; a ordem ainda não foi divulgada | Hipótese anterior: a partir de 23/11 |
| 29/10 | Padrão = linha + sequência exata de paradas (D1) | O G_E encadeia plataformas numa sequência fixa; variantes de itinerário quebrariam o encadeamento | Linha + sentido (`direction_id`) |
| 29/10 | Tempo entre paradas consecutivas = mediana das viagens do padrão no dia típico (D2) | Robusta a horários com erro de cadastro; variação ao longo do dia vira limitação | Média; mediana por faixa horária |
| 29/10 | Paradas com um `stop_id` por sentido ficam separadas, ligadas por caminhada (D3) | Fiel ao GTFS; o raio de 300 m já liga as duas; fundir alteraria os dados e esconderia a travessia | Fundir por `parent_station` ou proximidade |
| 29/10 | Dia típico = uma quarta-feira fixa dentro da vigência do feed, com `calendar.txt` e `calendar_dates.txt` (D4) | Trata as exceções de calendário e é reprodutível | Dia útil genérico (segunda a sexta = 1) |
| 29/10 | Faixas: 06h a 09h, 09h a 16h, 16h a 19h, 19h a 24h; madrugada fora (D5) | Na madrugada há poucas partidas e intervalos longos que distorceriam as médias | Incluir a madrugada como quinta faixa |
| 29/10 | Espera provisória de 300 s em todo embarque até a tabela de intervalos de F-ESPERA (D6) | Evita duplicar em P0-MODELO o cálculo que é de F-ESPERA; vale até 06/11 | Estimar H/2 dentro do construtor |
| 29/10 | Visões salvas com pickle em `dados/cache/`, fora do Git (D7) | Simples e rápido; o arquivo é cache gerado pela própria ferramenta e nunca vem de fonte externa | JSON |
| 29/10 | Uma classe por visão herdando de `Visao`; `construir_ge` recebe a faixa e a tabela de intervalos; salvar e carregar ficam nos construtores | Cada visão tem mapas próprios (paradas, plataformas, padrões); o G_E depende da faixa porque a espera muda ao longo do dia | Uma classe única com mapas opcionais |
| 29/10 | Arquivo de feature com seção Retomada, reescrita ao fim de toda sessão | Qualquer agente novo precisa saber onde parou e o próximo passo sem reler o código | Só status por camada |
| 29/10 | Todos os arquivos de feature e as issues criados na abertura do repositório | Cada integrante clona, pergunta ao agente o que fazer e começa no mesmo dia | Cada dono cria os seus quando começar |
| 03/11 | `medir` usa `time.perf_counter` e devolve média e desvio amostral (N − 1), sem aquecimento nem descarte de outliers (P0-AVAL) | Relógio monotônico de maior resolução; as N execuções são amostra; número honesto e contrato simples | `time.time`, desvio populacional, descartar a primeira execução |
| 03/11 | `Medicao.formatar()` acrescentado ao contrato de medição, escolhendo µs, ms ou s pela média (P0-AVAL) | Mesmo formato de tempo em todas as features, na interface e na tabela do relatório | Cada feature formata o seu |
| 03/11 | Relatório com uma seção por arquivo, seções de feature incluídas sozinhas por `\InputIfFileExists` e `\pendente` para o que falta (P0-AVAL) | Cada dono edita só o seu arquivo, sem conflito de merge e sem mexer no `main.tex`; o que falta fica visível no PDF | Um `main.tex` único editado por todos |
| 03/11 | Relatório compilado com `latexmk` para `relatorio/build/`, fora do Git; PDF versionado só na entrega (P0-AVAL) | Arquivos gerados não poluem o histórico nem causam conflito | Versionar o PDF a cada mudança |
| 05/11 | Piso de 1 s nas arestas de viagem e de caminhada de G_P e G_E (`Parametros.peso_minimo_s`); desembarque continua com 0 (P0-MODELO, a pedido da F-MET, decisão M2) | O GTFS arredonda horários e paradas no mesmo ponto ficam a 0 m; com peso 0 o Brandes deixa de contar certo os caminhos mínimos, e 0 s entre paradas distintas não é tempo real | Desempatar pelo número de arestas no Brandes; somar ε só dentro do Brandes |
| 05/11 | Diferença de horário negativa fica fora da mediana; trecho sem diferença válida recebe o piso (D8) | É erro de cadastro isolado; o trecho existe na sequência do padrão | Levantar erro; descartar a viagem inteira |
| 05/11 | Sem embarque na última parada do padrão e sem desembarque na primeira (D9) | Essas arestas nunca estão num caminho útil e só aumentam o G_E | Criar as quatro arestas em toda plataforma |
| 05/11 | Padrão com partida na faixa = alguma viagem com o primeiro horário na faixa (D10) | É a definição de partida e casa com a tabela de intervalos de F-ESPERA, por (padrão, faixa); ônibus que sai às 08h55 não dá embarque às 09h20 no entrepico (limitação) | Alguma viagem passar pela parada dentro da faixa |
| 05/11 | Linha circular usa uma plataforma por (parada, padrão) (D11) | É o que a chave do contrato `plataforma[(parada, padrão)]` implica; o passageiro pode dar a volta e seguir no início do padrão (limitação) | Uma plataforma por ocorrência da parada no padrão |
| 05/11 | RNF-05: a consulta de trajeto responde em até 1 s na rede completa (R4 da F-ROTA) | Na primeira medição (feed real, G_E com 46.100 vértices), a média foi 75,8 ms e o pior caso de 200 consultas 162,2 ms: margem de cerca de 6 vezes para máquina mais lenta e para a página. A construção do G_E fica fora, porque é feita uma vez por faixa | X = 0,5 s, com margem de 3 vezes |
| 05/11 | `construir_ge` recebe `esperas[(padrão, faixa)]`, a espera de embarque já calculada pela F-ESPERA, e a aplica sem transformação; substitui `intervalos`, de que o construtor tirava H/2 (P0-MODELO) | Calcular a espera é do RF-ESP-02. A versão essencial usa H/2, e a comparação com E[H²]/(2 E[H]), a espera com intervalos irregulares, é resultado a discutir (`modelagem.md`, espera esperada); dividindo H por 2 no construtor, essa comparação exigiria passar E[H²]/E[H] num campo chamado "intervalo". Mudado antes do merge do #38 e antes de a F-ESPERA começar, sem retrabalho | Manter `intervalos` com H/2 no construtor; receber H e a variância |
| 06/11 | Henrique integra o relatório final (itens 5 e 6 da seção 2.1) e monta o vídeo (item 9) | Pedido do Henrique; issues #28 e #30 reatribuídas a ele. Rafael segue com a avaliação de desempenho e o fechamento do vídeo; cada dono continua escrevendo a sua seção e gravando o seu trecho | Rafael integra o relatório; Caio monta o vídeo |
| 05/11 (rascunho para Miguel revisar) | Leitor escolhe a quarta-feira ativa mais próxima da versão do feed, quando essa data existe | Mantém a análise reproduzível e próxima do instantâneo baixado | Usar sempre a primeira quarta-feira da vigência, que pode ser antiga |
| 05/11 (rascunho para Miguel revisar) | `stop_times.txt` é lido em fluxo e só horários de serviços ativos são guardados | Evita carregar o CSV inteiro do feed real em memória | Materializar todos os horários antes de filtrar |
| 05/11 (rascunho para Miguel revisar) | Recorte separa trechos desconectados e reúne os que têm a mesma linha e sequência de paradas | Não inventa viagem direta entre paradas quando a intermediária sai do recorte nem divide as partidas de uma plataforma equivalente | Concatenar todas as paradas restantes; manter padrões duplicados após o recorte |
| 11/11 | G_L dirigida, com as trocas não dominadas (posição de descida, posição de embarque) em cada aresta; mínimo de baldeações por BFS por camadas com a posição de embarque no rótulo (B1, F-BALD) | Os padrões têm sentido: o BFS comum usa trocas que ficaram para trás e dá só um limite inferior (menos baldeações que o possível em 14 de 200 pares no feed real) | BFS comum na G_L; BFS 0-1 no G_E (exato, mas não constrói a G_L e roda num grafo de 46.100 vértices, com caminhadas encadeadas) |
| 11/11 | Laço P → P na G_L (B2, F-BALD) | Descer, andar e pegar o mesmo padrão mais atrás é outro embarque; sem o laço, o NetworkX achou trajetos com um ônibus a menos | Proibir troca para o mesmo padrão |
| 11/11 | Caminhada de até 300 m, uma por vez, entre paradas, na F-BALD; destino a até 300 m da origem vai a pé (B3) | É a ligação que a modelagem define para a G_L; encadear caminhadas tornaria a distância a pé ilimitada | Caminhadas encadeadas, como no G_E |
| 11/11 | G_L do dia por padrão ou de uma faixa, só com os padrões com partida nela, pela regra D10 (B4, F-BALD) | A F-BALD-2 compara com o G_E da mesma faixa sem usar linha que não circula nela | Só a G_L do dia; só por faixa |
| 17/11 | Perda de eficiência da F-RES com o denominador de antes da falha: as mesmas origens e o mesmo n antes e depois (R1) | Com o n de depois, remover uma parada mal conectada aumentaria a eficiência, porque os pares ruins dela sairiam da média; com o mesmo n, os pares da parada removida contam 0 e a perda nunca é negativa | Renormalizar pelo n de depois da falha |
| 17/11 | Parada isolada = ficou sozinha na componente fortemente conexa depois da falha e não estava antes; desconectada = saiu da maior componente (R2, F-RES) | "Saiu da maior" fica ambíguo quando duas componentes empatam de tamanho; a isolada não depende de desempate. A desconectada continua útil para quem caiu num grupo pequeno | Um único critério, "fora da maior componente" |
| 17/11 | Falha de trecho remove só a aresta de viagem a -> b, num sentido, e mantém a caminhada (R3, F-RES) | Interdição costuma ser de uma mão, e a volta é outro trecho de G_P; a caminhada entre as paradas continua possível | Remover os dois sentidos e a caminhada |
| 18/11 | A\* da F-ROTA-2 com h = distância em linha reta / vmax, vmax = maior velocidade entre as arestas de G_E, mesmo com ganho quase nulo no feed real (99,7% dos vértices expandidos) | A RF-ROT-04 compara A\* e Dijkstra, e a comparação só vale se os dois devolvem o ótimo; o ganho baixo vem do piso de 1 s em 181 trechos com horário repetido no GTFS e das esperas, que a h não enxerga, e é relatado como resultado | vmax realista (perde a garantia de ótimo); somar a espera mínima à h; interpolar os horários repetidos no P0-MODELO (muda M2 e os números das outras features depois do congelamento; fica como trabalho futuro); ALT |

## 9. Glossário
Parada, padrão, plataforma, embarque, baldeação, intervalo, isócrona, intermediação, ...

## 10. Perguntas de verificação
Todas as perguntas das features, com resposta, agrupadas por seção.

### 2. Dados e GTFS (P0-DADOS)
1. **Por que guardar os horários por viagem?** Para ligar passagens consecutivas do
   mesmo ônibus e calcular seu tempo entre paradas.
2. **O que significa `24:10:00`?** Dez minutos após a meia-noite seguinte, ainda na
   mesma jornada GTFS.
3. **Por que dividir um padrão durante o recorte?** Para não criar uma ligação direta
   entre paradas cujo trecho intermediário foi removido.

### 3. Construtores de G_P e G_E (P0-MODELO)
1. **Por que G_E tem vértices de plataforma?** Para que trocar de linha custe alguma coisa:
   trocar obriga a desembarcar, voltar à parada e pagar um novo embarque, com a espera da nova
   linha. Em G_P a aresta não sabe em que linha o passageiro está.
2. **Como se conta o número de baldeações de um trajeto em G_E?** Embarques no caminho menos
   um; um trajeto só a pé tem 0.
3. **Por que o tempo entre paradas é a mediana, e o que acontece com uma diferença negativa?**
   A mediana resiste a horários errados. A diferença negativa fica fora; se não sobrar nenhuma,
   o trecho recebe o piso de 1 s, porque existe na sequência do padrão (D8).
4. **Por que montar a caminhada não custa O(V²)?** A grade espacial só compara cada parada com
   as 9 células vizinhas: O(V + K) esperado.
5. **Por que viagem e caminhada têm piso de 1 s, mas o desembarque fica com 0?** Peso 0 entre
   paradas distintas é artefato do arredondamento e quebra a contagem de caminhos do Brandes;
   desembarcar não leva tempo e só liga a plataforma à própria parada.

### 5.1 Trajeto mais rápido (F-ROTA)
1. **Por que um único Dijkstra basta para somar caminhada, espera, viagem e baldeação?** Porque
   em G_E trocar de linha passa por uma aresta de embarque, que pesa a espera da nova linha.
2. **Por que o caminho é reconstruído por arestas e não por vértices?** O tipo do passo
   (caminhada, embarque, viagem, desembarque) está na aresta; dele saem os trechos e as baldeações.
3. **Por que dá para parar o Dijkstra quando o destino sai do heap?** Com pesos não negativos, a
   distância de um vértice fechado é definitiva.
4. **O tempo total é o horário de chegada de quem sai agora?** Não: é o tempo esperado para quem
   chega à parada num instante qualquer da faixa (espera H/2 em cada embarque).
5. **O que acontece se não houver trajeto?** A função devolve None, e a página mostra "sem
   trajeto"; é normal com paradas ou linhas desativadas (F-RES).

### 5.2 Espera (F-ESPERA)
1. **Por que usar o primeiro horário da viagem?** Para respeitar a mesma regra D10 que decide se há embarque em G_E; visitas repetidas de uma circular não são novas saídas.
2. **Por que o construtor recebe espera e não intervalo?** Porque H/2 é calculado por F-ESPERA e deve ser aplicado apenas uma vez.
3. **Uma partida permite estimar H?** Não. Usa-se a espera provisória identificada na tela; sem partida não há embarque.
4. **A saída às 08h59 usa a faixa seguinte durante a viagem?** Não: a versão essencial mantém a faixa da saída fixa; partidas exatas são da extensão G_T.
5. **H/2 vale para intervalos muito irregulares?** É a aproximação essencial; a espera com chegadas ao acaso seria E[H²]/(2 E[H]).

### 5.3 Menos baldeações (F-BALD)
1. **Por que a G_L tem um vértice por padrão, e não por parada?** Porque baldeação é troca de
   linha: cada camada da busca em largura é um ônibus a mais, e as paradas percorridas não importam.
2. **Por que um BFS comum sobre a G_L não basta?** Os padrões têm sentido: quem embarca numa
   posição só desce depois dela. O BFS comum usaria trocas que ficaram para trás e dá só um limite
   inferior (errou para menos em 14 de 200 pares no feed real).
3. **O que é uma troca não dominada?** Numa aresta P → Q, uma troca que nenhuma outra supera
   descendo mais tarde em P e embarcando mais cedo em Q ao mesmo tempo. Só essas ficam na aresta.
4. **Por que um padrão pode voltar numa camada posterior?** Porque pode ser alcançado depois numa
   posição mais cedo, e embarcar antes abre trocas que antes não serviam.
5. **O trajeto devolvido é o mais rápido entre os de menos baldeações?** Não. O critério é só o
   número de baldeações; o tempo a mais em relação ao mais rápido é a F-BALD-2.

### 5.6 Falhas e resiliência (F-RES)
1. **Por que o Tarjan é iterativo?** Porque a recursão vai tão fundo quanto o caminho da DFS, e no G_P real esse caminho chega a 4.657 níveis, acima do limite de recursão do Python (1.000).
2. **Remover uma linha remove as paradas dela?** Não. Saem só os trechos de viagem que nenhuma outra linha usa; as paradas continuam, porque outras linhas e a caminhada as atendem.
3. **Qual a diferença entre parada isolada e desconectada?** Isolada ficou sozinha na componente (não vai e volta de nenhuma outra). Desconectada saiu da maior componente, mas pode estar num grupo pequeno com outras.
4. **Por que a eficiência depois da falha usa o n de antes?** Para que remover parada nunca aumente a eficiência: os pares da parada removida contam 0 em vez de sumir da média.
5. **Por que a simulação não estraga o G_P para a próxima consulta?** Ela só desativa, e no fim religa exatamente o que desligou, inclusive se der erro.

### 5.7.1 A\* e ponto no mapa (F-ROTA-2)
1. **Qual a diferença entre o A\* e o Dijkstra?** O Dijkstra escolhe o próximo vértice por g(v);
   o A\* por g(v) + h(v), uma estimativa do que falta. Com h = 0 os dois são iguais.
2. **Por que o A\* devolve o mesmo custo do Dijkstra?** Porque a h é consistente
   (h(u) ≤ w + h(v) em toda aresta), logo nunca superestima o custo restante.
3. **Por que a h usa a velocidade máxima da rede, e não uma típica?** Com uma velocidade menor que
   a de alguma aresta, a h passaria do custo real nela e o A\* poderia devolver um trajeto pior.
4. **Por que o A\* quase não ganhou no feed de BH?** O vmax de 1.258 m/s, de trechos de 1 s no
   GTFS, deixa a h muito pequena, e ela não conta as esperas.
5. **Como um clique no mapa vira origem do trajeto?** `parada_mais_proxima` acha a parada mais
   próxima em O(V); a caminhada até ela entra só no tempo porta a porta.

### 5.7.2 Trajetos alternativos (F-ROTA-OPC)
1. **O que o Yen devolve?** Até k caminhos sem ciclo, em ordem crescente de custo; o primeiro é o
   trajeto mais rápido.
2. **O que é o ponto de desvio?** Um vértice do caminho anterior: mantém-se o trecho até ele e
   procura-se outra continuação, com as saídas já usadas desativadas.
3. **Por que desativar os vértices da raiz?** Para o novo caminho não voltar a eles e formar ciclo.
4. **Por que o Yen é muito mais lento que uma busca?** Faz uma busca por vértice do caminho
   anterior, para cada um dos k caminhos: O(k · n · (V + E) log V).
5. **Como o Yen não estraga uma falha simulada pela F-RES?** Só reativa o que ele mesmo desativou,
   num `finally`.

### 7. Medição de tempo (P0-AVAL)
1. **Por que `perf_counter` e não `time.time()`?** Porque é monotônico e tem a maior resolução;
   `time.time()` segue o relógio do sistema, que pode ser ajustado no meio da medição.
2. **Por que o desvio divide por N − 1?** Porque as N execuções são uma amostra; N − 1 corrige o
   viés do desvio estimado a partir da média da própria amostra.
3. **O que entra no tempo medido?** Só a chamada `func(*args, **kwargs)`; a leitura do GTFS e a
   construção do grafo ficam de fora, a menos que sejam elas a função passada.
4. **Como os testes têm gabarito exato para algo que depende da máquina?** Trocam
   `medicao._relogio` por um relógio falso que devolve leituras conhecidas (1, 2 e 3 s dão
   média 2 e desvio 1).
5. **Como uma feature entra no relatório?** Criando `relatorio/secoes/<ID>.tex` com
   `\subsection{...}`; o `funcionalidades.tex` a inclui sozinho.

### 6. Interface (P0-UI)
1. **Por que a interface não interpreta o GTFS diretamente?** A leitura, validação e
   normalização pertencem a P0-DADOS; a UI consome a `Rede` publicada nesse contrato.
2. **Como uma nova página entra na navegação?** O módulo da feature publica `render(rede)`;
   a aplicação importa esse módulo e passa a mesma rede carregada.
3. **Quais camadas o componente de mapa pode exibir?** Paradas, padrões/linhas, caminhos e
   intensidades de calor, cada uma como camada separada.
4. **Por que a rede carregada fica em cache?** Para não reler e reconstruir os dados a cada
   interação do Streamlit; a chave considera a origem e a versão observável da fonte.
5. **Como a página inicial carrega e resume o GTFS?** Ela chama o `ler` oficial de P0-DADOS
   para uma pasta ou ZIP, mantém a rede anterior em caso de erro e mostra o dia, as
   inconsistências e V/E de G_P e G_E. A medição em um feed real ainda depende de um feed
   disponível no ambiente.
