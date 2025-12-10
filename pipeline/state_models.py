# -*- coding: utf-8 -*-
"""
Created on Tue Dec  9 16:05:29 2025

@author: aengstrom
"""

from pydantic import BaseModel
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class FileOpsState(BaseModel):
    unzipped: List[Path] = []
    moved_dat: List[Path] = []
    moved_tx1: List[Path] = []
    renamed_files: List[Path] = []
    converted_pdfs: List[Path] = []
    errors: Dict[str, str] = {}  # filename -> error
    last_run: datetime | None = None
    
class QCState(BaseModel):
    