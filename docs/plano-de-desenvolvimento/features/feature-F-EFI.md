# F-EFI · Eficiência da rede

**Período:** 1 · Essenciais (04/11 a 11/11) · **Classe:** prioritária
**Dono:** Arthur (@ArthurkkLS) · **Issue:** #11 · **Visões do grafo:** G_E ou G_P
**Depende de:** P0-MODELO · **Bloqueia:** F-RES (função de eficiência até 07/11), F-EFI-2
**Prazo:** 11/11 (checkpoint 07/11)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-EFI-01, RF-EFI-02). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 15/11/2026, Arthur.
- **Onde parou:** núcleo, página, testes e documentação implementados. A suíte completa passou (660 testes, Python 3.14.4); Ruff, verificador de imports, hook manual, formatação dos arquivos F-EFI e `git diff --check` também passaram. A API `eficiencia_global(g, origens=None, n_referencia=None)` preserva a matemática da eficiência provisória da F-RES. Faltam medição e validação no feed real, revisão cruzada e fechamento dos itens de entrega que dependem de artefatos/resultados reais.
- **Próximo passo:** quando `dados/brutos/` estiver disponível, medir a rede real com `medir` e validar a página; combinar com Caio a substituição da implementação provisória da F-RES e com o grupo a atualização da espera de G_E.
- **Arquivos tocados:** `src/transporte/algoritmos/eficiencia.py`, `src/transporte/interface/paginas/eficiencia.py`, `tests/algoritmos/test_eficiencia.py`, `tests/interface/test_pagina_eficiencia.py`, `docs/GUIA.md`, `docs/diagramas/sequencia-eficiencia.puml`, `relatorio/secoes/F-EFI.tex` e este arquivo.
- **Como testar:** `python -m pytest tests/algoritmos/test_eficiencia.py tests/interface/test_pagina_eficiencia.py -q`; `python -m pytest -q`; `ruff check`; format check dos quatro arquivos F-EFI; `python scripts/verificar_imports.py`; `.githooks/pre-commit`; `git diff --check`. A suíte completa e as verificações aplicáveis foram executadas nesta sessão; o format check de diretórios amplos ainda encontra arquivos antigos fora do escopo.
- **Bloqueios:** `dados/brutos/` não está disponível, então a medição de desempenho e validação de interface na rede real não podem ser feitas. G_E ainda usa espera padrão de 300 s até F-ESPERA. O plano prevê congelamento do código em 15/11, às 23:59; alinhar com o grupo qualquer trabalho de integração posterior.

## Objetivo
Eficiência da rede. Fecha:

- **RF-EFI-01** (E): Calcular a eficiência global da rede (média de 1/d entre pares)
- **RF-EFI-02** (E): Calcular o tempo médio de viagem entre pares origem-destino sorteados

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | implementado | 15/11: eficiência global em G_P e tempo médio amostrado em G_E, usando Dijkstra do núcleo |
| Modelo e dados | em andamento | Construtores de G_P/G_E e Rede de teste disponíveis; falta validar no feed real |
| Interface | implementado | 15/11: página `render(rede)` com tamanho de amostra e semente configuráveis; AppTest verde na rede de teste |
| Testes | implementado | 15/11: 660 testes verdes na suíte; gabaritos à mão, NetworkX, casos extremos, compatibilidade F-RES e AppTest |
| Desempenho (tempo medido) | não iniciado | |
| Guia (explicação e quiz) | em andamento | Explicação e perguntas adicionadas ao arquivo e ao GUIA; revisão cruzada pendente |
| Relatório | em andamento | Seção estruturada; medição/figura real pendentes |
| Vídeo | em andamento | Roteiro atualizado para demonstração; gravação e resultado real pendentes |

## Especificação
Assinaturas públicas em `src/transporte/algoritmos/eficiencia.py` (`estado: implementado`):

- `eficiencia_global(g, origens=None, n_referencia=None) -> float`: média de `1/d` sobre pares ordenados distintos. `origens=None` considera todas as origens ativas; uma origem explícita inativa contribui zero. `n_referencia` fixa a população do denominador e é compatível com a simulação de falhas da F-RES. Par sem caminho soma zero. Distância zero entre vértices distintos levanta `ValueError`. Tempo O(V + s (V + E) log V), espaço O(V + E + s).
- `estimar_eficiencia_global(g, tamanho_amostra=None, semente=0) -> Estimativa`: G_P; amostra uniforme sem reposição de origens. A observação de cada origem é sua média de `1/d` para os outros vértices; o erro padrão usa a variância amostral com correção para população finita. `None` calcula todas as origens e retorna erro zero. Tempo O(V + s (V + E) log V), espaço O(V + E + s).
- `tempo_medio_viagem(ge, tamanho_amostra, semente=0) -> Estimativa`: G_E; sorteia pares ordenados distintos de paradas uniformemente sem reposição, excluindo plataformas e pares de uma parada para ela mesma. O custo é o tempo total da rota da F-ROTA (caminhada, espera e ônibus). Pares sem trajeto são reportados em `pares_alcancaveis`, mas não entram na média como zero. Tempo O(V + k (V + E) log V + m), k origens amostradas distintas e m pares; espaço O(V + E + m).
- `Estimativa(valor, erro_padrao, tamanho_amostra, tamanho_populacao, pares_alcancaveis=None)`: erro padrão amostral; fica `None` em amostra incompleta com menos de duas observações válidas. Enumeração exata com observações válidas tem erro zero; sem viagem alcançável, `valor` e erro ficam `None`.

Algoritmos previstos (docs/fontes/modelagem.md §3.5):
- Eficiência global · G_P · O(V (V + E) log V) exata; O(s (V + E) log V) amostrada · Média de `1/d`; par sem caminho soma 0
- Tempo médio de viagem · G_E, somente vértices de paradas · uma busca por origem amostrada, não uma por par

G_P foi escolhido para RF-EFI-01 por medir eficiência estrutural e manter compatibilidade com a métrica provisória da F-RES. RF-EFI-02 usa G_E porque seus pesos e a semântica de `Trajeto.tempo_total_s` incluem caminhada, espera e viagem. G_E contém desembarque de peso zero; por isso a eficiência não é calculada sobre todas as plataformas.

## Como funciona e por quê

**Eficiência global.** Para cada origem de G_P, o Dijkstra do núcleo calcula de uma vez as distâncias a todos os destinos alcançáveis. A contribuição da origem é a soma de `1/d` para as demais paradas; os destinos inalcançáveis contribuem zero. A média é sobre os pares ordenados distintos, pois o grafo é dirigido. Por exemplo, com duas paradas e apenas uma aresta `A -> B` de peso 4 s, a soma é `1/4`; existem dois pares ordenados, então a eficiência é `1/8 s⁻¹`.

**Amostragem e erro.** A estimativa amostra origens uniformemente sem reposição e calcula a contribuição de cada origem em relação a todas as outras. O erro padrão é o desvio padrão amostral dessas contribuições dividido pela raiz do tamanho da amostra, com a correção de população finita; enumerar todas as origens produz o valor exato e erro zero. A semente fixa torna os resultados repetíveis. Essa escolha reduz o número de Dijkstras de V para s e corresponde ao requisito de amostragem de métricas de todos os pares (RNF-06).

**Tempo médio de viagem.** A população é formada pelos pares ordenados distintos de paradas em G_E, não pelas plataformas. A amostra de pares é uniforme sem reposição. Para cada origem diferente sorteada, uma chamada ao Dijkstra fornece os tempos aos destinos da amostra. O peso total tem a semântica da F-ROTA: caminhada, espera esperada da faixa e viagem de ônibus. Pares inalcançáveis são contados, mas excluídos da média; em amostra incompleta com menos de duas durações alcançáveis, não há erro padrão estimável. Como o tamanho total da população alcançável não é conhecido sem calcular todos os pares, o erro padrão dos tempos é a estimativa amostral sem correção finita. Se toda a população OD for enumerada e houver ao menos uma viagem alcançável, o erro é zero; sem nenhuma, valor e erro são `None`.

**Integração com a F-RES.** `eficiencia_global` conserva a assinatura provisória `eficiencia_global(g, origens=None, n_referencia=None) -> float`. A lista de origens e o denominador fixo mantêm a comparação antes/depois de falhas: par removido continua representado por contribuição zero. O módulo da F-RES não foi alterado; Caio pode substituir a função provisória pela importação desta API.

**Complexidade.** Uma busca Dijkstra por origem custa O((V + E) log V), usando o heap próprio do núcleo. A eficiência exata executa V buscas; a estimativa executa s. Para o tempo médio, k origens distintas atendem aos m pares amostrados, custando O(V + k (V + E) log V + m). A memória de cada execução é a do Dijkstra, O(V + E), mais O(m) para guardar os pares e tempos amostrados.

**Limitações.** G_P usa tempos medianos de viagem e caminhada, sem espera. Em G_E, o valor depende da faixa e a espera continua provisória em 300 s até a F-ESPERA fornecer a tabela. A média de viagens é condicional aos pares alcançáveis na amostra. Sem `dados/brutos/`, não foi possível medir desempenho na rede real nesta sessão.

## Perguntas de verificação
1. **Por que a eficiência global usa G_P?** Para medir a estrutura entre paradas sem incluir plataformas nem arestas de desembarque de peso zero; também mantém a métrica comparável à provisória da F-RES.
2. **Por que os pares são ordenados?** As arestas são dirigidas; o custo de A para B pode diferir do custo de B para A.
3. **Como o cálculo evita um Dijkstra por par?** Executa uma busca por origem e lê nela as distâncias aos destinos necessários.
4. **Como os pares inalcançáveis entram nas duas métricas?** Na eficiência contribuem zero; no tempo médio são contados à parte e não viram viagens de duração zero.
5. **O que significa o erro padrão exibido?** É a dispersão estimada da média amostrada; a amostra e a semente são exibidas para permitir repetir o cálculo.

## Critérios de aceite
- [x] RF-EFI-01: Calcular a eficiência global da rede (média de 1/d entre pares), com desconexão e origens inativas tratadas
- [x] RF-EFI-02: Calcular o tempo médio de viagem em pares de paradas amostrados em G_E, sem registrar pares inalcançáveis como tempo zero

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde (hook executado manualmente; não está configurado como hook automático neste checkout)
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [ ] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
- [ ] Página ou bloco na interface funcionando com o dataset real (AppTest cobre a rede de teste)
- [ ] Diagrama UML da feature gerado em `docs/diagramas/` (fonte PlantUML criada; PNG pendente)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação
- [x] Roteiro do vídeo escrito no arquivo da feature (rascunho, sem resultado real)
- [ ] Arquivo da feature atualizado: retomada ("concluída"), status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | concluída em 15/11; compatibilidade F-RES documentada |
| 2 | Algoritmo com testes de corretude | concluída; suíte completa passou (660 testes, Python 3.14.4) |
| 3 | Integração com a visão do grafo e com os dados reais | integrada às visões; rede real pendente |
| 4 | Página na interface | implementada; AppTest com rede de teste |
| 5 | Tempo medido na rede real e complexidade justificada | complexidade concluída; medição real pendente |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | explicação/quiz/roteiro escritos; PNG e resultado real pendentes |

## Resultados para o relatório
Sem medição na rede real: `dados/brutos/` não está disponível. O AppTest usa `dados/rede-teste/`; seus resultados validam integração e corretude, mas não são apresentados como desempenho da rede real.

## Roteiro do vídeo (2 a 2,5 min)
1. **Problema (25 s):** explicar que a eficiência estrutural resume os caminhos entre paradas e que o tempo médio complementa a análise com caminhada, espera e ônibus.
2. **Na interface (45 s):** abrir Eficiência, escolher quantidade de origens e pares, fixar a semente, calcular e apontar o erro padrão e os pares alcançáveis.
3. **Algoritmo (45 s):** mostrar G_P e G_E; explicar uma busca Dijkstra por origem amostrada, sem busca por cada par, e por que G_E é restrito a vértices de paradas.
4. **Resultado e limitação (25 s):** usar a rede de teste enquanto não houver GTFS real; explicar que a espera de G_E é provisoriamente 300 s e que os resultados reais ainda precisam ser medidos.

## Pendências
- **F-RES (Caio):** trocar a função provisória pela API `transporte.algoritmos.eficiencia.eficiencia_global`; a assinatura e a compatibilidade matemática foram testadas, mas a integração de produção não foi feita porque arquivos da F-RES estão fora do escopo autorizado.
- **F-ESPERA (Miguel):** `construir_ge` ainda usa a espera padrão de 300 s nesta execução; recalcular o tempo médio quando a tabela de esperas estiver disponível.
- **Rede real:** executar `medir` e registrar V, E, máquina, média e desvio quando o feed estiver disponível.
- **Fechamento:** gerar o PNG do diagrama, completar a seção do relatório com figura e resultados reais, validar na rede real, obter revisão cruzada e integrar por PR aprovado.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Arthur.
### Sessão 15/11/2026: implementados o contrato oficial e os algoritmos em `algoritmos/eficiencia.py`, página `render(rede)`, testes matemáticos/NetworkX/AppTest e documentação; suíte completa (660 testes, Python 3.14.4), Ruff, verificador de imports, hook manual e verificações de diff passaram. F-RES permanece sem alteração. Feed real indisponível; medição, PNG, fechamento do relatório e revisão cruzada continuam pendentes.
