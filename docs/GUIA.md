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
| 29/10 | Arquivo de feature com seção Retomada, reescrita ao fim de toda sessão | Qualquer agente novo precisa saber onde parou e o próximo passo sem reler o código | Só status por camada |
| 29/10 | Todos os arquivos de feature e as issues criados na abertura do repositório | Cada integrante clona, pergunta ao agente o que fazer e começa no mesmo dia | Cada dono cria os seus quando começar |

## 9. Glossário
Parada, padrão, plataforma, embarque, baldeação, intervalo, isócrona, intermediação, ...

## 10. Perguntas de verificação
Todas as perguntas das features, com resposta, agrupadas por seção.
