"""
Component management for PySyslog LFC
"""

import logging
import importlib
import pkgutil
from typing import Dict, Any, Type, Optional
from abc import ABC, abstractmethod

class BaseComponent(ABC):
    """Base class for all components"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def close(self) -> None:
        """Cleanup resources"""
        pass

class InputComponent(BaseComponent):
    """Base class for input components"""
    
    @abstractmethod
    def read(self) -> Optional[str]:
        """Read input data"""
        pass

class ParserComponent(BaseComponent):
    """Base class for parser components"""
    
    @abstractmethod
    def parse(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse input data into structured format"""
        pass

class OutputComponent(BaseComponent):
    """Base class for output components"""
    
    @abstractmethod
    def write(self, data: Dict[str, Any]) -> None:
        """Write parsed data to output"""
        pass

class ComponentRegistry:
    """Registry for managing component types"""
    
    def __init__(self):
        self.input_types: Dict[str, Type[InputComponent]] = {}
        self.parser_types: Dict[str, Type[ParserComponent]] = {}
        self.output_types: Dict[str, Type[OutputComponent]] = {}
        self._load_components()
    
    def _load_components(self) -> None:
        """Load all available components"""
        # Load input components
        for _, name, _ in pkgutil.iter_modules(["pysyslog.input"]):
            module = importlib.import_module(f"pysyslog.input.{name}")
            if hasattr(module, "Input"):
                self.input_types[name] = module.Input
        
        # Load parser components
        for _, name, _ in pkgutil.iter_modules(["pysyslog.parser"]):
            module = importlib.import_module(f"pysyslog.parser.{name}")
            if hasattr(module, "Parser"):
                self.parser_types[name] = module.Parser
        
        # Load output components
        for _, name, _ in pkgutil.iter_modules(["pysyslog.output"]):
            module = importlib.import_module(f"pysyslog.output.{name}")
            if hasattr(module, "Output"):
                self.output_types[name] = module.Output
    
    def create_input(self, type_name: str, config: Dict[str, Any]) -> InputComponent:
        """Create an input component"""
        if type_name not in self.input_types:
            raise ValueError(f"Unknown input type: {type_name}")
        return self.input_types[type_name](config)
    
    def create_parser(self, type_name: str, config: Dict[str, Any]) -> ParserComponent:
        """Create a parser component"""
        if type_name not in self.parser_types:
            raise ValueError(f"Unknown parser type: {type_name}")
        return self.parser_types[type_name](config)
    
    def create_output(self, type_name: str, config: Dict[str, Any]) -> OutputComponent:
        """Create an output component"""
        if type_name not in self.output_types:
            raise ValueError(f"Unknown output type: {type_name}")
        return self.output_types[type_name](config) 