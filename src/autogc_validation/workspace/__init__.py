# -*- coding: utf-8 -*-
"""
Workspace management for monthly AutoGC validation.

Provides functions for setting up the monthly folder structure,
extracting and organizing data files, and a high-level orchestrator
that runs the full workspace initialization sequence.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from autogc_validation.workspace.folders import generate_monthly_folder_structure
from autogc_validation.workspace.files import (
    unzip_files,
    move_dat_files,
    move_tx1_files,
    move_files_by_week,
    rename_dattxt_files_to_txt,
)

logger = logging.getLogger(__name__)


@dataclass
class WorkspaceResult:
    """Record of a workspace initialization run.

    Each field captures the result of one step. A value of None
    means the step was skipped.
    """
    base_dir: Optional[Path] = None
    unzipped: Optional[list[Path]] = None
    dat_summary: Optional[dict] = None
    tx1_summary: Optional[dict] = None
    week_counts: Optional[dict[str, int]] = None
    steps_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def init_workspace(
    root_dir: Union[str, Path],
    source_dir: Union[str, Path],
    sitename: str,
    year: Union[int, str],
    month: Union[int, str],
    unzip: bool = True,
    allow_network_drive: bool = False,
) -> WorkspaceResult:
    """Run the full workspace initialization sequence.

    Executes the following steps in order:
      1. Create monthly folder structure
      2. Unzip daily zip files from source to temp/
      3. Move .dat files from temp/ to Original/
      4. Move .tx1 files from temp/ to Original/
      5. Sort .dat files into FINAL/week N/ folders

    Each step is logged and recorded in the returned WorkspaceResult.
    If a step fails, the error is captured and subsequent steps
    continue where possible.

    Args:
        root_dir: Parent directory for the monthly folder.
        source_dir: Directory containing source data (zip files).
        sitename: Site name code (e.g. "RB").
        year: Year.
        month: Month number (1-12).
        unzip: Whether to unzip files from source_dir.
        allow_network_drive: Allow operation on network drives.

    Returns:
        WorkspaceResult with a record of each step.
    """
    result = WorkspaceResult()
    source = Path(source_dir)

    # Step 1: Create folder structure
    logger.info("Step 1: Creating monthly folder structure")
    try:
        base_dir = generate_monthly_folder_structure(root_dir, sitename, year, month)
        result.base_dir = base_dir
        result.steps_completed.append("create_folders")
        logger.info("Step 1 complete: %s", base_dir)
    except Exception as e:
        result.errors.append(f"create_folders: {e}")
        logger.exception("Step 1 failed")
        return result  # Can't continue without the folder structure

    temp_dir = base_dir / "temp"
    original_dir = base_dir / "Original"
    final_dir = base_dir / "FINAL"

    # Step 2: Unzip files
    if unzip:
        logger.info("Step 2: Unzipping files from %s", source)
        try:
            extracted = unzip_files(
                source, temp_dir,
                allow_network_drive=allow_network_drive,
            )
            result.unzipped = extracted
            result.steps_completed.append("unzip_files")
            logger.info("Step 2 complete: %d zip(s) extracted", len(extracted))
        except Exception as e:
            result.errors.append(f"unzip_files: {e}")
            logger.exception("Step 2 failed")
    else:
        logger.info("Step 2: Skipped (unzip=False)")

    # Step 3: Move .dat files
    logger.info("Step 3: Moving .dat files to Original/")
    try:
        dat_folder, dat_summary = move_dat_files(temp_dir, original_dir)
        result.dat_summary = dat_summary
        result.steps_completed.append("move_dat_files")
        logger.info(
            "Step 3 complete: %d found, %d copied, %d duplicates",
            dat_summary["found"][0],
            dat_summary["copied"][0],
            dat_summary["duplicates"][0],
        )
    except Exception as e:
        result.errors.append(f"move_dat_files: {e}")
        logger.exception("Step 3 failed")
        dat_folder = None

    # Step 4: Move .tx1 files
    logger.info("Step 4: Moving .tx1 files to Original/")
    try:
        _, tx1_summary = move_tx1_files(temp_dir, original_dir)
        result.tx1_summary = tx1_summary
        result.steps_completed.append("move_tx1_files")
        logger.info(
            "Step 4 complete: %d found, %d copied, %d duplicates",
            tx1_summary["found"][0],
            tx1_summary["copied"][0],
            tx1_summary["duplicates"][0],
        )
    except Exception as e:
        result.errors.append(f"move_tx1_files: {e}")
        logger.exception("Step 4 failed")

    # Step 5: Sort .dat files by week
    if dat_folder:
        logger.info("Step 5: Sorting .dat files into weekly folders")
        try:
            week_counts = move_files_by_week(
                dat_folder, final_dir, int(month), int(year),
            )
            result.week_counts = week_counts
            result.steps_completed.append("sort_by_week")
            logger.info("Step 5 complete: %s", week_counts)
        except Exception as e:
            result.errors.append(f"sort_by_week: {e}")
            logger.exception("Step 5 failed")
    else:
        logger.warning("Step 5: Skipped (no dat folder from step 3)")

    # Summary
    logger.info(
        "Workspace init complete: %d/%d steps succeeded",
        len(result.steps_completed),
        5,
    )
    if result.errors:
        logger.warning("Errors: %s", result.errors)

    return result
