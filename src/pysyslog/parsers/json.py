"""JSON parser."""

from __future__ import annotations

import json
from typing import Any, Mapping, Optional

from ..components.base import Parser


class JsonParser(Parser):
    """Parse each input line as JSON."""

    def __init__(self, config):
        super().__init__(config)
        self._allow_null = self.config.get("allow_null", "false").lower() in {"1", "true", "yes"}

    async def parse(self, message: str) -> Optional[Mapping[str, Any]]:
        if not message and not self._allow_null:
            return None
        return json.loads(message)
