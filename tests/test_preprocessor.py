from mkquartodocs.extension import AdmotionCellDataPreprocessor
import os
from pathlib import Path
import pytest

# Preprocessor snapshot tests
PREPROCESSOR_SNAPSHOT_DIR = Path(__file__).parent / "preprocessor_snapshots"
snapshot_test_cases = [
    d
    for d in PREPROCESSOR_SNAPSHOT_DIR.glob("*")
    if d.is_dir() and (d / "input.md").exists()
]

sample_cell_elements = [
    ':::: {.cell execution_count="1"}',
    "::: {.cell-output .cell-output-stdout}",
    "::: ",
    ":::: ",
    ':::: {.cell execution_count="3"}',
    "``` {.python .cell-code}",
    "```",
    "::::",
]

# Tests from quarto version 1.5.56
# Rendered with --to=markdown

EXAMMPLE_INPUT_FILE = """
:::: {.cell execution_count="3"}
``` {.python .cell-code}
import warnings
warnings.warn("This is a warning")
```

::: {.cell-output .cell-output-stderr}
    ... UserWarning: This is a warning
      warnings.warn("This is a warning")
:::
::::
"""

EXAMPLE_OUTPUT_FILE = """
```python
import warnings
warnings.warn("This is a warning")

```



???+ warning "stderr"

        ... UserWarning: This is a warning
          warnings.warn("This is a warning")
"""


def test_conversion():
    preprocessor = AdmotionCellDataPreprocessor()
    out = preprocessor.run(sample_cell_elements)
    # Right now I write a lot of ... unnecessary
    # newlines to be safe but I could trim it ...
    assert out == [
        '???+ note "output"',
        "",
        "",
        "",
        "",
        "```python",
        "```",
        "",
        "",
    ]


def test_conversion_file_chunk():
    preprocessor = AdmotionCellDataPreprocessor()
    file_lines = EXAMMPLE_INPUT_FILE.split("\n")
    out = preprocessor.run(file_lines)

    out_str = "\n".join(out)
    are_equal = EXAMPLE_OUTPUT_FILE.strip() == out_str.strip()
    if not are_equal:
        msg = "Files do not match"
        if os.getenv("MKQUARTODOCS_TEST_DEBUG_OUT_DIR"):
            out_dir = Path(os.getenv("MKQUARTODOCS_TEST_DEBUG_OUT_DIR"))
            out_dir.mkdir(exist_ok=True)
            msg += f", Output written to {out_dir}"
            with open(out_dir / "expected_output.txt", "w") as f:
                f.write(EXAMPLE_OUTPUT_FILE)
            with open(out_dir / "actual_output.txt", "w") as f:
                f.write(out_str)
        else:
            msg += ", For extra information set MKQUARTODOCS_TEST_DEBUG_OUT_DIR=1"
        raise AssertionError(msg)


HERE = Path(__file__)
TEST_DATA = HERE.parent / "test_preprocessor"
documents = list(TEST_DATA.glob("*.md"))


@pytest.mark.parametrize("document", documents, ids=[x.stem for x in documents])
def test_conversion_file(document):
    input_lines = document.read_text().split("\n")
    out_file = document.with_name(document.name + ".md.postprocessed")
    out_lines = out_file.read_text().split("\n")
    preprocessor = AdmotionCellDataPreprocessor()

    out = preprocessor.run(input_lines)
    are_equal = out_lines == out
    if not are_equal:
        msg = "Files do not match"
        if os.getenv("MKQUARTODOCS_TEST_DEBUG_OUT_DIR"):
            filestem = document.stem
            out_dir = Path(os.getenv("MKQUARTODOCS_TEST_DEBUG_OUT_DIR"))
            out_dir.mkdir(exist_ok=True)
            msg += f", Output written to {out_dir}"
            with open(out_dir / f"{filestem}_expected_output.txt", "w") as f:
                f.write("\n".join(out_lines))
            with open(out_dir / f"{filestem}_actual_output.txt", "w") as f:
                f.write("\n".join(out))
        else:
            msg += ", For extra information set MKQUARTODOCS_TEST_DEBUG_OUT_DIR=1"
        raise AssertionError(msg)


@pytest.mark.parametrize(
    "test_case", snapshot_test_cases, ids=[t.name for t in snapshot_test_cases]
)
def test_preprocessor_snapshot(test_case: Path, snapshot):
    """Snapshot test for preprocessor transformations.

    Each test case directory contains:
    - input.md: Raw Quarto-rendered markdown to be processed
    - README.md: Documentation explaining what the test validates
    - __snapshots__/: Auto-generated snapshots (created by syrupy)

    To update snapshots after intentional changes:
        pytest tests/test_preprocessor.py::test_preprocessor_snapshot --snapshot-update
    """
    input_file = test_case / "input.md"
    assert input_file.exists(), f"Missing input.md in {test_case.name}"

    # Read and process input
    input_lines = input_file.read_text().splitlines()
    preprocessor = AdmotionCellDataPreprocessor()
    output_lines = preprocessor.run(input_lines)

    # Snapshot the output as a single string
    output_text = "\n".join(output_lines)
    assert output_text == snapshot(name=test_case.name)


def test_issue69_mkdocstrings_syntax():
    """Test that mkdocstrings syntax (::: prefix) is allowed.

    This is issue #69: https://github.com/jspaezp/mkquartodocs/issues/69
    The preprocessor should allow mkdocstrings syntax (which doesn't match
    Quarto cell patterns) to pass through unchanged.
    """
    preprocessor = AdmotionCellDataPreprocessor()

    # Markdown with mkdocstrings syntax
    mkdocstrings_input = [
        "# API Documentation",
        "",
        "::: foo.main.hello",
        "",
        "This uses mkdocstrings syntax.",
        "",
        "::: another.module.function",
    ]

    # This should NOT raise an error - mkdocstrings syntax should pass through
    output = preprocessor.run(mkdocstrings_input)

    # The mkdocstrings lines should be preserved unchanged
    assert "::: foo.main.hello" in output
    assert "::: another.module.function" in output

    # Verify the output structure is preserved
    assert len([line for line in output if line.startswith(":::")]) == 2
