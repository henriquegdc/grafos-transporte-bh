# P0-UI · Aplicação Streamlit e componente de mapa

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Arthur (@ArthurkkLS) · **Issue:** #5 · **Visões do grafo:** todas (exibição)
**Depende de:** contrato de P0-DADOS · **Bloqueia:** páginas de todas as features
**Prazo:** contrato 30/10; aplicação 02/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-UI-01, RF-UI-02, RF-UI-03). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada

**Preparação da página Início medida no feed real.** A leitura da fonte, a cópia por sessão e a montagem dos dois grafos usam as funções chamadas pela página, na main após o #45. O diagrama está em `docs/diagramas/sequencia-p0-ui.puml` e seu PNG é incluído em Implementação. Para reproduzir o benchmark use o comando em Resultados. Para validar a interface: `python -m pytest tests/interface`. Próximo passo pessoal: gravar a demonstração.

## Objetivo
Aplicação Streamlit e componente de mapa. Fecha:

- **RF-UI-01** (E): Aplicação gráfica com mapa da rede e navegação por páginas
- **RF-UI-02** (E): Carregar o conjunto de dados e mostrar o resumo da rede
- **RF-UI-03** (E): Componente de mapa reutilizável para paradas, caminhos e mapas de calor

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | não aplicável | P0-UI não implementa algoritmo de grafo. |
| Modelo e dados | integrado | Usa a Rede normalizada e os construtores da main. |
| Interface | concluído | Pasta/ZIP, preservação da rede em erro, resumo, dia, inconsistências, V/E, mapa real no Streamlit e contrato `render(rede)` validados com `dados/rede-teste`. |
| Testes | concluído | Casos de pasta e ZIP, erro preservando a sessão, mapa, navegação e resumo. |
| Desempenho (tempo medido) | concluído | Carga fria e quente e montagem de G_P/G_E pelo código da página. Ver JSON em Resultados. |
| Guia (explicação e quiz) | concluído | Seção 6 e pergunta 5 atualizadas em `docs/GUIA.md`. |
| Relatório | concluído | Figura de sequência da página e números do feed real na seção Implementação. |
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
- [x] Hook e suíte executados sobre a base da main no Python 3.12, com as dependências fixadas.
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (casos de UI testados; comparação de grafos não se aplica)
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [x] Tempo medido no feed real, por etapa e com contagens V/E.
- [x] Página no feed real validada pelo AppTest da integração de P0-DADOS em 11/11 (ver feature-P0-DADOS).
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/sequencia-p0-ui.puml`
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [x] Seção Implementação com figura de sequência de Início, resultados e custo fora do escopo da medição.
- [x] Roteiro do vídeo escrito no arquivo da feature
- [x] Arquivo da feature atualizado com retomada, status, pendências e timeline (a feature não está concluída)

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | Implementado com protocolos estruturais para `Rede`, `Trecho` e `Trajeto`; a interface usa o loader publicado por P0-DADOS. |
| 2 | Algoritmo com testes de corretude | Não aplicável: P0-UI não implementa algoritmo de grafo; mapa e integração têm testes próprios. |
| 3 | Integração com a visão do grafo e com os dados reais | Integrada em main; feed real carregado na validação P0-DADOS e no benchmark P0-UI. |
| 4 | Página na interface | Concluída para pasta/ZIP: carga, resumo, V/E, inconsistências, mapa e despacho `render(rede)` testados. |
| 5 | Tempo medido na rede real e complexidade justificada | Carga e montagem medidas na rede real com a função medir; ver Resultados. |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | Guia, UML, PNG no relatório e roteiro disponíveis. Gravação a cargo do integrante. |

## Resultados para o relatório

Comando na raiz, com o ZIP de BH e o ambiente do projeto:

```sh
PYTHONPATH=src python benchmarks/medir_inicio.py dados/brutos/bhtrans.zip --repeticoes 3
```

O [JSON da execução](../../../benchmarks/resultados/inicio-bhtrans.json) identifica o SHA-256 do ZIP, a máquina e o serviço de 04/11/2026. No macOS arm64 com Python 3.12.13, `medir` produziu estes resultados em três repetições (média e desvio padrão amostral).

| Etapa da página | Média (s) | Desvio (s) |
|---|---:|---:|
| Esvaziar o cache da aplicação, ler o ZIP e devolver a cópia por sessão | 7,827 | 0,034 |
| Recuperar a mesma fonte do cache e copiar para a sessão | 0,671 | 0,017 |
| Construir G_P e G_E do pico da manhã e obter os totais | 0,440 | 0,001 |

O resumo exibiu G_P com 9.659 vértices e 122.732 arestas e G_E com 46.100 vértices e 208.956 arestas. O cache frio se refere ao cache Streamlit. O sistema operacional pode conservar o arquivo em memória. O benchmark termina antes de desenhar o mapa no navegador.

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
   que a renderização do mapa no navegador fica fora das medidas de carga e montagem.

## Pendências

- Gravar a demonstração no feed real. A renderização no navegador varia com o tamanho do mapa e permanece fora da medição de preparação. A identidade da fonte em cache usa caminho, tamanho e data de modificação.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Arthur.
### Implementação 09/11/2026: shell Streamlit, navegação, contrato estrutural, cache, mapa Folium, testes e documentação local; carga real bloqueada por P0-DADOS.
### Correção 12/11/2026: bootstrap do layout `src/` para o comando direto e teste real de inicialização em subprocesso sem `PYTHONPATH`; 13 testes de interface e 515 totais aprovados com Python 3.14.4.
### Integração 15/11/2026: leitor P0-DADOS como padrão, visões G_P/G_E, carga de pasta/ZIP, mapa de trajetos, testes e documentação atualizados; 24 testes de interface e 632 testes totais aprovados numa árvore combinada, Python 3.14.4. Feed real e PNG PlantUML pendentes.

### Fechamento documental de 20/11/2026
Medidas as etapas que preparam Início no GTFS de BH. O relatório recebeu o diagrama renderizado e os tempos, com a separação entre cache frio e quente.
