# P0-AVAL · Relatório SBC no repositório e medição de tempo

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Rafael (@Rafael-Fonseca1510) · **Issue:** #6 · **Visões do grafo:** não se aplica
**Depende de:** nada · **Bloqueia:** medição de tempo de todas as features; seções do relatório
**Prazo:** medição 01/11; relatório compilando 31/10; estrutura 03/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-AVA-01). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 05/11, Rafael, branch `feat/P0-AVAL-medicao-relatorio`.
- **Onde parou:** PR aberto e revisado. Código aprovado na revisão (24 testes verdes, ruff limpo); os pedidos do revisor foram atendidos: `plantuml-1.2026.9.jar` removido do Git e `*.jar` no `.gitignore`, `relatorio/figuras/.gitkeep` criado, este arquivo alinhado aos commits (o `atividade-medir.png` já está commitado desde `dc3a656`) e DoD corrigido (hook e tempo na rede real como "não aplicável", com o motivo). Falta a descrição do PR preenchida (com `Closes #6`) e o título em Conventional Commits.
- **Próximo passo:** commitar e subir as correções; trocar o título do PR para `feat(P0-AVAL): medir e estrutura do relatório SBC` e preencher a descrição com `Closes #6`; pedir nova revisão. O merge será por squash, para o jar não entrar no histórico da `main`. Depois do merge: avisar o grupo que `medir` está pronto, que o contrato ganhou `Medicao.formatar()` e onde cada um escreve no relatório (`relatorio/README.md`); começar a F-BALD.
- **Arquivos tocados:** `src/transporte/util/medicao.py`, `tests/util/test_medicao.py`, `relatorio/` (todo), `docs/diagramas/atividade-medir.puml` e `.png`, `docs/GUIA.md` (§7, §8 e §10), `.gitignore`, este arquivo.
- **Como testar:** `PYTHONPATH=src pytest tests/util` (no PowerShell: `$env:PYTHONPATH="src"; pytest tests/util`); `ruff check src tests`; relatório: `cd relatorio && latexmk` gera `relatorio/build/main.pdf`.
- **Bloqueios:** nenhum. O `pytest` ainda precisa de `PYTHONPATH=src` até o P0-REPO publicar a configuração do projeto (ver Pendências).

## Objetivo
Relatório SBC no repositório e medição de tempo. Fecha:

- **RF-AVA-01** (E): Função de medição de tempo (média e desvio de N execuções) usada por todas as features na rede real

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 03/11: `medir` e `Medicao` em `src/transporte/util/medicao.py`, `estado: implementado` |
| Modelo e dados | não aplicável | A medição não usa nenhuma visão do grafo nem o modelo normalizado |
| Interface | não aplicável | A página "Desempenho" é da F-AVAL-OPC (RF-AVA-05); `Medicao.formatar()` já serve para ela |
| Testes | concluído | 03/11: `tests/util/test_medicao.py`, 23 testes com gabarito à mão e relógio falso, mais 1 doctest |
| Desempenho (tempo medido) | concluído | 03/11: custo da própria medição e resolução do relógio medidos (ver Resultados); não há algoritmo de grafo para medir na rede real |
| Guia (explicação e quiz) | concluído | 03/11: `docs/GUIA.md` §7 e §10, mais 4 decisões em §8 |
| Relatório | em andamento | 03/11: estrutura SBC compilando (3 páginas), seções 8 (metodologia) e 10 em v1; tabela de tempos fica para a F-AVAL; resumo e abstract no P3 |
| Vídeo | concluído | Roteiro abaixo; o trecho entra na parte de avaliação do vídeo do Rafael |

## Especificação
Contrato de `docs/fontes/plano-de-projeto.md` §9, mantido sem mudança na assinatura e acrescido de `Medicao.formatar()`.

| Arquivo | Conteúdo público |
|---|---|
| `src/transporte/util/medicao.py` | `Medicao(media_s, desvio_s, repeticoes)`, dataclass imutável; `Medicao.formatar() -> str`; `medir(func, *args, repeticoes=5, **kwargs) -> Medicao` |
| `relatorio/` | `main.tex`, `secoes/<secao>.tex`, `secoes/<ID>.tex` por feature (incluído sozinho), `referencias.bib`, `figuras/`, template oficial SBC (`sbc-template.sty`, `sbc.bst`), `.latexmkrc`, `README.md` |

Uso por qualquer feature:

```python
from transporte.util.medicao import medir

m = medir(dijkstra, visao.grafo, origem, repeticoes=5)
print(m.formatar())        # formato: "<média> <unidade> ± <desvio> <unidade> (n=<N>)"
m.media_s, m.desvio_s      # em segundos, para a tabela da F-AVAL
```

Complexidade de `medir`: tempo O(N · T) mais O(N) para a média e o desvio, em que T é o tempo de uma execução de `func`; espaço O(N) para os N tempos. Justificativa: um laço de N chamadas, cada uma cronometrada por duas leituras O(1) do relógio, seguido de duas passadas sobre a lista de N tempos (soma e soma dos quadrados). `Medicao` e `formatar` são O(1).

## Como funciona e por quê

**O problema.** O enunciado pede avaliação de desempenho, e o DoD de toda feature pede o tempo medido na rede real. Se cada pessoa medisse do seu jeito, com `time.time()`, uma execução só, incluindo ou não a leitura do GTFS, os números da tabela da F-AVAL não seriam comparáveis entre si. Por isso existe uma função única, que todos usam do mesmo jeito.

**Como `medir` funciona, passo a passo.**
1. Valida `repeticoes`: precisa ser `int` (bool não vale) e ≥ 1. Se não for, levanta erro **antes** de rodar o algoritmo, para não gastar minutos numa medição inválida.
2. Repete N vezes: lê o relógio, chama `func(*args, **kwargs)`, lê o relógio de novo e guarda a diferença. Só a chamada fica entre as duas leituras; o resultado é descartado.
3. Calcula a média e o desvio padrão amostral, com divisor N − 1. Com N = 1, o desvio é 0.0.
4. Devolve uma `Medicao` imutável com `media_s`, `desvio_s` e `repeticoes`.

**Exemplo pequeno.** Se as três execuções levarem 1 s, 2 s e 3 s, a média é 2 s. Os desvios em relação à média são −1, 0 e 1, a soma dos quadrados é 2, e 2 / (3 − 1) = 1, logo o desvio é 1 s. É exatamente o primeiro teste de `tests/util/test_medicao.py`, que usa um relógio falso com essas durações.

**Decisões e alternativas descartadas.**
- **`time.perf_counter` e não `time.time`.** `perf_counter` é monotônico (não volta no tempo se o relógio do sistema for acertado) e tem a maior resolução disponível, 100 ns nesta máquina. `time.time` pode pular e, no Windows, tem resolução pior. `time.process_time` mede só CPU e ignora espera de E/S, que o usuário da ferramenta sente.
- **Desvio amostral (N − 1) e não populacional (N).** As N execuções são uma amostra de infinitas execuções possíveis; o divisor N − 1 corrige o viés da estimativa. Com N = 5 a diferença é de cerca de 12%, então importa.
- **N = 5 por padrão.** Dá uma estimativa de dispersão com custo baixo, mesmo para algoritmos de segundos na rede real. Quem mede algo de microssegundos deve subir N.
- **Sem aquecimento e sem descarte de outliers.** Mantém o contrato do §9 simples e o número honesto: a primeira execução, com cache frio, entra na conta e aumenta o desvio. Se alguma feature precisar disso, vira pendência e mudança de contrato avisada ao grupo.
- **O resultado de `func` é descartado.** Devolver o resultado misturaria duas responsabilidades e incentivaria medir e usar o resultado na mesma chamada. Quem precisa do resultado chama a função mais uma vez, fora da medição.
- **Relógio numa variável do módulo (`_relogio`).** Permite testar média e desvio com gabarito exato, trocando o relógio por um falso, sem depender da velocidade da máquina.
- **Relatório:** template oficial da SBC sem alteração, uma seção por arquivo (cada dono edita só o seu, sem conflito de merge) e seções de feature incluídas por `\InputIfFileExists`. Assim, ninguém precisa editar `main.tex` para encaixar a sua parte. `\pendente{...}` marca em cinza o que falta. A compilação vai para `relatorio/build/`, fora do Git.

**Limitações.** Mede tempo de parede (wall-clock): outros programas abertos, o modo de energia e o turbo do processador mudam o número, e por isso cada tempo vem com a máquina. Não mede memória. Para funções muito rápidas (µs), o custo da chamada e da leitura do relógio, de cerca de 0,08 µs aqui, pesa no resultado. A função também não isola o coletor de lixo do Python.

## Perguntas de verificação
1. **Por que `perf_counter` e não `time.time()`?** Porque é monotônico e tem a maior resolução; `time.time()` segue o relógio do sistema, que pode ser ajustado no meio da medição.
2. **Por que o desvio divide por N − 1?** Porque as N execuções são uma amostra; N − 1 corrige o viés do desvio estimado a partir da média da própria amostra.
3. **O que entra no tempo medido?** Só a chamada `func(*args, **kwargs)`. A leitura do GTFS e a construção do grafo ficam de fora, a menos que sejam elas a função passada.
4. **Como os testes conseguem um gabarito exato para algo que depende da máquina?** Trocam `medicao._relogio` por um relógio falso que devolve leituras conhecidas, por exemplo durações de 1, 2 e 3 s, que dão média 2 e desvio 1.
5. **Como uma feature entra no relatório?** Criando `relatorio/secoes/<ID>.tex` com `\subsection{...}`; o `funcionalidades.tex` a inclui sozinho.

## Critérios de aceite
- [x] RF-AVA-01: Função de medição de tempo (média e desvio de N execuções) usada por todas as features na rede real. A função está pronta e testada; o uso por cada feature é cobrado no DoD dela ("Tempo medido na rede real com `medir`").

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [ ] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde. Hook: não aplicável até o P0-REPO (o hook ainda não existe). No lugar dele, `ruff check src tests` está limpo e `pytest` está verde (24 testes, 03/11, confirmado pelo revisor no PR)
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação com o NetworkX: não aplicável (o NetworkX não tem medição de tempo); a comparação equivalente é contra `statistics.mean` e `statistics.stdev`
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido na rede real: não aplicável. A P0-AVAL não tem algoritmo de grafo para rodar na rede real; no lugar, foi medido o custo da própria medição e a resolução do relógio, com a máquina (ver Resultados)
- [x] Página ou bloco na interface: não aplicável (a página "Desempenho" é da F-AVAL-OPC, RF-AVA-05)
- [x] Diagrama UML da feature (atividade) em `docs/diagramas/`: `atividade-medir.puml` e `atividade-medir.png` (commit `dc3a656`)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [x] Seção do relatório: não há `relatorio/secoes/P0-AVAL.tex` porque a P0-AVAL é a própria estrutura do relatório; a metodologia de medição está em `relatorio/secoes/avaliacao.tex` (§8.1)
- [x] Roteiro do vídeo escrito no arquivo da feature
- [x] Arquivo da feature atualizado: retomada, status, pendências e timeline. A Retomada passa a "concluída" no merge

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | concluída em 03/11 (publicado já com `estado: implementado`, junto com os testes) |
| 2 | Algoritmo com testes de corretude | concluída em 03/11 |
| 3 | Integração com a visão do grafo e com os dados reais | não aplicável: a medição recebe qualquer função |
| 4 | Página na interface | não aplicável: a página é da F-AVAL-OPC |
| 5 | Tempo medido na rede real e complexidade justificada | concluída em 03/11 (custo da medição; complexidade na Especificação) |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | concluída em 03/11 (PNG do diagrama commitado em `dc3a656`) |
| 7 | Relatório SBC: template, `main.tex`, uma seção por arquivo, compilando | concluída em 03/11 (3 páginas, sem erro nem aviso) |

## Resultados para o relatório
Máquina: Intel Core i5-1235U (12ª geração, 12 threads), 15,7 GB de RAM, Windows 11 (10.0.26200), Python 3.12.10. Medido em 03/11/2026.

Comando (na raiz do repositório):

```text
PYTHONPATH=src python -c "import time; from transporte.util.medicao import medir; print('resolucao', time.get_clock_info('perf_counter').resolution); print('vazia', medir(lambda: None, repeticoes=1000).formatar()); print('sorted', medir(sorted, list(range(100_000, 0, -1)), repeticoes=10).formatar())"
```

Saída:

```text
resolucao 1e-07
vazia 0.083 µs ± 0.076 µs (n=1000)
sorted 855.140 µs ± 60.252 µs (n=10)
```

Leitura: a resolução do relógio é de 100 ns, e o custo fixo de uma medição (chamar uma função vazia e ler o relógio duas vezes) fica em torno de 0,08 µs. Isso é desprezível para qualquer algoritmo de grafo na rede real, que roda na escala de milissegundos ou mais. A linha do `sorted` serve só como controle: em três execuções da mesma medição, nesta sessão, a média variou entre 0,86 ms e 1,48 ms, o que mostra por que cada tempo precisa vir com média, desvio e máquina.

## Roteiro do vídeo (2 a 2,5 min)
Trecho de cerca de 30 s dentro da parte de avaliação de desempenho do vídeo do Rafael:
1. O problema: tempos medidos de jeitos diferentes não se comparam.
2. A função `medir` no código: N execuções, `perf_counter`, só a chamada dentro do cronômetro.
3. Média e desvio amostral com o exemplo 1, 2 e 3 s, e complexidade O(N · T).
4. Limitação: tempo de parede depende da máquina; por isso cada número vem com V, E e a máquina.

## Pendências
- **P0-REPO (Caio):** o projeto ainda não tem `requirements.txt` nem configuração do pytest; os testes rodam com `PYTHONPATH=src`. Sugestão: `pythonpath = ["src"]` em `[tool.pytest.ini_options]` no `pyproject.toml`, e `pytest` e `ruff` no `requirements.txt`. Avisar o Caio.
- **Relatório:** nomes completos, curso, instituição e e-mails dos seis em `relatorio/main.tex` (marcados com `\pendente`). Preciso dos dados com o grupo.
- **Relatório:** seções da Etapa 1 em v1 hoje (03/11), a cargo do Henrique, nos arquivos já criados em `relatorio/secoes/`.
- **Relatório:** a referência do feed GTFS da BHTrans (URL e data) entra em `relatorio/referencias.bib` pelo Miguel.
- **Contrato:** `Medicao.formatar()` foi acrescentado ao contrato do §9 (sem mudar a assinatura de `medir`). Avisar o grupo; não altera `docs/fontes/`. Lembrado também pelo revisor do PR.
- **PR:** título em Conventional Commits (`feat(P0-AVAL): medir e estrutura do relatório SBC`, vira a mensagem do squash) e descrição preenchida com `Closes #6`.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Rafael.
### Sessão 03/11/2026: medição e relatório.
`medir` e `Medicao` implementados com 23 testes (relógio falso para o gabarito) e publicados direto como `estado: implementado`, com atraso de dois dias sobre o prazo de 01/11. Acréscimo ao contrato: `Medicao.formatar()`. Relatório SBC montado com o template oficial (zip da SBC de 07/2024), uma seção por arquivo e seções de feature incluídas sozinhas; compila com `latexmk` em 3 páginas. Seções 8.1 (metodologia de medição) e 10 (responsabilidades) em v1. Guia §7 e §10 escritos e 4 decisões registradas em §8. Diagrama de atividade em `.puml`; PNG gerado e commitado em `dc3a656`.
### Sessão 05/11/2026: correções pedidas na revisão do PR.
O revisor aprovou o código (24 testes verdes, ruff limpo) e pediu: tirar do Git o `plantuml-1.2026.9.jar` (30 MB, ferramenta, não projeto), alinhar este arquivo aos commits (PNG do diagrama já commitado), não marcar no DoD o que não foi feito (hook e tempo na rede real), criar `relatorio/figuras/` no Git e preencher a descrição do PR com `Closes #6`. Feito: jar removido do índice e `*.jar` no `.gitignore` (o arquivo continua local para gerar diagramas), `relatorio/figuras/.gitkeep`, Retomada reescrita, DoD e pendências corrigidos. Integração combinada por squash merge, para o jar não ficar no histórico da `main`.
