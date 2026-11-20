# F-EFI-OPC · Pico contra fora do pico

**Dono original:** Arthur (@ArthurkkLS). **Implementação de 20/11:** Miguel (@Miguelgdn1).
**Issue:** #23. **Classe:** opcional. **Visão:** G_E.

## Retomada

Implementação, ensaios, interface, material do guia, relatório e medição final
concluídos na branch de eficiência. Próximo passo: revisão de Henrique e
integração do PR na main. A gravação do trecho segue o roteiro abaixo.

## Critérios de aceite

- [x] RF-EFI-05 · Comparar eficiência e tempo médio entre as faixas de serviço.

## Status

| Camada | Evidência |
|---|---|
| Modelo e núcleo | `algoritmos/eficiencia.py` |
| Testes | `tests/algoritmos/test_extensoes_eficiencia.py`; gabarito manual, bordas e comparação das isócronas com NetworkX em dez grafos semeados |
| Interface | Página Eficiência; fluxo AppTest com `dados/rede-teste` em `tests/interface/test_pagina_eficiencia.py` |
| Desempenho | `benchmarks/resultados/f-efi-opc-bhtrans.json` |
| Guia e relatório | `docs/GUIA.md` §5.5 e §10; `relatorio/secoes/F-EFI-OPC.tex` |
| Vídeo | Roteiro pronto; gravação pelo integrante |
| Integração | Revisão e merge pendentes |

Validação em 20/11: hook limpo e suíte completa com 878 testes aprovados.
Os três modos da página também foram executados via AppTest com o ZIP de BH;
o mapa, a tabela de desvios e os indicadores reproduziram os valores dos JSON.
As seções de ambas as features compilaram no relatório com Tectonic.

## Especificação

Contrato implementado.

- `comparar_faixas(rede, tamanho_amostra, semente=0, params=None) -> list[IndicadoresFaixa]`. Retorna uma linha por faixa na ordem de `params.faixas`, com pares sorteados, alcançáveis, eficiência (1/s), tempo médio (s) e tamanho de G_E.

## Como funciona e por quê

O sorteio uniforme de pares ordenados distintos, sem reposição, acontece antes
do laço sobre as faixas. Assim, a comparação entre conjuntos alcançáveis reflete
a oferta, e não uma mudança de amostra. As esperas são as estimativas H/2 de
F-ESPERA. Para cada faixa, monta-se G_E e executa-se um Dijkstra por origem
distinta. Para k origens e m pares em F faixas, a busca custa
O(F·(construção de G_E + k(V+E) log(E+2)+m)). Apenas uma faixa é analisada por
vez, com O(V+E+m+F) de espaço além da construção e das estimativas. A eficiência
divide a soma de 1/t por todos os pares. O tempo médio divide a soma das durações
somente pelo número de pares alcançáveis, exibido na tabela. Sem pares sorteados
as duas estatísticas são ausentes. A tabela informa o erro padrão como em F-EFI,
com correção de população finita nas eficiências amostradas e com o subconjunto
alcançável nos tempos médios. São tempos programados, sem atrasos de trânsito.

Diagrama: [atividade](../../diagramas/atividade-extensoes-eficiencia.png) e
[fonte PlantUML](../../diagramas/atividade-extensoes-eficiencia.puml).

## Perguntas de verificação

1. Qual é a população? Pares ordenados de paradas distintas, sem plataformas nas pontas.
2. O que muda com a faixa? Serviço disponível e esperas aplicadas aos embarques.
3. Qual é a eficiência se nenhum par sorteado é alcançável? Zero para uma amostra não vazia; a duração média fica indefinida.

## Resultados para o relatório

**Regerado em 20/11/2026 (vai para o relatório).** Feed oficial de 18/11 (SHA-256
`8cb0a498b90b227221d0234e3b6386a7dfbe375a2cb2e52e86238010be05f6d6`, serviço de 18/11/2026);
Intel Core i5-13600KF, Windows 11 (10.0.26200), Python 3.12.10; mesmo comando e parâmetros
(abaixo). JSON: `benchmarks/resultados/f-efi-opc-bhtrans.json`.

Com 12 pares alcançáveis em cada faixa (semente 2026), o tempo médio foi 59,95 min no pico
da manhã, 62,96 no entrepico, 60,08 no pico da tarde e 66,03 à noite (erro padrão de 5,02 a
5,32 min). As eficiências foram 3,02/2,90/3,03/2,72 × 10⁻⁴ s⁻¹ (erro padrão de 0,24 a 0,29).
As diferenças entre faixas são da ordem de um erro padrão: com 12 pares, a amostra não distingue
as faixas. Cada visão teve 46.102 vértices e 209.025/207.274/208.619/206.937 arestas. O cálculo
das quatro faixas, incluindo construção e esperas, levou 4,250 ± 0,047 s em cinco repetições.

Medição anterior (substituída): serviço de 04/11 em macOS arm64, Python 3.12.13; tempos médios
57,48/60,66/58,50/62,36 min, eficiências 3,566/3,308/3,464/3,431 × 10⁻⁴ s⁻¹, 3,277 ± 0,066 s.

Comando sequencial que grava os JSON de ambas as features:

```sh
PYTHONPATH=src python benchmarks/medir_extensoes_eficiencia.py dados/brutos/bhtrans.zip --origem 14788851
```

## Roteiro do vídeo (30 s)

**0–10 s:** abrir Comparar faixas e fixar 12 pares e semente 2026. **10–20 s:** comparar o pico da manhã com a noite na tabela e nas barras. **20–30 s:** mostrar a coluna Alcançáveis e explicar os denominadores das duas médias.

## Definition of Done e pendências

- [x] Contratos, código, testes de corretude, interface, medição em BH e artefatos de documentação.
- [ ] Henrique revisa o PR e explica o resultado. Integração na main após aprovação.
- [ ] Gravar o trecho do vídeo.

## Timeline

- 29/10/2026: feature criada e atribuída a Arthur.
- 20/11/2026: Miguel assumiu a implementação no plano de finalização. Contratos registrados antes do código; testes, guia, relatório e benchmarking do GTFS de BH concluídos.
