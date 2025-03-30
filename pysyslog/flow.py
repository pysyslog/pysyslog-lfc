"""
Flow management for PySyslog LFC
"""

import logging
import threading
from typing import Dict, Any, Optional, List
from queue import Queue
from dataclasses import dataclass

from .components import ComponentRegistry, InputComponent, ParserComponent, OutputComponent, FilterComponent

@dataclass
class FlowConfig:
    """Configuration for a flow"""
    input_type: str
    input_config: Dict[str, Any]
    parser_type: str
    parser_config: Dict[str, Any]
    output_type: str
    output_config: Dict[str, Any]
    filters: List[Dict[str, Any]]

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
        self.filters = self._create_filters()
        
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
        filters = []
        
        for key, value in config.items():
            if key.startswith("input."):
                input_config[key[6:]] = value
            elif key.startswith("parser."):
                parser_config[key[7:]] = value
            elif key.startswith("output."):
                output_config[key[7:]] = value
            elif key.startswith("filter."):
                # Parse filter configuration
                filter_parts = key[7:].split(".")
                if len(filter_parts) == 2:
                    filter_index = int(filter_parts[0])
                    while len(filters) <= filter_index:
                        filters.append({})
                    filters[filter_index][filter_parts[1]] = value
        
        return FlowConfig(
            input_type=input_config.pop("type"),
            input_config=input_config,
            parser_type=parser_config.pop("type"),
            parser_config=parser_config,
            output_type=output_config.pop("type"),
            output_config=output_config,
            filters=filters
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
    
    def _create_filters(self) -> List[FilterComponent]:
        """Create filter components"""
        filters = []
        for filter_config in self.config.filters:
            if not filter_config:
                continue
            filter_type = filter_config.pop("type")
            filters.append(
                self.registry.create_filter(
                    filter_type,
                    filter_config
                )
            )
        return filters
    
    def start(self) -> None:
        """Start the flow processing"""
        if self.running:
            return
        
        self.running = True
        self.logger.info("Starting flow")
        
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
        for filter_component in self.filters:
            filter_component.close()
    
    def _input_loop(self) -> None:
        """Input processing loop"""
        while self.running:
            try:
                data = self.input.read()
                if data:
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
                    # Apply filters
                    should_output = True
                    for filter_component in self.filters:
                        if not filter_component.filter(parsed):
                            should_output = False
                            break
                    
                    if should_output:
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
                self.output.write(data)
            except Queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Output error: {e}", exc_info=True) 