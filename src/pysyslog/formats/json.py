"""JSON output format."""

from __future__ import annotations

import json
from typing import Any, Mapping

from ..components.base import OutputFormat


class JsonFormat(OutputFormat):
    """Serialize records using :func:`json.dumps`."""

    def __init__(self, config):
        super().__init__(config)
        self._indent = self.config.get("indent")
        if self._indent is not None:
            self._indent = int(self._indent)
        self._sort_keys = self.config.get("sort_keys", "false").lower() in {"1", "true", "yes"}

    async def format(self, record: Mapping[str, Any]) -> str:
        return json.dumps(record, indent=self._indent, sort_keys=self._sort_keys)
