import re
from typing import Final

from markdown import Markdown
from markdown.extensions import Extension
from markdown.extensions.admonition import AdmonitionProcessor
from markdown.preprocessors import Preprocessor

from .logging import get_logger

log = get_logger(__name__)

# TODO: implement ways to actually use the information ...


class AdmotionCellDataPreprocessor(Preprocessor):

    CELL_REGEX: Final = re.compile(r"^::: \{\.cell .*}\s*$")
    CELL_END: Final = re.compile(r"^:::$")
    CELL_ELEM_REGEX: Final = re.compile(
        r"^::: \{(.cell-\w+) (\.cell-[\w-]+)( execution_count=\"\d+\")?\}$"
    )
    CODEBLOCK_REGEX: Final = re.compile(r"^```{\.(\w+) .*}")

    # https://squidfunk.github.io/mkdocs-material/reference/admonitions/#supported-types
    TYPE_MAPPING: Final = {
        ".cell-output-stdout": '!!! note "output"',
        ".cell-output-stderr": '!!! warning "stderr"',
        ".cell-output-error": '!!! danger "error"',
        ".cell-output-display": '!!! note "Display"',
    }

    def run(self, lines):
        log.info(f"Running {self}")
        outs = [self._process_line(x) for x in lines]
        log.debug(f"Removing {sum(1 for x in outs if x is None)} lines")
        out = [x for x in outs if x is not None]

        return out

    def _process_line(self, line):
        if sr := self.CELL_REGEX.search(line):
            log.debug(f"Matched Cell start: {line}")
            out = "\n\n"

        elif sr := self.CELL_END.search(line):
            log.debug(f"Matched Cell end: {line}")
            out = "\n\n"

        elif sr := self.CELL_ELEM_REGEX.search(line):
            log.debug(f"Matched Cell element: {line}")
            output_type = sr.groups()[1]
            out = self.TYPE_MAPPING[output_type]

        elif sr := self.CODEBLOCK_REGEX.search(line):
            log.debug(f"Matched codeblock: {line}")
            lang = sr.groups(1)
            out = f"```{lang}"
        else:
            out = line

        if line != out:
            log.debug(f"Transformed {line} -> {out}")
        return out


# TODO consider implemeting this ...
# class CellBLockProcessor(BlockProcessor):


class QuartoCellDataExtension(Extension):
    def extendMarkdown(
        self, md: Markdown
    ) -> None:  # noqa: N802 (casing: parent method's name)
        """Register the extension.

        Adds an instance of the Processor to the Markdown instance.
            md: A `markdown.Markdown` instance.
        """
        md.registerExtension(self)
        md.preprocessors.register(
            AdmotionCellDataPreprocessor(),
            name="QuatoCellData",
            priority=106,  # Right before Admonition
        )
        md.parser.blockprocessors.register(
            AdmonitionProcessor(md.parser), "admonition", 105
        )
