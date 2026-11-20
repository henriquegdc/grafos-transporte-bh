# F-EFI-2 · Isócronas e índice de desvio

**Dono original:** Arthur (@ArthurkkLS). **Implementação de 20/11:** Miguel (@Miguelgdn1).
**Issue:** #17. **Classe:** desejável. **Visão:** G_E.

## Retomada

Implementação, ensaios, interface, material do guia, relatório e medição final
concluídos na branch de eficiência. Próximo passo: revisão de Henrique e
integração do PR na main. A gravação do trecho segue o roteiro abaixo.

## Critérios de aceite

- [x] RF-EFI-03 · Mostrar paradas alcançáveis em até T minutos.
- [x] RF-EFI-04 · Comparar comprimento e tempo na rede com a distância direta.

## Status

| Camada | Evidência |
|---|---|
| Modelo e núcleo | `algoritmos/isocronas.py`, `algoritmos/eficiencia.py` |
| Testes | `tests/algoritmos/test_extensoes_eficiencia.py`; gabarito manual, bordas e comparação das isócronas com NetworkX em dez grafos semeados |
| Interface | Página Eficiência; fluxo AppTest com `dados/rede-teste` em `tests/interface/test_pagina_eficiencia.py` |
| Desempenho | `benchmarks/resultados/f-efi-2-bhtrans.json` |
| Guia e relatório | `docs/GUIA.md` §5.5 e §10; `relatorio/secoes/F-EFI-2.tex` |
| Vídeo | Roteiro pronto; gravação pelo integrante |
| Integração | Revisão e merge pendentes |

Validação em 20/11: hook limpo e suíte completa com 878 testes aprovados.
Os três modos da página também foram executados via AppTest com o ZIP de BH;
o mapa, a tabela de desvios e os indicadores reproduziram os valores dos JSON.
As seções de ambas as features compilaram no relatório com Tectonic.

## Especificação

Contrato implementado.

- `isocrona(ge, origem, limite_s) -> dict[str, float]`. Os valores são tempos mínimos em segundos.
- `indices_desvio(rede, ge, tamanho_amostra, semente=0) -> list[DesvioPar]`. Cada par registra metros em linha reta e no percurso, segundos do trajeto rápido e quadrante da origem. As propriedades `desvio` e `min_por_km` tratam divisões indefinidas.
- `medias_por_quadrante(desvios) -> dict[str, float]`. Usa a média aritmética dos desvios definidos.

## Como funciona e por quê

A busca começa no vértice da parada, atravessa embarques, viagens, desembarques e
caminhadas, e descarta relaxamentos acima do limite inclusivo. Um dicionário
guarda apenas os vértices alcançados. Com V′ vértices e E′ arestas examinadas,
o custo é O((V′+E′) log(E′+2)) e o espaço é O(V′+E′) devido às reinserções no heap.

O Dijkstra de F-ROTA fornece o trajeto mais rápido do par. O índice divide a soma
das distâncias haversine entre as paradas de cada trecho pela distância direta
entre as pontas. A razão de tempo inclui caminhada e espera. Coordenadas
coincidentes e pares sem caminho ficam fora das razões. Os quadrantes da origem
são relativos ao centro da caixa das paradas ativas. Para m pares a busca custa
O(V+m(V+E) log(E+2)), com espaço O(V+E+m). Curvas das vias podem alongar o
percurso real além da aproximação por segmentos.

Diagrama: [atividade](../../diagramas/atividade-extensoes-eficiencia.png) e
[fonte PlantUML](../../diagramas/atividade-extensoes-eficiencia.puml).

## Perguntas de verificação

1. A origem entra na isócrona? Sim, quando ativa, com tempo zero.
2. Embarques somam distância? A espera afeta o tempo e a escolha da rota. Distância vem dos deslocamentos entre coordenadas.
3. Para quais pares o índice é indefinido? Pares sem caminho ou com distância direta zero.

## Resultados para o relatório

**Regerado em 20/11/2026 (vai para o relatório).** Feed oficial de 18/11 (SHA-256
`8cb0a498b90b227221d0234e3b6386a7dfbe375a2cb2e52e86238010be05f6d6`, serviço de 18/11/2026);
Intel Core i5-13600KF, Windows 11 (10.0.26200), Python 3.12.10; mesmo comando e parâmetros
(abaixo). JSON: `benchmarks/resultados/f-efi-2-bhtrans.json`. A leitura do ZIP fica fora das medições.

Para a parada 14788851 no pico da manhã, G_E tinha V=46.102 e E=209.025.
Em 15/30/45/60 min foram alcançadas 68/603/1.912/4.121 paradas. Com cinco
repetições, a isócrona de 60 min levou 55,18 ± 0,65 ms e o cálculo dos desvios
dos 12 pares levou 759,06 ± 9,00 ms (média e desvio amostral). O par de maior
desvio na amostra foi 14792221 → 14786004, com razão 1,548 (13,74 km percorridos para
8,88 km em linha reta) e 6,74 min/km. Os 12 pares sorteados mudaram em relação à medição
anterior porque o feed de 18/11 tem uma parada a mais.

Medição anterior (substituída): serviço de 04/11 em macOS arm64, Python 3.12.13; 68/603/1.911/4.120
paradas, isócrona 39,99 ± 0,58 ms, desvios 583,12 ± 11,40 ms, maior desvio 2,215
(14793286 → 14785528).

Comando sequencial que grava os JSON de ambas as features:

```sh
PYTHONPATH=src python benchmarks/medir_extensoes_eficiencia.py dados/brutos/bhtrans.zip --origem 14788851
```

## Roteiro do vídeo (30 s)

**0–10 s:** escolher Isócronas, parada 14788851 e pico da manhã. **10–20 s:** comparar o alcance aos 15 e 60 min. **20–30 s:** abrir Índice de desvio e explicar o primeiro par da tabela e a aproximação por segmentos.

## Definition of Done e pendências

- [x] Contratos, código, testes de corretude, interface, medição em BH e artefatos de documentação.
- [ ] Henrique revisa o PR e explica o resultado. Integração na main após aprovação.
- [ ] Gravar o trecho do vídeo.

## Timeline

- 29/10/2026: feature criada e atribuída a Arthur.
- 20/11/2026: Miguel assumiu a implementação no plano de finalização. Contratos registrados antes do código; testes, guia, relatório e benchmarking do GTFS de BH concluídos.
