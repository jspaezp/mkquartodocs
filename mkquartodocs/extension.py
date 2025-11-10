from __future__ import annotations

from dataclasses import dataclass
import re
import enum
from typing import Final

from markdown import Markdown
from markdown.extensions import Extension
from markdown.extensions.admonition import AdmonitionProcessor
from markdown.extensions.md_in_html import (
    HtmlBlockPreprocessor,
    MarkdownInHtmlProcessor,
    MarkdownInHTMLPostprocessor,
)
from markdown.preprocessors import Preprocessor

# Installed as pymdown-extensions
from pymdownx.details import DetailsProcessor

from .logging import get_logger

log = get_logger(__name__)

# `:::: {.cell execution_count="1"}`
# `:::::: {.cell layout-align="default"}` <-  happens in mermaid diagrams
CELL_REGEX: Final = re.compile(r"^(:{3,}) \{\.cell .*}\s*$")
CELL_END: Final = re.compile(r"^(:{3,})$")

# In theory it would be a 'cell-output' but there are other kinds of out
# Cells contain multiple cell elements.
# `::: {.cell-output .cell-output-stdout}`
CELL_ELEM_REGEX: Final = re.compile(
    r"^(:{3,}) \{(.cell-\w+)\s?(\.cell-[\w-]+)?( execution_count=\"\d+\")?\}$"
)
# `::::: cell-output-display`
CELL_ELEM_ALT_REGEX: Final = re.compile(r"^(:{3,})\s*(cell-output-display\s*)$")

# ``` {.python .cell-code}
CODEBLOCK_REGEX: Final = re.compile(r"^(`{3,})\s?{\.(\w+) .*}")

# mkdocstrings syntax normalization:
# Quarto wraps markdown divs (including mkdocstrings `::: module.path` syntax)
# in extra colons when rendering nested structures. For example:
#   Source .qmd: `::: pathlib.Path`
#   Quarto output: `::::: pathlib.Path` (5 colons instead of 3)
# mkdocstrings expects exactly 3 colons, so we need to normalize any colon-fences
# that don't match Quarto cell patterns back to 3 colons.
# This regex matches lines with 3+ colons that aren't Quarto cell syntax:
# - Matches: `::::: module.path` (mkdocstrings), `:::::` (closing fence)
# - Doesn't match: `:::: {.cell ...}` (has braces), handled by other regexes
MKDOCSTRINGS_NORMALIZE_REGEX: Final = re.compile(r"^(:{3,})(\s+(?!{).*)?$")

# https://squidfunk.github.io/mkdocs-material/reference/admonitions/#supported-types
# ???+ means a collapsable block rendered open by default
TYPE_MAPPING: Final = {
    ".cell-output-stdout": '???+ note "output"',
    ".cell-output-stderr": '???+ warning "stderr"',
    ".cell-output-error": '???+ danger "error"',
    ".cell-output-display": '???+ note "Display"',
    "cell-output-display": "???+ note",
}


class BlockType(enum.Enum):
    CELL = "cell"
    CELL_ELEM = "cell_elem"
    CODEBLOCK = "codeblock"
    HTML = "html"


LINE_BLOCKS = [BlockType.CELL, BlockType.CODEBLOCK, BlockType.CELL_ELEM]
LINECOL_BLOCKS = [BlockType.HTML]


@dataclass(slots=True, frozen=True)
class UnknownEnd:
    pass


@dataclass(slots=True, frozen=True)
class FileContent:
    lines: list[str]

    def get_line_content(self, cursor: Cursor) -> str:
        line = self.lines[cursor.line]
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
        # TODO ... this is an off-by 1 error nightmare ...
        # Some unit testing might be really worth it ...
        if start == end:
            return []

        if start.line == end.line:
            return [self._trim_line(self.lines[start.line], start=start, end=end)]

        first = self._trim_line(self.lines[start.line], start=start, end=None)
        last = self._trim_line(self.lines[end.line + 1], start=None, end=end)
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

    def __post_init__(self):
        log.debug(f"BlockContext: {self}")

    def get_content(self, file_content: FileContent) -> str:
        return file_content.get_lines_content(self.start, self.end)

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
        sr = CELL_ELEM_REGEX.search(line)
        grp = sr.groups()
        return BlockContext(
            block_type=BlockType.CELL_ELEM,
            delimiter=grp[0],
            attributes=grp[1:],
            start=Cursor(line=line_number, col=0),
            end=UnknownEnd(),
        )

    @classmethod
    def _from_cell_element_line_alt(cls, line: str, line_number: int) -> BlockContext:
        """This function assumes that you already checked that the line matches CELL_ELEM_ALT_REGEX"""
        sr = CELL_ELEM_ALT_REGEX.search(line)
        grp = sr.groups()
        return BlockContext(
            block_type=BlockType.CELL_ELEM,
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

        elif sr := CELL_ELEM_ALT_REGEX.search(line):
            log.debug(f"Matched Cell element alternative: {line}")
            return BlockContext._from_cell_element_line_alt(line, cursor.line)

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
        self,
        file_content: FileContent,
        context: list[BlockContext],
        start: Cursor,
    ) -> BlockContext | None:
        cursor = start.copy()
        while cursor < self.end:
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
            return self.__find_delimited_end(file_content)
        elif self.block_type == BlockType.CODEBLOCK:
            return self.__find_delimited_end(file_content)
        elif self.block_type == BlockType.CELL_ELEM:
            return self.__find_delimited_end(file_content)
        elif self.block_type == BlockType.HTML:
            return self._find_html_end(file_content, context)
        raise NotImplementedError

    def __find_delimited_end(self, file_content: FileContent) -> Cursor:
        local_cursor = self.start.copy()
        local_cursor = local_cursor.advance_line(1)

        local_regex = re.compile(rf"^{self.delimiter}(\s|\n)?$")
        while local_cursor < file_content:
            line = file_content.get_line_content(local_cursor)
            if local_regex.match(line):
                log.debug(f"Matched {self.block_type} end: {line}")
                out = Cursor(local_cursor.line, len(line) + 1)
                return out
            local_cursor = local_cursor.advance_line(1)

        raise RuntimeError(f"Failed to find end for {self}")

    def _find_html_end(
        self, file_content: FileContent, context: list[BlockContext]
    ) -> Cursor:
        raise NotImplementedError

    def into_output_lines(self, file_content: FileContent) -> list[str]:
        out = None
        if self.end == UnknownEnd:
            raise ValueError("BlockContext has no end")

        elif self.block_type == BlockType.CELL:
            out = self._into_output_lines_cell(file_content)

        elif self.block_type == BlockType.CELL_ELEM:
            out = self._into_output_lines_cell_elem(file_content)

        elif self.block_type == BlockType.CODEBLOCK:
            out = self._into_output_lines_codeblock(file_content)

        elif self.block_type == BlockType.HTML:
            out = self._into_output_lines_html(file_content)

        if out is None:
            raise NotImplementedError(
                f"Building output for type {self.block_type} not implemented"
            )

        if any(line.startswith(":::") for line in out):
            bads_i = [i for i, line in enumerate(out) if line.startswith(":::")]
            show = [
                f"{i}: {line}"
                for i, line in enumerate(out)
                if any(abs(i - w) < 3 for w in bads_i)
            ]
            show = "\n" + "\n".join(show)
            msg = f"BlockContext {self} contains starting :::, which is not allowed: {show}"
            raise RuntimeError(msg)

        return out

    def _into_output_lines_cell(self, file_content: FileContent) -> list[str]:
        if isinstance(self.end, UnknownEnd):
            raise ValueError(f"BlockContext {self} has no end")
        out = []
        last_end = self.start.advance_line(1)
        tmp = self.find_inner_block(file_content, context=[], start=last_end)
        while tmp is not None:
            inter = file_content.get_lines_content(last_end, tmp.start)
            inner = tmp.into_output_lines(file_content)
            out.extend(inter)
            out.extend(inner)
            last_end = tmp.end
            tmp = self.find_inner_block(file_content, context=[], start=last_end)

        out.extend(file_content.get_lines_content(last_end, self.end.advance_line(-1)))

        return out

    def _into_output_lines_cell_elem(self, file_content: FileContent) -> list[str]:
        if isinstance(self.end, UnknownEnd):
            raise ValueError(f"BlockContext {self} has no end")

        out = []
        admon_candidates = [
            TYPE_MAPPING[k] for k in self.attributes if k in TYPE_MAPPING
        ]
        if not len(admon_candidates):
            raise ValueError(
                f"Could not map attributes {self.attributes} to admonition type"
            )

        out.append(admon_candidates[0])
        out.append("")

        internal = []
        last_end = self.start.advance_line(1)
        # Do special handing of <div>
        # This whole branch is kind of ugly tbh ..
        # I should move it to its own "kind" of block
        if "div" in file_content.get_line_content(last_end):
            internal = file_content.get_lines_content(
                last_end, self.end.advance_line(0)
            )
            # if the first line is a starting div tag and the last non-empty is a
            # closing div tag, then we just add the
            # markdown in html attribute and leave as is.
            non_empty = [line for line in internal if line.strip()]
            if internal[0].startswith("<div>") and non_empty[-1].endswith("</div>"):
                if "style" in internal[1]:
                    internal[0] = '<div markdown="block">'

                last_end = self.end

        else:
            tmp = self.find_inner_block(file_content, context=[], start=last_end)
            while tmp is not None:
                inter = file_content.get_lines_content(last_end, tmp.start)
                inner = tmp.into_output_lines(file_content)
                internal.extend(inter)
                internal.extend(inner)
                last_end = tmp.end
                tmp = self.find_inner_block(file_content, context=[], start=last_end)

        internal.extend(
            file_content.get_lines_content(last_end, self.end.advance_line(0))
        )
        out.extend([" " * 4 + line for line in internal])
        out.append("")

        return out

    def _into_output_lines_codeblock(
        self,
        file_content: FileContent,
    ) -> list[str]:
        if isinstance(self.end, UnknownEnd):
            raise ValueError(f"BlockContext {self} has no end")
        out = []
        language = ""
        if self.attributes:
            language = self.attributes[0]
        out.append(f"{self.delimiter}{language}")

        last_end = self.start.advance_line(1)
        tmp = self.find_inner_block(file_content, context=[], start=last_end)
        while tmp is not None:
            out.extend(file_content.get_lines_content(last_end, tmp.start))
            out.extend(tmp.into_output_lines(file_content))
            last_end = tmp.end
            tmp = self.find_inner_block(file_content, context=[], start=last_end)

        out.extend(file_content.get_lines_content(last_end, self.end.advance_line(0)))
        out.append(f"{self.delimiter}")
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
                # Normalize mkdocstrings syntax that Quarto wrapped in extra colons
                # This only affects lines that didn't match any Quarto block patterns
                if match := MKDOCSTRINGS_NORMALIZE_REGEX.match(line):
                    # Double-check this isn't a Quarto pattern (shouldn't be, but be safe)
                    if not (
                        CELL_REGEX.match(line)
                        or CELL_ELEM_REGEX.match(line)
                        or CELL_ELEM_ALT_REGEX.match(line)
                    ):
                        rest = match.group(2) or ""
                        line = ":::" + rest
                        log.debug(
                            f"Normalized mkdocstrings: {match.group(0).strip()!r} -> {line.strip()!r}"
                        )
                outs.append(line)
                cursor = cursor.advance_line(1)

        if any(x.startswith(":::") for x in outs):
            # Check if these are unprocessed Quarto cell blocks (which would be a bug)
            # vs. mkdocstrings syntax or other valid uses of ::: (which should be allowed)
            potential_bugs = []
            for x in outs:
                if x.startswith(":::"):
                    # Check if it looks like Quarto cell syntax that escaped processing
                    if (
                        CELL_REGEX.match(x)
                        or CELL_ELEM_REGEX.match(x)
                        or CELL_ELEM_ALT_REGEX.match(x)
                    ):
                        potential_bugs.append(x)

            if potential_bugs:
                raise ValueError(
                    f"Unprocessed Quarto cell syntax found: {potential_bugs}"
                )
        return outs


class QuartoCellDataExtension(Extension):
    def extendMarkdown(
        self,
        md: Markdown,
    ) -> None:  # noqa: N802 (casing: parent method's name)
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
        md.parser.blockprocessors.register(
            DetailsProcessor(md.parser),
            "details",
            104,
        )

        # essentially re-impement MarkdownInHtmlExtension
        # Replace raw HTML preprocessor
        md.preprocessors.register(HtmlBlockPreprocessor(md), "html_block", 20)
        # Add `blockprocessor` which handles the placeholders for `etree` elements
        md.parser.blockprocessors.register(
            MarkdownInHtmlProcessor(md.parser), "markdown_block", 105
        )
        # Replace raw HTML postprocessor
        md.postprocessors.register(MarkdownInHTMLPostprocessor(md), "raw_html", 30)
