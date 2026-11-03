# Configuração do latexmk para o relatório (ver relatorio/README.md).
$pdf_mode = 1;
$out_dir = 'build';
@default_files = ('main.tex');
# O bibtex roda dentro de build/; estes caminhos o fazem achar referencias.bib e sbc.bst.
ensure_path('BIBINPUTS', '..', '.');
ensure_path('BSTINPUTS', '..', '.');
