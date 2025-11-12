from pathlib import Path
from dataclasses import dataclass, field
import fnmatch
import re

import pytest
import yaml
from mkdocs import config
from mkdocs.commands import build

HERE = Path(__file__)
TEST_DATA = HERE.parent / "data"
doc_dirs = list(TEST_DATA.glob("docs_*"))


@dataclass
class _TestConfig:
    """Configuration for integration tests.

    Supports both new YAML format (test_config.yml) and legacy format
    (expected_output.txt / expected_missing.txt).
    """

    files_must_exist: list[str] = field(default_factory=list)
    files_must_not_exist: list[str] = field(default_factory=list)
    snapshots: list[str] = field(default_factory=list)
    normalize: list[dict] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, config_file: Path) -> "_TestConfig":
        """Load test configuration from YAML file.

        Falls back to legacy format if test_config.yml doesn't exist.
        """
        if not config_file.exists():
            return cls.from_legacy(config_file.parent)

        with open(config_file) as f:
            data = yaml.safe_load(f) or {}

        return cls(
            files_must_exist=data.get("files_must_exist", []),
            files_must_not_exist=data.get("files_must_not_exist", []),
            snapshots=data.get("snapshots", []),
            normalize=data.get("normalize", []),
        )

    @classmethod
    def from_legacy(cls, test_dir: Path) -> "_TestConfig":
        """Load from legacy expected_output.txt / expected_missing.txt."""
        must_exist = []
        must_not_exist = []

        output_file = test_dir / "expected_output.txt"
        if output_file.exists():
            must_exist = [
                line.strip()
                for line in output_file.read_text().splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]

        missing_file = test_dir / "expected_missing.txt"
        if missing_file.exists():
            must_not_exist = [
                line.strip()
                for line in missing_file.read_text().splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]

        return cls(
            files_must_exist=must_exist,
            files_must_not_exist=must_not_exist,
            snapshots=[],  # No snapshots for legacy tests
            normalize=[],
        )

    def should_snapshot(self, rel_path: str) -> bool:
        """Determine if a file should be snapshotted.

        Patterns starting with ! are exclusions.
        """
        included = False

        for pattern in self.snapshots:
            # Exclusion pattern (starts with !)
            if pattern.startswith("!"):
                if fnmatch.fnmatch(rel_path, pattern[1:]):
                    return False
            # Inclusion pattern
            elif fnmatch.fnmatch(rel_path, pattern):
                included = True

        return included

    def normalize_content(self, content: str, rel_path: str) -> str:
        """Apply normalization rules to content before snapshotting."""
        for rule in self.normalize:
            pattern = rule.get("pattern", "**/*")
            if fnmatch.fnmatch(rel_path, pattern):
                regex_pattern = rule.get("regex")
                replace_str = rule.get("replace", "")
                content = re.sub(regex_pattern, replace_str, content)
        return content


@pytest.mark.parametrize("doc_dir", doc_dirs, ids=[x.stem for x in doc_dirs])
def test_build(shared_datadir, doc_dir, snapshot):
    """Integration test for full MkDocs build process.

    Supports two configuration formats:
    1. New format: test_config.yml (with snapshot support)
    2. Legacy format: expected_output.txt + expected_missing.txt
    """
    doc_dir_base = shared_datadir / doc_dir.stem
    config_file = doc_dir_base / "mkdocs.yml"

    # Load test configuration (YAML or legacy)
    test_config = _TestConfig.from_yaml(doc_dir_base / "test_config.yml")

    # Build the docs
    cfg = config.load_config(config_file=str(config_file))
    build.build(cfg)

    # 1. Verify files that must exist
    not_found = []
    for expected_file in test_config.files_must_exist:
        if not (doc_dir_base / expected_file).exists():
            not_found.append(expected_file)

    if not_found:
        files = [str(x.relative_to(doc_dir_base)) for x in doc_dir_base.rglob("*")]
        msg = "Files expected but not found:\n > "
        msg += "\n > ".join(not_found)
        msg += "\n\nFiles found:\n" + "\n".join(files)
        raise ValueError(msg)

    # 2. Verify files that must NOT exist
    for unexpected_file in test_config.files_must_not_exist:
        assert not (
            doc_dir_base / unexpected_file
        ).exists(), f"{unexpected_file} should not exist"

    # 3. Snapshot testing (if configured)
    if test_config.snapshots:
        snapshot_files = {}
        for file_path in doc_dir_base.rglob("*"):
            if not file_path.is_file():
                continue

            rel_path = str(file_path.relative_to(doc_dir_base))
            if test_config.should_snapshot(rel_path):
                try:
                    content = file_path.read_text()
                    content = test_config.normalize_content(content, rel_path)
                    snapshot_files[rel_path] = content
                except UnicodeDecodeError:
                    # Skip binary files
                    pass

        # Snapshot the dictionary of file contents
        assert snapshot_files == snapshot(name=doc_dir.stem)
