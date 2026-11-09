# P0-REPO · Repositório, hook, README de instalação e Kanban

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Caio (@CaioSResende) · **Issue:** #1 · **Visões do grafo:** não se aplica
**Depende de:** nada · **Bloqueia:** todas (hook e proteção da `main`)
**Prazo:** 30/10

> Fonte de verdade: docs/fontes/REQUISITOS.md (RNF-01, RNF-02, RNF-07, RNF-09). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 05/11/2026.
- **Onde parou:** hook, `scripts/verificar_imports.py` (com testes), `requirements.txt` com versões fixadas, `pyproject.toml` (pytest sem `PYTHONPATH`, ruff), `.gitattributes` (hook com LF) e README §5 prontos na branch `feat/P0-REPO-hook`. Falta o que só se faz no site do GitHub: proteção da `main` e Kanban.
- **Próximo passo:** abrir o PR com `Closes #1`; no GitHub, Settings > Branches: regra para `main` exigindo PR com 1 aprovação; criar o Kanban (Projects) com as issues. Avisar o grupo para rodar `pip install -r requirements.txt` e `git config core.hooksPath .githooks`.
- **Arquivos tocados:** `.githooks/pre-commit`, `.gitattributes`, `scripts/verificar_imports.py`, `tests/scripts/test_verificar_imports.py`, `requirements.txt`, `pyproject.toml`, `README.md`, `AGENTS.md` (§4).
- **Como testar:** `pytest` (231 testes em 05/11, 30 deles do script); `sh .githooks/pre-commit`; para ver o bloqueio, criar um `.py` em `src/` com `import networkx` e tentar commitar.
- **Bloqueios:** nenhum.

## Objetivo
Repositório, hook, README de instalação e Kanban. Fecha:

- **RNF-01** (E): Nenhum módulo em `src/` importa biblioteca de grafo (networkx, igraph, graph_tool, rustworkx, scipy.sparse.csgraph, osmnx)
- **RNF-02** (E): A `main` só recebe PR revisado e aprovado por outro integrante, com hook e pytest verdes
- **RNF-07** (E): Reprodutibilidade: versões fixadas, dataset com data e origem registradas, script de download, sementes fixas
- **RNF-09** (E): Toda feature tem "Como funciona e por quê" e perguntas de verificação incorporadas ao `docs/GUIA.md`

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 05/11: `scripts/verificar_imports.py` e `.githooks/pre-commit`; hook testado bloqueando `import networkx` em `src/` |
| Modelo e dados | não aplicável | Dataset e script de download são da P0-DADOS (parte do RNF-07) |
| Interface | não aplicável | |
| Testes | concluído | 05/11: `tests/scripts/test_verificar_imports.py`, 30 testes; suíte toda com 231 verdes |
| Desempenho (tempo medido) | não aplicável | |
| Guia (explicação e quiz) | em andamento | Rascunho de "Como funciona e por quê" e perguntas abaixo; falta revisão do Caio |
| Relatório | não iniciado | |
| Vídeo | não iniciado | |

## Especificação
Hook em `.githooks/pre-commit`, ativado com `git config core.hooksPath .githooks`. `requirements.txt` com versões fixadas (Python 3.12, streamlit, streamlit-folium, folium, pandas, pytest, ruff; networkx só para `tests/` e `benchmarks/`). Proteção da `main` com 1 aprovação. README de instalação (`docs/fontes/plano-de-projeto.md` §14.2, item 5).

## Como funciona e por quê
_Rascunho do agente em 05/11; o Caio revisa._

**O problema.** Importar biblioteca de grafo em `src/` zera a nota (RNF-01). A regra não pode depender só da atenção de quem revisa.

**O hook.** `.githooks/pre-commit` roda a cada `git commit`, depois que cada pessoa ativa com `git config core.hooksPath .githooks`. Usar `core.hooksPath` em vez de `.git/hooks/` deixa o hook versionado: todo mundo roda o mesmo arquivo. Ele roda duas coisas, e se qualquer uma falhar o commit não acontece:
1. `scripts/verificar_imports.py`: abre cada `.py` de `src/` com `ast.parse` (lê a árvore sintática, não executa o código) e percorre os nós `Import`, `ImportFrom` e as chamadas `importlib.import_module("x")` e `__import__("x")` com nome literal. Um nome é proibido se for igual a networkx, igraph, graph_tool, rustworkx, scipy.sparse.csgraph, osmnx ou heapq, ou um submódulo deles. `from scipy.sparse import csgraph` vira `scipy.sparse.csgraph` e também é pego.
2. `ruff check`, com `line-length = 100` e alvo Python 3.12 (`pyproject.toml`).

**Por que `ast` e não busca por texto.** Busca por texto pegaria `"import networkx"` dentro de string ou comentário e erraria `import os, heapq`. A `ast` vê só imports de verdade e devolve a linha certa.

**Decisões.**
- `heapq` entra na lista: a fila de prioridade tem que ser a própria (AGENTS.md §3). Isso vai além do texto do RNF-01, mas segue a regra do grupo.
- `scipy` e `scipy.sparse` sozinhos são permitidos; só o `csgraph` é proibido.
- O hook prefere o Python do `.venv`, para usar o ruff fixado no `requirements.txt`.
- `pyproject.toml` põe `src/` e `scripts/` no path do pytest, o que acaba com o `PYTHONPATH=src`.
- `.gitattributes` força LF no hook: com CRLF, o `sh` quebra no Windows.

**Limitações.** O hook pode ser pulado com `git commit --no-verify` ou não estar ativado. Por isso o revisor confere os imports no PR, e o Caio roda o script em cada fechamento de período (03/11, 11/11, 15/11). Import com nome montado em tempo de execução (`import_module("net" + "workx")`) não é pego; a revisão cobre esse caso.

## Perguntas de verificação
1. **O que acontece se eu commitar um arquivo em `src/` com `import networkx`?** O hook roda o `verificar_imports.py`, que mostra o arquivo e a linha, e o commit é bloqueado.
2. **Por que o script usa `ast` e não procura o texto "networkx"?** Para pegar só imports reais, inclusive vários na mesma linha, e não strings ou comentários.
3. **Posso usar NetworkX nos testes?** Sim, em `tests/` e `benchmarks/`, para comparar resultados. O script só olha `src/`.
4. **O hook garante sozinho a regra?** Não: dá para pular com `--no-verify`. A revisão do PR e a verificação nos fechamentos de período completam.
5. **Por que `heapq` é barrado se não é biblioteca de grafo?** Porque a fila de prioridade do Dijkstra tem que ser implementação própria.

## Critérios de aceite
- [x] RNF-01: Nenhum módulo em `src/` importa biblioteca de grafo (networkx, igraph, graph_tool, rustworkx, scipy.sparse.csgraph, osmnx)
- [ ] RNF-02: A `main` só recebe PR revisado e aprovado por outro integrante, com hook e pytest verdes
- [ ] RNF-07: Reprodutibilidade: versões fixadas, dataset com data e origem registradas, script de download, sementes fixas
- [ ] RNF-09: Toda feature tem "Como funciona e por quê" e perguntas de verificação incorporadas ao `docs/GUIA.md`

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

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
_Vazio até haver execução real. Todo número vem com o comando que o gerou._

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

## Pendências
- **Proteção da `main` (RNF-02):** configurar no GitHub (Settings > Branches) a exigência de PR com 1 aprovação. O `gh` não está instalado; é preciso fazer pelo site, e só o dono do repositório (Henrique) ou um admin consegue.
- **Kanban:** criar o GitHub Project com as issues do backlog.
- **RNF-07:** a parte da P0-REPO (versões fixadas) está feita. Dataset com data e origem e o script de download são da P0-DADOS (Miguel).
- **Python 3.12:** as versões do `requirements.txt` foram validadas num `.venv` com Python 3.14.4, a única versão nesta máquina. Todas declaram suporte ao 3.12 (`Requires-Python`), mas falta instalar num 3.12 real. O Thiago tem `.venv` 3.12.14 (P0-GRAFO).
- **Avisar o Rafael (P0-AVAL) e o Thiago (P0-GRAFO):** o `PYTHONPATH=src` não é mais necessário; podem tirar a pendência dos arquivos deles.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Caio.
### Hook 05/11/2026: `verificar_imports.py` com 30 testes, hook de pre-commit, `requirements.txt`, `pyproject.toml`, `.gitattributes` e README §5 na branch `feat/P0-REPO-hook`. Suíte com 231 testes verdes. Proteção da `main` e Kanban pendentes (site do GitHub).
