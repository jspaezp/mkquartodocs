---
pagetitle: encoding_options
toc-title: Table of contents
---

# Encodings to tensors

When getting the data into your model, you usually will have to process
it to some form of structured numeric input.

There is a plethora fo ways to encode information. And I will show a
couple (and how to get them using ms2ml)

## Encoding Peptides

::: {.cell execution_count="1"}
``` {.python .cell-code}
import numpy as np
from ms2ml.peptide import Peptide

p = Peptide.from_sequence("MYPEPTIDE")
print(p)
```

::: {.cell-output .cell-output-stdout}
    Peptide.from_sequence(MYPEPTIDE)
:::

::: {.cell-output .cell-output-stderr}
    /Users/sebastianpaez/git/ms2ml/ms2ml/config.py:195: UserWarning: Using default config. Consider creating your own.
      warnings.warn("Using default config. Consider creating your own.", UserWarning)
:::