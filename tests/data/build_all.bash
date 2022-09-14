
set -x
set -e

for i in $PWD/docs_* ; do
  cd $i
  python -m mkdocs build
  find . > actual_output.txt
done
