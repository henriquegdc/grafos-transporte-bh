# F-AVAL · Tabela de complexidade e tempos para o relatório

**Período:** 3 · Entrega (16/11 a 22/11) · **Classe:** prioritária
**Dono:** Rafael (@Rafael-Fonseca1510) · **Issue:** #25 · **Visões do grafo:** não se aplica
**Depende de:** tempos medidos de todas as features · **Bloqueia:** seção 8 do relatório
**Prazo:** 19/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-AVA-02). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 20/11/2026 (Henrique, com agente; a feature passou do Rafael para o Henrique na redistribuição de 20/11, `plano.md` §3).
- **Onde parou:** concluída. `benchmarks/consolidar.py` gera `relatorio/secoes/tabela-desempenho.tex`, incluída em `relatorio/secoes/avaliacao.tex` (Tabela "desempenho").
- **Próximo passo:** quando alguém regerar um JSON (por exemplo, F-EFI-2/OPC no feed de 18/11), rodar `python benchmarks/consolidar.py` de novo e recompilar o relatório.
- **Arquivos tocados:** `benchmarks/consolidar.py`, `relatorio/secoes/tabela-desempenho.tex`, `relatorio/secoes/avaliacao.tex`, `docs/GUIA.md` §7.
- **Como testar:** `python benchmarks/consolidar.py` (imprime o número de linhas) e compilar o relatório; a tabela não pode ter "não registrada" onde a feature registra a máquina.
- **Bloqueios:** nenhum.

## Objetivo
Tabela de complexidade e tempos para o relatório. Fecha:

- **RF-AVA-02** (E): Tabela consolidada com a complexidade teórica e o tempo medido de cada algoritmo, para o relatório

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | não aplicável | Não toca `src/` |
| Modelo e dados | concluído | 20/11: lê os JSON de `benchmarks/resultados/` e as medições só registradas nos arquivos de feature |
| Interface | não aplicável | A página Desempenho é da F-AVAL-OPC |
| Testes | não aplicável | Script de relatório; conferido rodando e compilando o PDF sem erro |
| Desempenho (tempo medido) | concluído | 29 linhas, 7 grupos de máquina e feed |
| Guia (explicação e quiz) | concluído | GUIA §7, "Tabela consolidada de desempenho (F-AVAL)" |
| Relatório | concluído | `avaliacao.tex` inclui `tabela-desempenho.tex`, sem `\pendente` |
| Vídeo | não aplicável | Coberto pela cena da F-AVAL-OPC |

## Especificação
Tabela com a complexidade teórica e o tempo medido de cada algoritmo, montada a partir da seção Resultados de cada arquivo de feature. Não toca `src/`.

## Como funciona e por quê
_A escrever a cada etapa concluída do plano de implementação, para um colega que não viu o código: o problema, a visão do grafo e por que ela, o algoritmo passo a passo com um exemplo pequeno, a complexidade com a justificativa, as decisões com as alternativas descartadas e as limitações._

## Perguntas de verificação
_3 a 5 perguntas que qualquer integrante deve saber responder, cada uma com a resposta curta._

## Critérios de aceite
- [x] RF-AVA-02: Tabela consolidada com a complexidade teórica e o tempo medido de cada algoritmo, para o relatório (20/11, `benchmarks/consolidar.py`)

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
_Todo número vem com o comando que o gerou._

**Tabela consolidada, 20/11/2026.** Comando, na raiz: `python benchmarks/consolidar.py` →
`relatorio/secoes/tabela-desempenho.tex` (29 linhas). Fontes: todos os JSON de
`benchmarks/resultados/` com extrator (`comparacao-networkx`, `metricas-extensoes`,
`nao-dominados`, `falhas-extensoes`, `centralidade`, `nucleo`, `espera`, `quadro-horarios-bhtrans`,
`sensibilidade`, `f-efi-2`, `f-efi-opc`) e, sem JSON versionado, a seção Resultados de F-ROTA,
F-ROTA-2, F-ROTA-OPC, F-BALD, F-BALD-2, F-EFI e F-RES (marcadas com † na tabela). Três linhas já
mostradas em outro ponto do relatório são omitidas (`OMITIDAS` no script) para caber em meia página.

Grupos de máquina e feed na tabela: i5-13600KF / feed de 18/11; Core 5 120U / feed de 11/11 (SHA
241f0bb2); i5-1235U / feed baixado em 11/11, serviço de 04/11; Ryzen 7 7730U / feed de 18/11;
Windows 11 10.0.26200 sem processador no JSON / feed de 18/11 (F-ESPERA-OPC). Na segunda rodada
de 20/11, F-ESPERA (`espera-2026-11-20.json`, no lugar do de 11/11), F-ESPERA-2, F-EFI-2 e
F-EFI-OPC foram regeradas no feed de 18/11 no i5-13600KF e saíram dos grupos do Apple M4; o JSON
do quadro de horários não grava o SHA, que vem de `SHA_NA_FEATURE` (registrado em
`feature-F-ESPERA-2.md`). O nome da máquina vem do processador do JSON casado com o registrado no arquivo da
feature (Model 183 = i5-13600KF; Model 186 = Core 5 120U). Ao conferir o JSON da F-RES-2, a linha
5034 isola uma parada (o arquivo da F-RES-2 e o GUIA diziam "nenhuma"); corrigido nos dois.

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

## Pendências
- Nenhuma.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Rafael.
### Redistribuição 20/11/2026: feature passou ao Henrique (`plano.md` §3).
### Concluída 20/11/2026: `benchmarks/consolidar.py`, tabela no relatório e subseção no GUIA §7.
