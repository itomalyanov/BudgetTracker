from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any


class CategoryTaxonomy:
    """Loads a category taxonomy where each top-level group's value is either
    a leaf name (str), a flat list of leaves, or a dict of subgroup -> (list | dict | str),
    nested arbitrarily deep.
    """

    def __init__(self, raw: dict[str, Any]) -> None:
        self._rows: list[tuple[str, str | None, str]] = []
        self._group_for_leaf: dict[str, str] = {}
        for top_group, value in raw.items():
            self._flatten(top_group, None, value)

    def _flatten(self, top_group: str, subgroup: str | None, value: Any) -> None:
        if isinstance(value, str):
            self._add(top_group, subgroup, value)
        elif isinstance(value, list):
            for leaf in value:
                self._add(top_group, subgroup, leaf)
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                self._flatten(top_group, sub_key, sub_value)
        else:
            raise TypeError(f"Unsupported category value for {top_group!r}: {value!r}")

    def _add(self, top_group: str, subgroup: str | None, leaf: str) -> None:
        self._rows.append((top_group, subgroup, leaf))
        self._group_for_leaf[leaf] = top_group

    @classmethod
    def from_json(cls, path: str | Path) -> CategoryTaxonomy:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(raw)

    @classmethod
    def default(cls) -> CategoryTaxonomy:
        source = resources.files("budget_tracker") / "data" / "categories.json"
        raw = json.loads(source.read_text(encoding="utf-8"))
        return cls(raw)

    def leaf_names(self) -> set[str]:
        return set(self._group_for_leaf)

    def group_for_leaf(self, leaf: str) -> str | None:
        return self._group_for_leaf.get(leaf)

    def is_known_category(self, name: str) -> bool:
        return name in self._group_for_leaf

    def as_rows(self) -> list[tuple[str, str | None, str]]:
        return list(self._rows)
