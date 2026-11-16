# P0-UI · Aplicação Streamlit e componente de mapa

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Arthur (@ArthurkkLS) · **Issue:** #5 · **Visões do grafo:** todas (exibição)
**Depende de:** contrato de P0-DADOS · **Bloqueia:** páginas de todas as features
**Prazo:** contrato 30/10; aplicação 02/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-UI-01, RF-UI-02, RF-UI-03). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 15/11/2026.
- **Onde parou:** conexão com `transporte.dados.leitor_gtfs.ler`, carga de pastas/ZIP, preservação da rede anterior quando a carga falha, resumo da rede, V/E de G_P e G_E, inconsistências e trajetos segmentados no mapa implementados. A branch ainda não contém P0-DADOS porque está 4 commits atrás de `origin/main`; nenhuma alteração de Miguel foi copiada ou mesclada.
- **Próximo passo:** alinhar a atualização da branch com o responsável por P0-DADOS e resolver as sobreposições do app/testes com o PR #50 antes de integrar. Em seguida medir na rede real, quando os dados GTFS estiverem disponíveis, e concluir relatório/vídeo.
- **Arquivos tocados:** `src/transporte/interface/app.py`, `src/transporte/interface/mapa.py`, `src/transporte/interface/protocolos.py`, `tests/interface/test_mapa.py`, `tests/interface/test_integracao_dados.py`, `docs/GUIA.md`, `docs/diagramas/sequencia-p0-ui.puml`, este arquivo e `relatorio/secoes/implementacao.tex`.
- **Como testar:** `python -m pytest tests/interface/test_app.py::test_entrada_real_inicia_sem_pythonpath -q`; `python -m pytest tests/interface -q`; `python -m pytest -q`; `ruff check`; `ruff format --check src/transporte/interface tests/interface`; `python scripts/verificar_imports.py`; `git diff --check`.
- **Bloqueios:** o checkout desta branch não contém os arquivos da P0-DADOS nem os arquivos de `dados/rede-teste/`, embora estejam em `origin/main`; por isso os testes de integração foram executados numa árvore temporária combinada, sem atualizar o histórico da branch. Não há feed GTFS real em `dados/brutos/` para medir desempenho.

## Objetivo
Aplicação Streamlit e componente de mapa. Fecha:

- **RF-UI-01** (E): Aplicação gráfica com mapa da rede e navegação por páginas
- **RF-UI-02** (E): Carregar o conjunto de dados e mostrar o resumo da rede
- **RF-UI-03** (E): Componente de mapa reutilizável para paradas, caminhos e mapas de calor

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | não aplicável | P0-UI não implementa algoritmo de grafo. |
| Modelo e dados | integrado | A interface consome `ler` e `Rede` publicados em P0-DADOS na `origin/main`; o checkout local permanece atrás desse commit. |
| Interface | implementado | Pasta/ZIP, preservação da rede em erro, resumo, dia, inconsistências, V/E, mapa real no Streamlit e contrato `render(rede)` validados com `dados/rede-teste`. |
| Testes | aprovado em árvore combinada | 24 testes de interface e 632 testes totais passaram com Python 3.14.4. Python 3.12 não está instalado. |
| Desempenho (tempo medido) | pendente | Não há feed real disponível no checkout. O requisito de medição com dados reais permanece aberto; não substituir por números da rede de teste. |
| Guia (explicação e quiz) | implementado | Seção 6 e pergunta 5 atualizadas em `docs/GUIA.md`. |
| Relatório | parcial | Seção da UI preenchida com figura de componentes, resultado da rede de teste e limitação explícita; figura de sequência ainda não renderizada porque PlantUML não está disponível. |
| Vídeo | roteiro atualizado | Roteiro de demonstração incluído abaixo; gravação com feed real ainda pendente. |

## Especificação
Contrato inicial em `docs/fontes/plano-de-projeto.md` §9. Publicar as assinaturas com o comentário `estado: planejado` antes de implementar; trocar para `implementado` quando os testes passarem.

## Como funciona e por quê

A aplicação não interpreta GTFS: ela descobre fontes locais e usa o `ler` publicado por P0-DADOS,
que aceita pasta ou ZIP e devolve o modelo `Rede`. O parâmetro `main(carregador=...)` mantém a
possibilidade de injetar outro carregador nos testes e em integrações, enquanto a entrada
documentada usa `ler` por padrão. O cache de recurso do Streamlit reutiliza o resultado de uma
leitura; `carregar_rede` devolve uma cópia profunda independente a cada sessão. Se a carga nova
falhar, o estado atual não é substituído. Depois da carga, os construtores existentes de P0-MODELO
produzem G_P e G_E para exibir V/E, sem mover algoritmos ou responsabilidade de modelagem para a UI.

O protocolo local `RedeUI` substitui a referência provisória `RedeCarregada` do contrato de
planejamento: ele descreve estruturalmente os campos efetivamente publicados em `Rede`, incluindo
linhas, viagens, dia e inconsistências, sem criar um segundo modelo nem importar o parser no
componente de mapa. O mapa usa camadas Folium para paradas, padrões, caminhos, calor e segmentos
de trajeto. `TrajetoUI` aceita os campos existentes de F-ROTA; exibe rótulos, cores e marcador de
baldeação quando esses dados existem. Páginas que adicionarem camadas após `criar_mapa` podem
chamar `atualizar_controle_camadas` antes da renderização.

As páginas entram por um registro de módulos e seguem `render(rede)`. Se o módulo ainda não
existe, a navegação mostra que a página está indisponível. Como o comando documentado executa
`app.py` diretamente e o projeto usa layout `src/` sem instalação, o arquivo inclui `src/` no
caminho de importação antes de importar `transporte`. O teste de inicialização roda a entrada
real por subprocesso desde a raiz, sem herdar `PYTHONPATH`.

## Perguntas de verificação

1. **Por que a UI não lê os CSV GTFS?** Para manter a leitura e normalização sob responsabilidade
   de P0-DADOS e consumir o contrato único `Rede`.
2. **Quais visualizações o mapa reutilizável suporta?** Paradas, linhas/padrões, caminhos e mapas
   de calor, em camadas Folium separadas.
3. **Como uma página de feature se integra?** Publicando `render(rede)` no módulo registrado na
   navegação.
4. **Como o cache evita compartilhar mutações entre sessões?** O recurso carregado é armazenado
   em cache, mas cada carga de sessão recebe uma cópia profunda.
5. **Como o resumo combina o leitor e as visões?** `ler` devolve a `Rede` com dia e
   inconsistências; a página chama `construir_gp` e `construir_ge` para mostrar V/E. A faixa de
   G_E indicada é `pico_manha`; medir o fluxo em um feed real ainda depende de dados reais locais.

## Critérios de aceite
- [x] RF-UI-01: Aplicação gráfica com mapa e navegação; servidor retornou HTTP 200/`ok`, e AppTest carregou a rede de teste e renderizou o mapa sem exceção.
- [x] RF-UI-02: Carga de pasta e ZIP, resumo, dia de serviço e inconsistências verificados por AppTest.
- [x] RF-UI-03: Camadas Folium, caminho segmentado, `returned_objects=[]` e camadas adicionadas após `criar_mapa` verificados por testes.

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [x] Hook executado manualmente e verde; Ruff e verificador de imports verdes; pytest verde na árvore combinada baseada em `origin/main` + mudanças P0-UI. A branch isolada ainda não contém P0-DADOS.
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (casos de UI testados; comparação de grafos não se aplica)
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [ ] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
- [ ] Página ou bloco na interface funcionando com o dataset real
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/sequencia-p0-ui.puml`
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [x] Seção do relatório em `relatorio/secoes/implementacao.tex`, com figura de componentes, resultado da rede de teste e limitação explícita
- [x] Roteiro do vídeo escrito no arquivo da feature
- [x] Arquivo da feature atualizado com retomada, status, pendências e timeline (a feature não está concluída)

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | Implementado com protocolos estruturais para `Rede`, `Trecho` e `Trajeto`; a interface usa o loader publicado por P0-DADOS. |
| 2 | Algoritmo com testes de corretude | Não aplicável: P0-UI não implementa algoritmo de grafo; mapa e integração têm testes próprios. |
| 3 | Integração com a visão do grafo e com os dados reais | Integração e teste com a rede de teste concluídos na árvore combinada; validação com feed real pendente. |
| 4 | Página na interface | Concluída para pasta/ZIP: carga, resumo, V/E, inconsistências, mapa e despacho `render(rede)` testados. |
| 5 | Tempo medido na rede real e complexidade justificada | Complexidades documentadas; não há feed real local para medição, então o item permanece pendente. |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | Guia, fonte PlantUML, seção do relatório e roteiro atualizados; PNG da sequência e gravação do vídeo pendentes. |

## Resultados para o relatório
Na rede de teste GTFS, o AppTest confirmou 4 paradas, 2 linhas, 2 padrões e dia de serviço
2026-11-04. Para `pico_manha`, a execução mostrou G_P com V=4 e E=13, e G_E com V=9 e E=18.
Comando: `python -m pytest tests/interface -q` (24 passed, Python 3.14.4) e execução do app por
AppTest com o componente Folium real. A suíte completa na árvore temporária combinada
(`origin/main` mais as mudanças desta branch) passou: `python -m pytest -q` (632 passed).
Não foram medidos tempos de carregamento nem `criar_mapa` em feed real: `dados/brutos/` não está
disponível neste ambiente, então os totais da rede de teste não são apresentados como resultado
do feed real.

## Roteiro do vídeo (2 a 2,5 min)
1. **0:00–0:20 — Objetivo:** explicar que a interface conecta o GTFS normalizado às páginas
   das features, sem reler ou reinterpretar CSVs.
2. **0:20–0:45 — Entrada:** iniciar com `streamlit run src/transporte/interface/app.py`, escolher
   `dados/rede-teste/` e carregar; mostrar que pasta e ZIP usam o mesmo `ler` de P0-DADOS.
3. **0:45–1:20 — Resumo e mapa:** apontar o dia de serviço, paradas/linhas/padrões,
   inconsistências, V/E de G_P e G_E e as camadas Folium selecionáveis.
4. **1:20–1:50 — Integração:** explicar `main(carregador=ler)`, a cópia isolada por sessão e
   como uma página registra `render(rede)`; mostrar o suporte do mapa aos trechos publicados por
   F-ROTA sem inventar dados ausentes.
5. **1:50–2:20 — Limitações:** mostrar o teste de erro que preserva a rede anterior e esclarecer
   que o feed GTFS real e a medição de desempenho ainda não estão disponíveis.

## Pendências
- Alinhar a identidade do cache com P0-DADOS; a invalidação atual considera caminho, tamanho e
  data de modificação, não o conteúdo de cada arquivo.
- O checkout local está 4 commits atrás de `origin/main` e não contém P0-DADOS nem `dados/rede-teste`; atualizar a base em coordenação com o responsável antes de executar a suíte diretamente na branch.
- Coordenar com Miguel a sobreposição do app, mapa e testes com o PR #50; não copiar os arquivos do leitor nem a rede de teste para esta branch.
- Confirmar com F-ROTA o uso de `render_mapa(..., trajeto=...)` na página da feature, que ainda não existe nesta branch.
- Descoberta de fontes aceita ZIPs na raiz e pastas GTFS na raiz ou um nível abaixo das pastas configuradas; alinhar se outros layouts forem necessários.
- Medir carregamento e `criar_mapa` com `medir` no feed GTFS real, quando disponível, e registrar V/E e máquina.
- Gerar PNG da sequência P0-UI quando PlantUML estiver disponível; o repositório não contém esse PNG nem foi encontrado CLI/JAR neste ambiente.
- Fazer revisão por outro integrante e integrar via PR; não executado nesta sessão.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Arthur.
### Implementação 09/11/2026: shell Streamlit, navegação, contrato estrutural, cache, mapa Folium, testes e documentação local; carga real bloqueada por P0-DADOS.
### Correção 12/11/2026: bootstrap do layout `src/` para o comando direto e teste real de inicialização em subprocesso sem `PYTHONPATH`; 13 testes de interface e 515 totais aprovados com Python 3.14.4.
### Integração 15/11/2026: leitor P0-DADOS como padrão, visões G_P/G_E, carga de pasta/ZIP, mapa de trajetos, testes e documentação atualizados; 24 testes de interface e 632 testes totais aprovados numa árvore combinada, Python 3.14.4. Feed real e PNG PlantUML pendentes.
