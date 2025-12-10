# -*- coding: utf-8 -*-
"""
Created on Tue Dec  9 16:54:31 2025

@author: aengstrom
"""

import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_state(state_file: Path) -> dict:
    """Load the pipeline state from a JSON file."""
    state_file = Path(state_file)
    if not state_file.exists():
        logger.info(f"State file not found, initializing new state: {state_file}")
        return {}  # start with empty state

    try:
        with open(state_file, "r") as f:
            state = json.load(f)
        logger.info(f"Loaded state from {state_file}")
        return state
    except json.JSONDecodeError:
        logger.warning(f"State file {state_file} is corrupted, resetting state.")
        return {}
    
def save_state(state_file: Path, state: dict):
    """Save the pipeline state to a JSON file."""
    state_file = Path(state_file)
    state_file.parent.mkdir(parents=True, exist_ok=True)  # ensure folder exists

    with open(state_file, "w") as f:
        json.dump(state, f, indent=4)
    logger.info(f"Saved state to {state_file}")