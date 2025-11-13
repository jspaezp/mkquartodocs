
# This script is meant to be run from the root of the repository

uv export --format requirements.txt -o requirements.txt --no-emit-workspace --group check --group check_mkdocstrings
docker build --platform=linux/amd64 -t mkquartodocs-test:local -f tests/Dockerfile.test .
# --progress=plain
docker run --rm -t mkquartodocs-test:local
# To update snapshots, run the container with an overridden command:
# docker run --rm -t mkquartodocs-test:local pytest tests -vv --update-snapshots
