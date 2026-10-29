# AGENTS.md · Análise de redes de transporte público (Trabalho de Grafos)

Contexto raiz para agentes e pessoas. Resume `docs/fontes/plano-de-projeto.md` e
`docs/fontes/REQUISITOS.md`. Em conflito, as fontes prevalecem.

## 0. Começando: "o que eu preciso fazer?"

| Letra | Integrante | Usuário GitHub | Features, na ordem |
|---|---|---|---|
| A | Thiago | (a preencher) | P0-GRAFO, F-MET, F-MET-2, F-MET-OPC |
| B | Miguel | (a preencher) | P0-DADOS, F-ESPERA, F-ESPERA-2, F-ESPERA-OPC |
| C | Henrique | henriquegdc | P0-MODELO, F-ROTA, F-ROTA-2, F-ROTA-OPC |
| D | Arthur | (a preencher) | P0-UI, F-EFI, F-EFI-2, F-EFI-OPC |
| E | Caio | (a preencher) | P0-REPO, F-RES, F-RES-2, F-RES-OPC |
| F | Rafael | (a preencher) | P0-AVAL, F-BALD, F-BALD-2, F-BALD-OPC, F-AVAL, F-AVAL-OPC |

Quando alguém perguntar o que fazer:

1. Identifique a pessoa: pergunte o nome, ou use `gh api user --jq .login` se o `gh` estiver autenticado.
2. Na ordem da tabela, ache a primeira feature dela que não está "concluída" em
   `docs/plano-de-desenvolvimento/features/feature-<ID>.md`. Se houver `gh`, liste também
   `gh issue list --assignee @me`.
3. Leia a seção **Retomada**, o status e as dependências da feature. Se depende de um contrato
   ainda `estado: planejado`, avise e proponha o que dá para fazer contra a assinatura publicada.
4. Responda com: feature ativa, próximo passo concreto, arquivos a ler (pacote de contexto,
   plano-de-projeto §12.2), prazo (calendário em plano-de-projeto §7) e bloqueios.
5. Só implemente depois que a pessoa confirmar.
6. Ao fim de toda sessão, reescreva a Retomada e atualize status, pendências e timeline
   (plano-de-projeto §12.5, "Fechamento de sessão").

## 1. Fontes de verdade (`docs/fontes/`)

| Documento | Papel | Em conflito |
|---|---|---|
| `REQUISITOS.md` | O que a ferramenta faz | Sempre vence |
| `modelagem.md` | Como o problema vira grafo | Perde para REQUISITOS |
| `plano-de-projeto.md` | Como o grupo trabalha | Não se aplica |

Regra dura: nenhum agente altera `docs/fontes/` por conta própria; divergência vira pendência
no arquivo da feature. Explicações e registro de decisões: `docs/GUIA.md`.

## 2. A ferramenta em uma frase

Ferramenta em Python que lê o GTFS dos ônibus de Belo Horizonte, monta grafos com estrutura e
algoritmos próprios e responde seis perguntas: trajeto mais rápido, espera, baldeações,
centralidades, eficiência e falhas, com interface Streamlit.

## 3. Regra que zera a nota

Nenhuma biblioteca de grafo em `src/` (networkx, igraph, graph_tool, rustworkx,
scipy.sparse.csgraph, osmnx). NetworkX só em `tests/`, para comparar resultados, e em
`benchmarks/`. Fila de prioridade própria: não usar `heapq`. pandas só para ler CSV.

## 4. Estrutura e comandos

Estrutura: `docs/fontes/plano-de-projeto.md` §4.4. Dados brutos em `dados/brutos/` (fora do
Git); rede de teste em `dados/rede-teste/`.

Comandos (P0-REPO completa esta seção):

```text
pip install -r requirements.txt
git config core.hooksPath .githooks
pytest
ruff check
streamlit run src/transporte/interface/app.py
```

## 5. Regras para agentes (plano-de-projeto §12.3)

1. Toda sessão de implementação começa com o pacote de contexto (§12.2).
2. Ao fim de toda sessão: Retomada reescrita, status, pendências, decisões e timeline.
3. Não editar arquivo de feature que não é do dono da sessão.
4. Não alterar `docs/fontes/` por conta própria.
5. Não importar biblioteca de grafo em `src/`.
6. Nenhum número no relatório ou no guia que não tenha saído de execução real.
7. Pode rascunhar "Como funciona e por quê"; o dono revisa. Decisão sem porquê registrado vira
   pendência, não invenção.
8. Quem roda o agente revisa e commita; o agente não é autor nem coautor (sem trailers de
   atribuição).

## 6. Fluxo da feature

Arquivo da feature (plano-de-projeto §8) → contrato com `estado: planejado` (§9) → código e
testes → hook e pytest verdes → PR com 1 aprovação (§10) → Definition of Done (§11).

## 7. Git

Branch curta `feat/<ID>-<assunto>`; Conventional Commits com o ID como escopo
(`feat(F-ROTA): ...`); `git pull --rebase` antes de começar e antes de subir; PR referencia a
issue com `Closes #<n>`. Sem tags de versão.
