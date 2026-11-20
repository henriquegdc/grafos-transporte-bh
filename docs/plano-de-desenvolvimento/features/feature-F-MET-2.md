# F-MET-2 · Proximidade e intermediação amostrada

**Período:** 2 · Desejáveis (12/11 a 15/11) · **Classe:** desejável
**Dono:** Thiago (@Thiagocs8); implementação em 20/11 por Henrique (plano.md, H1) · **Issue:** #16 · **Visões do grafo:** G_P
**Depende de:** F-MET · **Bloqueia:** nada
**Prazo:** 20/11 (reaberta pelo grupo)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-MET-04, RF-MET-05). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 20/11, Henrique (agente), item H1 do plano.md.
- **Onde parou:** código, testes, página, script de medição, guia e seção do relatório prontos no PR `feat(F-MET-2, F-MET-OPC)`. O corte de 16/11 deixou de valer: em 20/11 o grupo decidiu fazer todas as features. RF-MET-05 continua atendido pela F-MET (`estimar_intermediacao`).
- **Próximo passo:** rodar a medição final no feed real com a CPU livre (comando em Resultados), copiar os números para Resultados e trocar o `\pendente` de `relatorio/secoes/F-MET-2.tex`.
- **Arquivos tocados:** `src/transporte/algoritmos/centralidade.py` (`proximidade`), `src/transporte/interface/paginas/centralidades.py` (métrica Proximidade), `tests/algoritmos/test_centralidade.py`, `tests/interface/test_pagina_centralidades.py`, `benchmarks/medir_metricas_extensoes.py`, `docs/GUIA.md` (§5.4 e §10), `relatorio/secoes/F-MET-2.tex`.
- **Como testar:** `pytest tests/algoritmos/test_centralidade.py -k proximidade` e `pytest tests/interface/test_pagina_centralidades.py`; na interface, página Centralidades, métrica "Proximidade (Wasserman-Faust)", Calcular.
- **Bloqueios:** nenhum; só a medição final, que espera a CPU livre.

## Objetivo
Proximidade e intermediação amostrada. Fecha:

- **RF-MET-04** (D): Calcular a proximidade (closeness) de cada parada
- **RF-MET-05** (D): Calcular a intermediação por amostragem e medir o erro contra a exata

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 20/11: `proximidade` em `centralidade.py`; RF-MET-05 pela F-MET (`estimar_intermediacao`) |
| Modelo e dados | não aplicável | usa o G_P da P0-MODELO sem mudança |
| Interface | concluído | 20/11: métrica "Proximidade" na página Centralidades (ranking e mapa de calor), com o controle de origens sorteadas |
| Testes | concluído | 20/11: gabaritos à mão, bordas, amostragem e comparação com `nx.closeness_centrality` em 15 grafos aleatórios nos dois sentidos; AppTest na rede de teste |
| Desempenho (tempo medido) | pendente | script pronto; medição final no feed real pendente (CPU ocupada por outros agentes em 20/11) |
| Guia (explicação e quiz) | concluído | 20/11: `docs/GUIA.md` §5.4 "Proximidade (F-MET-2)" e §10 |
| Relatório | em andamento | 20/11: `relatorio/secoes/F-MET-2.tex`; falta o número do feed real (`\pendente`) |
| Vídeo | concluído | roteiro de 30 s abaixo |

## Especificação
```python
# src/transporte/algoritmos/centralidade.py  (estado: implementado)
SAIDA = "saida"; ENTRADA = "entrada"
def proximidade(g: Grafo, sentido: str = SAIDA, tamanho_amostra: int | None = None,
                semente: int = 0) -> list[float]
```

Algoritmos (docs/fontes/modelagem.md §3.5):
- Proximidade (closeness) · visão G_P · O(V (V + E) log V) exata; O(k (V + E) log V) com k origens
- Intermediação amostrada · visão G_P · O(s (V + E) log V) · na F-MET

## Como funciona e por quê
**Problema.** Quão perto, em tempo, cada parada está das outras: uma parada com proximidade alta
chega rápido a muitos lugares.

**Visão G_P**, como a F-MET: a pergunta é sobre a parada física, e o peso de G_P é o tempo.

**Fórmula (decisão P1: Wasserman e Faust).** G_P não é fortemente conexo, então a fórmula
clássica (N − 1) / D poria no topo uma parada que alcança só três vizinhas, todas perto. Com
r = paradas alcançadas a partir de v (sem contar v) e D = soma dos tempos até elas:
C(v) = (r / D) · (r / (N − 1)), 0 se r = 0 ou D = 0. N = vértices ativos (falhas da F-RES
contam). É o `closeness_centrality(wf_improved=True)` do NetworkX. Alternativa descartada: a
média harmônica (soma de 1/d), que também trata a desconexão mas não é a que o plano e o NetworkX
de referência usam.

**Sentido (decisão P2: saída).** A página usa a saída: tempos de v até as outras ("daqui chego
rápido à cidade?"). O NetworkX usa a entrada em grafo dirigido; a função aceita os dois. Um
Dijkstra a partir da origem s dá d(s, v) para todo v, que é a distância de *entrada* de v; para
a saída, os Dijkstras rodam em `g.reverso()`, onde d_rev(s, v) = d(v, s). Assim exato e amostrado
usam o mesmo laço.

**Amostragem (decisão P3).** O exato faz V Dijkstras (no G_P real, a mesma ordem do Brandes
exato, dezenas de minutos). Com k origens sorteadas (semente, RNF-07), r_k e D_k somam só as
origens da amostra. Como r / D não muda com o mesmo fator nos dois, a estimativa é
(r_k / D_k) · (r_k / k_v), k_v = origens sorteadas diferentes de v; com k = N, é a exata. Não
damos erro padrão: é uma razão (o estimador de razão tem viés pequeno), e o uso na página é
ordenar. A única origem de uma amostra com k = 1 fica com 0.

**Exemplo.** 0→1→2→4 e 0→3→2, pesos 1, N = 5. Saída: 0 alcança 1 e 3 (1), 2 (2), 4 (3): r = 4,
D = 7, C = 4/7. 1 alcança 2 (1) e 4 (2): (2/3)(2/4) = 1/3. 2 alcança 4: (1)(1/4). 4: 0.

**Complexidade.** Um Dijkstra com `HeapMin` por origem, O((V + E) log V), mais O(V) para somar
as distâncias: exata O(V (V + E) log V), amostrada O(k (V + E) log V); o reverso custa O(V + E).
Espaço O(V + E).

**Limitações.** Sem erro padrão na estimativa; G_P não tem espera nem horário, então é a
proximidade estrutural; peso 0 é aceito (diferente do Brandes).

## Perguntas de verificação
1. **Por que não (N − 1) / soma das distâncias?** G_P não é fortemente conexo; quem alcança
   poucas paradas, todas perto, ficaria no topo. Wasserman e Faust multiplica por r / (N − 1).
2. **Saída ou entrada, e qual o NetworkX usa?** A página usa saída; o NetworkX, entrada; a saída
   é a entrada no grafo reverso.
3. **Por que a estimativa não multiplica por N/k?** r / D é razão; o fator some.

## Critérios de aceite
- [x] RF-MET-04: Calcular a proximidade (closeness) de cada parada (20/11: `proximidade`, igual ao NetworkX nos testes; página Centralidades)
- [x] RF-MET-05: Calcular a intermediação por amostragem e medir o erro contra a exata (atendido pela F-MET: `estimar_intermediacao` e `benchmarks/medir_centralidade.py --exato`; resultados no arquivo da F-MET)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [ ] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina (medição final pendente)
- [x] Página ou bloco na interface funcionando com o dataset real
- [ ] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/` (não feito; o fluxo é o mesmo da F-MET)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação (sem figura; número do feed real pendente)
- [x] Roteiro do vídeo escrito no arquivo da feature
- [x] Arquivo da feature atualizado: retomada, status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | 20/11, direto como implementado |
| 2 | Algoritmo com testes de corretude | concluída 20/11 |
| 3 | Integração com a visão do grafo e com os dados reais | concluída 20/11 |
| 4 | Página na interface | concluída 20/11 |
| 5 | Tempo medido na rede real e complexidade justificada | complexidade feita; medição final pendente |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | feita, sem diagrama |

## Resultados para o relatório
**Medição final pendente** (a CPU estava ocupada por outros agentes em 20/11; os tempos sairiam
distorcidos). Comando a rodar na raiz do repositório, com o `.venv` ativo e a máquina livre:

```text
python benchmarks/medir_metricas_extensoes.py dados/brutos/bhtrans.zip --repeticoes 3
```

Grava `benchmarks/resultados/metricas-extensoes-<data>.json` (bloco `proximidade_amostrada`:
tempo com `medir` e top 5 para k = 25, 50, 100, 200). Opcional, se houver ~30 min: `--exato`
acrescenta a proximidade exata, a diferença máxima contra o NetworkX e a concordância do top 10
e do top 50 de cada amostra com o exato.

Validação do script em 20/11 no feed real (`--repeticoes 1`, CPU ocupada; tempos **não** valem
e não foram copiados; JSON fora do Git): G_P com V = 9.660 e E = 122.799; com k = 25, 50, 100
e 200 origens (semente 2026), as quatro primeiras são sempre as mesmas paradas da Avenida
Presidente Antônio Carlos (14791822, 14791788, 14791789, 14791783, nos números 561, 584, 583 e
582), e com k = 50 as cinco primeiras ficam nessa avenida. Esses resultados são determinísticos
dada a semente e se repetem na medição final.

Execução real já feita: testes `pytest tests/algoritmos/test_centralidade.py -k proximidade`
(20/11): proximidade igual à do NetworkX (`abs=1e-12`) em 15 grafos aleatórios com falhas, nos
dois sentidos, com e sem pesos 0.

## Roteiro do vídeo (30 s)
1. (5 s) "Proximidade: quão rápido saio desta parada para o resto da cidade."
2. (15 s) Página Centralidades, métrica Proximidade, 50 origens, Calcular: ranking e mapa de calor.
3. (10 s) "Um Dijkstra por origem; como a rede não é fortemente conexa, usamos Wasserman e Faust,
   que pune quem alcança só parte da rede. Conferido com o NetworkX."

## Pendências
- Medição final no feed real (comando em Resultados) e troca do `\pendente` no relatório.
- Diagrama UML não feito (fluxo igual ao da F-MET).

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Thiago.
### Corte 16/11/2026: feature cortada pelo congelamento de 15/11; RF-MET-05 entregue pela F-MET (amostragem com erro, RNF-06); RF-MET-04 (proximidade) não feito.
### Reabertura 20/11/2026: o grupo decide fazer todas as features (plano.md); corte sem efeito.
### Implementação 20/11/2026: `proximidade` (Wasserman e Faust, saída/entrada, amostragem), página, testes, guia e relatório (Henrique, H1).
