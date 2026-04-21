# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 13:04:27 2026

@author: aengstrom
"""
from openpyxl import load_workbook
import calendar
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
def populate_mdvr(mdvr_path: os.PathLike, 
                  month: int, 
                  year: int,
                  db_path: os.PathLike = None) -> None:
    
    add_month_to_mdvr(mdvr_path, month, year)
    if db_path:        
        return None


DATE_ROW = 5
DATE_COL = 2
def add_month_to_mdvr(mdvr_path: os.PathLike, month: int, year: int) -> None:
    mdvr_path = Path(mdvr_path)
    month_name = calendar.month_name[month]
    wb = load_workbook(mdvr_path)
    ws = wb["Validator Notes"]
    
    ws.cell(DATE_ROW, DATE_COL).value = f"{month_name} {year}"
    wb.save(mdvr_path)
    logger.info(f"Wrote date to MDVR doc: '{month_name} {year}'")
    
    