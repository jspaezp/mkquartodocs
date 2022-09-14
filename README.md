# mkquartodocs

**Make gorgeous reproducible documentation with quarto and mkdocs**

It is a plugin for [mkdocs](https://www.mkdocs.org/) that renders
quarto markdown documents into github, so they are built with the
rest of the documentation.

### Why?

In many instances the documentation contains runnable code, and it
makes sense that you verify that the code runs and keep the output
of the code in sync with the current status of the document and
software packages involved.

**But mainly** I really got tired of manually rendering documents
and copying outpus.

## Usage

1. Install the dependencies: [Installation](#installation)
1. Add the plugin to your configuration: [Configuration](#configuration)
1. Add `.qmd` files to your `./docs/` directoy
1. Run `mkdocs build`

## Installation

1. Make sure you have quarto installed in your computer.

   - https://quarto.org/docs/get-started/

1. Install `mkquartodocs`

```shell
pip install placeholderBecauseItIsNotPublished
```

## Configuration

Add `mkquartodocs` to your plugins in your `mkdocs.yml`

```yaml
# Whatever is in your mkdocs.yml configuration file....
# ...

plugins:
  - mkquartodocs

```

Available configuration options:

- **quarto_path**: Specifies where to look for the quarto executable.
- **keep_out**: If true it will skip the cleanup step in the directory.

```yaml
# Whatever is in your mkdocs.yml configuration file....
# ...

plugins:
  - mkquartodocs:
    quarto_path: /home/my_folder/some/weird/place/to/have/executables/quarto
    keep_out: true

```

## Running

**NOTHING !!! you do not have to run it manually!!**

When you call `mkdocs build`, it should automatically find your `.qmd`
files, render them, generate the output and clean after itself.
