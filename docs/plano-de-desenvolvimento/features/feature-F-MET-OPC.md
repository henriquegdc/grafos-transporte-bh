# F-MET-OPC · Comunidades

**Período:** 2 · Desejáveis (12/11 a 15/11) · **Classe:** opcional
**Dono:** Thiago (@Thiagocs8); implementação em 20/11 por Henrique (plano.md, H2) · **Issue:** #22 · **Visões do grafo:** G_P
**Depende de:** F-MET · **Bloqueia:** nada
**Prazo:** 20/11 (reaberta pelo grupo)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-MET-06). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 20/11, Henrique (agente), item H2 do plano.md.
- **Onde parou:** código, testes, aba Comunidades na página Centralidades, script de medição, guia e seção do relatório prontos no PR `feat(F-MET-2, F-MET-OPC)`. O corte de 16/11 deixou de valer: em 20/11 o grupo decidiu fazer todas as features.
- **Próximo passo:** rodar a medição final no feed real com a CPU livre (comando em Resultados) e trocar o `\pendente{tempo}` de `relatorio/secoes/F-MET-OPC.tex`.
- **Arquivos tocados:** `src/transporte/algoritmos/comunidades.py` (novo), `src/transporte/interface/paginas/centralidades.py` (aba Comunidades), `tests/algoritmos/test_comunidades.py` (novo), `tests/interface/test_pagina_centralidades.py`, `benchmarks/medir_metricas_extensoes.py`, `docs/GUIA.md` (§5.4 e §10), `relatorio/secoes/F-MET-OPC.tex`.
- **Como testar:** `pytest tests/algoritmos/test_comunidades.py tests/interface/test_pagina_centralidades.py`; na interface, página Centralidades, aba Comunidades, Detectar comunidades.
- **Bloqueios:** nenhum; só a medição final, que espera a CPU livre.

## Objetivo
Comunidades. Fecha:

- **RF-MET-06** (O): Detectar comunidades por propagação de rótulos

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 20/11: `propagar_rotulos` e `modularidade` em `algoritmos/comunidades.py` |
| Modelo e dados | não aplicável | usa o G_P da P0-MODELO sem mudança |
| Interface | concluído | 20/11: aba Comunidades (número, modularidade, iterações, tabela das maiores, mapa por comunidade) |
| Testes | concluído | 20/11: cliques disjuntos e ligados por ponte, bordas, determinismo, modularidade com gabarito e contra `nx.community.modularity` em 15 grafos aleatórios; AppTest na rede de teste |
| Desempenho (tempo medido) | pendente | script pronto; medição final no feed real pendente (CPU ocupada por outros agentes em 20/11) |
| Guia (explicação e quiz) | concluído | 20/11: `docs/GUIA.md` §5.4 "Comunidades (F-MET-OPC)" e §10 |
| Relatório | em andamento | 20/11: `relatorio/secoes/F-MET-OPC.tex`; falta o tempo (`\pendente`) |
| Vídeo | concluído | roteiro de 30 s abaixo |

## Especificação
```python
# src/transporte/algoritmos/comunidades.py  (estado: implementado)
SEM_COMUNIDADE = -1
MAX_ITER_PADRAO = 100

@dataclass(frozen=True)
class Comunidades:
    rotulos: list[int]; quantidade: int; iteracoes: int; convergiu: bool; semente: int
    def tamanhos(self) -> list[int]

def vizinhanca_nao_dirigida(g: Grafo) -> list[list[int]]
def propagar_rotulos(g: Grafo, semente: int = 0, max_iter: int = MAX_ITER_PADRAO) -> Comunidades
def modularidade(g: Grafo, rotulos: Sequence[int]) -> float
```

Algoritmos (docs/fontes/modelagem.md §3.5):
- Propagação de rótulos (comunidades) · visão G_P · O(E) por iteração · Opcional

## Como funciona e por quê
**Problema.** Achar grupos de paradas mais ligadas entre si do que com o resto da rede, sem dizer
quantos grupos se quer.

**Visão G_P, não dirigida e sem pesos (decisão C1).** Comunidade é sobre quem está ligado a
quem; o sentido de uma linha (ida por uma rua, volta por outra) não muda a vizinhança, e a
propagação clássica é para grafo não dirigido. u e v são vizinhos se há aresta utilizável
u → v ou v → u; laços e paralelas contam uma vez. As listas de vizinhos são ordenadas para o
resultado não depender da ordem de inserção das arestas.

**Propagação de rótulos (Raghavan, Albert e Kumara, 2007).** Cada parada começa com o próprio
rótulo. Em cada iteração, numa ordem embaralhada com `random.Random(semente)`, a parada adota o
rótulo mais frequente entre as vizinhas, já vendo as mudanças desta iteração (assíncrona).
Para quando uma iteração inteira não muda nada (`convergiu`) ou em `max_iter` = 100. Os rótulos
finais são renumerados 0, 1, ... pela ordem do menor vértice de cada comunidade.

**Empate (decisão C2).** Se o rótulo atual está entre os mais frequentes, ele fica; senão vence o
menor rótulo. O plano dizia "empate pelo menor rótulo"; manter o atual é o critério de parada
do artigo e evita que uma parada troque sem parar entre dois rótulos empatados. Continua
determinístico: mesma semente, mesmo resultado.

**Exemplo.** Dois K5 ligados pela aresta 4 → 5. Cada ponta da ponte tem 4 vizinhas no próprio
clique e 1 no outro; depois que o clique se uniformiza, o rótulo dele tem 4 votos contra 1, e
nenhum rótulo atravessa: saem as duas comunidades {0..4} e {5..9}.

**Modularidade (decisão C3: implementação própria).** Q = Σ_c [L_c / m − (d_c / 2m)²], com m =
arestas não dirigidas distintas, L_c = arestas dentro de c, d_c = soma dos graus de c. Mede
quanto as ligações internas passam do esperado ao acaso; uma comunidade só dá 0. Implementada
para avaliar a partição sem biblioteca em `src/`; igual à do NetworkX (`weight=None`).
Exemplo: dois triângulos ligados por uma aresta, m = 7, Q = 2 (3/7 − (7/14)²) = 6/7 − 1/2.

**Complexidade.** Vizinhança O(V + E log E) (ordenação das listas), uma vez. Cada iteração
O(V + E): cada vértice conta os rótulos das vizinhas uma vez, com dicionário. Total
O(E log E + t (V + E)), t = iterações. Modularidade O(V + E log E). Espaço O(V + E).

**Página.** Aba "Comunidades" com a semente; mostra número de comunidades, modularidade,
iterações e tempo, a tabela das 10 maiores (tamanho, % e uma parada de exemplo) e um mapa só
com as paradas dessas 10, uma cor e uma camada por comunidade (desenhar as 9.660 paradas pesa
no navegador).

**Limitações.** Depende da semente; ignora o tempo das ligações (a caminhada pesa igual à
viagem); no feed real as comunidades saem pequenas.

## Perguntas de verificação
1. **Por que manter o rótulo atual no empate?** É o critério de parada do artigo; desempatar
   sempre pelo menor poderia oscilar e nunca parar.
2. **O que a modularidade mede?** Quanto as arestas internas passam da fração esperada ao acaso;
   0 com uma comunidade só.
3. **Por que o resultado depende da semente?** A ordem de visita decide quem adota primeiro; com
   a mesma semente, o resultado é sempre o mesmo.

## Critérios de aceite
- [x] RF-MET-06: Detectar comunidades por propagação de rótulos (20/11: `propagar_rotulos`, modularidade igual à do NetworkX, aba Comunidades)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (a modularidade; a partição da propagação não tem equivalente determinístico no NetworkX)
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [ ] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina (medição final pendente)
- [x] Página ou bloco na interface funcionando com o dataset real
- [ ] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/` (não feito)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação (sem figura; tempo pendente)
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

Grava `benchmarks/resultados/metricas-extensoes-<data>.json` (bloco `comunidades`: tempo da
propagação e da modularidade com `medir`, número de comunidades, iterações, modularidade nossa e
do NetworkX, 10 maiores e variação com 5 sementes).

Validação do script em 20/11 no feed real (`--repeticoes 1`, CPU ocupada; tempos **não** valem
e não foram copiados; JSON fora do Git). Os números abaixo são determinísticos dada a semente:
G_P com V = 9.660 e E = 122.799 (serviço de 18/11/2026); semente 2026: convergiu em 11
iterações, 604 comunidades, 3 unitárias, as 10 maiores com 141, 71, 67, 67, 63, 62, 62, 60, 59 e
55 paradas; modularidade 0,8062, igual à do `nx.community.modularity(..., weight=None)` para a
mesma partição. Sementes 2026 a 2030: 604, 602, 587, 608 e 607 comunidades; modularidade entre
0,8062 e 0,8151.

## Roteiro do vídeo (30 s)
1. (5 s) "Quais paradas formam grupos mais ligados entre si?"
2. (15 s) Página Centralidades, aba Comunidades, Detectar: número de comunidades, modularidade,
   tabela e mapa colorido.
3. (10 s) "Propagação de rótulos: cada parada adota o rótulo mais comum entre as vizinhas até nada
   mudar; a modularidade, nossa e conferida com o NetworkX, mede a qualidade."

## Pendências
- Medição final no feed real (comando em Resultados) e troca do `\pendente{tempo}` no relatório.
- Diagrama UML não feito.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Thiago.
### Corte 16/11/2026: feature opcional cortada pelo congelamento de 15/11.
### Reabertura 20/11/2026: o grupo decide fazer todas as features (plano.md); corte sem efeito.
### Implementação 20/11/2026: propagação de rótulos, modularidade, aba Comunidades, testes, guia e relatório (Henrique, H2).
