# -*- coding: utf-8 -*-
"""
Monthly validation folder structure creation.
"""

import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def _next_version(root_dir: Path, prefix: str) -> int:
    """Find the next available version number for a workspace folder.

    Scans root_dir for existing folders matching {prefix}v1, {prefix}v2, etc.
    and returns the next version number.

    Args:
        root_dir: Parent directory to scan.
        prefix: Folder name prefix (e.g., "RB202601").

    Returns:
        Next available version number (1 if none exist).
    """
    version = 1
    while (root_dir / f"{prefix}v{version}").exists():
        version += 1
    return version


def generate_monthly_folder_structure(
    root_dir: Union[str, Path],
    sitename: str,
    year: Union[int, str],
    month: Union[int, str],
) -> Path:
    """Generate the monthly validation folder structure.

    Creates a directory tree for a site's monthly validation. If a prior
    version already exists (v1, v2, ...), the next version is created
    automatically.

        {sitename}{year}{month:02d}v{N}/
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
    root_dir = Path(root_dir)
    year = str(year)
    month = int(month)

    prefix = f"{sitename}{year}{month:02d}"
    version = _next_version(root_dir, prefix)
    base_dir = root_dir / f"{prefix}v{version}"
    base_dir.mkdir()

    subdirs = ["AQS", "FINAL", "MDVR", "Original", "temp"]
    weeks = [f"week {i}" for i in range(1, 5)]

    logger.info("Creating folder structure in %s", base_dir)

    for name in subdirs:
        top_path = base_dir / name
        top_path.mkdir()
        if name == "FINAL":
            for w in weeks:
                (top_path / w).mkdir()

    logger.info("Folder structure created successfully")
    return base_dir
