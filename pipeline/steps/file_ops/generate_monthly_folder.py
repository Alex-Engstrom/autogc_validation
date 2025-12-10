# -*- coding: utf-8 -*-
"""
Created on Tue Dec  9 15:54:09 2025

@author: aengstrom
"""
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def generate_monthly_folder(
    root_dir: str | os.PathLike,
    sitename: str,
    year: int | str,
    month: int | str
) -> Path:
    """Generate the monthly validation folder structure."""
    try:
        year = str(year)
        month = int(month)  
        base_dir = Path(root_dir) / f"{sitename}{year}{month:02d}v1"
        base_dir.mkdir(exist_ok=True)

        subdirs = {
            "AQS": [],
            "FINAL": ["dat_and_txt/Final", "dat_and_txt/Original", "dat_and_txt/RPO"],
            "MDVR": ["dat_and_txt/Final", "dat_and_txt/Original", "dat_and_txt/RPO"],
            "Original": []
        }

        weeks = [f"week {i}" for i in range(1, 5)]

        logger.info(f"Creating folder structure in directory {base_dir}")

        for top, nested in subdirs.items():
            top_path = base_dir / top
            top_path.mkdir(exist_ok=True)
            for sub in nested:
                sub_path = top_path / sub
                sub_path.mkdir(parents=True, exist_ok=True)

                # Add week folders under "Original" and "RPO"
                if any(k in sub for k in ["Original", "RPO"]):
                    for w in weeks:
                        (sub_path / w).mkdir(exist_ok=True)

        logger.info("Folder structure finished successfully")

    except Exception as e:
        logger.exception(f"Error generating monthly folder structure: {e}")
        raise
    return base_dir