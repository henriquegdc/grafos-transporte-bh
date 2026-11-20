# F-ESPERA-OPC · Sensibilidade ao intervalo

Miguel · issue #20 · RF-ESP-06 · G_E.

## Retomada e status

Em 20/11, o cenário de alteração de uma linha foi implementado na página Espera,
validado pelo gabarito, por NetworkX e pelo AppTest. O benchmark em BH, o guia
(§5.2 e §10), o relatório e o roteiro estão prontos para revisão. Faltam a aprovação
de outro integrante, a integração e a gravação do grupo.

## Contrato e critérios de aceite

Contrato implementado em `src/transporte/simulacao/espera.py`:
`sensibilidade_intervalo(rede, linha, faixa, fator, pares, semente, params=None)`.
O retorno traz por padrão a espera original e alternativa em segundos, os pares sorteados
com ambos os tempos e as dimensões de G_E.

- [x] RF-ESP-06: alterar o intervalo de uma linha e apresentar efeitos tanto na espera como nos trajetos.
- [x] Comparar os mesmos pares, conservar as esperas das outras linhas e distinguir pares inacessíveis.
- [x] Interface, testes, complexidade, guia, relatório, resultados e roteiro.
- [ ] Revisão e integração na main.

## Como funciona e por quê

A tabela de intervalos ganha uma cópia. Só os valores estimáveis dos padrões da
linha e faixa selecionadas recebem o fator; cada tabela é convertida em H/2.
Os dois grafos permitem que a rota ótima mude. Uma linha sem estimativa na faixa
gera aviso na página. Padrões com uma única partida conservam a espera provisória.
Cada par ordenado distinto tem a mesma chance de entrar na amostra, sem reposição.
A consulta custa duas construções de G_E mais até 2n Dijkstras para n pares.
O espaço auxiliar é O(V+E+n) além das tabelas. Diagrama: `docs/diagramas/atividade-sensibilidade.puml`.

## Perguntas de verificação

1. Por que usar os mesmos pares? Para isolar o efeito do intervalo.
2. O que dobra com o fator dois? A espera H/2 dos padrões estimáveis selecionados.
3. Quando o trajeto pode mudar de linha? Quando o novo custo de embarque faz outra rota chegar antes.

## Resultados e reprodução

```sh
PYTHONPATH=src .venv/bin/python benchmarks/medir_sensibilidade.py dados/brutos/bhtrans.zip
sh .githooks/pre-commit
.venv/bin/python -m pytest -q
```

`benchmarks/resultados/sensibilidade-bhtrans.json` registra o serviço de 04/11,
linha 561787, pico da manhã, dez pares e semente 42. A espera no padrão passou
de 566,67 s a 1.133,33 s. Em macOS arm64 e Python 3.12.13, V=46.100 e E=208.956,
a comparação completa levou 1,504 ± 0,085 s em cinco repetições.

## Vídeo · 30 s

Selecionar **Simular alteração do intervalo de uma linha**, escolher a linha e a faixa,
dobrar o intervalo e clicar em **Comparar cenários**. Ler os dois valores de espera.
Na tabela seguinte, apontar um par e explicar por que mudar uma única linha pode
preservar o melhor tempo entre aquelas duas paradas.

## Timeline

- 29/10: criação e atribuição a Miguel.
- 11/11: adiamento para priorizar a entrega essencial.
- 20/11: implementação, medição serial, testes e preparação para revisão e gravação.
