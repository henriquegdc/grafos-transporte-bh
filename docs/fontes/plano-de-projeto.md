# Plano de projeto · Trabalho de Grafos

**Tema 5: análise de redes de transporte público**

- **Trabalho:** Ferramenta de Processamento de Dados com Grafos (`enunciado.pdf`).
- **Entrega:** 22/11/2026, domingo, às 23:59, no Canvas. Valor: 15 pontos.
- **Duração:** 25 dias, de 29/10 a 22/11. Código congelado em 15/11.
- **Repositório:** público no GitHub.

| Letra | Integrante | Usuário GitHub | Frente principal |
|---|---|---|---|
| A | Thiago | (a preencher) | Núcleo do grafo e centralidades |
| B | Miguel | (a preencher) | Dados e tempo de espera |
| C | Henrique | (a preencher) | Modelagem e trajeto mais rápido (caminho crítico, seção 6.2) |
| D | Arthur | (a preencher) | Interface e eficiência |
| E | Caio | (a preencher) | Repositório, guia, entrega e falhas |
| F | Rafael | (a preencher) | Relatório e baldeações |

O usuário GitHub é preenchido na criação do repositório; é por ele que as issues são atribuídas e que o agente identifica quem está pedindo tarefa (seção 12.6).

## Como ler este documento

A seção 1 resume o plano em uma página. A seção 2 lê o enunciado e transforma cada exigência em item com dono e prazo. A seção 3 é a proposta técnica para o tema 5. As seções 4 a 13 descrevem o método: requisitos, features, divisão, calendário e regras de trabalho. As seções 14 a 16 tratam da entrega final, dos riscos, das decisões já tomadas e dos próximos passos.

Este documento é a fonte sobre como o grupo trabalha. As seções 3, 5 e 6 do plano aprovado foram para `docs/fontes/REQUISITOS.md`, `docs/fontes/modelagem.md` e `docs/plano-de-desenvolvimento/README.md`; a seção 16.1 é também o início do registro de decisões em `docs/GUIA.md` §8.

## Sumário

1. O plano em uma página
2. Leitura do enunciado
3. Proposta técnica para o tema 5
4. O método enxuto
5. Requisitos e features
6. Divisão entre as seis pessoas
7. Calendário
8. O arquivo de feature
9. Contratos internos
10. Git e verificação local
11. Definition of Done
12. Agentes de IA e domínio do trabalho
13. Rituais
14. Relatório, apresentação e vídeo
15. Riscos e mitigações
16. Decisões tomadas e próximos passos

Apêndice A. Esqueleto do `AGENTS.md`
Apêndice B. Esqueleto do `docs/GUIA.md`

## 1. O plano em uma página

**O que vamos construir.** Uma ferramenta em Python que lê os dados da rede de ônibus de Belo Horizonte no formato GTFS, monta grafos com estrutura e algoritmos próprios, sem NetworkX, e responde seis perguntas. Cada pergunta é uma feature com um dono:

| Pergunta que a ferramenta responde | Feature | Dono |
|---|---|---|
| Qual o trajeto mais rápido de A a B, somando caminhada, espera e viagem? | F-ROTA | Henrique |
| Quanto tempo se espera, e como isso muda com o horário de saída? | F-ESPERA | Miguel |
| Qual o trajeto com menos baldeações, e quanto tempo ele custa a mais? | F-BALD | Rafael |
| Quais paradas são estruturalmente críticas para a rede? | F-MET | Thiago |
| Quão eficiente é a rede, e quais regiões são mal atendidas? | F-EFI | Arthur |
| O que acontece quando uma parada ou uma linha sai de operação? | F-RES | Caio |

**Como vamos trabalhar.** Sete mecanismos:

1. **Fontes com precedência.** Três documentos decidem: `REQUISITOS.md` (o que a ferramenta faz), `modelagem.md` (como o problema vira grafo) e `plano-de-projeto.md` (como o grupo trabalha). Em conflito, o `REQUISITOS.md` vence.
2. **A feature como unidade de trabalho e de memória.** Cada feature tem um arquivo com retomada (onde parou e o próximo passo), especificação, estado, pendências, explicação e roteiro do vídeo. A sessão do agente de IA é descartável; o arquivo não. Quem clona o repositório pergunta ao agente "o que eu preciso fazer?", e o agente responde a partir desses arquivos (seção 12.6).
3. **Dono de ponta a ponta.** Cada pessoa faz a feature inteira: algoritmo, interface, testes, medição de tempo, explicação no guia, seção do relatório e trecho do vídeo.
4. **Contrato antes do código.** A API do núcleo de grafo, o modelo de dados e o contrato de página são publicados no segundo dia, antes de qualquer implementação que dependa deles.
5. **Verificação local e revisão.** Um hook de pre-commit barra biblioteca de grafo em `src/` e erro de lint. A `main` só recebe PR revisado por outro integrante.
6. **Domínio coletivo.** Todos dominam o trabalho inteiro, não só a própria feature. O `docs/GUIA.md` explica como tudo funciona e por quê; cada feature traz perguntas de verificação; duas sessões de explicação cruzada conferem.
7. **Data fixa, escopo variável.** O que não fecha no marco desce de prioridade. As opcionais saem primeiro; a entrega não atrasa. O benchmark contra NetworkX é etapa opcional, só depois de tudo pronto.

**Quando.**

| Período | Datas | Saída |
|---|---|---|
| P0 · Fundação e Etapa 1 | 29/10 a 03/11 | Contratos, núcleo do grafo com heap próprio, dados, modelagem com UML, aplicação com mapa, seções da Etapa 1 |
| P1 · Essenciais | 04/11 a 11/11 | Seis features essenciais de ponta a ponta |
| P2 · Desejáveis | 12/11 a 15/11 | Extensões e, se sobrar tempo, opcionais; código congelado em 15/11 |
| P3 · Entrega | 16/11 a 22/11 | Guia completo, relatório, slides, vídeo; entrega interna em 21/11; Canvas até 22/11 |
| Etapa opcional · Benchmark | 16/11 a 18/11 | Só se todas as essenciais e desejáveis estiverem prontas em 15/11 |

**Por que assim.** Cinco regras decidem o desenho:

- Biblioteca pronta de grafo é proibida. O núcleo próprio vem primeiro, e o hook com a revisão fiscalizam a regra.
- Commits individuais, relatório e vídeo avaliam cada aluno. Cada um precisa de uma feature inteira para mostrar.
- Faltou um item, a nota é zero. Cada item da entrega tem dono e prazo interno.
- Qualquer integrante pode ser perguntado sobre qualquer parte na apresentação. Por isso o guia e as sessões de explicação cruzada.
- A semana de 16/11 é tomada pelo TI5. O código deste trabalho congela em 15/11.

```text
FONTES (decidem; mudam só por decisão do grupo)
  REQUISITOS.md ........ o que a ferramenta faz (vence conflitos)
  modelagem.md ......... como o problema vira grafo e algoritmo
  plano-de-projeto.md .. como o grupo trabalha
          |
          | deriva
          v
  tabela-mestre ........ features por período, cada uma com dono
          |
          v
  arquivo da feature ... especificação, estado, pendências, timeline,
          |              como funciona e por quê, perguntas de verificação,
          |              resultados para o relatório, roteiro do vídeo
          v
  contrato ............. assinatura pública com estado (planejado, implementado)
          |
          v
  código + testes -> hook verde -> PR revisado -> main
          |
          v
  DERIVADOS: GUIA.md, README, relatório SBC (com a Etapa 1), slides, vídeo

  divergência em qualquer ponto -> pendência no arquivo da feature
  -> decisão do grupo -> linha no registro de decisões do GUIA
  -> alteração na fonte
```

## 2. Leitura do enunciado

### 2.1 Checklist de entrega

O enunciado diz que "somente serão avaliadas entregas que tenham todos os itens; a falta de um deles causa nota igual a zero". Por isso cada item tem dono e prazo interno, e Caio confere a checklist em todo fechamento de período.

| # | Item | Etapa | Forma | Dono | Prazo interno |
|---|---|---|---|---|---|
| 1 | Descrição do problema, justificativa da modelagem e plano de desenvolvimento | 1 | Seções do relatório (Introdução, Dados, Modelagem, Plano de desenvolvimento) e `README.md` estruturado com a mesma espinha | Henrique (Caio cuida da parte de instalação do README) | v1 em 03/11; final em 19/11 |
| 2 | Diagramas UML da modelagem | 1 | Figuras no relatório, fontes em `docs/diagramas/` | Henrique (globais) e cada dono (da sua feature) | Globais em 03/11; por feature até 11/11 |
| 3 | Protótipo funcional com interface gráfica que mostra os resultados | 2 | Aplicação Streamlit | Todos; Arthur integra | Congelamento em 15/11 |
| 4 | Código versionado no Git, com histórico e commits individuais | 2 e 3 | Repositório público no GitHub | Todos; Caio cuida do repositório | Contínuo |
| 5 | Relatório técnico em LaTeX, template SBC, 12 a 15 páginas | 3 | `.tex` e PDF | Rafael integra; cada dono escreve sua parte | Completo em 19/11; final em 20/11 |
| 6 | Responsabilidades e o que cada membro fez | 3 | Seção do relatório | Rafael | 20/11 |
| 7 | Slides da apresentação | 3 | PDF | Arthur | 19/11 |
| 8 | Apresentação presencial de 10 min com demonstração, todos participando | 3 | Presencial | Todos | A partir de 24/11; ordem a confirmar |
| 9 | Vídeo de 12 a 18 min, cada aluno mostrando as próprias features | 3 | Link enviado no Canvas junto com o `.zip` | Cada um grava o seu trecho; Caio monta e publica | 20/11 |
| 10 | Arquivo `.zip` com o código-fonte, o `.tex` e o PDF do relatório | Entrega | `.zip` | Caio | 21/11 |
| 11 | Envio no Canvas por cada um dos seis | Entrega | O mesmo `.zip` e o link do vídeo | Cada um | 21/11 (limite: 22/11, 23:59) |
| 12 | Guia do projeto com perguntas de verificação (exigência do grupo, não do enunciado) | Interna | `docs/GUIA.md` | Caio integra; cada dono escreve a sua parte | 17/11 |

### 2.2 Restrições e o que cada uma implica

| Restrição do enunciado | Implicação no plano |
|---|---|
| Proibido usar bibliotecas prontas para criar e processar o grafo, como NetworkX, salvo para comparar desempenho | O núcleo de grafo próprio (`P0-GRAFO`), com heap próprio, é a primeira entrega. NetworkX nunca aparece em `src/`; aparece só em `tests/`, para comparar resultados, e em `benchmarks/`. O hook de pre-commit falha se `src/` importar biblioteca de grafo, e o revisor confere os imports no PR. |
| Commits individuais avaliados; relatório com as responsabilidades de cada membro; vídeo com as features de cada aluno | Divisão vertical: cada feature tem um dono que faz todas as camadas, inclusive a seção do relatório e o trecho do vídeo. Cada um commita com a própria conta. |
| Cada membro entrega a própria cópia; quem não entrega fica com zero | Todos enviam em 21/11 e postam a confirmação no grupo; Caio confere os seis. |
| A falta de um item zera a entrega | Checklist da seção 2.1, com dono e prazo, conferida em cada fechamento. |
| Três etapas com a mesma data | As etapas viram marcos internos: Etapa 1 fecha em 03/11, Etapa 2 em 15/11 e Etapa 3 em 21/11. Tudo é entregue junto em 22/11. |
| Implementação em C/C++, Java ou Python; frontend livre | Python em tudo, inclusive na interface (Streamlit). |
| Relatório em LaTeX, template SBC, 12 a 15 páginas | Relatório dentro do repositório, uma seção por feature, com orçamento de páginas (seção 14.1). A Etapa 1 entra como seções do relatório. |
| Diagramas UML avaliados na modelagem | UML como texto (PlantUML) versionado: diagramas globais na fundação e um por feature no Definition of Done. |
| Bases de dados sugeridas no Kaggle | GTFS da BHTrans, com rede de teste feita à mão como reserva (seção 3.3). |
| Demonstrar a correção, analisar a complexidade e discutir as limitações | O Definition of Done exige teste de corretude, complexidade teórica, tempo medido na rede real e limitações escritas. |
| Avaliação do desempenho no relatório | Obrigatório: complexidade teórica e tempo medido de cada algoritmo. Opcional, no fim: comparação de tempo com NetworkX e curvas de complexidade empírica (seção 3.7). |
| Vídeo de 12 a 18 min com foco nas features de cada aluno; apresentação de 10 min com todos | Roteiro de 2 a 2,5 min por dono no arquivo da feature, gravado depois do congelamento (seção 14). |
| Cópias são zeradas | Código escrito pelo grupo, commits próprios e datados como prova de autoria, toda fonte externa citada no relatório. O repositório é público, e esse risco está na seção 15. |

### 2.3 Respostas e hipóteses

| ID | Questão | Situação |
|---|---|---|
| P-01 | Formato do documento da Etapa 1 | Decidido: seções do relatório SBC e `README.md` estruturado; tudo entregue junto em 22/11 |
| P-02 | Como entregar o vídeo | Decidido: link enviado no Canvas junto com o `.zip` |
| P-03 | Data e ordem da apresentação presencial | As apresentações começam em 24/11. **Ordem ainda aberta;** Henrique confirma |
| P-04 | `heapq` e pandas são permitidos? | Decidido: pandas permitido, só para ler os CSV; fila de prioridade própria, sem `heapq` |
| P-05 | NetworkX nos testes de corretude | Decidido pelo grupo: permitido em `tests/` só para comparar o resultado do nosso algoritmo com o dele; nunca em `src/` |
| P-06 | Repositório privado ou público | Decidido: público |
| P-07 | Data da tarefa no Canvas | 22/11, 23:59 |

## 3. Proposta técnica para o tema 5

Movida para `docs/fontes/REQUISITOS.md` (§3.1) e `docs/fontes/modelagem.md` (§3.2 a §3.8).

## 4. O método enxuto

### 4.1 Por que usar um método

Seis pessoas, 25 dias, agentes de IA na maior parte das tarefas e regras que zeram a nota. As falhas prováveis são cinco:

1. **Trabalho concentrado em uma ou duas pessoas.** Prejudica justamente quem fez pouco, porque commits, relatório e vídeo avaliam cada um.
2. **Peças que não encaixam.** Cada agente inventa um formato de grafo ou de dado, e a integração vira retrabalho no fim.
3. **Relatório e vídeo no último fim de semana.** Com 12 a 15 páginas, UML e 12 a 18 minutos de vídeo, não cabe.
4. **Um item esquecido.** Basta um para zerar.
5. **Domínio fragmentado.** Cada um conhece só a própria parte, que muitas vezes foi escrita por um agente, e trava quando é perguntado sobre o resto.

O dono de ponta a ponta resolve a primeira; fonte de verdade, contrato antes do código e arquivo de feature resolvem a segunda; relatório e vídeo no Definition of Done resolvem a terceira; a checklist resolve a quarta; o guia, as perguntas de verificação e a explicação cruzada resolvem a quinta.

### 4.2 O que mantemos e o que cortamos

O método vem do TI5, um projeto de seis meses. Para um trabalho de um mês, fica só o que se paga em 25 dias.

**Mantemos:**

- **Fontes com precedência.** Com seis pessoas e agentes, o texto mais próximo no contexto vira regra; a precedência escrita evita duas implementações do mesmo requisito.
- **Arquivo de feature.** É a memória que sobrevive à sessão do agente e a fonte da seção do relatório, do guia e do roteiro do vídeo.
- **Dono de ponta a ponta.** Commits, relatório e vídeo avaliam cada aluno.
- **Contrato antes do código.** Os contratos são a API do núcleo de grafo, o modelo de dados e o contrato de página.
- **Data fixa e escopo variável.** O prazo é único e não se negocia.

**Cortamos:**

- **CI/CD e releases (tags).** Não há servidor nem versão publicada; o custo de manter um pipeline não se paga em um mês. A regra crítica, a de importar biblioteca de grafo, fica garantida pelo hook local e pela revisão do PR.
- **Plantão, ata, reunião semanal e check-in diário.** O grupo se coordena por mensagens e pelo Kanban; as decisões vão para o registro de decisões do guia.
- **Controle de mudança formal.** Fica uma versão leve: pendência no arquivo da feature, decisão do grupo, linha no registro de decisões.
- **OpenAPI, mensageria, migrations, design system, homologação e deploy.** Não existem nesta ferramenta.

**Acrescentamos:**

- **`docs/GUIA.md` e perguntas de verificação.** Todos precisam dominar o trabalho inteiro, mesmo o que foi feito com IA.
- **Relatório e vídeo no Definition of Done.** Quem fez escreve logo depois de fazer.
- **UML como texto, um diagrama por feature.** UML é avaliado; PlantUML entra no Git com autoria.

### 4.3 Princípios

- **P1. Uma fonte de verdade, com precedência.** O `REQUISITOS.md` decide o que a ferramenta faz e vence qualquer conflito.
- **P2. Agente não altera a fonte.** Divergência vira pendência e decisão do grupo.
- **P3. O estado vive no repositório.** Toda sessão termina atualizando o arquivo da feature. O teste: se a sessão acabar agora, outra pessoa continua só com o que está commitado?
- **P4. Dono de ponta a ponta.** É também a forma de cada um ter o que mostrar na nota.
- **P5. Contrato antes do código.** A assinatura pública é escrita antes da implementação, com estado.
- **P6. Ninguém integra o que não sabe explicar.** Nem o dono, nem o revisor. Toda decisão tem o porquê escrito.
- **P7. Data é piso, escopo é a variável.**

### 4.4 Estrutura do repositório

```text
/
├── AGENTS.md                  # contexto raiz para agentes e pessoas
├── CLAUDE.md                  # uma linha: leia AGENTS.md
├── README.md                  # Etapa 1 resumida; instalar, rodar, testar
├── requirements.txt           # versões fixadas
├── .githooks/
│   └── pre-commit             # imports proibidos + ruff
├── .github/
│   └── pull_request_template.md
├── docs/
│   ├── GUIA.md                # como tudo funciona e por quê; registro de decisões
│   ├── fontes/                # FONTE: decide
│   │   ├── REQUISITOS.md
│   │   ├── modelagem.md
│   │   └── plano-de-projeto.md
│   ├── plano-de-desenvolvimento/
│   │   ├── README.md          # tabela-mestre e cobertura dos RFs
│   │   └── features/
│   │       └── feature-<ID>.md
│   └── diagramas/             # fontes .puml e imagens geradas
├── src/transporte/
│   ├── dados/                 # leitura do GTFS, modelo normalizado, rede de teste
│   ├── grafo/                 # núcleo: estrutura, heap, BFS, Dijkstra
│   ├── modelo/                # construtores de G_P, G_E, G_L e G_T
│   ├── algoritmos/            # algoritmos das features
│   ├── simulacao/             # espera, Monte Carlo, falhas
│   ├── util/                  # medição de tempo
│   └── interface/             # app Streamlit, mapa, paginas/<feature>.py
├── tests/                     # espelha src/; NetworkX só para comparar resultados
├── benchmarks/                # etapa opcional; NetworkX permitido
├── dados/                     # brutos/ (fora do Git, baixados por script) e rede-teste/
├── scripts/                   # download do GTFS, verificar_imports.py
├── relatorio/                 # LaTeX SBC: main.tex, secoes/<secao>.tex, figuras/
└── apresentacao/              # slides e roteiro do vídeo
```

- `AGENTS.md` e `CLAUDE.md` ficam na raiz porque as ferramentas de agente os procuram ali.
- Referências entre documentos usam o caminho a partir da raiz, nunca o nome solto do arquivo.
- Se a estrutura mudar, os caminhos são corrigidos no `plano-de-projeto.md` e no `AGENTS.md` na mesma passada.

### 4.5 Fontes, guia e derivados

| Documento | Papel | Quem edita |
|---|---|---|
| `docs/fontes/REQUISITOS.md` | O que a ferramenta faz: problema, perguntas, RFs com prioridade, RNFs, dados, fora de escopo | O grupo. Em baseline desde 29/10; muda só por decisão registrada |
| `docs/fontes/modelagem.md` | Como o problema vira grafo: modelo de dados, visões, parâmetros, algoritmos e complexidade, diagramas UML | Henrique integra; cada dono escreve a parte da sua feature |
| `docs/fontes/plano-de-projeto.md` | Como o grupo trabalha (este plano, depois de aprovado) | O grupo |
| `docs/GUIA.md` | Explica a ferramenta de ponta a ponta para quem não escreveu o código: como cada parte funciona, por que foi feita assim, quais alternativas foram descartadas. Contém o **registro de decisões**, que é o lugar canônico de toda decisão do grupo | Caio integra; cada dono escreve a parte da sua feature a partir do arquivo da feature |

O guia não cria requisito nem muda modelagem: explica o que as fontes decidem. Quando uma decisão é tomada, ela entra no registro de decisões do guia (data, decisão, porquê, alternativas descartadas, o que afeta) e é aplicada na fonte no mesmo commit.

| Derivado | Deriva de |
|---|---|
| `README.md` | Etapa 1 resumida (`REQUISITOS.md` §1 a §3 e `modelagem.md`) e instruções de uso |
| Relatório SBC, inclusive as seções da Etapa 1 | `REQUISITOS.md`, `modelagem.md`, arquivos de feature (resultados, complexidade, tempos, limitações) e este plano (seção de plano de desenvolvimento) |
| Slides | Relatório |
| Vídeo | Roteiros dos arquivos de feature |
| Seção de responsabilidades | Tabela-mestre e `git log` |

**Mudança, versão leve.** Quem encontra a divergência registra uma pendência no arquivo da feature e avisa no grupo. O grupo decide por mensagem. Quem aplica registra a decisão no guia, com o que é afetado (features, testes, relatório, diagramas) e o que não é.

## 5. Requisitos e features

Movida para `docs/fontes/REQUISITOS.md` (§5.1 e §5.2) e `docs/plano-de-desenvolvimento/README.md` (§5.3 e §5.4).

## 6. Divisão entre as seis pessoas

Movida para `docs/plano-de-desenvolvimento/README.md` (§6).

## 7. Calendário

### 7.1 Períodos e marcos

| Período | Datas | Objetivo | Fecha com |
|---|---|---|---|
| P0 · Fundação e Etapa 1 | 29/10 (qui) a 03/11 (ter) | Contratos, núcleo do grafo com heap, dados, modelagem e UML, aplicação com mapa, relatório compilando, esqueleto do guia | `modelagem.md` v1; seções da Etapa 1 v1 no relatório e no README; explicação cruzada 1 |
| P1 · Essenciais | 04/11 (qua) a 11/11 (qua) | As seis features essenciais de ponta a ponta | Checkpoint em 07/11 (sáb); fechamento em 11/11 com o DoD conferido |
| P2 · Desejáveis | 12/11 (qui) a 15/11 (dom) | Extensões desejáveis; opcionais só se sobrar tempo | Congelamento do código em 15/11, às 23:59 |
| P3 · Entrega | 16/11 (seg) a 22/11 (dom) | Guia completo, relatório final, slides, vídeo, ensaio, `.zip` | Explicação cruzada 2 em 16/11; guia completo em 17/11; relatório completo em 19/11; vídeo montado em 20/11; entrega interna e envio de todos em 21/11 (sáb); limite do Canvas em 22/11, às 23:59 |
| Etapa opcional · Benchmark | 16/11 (seg) a 18/11 (qua) | Comparação com NetworkX, complexidade empírica e página Desempenho | Só acontece se todas as essenciais e desejáveis cumpriram o DoD em 15/11; não toca `src/` |

Regras do calendário:

- **A tabela é piso, não teto.** Cada marco é o mínimo pronto naquele dia; chegar antes é desejável.
- **Teste, relatório e guia não são fase.** São escritos junto com a feature. O P3 só junta, revisa e grava.
- **O congelamento de 15/11 não se antecipa nem se estica.** Depois dele, só correção de defeito.
- **Terminar antes não vira escopo novo.** Quem fecha cedo puxa a próxima feature na ordem de prioridade, ou investe em testes, guia e relatório.

### 7.2 Período 0, dia a dia

| Dia | Alvo |
|---|---|
| 29/10 (qui) | Com o ok do grupo, Henrique cria o repositório público e, com um agente, sobe a estrutura da seção 4.4, o `AGENTS.md`, as fontes a partir deste plano, os arquivos de **todas** as features (seção 12.6) e as issues do backlog, atribuídas aos donos. Caio assume o P0-REPO a partir daí: hook, `verificar_imports.py`, proteção da `main`, Kanban e README de instalação. Todos clonam, ativam o hook e pedem ao agente a primeira tarefa. |
| 30/10 (sex) | Contratos publicados como "planejado": API do grafo e do heap (Thiago), modelo normalizado (Miguel) e contrato de página (Arthur). Henrique começa os diagramas UML globais. |
| 31/10 (sáb) | Rede de teste GTFS com respostas conhecidas e confirmação do feed BHTrans (Miguel). Assinaturas dos construtores (Henrique). Relatório SBC compilando e função de medição (Rafael). Esqueleto do guia com o registro de decisões de 29/10 (Caio). |
| 01/11 (dom) | Núcleo com heap, BFS e Dijkstra testados (Thiago). Feed BHTrans lido no modelo normalizado (Miguel). |
| 02/11 (seg, feriado) | Trabalho assíncrono, sem sessão marcada: G_P sobre a rede de teste (Henrique); aplicação com mapa e páginas vazias (Arthur). |
| 03/11 (ter) | G_E sobre a rede de teste e diagramas UML globais: classes, componentes e casos de uso (Henrique). Feed real recortado (Miguel). `modelagem.md` v1, seções da Etapa 1 v1 no relatório e no README (Henrique). Explicação cruzada 1, sobre a fundação. Fechamento do P0. |

### 7.3 Gatilhos de corte

| Se | Até | Então |
|---|---|---|
| O núcleo do grafo não tem heap, BFS e Dijkstra testados | 01/11 | Rafael pareia com Thiago até fechar; as features começam contra a assinatura publicada |
| O feed real não está carregado | 03/11 | Segue com a rede de teste ampliada ou com o dataset reserva; o feed real vira pendência do P1, sem bloquear features |
| Uma feature essencial não fechou a parte central | 07/11 (checkpoint) | O dono reduz ao mínimo que cumpre os RFs e registra o resto como pendência |
| Uma feature essencial não cumpriu o Definition of Done | 11/11 | Desce para o P2 e ocupa o lugar das extensões do dono; as opcionais dele saem |
| Qualquer feature incompleta | 15/11 | Sai do escopo e vira limitação no relatório |
| Alguma essencial ou desejável sem DoD | 15/11 | A etapa opcional de benchmark não acontece |
| Guia com lacunas | 17/11 | Caio lista as lacunas; cada dono completa até 18/11 |
| Relatório fora de 12 a 15 páginas | 19/11 | Rafael corta pelas seções com folga, seguindo o orçamento da seção 14.1 |

### 7.4 Feriados e o TI5

- **Feriados:** 02/11 (segunda, Finados), no P0, só com trabalho assíncrono; 15/11 (domingo, Proclamação da República), dia do congelamento; 20/11 (sexta, Consciência Negra), no P3, só a montagem do vídeo. Nenhuma sessão é marcada nessas datas.
- **TI5:** o TI5 congela features em 17/11, vai para produção em 24/11 e entrega em 01/12. Quem está nos dois trabalhos terá a semana de 16/11 cheia. Por isso o código deste trabalho congela em 15/11, e a última semana fica com guia, relatório, vídeo e entrega, tarefas que já chegam adiantadas pelo Definition of Done.

## 8. O arquivo de feature

É a peça central do método: a especificação da entrega, o painel de estado, a memória que sobrevive às sessões de agente e a fonte da explicação que vai para o guia. Fica em `docs/plano-de-desenvolvimento/features/feature-<ID>.md`. Os arquivos de todas as features são criados na abertura do repositório, já com objetivo, RFs, dependências, contrato inicial, critérios de aceite, plano de implementação e a primeira retomada ("não iniciado; primeiro passo: ..."), para que qualquer agente saiba o que fazer desde o primeiro dia.

A seção **Retomada** é o que um agente novo lê primeiro. Ela é reescrita, não acumulada, ao fim de toda sessão; o histórico fica na timeline.

```markdown
# <ID> · <Nome da feature>

**Período:** N · **Classe:** fundacao | prioritaria | desejavel | opcional
**Dono:** <nome> (@<usuário GitHub>) · **Issue:** #<n> · **Visões do grafo:** G_P | G_E | G_L | G_T
**Depende de:** <IDs e contratos, com o estado de cada um> · **Bloqueia:** <IDs>

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-...). Modelagem: docs/fontes/modelagem.md §<n>.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** DD/MM, <nome>.
- **Onde parou:** o que ficou pronto e o que ficou pela metade.
- **Próximo passo:** uma ação concreta, a primeira coisa a fazer na próxima sessão.
- **Arquivos tocados:** caminhos.
- **Como testar:** comando exato (ex.: `pytest tests/grafo/test_dijkstra.py`).
- **Bloqueios:** o que impede de avançar e de quem depende (ou "nenhum").

## Objetivo
O que a feature entrega e para quem. Os RFs que fecha, um por linha.

## Status
| Camada                     | Status | Observação (data, evidência, o que falta) |
|----------------------------|--------|-------------------------------------------|
| Núcleo (algoritmo)         |        |                                           |
| Modelo e dados             |        |                                           |
| Interface                  |        |                                           |
| Testes                     |        |                                           |
| Desempenho (tempo medido)  |        |                                           |
| Guia (explicação e quiz)   |        |                                           |
| Relatório                  |        |                                           |
| Vídeo                      |        |                                           |

## Especificação
Assinaturas públicas (contrato), entradas e saídas, visão do grafo usada,
algoritmo, complexidade de tempo e de espaço.

## Como funciona e por quê
Escrito para um colega que não viu o código. Atualizado a cada etapa concluída do plano de
implementação, não só no fim:
- O problema que a feature resolve, em uma frase.
- A visão do grafo usada e por que ela, e não outra.
- O algoritmo passo a passo, com um exemplo pequeno.
- A complexidade, com a justificativa (de onde vem cada termo).
- As decisões tomadas, com as alternativas descartadas e o motivo.
- As limitações conhecidas.

## Perguntas de verificação
3 a 5 perguntas que qualquer integrante deve saber responder, cada uma com a resposta curta.
1. **P:** ... **R:** ...

## Critérios de aceite
- [ ] Verificável, citando o RF que comprova.

## Definition of Done
(lista-base da seção 11, marcada) + itens próprios da feature.

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | |
| 2 | Algoritmo com testes de corretude | |
| 3 | Integração com a visão do grafo e com os dados reais | |
| 4 | Página na interface | |
| 5 | Tempo medido na rede real e complexidade justificada | |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | |

## Resultados para o relatório
Números (com a origem: comando e saída), tempos medidos (V, E, máquina), figuras geradas (caminho),
limitações observadas.

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

## Pendências
- **<Assunto>:** descrição, de quem depende, o que bloqueia.
- ~~**<Assunto>**~~ **decidido em DD/MM/AAAA:** a decisão e onde foi aplicada.

## Timeline
### Criação DD/MM/AAAA: origem do arquivo.
### Dono DD/MM/AAAA: feature atribuída a <nome>.
```

Status usados: `não iniciado`, `em andamento`, `implementado`, `parcial`, `concluído`, `não aplicável`. Pendência resolvida não se apaga: é riscada, com a decisão ao lado. Não existe arquivo global de pendências; quando o grupo precisa da visão consolidada, um agente varre os arquivos de feature (seção 12.5).

## 9. Contratos internos

Não há HTTP nem mensageria, mas há fronteiras entre pessoas. Cada uma vira um contrato: a assinatura pública, com docstring e complexidade, publicada antes da implementação com o comentário `estado: planejado`, que passa a `implementado` quando os testes passam. Mudança numa assinatura que outra pessoa consome é avisada no grupo antes e registrada na timeline da feature.

**Núcleo de grafo e heap** (dono: Thiago)

```python
# src/transporte/grafo/heap.py · estado: planejado
class HeapMin:
    """Heap binário de mínimo sobre lista. Espaço O(n)."""

    def inserir(self, prioridade: float, item: int) -> None: ...  # O(log n)
    def extrair_min(self) -> tuple[float, int]: ...             # O(log n)
    def vazio(self) -> bool: ...                                 # O(1)
    def __len__(self) -> int: ...                                # O(1)

# src/transporte/grafo/grafo.py · estado: planejado
class Grafo:
    """Grafo dirigido e ponderado. Vértices 0..n-1, lista de adjacência. Espaço O(V + E)."""

    def adicionar_vertice(self, rotulo: str) -> int: ...
    def adicionar_aresta(self, u: int, v: int, peso: float, tipo: str = "") -> int: ...
    def vizinhos(self, u: int) -> list[tuple[int, float, int]]: ...  # (destino, peso, id da aresta), só ativas
    def desativar_vertice(self, u: int) -> None: ...
    def desativar_aresta(self, a: int) -> None: ...
    def reativar_tudo(self) -> None: ...
    def reverso(self) -> "Grafo": ...

# src/transporte/grafo/buscas.py · estado: planejado
def bfs(g: Grafo, origem: int) -> Resultado: ...                                   # O(V + E)
def dijkstra(g: Grafo, origem: int, destino: int | None = None) -> Resultado: ...  # O((V + E) log V)
def caminho(r: Resultado, destino: int) -> list[int]: ...
```

O Dijkstra usa inserção preguiçosa: em vez de diminuir a chave de um vértice já no heap, insere de novo com a distância menor e descarta, na extração, as entradas desatualizadas. O heap chega a O(E) entradas, e como log E ≤ 2 log V, a complexidade continua O((V + E) log V).

**Modelo normalizado de dados** (dono: Miguel)

```python
# src/transporte/dados/modelo.py · estado: planejado
@dataclass(frozen=True)
class Parada:
    id: str
    nome: str
    lat: float
    lon: float

@dataclass(frozen=True)
class Padrao:  # sequência de paradas de uma linha num sentido
    id: str
    linha_id: str
    paradas: tuple[str, ...]

@dataclass
class Rede:
    paradas: dict[str, Parada]
    linhas: dict[str, Linha]
    padroes: dict[str, Padrao]
    partidas: dict[tuple[str, str], list[int]]  # (padrão, parada) -> horários em segundos

    def recortar(self, caixa=None, linhas=None) -> "Rede": ...
```

**Página da interface** (dono do contrato: Arthur)

```python
# src/transporte/interface/paginas/trajetos.py · estado: planejado
TITULO = "Trajetos"

def render(rede: RedeCarregada) -> None:
    """Desenha a página. Usa interface/mapa.py para o mapa."""
```

**Medição de tempo** (dono: Rafael)

```python
# src/transporte/util/medicao.py · estado: planejado
@dataclass(frozen=True)
class Medicao:
    media_s: float
    desvio_s: float
    repeticoes: int

def medir(func, *args, repeticoes: int = 5, **kwargs) -> Medicao: ...  # usa time.perf_counter
```

Os nomes acima são proposta. O que importa é que estejam escritos e commitados até 30/10 (31/10 para a medição), porque é contra eles que os agentes de cada pessoa vão programar.

## 10. Git e verificação local

Sem CI/CD e sem releases. A segurança vem de três camadas locais e humanas: o hook de pre-commit, o pytest antes do PR e a revisão de outro integrante.

**Branches.**

```text
feat/<ID>-<assunto> --(hook verde + pytest verde + PR com 1 aprovação)--> main
  (vida de 1 a 3 dias)
```

- A `main` é protegida no GitHub: só recebe PR, com uma aprovação de outro integrante.
- O trabalho acontece em branches curtas `feat/<ID>-<assunto>`, como `feat/F-ROTA-dijkstra`. Branch longa é o que gera conflito.
- `git pull --rebase` antes de começar e antes de subir. Quem quebrar a `main` conserta ou reverte na hora.
- Sem tags de versão: a entrega é o estado da `main` em 21/11.

**Hook de pre-commit.** O arquivo `.githooks/pre-commit` roda, a cada commit:

1. `python scripts/verificar_imports.py`: lê os imports de `src/` com o módulo `ast` e falha se aparecer biblioteca de grafo.
2. `ruff check`.

Cada integrante ativa o hook uma vez, ao clonar: `git config core.hooksPath .githooks` (instrução no README). O pytest roda antes de abrir o PR, e o resumo da saída vai na descrição. Como o hook pode ser pulado com `--no-verify` ou não estar ativado, o revisor também confere os imports no diff, e Caio roda o script de novo em cada fechamento de período.

**Revisão.** O revisor aprova só o que entende. Se não consegue explicar o que o código faz, pede ao dono que explique ou melhore a seção "Como funciona e por quê" antes de aprovar. Isso espalha o domínio do código pelo grupo.

**Commits.** Conventional Commits com o ID da feature como escopo: `feat(F-ROTA): reconstrói o trajeto por trechos`, `test(P0-GRAFO): casos de borda do Dijkstra`, `docs(F-MET): seção do relatório`. Um commit por assunto. Com isso, a seção de responsabilidades do relatório sai quase pronta do `git log`.

**Autoria.** O professor avalia commits individuais, e o repositório é público, então o histórico também é a prova de autoria:

- Cada um commita com a própria conta, com `user.name` e `user.email` iguais aos do GitHub.
- O trabalho de uma pessoa nunca entra pelo commit de outra.
- Em pareamento entre integrantes, o commit leva `Co-authored-by: Nome <email>` do colega.
- Agente de IA não é autor nem coautor: quem roda o agente revisa e commita, sem trailer de atribuição ao agente.

**Template de PR** (`.github/pull_request_template.md`):

```markdown
## Feature
<ID> · <nome> · docs/plano-de-desenvolvimento/features/feature-<ID>.md

## O que muda

## Verificação
- [ ] Hook ativo e verde (imports proibidos e ruff)
- [ ] pytest verde localmente (resumo da saída abaixo)

## Definition of Done
- [ ] Testes de corretude com gabarito à mão (e comparação com NetworkX, se houver equivalente)
- [ ] Complexidade declarada na docstring
- [ ] Tempo medido na rede real registrado no arquivo da feature
- [ ] Página ou bloco na interface
- [ ] "Como funciona e por quê" e perguntas de verificação escritas
- [ ] Diagrama UML da feature
- [ ] Seção do relatório
- [ ] Roteiro do vídeo
- [ ] Arquivo da feature atualizado, com a Retomada reescrita

## Para o revisor
Aprove só se conseguir explicar o que este código faz.
```

## 11. Definition of Done

Obrigatório para toda feature:

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [ ] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [ ] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente
- [ ] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [ ] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
- [ ] Página ou bloco na interface funcionando com o dataset real
- [ ] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/`
- [ ] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação
- [ ] Roteiro do vídeo escrito no arquivo da feature
- [ ] Arquivo da feature atualizado: retomada ("concluída"), status, pendências e timeline

Uma feature pode acrescentar itens no próprio arquivo, nunca remover. As features de fundação marcam como "não aplicável" o que não se aplica a elas (por exemplo, página na interface para `P0-REPO`), sempre com o motivo. A comparação de tempo com o NetworkX não faz parte do DoD: pertence à etapa opcional.

## 12. Agentes de IA e domínio do trabalho

### 12.1 Arquivos de contexto

- **`AGENTS.md` na raiz** (esqueleto no Apêndice A), em Markdown puro. `CLAUDE.md` tem uma linha apontando para ele; o conteúdo vive num lugar só.
- O `AGENTS.md` traz só o mínimo operacional e aponta para a seção da fonte. Resumo que reescreve regra envelhece e passa a divergir da fonte, e o agente lê o resumo.

### 12.2 Pacote de contexto por sessão

| Sessão | Precisa ter em contexto |
|---|---|
| Implementação | `AGENTS.md`, RFs da feature no `REQUISITOS.md`, arquivo da feature, seção da visão usada em `modelagem.md` |
| Interface | O pacote acima, mais o contrato de página e o componente de mapa |
| Explicação para o guia | Código da feature, arquivo da feature, `modelagem.md` e o registro de decisões do `docs/GUIA.md` |
| Seção do relatório | Arquivo da feature (Especificação, Como funciona e Resultados), orçamento de páginas |
| Revisão ou validação | O que a pergunta exige; sessão só de leitura, que entrega lista de defeitos e não corrige |

### 12.3 Regras

1. Toda sessão de implementação começa com o pacote de contexto.
2. O agente atualiza o arquivo da feature ao fim de toda sessão, mesmo quando a sessão termina no meio de uma etapa: retomada reescrita, status, pendências, decisões e timeline. Sessão que não atualiza a retomada não terminou (prompt de fechamento na seção 12.5).
3. O agente não edita arquivo de feature que não é do seu dono.
4. O agente não altera `docs/fontes/` por conta própria; divergência vira pendência e decisão do grupo.
5. O agente não importa biblioteca de grafo em `src/`; NetworkX só em `tests/` (comparação de resultado) e em `benchmarks/`.
6. O agente não escreve no relatório nem no guia número que não saiu de execução real; todo número vem de um comando registrado.
7. O agente pode rascunhar "Como funciona e por quê" e as perguntas de verificação; o dono revisa e reescreve tudo o que não entendeu. Decisão sem porquê registrado vira pendência, não invenção.
8. Quem roda o agente revisa e commita; o agente não é autor nem coautor.

### 12.4 Integridade e domínio

Cada integrante precisa explicar o próprio código no vídeo e na apresentação, e qualquer integrante pode ser perguntado sobre qualquer parte. O agente acelera, mas a explicação é individual e é avaliada. Por isso:

- **Ninguém integra o que não sabe explicar.** Vale para o dono e para o revisor (seção 10).
- **Tudo tem o porquê escrito.** O `docs/GUIA.md` explica a ferramenta de ponta a ponta, e o registro de decisões guarda cada escolha com as alternativas descartadas.
- **O domínio é verificado.** Cada feature traz perguntas de verificação com resposta. Nas sessões de explicação cruzada (seção 13), cada um responde perguntas de features que não são suas.
- **Antes de gravar,** o dono explica a feature para outro integrante sem olhar o código; o que não conseguir explicar, revisa antes de gravar.

### 12.5 Modelos de prompt

**Abertura de sessão de implementação**

```text
Leia, nesta ordem: AGENTS.md, docs/fontes/REQUISITOS.md (RFs da feature),
docs/plano-de-desenvolvimento/features/feature-<ID>.md e docs/fontes/modelagem.md §<visão>.
Tarefa: executar a etapa <N> do plano de implementação da feature.
Regras: não edite docs/fontes/ nem arquivos de outras features; não importe biblioteca
de grafo em src/; divergência vira pendência no arquivo da feature.
Ao terminar: pytest e ruff verdes; status, pendências e timeline atualizados;
um commit por assunto em Conventional Commits (eu reviso e commito).
```

**Rascunho de "Como funciona e por quê"**

```text
A partir do código da feature <ID> (src/...), de docs/plano-de-desenvolvimento/features/feature-<ID>.md,
de docs/fontes/modelagem.md e do registro de decisões em docs/GUIA.md, escreva a seção
"Como funciona e por quê" para um colega que não viu o código: o problema, a visão do grafo
usada e por que ela, o algoritmo passo a passo com um exemplo pequeno, a complexidade com a
justificativa de cada termo, as decisões com as alternativas descartadas e as limitações.
Depois, 3 a 5 perguntas de verificação com resposta curta. Não invente decisão que não esteja
registrada; se faltar o porquê de algo, liste como pendência.
```

**Rascunho da seção do relatório**

```text
A partir de docs/plano-de-desenvolvimento/features/feature-<ID>.md (Especificação, Como funciona
e Resultados), escreva relatorio/secoes/<id>.tex com no máximo <p> páginas: problema, visão do
grafo, algoritmo e complexidade, tempo medido, resultado com a figura <arquivo> e limitação.
Use só números que estão no arquivo da feature. Não invente referência.
```

**Validação independente**

```text
Sem contexto anterior. Confira a feature <ID> contra os RFs citados no arquivo da feature
e contra docs/fontes/modelagem.md. Rode os testes. Liste só defeitos verificáveis, cada um
com arquivo, linha, cenário de falha e a regra violada. Não corrija nada.
```

**Consolidação de pendências**

```text
Varra docs/plano-de-desenvolvimento/features/feature-*.md e liste as pendências abertas (não
riscadas), agrupadas em: decisão do grupo, bloqueio entre features e débito técnico.
Cite o arquivo de cada uma. Somente leitura.
```

**Fechamento de sessão**

```text
Antes de encerrar: reescreva a seção Retomada de
docs/plano-de-desenvolvimento/features/feature-<ID>.md (onde parou, próximo passo concreto,
arquivos tocados, comando para testar, bloqueios); atualize status, pendências e timeline;
se uma etapa do plano de implementação foi concluída, atualize "Como funciona e por quê".
Confira que pytest e ruff estão verdes e liste os commits sugeridos (eu reviso e commito).
```

### 12.6 Como cada integrante começa

A ideia é que ninguém precise ler o plano inteiro para começar: clona, abre um agente e pergunta.

**Passo a passo do integrante.**

1. `git clone` do repositório, `pip install -r requirements.txt` e `git config core.hooksPath .githooks`.
2. Conferir que `git config user.email` é o mesmo e-mail da conta GitHub.
3. Abrir o agente na raiz do repositório e mandar:

```text
Leia o AGENTS.md e me diga o que eu preciso fazer agora.
```

**O que o agente faz** (roteiro escrito no `AGENTS.md`, seção 0):

1. Identifica quem está pedindo pelo `git config user.email` (ou pergunta o nome) e acha o integrante na tabela do `AGENTS.md`.
2. Lista as features desse integrante na ordem de período, a partir da tabela-mestre (`docs/plano-de-desenvolvimento/README.md`), e, se o `gh` estiver disponível, as issues abertas atribuídas a ele.
3. Escolhe a feature ativa: a primeira que não está "concluída".
4. Lê a Retomada, o status e as dependências da feature. Se um contrato de que ela depende ainda está "planejado", avisa e propõe o que dá para fazer contra a assinatura publicada.
5. Responde com: a feature ativa, o próximo passo concreto, os arquivos a ler (pacote de contexto da seção 12.2), o prazo do calendário e os bloqueios.
6. Só começa a implementar depois que o integrante confirmar.

**Issues do backlog.** Geradas na criação do repositório, uma por feature (as 26 da tabela-mestre), mais uma por item da checklist da seção 2.1 que não é feature (slides, vídeo, `.zip`, envio no Canvas):

| Campo | Conteúdo |
|---|---|
| Título | `<ID> · <nome da feature>` |
| Responsável | Usuário GitHub do dono |
| Labels | Período (`P0`, `P1`, `P2`, `P3`, `opcional`) e classe (`fundação`, `prioritária`, `desejável`, `opcional`) |
| Milestone | O período, com a data de fechamento (milestone é só agrupamento de prazo, não release) |
| Corpo | Link para o arquivo da feature, RFs, dependências, prazo e a checklist do Definition of Done |

O PR que fecha a feature referencia a issue (`Closes #<n>`). O arquivo da feature continua sendo a memória detalhada; a issue é o índice no quadro.

## 13. Rituais

Só o necessário para um mês. A coordenação do dia a dia é pelo grupo de mensagens; as decisões vão para o registro de decisões do guia.

| Ritual | Quando | O que sai |
|---|---|---|
| Quadro Kanban | Contínuo | Issues geradas na criação do repositório (seção 12.6), no GitHub Projects, com o ID no título, o dono atribuído e os PRs ligados |
| Explicação cruzada 1 · fundação | 03/11 (ter), cerca de 40 min | Cada dono de P0 explica em 5 min a sua peça (núcleo e heap, dados, visões do grafo, interface, relatório, guia). Dúvidas viram pendência no arquivo da feature |
| Explicação cruzada 2 · features | 16/11 (seg), cerca de 60 min | Cada dono explica a sua feature em 6 min; em seguida, cada integrante responde, sem consulta, duas perguntas de verificação sorteadas de features que não são suas. Resposta errada vira melhoria no guia até 17/11 |
| Fechamento de período | 03/11, 11/11 e 15/11 | Caio confere o DoD no Kanban, roda `scripts/verificar_imports.py` e revisa a checklist da seção 2.1 |
| Ensaios | 19/11 e 21/11 | Apresentação cronometrada, com perguntas cruzadas: cada um pergunta sobre a feature de outro |

## 14. Relatório, apresentação e vídeo

### 14.1 Relatório SBC (12 a 15 páginas)

O relatório fica em `relatorio/`, com o template oficial da SBC, um `main.tex` e uma pasta `secoes/` com um arquivo por seção, editado no repositório e compilado localmente; o Overleaf pode servir só para visualizar. As seções da Etapa 1 (Introdução, Dados, Modelagem e Plano de desenvolvimento) ficam prontas em v1 no fim do P0. Cada seção de feature é escrita pelo dono no Definition of Done, então o P3 só junta, revisa e ajusta o tamanho.

| # | Seção | Conteúdo | Dono | Páginas |
|---|---|---|---|---|
| 1 | Introdução | Contexto, problema, objetivos e as seis perguntas | Henrique | 1 |
| 2 | Fundamentação | GTFS, modelos de grafo para transporte, algoritmos usados | Thiago e Henrique | 1 |
| 3 | Dados | Fonte, limpeza, recorte e estatísticas da rede | Miguel | 1 |
| 4 | Modelagem | Modelo de dados, visões G_P, G_E, G_L e G_T, diagramas UML | Henrique | 2,5 |
| 5 | Plano de desenvolvimento | Método, divisão e calendário (Etapa 1) | Henrique | 0,5 |
| 6 | Implementação | Núcleo de grafo e heap, organização do código e interface | Thiago e Arthur | 1 |
| 7 | Funcionalidades e resultados | Uma subseção por feature, com tela, resultado e complexidade | Cada dono | 4 |
| 8 | Avaliação de desempenho | Complexidade teórica e tempos medidos de cada algoritmo; comparação com NetworkX se a etapa opcional acontecer | Rafael | 1 |
| 9 | Limitações e conclusão | O que o modelo não captura e o que fica para depois | Caio | 1 |
| 10 | Responsabilidades | Quem fez o quê, a partir da tabela-mestre e do `git log` | Rafael | 0,5 |
| | Referências | | Rafael | 0,5 |
| | **Total** | | | **14** |

O orçamento deixa uma página de folga até o limite de 15 e duas acima do mínimo de 12. Marcos: seções da Etapa 1 em v1 em 03/11; rascunho de todas as seções em 15/11; relatório completo em 19/11; versão final em 20/11.

### 14.2 README estruturado

O `README.md` segue a espinha da Etapa 1, de forma resumida, e termina com o uso:

1. O problema (Henrique).
2. Os dados (Miguel).
3. A modelagem e as visões do grafo, com o diagrama de classes (Henrique).
4. O plano de desenvolvimento: divisão e calendário (Henrique).
5. Instalar, ativar o hook, rodar a interface e rodar os testes (Caio).
6. Link para o `docs/GUIA.md` e para o vídeo.

### 14.3 Apresentação de 10 minutos

| Bloco | Quem | Tempo |
|---|---|---|
| Problema, dados e modelagem | Henrique | 1 min |
| Uma demonstração por feature: rota, espera, baldeações, centralidades, eficiência, falhas | Henrique, Miguel, Rafael, Thiago, Arthur, Caio | 6 × 1,2 min |
| Desempenho e limitações | Rafael | 1 min |
| **Total** | | **cerca de 9 min, com 1 min de folga** |

Todos falam, como o enunciado exige. Os slides derivam do relatório, e Arthur os monta até 19/11. As apresentações começam em 24/11; a ordem depende de P-03.

### 14.4 Vídeo de 12 a 18 minutos

| Bloco | Quem | Tempo |
|---|---|---|
| Abertura: problema, dados e organização da ferramenta | Miguel e Henrique | 1,5 min |
| Uma parte por aluno: as features dele funcionando e a explicação de como foram feitas | Cada dono | 6 × 2 a 2,5 min |
| Fechamento: desempenho e limitações | Rafael | 1 min |
| **Total** | | **14,5 a 17,5 min** |

O enunciado pede foco no funcionamento e nas features de cada aluno, por isso abertura e fechamento são curtos. Cada dono grava o seu trecho por captura de tela depois do congelamento, até 18/11, seguindo o roteiro do arquivo da feature. Caio monta o vídeo até 20/11, publica e distribui o link, que cada um envia no Canvas junto com o `.zip`.

## 15. Riscos e mitigações

| # | Risco | Chance | Impacto | Mitigação |
|---|---|---|---|---|
| 1 | Item obrigatório faltando zera a nota | Baixa | Crítico | Checklist da seção 2.1, com dono, conferida em cada fechamento; entrega interna em 21/11 |
| 2 | Um integrante não envia a cópia no Canvas | Média | Crítico para ele | Todos enviam em 21/11 e postam a confirmação; Caio confere os seis |
| 3 | Biblioteca de grafo entra em `src/`, por descuido ou por agente | Média | Crítico | Hook de pre-commit, regra no `AGENTS.md`, revisão do diff no PR, script rodado de novo em cada fechamento |
| 4 | Hook não ativado ou pulado com `--no-verify` | Média | Alto | Instrução no README; item no template de PR; revisor confere imports; conferência no fechamento |
| 5 | Calendário comprimido: fundação em 6 dias, com feriado | Alta | Alto | Contratos em 30/10, rede de teste em 31/10, gatilho de pareamento em 01/11; opcionais saem primeiro |
| 6 | Feed GTFS grande demais ou com defeito | Média | Alto | Conferência até 31/10; recorte; rede de teste e dataset reserva |
| 7 | Python lento nas métricas de todos os pares | Alta | Médio | Amostragem com erro medido; recorte |
| 8 | Semana de 16/11 tomada pelo TI5 | Alta | Alto | Código congela em 15/11; relatório, guia e vídeo escritos junto com cada feature |
| 9 | Trabalho concentrado em poucos | Média | Alto | Divisão vertical, commits próprios, quadro com dono |
| 10 | Integrante não sabe explicar o próprio código | Média | Alto | Regra "ninguém integra o que não sabe explicar"; explicação antes de gravar |
| 11 | Integrante não domina o resto do trabalho | Média | Alto | `docs/GUIA.md`, perguntas de verificação, explicação cruzada 2 com perguntas sorteadas, ensaios com perguntas cruzadas |
| 12 | Repositório público copiado por outro grupo, gerando suspeita de cópia | Média | Crítico | Commits próprios e datados provam a autoria; se houver indício de cópia, tornar o repositório privado e avisar o professor com o histórico |
| 13 | Relatório fora de 12 a 15 páginas | Média | Médio | Orçamento por seção; conferência em 15/11 e em 19/11 |
| 14 | `main` quebrada ou conflito de merge | Média | Médio | Branches curtas, `git pull --rebase`, pytest antes do PR, revisão obrigatória |
| 15 | Agente orienta errado porque o arquivo da feature está desatualizado | Média | Alto | Retomada reescrita ao fim de toda sessão; prompt de fechamento; item no template de PR |
| 16 | Frente C (caminho crítico) sobrecarregada: modelagem, Etapa 1, criação do repositório e F-ROTA | Média | Alto | Caio assume o P0-REPO logo após a criação; Thiago assume o construtor de G_P se houver atraso (seção 6.4); README de instalação fica com Caio |

## 16. Decisões tomadas e próximos passos

### 16.1 Decisões de 29/10

Esta tabela é o início do registro de decisões do `docs/GUIA.md`.

| Decisão | Por quê | Alternativa descartada |
|---|---|---|
| Método enxuto, sem plantão, ata, reunião semanal nem controle de mudança formal | Trabalho de 1 mês; o custo desses rituais só se paga em projetos longos | Manter o método do TI5 inteiro |
| Sem CI/CD e sem releases | Não há deploy nem versão publicada; a regra crítica fica no hook e na revisão | GitHub Actions com checks obrigatórios |
| Hook de pre-commit com verificação de imports e ruff | A regra que zera a nota não pode depender só de atenção | Só revisão humana |
| PR com 1 aprovação de outro integrante | Evita `main` quebrada e obriga uma segunda pessoa a entender cada código | Commit direto na `main` |
| Python 3.12 e Streamlit | Uma linguagem para todos, interface sem frontend separado | Java ou C++ com frontend à parte |
| Heap binário próprio, sem `heapq` | Elimina a dúvida sobre "estrutura pronta" no centro do Dijkstra, com custo baixo | Usar `heapq` |
| pandas só para ler CSV | Não cria nem processa grafo | Leitura manual dos CSV |
| GTFS da BHTrans | Rede real, com horários, conhecida pela banca | Dataset de metrô do Kaggle, muitas vezes sem horários |
| R = 300 m, 1,2 m/s, 4 faixas, sem penalidade por baldeação | Ver seção 3.4 | Valores ajustados depois, sem registro |
| NetworkX permitido em `tests/` para comparar resultados e em `benchmarks/` | Comparar resultado não é a ferramenta usando a biblioteca; o grupo assume essa interpretação do enunciado | Só gabarito à mão |
| Desempenho obrigatório: complexidade teórica e tempo medido; benchmark contra NetworkX opcional, só depois de tudo pronto | O enunciado pede complexidade e avaliação de desempenho; a comparação completa não cabe no prazo antes das features | Benchmark como item do DoD |
| Etapa 1 como seções do relatório e no README | Tudo é entregue junto; evita escrever o mesmo texto duas vezes | Documento separado |
| Vídeo por link no Canvas | Sem limite de tamanho de arquivo | Arquivo de vídeo no `.zip` |
| Repositório público | Decisão do grupo; o risco está na seção 15 | Privado até a entrega |
| Relatório editado no repositório | Commits individuais no relatório contam | Só Overleaf |
| `docs/GUIA.md` global e "Como funciona e por quê" e perguntas de verificação em cada feature | Todos precisam dominar o trabalho inteiro, inclusive o que foi feito com IA | Só documentação por feature |
| Congelamento em 15/11 | A semana de 16/11 é do TI5 | Congelar em 18/11 |
| Nomes: Thiago, Miguel, Henrique, Arthur, Caio e Rafael nas frentes A a F | Ver seção 6.2 | |
| Henrique fica com a frente C (modelagem e trajeto mais rápido), o caminho crítico | Pedido dele; a frente alimenta 5 das 6 features essenciais e concentra o que é avaliado na Etapa 1 | Henrique em dados e espera |
| Arquivo de feature com seção Retomada, reescrita ao fim de toda sessão | Qualquer agente novo precisa saber onde parou e o próximo passo sem reler o código | Só status por camada |
| Todos os arquivos de feature e as issues criados na abertura do repositório | Cada integrante clona, pergunta ao agente o que fazer e começa no mesmo dia | Cada dono cria os seus quando começar |

O grupo aprovou este plano em 29/10; todas as decisões desta tabela estão em vigor.

**Em aberto:** P-03, ordem da apresentação presencial; a data de início é 24/11 (Henrique confirma a ordem).

### 16.2 Próximos passos, na ordem

0. ~~**Antes de tudo:** o grupo dá o ok a este plano~~ **aprovado em 29/10.** Cada um informa o usuário GitHub e o e-mail do git.
1. **29/10:** Henrique cria o repositório público, convida os outros cinco e o professor e, com um agente, sobe a estrutura da seção 4.4, o `AGENTS.md` (com a tabela de integrantes), as fontes, os arquivos de todas as features e as issues do backlog atribuídas aos donos (seção 12.6).
2. **29/10 e 30/10:** Caio ativa a proteção da `main`, sobe o hook e o `verificar_imports.py`, monta o Kanban e escreve o README de instalação. Cada integrante clona, ativa o hook e pergunta ao agente o que fazer.
3. **30/10:** Thiago, Miguel e Arthur publicam os contratos com estado "planejado"; o `REQUISITOS.md` já está em baseline desde 29/10, sem revisão separada.
4. **31/10:** Miguel confirma o feed BHTrans; Rafael publica a função de medição; Caio abre o `docs/GUIA.md` com a seção 16.1 como registro de decisões.
5. **Quando sair:** Henrique confirma a ordem das apresentações (P-03) e atualiza a seção 2.3.

### 16.3 Checklist de adoção

- [ ] Repositório público com `AGENTS.md`, `CLAUDE.md`, hook e a estrutura da seção 4.4
- [ ] Proteção da `main` com 1 aprovação obrigatória
- [ ] Hook ativado por todos (`git config core.hooksPath .githooks`)
- [ ] `REQUISITOS.md`, `modelagem.md` e `plano-de-projeto.md`, cada um com versão e timeline
- [ ] `docs/GUIA.md` com o registro de decisões
- [x] RFs com ID e prioridade; baseline em 29/10
- [ ] Toda feature com arquivo, dono, retomada, status por camada, pendências e timeline
- [ ] Tabela de integrantes com usuário GitHub e e-mail no `AGENTS.md`
- [ ] Cada integrante testou "Leia o AGENTS.md e me diga o que eu preciso fazer agora." e recebeu a tarefa certa
- [ ] Todo RF em exatamente uma feature
- [ ] Contratos publicados com estado
- [ ] Definition of Done publicado e marcado em cada feature
- [ ] Issues do backlog com responsável, labels e milestone (seção 12.6)
- [ ] Checklist de entrega (seção 2.1) revisada em cada fechamento

## Apêndice A. Esqueleto do `AGENTS.md`

```markdown
# AGENTS.md · Análise de redes de transporte público (Trabalho de Grafos)

Contexto raiz para agentes e pessoas. Resume docs/fontes/plano-de-projeto.md e
docs/fontes/REQUISITOS.md. Em conflito, as fontes prevalecem.

## 0. Começando: "o que eu preciso fazer?"
| Letra | Integrante | Usuário GitHub | E-mail do git | Features (ordem) |
|---|---|---|---|---|
| A | Thiago | ... | ... | P0-GRAFO, F-MET, F-MET-2, F-MET-OPC |
| B | Miguel | ... | ... | P0-DADOS, F-ESPERA, F-ESPERA-2, F-ESPERA-OPC |
| C | Henrique | ... | ... | P0-MODELO, F-ROTA, F-ROTA-2, F-ROTA-OPC |
| D | Arthur | ... | ... | P0-UI, F-EFI, F-EFI-2, F-EFI-OPC |
| E | Caio | ... | ... | P0-REPO, F-RES, F-RES-2, F-RES-OPC |
| F | Rafael | ... | ... | P0-AVAL, F-BALD, F-BALD-2, F-BALD-OPC, F-AVAL, F-AVAL-OPC |

Quando alguém perguntar o que fazer:
1. Identifique a pessoa pelo `git config user.email` (ou pergunte o nome).
2. Na ordem acima, ache a primeira feature dela que não está "concluída" em
   docs/plano-de-desenvolvimento/features/feature-<ID>.md; se houver `gh`, liste também as issues abertas dela.
3. Leia a Retomada, o status e as dependências. Contrato de que ela depende ainda "planejado":
   avise e proponha o que dá para fazer contra a assinatura publicada.
4. Responda: feature ativa, próximo passo concreto, arquivos a ler, prazo (calendário em
   plano-de-projeto §7) e bloqueios. Só implemente depois que a pessoa confirmar.
5. Ao fim de toda sessão, reescreva a Retomada (plano-de-projeto §12.5, fechamento de sessão).

## 1. Fontes de verdade (docs/fontes/)
| Documento | Papel | Em conflito |
|---|---|---|
| REQUISITOS.md | O que a ferramenta faz | Sempre vence |
| modelagem.md | Como o problema vira grafo | Perde para REQUISITOS |
| plano-de-projeto.md | Como o grupo trabalha | Não se aplica |

Regra dura: nenhum agente altera docs/fontes/ por conta própria.
Explicações e registro de decisões: docs/GUIA.md.

## 2. A ferramenta em uma frase
## 3. Regra que zera a nota: nenhuma biblioteca de grafo em src/
   (NetworkX só em tests/, para comparar resultados, e em benchmarks/; heap próprio, sem heapq)
## 4. Estrutura do repositório e comandos (instalar, ativar o hook, rodar, testar, lint)
## 5. Regras para agentes (plano-de-projeto §12.3)
## 6. Fluxo da feature, Definition of Done e "Como funciona e por quê" (plano-de-projeto §8 e §11)
## 7. Git, hook e commits; agente não é autor nem coautor (plano-de-projeto §10)
```

## Apêndice B. Esqueleto do `docs/GUIA.md`

```markdown
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
| Data | Decisão | Por quê | Alternativas descartadas | O que afeta |

## 9. Glossário
Parada, padrão, plataforma, embarque, baldeação, intervalo, isócrona, intermediação, ...

## 10. Perguntas de verificação
Todas as perguntas das features, com resposta, agrupadas por seção.
```
