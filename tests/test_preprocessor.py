from mkquartodocs.extension import AdmotionCellDataPreprocessor
import os
from pathlib import Path
import pytest

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
