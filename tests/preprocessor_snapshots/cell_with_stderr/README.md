# Test: Cell with stderr output

Tests that Quarto cells with stderr/warning output are transformed into warning admonitions.

## Input Pattern

- Cell wrapper with execution count
- Python code block generating a warning
- Cell output with stderr: `::: {.cell-output .cell-output-stderr}`

## Expected Transformation

- Code block with language highlighting
- `???+ warning "stderr"` admonition for stderr output
- Indented stderr content (4 spaces)
