# -*- coding: utf-8 -*-
"""
Created on Tue Dec  9 17:18:04 2025

@author: aengstrom
"""

import pytest
from pathlib import Path
import json

from pipeline.steps.file_ops.generate_monthly_folder import generate_monthly_folder
from pipeline.state import load_state, save_state


def test_generate_monthly_folder_structure(temp_root):
    sitename = "LP"
    year = 2025
    month = 7

    # Step 1: Generate folders
    base_dir = generate_monthly_folder(temp_root, sitename, year, month)

    # Step 2: Save state
    state_file = base_dir / "state.json"
    state_data = {
        "base_dir": str(base_dir),
        "sitename": sitename,
        "year": year,
        "month": month
    }
    save_state(state_file, state_data)

    # Step 3: Load state and assert
    loaded_state = load_state(state_file)
    assert loaded_state["sitename"] == sitename
    assert loaded_state["year"] == year
    assert loaded_state["month"] == month
    assert Path(loaded_state["base_dir"]).exists()

    # Step 4: Optional: check folder structure
    expected_subdirs = ["AQS", "FINAL", "MDVR", "Original"]
    for subdir in expected_subdirs:
        assert (base_dir / subdir).exists()
    
    reloaded_base_dir = Path(loaded_state["base_dir"])
    assert reloaded_base_dir.exists()