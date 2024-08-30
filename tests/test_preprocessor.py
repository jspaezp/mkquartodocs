from mkquartodocs.extension import AdmotionCellDataPreprocessor

sample_cell_elements = [
    ':::: {.cell execution_count="1"}',
    "::: {.cell-output .cell-output-stdout}",
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
``` {.python .cell-code}
import warnings
warnings.warn("This is a warning")
```

!!! warning "stderr"
    ... UserWarning: This is a warning
      warnings.warn("This is a warning")
"""


def test_conversion():
    preprocessor = AdmotionCellDataPreprocessor()
    out = [preprocessor._process_line(x) for x in sample_cell_elements]
    assert out == [
        "\n\n",
        '!!! note "output"',
        "\n\n",
        "``` {.python .cell-code}",
        "```",
        "\n\n",
    ]


def test_conversion_file_chunk():
    preprocessor = AdmotionCellDataPreprocessor()
    file_lines = EXAMMPLE_INPUT_FILE.split("\n")
    out = [preprocessor._process_line(x) for x in file_lines]

    out_str = "\n".join(out)
    assert EXAMPLE_OUTPUT_FILE.strip() == out_str.strip()
