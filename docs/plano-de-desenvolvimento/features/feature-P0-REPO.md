# P0-REPO · Repositório, hook, README de instalação e Kanban

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Caio (@CaioSResende) · **Issue:** #1 · **Visões do grafo:** não se aplica
**Depende de:** nada · **Bloqueia:** todas (hook e proteção da `main`)
**Prazo:** 30/10

> Fonte de verdade: docs/fontes/REQUISITOS.md (RNF-01, RNF-02, RNF-07, RNF-09). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada

**Guia e relatório concluídos.** O hook, o leitor AST e as perguntas de revisão estão no guia §7 e §10 e na seção Implementação. O bit executável do hook passou a ser versionado para sistemas POSIX. Reproduza com `git config core.hooksPath .githooks`, `sh .githooks/pre-commit` e `python -m pytest`. O núcleo da P0-REPO foi aprovado por Henrique no [#43](https://github.com/henriquegdc/grafos-transporte-bh/pull/43). A configuração remota de proteção/Kanban e a sessão coletiva de explicação têm situação própria em Pendências.

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
| Guia (explicação e quiz) | concluído | Explicação, comando do hook e perguntas sobre seu escopo integrados ao guia. |
| Relatório | concluído | Parágrafo em `relatorio/secoes/implementacao.tex` distingue o hook e o pytest. |
| Vídeo | não iniciado | |

## Especificação
Hook em `.githooks/pre-commit`, ativado com `git config core.hooksPath .githooks`. `requirements.txt` com versões fixadas (Python 3.12, streamlit, streamlit-folium, folium, pandas, pytest, ruff; networkx só para `tests/` e `benchmarks/`). Proteção da `main` com 1 aprovação. README de instalação (`docs/fontes/plano-de-projeto.md` §14.2, item 5).

## Como funciona e por quê
Implementação conferida com o hook e o verificador de imports.

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
- [x] RNF-07: Reprodutibilidade: versões fixadas, dataset com data e origem registradas, script de download, sementes fixas
- [ ] RNF-09: Toda feature tem "Como funciona e por quê" e perguntas de verificação incorporadas ao `docs/GUIA.md`

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [x] Código do hook integrado pelo #43 com aprovação do Henrique.
- [x] Hook e pytest validados pela frente de fechamento documental.
- [x] Cobertura do verificador em `tests/scripts/test_verificar_imports.py`; sem algoritmo de grafo nesta feature.
- [ ] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [ ] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
- [ ] Página ou bloco na interface funcionando com o dataset real
- [ ] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/`
- [x] Explicação e quiz do hook integrados ao guia §7 e §10.
- [ ] O revisor do PR consegue explicar o que o código faz
- [x] Parágrafo do hook na seção Implementação. Sem resultado experimental de grafo nesta feature.
- [ ] Roteiro do vídeo escrito no arquivo da feature
- [x] Retomada, status e pendências atualizados.

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

- Em 20/11, a consulta pública ao endpoint GitHub `GET /repos/henriquegdc/grafos-transporte-bh/branches/main` retornou `protected: false`. O responsável pelo repositório deve conferir e aplicar a exigência de aprovação se ainda estiver desligada.
- Confirmar o link do quadro Kanban que reúne as issues. O backlog está nas issues do GitHub. A definição da organização do Project pertence ao grupo.
- Para o encerramento da issue ENT-GUIA, registrar a realização da explicação cruzada pelo grupo e incorporar eventuais lacunas apontadas.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Caio.
### Hook 05/11/2026: `verificar_imports.py` com 30 testes, hook de pre-commit, `requirements.txt`, `pyproject.toml`, `.gitattributes` e README §5 na branch `feat/P0-REPO-hook`. Suíte com 231 testes verdes. Proteção da `main` e Kanban pendentes (site do GitHub).
### Merge 06/11/2026: PR #43 integrado na `main` (`c3da48a`).
### Fechamento 10/11/2026: `verificar_imports.py` rodado na `main` (`fbb330d`), sem import proibido. Proteção da `main` e Kanban seguem pendentes.
### Fechamento 15/11/2026 (feito em 16/11): na `main` (`cbb1f90`), nenhum import proibido, ruff limpo, pytest com 667 verdes e 1 falha por timeout. Alerta ao grupo sobre as páginas que faltam na interface (ver Pendências).
### Guia 17/11/2026: lacunas do `docs/GUIA.md` listadas por dono (ver Pendências); prazo 18/11.

### Fechamento documental de 20/11/2026
O guia passa a descrever o hook e o relatório explica sua execução. Conferidas as lacunas do guia e a proteção pública da branch principal.
