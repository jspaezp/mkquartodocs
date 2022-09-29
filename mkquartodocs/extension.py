import re

from markdown import Markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

from .logging import get_logger

log = get_logger(__name__)
CELL_REGEX = re.compile(r"::: {\.cell .*}\s*$")

# TODO: implement ways to actually use the information ...


class RemoveCellDataPreprocessor(Preprocessor):
    def run(self, lines):
        log.info("Running RemoveCellDataPreprocessor")
        matches = [CELL_REGEX.match(x) for x in lines]
        log.debug(f"Removing {sum(1 for x in matches if x)} lines")
        out = [x for x, y in zip(lines, matches) if not y]
        return out


class QuartoCellDataExtension(Extension):
    def extendMarkdown(
        self, md: Markdown
    ) -> None:  # noqa: N802 (casing: parent method's name)
        """Register the extension.

        Adds an instance of the Processor to the Markdown instance.
            md: A `markdown.Markdown` instance.
        """
        md.preprocessors.register(
            RemoveCellDataPreprocessor(),
            "QuatoCellData",
            priority=75,  # Right before markdown.blockprocessors.HashHeaderProcessor
        )
