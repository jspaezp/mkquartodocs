---
title: This is a simple example that uses python
toc-title: Table of contents
---

You can take a look at the .qmd that generated this docs from:

<https://github.com/jspaezp/mkquartodocs/tree/main/docs>

But we can use python to check the contents of this file!

:::: {.cell execution_count="1"}
``` {.python .cell-code}
with open("example.qmd", "r") as f:
    for l in f:
        print("> ", str(l))
```

::: {.cell-output .cell-output-stdout}
    >  

    >  # This is a simple example that uses python

    >  

    >  You can take a look at the .qmd that generated this docs

    >  from:

    >  

    >  [https://github.com/jspaezp/mkquartodocs/tree/main/docs](https://github.com/jspaezp/mkquartodocs/tree/main/docs)

    >  

    >  

    >  But we can use python to check the contents of this file!

    >  

    >  ```{python}

    >  with open("example.qmd", "r") as f:

    >      for l in f:

    >          print("> ", str(l))

    >  

    >  ```

    >  

    >  

    >  # Hello

    >  

    >  Here is some text

    >  

    >  

    >  ```{python}

    >  print("Hello World")

    >  ```

    >  

    >  Here is how warnings look

    >  

    >  

    >  ```{python}

    >  import warnings

    >  warnings.warn("This is a warning")

    >  ```

    >  

    >  Some python logic

    >  

    >  

    >  ```{python}

    >  # Fizz buzz as a simple list comprehension

    >  out = ["Fizz"*(i%3==0)+"Buzz"*(i%5==0) or str(i) for i in range(1, 101)]

    >  print(out)

    >  ```

    >  

    >  And finally an error just to see how it looks

    >  

    >  

    >  ```{python}

    >  #| error: true

    >  raise NotImplementedError

    >  ```
:::
::::

# Hello

Here is some text

:::: {.cell execution_count="2"}
``` {.python .cell-code}
print("Hello World")
```

::: {.cell-output .cell-output-stdout}
    Hello World
:::
::::

Here is how warnings look

:::: {.cell execution_count="3"}
``` {.python .cell-code}
import warnings
warnings.warn("This is a warning")
```

::: {.cell-output .cell-output-stderr}
    /var/folders/42/tyvw22cj7t35kbjs0frhf_vw0000gp/T/ipykernel_26837/1338237052.py:2: UserWarning: This is a warning
      warnings.warn("This is a warning")
:::
::::

Some python logic

:::: {.cell execution_count="4"}
``` {.python .cell-code}
# Fizz buzz as a simple list comprehension
out = ["Fizz"*(i%3==0)+"Buzz"*(i%5==0) or str(i) for i in range(1, 101)]
print(out)
```

::: {.cell-output .cell-output-stdout}
    ['1', '2', 'Fizz', '4', 'Buzz', 'Fizz', '7', '8', 'Fizz', 'Buzz', '11', 'Fizz', '13', '14', 'FizzBuzz', '16', '17', 'Fizz', '19', 'Buzz', 'Fizz', '22', '23', 'Fizz', 'Buzz', '26', 'Fizz', '28', '29', 'FizzBuzz', '31', '32', 'Fizz', '34', 'Buzz', 'Fizz', '37', '38', 'Fizz', 'Buzz', '41', 'Fizz', '43', '44', 'FizzBuzz', '46', '47', 'Fizz', '49', 'Buzz', 'Fizz', '52', '53', 'Fizz', 'Buzz', '56', 'Fizz', '58', '59', 'FizzBuzz', '61', '62', 'Fizz', '64', 'Buzz', 'Fizz', '67', '68', 'Fizz', 'Buzz', '71', 'Fizz', '73', '74', 'FizzBuzz', '76', '77', 'Fizz', '79', 'Buzz', 'Fizz', '82', '83', 'Fizz', 'Buzz', '86', 'Fizz', '88', '89', 'FizzBuzz', '91', '92', 'Fizz', '94', 'Buzz', 'Fizz', '97', '98', 'Fizz', 'Buzz']
:::
::::

And finally an error just to see how it looks

:::: {.cell execution_count="5"}
``` {.python .cell-code}
raise NotImplementedError
```

::: {.cell-output .cell-output-error}
    NotImplementedError: 
    [0;31m---------------------------------------------------------------------------[0m
    [0;31mNotImplementedError[0m                       Traceback (most recent call last)
    Cell [0;32mIn[5], line 1[0m
    [0;32m----> 1[0m [38;5;28;01mraise[39;00m [38;5;167;01mNotImplementedError[39;00m

    [0;31mNotImplementedError[0m: 
:::
::::
