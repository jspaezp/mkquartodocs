---
toc-title: Table of contents
---

![Pypi
version](https://img.shields.io/pypi/v/mkquartodocs?style=flat-square.png)
![Pypi
Downloads](https://img.shields.io/pypi/dm/mkquartodocs?style=flat-square.png)
![Github
Activity](https://img.shields.io/github/last-commit/jspaezp/mkquartodocs?style=flat-square.png)
![Python
versions](https://img.shields.io/pypi/pyversions/mkquartodocs?style=flat-square.png)
![GitHub
Actions](https://img.shields.io/github/workflow/status/jspaezp/mkquartodocs/CI%20Testing/release?style=flat-square.png)
![License](https://img.shields.io/pypi/l/mkquartodocs?style=flat-square.png)

# mkquartodocs

![Example](readme_assets/gif.gif "Example")

**Make gorgeous reproducible documentation with quarto and mkdocs**

It is a plugin for [mkdocs](https://www.mkdocs.org/) that renders
[quarto](https://quarto.org) markdown documents into github, so they are
built with the rest of the documentation.

### Why?

In many instances the documentation contains runnable code, and it makes
sense that you verify that the code runs and keep the output of the code
in sync with the current status of the document and software packages
involved.

**But mainly** I really got tired of manually rendering documents and
copying outpus.

## Usage

1.  Install the dependencies: [Installation](#installation)
2.  Add the plugin to your configuration:
    [Configuration](#configuration)
3.  Add `.qmd` files to your `./docs/` directoy
4.  Run `mkdocs build`

This will render code chunks and save the outputs! Check out
https://quarto.org/ for more examples on how to use the format.

This ....

```` markdown

```{python}
print(1+2)
```
````

Will become this ...

:::: {.cell execution_count="1"}
``` {.python .cell-code}
print(1+2)
```

::: {.cell-output .cell-output-stdout}
    3
:::
::::

## Installation

1.  Make sure you have quarto installed in your computer.

    -   https://quarto.org/docs/get-started/

2.  Install `mkquartodocs`

``` shell
pip install mkquartodocs
```

## Configuration

Add `mkquartodocs` to your plugins in your `mkdocs.yml`

``` yaml
# Whatever is in your mkdocs.yml configuration file....
# ...

plugins:
  - mkquartodocs
```

Available configuration options:

-   **quarto_path**: Specifies where to look for the quarto executable.
-   **keep_output**: If true it will skip the cleanup step in the
    directory.
-   **ignore**: a python regular expressions that if matched will mark
    the file to not be rendered. Note that they need to be full matches

``` yaml
# Whatever is in your mkdocs.yml configuration file....
# ...

plugins:
  - mkquartodocs:
      quarto_path: /home/my_folder/some/weird/place/to/have/executables/quarto
      keep_output: true
      ignore: (.*broken.*.qmd)|(.*page[0-9].qmd)
```

## Running

**NOTHING !!! you do not have to run it manually!!**

When you call `mkdocs build`, it should automatically find your `.qmd`
files, render them, generate the output and clean after itself.

# TODO

The things that need to/could be added to the project:

-   [ ] quarto project support
-   [ ] render in temporary directory, posibly with a 'safe' argument
-   [ ] addition of files not in the docs directory, 'include' argument
-   [ ] add readme to testing data
-   [ ] move
    `INFO     -  mkquartodocs: Running RemoveCellDataPreprocessor` to
    debug log
