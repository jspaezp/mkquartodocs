
for x in *.qmd ; do
  quarto render $x --to=markdown-simple_tables
done
