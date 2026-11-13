# P0-UI · Aplicação Streamlit e componente de mapa

**Período:** 0 · Fundação (29/10 a 03/11) · **Classe:** fundação
**Dono:** Arthur (@ArthurkkLS) · **Issue:** #5 · **Visões do grafo:** todas (exibição)
**Depende de:** contrato de P0-DADOS · **Bloqueia:** páginas de todas as features
**Prazo:** contrato 30/10; aplicação 02/11

> Fonte de verdade: docs/fontes/REQUISITOS.md (RF-UI-01, RF-UI-02, RF-UI-03). Modelagem: docs/fontes/modelagem.md.
> Em conflito, o REQUISITOS.md vence.

## Retomada
- **Última sessão:** 12/11/2026.
- **Onde parou:** aplicação Streamlit, navegação, descoberta de fontes, cache isolado por sessão, contratos estruturais e mapa Folium implementados. Corrigido o bootstrap do `src/` para executar o comando documentado sem `PYTHONPATH`, com cobertura em subprocesso; P0-DADOS ainda não oferece carregador nem há GTFS no repositório.
- **Próximo passo:** alinhar com Miguel a função de carregamento que devolve a `Rede` publicada e conectá-la à chamada `main(carregador=...)`/ponto de entrada Streamlit; testar com a rede de teste e o feed real quando disponíveis.
- **Arquivos tocados:** `src/transporte/interface/app.py`, `tests/interface/test_app.py`, este arquivo.
- **Como testar:** `python -m pytest tests/interface/test_app.py::test_entrada_real_inicia_sem_pythonpath -q`; `python -m pytest tests/interface -q`; `python -m pytest -q`; `ruff check`; `ruff format --check src/transporte/interface tests/interface`; `python scripts/verificar_imports.py`; `git diff --check`.
- **Bloqueios:** integração real de carga e resumo com dataset depende de P0-DADOS; a implementação não duplica o parser GTFS nem presume uma API de carregamento que ainda não foi publicada. A cópia por sessão protege mutações, mas tem custo de memória proporcional ao tamanho da rede.

## Objetivo
Aplicação Streamlit e componente de mapa. Fecha:

- **RF-UI-01** (E): Aplicação gráfica com mapa da rede e navegação por páginas
- **RF-UI-02** (E): Carregar o conjunto de dados e mostrar o resumo da rede
- **RF-UI-03** (E): Componente de mapa reutilizável para paradas, caminhos e mapas de calor

## Status
| Camada | Status | Observação (data, evidência, o que falta) |
|---|---|---|
| Núcleo (algoritmo) | não aplicável | P0-UI não implementa algoritmo de grafo. |
| Modelo e dados | bloqueado | P0-DADOS ainda não implementa o carregador; `dados/rede-teste/` não contém GTFS. |
| Interface | parcial | Aplicação, navegação, mapa e registro de páginas implementados; carregamento integrado e mapa na rede real aguardam P0-DADOS. |
| Testes | implementado localmente | 13 testes de interface e 515 testes totais passaram em Python 3.14.4; o projeto especifica Python 3.12. O teste de inicialização executa o arquivo real em subprocesso sem `PYTHONPATH`; os demais não dependem de feed. |
| Desempenho (tempo medido) | pendente | Sem feed para medir carregamento; mapa não executa algoritmo de grafo. |
| Guia (explicação e quiz) | implementado | Seção 6 e perguntas da P0-UI incluídas em `docs/GUIA.md`. |
| Relatório | pendente | Resultado de uso real depende da integração de dados. |
| Vídeo | pendente | Gravação após integração e validação com dataset. |

## Especificação
Contrato inicial em `docs/fontes/plano-de-projeto.md` §9. Publicar as assinaturas com o comentário `estado: planejado` antes de implementar; trocar para `implementado` quando os testes passarem.

## Como funciona e por quê

A aplicação não interpreta GTFS: ela descobre fontes locais e delega o carregamento a um
`CarregadorRede` injetado, que deve devolver o modelo `Rede` de P0-DADOS. O cache de recurso do
Streamlit guarda o resultado de uma leitura para reutilizar o trabalho, mas `carregar_rede`
devolve uma cópia profunda independente a cada sessão. Isso evita que uma feature que altere
grafos ou dados durante uma simulação compartilhe mutações com outra sessão.

O mapa usa camadas Folium independentes para paradas, padrões, caminhos e intensidades; assim,
cada página reaproveita o mesmo componente e escolhe o que exibir. A construção percorre as
paradas, os padrões/caminhos solicitados e as intensidades uma vez: tempo e espaço
O(P + S + C + H), em que P são paradas, S é o total de paradas dos padrões exibidos, C é o total
de pontos dos caminhos e H é o número de intensidades.

As páginas entram por um registro de módulos e seguem `render(rede)`. Se o módulo ainda não
existe, a navegação mostra que a página está indisponível. Como o comando documentado executa
`app.py` diretamente e o projeto usa layout `src/` sem instalação, o arquivo inclui `src/` no
caminho de importação antes de importar `transporte`. O teste de inicialização roda a entrada
real por subprocesso desde a raiz, sem herdar `PYTHONPATH`. O carregador de P0-DADOS ainda não foi
publicado; por isso a execução atual informa a pendência em vez de apresentar um falso resumo ou
de criar um segundo modelo de dados.

## Perguntas de verificação

1. **Por que a UI não lê os CSV GTFS?** Para manter a leitura e normalização sob responsabilidade
   de P0-DADOS e consumir o contrato único `Rede`.
2. **Quais visualizações o mapa reutilizável suporta?** Paradas, linhas/padrões, caminhos e mapas
   de calor, em camadas Folium separadas.
3. **Como uma página de feature se integra?** Publicando `render(rede)` no módulo registrado na
   navegação.
4. **Como o cache evita compartilhar mutações entre sessões?** O recurso carregado é armazenado
   em cache, mas cada carga de sessão recebe uma cópia profunda.
5. **O que falta para carregar um dataset de ponta a ponta?** P0-DADOS publicar e integrar uma
   função que receba a origem e devolva a `Rede` definida no contrato.

## Critérios de aceite
- [ ] RF-UI-01: Aplicação gráfica com mapa da rede e navegação por páginas (shell iniciou; smoke test retornou HTTP 200 e health `ok`; falta validação com rede carregada)
- [ ] RF-UI-02: Carregar o conjunto de dados e mostrar o resumo da rede
- [x] RF-UI-03: Componente de mapa reutilizável para paradas, caminhos e mapas de calor (testes de camadas Folium aprovados)

## Definition of Done
Lista-base de `docs/fontes/plano-de-projeto.md` §11. Item que não se aplica fica marcado como "não aplicável", com o motivo.

- [ ] Código integrado na `main` por PR aprovado por outro integrante
- [x] Hook verde (nenhuma biblioteca de grafo em `src/`, ruff limpo) e pytest verde (verificações executadas localmente nesta branch)
- [x] Testes de corretude com gabarito à mão, inclusive casos de borda; comparação de resultado com o NetworkX quando houver equivalente (casos de UI testados; comparação de grafos não se aplica)
- [x] Complexidade de tempo e de espaço declarada na docstring e justificada no arquivo da feature
- [ ] Tempo medido na rede real com `medir`, registrado no arquivo da feature com V, E e a máquina
- [ ] Página ou bloco na interface funcionando com o dataset real
- [x] Diagrama UML da feature (sequência ou atividade) em `docs/diagramas/sequencia-p0-ui.puml`
- [x] "Como funciona e por quê" e perguntas de verificação escritas no arquivo da feature e incorporadas ao `docs/GUIA.md`
- [ ] O revisor do PR consegue explicar o que o código faz
- [ ] Seção do relatório em `relatorio/secoes/<feature>.tex`, com figura, resultado e limitação
- [ ] Roteiro do vídeo escrito no arquivo da feature
- [ ] Arquivo da feature atualizado: retomada ("concluída"), status, pendências e timeline

## Plano de implementação
| Etapa | Escopo | Situação |
|---|---|---|
| 1 | Contrato (assinaturas com estado "planejado") | Implementado na UI com protocolos estruturais que consomem os campos publicados de `Rede`; assinatura do loader segue pendente de P0-DADOS. |
| 2 | Algoritmo com testes de corretude | Não aplicável: P0-UI não implementa algoritmo de grafo; mapa e integração têm testes próprios. |
| 3 | Integração com a visão do grafo e com os dados reais | Bloqueada: sem loader P0-DADOS e sem dataset GTFS versionado/disponível. |
| 4 | Página na interface | Parcial: shell Streamlit, navegação, descoberta, cache, mapa e despacho `render(rede)` implementados; faltam carga e resumo de rede real. |
| 5 | Tempo medido na rede real e complexidade justificada | Complexidade do mapa documentada; medição na rede real pendente por falta de feed. |
| 6 | Como funciona e por quê, perguntas de verificação, diagrama UML, seção do relatório e roteiro do vídeo | Explicação, perguntas e fonte UML adicionadas; relatório e vídeo aguardam integração/execução real. |

## Resultados para o relatório
_Vazio até haver execução real. Todo número vem com o comando que o gerou._

## Roteiro do vídeo (2 a 2,5 min)
1. O problema que a feature resolve. 2. A feature funcionando na interface.
3. Algoritmo e complexidade. 4. Resultado e limitação.

## Pendências
- Integrar o carregador de P0-DADOS quando sua assinatura for publicada, sem duplicar o parser.
- Alinhar a identidade do cache com P0-DADOS; a invalidação atual considera caminho, tamanho e
  data de modificação, não o conteúdo de cada arquivo.
- O ponto de entrada `streamlit run ...` chama `main()` sem loader; ligar o loader de P0-DADOS ao
  ponto de entrada ao integrar essa feature.
- Confirmar com P0-DADOS os layouts de GTFS aceitos (a descoberta atual cobre ZIPs e diretórios
  extraídos na raiz ou um nível abaixo das pastas configuradas).
- Alinhar com P0-MODELO/P0-DADOS o resumo das arestas por visão indicado em `modelagem.md` §3.6;
  o resumo atual só conta paradas, linhas e padrões.
- Alinhar com F-ROTA a apresentação no mapa de cada trecho por modo/linha/tempo; o componente
  atual recebe sequências de paradas e desenha uma linha genérica.
- Validar carregamento, resumo e mapa com a rede de teste e o GTFS real.
- Completar RF-UI-01/02, medir a interação com os dados reais e concluir relatório e vídeo após validação.
- Fazer revisão por outro integrante e integrar via PR; não executado nesta sessão.

## Timeline
### Criação 29/10/2026: gerado a partir do plano aprovado pelo grupo.
### Dono 29/10/2026: feature atribuída a Arthur.
### Implementação 09/11/2026: shell Streamlit, navegação, contrato estrutural, cache, mapa Folium, testes e documentação local; carga real bloqueada por P0-DADOS.
### Correção 12/11/2026: bootstrap do layout `src/` para o comando direto e teste real de inicialização em subprocesso sem `PYTHONPATH`; 13 testes de interface e 515 totais aprovados com Python 3.14.4.
