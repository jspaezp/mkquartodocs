# Test: Cell with stdout output

Tests that Quarto cells with stdout output are transformed into MkDocs Material admonitions correctly.

## Input Pattern

- Cell wrapper with execution count: `:::: {.cell execution_count="1"}`
- Python code block: ``` {.python .cell-code}
- Cell output with stdout: `::: {.cell-output .cell-output-stdout}`

## Expected Transformation

- Code block with language highlighting (```python)
- `???+ note "output"` admonition for stdout
- Indented output content (4 spaces)
- All cell wrapper syntax removed
