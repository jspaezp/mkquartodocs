# Test: Multiple Output Types

Tests handling of cells with multiple different output types in sequence.

## Input Pattern

- Single cell with multiple outputs
- stdout output
- stderr output
- Regular text between cells

## Expected Transformation

- Multiple admonitions, one for each output type
- Correct admonition type for each (`note` for stdout, `warning` for stderr)
- Proper ordering preserved
