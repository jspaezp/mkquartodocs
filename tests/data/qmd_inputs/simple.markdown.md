---
pagetitle: simple
toc-title: Table of contents
---

# Hello

Here is some text

::: {.cell execution_count="1"}
``` {.python .cell-code}
print("Hello World")

import warnings

warnings.warn("This is a warning")

raise NotImplementedError
```

::: {.cell-output .cell-output-stdout}
    Hello World
:::

::: {.cell-output .cell-output-stderr}
    /var/folders/5j/x2qvf77j1m7736lccs2xt6c40000gn/T/ipykernel_10621/3924225401.py:5: UserWarning: This is a warning
      warnings.warn("This is a warning")
:::

::: {.cell-output .cell-output-error}
    NotImplementedError: 
:::
:::

Some other text

::: {.cell execution_count="2"}
``` {.python .cell-code}
print("Hello World2")

import warnings

warnings.warn("This is a warning")

raise NotImplementedError
```

::: {.cell-output .cell-output-stdout}
    Hello World2
:::

::: {.cell-output .cell-output-stderr}
    /var/folders/5j/x2qvf77j1m7736lccs2xt6c40000gn/T/ipykernel_10621/3538506256.py:5: UserWarning: This is a warning
      warnings.warn("This is a warning")
:::

::: {.cell-output .cell-output-error}
    NotImplementedError: 
:::
:::
