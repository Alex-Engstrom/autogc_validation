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

import nbformat

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


def _generate_notebook(
    result: WorkspaceResult,
    site: str,
    year: int,
    month: int,
) -> Path:
    """Generate a pre-filled Jupyter notebook inside the workspace.

    The notebook mirrors the workspace_workflow template with paths
    hardcoded for the given site and month.

    Args:
        result: WorkspaceResult from create_workspace (must have base_dir set).
        site: Site name code (e.g. "RB").
        year: Year.
        month: Month number (1-12).

    Returns:
        Path to the created notebook file.
    """
    yyyymm = f"{year}{month:02d}"

    workspace_dir = str(result.base_dir)
    date_str = f"{year}-{month:02d}-01 00:00"

    nb = nbformat.v4.new_notebook()
    nb.cells = [
        # --- Header ---
        nbformat.v4.new_markdown_cell(
            f"# {site} {yyyymm} Monthly Validation"
        ),
        nbformat.v4.new_code_cell(
            "import logging\n"
            "from pathlib import Path\n\n"
            "logging.basicConfig(level=logging.INFO)\n"
            "logger = logging.getLogger(__name__)"
        ),

        # --- Configuration ---
        nbformat.v4.new_markdown_cell("## Configuration"),
        nbformat.v4.new_code_cell(
            f'workspace_dir = Path(r"{workspace_dir}")\n'
            f'site_id = 0  # TODO: set AQS site ID\n'
            f'database = r""  # TODO: path to SQLite database\n'
            f'date = "{date_str}"'
        ),

        # --- File processing ---
        nbformat.v4.new_markdown_cell(
            "## 1. Copy and process files\n\n"
            "Copy zipped `.zip` files from the network location into "
            f"`{workspace_dir}\\temp`, then run the cell below."
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.workspace import process_workspace\n\n"
            "result = process_workspace(workspace_dir)\n\n"
            'print(f"Steps completed: {result.steps_completed}")\n'
            'print(f"Errors: {result.errors}")\n'
            "if result.dat_summary:\n"
            "    print(f\"DAT files: {result.dat_summary['found'][0]} found, "
            "{result.dat_summary['copied'][0]} copied\")\n"
            "if result.tx1_summary:\n"
            "    print(f\"TX1 files: {result.tx1_summary['found'][0]} found, "
            "{result.tx1_summary['copied'][0]} copied\")\n"
            "if result.week_counts:\n"
            '    print(f"Week counts: {result.week_counts}")'
        ),

        # --- Load dataset ---
        nbformat.v4.new_markdown_cell("## 2. Load dataset"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.dataset import Dataset\n\n"
            'ds = Dataset(workspace_dir / "FINAL")\n'
            'print(f"Loaded {len(ds.samples)} samples")\n'
            "ds.data.head()"
        ),

        # --- Query MDLs ---
        nbformat.v4.new_markdown_cell("## 3. Query MDLs and canister concentrations"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.database.operations.mdl_info import get_active_mdls\n"
            "from autogc_validation.database.operations.canister_info import get_active_canister_concentrations\n\n"
            "mdls = get_active_mdls(database, site_id, date)\n"
            'print(f"MDLs loaded: {len(mdls)} compounds")\n\n'
            'cvs_conc = get_active_canister_concentrations(database, site_id, "CVS", date)\n'
            'lcs_conc = get_active_canister_concentrations(database, site_id, "LCS", date)\n'
            'rts_conc = get_active_canister_concentrations(database, site_id, "RTS", date)\n'
            'print(f"Canister concentrations loaded — CVS: {len(cvs_conc)}, LCS: {len(lcs_conc)}, RTS: {len(rts_conc)}")'
        ),

        # --- Blank QC ---
        nbformat.v4.new_markdown_cell("## 4. Blank check"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.blanks import compounds_above_mdl, compounds_above_mdl_wide\n\n"
            "blank_results = compounds_above_mdl(ds.data, mdls)\n"
            "blank_wide = compounds_above_mdl_wide(ds.data, mdls)\n\n"
            "failing_blanks = blank_results[\n"
            "    blank_results['compounds_above_mdl'].apply(lambda x: x != ['__NONE__'])\n"
            "]\n"
            'print(f"Blanks with exceedances: {len(failing_blanks)} / {len(blank_results)}")\n'
            "failing_blanks"
        ),

        # --- Recovery QC ---
        nbformat.v4.new_markdown_cell("## 5. QC recovery checks (CVS / LCS / RTS)"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.recovery import check_qc_recovery, check_qc_recovery_wide\n\n"
            "# CVS recovery\n"
            "cvs_results = check_qc_recovery(ds.data, 'c', cvs_conc, blend_ratio=1.0)\n"
            "cvs_wide = check_qc_recovery_wide(ds.data, 'c', cvs_conc, blend_ratio=1.0)\n"
            "cvs_failing = cvs_results[cvs_results['failing_qc'].apply(lambda x: x != ['__NONE__'])]\n"
            'print(f"CVS failures: {len(cvs_failing)} / {len(cvs_results)}")\n\n'
            "# LCS recovery\n"
            "lcs_results = check_qc_recovery(ds.data, 'e', lcs_conc, blend_ratio=1.0)\n"
            "lcs_wide = check_qc_recovery_wide(ds.data, 'e', lcs_conc, blend_ratio=1.0)\n"
            "lcs_failing = lcs_results[lcs_results['failing_qc'].apply(lambda x: x != ['__NONE__'])]\n"
            'print(f"LCS failures: {len(lcs_failing)} / {len(lcs_results)}")\n\n'
            "# RTS recovery\n"
            "rts_results = check_qc_recovery(ds.data, 'q', rts_conc, blend_ratio=1.0)\n"
            "rts_wide = check_qc_recovery_wide(ds.data, 'q', rts_conc, blend_ratio=1.0)\n"
            "rts_failing = rts_results[rts_results['failing_qc'].apply(lambda x: x != ['__NONE__'])]\n"
            'print(f"RTS failures: {len(rts_failing)} / {len(rts_results)}")'
        ),

        # --- Ambient screening ---
        nbformat.v4.new_markdown_cell("## 6. Ambient screening"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.screening import (\n"
            "    check_ratios, check_overrange_values, check_daily_max_tnmhc\n"
            ")\n\n"
            "# Compound ratio screening (EPA TAD Table 10-1)\n"
            "ratios = check_ratios(ds.data, mdls)\n"
            'print(f"Ratio flags: {len(ratios)}")\n'
            "if not ratios.empty:\n"
            "    display(ratios)\n\n"
            "# Overrange detection\n"
            "overrange = check_overrange_values(ds.data)\n"
            'print(f"\\nOverrange values: {len(overrange)}")\n'
            "if not overrange.empty:\n"
            "    display(overrange)\n\n"
            "# Daily max TNMHC\n"
            "daily_tnmhc = check_daily_max_tnmhc(ds.data)\n"
            'print(f"\\nDaily max TNMHC:")\n'
            "daily_tnmhc"
        ),

        # --- MDVR ---
        nbformat.v4.new_markdown_cell("## 7. MDVR qualifier generation"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.mdvr import (\n"
            "    build_blank_qualifier_lines,\n"
            "    build_qc_qualifier_lines,\n"
            "    write_mdvr_to_excel,\n"
            ")\n\n"
            "blank_quals = build_blank_qualifier_lines(ds.data, blank_wide)\n"
            'print(f"Blank qualifier lines: {len(blank_quals)}")\n\n'
            "cvs_quals = build_qc_qualifier_lines(ds.data, cvs_wide, 'c')\n"
            "lcs_quals = build_qc_qualifier_lines(ds.data, lcs_wide, 'e')\n"
            "rts_quals = build_qc_qualifier_lines(ds.data, rts_wide, 'q')\n"
            'print(f"QC qualifier lines — CVS: {len(cvs_quals)}, LCS: {len(lcs_quals)}, RTS: {len(rts_quals)}")'
        ),
        nbformat.v4.new_markdown_cell(
            "### Export MDVR to Excel\n\n"
            "Uncomment and set template/output paths to export."
        ),
        nbformat.v4.new_code_cell(
            "import pandas as pd\n\n"
            "all_quals = pd.concat([blank_quals, cvs_quals, lcs_quals, rts_quals], ignore_index=True)\n"
            'print(f"Total qualifier lines: {len(all_quals)}")\n'
            "all_quals\n\n"
            "# write_mdvr_to_excel(\n"
            "#     all_quals,\n"
            '#     template_path=Path(r"path/to/template.xlsx"),\n'
            f'#     output_path=workspace_dir / "MDVR" / "{site}{yyyymm}_MDVR.xlsx",\n'
            "# )"
        ),
    ]

    notebook_path = result.base_dir / f"{site}{yyyymm}.ipynb"
    nbformat.write(nb, str(notebook_path))
    logger.info("Notebook created: %s", notebook_path)
    return notebook_path


def start_month(
    sites: list[str],
    project_dir: Union[str, Path],
    year: int,
    month: int,
) -> dict[str, WorkspaceResult]:
    """Initialize workspaces for multiple sites for a given month.

    For each site this function:
      - Creates ``project_dir/validation/{site}/``
      - Creates ``project_dir/data/{site}/{YYYYMM}/``
      - Calls :func:`create_workspace` to build the folder structure
      - Generates a pre-filled Jupyter notebook in the workspace

    Args:
        sites: List of site name codes (e.g. ``["RB", "HW", "LP"]``).
        project_dir: Path to the autogc_validation project root.
        year: Year.
        month: Month number (1-12).

    Returns:
        Dict mapping site name to its WorkspaceResult.
    """
    project_dir = Path(project_dir)
    yyyymm = f"{year}{month:02d}"
    results: dict[str, WorkspaceResult] = {}

    for site in sites:
        logger.info("Starting month setup for site %s (%s)", site, yyyymm)

        # Create site validation directory
        validation_dir = project_dir / "validation" / site
        validation_dir.mkdir(parents=True, exist_ok=True)

        # Create site data directory
        data_dir = project_dir / "data" / site / yyyymm
        data_dir.mkdir(parents=True, exist_ok=True)

        # Create workspace folder structure
        result = create_workspace(validation_dir, site, year, month)

        # Generate notebook
        if result.base_dir is not None:
            _generate_notebook(result, site, year, month)

        results[site] = result
        logger.info("Site %s setup complete", site)

    return results
