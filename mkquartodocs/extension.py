from __future__ import annotations

from dataclasses import dataclass
import re
import enum
from typing import Final

from markdown import Markdown
from markdown.extensions import Extension
from markdown.extensions.admonition import AdmonitionProcessor
from markdown.extensions.md_in_html import MarkdownInHtmlExtension
from markdown.preprocessors import Preprocessor

from .logging import get_logger

log = get_logger(__name__)

CELL_REGEX: Final = re.compile(r"^(:{3,}) \{\.cell .*}\s*$")
CELL_END: Final = re.compile(r"^(:{3,})$")

# In theory it would be a 'cell-output' but there are other kinds of out
# Cells contain multiple cell elements.
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
        try:
            line = self.lines[cursor.line]
        except IndexError:
            breakpoint()
        # Return line content from the cursor column
        return line[cursor.col :]

    def _trim_line(
        self, line: str, start: Cursor | None = None, end: Cursor | None = None
    ) -> str:
        if start is None:
            start = Cursor(line=0, col=0)
        if end is None:
            end = Cursor(line=len(line), col=len(line))
        return line[start.col : end.col]

    def get_lines_content(self, start: Cursor, end: Cursor) -> list[str]:
        first = self._trim_line(self.lines[start.line], start=start, end=None)
        last = self._trim_line(self.lines[end.line], start=None, end=end)
        return [first] + self.lines[start.line + 1 : end.line] + [last]


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
            return self.line > (len(other.lines) - 1)
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
    def _from_cell_start_line(cls, line: str, line_number: int) -> BlockContext:
        """This function assumes that you already checked that the line matches CELL_REGEX"""
        sr = CELL_REGEX.search(line)
        grp = sr.groups()
        assert all(w == ":" for w in grp[0]), f"{grp[0]} should be :"
        return BlockContext(
            block_type=BlockType.CELL,
            delimiter=grp[0],
            attributes=grp[1:],
            start=Cursor(line=line_number, col=0),
            end=UnknownEnd(),
        )

    @classmethod
    def _from_cell_element_line(cls, line: str, line_number: int) -> BlockContext:
        """This function assumes that you already checked that the line matches CELL_ELEM_REGEX"""
        sr = cls.CELL_ELEM_REGEX.search(line)
        grp = sr.groups()
        breakpoint()
        return BlockContext(
            block_type=BlockType.CELL,
            delimiter=grp[0],
            attributes=grp[1:],
            start=Cursor(line=line_number, col=0),
            end=UnknownEnd(),
        )

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
            return BlockContext._from_cell_start_line(line, cursor.line)

        elif sr := CELL_ELEM_REGEX.search(line):
            grp = sr.groups()
            log.debug(f"Matched Cell element: {line}, groups: {grp}")
            return BlockContext._from_cell_element_line(line, cursor.line)

        elif sr := CODEBLOCK_REGEX.search(line):
            grp = sr.groups()
            log.debug(f"Matched codeblock: {line}, groups: {grp}")
            return BlockContext(
                block_type=BlockType.CODEBLOCK,
                delimiter=grp[0],
                attributes=grp[1:3],
                start=cursor,
                end=UnknownEnd(),
            )

        log.debug(f"No match for line: {line}")
        return None

    def find_inner_block(
        self, file_content: FileContent, context: list[BlockContext]
    ) -> BlockContext | None:
        cursor = self.start.copy()
        while cursor <= file_content:
            tmp = BlockContext.try_from_line(file_content, cursor, context=context)
            if tmp is not None:
                cursor = tmp.find_end(file_content, context)
                return tmp.with_end(end=cursor)
            cursor = cursor.advance_line(1)
        return None

    def with_end(self, end: Cursor | UnknownEnd) -> BlockContext:
        return BlockContext(
            block_type=self.block_type,
            delimiter=self.delimiter,
            attributes=self.attributes,
            start=self.start,
            end=end,
        )

    def find_end(
        self, file_content: FileContent, context: list[BlockContext]
    ) -> Cursor:
        if self.block_type == BlockType.CELL:
            return self._find_cell_end(file_content)
        elif self.block_type == BlockType.CODEBLOCK:
            return self._find_codeblock_end(file_content, context)
        elif self.block_type == BlockType.HTML:
            return self._find_html_end(file_content, context)
        raise NotImplementedError

    def _find_cell_end(self, file_content: FileContent) -> Cursor:
        local_cursor = self.start.copy()
        local_cursor = local_cursor.advance_line(1)
        local_regex = re.compile(f"^{self.delimiter}(\s|\n)?$")
        while local_cursor < file_content:
            line = file_content.get_line_content(local_cursor)
            if local_regex.match(line):
                log.debug(f"Matched Cell end: {line}")
                return local_cursor
            local_cursor = local_cursor.advance_line(1)

        breakpoint()
        raise RuntimeError(f"Failed to find end for cell {self}")

    def _find_html_end(
        self, file_content: FileContent, context: list[BlockContext]
    ) -> Cursor:
        raise NotImplementedError

    def _find_codeblock_end(self, file_content: FileContent) -> Cursor:
        local_cursor = self.start.copy()
        local_cursor = local_cursor.advance_line(1)
        local_regex = re.compile(f"^{self.delimiter}(\s|\n)?$")
        while local_cursor <= file_content:
            line = file_content.get_line_content(local_cursor)
            if local_regex.match(line):
                log.debug(f"Matched Codeblock end: {line}")
                return local_cursor
            local_cursor = local_cursor.advance_line(1)

        raise RuntimeError("Codeblock end without matching codeblock start")

    def into_output_lines(self, file_content: FileContent) -> list[str]:
        if self.end == UnknownEnd:
            raise ValueError("BlockContext has no end")

        elif self.block_type == BlockType.CELL:
            return self._into_output_lines_cell(file_content)

        elif self.block_type == BlockType.CODEBLOCK:
            return self._into_output_lines_codeblock(file_content)

        elif self.block_type == BlockType.HTML:
            return self._into_output_lines_html(file_content)

        raise NotImplementedError

    def _into_output_lines_cell(self, file_content: FileContent) -> list[str]:
        if isinstance(self.end, UnknownEnd):
            raise ValueError(f"BlockContext {self} has no end")
        out = []
        out.append("\n\n")
        out.extend(
            file_content.get_lines_content(
                self.start.advance_line(1), self.end.advance_line(-1)
            )
        )
        out.append("\n\n")
        return out

    def _into_output_lines_codeblock(
        self,
        file_content: FileContent,
        context: list[BlockContext],
    ) -> list[str]:
        out = []
        out.append("\n\n")

        tmp = self.find_inner_block(file_content, context=context)
        if tmp is not None:
            out.extend(tmp.into_output_lines(file_content))
        else:
            out.extend(
                file_content.get_lines_content(
                    self.start.advance_line(1), self.end.advance_line(-1)
                )
            )

        out.append("\n\n")
        return out


@dataclass
class HTMLContext:
    lines: list[str]
    start: Cursor
    end: Cursor


class AdmotionCellDataPreprocessor(Preprocessor):
    def run(self, lines):
        log.info(f"Running {self}")
        file_content = FileContent(lines)
        context = []
        outs = []

        cursor = Cursor(0, 0)
        while cursor < file_content:
            tmp = BlockContext.try_from_line(file_content, cursor, context=context)
            if tmp is not None:
                cursor = tmp.find_end(file_content, context)
                outs.extend(tmp.with_end(cursor).into_output_lines(file_content))
                context.append(tmp)

            else:
                line = file_content.get_line_content(cursor)
                outs.append(line)
                cursor = cursor.advance_line(1)

        return outs


class QuartoCellDataExtension(Extension):
    def extendMarkdown(self, md: Markdown) -> None:  # noqa: N802 (casing: parent method's name)
        """Register the extension.

        Adds an instance of the Processor to the Markdown instance.
            md: A `markdown.Markdown` instance.
        """
        md.registerExtension(self)
        md.preprocessors.register(
            AdmotionCellDataPreprocessor(),
            name="QuartoCellData",
            priority=106,  # Right before Admonition
        )
        md.parser.blockprocessors.register(
            AdmonitionProcessor(md.parser), "admonition", 105
        )
