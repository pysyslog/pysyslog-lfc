"""Filter records using common field comparisons."""

from __future__ import annotations

import operator
import re
from typing import Any, Mapping

from ..components.base import Filter


OPERATORS = {
    "eq": operator.eq,
    "ne": operator.ne,
    "gt": operator.gt,
    "ge": operator.ge,
    "lt": operator.lt,
    "le": operator.le,
    "contains": lambda value, candidate: candidate in value if value is not None else False,
}


class FieldFilter(Filter):
    """Filter records using configurable comparisons."""

    def __init__(self, config):
        super().__init__(config)
        self.field = self.config.get("field")
        if not self.field:
            raise ValueError("FieldFilter requires a 'field' option")
        self.op_name = self.config.get("op", "eq")
        if self.op_name not in OPERATORS and self.op_name != "regex":
            raise ValueError(f"Unsupported filter operator '{self.op_name}'")
        self.expected = self.config.get("value")
        self.regex = None
        if self.op_name == "regex":
            pattern = self.config.get("pattern") or self.expected
            if not pattern:
                raise ValueError("regex filter requires 'pattern' or 'value'")
            self.regex = re.compile(pattern)
        self.stage = self.config.get("stage", "parser")

    async def allow(self, record: Mapping[str, Any]) -> bool:
        value = record.get(self.field)
        if self.op_name == "regex":
            if value is None:
                return False
            return bool(self.regex.search(str(value)))
        comparator = OPERATORS[self.op_name]
        candidate = self._convert(self.expected, type(value))
        return comparator(value, candidate)

    def _convert(self, raw: Any, target_type: type) -> Any:
        if raw is None:
            return None
        if target_type in (int, float):
            return target_type(raw)
        if target_type is bool:
            return str(raw).lower() in {"1", "true", "yes"}
        return raw
