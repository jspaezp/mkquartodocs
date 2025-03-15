from __future__ import annotations

from dataclasses import dataclass
import re
import enum
from typing import Final

from markdown import Markdown
from markdown.extensions import Extension
from markdown.extensions.admonition import AdmonitionProcessor
from markdown.preprocessors import Preprocessor

from .logging import get_logger

log = get_logger(__name__)

CELL_REGEX: Final = re.compile(r"^(:{3,}) \{\.cell .*}\s*$")
CELL_END: Final = re.compile(r"^(:{3,})$")
CELL_ELEM_REGEX: Final = re.compile(
    r"^(:{3,}) \{(.cell-\w+)\s?(\.cell-[\w-]+)?( execution_count=\"\d+\")?\}$"
)
CODEBLOCK_REGEX: Final = re.compile(r"^(`{3,}){\.(\w+) .*}")

# https://squidfunk.github.io/mkdocs-material/reference/admonitions/#supported-types
TYPE_MAPPING: Final = {
    ".cell-output-stdout": '!!! note "output"',
    ".cell-output-stderr": '!!! warning "stderr"',
    ".cell-output-error": '!!! danger "error"',
    ".cell-output-display": '!!! note "Display"',
}


class BlockType(enum.Enum):
    CELL = "cell"
    CODEBLOCK = "codeblock"
    HTML = "html"

LINE_BLOCKS = [BlockType.CELL, BlockType.CODEBLOCK]
LINECOL_BLOCKS = [BlockType.HTML]

@dataclass(slots=True, frozen=True)
class UnknownEnd:
    pass


@dataclass(slots=True, frozen=True)
class FileContent:
    lines: list[str]

    def get_line_content(self, cursor: Cursor) -> str:
        line = self.lines[cursor.line]
        # Return line content from the cursor column
        return line[cursor.col :]


@dataclass(slots=True, frozen=True)
class Cursor:
    line: int
    col: int

    def __gt__(self, other: Cursor | FileContent) -> bool:
        if isinstance(other, Cursor):
            return self.line > other.line or (
                self.line == other.line and self.col > other.col
            )
        elif isinstance(other, FileContent):
            return self.line > other.line
        else:
            raise ValueError(f"Cannot compare Cursor with {type(other)}")

    def __lt__(self, other: Cursor | FileContent) -> bool:
        return not self.__gt__(other)

    def advance_line(self, lines: int = 1) -> Cursor:
        return Cursor(self.line + lines, 0)
    
    def advance_col(self, cols: int) -> Cursor:
        return Cursor(self.line, self.col + cols)

    def copy(self) -> Cursor:
        return Cursor(self.line, self.col)


@dataclass
class BlockContext:
    block_type: BlockType
    delimiter: str
    attributes: list[str]
    start: Cursor
    end: Cursor | UnknownEnd

    @classmethod
    def from_cell_start_line(cls, line: str) -> BlockContext:
        pass
        


    @classmethod
    def try_from_line(
        cls,
        file_content: FileContent,
        cursor: Cursor,
        context: list[BlockContext],
    ) -> BlockContext | None:
        line = file_content.get_line_content(cursor)
        if sr := CELL_REGEX.search(line):
            log.debug(f"Matched Cell start: {line}")
            return BlockContext.from_cell_start_line(line)


        elif sr := self.CELL_ELEM_REGEX.search(line):
            grp = sr.groups()
            log.debug(f"Matched Cell element: {line}, groups: {grp}")
            breakpoint()
            output_type = grp[2]
            out = self.TYPE_MAPPING[output_type]

        elif sr := self.CODEBLOCK_REGEX.search(line):
            grp = sr.groups()
            log.debug(f"Matched codeblock: {line}, groups: {grp}")
            lang = grp[2]
            nesting_level = len(grp[1])
            out = f"{'`' * nesting_level}{lang}"
        raise NotImplementedError

    def with_end(self, end: Cursor | UnknownEnd) -> BlockContext:
        return BlockContext(
            block_type=self.block_type,
            delimiter=self.delimiter,
            attributes=self.attributes,
            start=self.start,
            end=end,
        )

    def find_end(self, file_content: FileContent, context: list[BlockContext]) -> Cursor:

        if sr := CELL_END.search(line):
            log.debug(f"Matched Cell end: {line}")
            if not context[-1].block_type == BlockType.CELL:
                raise ValueError("Cell end without matching cell start")
            self.nesting_state.pop()
            out = "\n\n"
        raise NotImplementedError

    def _find_linewise_end(self, file_content: FileContent, context: list[BlockContext]) -> tuple[Cursor, list[BlockContext]]:
        local_cursor = self.start.copy()
        local_cursor = local_cursor.advance_line(1)
        while local_cursor <= file_content:
            line = file_content.get_line_content(local_cursor)
            if sr := CELL_END.search(line):
                log.debug(f"Matched Cell end: {line}")
                if not context[-1].block_type == BlockType.CELL:
                    raise ValueError("Cell end without matching cell start")
                context.pop()
                return local_cursor, context
            local_cursor = local_cursor.advance_line(1)
        raise NotImplementedError

    def into_output_lines(self, file_content: FileContent) -> list[str]:
        if self.end == UnknownEnd:
            raise ValueError("BlockContext has no end")

        

        raise NotImplementedError


@dataclass
class HTMLContext:
    lines: list[str]
    start: Cursor
    end: Cursor


class AdmotionCellDataPreprocessor(Preprocessor):
    def run(self, lines):
        log.info(f"Running {self}")
        file_content = FileContent(lines)
        nesting_state = []
        outs = []

        cursor = Cursor(0, 0)
        while cursor <= file_content:
            line = file_content.get_line_content(cursor)
            # Check if it starts anything
            # If so, find the end of the block
            #     process the block
            #     add to outs
            # If not process the line

        outs = [self._process_line(x) for x in lines]
        log.debug(f"Removing {sum(1 for x in outs if x is None)} lines")
        out = [x for x in outs if x is not None]

        return out

    def _process_line(self, line):
        else:
            out = line

        if line != out:
            log.debug(f"Transformed {line} -> {out}")
        return out

    def process_cell(self, lines):
        pass

    def process_codeblock(self, lines):
        pass

    def find_closing_html(self, lines, start, tag: str):
        pass

    def process_html(self, context: HTMLContext, parents: list[BlockContext]):
        pass


# TODO consider implemeting this ...
# class CellBLockProcessor(BlockProcessor):


class QuartoCellDataExtension(Extension):
    def extendMarkdown(self, md: Markdown) -> None:  # noqa: N802 (casing: parent method's name)
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
