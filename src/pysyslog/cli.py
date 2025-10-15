"""Command line entry point for pysyslog."""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Iterable, Optional

from .config import ConfigLoader
from .runtime import Runtime


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Asynchronous flow-based log processor")
    parser.add_argument(
        "-c",
        "--config",
        default="/etc/pysyslog/main.ini",
        help="Path to the configuration file",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Root logging level (default: INFO)",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    loader = ConfigLoader(base_dir=Path(args.config).parent)
    config = loader.load(args.config)
    runtime = Runtime(config)

    try:
        asyncio.run(runtime.run_forever())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Interrupted, shutting down")
        return 130
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
