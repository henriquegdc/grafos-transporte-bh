# Plano de desenvolvimento · tabela-mestre e divisão

> Deriva de `docs/fontes/REQUISITOS.md`. Cada feature tem o seu arquivo em `docs/plano-de-desenvolvimento/features/`.
> A numeração das seções segue `docs/fontes/plano-de-projeto.md`, para que as referências cruzadas continuem válidas.

### 5.3 Tabela-mestre de features

| ID | Feature | Per. | Classe | RFs | Dono | Depende de |
|---|---|---|---|---|---|---|
| P0-REPO | Repositório, hook, `AGENTS.md`, README, Kanban, esqueleto do guia | 0 | fundação | RNF-01, 02, 07, 09 | Caio | nada |
| P0-GRAFO | Núcleo de grafos, heap e buscas | 0 | fundação | RF-GRF-01, 02, 03, 08 | Thiago | estrutura de P0-REPO |
| P0-DADOS | Leitura do GTFS, modelo normalizado, rede de teste | 0 | fundação | RF-DAD-01 a 04 | Miguel | estrutura de P0-REPO |
| P0-MODELO | Modelagem, UML, construtores de G_P e G_E | 0 | fundação | RF-GRF-04, 05, 07 | Henrique | contratos de P0-GRAFO e P0-DADOS |
| P0-UI | Aplicação Streamlit e componente de mapa | 0 | fundação | RF-UI-01 a 03 | Arthur | contrato de P0-DADOS |
| P0-AVAL | Relatório SBC no repositório e função de medição de tempo | 0 | fundação | RF-AVA-01 | Rafael | estrutura de P0-REPO |
| F-ROTA | Trajeto mais rápido | 1 | prioritária | RF-ROT-01, 02 | Henrique | P0-MODELO, P0-UI |
| F-ESPERA | Espera e simulação de trajeto | 1 | prioritária | RF-ESP-01 a 03 | Miguel | P0-DADOS, P0-MODELO |
| F-BALD | Menos baldeações | 1 | prioritária | RF-GRF-06, RF-BAL-01, 02 | Rafael | P0-DADOS, P0-GRAFO |
| F-MET | Centralidades | 1 | prioritária | RF-MET-01 a 03 | Thiago | G_P de P0-MODELO |
| F-EFI | Eficiência da rede | 1 | prioritária | RF-EFI-01, 02 | Arthur | P0-MODELO |
| F-RES | Falhas e resiliência | 1 | prioritária | RF-RES-01 a 03 | Caio | P0-GRAFO; eficiência de F-EFI |
| F-ROTA-2 | A* e origem e destino no mapa | 2 | desejável | RF-ROT-03, 04 | Henrique | F-ROTA |
| F-ESPERA-2 | Quadro de horários e Monte Carlo | 2 | desejável | RF-ESP-04, 05 | Miguel | F-ESPERA |
| F-BALD-2 | Menos baldeações contra mais rápido | 2 | desejável | RF-BAL-03 | Rafael | F-BALD, F-ROTA |
| F-MET-2 | Proximidade e intermediação amostrada | 2 | desejável | RF-MET-04, 05 | Thiago | F-MET |
| F-EFI-2 | Isócronas e índice de desvio | 2 | desejável | RF-EFI-03, 04 | Arthur | F-EFI |
| F-RES-2 | Ranking de criticidade | 2 | desejável | RF-RES-04 | Caio | F-RES |
| F-ROTA-OPC | Trajetos alternativos (Yen) | 2 | opcional | RF-ROT-05 | Henrique | F-ROTA |
| F-ESPERA-OPC | Sensibilidade ao intervalo | 2 | opcional | RF-ESP-06 | Miguel | F-ESPERA |
| F-BALD-OPC | Trajetos não dominados | 2 | opcional | RF-BAL-04 | Rafael | F-BALD-2 |
| F-MET-OPC | Comunidades | 2 | opcional | RF-MET-06 | Thiago | F-MET |
| F-EFI-OPC | Pico contra fora do pico | 2 | opcional | RF-EFI-05 | Arthur | F-EFI, F-ESPERA |
| F-RES-OPC | Falhas múltiplas | 2 | opcional | RF-RES-05 | Caio | F-RES |
| F-AVAL | Tabela de complexidade e tempos para o relatório | 3 | prioritária | RF-AVA-02 | Rafael | tempos medidos de todas as features |
| F-AVAL-OPC | Benchmark contra NetworkX, complexidade empírica e página Desempenho | opcional (16/11 a 18/11) | opcional | RF-DAD-05, RF-AVA-03 a 05 | Rafael | todas as essenciais e desejáveis prontas em 15/11 |

Duas exceções à regra "prioridade define o período", registradas de propósito: `F-AVAL` é prioritária mas fica no P3, porque só consolida em tabela os tempos que cada dono já mediu, sem tocar `src/`; `RF-GRF-07` é desejável mas fica na fundação, porque é parte do construtor (se não couber no P0, vai para o P2 sem bloquear nada).

### 5.4 Cobertura

Os 52 RFs estão em exatamente uma feature cada: 15 na fundação (P0), 16 nas seis essenciais (P1), 1 na consolidação da avaliação (P3), 10 nas desejáveis (P2) e 10 nas opcionais (6 no P2 e 4 na etapa opcional de benchmark). Por prioridade: 31 essenciais, 11 desejáveis e 10 opcionais. Nenhum RF fica sem período, e nenhum aparece em duas features.

## 6. Divisão entre as seis pessoas

### 6.1 Critérios

1. **Continuidade.** Quem faz a fundação de uma área fica com a feature que a estende; já conhece o código e os contratos.
2. **Produtor e consumidor com a mesma pessoa.** Quando uma peça só é usada por uma feature, as duas ficam com o mesmo dono.
3. **Integrador para o que é compartilhado.** Aplicação, relatório, guia, Etapa 1, API do grafo e entrega têm, cada um, uma pessoa que abre a estrutura. Os outros só encaixam a sua parte.
4. **Cada um com algo inteiro para mostrar.** Toda pessoa tem uma feature essencial com algoritmo e tela, para que commits, relatório e vídeo fiquem equilibrados.

### 6.2 Quem faz o quê

| Pessoa | P0 | P1 | P2 e depois | Integra | Seções do relatório | Trecho do vídeo |
|---|---|---|---|---|---|---|
| Thiago (A) | P0-GRAFO | F-MET | F-MET-2, F-MET-OPC | API do núcleo de grafo e heap | Fundamentação (com Henrique); Implementação: núcleo; Resultados: centralidades | Núcleo do grafo e centralidades |
| Miguel (B) | P0-DADOS | F-ESPERA | F-ESPERA-2, F-ESPERA-OPC | (nenhum: tem as features mais pesadas) | Dados; Resultados: espera | Dados e tempo de espera |
| Henrique (C) | P0-MODELO | F-ROTA | F-ROTA-2, F-ROTA-OPC | `modelagem.md` e as seções da Etapa 1 (relatório e README) | Introdução; Modelagem; Plano de desenvolvimento; Resultados: trajetos | Modelagem e trajeto mais rápido |
| Arthur (D) | P0-UI | F-EFI | F-EFI-2, F-EFI-OPC | Aplicação e slides | Implementação: interface; Resultados: eficiência | Interface e eficiência |
| Caio (E) | P0-REPO | F-RES | F-RES-2, F-RES-OPC | Repositório, hook, `docs/GUIA.md`, checklist de entrega, `.zip` e montagem do vídeo | Resultados: falhas; Limitações e conclusão | Falhas e resiliência |
| Rafael (F) | P0-AVAL | F-BALD | F-BALD-2, F-BALD-OPC; F-AVAL (P3); F-AVAL-OPC (se houver) | Relatório e figuras | Resultados: baldeações; Avaliação de desempenho; Responsabilidades | Baldeações e desempenho |

Por que esses pares:

- **Thiago:** o núcleo (heap, BFS e Dijkstra) é a base da intermediação de Brandes; quem fez o núcleo conhece o custo de cada operação.
- **Miguel:** a espera depende dos horários do GTFS; quem leu e limpou os horários sabe onde eles falham.
- **Henrique:** G_E nasce na modelagem; quem a desenhou implementa o roteamento sobre ela. A frente C é o caminho crítico do projeto: as visões G_P e G_E alimentam 5 das 6 features essenciais (F-ROTA, F-ESPERA, F-MET, F-EFI e F-RES), a modelagem com UML e a Etapa 1 são avaliadas diretamente, e o trajeto mais rápido é a pergunta central do tema. Henrique pediu para ficar com ela.
- **Arthur:** eficiência e isócronas são as features mais visuais; quem faz o componente de mapa sabe o que ele já desenha.
- **Caio:** falhas usam a desativação de vértices e arestas, e P0-REPO ficou leve sem CI, o que libera Caio para integrar o guia e montar a entrega e o vídeo.
- **Rafael:** G_L é usada só por F-BALD (produtor e consumidor juntos), e quem integra o relatório consolida a avaliação de desempenho.

### 6.3 O que cruza entre pessoas

| Contrato ou ponto de contato | Produtor | Consumidores | Assinatura publicada | Implementado até |
|---|---|---|---|---|
| API pública do núcleo de grafo e do heap | Thiago | Todos | 30/10 | 01/11 |
| Modelo normalizado de dados | Miguel | Henrique, Arthur, Rafael | 30/10 | 31/10 (rede de teste); 03/11 (feed real) |
| Contrato de página e componente de mapa | Arthur | Todos | 30/10 | 02/11 |
| Construtores de G_P e G_E | Henrique | Thiago, Miguel, Arthur, Caio | 31/10 | G_P em 02/11; G_E em 03/11 |
| Função de medição de tempo | Rafael | Todos | 31/10 | 01/11 |
| Estrutura do relatório e orçamento de páginas | Rafael | Todos | 31/10 | 03/11 |
| Esqueleto do `docs/GUIA.md` | Caio | Todos | 31/10 | 03/11 (com a fundação explicada) |
| Tabela de intervalos por linha e faixa horária (alimenta as arestas de embarque de G_E) | Miguel | Henrique | 04/11 | 06/11; antes disso, espera constante |
| Função de eficiência global | Arthur | Caio | 04/11 | 07/11; antes disso, F-RES usa componentes conexas |
| Função de trajeto mais rápido | Henrique | Rafael (F-BALD-2) | 04/11 | 08/11 |

**Telas compartilhadas.** Início: Arthur integra; os outros só acrescentam um cartão com link para a própria página.

**Mexer no código de outro dono.** Avisar no grupo antes, combinar com o dono e registrar na timeline do arquivo da feature: o que mudou, por quê e quais testes cobrem a mudança. O PR que toca o código de outro dono passa pela revisão dele.

### 6.4 Se o peso ficar torto

- Se Henrique atrasar no P0 (modelagem, UML e duas visões), Thiago assume o construtor de G_P depois de fechar o núcleo (alvo: 01/11).
- Se Miguel atrasar no P1, a simulação com quadro de horários continua com ele, e o Monte Carlo passa para Arthur.
- Quem ficar sem tarefa puxa a próxima feature na ordem de prioridade já definida, nunca escopo novo.
- Se um integrante sair do grupo, as features dele descem um nível, e as opcionais de todos saem primeiro.

## Timeline

### Criação 29/10/2026: gerado a partir do plano de desenvolvimento aprovado pelo grupo.
