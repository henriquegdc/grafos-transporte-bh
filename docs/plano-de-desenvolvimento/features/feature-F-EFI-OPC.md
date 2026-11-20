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

Feed BHTrans de serviço 04/11/2026 (SHA-256 e máquina completos no JSON).
Máquina macOS 26.6.2 arm64, Python 3.12.13. A leitura do ZIP fica fora das medições.

Com 12 pares alcançáveis em cada faixa, o tempo médio foi 57,48 min no pico
da manhã, 60,66 no entrepico, 58,50 no pico da tarde e 62,36 à noite. As eficiências
foram 3,566/3,308/3,464/3,431 × 10⁻⁴ s⁻¹, respectivamente. Cada visão teve
46.100 vértices e 208.956/207.205/208.550/206.868 arestas. O cálculo das quatro
faixas, incluindo construção e esperas, levou 3,277 ± 0,066 s em cinco repetições.

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
