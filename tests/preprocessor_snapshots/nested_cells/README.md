# Test: Nested Cell Structures

Tests that nested cell structures (cell containing cell elements) are processed correctly.

## Input Pattern

- Outer cell wrapper: `:::: {.cell execution_count="1"}`
- Code block inside: ``` {.python .cell-code}
- Multiple nested cell outputs
- Both stdout and display outputs

## Expected Transformation

- Each cell element transformed independently
- Proper nesting maintained through indentation
- Multiple admonitions for multiple outputs
