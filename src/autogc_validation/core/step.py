# -*- coding: utf-8 -*-
"""
Created on Mon Jan 12 11:11:45 2026

@author: aengstrom
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from dataclasses import dataclass
import logging
from datetime import datetime

@dataclass
class StepResult:
    """Result of executing a pipeline step"""
    success: bool
    output: Any
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class PipelineStep(ABC):
    """Base class for all pipeline steps"""
    
    def __init__(self, name: str, config: 'ValidationConfig'):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
    @abstractmethod
    def dependencies(self) -> List[str]:
        """Return list of step names that must complete before this step"""
        pass
    
    @abstractmethod
    def should_run(self) -> bool:
        """Check if this step needs to run (idempotency check)"""
        pass
    
    @abstractmethod
    def execute(self) -> StepResult:
        """Execute the step and return result"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate that the step completed successfully"""
        pass
    
    def run(self) -> StepResult:
        """Main entry point - checks if needed and executes"""
        if not self.should_run():
            self.logger.info(f"Step '{self.name}' already completed, skipping")
            return StepResult(
                success=True,
                output=None,
                message="Already completed",
                timestamp=datetime.now()
            )
        
        self.logger.info(f"Executing step '{self.name}'")
        try:
            result = self.execute()
            if result.success and self.validate():
                self.logger.info(f"Step '{self.name}' completed successfully")
                return result
            else:
                self.logger.error(f"Step '{self.name}' validation failed")
                return StepResult(
                    success=False,
                    output=result.output,
                    message="Validation failed",
                    timestamp=datetime.now()
                )
        except Exception as e:
            self.logger.error(f"Step '{self.name}' failed: {e}", exc_info=True)
            return StepResult(
                success=False,
                output=None,
                message=str(e),
                timestamp=datetime.now()
            )