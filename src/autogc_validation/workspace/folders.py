# -*- coding: utf-8 -*-
"""
Monthly validation folder structure creation.
"""

import logging
import shutil
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
        ├── Original/
        ├── MDVR/
        └── TEMP/

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

    subdirs = ["AQS", "FINAL", "Original", "MDVR", "TEMP"]
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


_TRANSFER_SUBDIRS = {"AQS", "FINAL", "Original", "MDVR"}


def transfer_to_network(
    workspace_dir: Union[str, Path],
    network_root: Union[str, Path],
) -> Path:
    """Copy a monthly validation folder to a network drive.

    Only the subfolders AQS, FINAL, Original, and MDVR are transferred —
    TEMP is excluded.  The destination
    folder is created under *network_root* with the same name as the
    source (e.g. ``EQ202503v1``).  Raises ``FileExistsError`` if the
    destination already exists.

    Args:
        workspace_dir: Path to the local monthly validation folder
            (e.g. ``/validation/EQ/EQ202503v1``).
        network_root: Parent directory on the network drive where the
            folder should be created.

    Returns:
        Path to the created destination folder on the network.

    Raises:
        FileNotFoundError: If *workspace_dir* does not exist.
        FileExistsError: If the destination folder already exists.
    """
    workspace_dir = Path(workspace_dir)
    network_root = Path(network_root)

    if not workspace_dir.exists():
        raise FileNotFoundError(f"Workspace directory not found: {workspace_dir}")

    dest = network_root / workspace_dir.name
    if dest.exists():
        raise FileExistsError(
            f"Destination already exists: {dest}\n"
            "Delete it manually before transferring."
        )

    # Pre-flight: confirm nothing under network_root would be touched.
    for subdir in _TRANSFER_SUBDIRS:
        dest_subdir = dest / subdir
        if dest_subdir.exists():
            raise FileExistsError(
                f"Destination subfolder already exists: {dest_subdir}\n"
                "Delete it manually before transferring."
            )

    dest.mkdir(parents=True)
    logger.info("Transferring %s → %s", workspace_dir.name, dest)

    for subdir in _TRANSFER_SUBDIRS:
        src = workspace_dir / subdir
        if not src.exists():
            logger.warning("Skipping missing subfolder: %s", subdir)
            continue
        shutil.copytree(src, dest / subdir, dirs_exist_ok=False)
        logger.info("Copied %s", subdir)

    logger.info("Transfer complete: %s", dest)
    return dest
