"""Plain text parser."""

from __future__ import annotations

from typing import Mapping, Optional

from ..components.base import Parser


class TextParser(Parser):
    """Wrap the raw message in a dictionary."""

    async def parse(self, message: str) -> Optional[Mapping[str, str]]:
        if message is None:
            return None
        return {"message": message.rstrip("\n")}
