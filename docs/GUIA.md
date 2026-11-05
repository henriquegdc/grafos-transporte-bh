# Guia do projeto · Análise de redes de transporte público

Para quem não escreveu o código. Explica como a ferramenta funciona e por que foi feita assim.
Não cria requisito: explica o que docs/fontes/ decide. Integrador: Caio.

## 1. Visão geral
O problema, as seis perguntas, o caminho do dado: GTFS -> modelo normalizado -> visões do grafo
-> algoritmos -> interface. Um diagrama de componentes.

## 2. Dados e GTFS (Miguel)
O que é cada arquivo do GTFS, como viram o modelo normalizado, armadilhas, recorte.

## 3. Modelagem e visões do grafo (Henrique)
G_P, G_E, G_L e G_T: o que é vértice, o que é aresta, que pergunta cada uma responde e por quê.
Espera esperada e paradoxo da inspeção. Parâmetros e seus motivos.

## 4. Núcleo do grafo e heap (Thiago)
Lista de adjacência, desativação de vértices e arestas, heap binário, BFS e Dijkstra,
inserção preguiçosa, complexidades.

## 5. Features
Uma subseção por feature, copiada e ajustada de "Como funciona e por quê" do arquivo da feature:
5.1 Trajeto mais rápido · 5.2 Espera · 5.3 Baldeações · 5.4 Centralidades · 5.5 Eficiência ·
5.6 Falhas · 5.7 Desejáveis e opcionais que foram feitas.

## 6. Interface (Arthur)
Como as páginas se organizam, o componente de mapa, o cache da rede.

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

## 9. Glossário
Parada, padrão, plataforma, embarque, baldeação, intervalo, isócrona, intermediação, ...

## 10. Perguntas de verificação
Todas as perguntas das features, com resposta, agrupadas por seção.

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
