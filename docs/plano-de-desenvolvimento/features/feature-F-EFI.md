# F-EFI · Eficiência da rede

**Período:** 1 · Essenciais (04/11 a 11/11) · **Classe:** prioritária
**Dono:** Arthur (@ArthurkkLS) · **Issue:** #11 · **Visões do grafo:** G_E ou G_P
**Depende de:** P0-MODELO, F-ESPERA · **Bloqueia:** F-RES (função de eficiência até 07/11), F-EFI-2
**Prazo:** 11/11 (checkpoint 07/11)

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-EFI-01, RF-EFI-02). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 18/11/2026, Arthur.
- **Onde parou:** página integrada a F-ESPERA e benchmark reproduzível executado no GTFS baixado nesta sessão. O revisor já confirmou 754 testes no Python 3.12.10 e a eficiência de `6,139 × 10⁻⁴ s⁻¹` para 100 origens, igual à medição do Caio. O benchmark temporal desta sessão está registrado abaixo; algoritmo e valor confirmado não foram reimplementados.
- **Próximo passo:** revisar os resultados e a integração no PR #52; ainda faltam a captura da página para o relatório e a revisão/aprovação final.
- **Arquivos tocados nesta etapa:** `benchmarks/medir_eficiencia.py`, `src/transporte/interface/paginas/eficiencia.py`, `tests/interface/test_pagina_eficiencia.py`, `docs/diagramas/sequencia-eficiencia.png`, `relatorio/secoes/F-EFI.tex` e este arquivo.
- **Como testar:** `python -m pytest tests/algoritmos/test_eficiencia.py tests/interface/test_pagina_eficiencia.py -q`; `$env:PYTHONPATH='src'; python benchmarks/medir_eficiencia.py dados/brutos/bhtrans.zip`; `ruff check` nos arquivos alterados; `python scripts/verificar_imports.py`; `git diff --check`. A suíte completa de 754 testes no Python 3.12.10 foi validada pelo revisor; nesta etapa, 28 testes direcionados de algoritmo e interface passaram em Python 3.14.4.
- **Bloqueios:** nenhum bloqueio de algoritmo ou feed. A validação visual da página no feed real, a figura de tela do relatório e a aprovação do PR ainda dependem de revisão manual.

## Objetivo
Eficiência da rede. Fecha:

- **RF-EFI-01** (E): Calcular a eficiência global da rede (média de 1/d entre pares)
- **RF-EFI-02** (E): Calcular o tempo médio de viagem entre pares origem-destino sorteados

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | implementado | 15/11: eficiência global em G_P e tempo médio amostrado em G_E, usando Dijkstra do núcleo |
| Modelo e dados | implementado | 18/11: G_E da página usa intervalos e esperas calculados pela F-ESPERA; benchmark executado no GTFS de 18/11 |
| Interface | implementado | 18/11: `render(rede)` usa as esperas da F-ESPERA; AppTest verifica peso de embarque calculado, além das métricas |
| Testes | implementado | Revisor confirmou 754 testes no Python 3.12.10; nesta etapa, 28 testes direcionados de algoritmo e interface passaram no Python 3.14.4 |
| Desempenho (tempo medido) | medido | 18/11: benchmark reproduzível; resultados e hash registrados abaixo |
| Guia (explicação e quiz) | em andamento | Explicação e perguntas adicionadas ao arquivo e ao GUIA; revisão cruzada pendente |
| Relatório | em andamento | Resultados reais incluídos; figura de tela pendente |
| Vídeo | em andamento | Roteiro atualizado com resultado real; gravação pendente |

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

**Limitações.** G_P usa tempos medianos de viagem e caminhada, sem espera. Em G_E, a página calcula intervalos e esperas pela F-ESPERA; padrões sem intervalo estimável usam o fallback configurado em `Parametros`. A média de viagens é condicional aos pares alcançáveis na amostra.

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
- [x] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
- [ ] Página ou bloco na interface funcionando com o dataset real (AppTest cobre a rede de teste; falta validação visual da aplicação)
- [x] Diagrama UML da feature gerado em `docs/diagramas/` (`sequencia-eficiencia.puml` e PNG)
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação
- [x] Roteiro do vídeo escrito no arquivo da feature (gravação pendente)
- [ ] Arquivo da feature atualizado: retomada ("concluída"), status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | concluída em 15/11; compatibilidade F-RES documentada |
| 2 | Algoritmo com testes de corretude | concluída; revisor confirmou 754 testes no Python 3.12.10 |
| 3 | Integração com a visão do grafo e com os dados reais | integrada às visões e às esperas da F-ESPERA; benchmark real executado |
| 4 | Página na interface | implementada; AppTest com rede de teste |
| 5 | Tempo medido na rede real e complexidade justificada | concluída; medição real registrada |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | PlantUML/PNG e resultados do benchmark registrados; figura de tela e gravação pendentes |

## Resultados e evidências do benchmark

- **Comando:** `$env:PYTHONPATH='src'; python benchmarks/medir_eficiencia.py dados/brutos/bhtrans.zip` (padrões: 100 origens, 100 pares, 3 repetições, semente 2026, faixa `pico_manha`).
- **Feed:** `dados/brutos/bhtrans.zip`; SHA-256 `8cb0a498b90b227221d0234e3b6386a7dfbe375a2cb2e52e86238010be05f6d6`; serviço de 18/11/2026.
- **Rede:** 9.660 paradas, 303 linhas, 698 padrões e 24.503 viagens; G_P: V=9.660, E=122.799; G_E (`pico_manha`): V=46.102, E=209.025.
- **Máquina:** Windows 11 (10.0.26200), AMD Ryzen 7 7730U with Radeon Graphics, 15,4 GB RAM; Python 3.14.4.
- **Tempo medido por `medir` (3 repetições):** eficiência global amostrada, 100 origens: média 8,696 s, desvio amostral 0,130 s; tempo médio de viagem, 100 pares: média 26,321 s, desvio amostral 0,125 s. A leitura do GTFS e a construção dos grafos/esperas ocorreram fora das chamadas cronometradas.
- **Valor da eficiência (feed de 18/11):** `5,884 × 10⁻⁴ s⁻¹` (erro padrão `1,20 × 10⁻⁵`) para 100 origens e semente 2026; `estimar_eficiencia_global(gp.grafo, tamanho_amostra=100, semente=2026)` no G_P acima, conferido pelo revisor em 19/11 com o feed de SHA-256 `8cb0a4…` e igual ao da captura da página. O benchmark desta etapa registra os tempos das chamadas; `medir` descarta os valores retornados.
- **Valor anterior, feed de 11/11:** o `6,139 × 10⁻⁴ s⁻¹` conferido na revisão de 17/11 e medido pelo Caio na F-RES é do feed de 11/11 (SHA-256 `459f3a…`, G_P com V=9.659 e E=122.732). Com uma parada a mais, as 100 origens sorteadas com a semente 2026 mudam, e a diferença (cerca de 2 erros padrão) vem da amostra e dos dados, não do código.

O benchmark usa a versão mais recente baixada em 18/11 e pode variar com o hardware, o Python, a amostra e a semente.

## Roteiro do vídeo (2 a 2,5 min)
1. **Problema (25 s):** explicar que a eficiência estrutural resume os caminhos entre paradas e que o tempo médio complementa a análise com caminhada, espera e ônibus.
2. **Na interface (45 s):** abrir Eficiência, escolher quantidade de origens e pares, fixar a semente, calcular e apontar o erro padrão e os pares alcançáveis.
3. **Algoritmo (45 s):** mostrar G_P e G_E; explicar uma busca Dijkstra por origem amostrada, sem busca por cada par, e por que G_E é restrito a vértices de paradas.
4. **Resultado e limitação (25 s):** apresentar a medição registrada para o GTFS baixado, explicando que tempos dependem da máquina, da amostra e da semente; a espera de G_E vem da estimativa da F-ESPERA.

## Pendências
- **F-RES (Caio):** trocar a função provisória pela API `transporte.algoritmos.eficiencia.eficiencia_global`; a assinatura e a compatibilidade matemática foram testadas, mas a integração de produção não foi feita porque arquivos da F-RES estão fora do escopo autorizado.
- **F-ESPERA (Miguel):** integrada à página; padrões sem intervalo estimável continuam sujeitos ao fallback definido em `Parametros`.
- **Interface/relatório:** validar visualmente a página com o GTFS real e adicionar a captura à seção do relatório.
- **Fechamento:** obter revisão cruzada e aprovação do PR; a API da F-RES ainda é provisória e permanece fora do escopo desta alteração.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Arthur.
### Sessão 15/11/2026: implementados o contrato oficial e os algoritmos em `algoritmos/eficiencia.py`, página `render(rede)`, testes matemáticos/NetworkX/AppTest e documentação; suíte completa (660 testes, Python 3.14.4), Ruff, verificador de imports, hook manual e verificações de diff passaram. F-RES permanece sem alteração. Feed real indisponível; medição, PNG, fechamento do relatório e revisão cruzada continuam pendentes.
### Sessão 18/11/2026: integração da página com as esperas calculadas pela F-ESPERA; AppTest confirma o peso derivado de H/2; benchmark no GTFS baixado (hash, V/E, máquina e tempos) e PNG de sequência gerados; relatório atualizado com o resultado e com a distinção entre G_P e G_E.
