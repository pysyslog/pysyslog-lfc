"""pysyslog - asynchronous, flow-based log processor."""

from importlib import metadata


def __getattr__(name: str):
    if name == "__version__":
        try:
            return metadata.version("pysyslog")
        except metadata.PackageNotFoundError:  # pragma: no cover - fallback for local dev
            return "0.0.dev0"
    raise AttributeError(name)


__all__ = ["__version__"]
