"""
Flow management for PySyslog LFC
"""

import logging
import threading
from typing import Dict, Any, Optional, List
from queue import Queue
from dataclasses import dataclass
from enum import Enum

from .components import ComponentRegistry, InputComponent, ParserComponent, OutputComponent, FilterComponent

class FilterStage(Enum):
    """Filter application stage"""
    INPUT = "input"
    PARSER = "parser"
    OUTPUT = "output"

@dataclass
class FilterConfig:
    """Configuration for a filter"""
    type: str
    field: str
    op: str
    value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    stage: FilterStage = FilterStage.PARSER

@dataclass
class FlowConfig:
    """Configuration for a flow"""
    name: str
    input_type: str
    input_config: Dict[str, Any]
    parser_type: str
    parser_config: Dict[str, Any]
    output_type: str
    output_config: Dict[str, Any]
    filter: Optional[FilterConfig] = None

class Flow:
    """Represents a log processing flow"""
    
    def __init__(self, name: str, config: Dict[str, str], registry: ComponentRegistry):
        self.name = name
        self.logger = logging.getLogger(f"pysyslog.flow.{name}")
        self.registry = registry
        
        # Parse configuration
        self.config = self._parse_config(config)
        
        # Initialize components
        self.input = self._create_input()
        self.parser = self._create_parser()
        self.output = self._create_output()
        self.filter = self._create_filter()
        
        # Setup queues
        self.input_queue = Queue()
        self.output_queue = Queue()
        
        # Thread control
        self.running = False
        self.threads: List[threading.Thread] = []
    
    def _parse_config(self, config: Dict[str, str]) -> FlowConfig:
        """Parse flow configuration into structured format"""
        input_config = {}
        parser_config = {}
        output_config = {}
        filter_config = None
        
        for key, value in config.items():
            if key.startswith("input."):
                input_config[key[6:]] = value
            elif key.startswith("parser."):
                parser_config[key[7:]] = value
            elif key.startswith("output."):
                output_config[key[7:]] = value
            elif key.startswith("filter."):
                # Parse filter configuration
                filter_key = key[7:]  # Remove "filter." prefix
                if filter_config is None:
                    filter_config = {}
                filter_config[filter_key] = value
        
        # Create filter config if present
        filter = None
        if filter_config:
            filter = FilterConfig(
                type=filter_config.get("type"),
                field=filter_config.get("field"),
                op=filter_config.get("op"),
                value=filter_config.get("value"),
                min_value=float(filter_config.get("min")) if "min" in filter_config else None,
                max_value=float(filter_config.get("max")) if "max" in filter_config else None,
                pattern=filter_config.get("pattern"),
                stage=FilterStage(filter_config.get("stage", "parser"))
            )
        
        return FlowConfig(
            name=self.name,
            input_type=input_config.pop("type"),
            input_config=input_config,
            parser_type=parser_config.pop("type"),
            parser_config=parser_config,
            output_type=output_config.pop("type"),
            output_config=output_config,
            filter=filter
        )
    
    def _create_input(self) -> InputComponent:
        """Create input component"""
        return self.registry.create_input(
            self.config.input_type,
            self.config.input_config
        )
    
    def _create_parser(self) -> ParserComponent:
        """Create parser component"""
        return self.registry.create_parser(
            self.config.parser_type,
            self.config.parser_config
        )
    
    def _create_output(self) -> OutputComponent:
        """Create output component"""
        return self.registry.create_output(
            self.config.output_type,
            self.config.output_config
        )
    
    def _create_filter(self) -> Optional[FilterComponent]:
        """Create filter component"""
        if not self.config.filter:
            return None
            
        # Add flow name to filter config
        filter_config = {
            "flow_name": self.name,
            "type": self.config.filter.type,
            "field": self.config.filter.field,
            "op": self.config.filter.op,
            "value": self.config.filter.value,
            "min": self.config.filter.min_value,
            "max": self.config.filter.max_value,
            "pattern": self.config.filter.pattern,
            "stage": self.config.filter.stage.value
        }
        
        return self.registry.create_filter(
            self.config.filter.type,
            filter_config
        )
    
    def start(self) -> None:
        """Start the flow processing"""
        if self.running:
            return
        
        self.running = True
        self.logger.info("Starting flow")
        
        # Initialize filter if present
        if self.filter:
            self.filter.initialize()
        
        # Start input thread
        input_thread = threading.Thread(
            target=self._input_loop,
            name=f"input-{self.name}"
        )
        input_thread.daemon = True
        input_thread.start()
        self.threads.append(input_thread)
        
        # Start parser thread
        parser_thread = threading.Thread(
            target=self._parser_loop,
            name=f"parser-{self.name}"
        )
        parser_thread.daemon = True
        parser_thread.start()
        self.threads.append(parser_thread)
        
        # Start output thread
        output_thread = threading.Thread(
            target=self._output_loop,
            name=f"output-{self.name}"
        )
        output_thread.daemon = True
        output_thread.start()
        self.threads.append(output_thread)
    
    def stop(self) -> None:
        """Stop the flow processing"""
        if not self.running:
            return
        
        self.running = False
        self.logger.info("Stopping flow")
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)
        
        # Cleanup components
        self.input.close()
        self.parser.close()
        self.output.close()
        if self.filter:
            self.filter.close()
    
    def _input_loop(self) -> None:
        """Input processing loop"""
        while self.running:
            try:
                data = self.input.read()
                if data:
                    # Apply input stage filter if present
                    if self.filter and self.filter.stage == FilterStage.INPUT:
                        if not self.filter.filter({"raw": data}):
                            continue
                    self.input_queue.put(data)
            except Exception as e:
                self.logger.error(f"Input error: {e}", exc_info=True)
    
    def _parser_loop(self) -> None:
        """Parser processing loop"""
        while self.running:
            try:
                data = self.input_queue.get(timeout=1)
                parsed = self.parser.parse(data)
                if parsed:
                    # Apply parser stage filter if present
                    if self.filter and self.filter.stage == FilterStage.PARSER:
                        if not self.filter.filter(parsed):
                            continue
                    self.output_queue.put(parsed)
            except Queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Parser error: {e}", exc_info=True)
    
    def _output_loop(self) -> None:
        """Output processing loop"""
        while self.running:
            try:
                data = self.output_queue.get(timeout=1)
                # Apply output stage filter if present
                if self.filter and self.filter.stage == FilterStage.OUTPUT:
                    if not self.filter.filter(data):
                        continue
                self.output.write(data)
            except Queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Output error: {e}", exc_info=True) 