# Relatório SBC

Integrador: Rafael (P0-AVAL). Estrutura, donos e orçamento de páginas:
`docs/fontes/plano-de-projeto.md` §14.1. Limite: 12 a 15 páginas.

## Onde escrever

| Arquivo | Seção | Dono |
|---|---|---|
| `secoes/introducao.tex` | 1. Introdução | Henrique |
| `secoes/fundamentacao.tex` | 2. Fundamentação | Thiago e Henrique |
| `secoes/dados.tex` | 3. Dados | Miguel |
| `secoes/modelagem.tex` | 4. Modelagem | Henrique |
| `secoes/plano.tex` | 5. Plano de desenvolvimento | Henrique |
| `secoes/implementacao.tex` | 6. Implementação | Thiago e Arthur |
| `secoes/<ID>.tex` (ex.: `secoes/F-ROTA.tex`) | 7. Funcionalidades: uma subseção por feature | Dono da feature |
| `secoes/avaliacao.tex` | 8. Avaliação de desempenho | Rafael |
| `secoes/conclusao.tex` | 9. Limitações e conclusão | Caio |
| `secoes/responsabilidades.tex` | 10. Responsabilidades | Rafael |
| `referencias.bib` | Referências | Rafael (qualquer um acrescenta) |

- **Seção de feature:** crie `secoes/<ID>.tex` começando com `\subsection{Título}\label{sec:<ID>}`.
  Ela entra sozinha em `secoes/funcionalidades.tex`; não precisa editar outro arquivo. Traga uma
  figura, o resultado medido, a complexidade e uma limitação.
- **Figuras** em `figuras/`; referencie só pelo nome (`\includegraphics{rota-exemplo}`).
- **Texto pendente:** `\pendente{...}` sai em cinza no PDF. A versão entregue não pode ter nenhum.
- **Números:** só de execução real, com o comando registrado no arquivo da feature (AGENTS.md §5).
- `sbc-template.sty` e `sbc.bst` são o template oficial da SBC
  (<https://www.sbc.org.br/wp-content/uploads/2024/07/modelosparapublicaodeartigos.zip>), sem alterações.

## Compilar

Precisa de uma distribuição LaTeX: MiKTeX no Windows (`winget install MiKTeX.MiKTeX`, com
instalação automática de pacotes ligada) ou TeX Live no Linux/macOS. Dentro de `relatorio/`:

```text
latexmk
```

O `.latexmkrc` gera tudo em `relatorio/build/` (fora do Git) e o PDF em `build/main.pdf`. Sem
`latexmk` (ele precisa de Perl), a sequência manual é:

```text
pdflatex -output-directory=build main
bibtex build/main
pdflatex -output-directory=build main
pdflatex -output-directory=build main
```

O Overleaf serve só para visualizar; o texto é editado aqui, para os commits contarem.
O PDF final é versionado só na entrega, como `relatorio/relatorio.pdf`.
