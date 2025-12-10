# -*- coding: utf-8 -*-
"""
Created on Tue Dec  9 17:15:46 2025

@author: aengstrom
"""

import pytest
from pathlib import Path

@pytest.fixture
def temp_root(tmp_path):
    """
    Provides a temporary root folder for file ops tests.
    Automatically cleaned up after tests run.
    """
    return tmp_path