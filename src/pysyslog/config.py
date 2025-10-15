"""Configuration loading and validation for pysyslog."""

from __future__ import annotations

import configparser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Mapping, Optional


class ConfigError(ValueError):
    """Raised when a configuration file cannot be parsed."""


@dataclass(slots=True)
class ComponentConfig:
    """Runtime description of a component declared in the INI file."""

    type: str
    options: Mapping[str, str] = field(default_factory=dict)

    def option(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.options.get(name, default)


@dataclass(slots=True)
class FilterConfig:
    """Representation of a filter component in a flow."""

    name: str
    component: ComponentConfig
    stage: str = "parser"


@dataclass(slots=True)
class ChannelConfig:
    """Definition of a reliability queue."""

    name: str
    maxsize: int = 1000
    ack_timeout: float = 30.0
    retry_limit: int = 3


@dataclass(slots=True)
class FlowConfig:
    """Definition of a flow pipeline."""

    name: str
    input: ComponentConfig
    parser: ComponentConfig
    output: ComponentConfig
    output_format: Optional[str] = None
    format_options: Mapping[str, str] = field(default_factory=dict)
    channel: Optional[str] = None
    filters: List[FilterConfig] = field(default_factory=list)


@dataclass(slots=True)
class RuntimeConfig:
    """Root configuration returned by :func:`ConfigLoader.load`."""

    flows: List[FlowConfig]
    channels: Dict[str, ChannelConfig]
    settings: Mapping[str, str]

    def get_flow(self, name: str) -> FlowConfig:
        for flow in self.flows:
            if flow.name == name:
                return flow
        raise KeyError(name)

    def get_channel(self, name: str) -> ChannelConfig:
        return self.channels[name]


class ConfigLoader:
    """Load configuration from INI files while preserving backwards compatibility."""

    def __init__(self, *, base_dir: Optional[Path] = None) -> None:
        self._base_dir = Path(base_dir) if base_dir else None

    def load(self, path: Path | str) -> RuntimeConfig:
        parser = self._new_parser()
        files = parser.read(path)
        if not files:
            raise ConfigError(f"Unable to read configuration file {path!s}")

        root_dir = Path(path).parent if self._base_dir is None else self._base_dir
        self._load_includes(parser, root_dir)
        return self._parse(parser)

    def loads(self, text: str) -> RuntimeConfig:
        parser = self._new_parser()
        parser.read_string(text)
        return self._parse(parser)

    def _new_parser(self) -> configparser.ConfigParser:
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        return parser

    def _load_includes(self, parser: configparser.ConfigParser, root_dir: Path) -> None:
        if parser.has_section("use") and parser.has_option("use", "include"):
            pattern = parser.get("use", "include")
            for include in sorted(root_dir.glob(pattern)):
                parser.read(include)

    def _parse(self, parser: configparser.ConfigParser) -> RuntimeConfig:
        channels = self._parse_channels(parser)
        flows, channels = self._parse_flows(parser, channels)
        settings = dict(parser["settings"]) if parser.has_section("settings") else {}
        if not flows:
            raise ConfigError("No flow sections were defined in the configuration")
        return RuntimeConfig(flows=flows, channels=channels, settings=settings)

    def _parse_channels(
        self, parser: configparser.ConfigParser
    ) -> Dict[str, ChannelConfig]:
        channels: Dict[str, ChannelConfig] = {}
        for section in parser.sections():
            if not section.startswith("channel."):
                continue
            name = section.split(".", 1)[1]
            cfg = parser[section]
            try:
                maxsize = int(cfg.get("maxsize", 1000))
                ack_timeout = float(cfg.get("ack_timeout", 30.0))
                retry_limit = int(cfg.get("retry_limit", 3))
            except ValueError as exc:  # pragma: no cover - defensive
                raise ConfigError(f"Invalid numeric value in [{section}]: {exc}") from exc
            channels[name] = ChannelConfig(
                name=name,
                maxsize=maxsize,
                ack_timeout=ack_timeout,
                retry_limit=retry_limit,
            )
        return channels

    def _parse_flows(
        self,
        parser: configparser.ConfigParser,
        channels: Mapping[str, ChannelConfig],
    ) -> tuple[List[FlowConfig], Dict[str, ChannelConfig]]:
        flows: List[FlowConfig] = []
        known_channels = dict(channels)
        for section in parser.sections():
            if not section.startswith("flow."):
                continue
            name = section.split(".", 1)[1]
            cfg = parser[section]
            input_cfg = self._component_from_section(cfg, "input", section)
            parser_cfg = self._component_from_section(cfg, "parser", section)
            output_cfg = self._component_from_section(cfg, "output", section)
            output_format = cfg.get("output.format")
            format_options = {
                option[len("format.") :]: value
                for option, value in cfg.items()
                if option.startswith("format.")
            }
            channel_name = cfg.get("channel") or cfg.get("channel.name")
            if channel_name and channel_name not in known_channels:
                known_channels[channel_name] = ChannelConfig(name=channel_name)
            filters = self._parse_filters(name, cfg)
            flows.append(
                FlowConfig(
                    name=name,
                    input=input_cfg,
                    parser=parser_cfg,
                    output=output_cfg,
                    output_format=output_format,
                    format_options=format_options,
                    channel=channel_name,
                    filters=filters,
                )
            )
        return flows, known_channels

    def _component_from_section(
        self, cfg: Mapping[str, str], prefix: str, section: str
    ) -> ComponentConfig:
        key = f"{prefix}.type"
        if key not in cfg:
            raise ConfigError(f"Missing required option '{key}' in [{section}]")
        type_name = cfg[key]
        options: Dict[str, str] = {}
        prefix_with_dot = f"{prefix}."
        for option, value in cfg.items():
            if option.startswith(prefix_with_dot) and option != key:
                options[option[len(prefix_with_dot) :]] = value
        return ComponentConfig(type=type_name, options=options)

    def _parse_filters(self, flow_name: str, cfg: Mapping[str, str]) -> List[FilterConfig]:
        filters: Dict[str, Dict[str, str]] = {}
        for option, value in cfg.items():
            if not option.startswith("filter"):
                continue
            remainder = option[len("filter") :]
            if remainder.startswith("."):
                remainder = remainder[1:]
            if not remainder:
                continue
            if "." in remainder:
                name, opt = remainder.split(".", 1)
            else:
                name, opt = "default", remainder
            filters.setdefault(name, {})[opt] = value
        parsed: List[FilterConfig] = []
        for name, options in sorted(filters.items()):
            stage = options.get("stage", "parser")
            type_name = options.get("type")
            if not type_name:
                raise ConfigError(
                    f"Filter '{name}' in flow '{flow_name}' is missing the 'type' option"
                )
            component = ComponentConfig(
                type=type_name,
                options={k: v for k, v in options.items() if k not in {"stage", "type"}},
            )
            parsed.append(FilterConfig(name=name, component=component, stage=stage))
        return parsed


def iter_flow_sections(config: RuntimeConfig) -> Iterator[str]:
    """Helper primarily used in tests to list flow names."""

    for flow in config.flows:
        yield flow.name
