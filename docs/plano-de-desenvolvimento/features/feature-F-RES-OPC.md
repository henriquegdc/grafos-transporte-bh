# F-RES-OPC · Falhas múltiplas

**Período:** 2 · Desejáveis (12/11 a 15/11) · **Classe:** opcional
**Dono:** Caio (@CaioSResende); implementada por Henrique em 20/11 (plano de finalização, H5) · **Issue:** #24 · **Visões do grafo:** G_P
**Depende de:** F-RES, F-MET · **Bloqueia:** nada
**Prazo:** 20/11 (plano de finalização)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-RES-05). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 20/11/2026 (Henrique, com agente).
- **Onde parou:** código, testes, aba Falhas múltiplas, script de medição (o mesmo da F-RES-2), seção do relatório e guia prontos no PR da branch `feat/F-RES-2-ranking` (PR #63). Medição final no feed real feita em 20/11 e números no relatório e no guia.
- **Próximo passo:** aprovação do PR #63; tirar a figura do gráfico dirigida x aleatória no feed real e o diagrama UML.
- **Arquivos tocados:** `src/transporte/simulacao/falhas.py`, `src/transporte/interface/paginas/falhas.py`, `tests/simulacao/test_falhas_extensoes.py`, `tests/interface/test_pagina_falhas.py`, `benchmarks/medir_falhas_extensoes.py`, `relatorio/secoes/F-RES-OPC.tex`, `docs/GUIA.md`.
- **Como testar:** `pytest tests/simulacao/test_falhas_extensoes.py tests/interface/test_pagina_falhas.py`.
- **Bloqueios:** nenhum.

## Objetivo
Falhas múltiplas. Fecha:

- **RF-RES-05** (O): Simular falhas múltiplas e em sequência

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | concluído | 20/11: `simular_falhas`, `sequencia_dirigida`, `sequencia_aleatoria` |
| Modelo e dados | concluído | usa G_P e `indexar_linhas` da F-RES |
| Interface | concluído | 20/11: aba Falhas múltiplas, com `st.line_chart` e AppTest |
| Testes | concluído | 20/11: final igual a aplicar tudo de uma vez, desfazer restaura, linhas acumulam |
| Desempenho (tempo medido) | concluído | 20/11: `benchmarks/resultados/falhas-extensoes-2026-11-20.json` (Resultados) |
| Guia (explicação e quiz) | concluído | `docs/GUIA.md` §5.6 e §10, sem números do feed real |
| Relatório | parcial | `relatorio/secoes/F-RES-OPC.tex` com o resultado real de 20/11; falta a figura de tela |
| Vídeo | roteiro | roteiro de 30 s abaixo |

## Especificação
Em `src/transporte/simulacao/falhas.py` (`estado: implementado`):

```python
def simular_falhas(visao: VisaoGP, falhas: Sequence[Falha],
                   linhas_do_trecho: Mapping[Trecho, set[str]] | None = None,
                   amostra: int | None = None, semente: int = 0) -> list[ResultadoFalha]
def sequencia_dirigida(visao: VisaoGP, k: int, amostra_intermediacao: int | None = None,
                       semente: int = 0) -> list[Falha]
def sequencia_aleatoria(visao: VisaoGP, k: int, semente: int = 0) -> list[Falha]
```

Complexidade de `simular_falhas`: O((k + 1) s (V + E) log V + k (V + E + K)) para k passos,
s origens e K o tamanho do índice de linhas; espaço O(k V) pelas componentes de cada passo.

## Como funciona e por quê
Problema: medir a rede quando várias coisas falham, uma depois da outra, e comparar um
ataque dirigido com falhas ao acaso. Visão: G_P, como na F-RES.

1. **Linha de base** (componentes e eficiência com as s origens) medida uma vez.
2. **Passo k:** aplica a falha k por cima das anteriores, mede componentes e eficiência e
   compara com a base (efeito acumulado). O resultado do passo traz só o que ele desligou a
   mais em `vertices_desativados` e `arestas_desativadas`.
3. **Fim:** desfaz os passos na ordem inversa, inclusive com erro; só religa o que a
   sequência desligou, então o que já estava fora continua fora.

Decisões:
- **Linhas se acumulam.** `aplicar_falha` remove os trechos que só as linhas da falha usam.
  Se L1 e L2 compartilham B -> C, tirar L1 deixa o trecho e tirar L2 depois também deixaria,
  se cada passo olhasse só a própria linha. Cada passo aplica as suas paradas e trechos com
  todas as linhas que já falharam, então o estado final é igual ao de uma falha única com
  tudo junto (teste `test_final_igual_a_tudo_de_uma_vez` em 8 grafos aleatórios e
  `test_linhas_em_sequencia_igual_a_juntas`).
- **Dirigida estática.** A intermediação é calculada uma vez, na rede intacta; recalcular a
  cada remoção custaria k Brandes. Alternativa descartada por custo.
- **Gerador próprio na aleatória.** `random.Random(semente)` é o mesmo gerador que sorteia
  as origens da eficiência sobre a mesma lista de vértices: as k paradas removidas seriam as
  k primeiras origens. Um teste rápido no feed real (2 origens, 2 remoções) deu perda de
  100 % na aleatória por esse artefato; o sorteio agora usa
  `random.Random(f"sequencia_aleatoria:{semente}")`, determinístico e independente.

Exemplo à mão (`test_sequencia_gabarito_articulacao`): no triângulo A-B-C com C-D e D-E,
tirar D dá perda 25/43 e E sai da rede principal; tirar C depois deixa só A-B, perda
1 - 6/43.

Limitações: perda amostrada instável quando poucas paradas se desconectam (ver F-RES); a
dirigida não se adapta à rede já danificada.

## Perguntas de verificação
1. **Tirar L1 e depois L2 é igual a tirar as duas de uma vez?** Sim, as linhas se acumulam.
2. **Por que a perda nunca diminui ao longo da sequência?** Remover mais não encurta caminho
   e o denominador é o da rede intacta.
3. **Por que a aleatória não usa `random.Random(semente)`?** Porque sortearia as mesmas
   paradas que são origens da eficiência.

## Critérios de aceite
- [x] RF-RES-05: Simular falhas múltiplas e em sequência

## Definition of Done
- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação com o NetworkX: não aplicável (sem equivalente); consistência com `simular_falha`
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
- [x] Página ou bloco na interface funcionando (AppTest na rede de teste)
- [ ] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/`
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação (falta a figura de tela)
- [x] Roteiro do vídeo escrito no arquivo da feature
- [x] Arquivo da feature atualizado: retomada, status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas) | concluída 20/11 |
| 2 | Algoritmo com testes de corretude | concluída 20/11 |
| 3 | Integração com a visão do grafo e com os dados reais | concluída 20/11 (rede de teste; execução mínima no feed real) |
| 4 | Página na interface | concluída 20/11 |
| 5 | Tempo medido na rede real e complexidade justificada | concluída 20/11 |
| 6 | Como funciona e por quê, perguntas, diagrama UML, seção do relatório e roteiro do vídeo | parcial: falta diagrama e figura |

## Resultados para o relatório
Medição de 20/11/2026 (`benchmarks/resultados/falhas-extensoes-2026-11-20.json`), feed `dados/brutos/bhtrans.zip` com SHA-256 `8cb0a498b90b227221d0234e3b6386a7dfbe375a2cb2e52e86238010be05f6d6` (dia 2026-11-18, 9.660 paradas, 303 linhas), G_P com V = 9.660 e E = 122.799. Máquina: Windows 11 (10.0.26200), Intel64 Family 6 Model 183 Stepping 1, Python 3.12.10; `medir` com 1 repetição, máquina livre. Comando (raiz do repositório, `.venv` ativo, `PYTHONPATH=src`):

```text
python benchmarks/medir_falhas_extensoes.py dados/brutos/bhtrans.zip --paradas 10 --linhas 20 --amostra 30 --amostra-intermediacao 100 --k 10 --repeticoes 1
```

| Medida (30 origens, semente 2026) | Dirigida | Aleatória |
|---|---|---|
| Perda após 1 remoção | 0,139 % | 0,040 % |
| Perda após 5 remoções | 1,127 % | 0,086 % |
| Perda após 10 remoções | 1,734 % | 0,245 % |
| Paradas desconectadas | 0 em todos os passos | 0 em todos os passos |
| Componentes fortemente conexas | 4 em todos os passos | 4 em todos os passos |
| Tempo de `simular_falhas` (10 passos) | 13,729 s | 13,734 s |

## Roteiro do vídeo (30 s)
1. (5 s) "E se várias paradas falharem em sequência?" Aba Falhas múltiplas.
2. (10 s) Modo Dirigida x aleatória: escolher 10 paradas, ver o custo estimado e rodar.
3. (10 s) Gráfico: a curva dirigida cai mais rápido que a aleatória; explicar que as linhas
   se acumulam e que o estado final é igual a tirar tudo de uma vez.
4. (5 s) Limitação: a dirigida usa a intermediação da rede intacta, sem recalcular.

## Pendências
- Medição final no feed real: feita em 20/11 (Resultados).
- Figura do gráfico dirigida x aleatória para o relatório.
- Diagrama UML (atividade) em `docs/diagramas/`.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Caio.
### Implementação 20/11/2026: Henrique (plano de finalização, H5), com agente: núcleo, testes, aba Falhas múltiplas, script de medição, relatório e guia. Corrigido o viés da remoção aleatória (mesmo gerador das origens). 
### Medição 20/11/2026: medição final no feed real (Resultados); números no relatório e no guia.
