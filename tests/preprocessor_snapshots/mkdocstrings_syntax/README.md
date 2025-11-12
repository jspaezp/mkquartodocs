# Test: mkdocstrings Syntax (Issue #69)

Tests that mkdocstrings syntax (`::: module.path`) passes through unchanged and doesn't trigger ValueError.

## Input Pattern

- Plain markdown text
- Lines with `::: module.path` syntax (no curly braces)
- No Quarto cell blocks

## Expected Behavior

- mkdocstrings syntax preserved unchanged
- No ValueError raised
- No transformation of `::: module.path` lines

## Related

- GitHub Issue: #69
- Fix: mkquartodocs/extension.py:436-452
