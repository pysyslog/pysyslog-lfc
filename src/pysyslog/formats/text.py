"""Plain text output format."""

from __future__ import annotations

from typing import Mapping

from ..components.base import OutputFormat


class TextFormat(OutputFormat):
    """Render records using :py:meth:`str.format`."""

    def __init__(self, config):
        super().__init__(config)
        self._template = self.config.get("template", "{message}")

    async def format(self, record: Mapping[str, object]) -> str:
        return self._template.format(**record)
