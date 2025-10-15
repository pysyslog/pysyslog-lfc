"""Component registry and auto-discovery."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Dict, Mapping, Type

from .base import Filter, InputDriver, Output, OutputFormat, Parser

ComponentFactory = Callable[[Mapping[str, Any]], Any]


class ComponentRegistry:
    """Dynamic registry used to resolve component names."""

    def __init__(self) -> None:
        self._inputs: Dict[str, Type[InputDriver]] = {}
        self._parsers: Dict[str, Type[Parser]] = {}
        self._filters: Dict[str, Type[Filter]] = {}
        self._outputs: Dict[str, Type[Output]] = {}
        self._formats: Dict[str, Type[OutputFormat]] = {}
        self._register_builtin()

    def register_input(self, name: str, cls: Type[InputDriver]) -> None:
        self._inputs[name] = cls

    def register_parser(self, name: str, cls: Type[Parser]) -> None:
        self._parsers[name] = cls

    def register_filter(self, name: str, cls: Type[Filter]) -> None:
        self._filters[name] = cls

    def register_output(self, name: str, cls: Type[Output]) -> None:
        self._outputs[name] = cls

    def register_format(self, name: str, cls: Type[OutputFormat]) -> None:
        self._formats[name] = cls

    def create_input(self, type_name: str, options: Mapping[str, Any]) -> InputDriver:
        return self._create(type_name, options, self._inputs, "input")

    def create_parser(self, type_name: str, options: Mapping[str, Any]) -> Parser:
        return self._create(type_name, options, self._parsers, "parser")

    def create_filter(self, type_name: str, options: Mapping[str, Any]) -> Filter:
        return self._create(type_name, options, self._filters, "filter")

    def create_output(self, type_name: str, options: Mapping[str, Any]) -> Output:
        return self._create(type_name, options, self._outputs, "output")

    def create_format(self, type_name: str, options: Mapping[str, Any]) -> OutputFormat:
        return self._create(type_name, options, self._formats, "format")

    def available_formats(self) -> Mapping[str, Type[OutputFormat]]:
        return dict(self._formats)

    def _create(
        self,
        type_name: str,
        options: Mapping[str, Any],
        registry: Mapping[str, Type[Any]],
        kind: str,
    ) -> Any:
        if type_name not in registry:
            raise KeyError(f"Unknown {kind} type '{type_name}'")
        return registry[type_name](options)

    def _register_builtin(self) -> None:
        for name, path in BUILTIN_INPUTS.items():
            self.register_input(name, _load_class(path))
        for name, path in BUILTIN_PARSERS.items():
            self.register_parser(name, _load_class(path))
        for name, path in BUILTIN_FILTERS.items():
            self.register_filter(name, _load_class(path))
        for name, path in BUILTIN_OUTPUTS.items():
            self.register_output(name, _load_class(path))
        for name, path in BUILTIN_FORMATS.items():
            self.register_format(name, _load_class(path))


def _load_class(path: str):
    module_name, class_name = path.split(":", 1)
    module = import_module(module_name)
    return getattr(module, class_name)


BUILTIN_INPUTS = {
    "memory": "pysyslog.inputs.memory:MemoryInput",
}

BUILTIN_PARSERS = {
    "json": "pysyslog.parsers.json:JsonParser",
    "text": "pysyslog.parsers.text:TextParser",
}

BUILTIN_FILTERS = {
    "field": "pysyslog.filters.field:FieldFilter",
}

BUILTIN_OUTPUTS = {
    "stdout": "pysyslog.outputs.stdout:StdoutOutput",
    "memory": "pysyslog.outputs.memory:MemoryOutput",
}

BUILTIN_FORMATS = {
    "json": "pysyslog.formats.json:JsonFormat",
    "text": "pysyslog.formats.text:TextFormat",
}
