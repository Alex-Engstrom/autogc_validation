# -*- coding: utf-8 -*-
"""
Monthly validation folder structure creation.
"""

import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def generate_monthly_folder_structure(
    root_dir: Union[str, Path],
    sitename: str,
    year: Union[int, str],
    month: Union[int, str],
) -> Path:
    """Generate the monthly validation folder structure.

    Creates a directory tree for a site's monthly validation:

        {sitename}{year}{month:02d}v1/
        ├── AQS/
        ├── FINAL/
        │   ├── week 1/
        │   ├── week 2/
        │   ├── week 3/
        │   └── week 4/
        ├── MDVR/
        ├── Original/
        └── temp/

    Args:
        root_dir: Parent directory for the monthly folder.
        sitename: Site name code (e.g. "RB").
        year: Year (int or string).
        month: Month number (1-12).

    Returns:
        Path to the created base directory.
    """
    year = str(year)
    month = int(month)
    base_dir = Path(root_dir) / f"{sitename}{year}{month:02d}v1"
    base_dir.mkdir(exist_ok=True)

    subdirs = ["AQS", "FINAL", "MDVR", "Original", "temp"]
    weeks = [f"week {i}" for i in range(1, 5)]

    logger.info("Creating folder structure in %s", base_dir)

    for name in subdirs:
        top_path = base_dir / name
        top_path.mkdir(exist_ok=True)
        if name == "FINAL":
            for w in weeks:
                (top_path / w).mkdir(exist_ok=True)

    logger.info("Folder structure created successfully")
    return base_dir
