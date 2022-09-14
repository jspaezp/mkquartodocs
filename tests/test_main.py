from pathlib import Path

import pytest
from mkdocs import config
from mkdocs.commands import build

HERE = Path(__file__)
TEST_DATA = HERE.parent / "data"
doc_dirs = list(TEST_DATA.glob("docs_*"))


@pytest.mark.parametrize("doc_dir", doc_dirs, ids=[x.stem for x in doc_dirs])
def test_build(shared_datadir, doc_dir):
    doc_dir_base = shared_datadir / doc_dir.stem
    config_file = doc_dir_base / "mkdocs.yml"

    cfg = config.load_config(config_file=str(config_file))
    build.build(cfg)

    with open(doc_dir_base / "expected_output.txt") as f:
        for line in f:
            line = line.strip()
            if line and line[0] != "#":
                assert (doc_dir_base / line).exists()

    with open(doc_dir_base / "expected_missing.txt") as f:
        for line in f:
            line = line.strip()
            if line and line[0] != "#":
                assert not (doc_dir_base / line).exists()
