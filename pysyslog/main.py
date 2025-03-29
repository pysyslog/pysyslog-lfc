#!/usr/bin/env python3
"""
PySyslog LFC - Lightweight Flow-based Log Processor
Main entry point
"""

import os
import sys
import logging
import configparser
from pathlib import Path
from typing import Dict, List, Optional

from .config import Config
from .flow import Flow
from .components import ComponentRegistry

def setup_logging(level: str = "INFO") -> None:
    """Configure logging with JSON format"""
    import pythonjsonlogger.jsonlogger
    
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    handler = logging.StreamHandler()
    formatter = pythonjsonlogger.jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def load_config(config_path: str) -> Config:
    """Load and parse configuration files"""
    config = Config()
    config.load_file(config_path)
    
    # Load included configurations
    if "use" in config and "include" in config["use"]:
        include_pattern = config["use"]["include"]
        for include_path in Path("/etc/pysyslog/conf.d").glob("*.ini"):
            config.load_file(str(include_path))
    
    return config

def main() -> int:
    """Main entry point"""
    try:
        # Load configuration
        config = load_config("/etc/pysyslog/main.ini")
        
        # Setup logging
        log_level = config.get("settings", "log_level", fallback="INFO")
        setup_logging(log_level)
        logger = logging.getLogger("pysyslog")
        
        # Initialize component registry
        registry = ComponentRegistry()
        
        # Create and start flows
        flows: Dict[str, Flow] = {}
        for section in config.sections():
            if section.startswith("flow."):
                flow_name = section[5:]  # Remove "flow." prefix
                flow_config = dict(config[section])
                flows[flow_name] = Flow(flow_name, flow_config, registry)
                flows[flow_name].start()
        
        # Keep the main thread alive
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            for flow in flows.values():
                flow.stop()
            return 0
            
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 