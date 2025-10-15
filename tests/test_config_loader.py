from __future__ import annotations

import pytest

from pysyslog.config import ConfigError, ConfigLoader


def test_config_loader_parses_flows_and_channels():
    text = """
[flow.main]
input.type = memory
parser.type = text
output.type = memory
output.format = json
format.indent = 2
channel = reliable

[channel.reliable]
maxsize = 256

[settings]
log_level = DEBUG
"""
    config = ConfigLoader().loads(text)
    assert [flow.name for flow in config.flows] == ["main"]
    flow = config.get_flow("main")
    assert flow.output_format == "json"
    assert flow.format_options["indent"] == "2"
    assert flow.channel == "reliable"
    assert "reliable" in config.channels
    assert config.settings["log_level"] == "DEBUG"


def test_filter_requires_type():
    text = """
[flow.invalid]
input.type = memory
parser.type = text
output.type = memory
filter.stage = parser
"""
    with pytest.raises(ConfigError):
        ConfigLoader().loads(text)
