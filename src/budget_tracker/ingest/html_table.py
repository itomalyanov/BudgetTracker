from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path


class _TableExtractor(HTMLParser):
    """Extracts <table> rows as plain text cells, expanding `colspan` with
    empty-string padding so column indices stay aligned with the header row.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._table_stack: list[list[list[str]]] = []
        self._current_row: list[str] | None = None
        self._in_cell = False
        self._cell_parts: list[str] = []
        self._cell_colspan = 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if tag == "table":
            table: list[list[str]] = []
            self.tables.append(table)
            self._table_stack.append(table)
        elif tag == "tr" and self._table_stack:
            self._current_row = []
            self._table_stack[-1].append(self._current_row)
        elif tag in ("td", "th") and self._current_row is not None:
            self._in_cell = True
            self._cell_parts = []
            try:
                self._cell_colspan = max(1, int(attr_map.get("colspan") or 1))
            except ValueError:
                self._cell_colspan = 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._in_cell:
            text = " ".join("".join(self._cell_parts).split())
            assert self._current_row is not None
            self._current_row.append(text)
            self._current_row.extend([""] * (self._cell_colspan - 1))
            self._in_cell = False
        elif tag == "table" and self._table_stack:
            self._table_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_parts.append(data)


def parse_html_tables(path: str | Path) -> list[list[list[str]]]:
    """Parses every <table> in an HTML document into rows of plain-text cells."""
    content = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    parser = _TableExtractor()
    parser.feed(content)
    return parser.tables
