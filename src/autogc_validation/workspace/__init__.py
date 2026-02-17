# -*- coding: utf-8 -*-
"""
Workspace management for monthly AutoGC validation.

Provides functions for setting up the monthly folder structure,
extracting and organizing data files, and a two-phase orchestrator:

  1. ``create_workspace`` — creates the folder structure so the user
     can manually copy zipped files into ``temp/``.
  2. ``process_workspace`` — unzips, moves, and sorts the files
     placed in ``temp/``.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
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

_STATE_FILENAME = ".workspace_state.json"


def _serialize_summary(summary: Optional[dict]) -> Optional[dict]:
    """Convert a file-move summary dict to JSON-serializable form."""
    if summary is None:
        return None
    return {
        key: {"count": val[0], "files": val[1]}
        for key, val in summary.items()
    }


def _deserialize_summary(data: Optional[dict]) -> Optional[dict]:
    """Convert a stored summary back to the (count, list) tuple format."""
    if data is None:
        return None
    return {
        key: (val["count"], val["files"])
        for key, val in data.items()
    }


@dataclass
class WorkspaceResult:
    """Record of a workspace initialization run.

    Each field captures the result of one step. A value of None
    means the step was skipped. The record can be saved to and
    loaded from disk to survive kernel restarts.
    """
    base_dir: Optional[Path] = None
    unzipped: Optional[list[Path]] = None
    dat_summary: Optional[dict] = None
    tx1_summary: Optional[dict] = None
    week_counts: Optional[dict[str, int]] = None
    steps_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    step_timestamps: dict[str, str] = field(default_factory=dict)

    def save(self) -> Path:
        """Save the workspace state to .workspace_state.json in base_dir.

        Returns:
            Path to the saved state file.

        Raises:
            ValueError: If base_dir is not set.
        """
        if self.base_dir is None:
            raise ValueError("Cannot save: base_dir is not set")

        state = {
            "base_dir": str(self.base_dir),
            "unzipped": [str(p) for p in self.unzipped] if self.unzipped else None,
            "dat_summary": _serialize_summary(self.dat_summary),
            "tx1_summary": _serialize_summary(self.tx1_summary),
            "week_counts": self.week_counts,
            "steps_completed": self.steps_completed,
            "errors": self.errors,
            "step_timestamps": self.step_timestamps,
            "saved_at": datetime.now().isoformat(),
        }

        state_path = self.base_dir / _STATE_FILENAME
        state_path.write_text(json.dumps(state, indent=2))
        logger.info("Workspace state saved to %s", state_path)
        return state_path

    @classmethod
    def load(cls, workspace_dir: Union[str, Path]) -> "WorkspaceResult":
        """Load workspace state from a previously saved .workspace_state.json.

        Args:
            workspace_dir: Path to the monthly validation folder
                (e.g. RB202601v1/).

        Returns:
            WorkspaceResult restored from disk.

        Raises:
            FileNotFoundError: If no state file exists in the directory.
        """
        state_path = Path(workspace_dir) / _STATE_FILENAME
        if not state_path.exists():
            raise FileNotFoundError(f"No workspace state found at {state_path}")

        data = json.loads(state_path.read_text())

        result = cls(
            base_dir=Path(data["base_dir"]),
            unzipped=[Path(p) for p in data["unzipped"]] if data.get("unzipped") else None,
            dat_summary=_deserialize_summary(data.get("dat_summary")),
            tx1_summary=_deserialize_summary(data.get("tx1_summary")),
            week_counts=data.get("week_counts"),
            steps_completed=data.get("steps_completed", []),
            errors=data.get("errors", []),
            step_timestamps=data.get("step_timestamps", {}),
        )
        logger.info("Workspace state loaded from %s", state_path)
        return result


def create_workspace(
    root_dir: Union[str, Path],
    sitename: str,
    year: Union[int, str],
    month: Union[int, str],
) -> WorkspaceResult:
    """Phase 1: Create the monthly folder structure.

    After this returns, copy zipped data files into
    ``result.base_dir / "temp"`` before calling :func:`process_workspace`.

    Args:
        root_dir: Parent directory for the monthly folder.
        sitename: Site name code (e.g. "RB").
        year: Year.
        month: Month number (1-12).

    Returns:
        WorkspaceResult with ``base_dir`` set and the
        ``create_folders`` step recorded.
    """
    result = WorkspaceResult()

    def _record_step(step_name: str) -> None:
        result.steps_completed.append(step_name)
        result.step_timestamps[step_name] = datetime.now().isoformat()
        result.save()

    logger.info("Phase 1: Creating monthly folder structure")
    try:
        base_dir = generate_monthly_folder_structure(root_dir, sitename, year, month)
        result.base_dir = base_dir
        _record_step("create_folders")
        logger.info("Phase 1 complete: %s", base_dir)
    except Exception as e:
        result.errors.append(f"create_folders: {e}")
        logger.exception("Phase 1 failed")

    return result


def process_workspace(
    workspace_dir: Union[str, Path],
) -> WorkspaceResult:
    """Phase 2: Unzip, move, and sort data files placed in ``temp/``.

    Loads saved state from *workspace_dir* and runs any steps not yet
    completed:

      - ``unzip_files`` — unzip all .zip files found in temp/
      - ``move_dat_files`` — move .dat files from temp/ to Original/
      - ``move_tx1_files`` — move .tx1 files from temp/ to Original/
      - ``sort_by_week`` — sort .dat files into FINAL/week N/ folders

    Args:
        workspace_dir: Path to the monthly validation folder created
            by :func:`create_workspace` (e.g. ``RB202601v1/``).

    Returns:
        Updated WorkspaceResult with processing steps recorded.
    """
    result = WorkspaceResult.load(workspace_dir)

    def _record_step(step_name: str) -> None:
        result.steps_completed.append(step_name)
        result.step_timestamps[step_name] = datetime.now().isoformat()
        result.save()

    base_dir = result.base_dir
    temp_dir = base_dir / "temp"
    original_dir = base_dir / "Original"
    final_dir = base_dir / "FINAL"

    # Step 2: Unzip files in temp/
    if "unzip_files" not in result.steps_completed:
        logger.info("Step 2: Unzipping files in temp/")
        try:
            extracted = unzip_files(temp_dir, temp_dir, create_subfolders=False)
            result.unzipped = extracted
            _record_step("unzip_files")
            logger.info("Step 2 complete: %d zip(s) extracted", len(extracted))
        except Exception as e:
            result.errors.append(f"unzip_files: {e}")
            logger.exception("Step 2 failed")
    else:
        logger.info("Step 2: Skipped (already completed)")

    # Step 3: Move .dat files
    dat_folder = None
    if "move_dat_files" not in result.steps_completed:
        logger.info("Step 3: Moving .dat files to Original/")
        try:
            dat_folder, dat_summary = move_dat_files(temp_dir, original_dir)
            result.dat_summary = dat_summary
            _record_step("move_dat_files")
            logger.info(
                "Step 3 complete: %d found, %d copied, %d duplicates",
                dat_summary["found"][0],
                dat_summary["copied"][0],
                dat_summary["duplicates"][0],
            )
        except Exception as e:
            result.errors.append(f"move_dat_files: {e}")
            logger.exception("Step 3 failed")
    else:
        logger.info("Step 3: Skipped (already completed)")
        # Reconstruct dat_folder so step 5 can proceed
        dat_folder = original_dir / "dat"
        if not dat_folder.exists():
            dat_folder = None

    # Step 4: Move .tx1 files
    if "move_tx1_files" not in result.steps_completed:
        logger.info("Step 4: Moving .tx1 files to Original/")
        try:
            _, tx1_summary = move_tx1_files(temp_dir, original_dir)
            result.tx1_summary = tx1_summary
            _record_step("move_tx1_files")
            logger.info(
                "Step 4 complete: %d found, %d copied, %d duplicates",
                tx1_summary["found"][0],
                tx1_summary["copied"][0],
                tx1_summary["duplicates"][0],
            )
        except Exception as e:
            result.errors.append(f"move_tx1_files: {e}")
            logger.exception("Step 4 failed")
    else:
        logger.info("Step 4: Skipped (already completed)")

    # Step 5: Sort .dat files by week
    if "sort_by_week" not in result.steps_completed:
        if dat_folder:
            logger.info("Step 5: Sorting .dat files into weekly folders")
            try:
                # Extract month/year from the base_dir name (e.g. RB202601v1)
                dirname = base_dir.name
                match = re.match(r".*(\d{4})(\d{2})v\d+$", dirname)
                if not match:
                    raise ValueError(
                        f"Cannot parse year/month from folder name: {dirname}"
                    )
                year = int(match.group(1))
                month = int(match.group(2))

                week_counts = move_files_by_week(
                    dat_folder, final_dir, month, year,
                )
                result.week_counts = week_counts
                _record_step("sort_by_week")
                logger.info("Step 5 complete: %s", week_counts)
            except Exception as e:
                result.errors.append(f"sort_by_week: {e}")
                logger.exception("Step 5 failed")
        else:
            logger.warning("Step 5: Skipped (no dat folder available)")
    else:
        logger.info("Step 5: Skipped (already completed)")

    # Final summary
    total_steps = 4  # steps 2, 3, 4, 5
    completed_processing = len([
        s for s in result.steps_completed if s != "create_folders"
    ])
    logger.info(
        "Workspace processing complete: %d/%d steps succeeded",
        completed_processing,
        total_steps,
    )
    if result.errors:
        logger.warning("Errors: %s", result.errors)

    return result
