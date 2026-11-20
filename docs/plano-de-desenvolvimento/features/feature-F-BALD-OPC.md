# F-BALD-OPC · Trajetos não dominados

**Período:** 2 · Desejáveis (12/11 a 15/11) · **Classe:** opcional
**Dono:** Henrique (@henriquegdc), por redistribuição de 20/11 (antes Rafael) · **Issue:** #21 · **Visões do grafo:** G_E
**Depende de:** F-BALD-2 · **Bloqueia:** nada
**Prazo:** 20/11 (plano de finalização, item H3)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-BAL-04). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 20/11/2026.
- **Onde parou:** código, testes, página, script de medição, guia e relatório prontos. Falta só
  a medição final no feed real (não rodada para não disputar CPU com outras medições).
- **Próximo passo:** rodar, da raiz do repositório e com a máquina livre,
  `python benchmarks/medir_nao_dominados.py dados/brutos/bhtrans.zip` (200 pares, 3 repetições;
  grava `benchmarks/resultados/nao-dominados-<data>.json`). Copiar o tempo médio e o máximo
  por par para "Resultados" abaixo, para o `\pendente` de `relatorio/secoes/F-BALD-OPC.tex` e
  para o GUIA §5.3 (parágrafo "Complexidade" da F-BALD-OPC).
- **Arquivos tocados:** `src/transporte/algoritmos/comparacao_baldeacoes.py`,
  `src/transporte/interface/paginas/baldeacoes.py`,
  `tests/algoritmos/test_comparacao_baldeacoes.py`, `tests/interface/test_pagina_baldeacoes.py`,
  `benchmarks/medir_nao_dominados.py`, `relatorio/secoes/F-BALD-OPC.tex`, `docs/GUIA.md`.
- **Como testar:** `pytest tests/algoritmos/test_comparacao_baldeacoes.py tests/interface/test_pagina_baldeacoes.py`.
- **Bloqueios:** nenhum.

## Objetivo
Trajetos não dominados. Fecha:

- **RF-BAL-04** (O): Listar os trajetos não dominados em tempo e baldeações

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 20/11: `trajetos_nao_dominados` sobre `mais_rapido_com_limite` (F-BALD-2) |
| Modelo e dados | concluído | 20/11: usa o G_E da faixa com as esperas da F-ESPERA, sem modelo novo |
| Interface | concluído | 20/11: bloco "Trajetos não dominados" na página Baldeações (tabela e mapa do escolhido) |
| Testes | concluído | 20/11: gabaritos à mão, bordas, falhas e força bruta com NetworkX em 20 redes |
| Desempenho (tempo medido) | em andamento | script validado com 5 pares e 1 repetição; medição final pendente |
| Guia (explicação e quiz) | concluído | 20/11: GUIA §5.3 e §10 |
| Relatório | em andamento | `relatorio/secoes/F-BALD-OPC.tex`; falta o tempo no feed real (`\pendente`) |
| Vídeo | roteiro escrito | gravação no fechamento do grupo |

## Especificação
Assinatura pública (`estado: implementado`), em `transporte.algoritmos.comparacao_baldeacoes`:

```python
def trajetos_nao_dominados(ge: VisaoGE, origem: str, destino: str) -> list[Trajeto]
```

Lista em ordem crescente de baldeações e estritamente decrescente de tempo; o último tem o tempo
do `trajeto_mais_rapido`. Lista vazia se o destino não é alcançável; origem == destino devolve
um trajeto de tempo 0 sem trechos; parada inexistente levanta KeyError.

Na página (`interface/paginas/baldeacoes.py`): `tabela_fronteira(rede, fronteira)` e
`para_mapa(trajeto)` (Trajeto do G_E no formato que `mapa_trajeto` desenha, sem as esperas).

## Como funciona e por quê
**Problema.** A F-BALD-2 compara dois trajetos: o mais rápido e o mais rápido com o mínimo de
baldeações. Entre eles pode haver opções intermediárias (por exemplo, uma baldeação a menos que
o mais rápido custando só 3 minutos). RF-BAL-04 pede todas as que valem a pena: as **não
dominadas**, para as quais nenhum outro trajeto tem tempo menor ou igual e baldeações menores
ou iguais, sendo melhor em um dos dois.

**Visão.** G_E da faixa, o mesmo da F-ROTA e da F-BALD-2: é a visão que tem tempo, e a busca
com limite de baldeações já roda nela.

**Algoritmo.** (1) `trajeto_mais_rapido` dá o mais rápido, com B baldeações; nenhum trajeto com
mais de B entra, porque o mais rápido o domina. (2) Para k = 0, ..., B - 1,
`mais_rapido_com_limite(k)`; o resultado entra só se reduz o tempo do último que entrou. (3) Se
um resultado já tem o tempo do mais rápido, a lista para ali (empate fica com menos
baldeações); senão, o mais rápido fecha a lista.

Exemplo (teste `test_fronteira_com_tres_pontos`): de A a D, linha direta em 3.300 s (0
baldeação), Q1 + R3 em 1.360 s (1) e Q1 + Q2 + Q3 em 1.080 s (2). Os três entram.

**Por que é exatamente a fronteira.** T(k) = tempo mínimo com até k baldeações não cresce com
k. Um trajeto qualquer com b baldeações tem tempo >= T(b); o guardado da busca b (ou o último
guardado antes dela, se ela não reduziu o tempo) tem tempo T(b) e no máximo b baldeações:
domina ou empata. E os guardados têm baldeações crescentes e tempos estritamente
decrescentes, então nenhum domina outro.

**Decisões.**
- D1. Começar em k = 0, não no mínimo da G_L. No G_E as caminhadas se encadeiam (B3 da
  F-BALD) e pode haver trajeto com menos baldeações que o mínimo da G_L; começar nele perderia
  pontos. O custo extra são buscas com k abaixo do mínimo real, que devolvem None.
- D2. Reusar `mais_rapido_com_limite` em vez de um Dijkstra multicritério de uma passada (que
  daria todos os T(k) de uma vez). Alternativa descartada por prazo: a reutilização já está
  testada contra o NetworkX, e o custo extra é um fator B.
- D3. Tolerância de 1e-9 s para "reduz o tempo": somas de float por caminhos diferentes podem
  diferir no último bit; sem ela, um empate viraria dois pontos.
- D4. Assinatura só com o G_E (sem a G_L): a fronteira não depende do mínimo da G_L (D1).

**Complexidade.** B + 1 buscas. Tempo O((V + E) log V) da F-ROTA mais
sum_{k<B} O((k + 2)(V + E) log((k + 2) V)) = O(B² (V + E) log(B V)) no pior caso. Espaço da maior
busca, O((B + 1)(V + E)), mais os trechos dos até B + 1 trajetos.

**Limitações.** Um trajeto por ponto da fronteira (outros com o mesmo tempo e as mesmas
baldeações não aparecem); herda as da F-BALD-2 e da F-ROTA (espera média H/2, uma faixa, sem
horário de saída).

## Perguntas de verificação
1. **O que é um trajeto não dominado?** Um para o qual não existe outro com tempo e baldeações
   menores ou iguais, sendo melhor em pelo menos um.
2. **Por que basta testar k de 0 até as baldeações do mais rápido?** Acima disso o mais rápido
   domina tudo; e o mais rápido com limite k representa todos os trajetos com k baldeações.
3. **Por que não começar no mínimo da G_L?** Caminhadas encadeadas no G_E podem fazer menos
   baldeações que ele; perderíamos pontos.

## Critérios de aceite
- [x] RF-BAL-04: Listar os trajetos não dominados em tempo e baldeações (função, testes e
  bloco na página Baldeações)

## Definition of Done
- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação com força bruta do NetworkX
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [ ] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina (medição final pendente)
- [x] Página ou bloco na interface funcionando (AppTest na rede de teste; script validado no feed real)
- [ ] Diagrama UML da feature em `docs/diagramas/` (não feito; o fluxo é o da F-BALD-2 repetido para cada k)
- [x] "Como funciona e por quê" e perguntas de verificação escritas e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [x] Seção do relatório em `relatorio/secoes/F-BALD-OPC.tex` (falta o tempo medido)
- [x] Roteiro do vídeo escrito no arquivo da feature
- [x] Arquivo da feature atualizado: retomada, status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato | concluída (20/11) |
| 2 | Algoritmo com testes de corretude | concluída (20/11) |
| 3 | Integração com a visão do grafo e com os dados reais | concluída (20/11, validação com 5 pares) |
| 4 | Página na interface | concluída (20/11) |
| 5 | Tempo medido na rede real e complexidade justificada | complexidade feita; medição final pendente |
| 6 | Como funciona, perguntas, relatório e roteiro do vídeo | concluída (sem diagrama UML) |

## Resultados para o relatório
**Validação do script (20/11/2026, não é a medição final):**
`python benchmarks/medir_nao_dominados.py dados/brutos/bhtrans.zip --pares 5 --repeticoes 1`
(saída gravada fora do repositório). G_E do pico da manhã com V = 46.102 e E = 209.025; Windows
11, Intel64 Family 6 Model 183, Python 3.12.10. Nos 5 pares todos alcançáveis, fronteiras de
1, 3, 3, 3 e 4 pontos e 0 divergência entre o último ponto e o `trajeto_mais_rapido`. Maior
fronteira: paradas 14786076 -> 14789446, 0/1/2/3 baldeações em 130,3/109,3/105,9/105,7 min (os
pontos não dependem da carga da máquina; os tempos desta validação não valem como medição,
porque a CPU estava ocupada por outras medições). Os 5 primeiros pares são os mesmos da medição
final, que usa a mesma semente.

**Medição final: pendente.** Comando exato, da raiz do repositório:

```text
python benchmarks/medir_nao_dominados.py dados/brutos/bhtrans.zip
```

Grava `benchmarks/resultados/nao-dominados-<data>.json` com tempo por par (média, mediana, p95,
máximo), tamanho da fronteira, distribuição de B e divergências.

## Roteiro do vídeo (30 s)
1. (5 s) "Mais rápido ou menos baldeações? Não precisa escolher só entre os dois extremos."
2. (15 s) Página Baldeações, faixa pico da manhã, origem 14786076 e destino 14789446: a tabela
   "Trajetos não dominados" mostra 0, 1, 2 e 3 baldeações com o tempo caindo; trocar o
   trajeto no seletor e mostrar o mapa mudando.
3. (10 s) "Para cada k até as baldeações do mais rápido, rodamos o Dijkstra com limite de
   baldeações e guardamos só quem reduz o tempo: é exatamente a fronteira de Pareto, com
   custo O(B² (V + E) log(BV))."

## Pendências
- Medição final no feed real (comando acima) e o número no relatório e no guia.
- Diagrama UML (opcional pelo plano de finalização).

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Rafael.
### Redistribuição 20/11/2026: plano de finalização (item H3) passa a feature ao Henrique.
### Implementação 20/11/2026: função, testes (gabarito e força bruta), bloco na página, script de medição validado, guia e relatório.
