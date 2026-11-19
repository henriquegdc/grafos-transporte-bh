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

Estrutura, buscas e fila de prioridade são do projeto: nada de biblioteca de grafo em `src/` e
nada de `heapq`. O núcleo não conhece GTFS: trabalha com vértices `0..V-1`, e cada visão guarda
os mapas entre os ids do GTFS e os vértices.

```python
from transporte.grafo.grafo import Grafo
from transporte.grafo.buscas import dijkstra, bfs, caminho, caminho_arestas

g = Grafo()
a, b = g.adicionar_vertice("A"), g.adicionar_vertice("B")
e = g.adicionar_aresta(a, b, 300.0, "viagem")   # peso >= 0, finito
r = dijkstra(g, a)            # r.dist, r.pred, r.pred_aresta
caminho(r, b)                 # [a, b]
g.desativar_vertice(b)        # O(1); vizinhos() deixa de devolver b
g.reativar_vertice(b)
```

**Grafo (`grafo.py`).** Listas paralelas indexadas pelo id: rótulo e flag de ativo dos
vértices; origem, destino, peso, tipo e flag das arestas; e a lista de adjacência `_adj[u]`
com os **ids** das arestas que saem de u. O id deixa peso, tipo e estado num lugar só e
permite arestas paralelas (viagem e caminhada entre o mesmo par). `vizinhos(u)` devolve
`(destino, peso, id)` só das arestas utilizáveis (aresta, origem e destino ativos). Desativar
é marcar um booleano: nada é removido, os ids continuam valendo e a F-RES fecha e reabre
paradas sem reconstruir o grafo. Espaço O(V + E); inserir, desativar e reativar O(1).

**Heap (`heap.py`).** Heap binário de mínimo numa lista (filhos de i em 2i + 1 e 2i + 2).
Inserir sobe a folha nova; extrair põe a última folha na raiz e a desce pelo menor filho. Cada
operação percorre a altura, O(log n). Pares `(prioridade, item)` comparados como tuplas: o
empate sai pelo menor item, o que deixa os caminhos de mesmo custo determinísticos.

**Dijkstra com inserção preguiçosa (`buscas.py`).** Não há "diminuir chave": quando acha um
caminho melhor até v, insere `(nova distância, v)` de novo; a entrada antiga sai depois e é
descartada porque v já está fechado. Passo a passo (`docs/diagramas/sequencia-dijkstra.puml`):
extrai o menor `(d, u)`; se u já está fechado, descarta; senão fecha u (com pesos ≥ 0, d é
definitiva) e relaxa cada vizinho, inserindo de novo quem melhorou. Com `destino`, para quando
ele é fechado. `caminho` e `caminho_arestas` reconstroem pelos predecessores; a F-ROTA usa as
arestas para saber o tipo de cada passo. A BFS é a mesma ideia com fila, contando arestas.

Exemplo: 0→1 (4), 0→2 (1), 2→1 (2), 1→3 (1). Fecha 0 e insere (4, 1) e (1, 2); fecha 2 e acha
0→2→1 = 3, insere (3, 1) sem tirar o (4, 1); fecha 1 e insere (4, 3); o (4, 1) sai e é
descartado; fecha 3 com 4. Caminho: 0, 2, 1, 3.

**Complexidade.** BFS O(V + E). Dijkstra: cada relaxamento bem-sucedido insere uma entrada,
então o heap recebe no máximo E + 1 entradas, cada uma O(log E) ≤ O(2 log V): tempo
O((V + E) log V) e espaço O(V + E). É o limite do Dijkstra com "diminuir chave", sem o mapa
vértice → posição no heap.

Limitações: sem pesos negativos (no projeto todo peso é tempo); vértice e aresta nunca são
removidos, só desativados; com `destino`, só a distância do destino é garantida.

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
real (05/11, `feature-F-ROTA.md`), no G_E com V = 46.100 e E = 208.956: 75,8 ms por consulta em
média e 162,2 ms no pior caso de 200 consultas, com 0 divergências contra o NetworkX.

Por quê: função em `algoritmos/` e não método da visão, para o A\* e o Yen entrarem no mesmo
módulo (R1); trechos em vez de arestas cruas, porque é o que a página desenha (R2); None em vez
de erro, porque não haver trajeto é normal numa rede com falhas (R3).

Limitações: o tempo é o esperado para quem chega à parada num instante qualquer da faixa (espera
H/2), não o de um horário de saída exato; enquanto a F-ESPERA não publica a tabela de esperas,
toda espera é 300 s, e baldear sai barato (31 de 200 trajetos medidos tinham 3 ou mais baldeações);
caminhada em linha reta, só entre paradas.

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

### 5.4 Centralidades (F-MET)

Quais paradas mais importam para a rede: as com mais ligações (grau) e as por onde passam mais
caminhos mínimos entre outras paradas (intermediação, os "gargalos").

```python
from transporte.algoritmos.centralidade import (
    graus, distribuicao_graus, intermediacao, estimar_intermediacao, ranking)

g = construir_gp(rede).grafo
r = graus(g, tipos={"viagem"})                  # r.entrada, r.saida
est = estimar_intermediacao(g, 50, semente=2026, normalizar=True)
ranking(g, est.valores, 10)                     # [(vértice, valor)], decrescente
est.erro_padrao                                 # ± de cada parada
```

**Visão G_P**, porque a pergunta é sobre a parada física; em G_E cada parada vira várias
plataformas e a centralidade se dividiria entre elas.

**Graus.** Cada aresta utilizável soma 1 na saída da origem e 1 na entrada do destino (M1). A
página conta só as de viagem: a caminhada liga todas as paradas vizinhas e inflaria o grau.

**Brandes.** bc(v) = soma, sobre os pares (s, t), da fração dos caminhos mínimos de s a t que
passam por v. Para cada origem s: (1) um Dijkstra que conta σ[v], o número de caminhos mínimos
de s a v, e guarda os predecessores; (2) do mais distante ao mais próximo, acumula
δ[v] = Σ σ[v]/σ[w] · (1 + δ[w]) sobre os sucessores w, e bc[v] += δ[v]. Exemplo: 0→1→2→4 e
0→3→2, pesos 1; de 0 a 2 há dois caminhos (por 1 e por 3), cada um ganha 1/2; bc = [0, 1, 3, 1, 0].
Peso 0 é recusado (M2), porque estraga a contagem σ; o G_P tem piso de 1 s.

**Amostragem (RNF-06, M5).** O exato faz um Dijkstra por parada, dezenas de minutos no feed
real. `estimar_intermediacao` usa k origens sorteadas e multiplica por N/k: a média sobre todas
as amostras possíveis é o valor exato (não viesada). O erro padrão de cada parada é
N · s_v / √k · √((N − k)/N), com s_v o desvio das k dependências; zera quando k = N.

**Página.** Monta G_P uma vez por rede, calcula a métrica escolhida e mostra o ranking (com
± erro padrão quando é amostra), a distribuição de graus e o mapa de calor. No calor, as
intensidades são divididas pelo maior valor (o Leaflet.heat satura acima de 1) e só entram as
10 % de paradas mais centrais, com raio menor: o Leaflet.heat soma a opacidade das vizinhas, e
com as 9.660 paradas o mapa inteiro saturava.

**Complexidade.** Graus O(V + E). Brandes exato O(V (V + E) log V), sem pesos O(V (V + E));
amostrado O(k (V + E) log V). Espaço O(V + E). Ranking O(V log V).

Limitações: G_P não tem espera nem horário (rede estrutural); caminhada em linha reta até
300 m; a estimativa é mais precisa nas paradas mais centrais do que nas de valor pequeno.

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
| 05/11 | Núcleo: `Resultado(origem, dist, pred, pred_aresta)`, acessores `num_vertices`, `aresta(a)`, `vertice_ativo` etc. e reativação individual (G1 a G3, P0-GRAFO) | Os consumidores leem o tipo das arestas do caminho (baldeações) e percorrem os vértices sem tocar em atributos internos; a F-RES-2 religa um candidato por vez em O(1) | Só `dist` e `pred`; só `reativar_tudo`, O(V + E) a cada candidato |
| 05/11 | Peso negativo, infinito ou NaN recusado na inserção; desativar é flag; empate no heap pelo menor item (G4 a G6, P0-GRAFO) | O Dijkstra só é correto com pesos ≥ 0; reativar volta exatamente ao estado anterior; caminhos de mesmo custo determinísticos para os gabaritos | Validar dentro do Dijkstra; remover vértices e arestas |
| 05/11 | Dijkstra com inserção preguiçosa, sem "diminuir chave" (P0-GRAFO) | Mesmo O((V + E) log V) com código menor e sem o mapa vértice → posição no heap; custa espaço O(E) | Heap indexado com diminuir chave |
| 05/11 | Grau conta arestas, com filtro por tipo; caminhos da intermediação como sequência de vértices (paralelas viram a de menor peso, laços ignorados); normalização opcional, ligada na página (M1, M3 e M4, F-MET) | Definições usuais, comparáveis ao NetworkX; viagem e caminhada entre o mesmo par são uma ligação só; o bruto é mais fácil de explicar e o normalizado compara redes de tamanhos diferentes | Vizinhos distintos; contar cada paralela como caminho distinto |
| 16/11 | Intermediação por amostragem de k origens, com estimativa (N/k) · soma e erro padrão por parada com correção de população finita (M5, F-MET, RNF-06) | O exato faz um Dijkstra por parada (cerca de 40 min no G_P real); a amostra de origens é não viesada e informa o erro; mesmo formato de estimativa da F-EFI | Amostrar pares (s, t); exato na página |
| 16/11 | F-MET-2 e F-MET-OPC cortadas pelo congelamento de 15/11; a intermediação amostrada com erro medido contra a exata (RF-MET-05) entrou pela F-MET, por causa do RNF-06 | Regra do calendário: depois de 15/11, só correção; a página essencial (RF-MET-03) ainda faltava | Fazer a proximidade (RF-MET-04) depois do congelamento |
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

### 4. Núcleo do grafo e heap (P0-GRAFO)
1. **Por que o heap pode ter o mesmo vértice várias vezes, e por que isso não quebra o
   Dijkstra?** Em vez de diminuir a chave, inserimos de novo com a distância menor; a entrada
   antiga sai depois e é descartada porque o vértice já está fechado.
2. **Por que inserção preguiçosa continua O((V + E) log V)?** O heap recebe no máximo uma
   entrada por relaxamento bem-sucedido, O(E), e cada operação custa O(log E) ≤ O(2 log V).
3. **Por que a adjacência guarda o id da aresta?** Para ter peso, tipo e estado num lugar só,
   permitir arestas paralelas e devolver o id no caminho (a F-ROTA lê o tipo de cada passo).
4. **Como a F-RES fecha uma parada sem reconstruir o grafo?** Desativa o vértice (um booleano,
   O(1)); `vizinhos` deixa de devolver as arestas que tocam nele.
5. **Por que a distância é definitiva quando o vértice sai do heap?** Com pesos não negativos,
   qualquer outro caminho até ele passa por um vértice ainda no heap, com distância ≥.

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

### 5.4 Centralidades (F-MET)
1. **Por que não contar, para cada par, se o caminho mínimo passa por v?** São V² pares e pode
   haver vários caminhos por par; o Brandes acumula as dependências por origem, com um Dijkstra
   e uma passada de volta, em O(V (V + E) log V).
2. **O que é σ[v]?** O número de caminhos mínimos de s a v; σ[v]/σ[w] é a fração dos caminhos
   até w que passa pelo predecessor v.
3. **Por que o Brandes ponderado recusa peso 0?** Dois vértices ficariam à mesma distância e a
   contagem σ sairia errada; o G_P tem piso de 1 s.
4. **Por que a estimativa com k origens multiplica por N/k, e o que é o "±"?** A soma de k
   origens é, em média, k/N da soma de todas; o "±" é o erro padrão, quanto a estimativa varia
   de uma amostra para outra.
5. **Por que G_P e não G_E?** A pergunta é sobre a parada física; em G_E a parada vira várias
   plataformas.

### 5.6 Falhas e resiliência (F-RES)
1. **Por que o Tarjan é iterativo?** Porque a recursão vai tão fundo quanto o caminho da DFS, e no G_P real esse caminho chega a 4.657 níveis, acima do limite de recursão do Python (1.000).
2. **Remover uma linha remove as paradas dela?** Não. Saem só os trechos de viagem que nenhuma outra linha usa; as paradas continuam, porque outras linhas e a caminhada as atendem.
3. **Qual a diferença entre parada isolada e desconectada?** Isolada ficou sozinha na componente (não vai e volta de nenhuma outra). Desconectada saiu da maior componente, mas pode estar num grupo pequeno com outras.
4. **Por que a eficiência depois da falha usa o n de antes?** Para que remover parada nunca aumente a eficiência: os pares da parada removida contam 0 em vez de sumir da média.
5. **Por que a simulação não estraga o G_P para a próxima consulta?** Ela só desativa, e no fim religa exatamente o que desligou, inclusive se der erro.

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
