# F-MET · Centralidades

**Período:** 1 · Essenciais (04/11 a 11/11) · **Classe:** prioritária
**Dono:** Thiago (@Thiagocs8) · **Issue:** #10 · **Visões do grafo:** G_P
**Depende de:** G_P de P0-MODELO · **Bloqueia:** F-MET-2
**Prazo:** 11/11 (checkpoint 07/11)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-MET-01, RF-MET-02, RF-MET-03). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 05/11, Thiago, branch `feat/F-MET-centralidades`.
- **Onde parou:** etapa 1 concluída (contrato); etapa 2 concluída: `graus`, `distribuicao_graus`, `intermediacao` (Brandes com e sem pesos) e `ranking` implementados (`estado: implementado`), com 190 testes verdes (gabarito à mão e comparação com o NetworkX). Decisões M1 a M4 aceitas pelo Thiago em 05/11.
- **Próximo passo:** subir a branch e abrir o PR (Refs #10, porque RF-MET-03 ainda depende da interface); pedir ao Henrique o piso de 1 s no G_P (pendência M2). Depois: etapa 3 (rodar sobre o G_P da rede de teste quando `construir_gp` existir), etapa 4 (página com ranking e mapa de calor, quando o P0-UI publicar o contrato de página e o mapa), etapa 5 (tempo com `medir` na rede real) e etapa 6.
- **Arquivos tocados:** `src/transporte/algoritmos/centralidade.py`, `tests/algoritmos/test_centralidade.py`, este arquivo.
- **Como testar:** `PYTHONPATH=src .venv/Scripts/python -m pytest tests/algoritmos` (190 testes em 05/11); `ruff check src tests`.
- **Bloqueios:** o algoritmo não depende de ninguém, porque roda sobre o `Grafo` genérico. A etapa 3 (G_P real) depende de P0-MODELO e P0-DADOS; a etapa 4 (página e mapa de calor) depende do contrato de página e do componente de mapa de P0-UI.

## Objetivo
Centralidades. Fecha:

- **RF-MET-01** (E): Calcular o grau de entrada e de saída de cada parada e a distribuição de graus
- **RF-MET-02** (E): Calcular a intermediação (Brandes) de cada parada
- **RF-MET-03** (E): Mostrar o ranking das paradas mais centrais e um mapa de calor

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 05/11: graus, distribuição, Brandes (com e sem pesos, normalização opcional) e ranking implementados |
| Modelo e dados | não iniciado | |
| Interface | não iniciado | |
| Testes | concluído | 05/11: 190 verdes; gabarito à mão, casos de borda (paralelas, laços, peso 0, desativação, grafos triviais) e comparação com o NetworkX (graus, graus por tipo, intermediação com e sem pesos, normalizada ou não) em grafos aleatórios com falhas; teste de mutação: sem a contagem de caminhos empatados, 32 testes falham |
| Desempenho (tempo medido) | não iniciado | |
| Guia (explicação e quiz) | não iniciado | |
| Relatório | não iniciado | |
| Vídeo | não iniciado | |

## Especificação
Contrato em `src/transporte/algoritmos/centralidade.py` (estado: planejado em 05/11):

```python
@dataclass
class Graus:
    entrada: list[int]
    saida: list[int]

def graus(g: Grafo, tipos: Collection[str] | None = None) -> Graus: ...                 # O(V + E)
def distribuicao_graus(g: Grafo, valores: list[int]) -> dict[int, int]: ...             # O(V + D log D)
def intermediacao(g: Grafo, ponderado: bool = True, normalizar: bool = False) -> list[float]: ...
    # ponderado O(V (V + E) log V); sem pesos O(V (V + E)); espaço O(V + E)
def ranking(g: Grafo, valores: list[float], k: int) -> list[tuple[int, float]]: ...     # O(V log V)
```

Todas respeitam vértices e arestas desativados (usam só `Grafo.vizinhos`), o que permite à F-RES recalcular centralidades após uma falha.

Algoritmos previstos (docs/fontes/modelagem.md §3.5):
- Brandes (intermediação) · visão G_P · O(V (V + E) log V) · Ponderado; O(VE) sem pesos

## Como funciona e por quê
_A escrever a cada etapa concluída do plano de implementação, para um colega que não viu o código: o problema, a visão do grafo e por que ela, o algoritmo passo a passo com um exemplo pequeno, a complexidade com a justificativa, as decisões com as alternativas descartadas e as limitações._

## Perguntas de verificação
_3 a 5 perguntas que qualquer integrante deve saber responder, cada uma com a resposta curta._

## Critérios de aceite
- [x] RF-MET-01: Calcular o grau de entrada e de saída de cada parada e a distribuição de graus (`graus`, `distribuicao_graus`; comparação com o NetworkX)
- [x] RF-MET-02: Calcular a intermediação (Brandes) de cada parada (`intermediacao`; comparação com o NetworkX com e sem pesos)
- [ ] RF-MET-03: Mostrar o ranking das paradas mais centrais e um mapa de calor (cálculo pronto em `ranking`; falta a página e o mapa de calor, que dependem do P0-UI)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [ ] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (190 testes em 05/11)
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
| 1 | Contrato (assinaturas com estado "planejado") | concluída em 05/11 |
| 2 | Algoritmo com testes de corretude | concluída em 05/11 |
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
- **Peso 0 no G_P (Henrique, P0-MODELO):** o GTFS arredonda horários, então duas paradas seguidas podem ter tempo mediano 0 s; a caminhada entre paradas no mesmo ponto também daria 0. Pela decisão M2, `intermediacao(ponderado=True)` recusa peso 0. Combinar com o Henrique um piso no construtor (ex.: 1 s), ou escolher outra opção de M2.
- **Página e mapa de calor (RF-MET-03):** dependem do contrato de página (`render`) e do componente de mapa de P0-UI (Arthur), ainda não publicados. O ranking já sai de `ranking()`; falta a exibição.

### ~~Decisões a tomar~~ Decididas em 05/11/2026: M1 a M4 aceitas pelo Thiago pela recomendação

- **M1. O que o grau conta.** (a) arestas utilizáveis, com paralelas contando uma vez cada e laço contando 1 na entrada e 1 na saída, mais um filtro opcional `tipos`; (b) vizinhos distintos. **Recomendo (a):** é a definição usual de grau em multigrafo dirigido (a mesma do NetworkX, o que permite comparar). O filtro `tipos={"viagem"}` resolve o caso em que a caminhada infla o grau de paradas vizinhas.
- **M2. Peso 0 na intermediação ponderada.** O Brandes conta caminhos mínimos processando os vértices em ordem de distância; com aresta de peso 0, dois vértices empatam na distância e a ordem pode sair errada (e um ciclo de peso 0 dá infinitos caminhos mínimos). Opções: (a) recusar peso 0 com ValueError e pedir ao construtor do G_P um piso de 1 s; (b) desempatar pelo número de arestas (distância lexicográfica), o que muda a definição e deixa de bater com o NetworkX quando há empates de tempo; (c) somar um ε aos pesos 0 dentro do Brandes. **Recomendo (a):** mantém o Brandes clássico e comparável ao NetworkX, e 0 s entre duas paradas distintas é artefato de arredondamento, não tempo real.
- **M3. Caminhos como sequência de vértices.** Na intermediação, arestas paralelas viram uma só, com o menor peso, e laços são ignorados. **Recomendo aceitar:** no G_P, uma aresta de viagem e uma de caminhada entre o mesmo par são a mesma ligação entre paradas; contar as duas como caminhos distintos daria peso extra a esse par. É também o que o NetworkX faz em multigrafos.
- **M4. Normalização opcional.** `normalizar=True` divide por (n - 1)(n - 2), n = paradas ativas, o máximo num grafo dirigido. **Recomendo deixar desligada por padrão e ligar na interface:** o valor bruto ("em quantos caminhos mínimos a parada aparece") é mais fácil de explicar, e o normalizado permite comparar a rede antes e depois de uma falha (F-RES), quando n muda.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Thiago.
### Sessão 05/11/2026: branch `feat/F-MET-centralidades`; contrato de `centralidade.py` publicado com estado: planejado; decisões M1 a M4 propostas.
### Decisão 05/11/2026: M1 a M4 aceitas pela recomendação.
### Sessão 05/11/2026: etapa 2, graus, distribuição, Brandes e ranking implementados com 190 testes verdes; RF-MET-01 e RF-MET-02 atendidos.
