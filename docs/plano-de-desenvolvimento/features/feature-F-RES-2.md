# F-RES-2 · Ranking de criticidade

**Período:** 2 · Desejáveis (12/11 a 15/11) · **Classe:** desejável
**Dono:** Caio (@CaioSResende); implementada por Henrique em 20/11 (plano de finalização, H4) · **Issue:** #18 · **Visões do grafo:** G_P
**Depende de:** F-RES, F-MET · **Bloqueia:** nada
**Prazo:** 20/11 (plano de finalização)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-RES-04). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 20/11/2026 (Henrique, com agente).
- **Onde parou:** código, testes, aba Ranking da página Falhas, script de medição, seção do relatório e guia prontos no PR da branch `feat/F-RES-2-ranking` (junto com a F-RES-OPC). **Falta a medição final no feed real.**
- **Próximo passo:** rodar a medição final (comando em Resultados), copiar o top 3 do ranking e o tempo para Resultados, `relatorio/secoes/F-RES-2.tex` (trocar o `\pendente`) e `docs/GUIA.md` §5.6; depois tirar a figura da aba Ranking.
- **Arquivos tocados:** `src/transporte/simulacao/falhas.py`, `src/transporte/interface/paginas/falhas.py`, `tests/simulacao/test_falhas_extensoes.py`, `tests/interface/test_pagina_falhas.py`, `benchmarks/medir_falhas_extensoes.py`, `relatorio/secoes/F-RES-2.tex`, `docs/GUIA.md`.
- **Como testar:** `pytest tests/simulacao/test_falhas_extensoes.py tests/interface/test_pagina_falhas.py`.
- **Bloqueios:** nenhum.

## Objetivo
Ranking de criticidade. Fecha:

- **RF-RES-04** (D): Ordenar paradas e linhas pela perda de eficiência que causam

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 20/11: `ranking_criticidade`, `candidatos_criticidade`, `paradas_mais_centrais` |
| Modelo e dados | concluído | usa G_P e `indexar_linhas` da F-RES |
| Interface | concluído | 20/11: aba Ranking da página Falhas, com AppTest |
| Testes | concluído | 20/11: gabarito à mão (articulação e ponte lideram), consistência com `simular_falha` |
| Desempenho (tempo medido) | pendente | script pronto e validado (rede de teste e feed real com parâmetros mínimos); medição final não rodada |
| Guia (explicação e quiz) | concluído | `docs/GUIA.md` §5.6 e §10, sem números do feed real |
| Relatório | parcial | `relatorio/secoes/F-RES-2.tex` com `\pendente` do resultado real |
| Vídeo | roteiro | roteiro de 30 s abaixo |

## Especificação
Em `src/transporte/simulacao/falhas.py` (`estado: implementado`):

```python
def paradas_mais_centrais(visao: VisaoGP, n: int, amostra_intermediacao: int | None = None,
                          semente: int = 0) -> list[str]
def candidatos_criticidade(visao: VisaoGP, n_paradas: int,
                           linhas_do_trecho: Mapping[Trecho, set[str]] | None = None,
                           n_linhas: int | None = None,
                           amostra_intermediacao: int | None = None,
                           semente: int = 0) -> list[Falha]
def ranking_criticidade(visao: VisaoGP, candidatos: Sequence[Falha],
                        linhas_do_trecho: Mapping[Trecho, set[str]] | None = None,
                        amostra: int | None = None, semente: int = 0) -> list[ResultadoFalha]
```

Complexidade: O((c + 1) s (V + E) log V + c (V + E)) para c candidatos e s origens, mais
O(k (V + E) log V) do Brandes amostrado com k origens na escolha das paradas.

## Como funciona e por quê
Problema: saber quais paradas e linhas mais pioram a rede se falharem. Visão: G_P, a mesma da
F-RES, em que parada é vértice e trecho é aresta, e a eficiência é estrutural.

1. **Candidatos.** Simular as V paradas custaria V simulações de s Dijkstras cada. As N
   paradas de maior intermediação (F-MET, Brandes amostrado) são as suspeitas naturais: por
   elas passam mais caminhos mínimos. As linhas são poucas (centenas), então entram todas,
   ou uma amostra sorteada com a semente quando o tempo não permite.
2. **Linha de base uma vez.** Componentes (Tarjan) e eficiência com as s origens são medidas
   antes do primeiro candidato. Chamar `simular_falha` c vezes refaria a eficiência de antes
   a cada vez: c + 1 eficiências em vez de 2c.
3. **Cada candidato sozinho.** Aplica a falha sobre a rede intacta, mede, desfaz. Mesmas
   origens e mesmo denominador para todos, então as perdas são comparáveis; cada perda é
   igual à de `simular_falha` com a mesma amostra e semente (testado).
4. **Ordem.** Perda decrescente; empate pelo número de paradas desconectadas e depois pela
   ordem de entrada.

Exemplo à mão (teste `test_ranking_gabarito_articulacao_lidera`): triângulo A-B-C, mais C-D
e D-E, tudo nos dois sentidos com 60 s. Soma de 1/d por par = 43/6 (em 1/min). Sem C sobram
A-B e D-E (perda 31/43); sem D, o triângulo (25/43); sem A ou B, 17/43; sem E, 13/43. O
ranking é C, D, A, B, E: as articulações lideram.

Decisões: intermediação como filtro (alternativa descartada: grau, que ignora se a parada
está em caminhos mínimos); linhas amostradas por sorteio, não pelas primeiras em ordem, para
não enviesar por id. Limitação: uma parada pouco central que desconecta um ramal pode ficar
fora dos candidatos; perdas amostradas de falhas que desconectam poucas paradas variam muito
com a amostra (ver F-RES).

## Perguntas de verificação
1. **Por que não simular todas as paradas?** V simulações de s Dijkstras cada; a
   intermediação escolhe as que concentram caminhos mínimos.
2. **Por que as mesmas origens para todos os candidatos?** Para a diferença entre perdas ser
   da falha, não da amostra.
3. **Quanto o ranking economiza em relação a c chamadas de `simular_falha`?** A eficiência de
   antes é medida uma vez: c + 1 eficiências em vez de 2c.

## Critérios de aceite
- [x] RF-RES-04: Ordenar paradas e linhas pela perda de eficiência que causam

## Definition of Done
- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação com o NetworkX: não aplicável (sem equivalente); consistência com `simular_falha`
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [ ] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
- [x] Página ou bloco na interface funcionando (AppTest na rede de teste)
- [ ] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/`
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação (falta o resultado real)
- [x] Roteiro do vídeo escrito no arquivo da feature
- [x] Arquivo da feature atualizado: retomada, status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas) | concluída 20/11 |
| 2 | Algoritmo com testes de corretude | concluída 20/11 |
| 3 | Integração com a visão do grafo e com os dados reais | concluída 20/11 (teste na rede de teste; execução mínima no feed real) |
| 4 | Página na interface | concluída 20/11 |
| 5 | Tempo medido na rede real e complexidade justificada | complexidade justificada; medição final pendente |
| 6 | Como funciona e por quê, perguntas, diagrama UML, seção do relatório e roteiro do vídeo | parcial: falta diagrama e número real |

## Resultados para o relatório
**Medição final pendente.** Comando (na raiz do repositório, com o `.venv` ativo e
`PYTHONPATH=src`; grava `benchmarks/resultados/falhas-extensoes-<data>.json`, que também
serve à F-RES-OPC):

```text
python benchmarks/medir_falhas_extensoes.py dados/brutos/bhtrans.zip --paradas 10 --linhas 20 --amostra 30 --amostra-intermediacao 100 --k 10 --repeticoes 1
```

Custo esperado: 31 eficiências de 30 Dijkstras no ranking e 22 nas curvas, cada uma rodada
duas vezes (resultado e `medir`), mais três Brandes amostrados; com cerca de 0,14 s por
Dijkstra, alguns minutos. Validação em 20/11: o script rodou na rede de teste e no feed real
com `--paradas 1 --linhas 1 --amostra 2 --amostra-intermediacao 2 --k 2`; esses números não
servem para o relatório (amostra de 2 origens).

## Roteiro do vídeo (30 s)
1. (5 s) "Quais falhas mais pioram a rede?" Página Falhas, aba Ranking.
2. (10 s) Mostrar N candidatos e o custo estimado antes de rodar; clicar em Calcular ranking.
3. (10 s) Tabela: a primeira linha é a falha mais crítica; explicar que todos usam as mesmas
   origens e que os candidatos vêm da intermediação. Custo (c + 1) s Dijkstras.
4. (5 s) Limitação: a intermediação é filtro; parada que corta um ramal pode ficar de fora.

## Pendências
- Medição final no feed real e números no relatório e no guia.
- Figura da aba Ranking para o relatório.
- Diagrama UML (atividade) em `docs/diagramas/`.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Caio.
### Implementação 20/11/2026: Henrique (plano de finalização, H4), com agente: núcleo, testes, aba Ranking, script de medição, relatório e guia. Medição final pendente.
