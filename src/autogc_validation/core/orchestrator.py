# -*- coding: utf-8 -*-
"""
Created on Mon Jan 12 11:13:05 2026

@author: aengstrom
"""

from typing import Dict, List, Optional
from pathlib import Path
import logging
from collections import defaultdict
import json
from datetime import datetime

from .base_step import PipelineStep, StepResult

class PipelineOrchestrator:
    """Orchestrates execution of pipeline steps with dependency management"""
    
    def __init__(self, config, state_file: Optional[Path] = None):
        self.config = config
        self.state_file = state_file or (config.output_dir / "pipeline_state.json")
        self.steps: Dict[str, PipelineStep] = {}
        self.results: Dict[str, StepResult] = {}
        self.logger = logging.getLogger(__name__)
        self.state = self._load_state()
        
    def _load_state(self) -> Dict:
        """Load pipeline state from disk"""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {"completed_steps": {}, "step_results": {}}
    
    def _save_state(self):
        """Save pipeline state to disk"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2, default=str))
    
    def register_step(self, step: PipelineStep):
        """Register a step in the pipeline"""
        self.steps[step.name] = step
        self.logger.info(f"Registered step: {step.name}")
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build a dependency graph for all registered steps"""
        graph = {}
        for name, step in self.steps.items():
            graph[name] = step.dependencies()
        return graph
    
    def _topological_sort(self) -> List[str]:
        """Sort steps in dependency order using topological sort"""
        graph = self._build_dependency_graph()
        in_degree = defaultdict(int)
        
        # Calculate in-degrees
        for node in graph:
            in_degree[node] = 0
        
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1
        
        # Find all nodes with in-degree 0
        queue = [node for node in graph if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Reduce in-degree for neighbors
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(result) != len(graph):
            raise ValueError("Circular dependency detected in pipeline")
        
        return result
    
    def run(self, step_names: Optional[List[str]] = None, force: bool = False):
        """
        Run the pipeline
        
        Args:
            step_names: Specific steps to run (None = all steps)
            force: Force re-run even if steps are marked complete
        """
        # Determine which steps to run
        if step_names is None:
            steps_to_run = self._topological_sort()
        else:
            # Include dependencies
            steps_to_run = self._get_steps_with_dependencies(step_names)
        
        self.logger.info(f"Pipeline execution order: {' -> '.join(steps_to_run)}")
        
        # Execute steps
        for step_name in steps_to_run:
            if step_name not in self.steps:
                self.logger.error(f"Step '{step_name}' not registered")
                continue
            
            # Check if already completed (unless forcing)
            if not force and step_name in self.state["completed_steps"]:
                self.logger.info(f"Step '{step_name}' already completed (use --force to re-run)")
                continue
            
            # Check dependencies
            if not self._dependencies_met(step_name):
                self.logger.error(f"Dependencies not met for '{step_name}'")
                raise RuntimeError(f"Cannot run '{step_name}': dependencies not met")
            
            # Run the step
            step = self.steps[step_name]
            result = step.run()
            self.results[step_name] = result
            
            # Update state
            if result.success:
                self.state["completed_steps"][step_name] = {
                    "timestamp": datetime.now().isoformat(),
                    "message": result.message,
                    "metadata": result.metadata
                }
                self._save_state()
            else:
                self.logger.error(f"Step '{step_name}' failed: {result.message}")
                raise RuntimeError(f"Pipeline failed at step '{step_name}'")
        
        self.logger.info("Pipeline completed successfully")
        return self.results
    
    def _get_steps_with_dependencies(self, step_names: List[str]) -> List[str]:
        """Get steps including all their dependencies in correct order"""
        required_steps = set()
        
        def add_with_deps(name):
            if name in required_steps:
                return
            required_steps.add(name)
            if name in self.steps:
                for dep in self.steps[name].dependencies():
                    add_with_deps(dep)
        
        for name in step_names:
            add_with_deps(name)
        
        # Sort topologically
        all_sorted = self._topological_sort()
        return [s for s in all_sorted if s in required_steps]
    
    def _dependencies_met(self, step_name: str) -> bool:
        """Check if all dependencies for a step are met"""
        step = self.steps[step_name]
        for dep in step.dependencies():
            if dep not in self.state["completed_steps"]:
                return False
        return True
    
    def reset(self, step_names: Optional[List[str]] = None):
        """Reset pipeline state for specified steps (or all)"""
        if step_names is None:
            self.state = {"completed_steps": {}, "step_results": {}}
            self.logger.info("Reset all pipeline state")
        else:
            for name in step_names:
                if name in self.state["completed_steps"]:
                    del self.state["completed_steps"][name]
                    self.logger.info(f"Reset state for step: {name}")
        
        self._save_state()
    
    def get_status(self) -> Dict:
        """Get current pipeline status"""
        status = {
            "total_steps": len(self.steps),
            "completed_steps": len(self.state["completed_steps"]),
            "steps": {}
        }
        
        for name, step in self.steps.items():
            is_completed = name in self.state["completed_steps"]
            status["steps"][name] = {
                "completed": is_completed,
                "dependencies": step.dependencies(),
                "can_run": self._dependencies_met(name)
            }
            
            if is_completed:
                status["steps"][name]["completed_at"] = self.state["completed_steps"][name]["timestamp"]
        
        return status