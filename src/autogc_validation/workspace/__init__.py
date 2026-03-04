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

import calendar
import json
import logging
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import nbformat
from autogc_validation.database.enums import Sites
from autogc_validation.workspace.folders import generate_monthly_folder_structure
from autogc_validation.workspace.files import (
    unzip_files,
    move_dat_files,
    move_tx1_files,
    move_files_by_week,
    rename_dattxt_files_to_txt,
    convert_folder_contents_to_pdf,
)

logger = logging.getLogger(__name__)

_STATE_FILENAME = ".workspace_state.json"

# Resolve database path relative to the project root (3 levels up from this file:
# workspace/ -> autogc_validation/ -> src/ -> project root)
_DBPATH = str(Path(__file__).parents[3] / "data" / "autogc.db")


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
    data_dir: Optional[Path] = None
    unzipped: Optional[list[Path]] = None
    documents: Optional[list[Path]] = None
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
            "data_dir": str(self.data_dir) if self.data_dir else None,
            "unzipped": [str(p) for p in self.unzipped] if self.unzipped else None,
            "documents": [str(p) for p in self.documents] if self.documents else None,
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
            data_dir=Path(data["data_dir"]) if data.get("data_dir") else None,
            unzipped=[Path(p) for p in data["unzipped"]] if data.get("unzipped") else None,
            documents=[Path(p) for p in data["documents"]] if data.get("documents") else None,
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
    workspace_dir: Union[str, Path], force = False
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
    if "unzip_files" not in result.steps_completed or force:
        logger.info("Step 2: Unzipping files in temp/")
        try:
            extracted = unzip_files(temp_dir, temp_dir, create_subfolders=True)
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
    if "move_dat_files" not in result.steps_completed or force:
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
    if "move_tx1_files" not in result.steps_completed or force:
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
    if "sort_by_week" not in result.steps_completed or force:
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

    # Step 6: Convert documents in temp/ to PDF
    if "convert_documents" not in result.steps_completed or force:
        logger.info("Step 6: Converting documents in temp/ to PDF")
        try:
            documents_dir = base_dir / "MDVR"
            converted = convert_folder_contents_to_pdf(temp_dir, documents_dir)
            result.documents = converted
            _record_step("convert_documents")
            logger.info("Step 6 complete: %d document(s) converted", len(converted))
        except Exception as e:
            result.errors.append(f"convert_documents: {e}")
            logger.exception("Step 6 failed")
    else:
        logger.info("Step 6: Skipped (already completed)")

    # Final summary
    total_steps = 5  # steps 2, 3, 4, 5, 6
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
    num_days = calendar.monthrange(year, month)[1]
    yyyymm = f"{year}{month:02d}"
    workspace_dir = str(result.base_dir)
    start_date_str = f"{year}-{month:02d}-01 00:00"
    end_date_str = f"{year}-{month:02d}-{num_days} 23:59"
    site_code: int = Sites[site]

    nb = nbformat.v4.new_notebook()
    nb.cells = [
        # --- Header ---
        nbformat.v4.new_markdown_cell(
            f"# {site} {yyyymm} Monthly Validation"
        ),
        nbformat.v4.new_code_cell(
            "import logging\n"
            "from pathlib import Path\n\n"
            "logging.basicConfig(level=logging.WARNING)\n"
            "logger = logging.getLogger(__name__)"
        ),

        # --- Configuration ---
        nbformat.v4.new_markdown_cell("## Configuration"),
        nbformat.v4.new_code_cell(
            "import pandas as pd\n\n"
            f'workspace_dir = Path(r"{workspace_dir}")\n'
            f'data_dir = Path(r"{result.data_dir}")\n'
            f'site_id = {site_code}\n'
            f'year  = {year}\n'
            f'month = {month}\n'
            f'database = Path(r"{_DBPATH}")\n'
            f'start_date = "{start_date_str}"\n'
            f'end_date   = "{end_date_str}"\n\n'
            f'# Week date ranges (boundaries: 1-7, 8-14, 15-21, 22-end)\n'
            f'weeks = {{\n'
            f'    1: (pd.Timestamp({year}, {month},  1), pd.Timestamp({year}, {month},  7, 23, 59, 59)),\n'
            f'    2: (pd.Timestamp({year}, {month},  8), pd.Timestamp({year}, {month}, 14, 23, 59, 59)),\n'
            f'    3: (pd.Timestamp({year}, {month}, 15), pd.Timestamp({year}, {month}, 21, 23, 59, 59)),\n'
            f'    4: (pd.Timestamp({year}, {month}, 22), pd.Timestamp({year}, {month}, {num_days}, 23, 59, 59)),\n'
            f'}}'
        ),

        # --- Database Update ---
        nbformat.v4.new_markdown_cell("## Database update"),
        nbformat.v4.new_code_cell(),
        nbformat.v4.new_code_cell(
            "from autogc_validation.database.management import dump_database\n\n"
            "dump_database(\n"
            "    database_path=database,\n"
            "    output_path=database.with_suffix('.sql'),\n"
            ")\n"
            'print("Done. Remember to commit data/autogc.sql.")'
        ),

        # --- File processing ---
        nbformat.v4.new_markdown_cell(
            "## 1. Copy and process files\n\n"
            "Copy zipped `.zip` files from the network location into "
            f"`{Path(workspace_dir).as_posix()}/temp`, then run the cell below."
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.workspace import process_workspace\n\n"
            "result = process_workspace(workspace_dir)\n\n"
            'print(f"Steps completed: {result.steps_completed}")\n'
            'print(f"Errors: {result.errors}")\n'
            "if result.dat_summary:\n"
            "    print(f\"DAT files: {result.dat_summary['found'][0]} found, "
            "{result.dat_summary['copied'][0]} copied, "
            "{result.dat_summary['duplicates'][0]} duplicated\")\n"
            "if result.tx1_summary:\n"
            "    print(f\"TX1 files: {result.tx1_summary['found'][0]} found, "
            "{result.tx1_summary['copied'][0]} copied, "
            "{result.tx1_summary['duplicates'][0]} duplicated\")\n"
            "if result.week_counts:\n"
            '    print(f"Week counts: {result.week_counts}")'
        ),

        # --- Load dataset ---
        nbformat.v4.new_markdown_cell("## 2. Load dataset"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.dataset import Dataset\n\n"
            "ds = Dataset(data_dir)\n"
            'print(f"Loaded {len(ds.samples)} samples")\n'
            "ds.data.head()"
        ),
        nbformat.v4.new_code_cell(
            "# Helper: print a day-by-day failure summary from a boolean wide DataFrame\n"
            "from autogc_validation.database.enums import aqs_to_name\n\n"
            "def print_failures(failures: 'pd.DataFrame', label: str) -> None:\n"
            '    """Print one line per sample showing filename and failing compound names."""\n'
            "    compound_cols = [c for c in failures.columns if isinstance(c, int)]\n"
            "    n_fail = 0\n"
            "    for ts, row in failures.iterrows():\n"
            "        failing = [aqs_to_name(c) for c in compound_cols if row[c] != 0]\n"
            "        if failing:\n"
            "            n_fail += 1\n"
            f'            print(f"  {{ts:%Y-%m-%d %H:%M}}  {{row[\'filename\']}}  →  {{\', \'.join(failing)}}")\n'
            f'    print(f"{{label}}: {{n_fail}} / {{len(failures)}} samples with failures")'
        ),

        # --- Monthly ambient compound plots ---
        nbformat.v4.new_markdown_cell("## 3. Monthly ambient compound plots"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.ambient import plot_ambient_comparisons\n\n"
            f"plot_ambient_comparisons(ds.ambient, '{site}', {year}, {month})"
        ),

        # --- Monthly retention time validation ---
        nbformat.v4.new_markdown_cell("## 4. Monthly retention time validation"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.rt import plot_rt\n"
            "from autogc_validation.qc.rt_outliers import detect_rt_outliers\n"
            "from autogc_validation.qc.utils import get_compound_cols\n"
            "from autogc_validation.database.enums import RT_REFERENCE_CODES\n\n"
            "rt_ref_cols = [c for c in RT_REFERENCE_CODES if c in ds.rt.columns]\n"
            "# rt_compound_cols = get_compound_cols(ds.rt)  # uncomment to check all compounds\n\n"
            f"plot_rt(ds.rt, ds.data, '{site}', {year}, {month}, samp_type='s')\n"
            "rt_outliers = detect_rt_outliers(ds.rt[ds.rt['sample_type'] == 's'], rt_ref_cols)\n"
            'print(f"Monthly RT outliers: {len(rt_outliers)}")\n'
            "rt_outliers"
        ),

        # --- Weekly method optimization ---
        nbformat.v4.new_markdown_cell("## 5. Weekly method optimization"),

        nbformat.v4.new_markdown_cell("### Week 1"),
        nbformat.v4.new_code_cell(
            "ambient_w1 = ds.ambient.loc[weeks[1][0]:weeks[1][1]]\n"
            f"plot_ambient_comparisons(ambient_w1, '{site}', {year}, {month}, label='Week 1')"
        ),
        nbformat.v4.new_code_cell(
            "rt_w1   = ds.rt.loc[weeks[1][0]:weeks[1][1]]\n"
            "data_w1 = ds.data.loc[weeks[1][0]:weeks[1][1]]\n"
            f"plot_rt(rt_w1, data_w1, '{site}', {year}, {month}, samp_type='s')\n"
            "rt_outliers_w1 = detect_rt_outliers(rt_w1[rt_w1['sample_type'] == 's'], rt_ref_cols)\n"
            "# rt_outliers_w1 = detect_rt_outliers(rt_w1[rt_w1['sample_type'] == 's'], rt_compound_cols)  # all compounds\n"
            'print(f"Week 1 RT outliers: {len(rt_outliers_w1)}")\n'
            "rt_outliers_w1"
        ),

        nbformat.v4.new_markdown_cell("### Week 2"),
        nbformat.v4.new_code_cell(
            "ambient_w2 = ds.ambient.loc[weeks[2][0]:weeks[2][1]]\n"
            f"plot_ambient_comparisons(ambient_w2, '{site}', {year}, {month}, label='Week 2')"
        ),
        nbformat.v4.new_code_cell(
            "rt_w2   = ds.rt.loc[weeks[2][0]:weeks[2][1]]\n"
            "data_w2 = ds.data.loc[weeks[2][0]:weeks[2][1]]\n"
            f"plot_rt(rt_w2, data_w2, '{site}', {year}, {month}, samp_type='s')\n"
            "rt_outliers_w2 = detect_rt_outliers(rt_w2[rt_w2['sample_type'] == 's'], rt_ref_cols)\n"
            "# rt_outliers_w2 = detect_rt_outliers(rt_w2[rt_w2['sample_type'] == 's'], rt_compound_cols)  # all compounds\n"
            'print(f"Week 2 RT outliers: {len(rt_outliers_w2)}")\n'
            "rt_outliers_w2"
        ),

        nbformat.v4.new_markdown_cell("### Week 3"),
        nbformat.v4.new_code_cell(
            "ambient_w3 = ds.ambient.loc[weeks[3][0]:weeks[3][1]]\n"
            f"plot_ambient_comparisons(ambient_w3, '{site}', {year}, {month}, label='Week 3')"
        ),
        nbformat.v4.new_code_cell(
            "rt_w3   = ds.rt.loc[weeks[3][0]:weeks[3][1]]\n"
            "data_w3 = ds.data.loc[weeks[3][0]:weeks[3][1]]\n"
            f"plot_rt(rt_w3, data_w3, '{site}', {year}, {month}, samp_type='s')\n"
            "rt_outliers_w3 = detect_rt_outliers(rt_w3[rt_w3['sample_type'] == 's'], rt_ref_cols)\n"
            "# rt_outliers_w3 = detect_rt_outliers(rt_w3[rt_w3['sample_type'] == 's'], rt_compound_cols)  # all compounds\n"
            'print(f"Week 3 RT outliers: {len(rt_outliers_w3)}")\n'
            "rt_outliers_w3"
        ),

        nbformat.v4.new_markdown_cell("### Week 4"),
        nbformat.v4.new_code_cell(
            "ambient_w4 = ds.ambient.loc[weeks[4][0]:weeks[4][1]]\n"
            f"plot_ambient_comparisons(ambient_w4, '{site}', {year}, {month}, label='Week 4')"
        ),
        nbformat.v4.new_code_cell(
            "rt_w4   = ds.rt.loc[weeks[4][0]:weeks[4][1]]\n"
            "data_w4 = ds.data.loc[weeks[4][0]:weeks[4][1]]\n"
            f"plot_rt(rt_w4, data_w4, '{site}', {year}, {month}, samp_type='s')\n"
            "rt_outliers_w4 = detect_rt_outliers(rt_w4[rt_w4['sample_type'] == 's'], rt_ref_cols)\n"
            "# rt_outliers_w4 = detect_rt_outliers(rt_w4[rt_w4['sample_type'] == 's'], rt_compound_cols)  # all compounds\n"
            'print(f"Week 4 RT outliers: {len(rt_outliers_w4)}")\n'
            "rt_outliers_w4"
        ),

        # --- Query MDL and canister periods ---
        nbformat.v4.new_markdown_cell("## 6. Query MDL and canister concentration periods"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.database.operations import (\n"
            "    get_mdl_periods, get_canister_periods\n"
            ")\n"
            "from autogc_validation.database.enums import ConcentrationUnit\n\n"
            "mdl_periods = get_mdl_periods(database, site_id, start_date, end_date, ConcentrationUnit.PPBC)\n"
            'print(f"MDL periods: {len(mdl_periods)} (changes on: {list(mdl_periods.index.date)})")\n\n'
            'cvs_periods = get_canister_periods(database, site_id, "CVS", start_date, end_date, ConcentrationUnit.PPBC)\n'
            'lcs_periods = get_canister_periods(database, site_id, "LCS", start_date, end_date, ConcentrationUnit.PPBC)\n'
            'rts_periods = get_canister_periods(database, site_id, "RTS", start_date, end_date, ConcentrationUnit.PPBC)\n'
            'print(f"Canister periods — CVS: {len(cvs_periods)}, LCS: {len(lcs_periods)}, RTS: {len(rts_periods)}")'
        ),

        # --- Blank QC ---
        nbformat.v4.new_markdown_cell("## 7. Blank check"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.blanks import compounds_above_mdl\n\n"
            "mdl_failures, threshold_failures = compounds_above_mdl(ds.blanks, mdl_periods)\n\n"
            'print("--- Compounds exceeding MDL ---")\n'
            'print_failures(mdl_failures, "MDL exceedances")\n\n'
            'print("\\n--- Compounds exceeding 0.5 ppbC ---")\n'
            'print_failures(threshold_failures, "Threshold exceedances")'
        ),

        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.qc import plot_blank_concentrations\n\n"
            f"plot_blank_concentrations(ds.blanks, mdl_failures, '{site}', {year}, {month})"
        ),

        # --- Recovery QC ---
        nbformat.v4.new_markdown_cell("## 8. QC recovery checks (CVS / LCS / RTS)"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.recovery import check_qc_recovery\n\n"
            "cvs_failures = check_qc_recovery(ds.cvs, cvs_periods)\n"
            "lcs_failures = check_qc_recovery(ds.lcs, lcs_periods)\n"
            "rts_failures = check_qc_recovery(ds.rts, rts_periods)\n\n"
            'print("--- CVS ---")\n'
            'print_failures(cvs_failures, "CVS")\n\n'
            'print("\\n--- LCS ---")\n'
            'print_failures(lcs_failures, "LCS")\n\n'
            'print("\\n--- RTS ---")\n'
            'print_failures(rts_failures, "RTS")'
        ),

        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.qc import plot_qc_recovery\n\n"
            f"plot_qc_recovery(ds.cvs, cvs_periods, 'CVS', '{site}', {year}, {month})\n"
            f"plot_qc_recovery(ds.lcs, lcs_periods, 'LCS', '{site}', {year}, {month})\n"
            f"plot_qc_recovery(ds.rts, rts_periods, 'RTS', '{site}', {year}, {month})"
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.precision import check_cvs_precision\n\n"
            "precision_failures, cvs_precision_pairs = check_cvs_precision(ds.cvs)\n"
            f'print(f"CVS precision pairs found: {{len(cvs_precision_pairs)}}")\n\n'
            "compound_cols_p = [c for c in precision_failures.columns if isinstance(c, int)]\n"
            "for ts, row in precision_failures.iterrows():\n"
            "    failing = [aqs_to_name(c) for c in compound_cols_p if row[c] == 1]\n"
            "    if failing:\n"
            f'        print(f"  {{ts:%Y-%m-%d %H:%M}}  {{row[\'filename\']}}  →  {{\', \'.join(failing)}}")\n'
            "n_fail_p = int((precision_failures[compound_cols_p] == 1).any(axis=1).sum())\n"
            f'print(f"Precision failures: {{n_fail_p}} / {{len(cvs_precision_pairs)}} pairs")'
        ),

        # --- QC Review table ---
        nbformat.v4.new_markdown_cell(
            "## 9. QC Review table\n\n"
            "Builds the human-readable QC summary table and writes it to the "
            "'QC Review' sheet of the MDVR spreadsheet.\n\n"
            "Set `blank_start_row`, `cvs_start_row`, `lcs_start_row`, and "
            "`rts_start_row` to match the merged-cell row ranges in your MDVR template."
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports import (\n"
            "    build_blank_qc_table, build_precision_qc_table,\n"
            "    build_recovery_qc_table, write_qc_table_to_excel,\n"
            ")\n\n"
            f'mdvr_path = workspace_dir / "MDVR" / "{site}{yyyymm}_MDVR.xlsx"\n\n'
            "# Adjust these start rows to match the merged-cell ranges in the MDVR template.\n"
            "blank_start_row     = 73\n"
            "cvs_start_row       = 22\n"
            "lcs_start_row       = 15\n"
            "rts_start_row       = 7\n"
            "precision_start_row = 7\n\n"
            "blank_table     = build_blank_qc_table(mdl_failures, threshold_failures)\n"
            "cvs_table       = build_recovery_qc_table(cvs_failures, 'CVS')\n"
            "lcs_table       = build_recovery_qc_table(lcs_failures, 'LCS')\n"
            "rts_table       = build_recovery_qc_table(rts_failures, 'RTS')\n"
            "precision_table = build_precision_qc_table(precision_failures)\n\n"
            "write_qc_table_to_excel(blank_table,     mdvr_path, mdvr_path, 'Field Blank',    blank_start_row)\n"
            "write_qc_table_to_excel(cvs_table,       mdvr_path, mdvr_path, 'CVS',            cvs_start_row)\n"
            "write_qc_table_to_excel(lcs_table,       mdvr_path, mdvr_path, 'LCS',            lcs_start_row)\n"
            "write_qc_table_to_excel(rts_table,       mdvr_path, mdvr_path, 'RTS',            rts_start_row)\n"
            "write_qc_table_to_excel(precision_table, mdvr_path, mdvr_path, 'CVS Precision',  precision_start_row)\n"
            f'print(f"QC Review table written to {{mdvr_path}}")'
        ),

        # --- Station temperature ---
        nbformat.v4.new_markdown_cell(
            "## 10. Station temperature check\n\n"
            "Requires an AirVision database connection. "
            "Hours where station temperature exceeds 30\u00b0C are nulled with flag AE."
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.room_temp import plot_station_temp\n"
            "from autogc_validation.reports import build_temp_null_lines\n\n"
            "# Temperature threshold for AE null qualification (°C).\n"
            "temp_null_threshold = 30.0\n\n"
            "# Optional: timestamps of the nearest temperature reading from adjacent months.\n"
            "# Set if the first or last hour of the month exceeds the threshold.\n"
            "prior_temp = None\n"
            "next_temp  = None\n\n"
            f"temp_result = plot_station_temp('{site}', {month}, {year}, upper_threshold=temp_null_threshold)\n"
            "hourly_max = temp_result.temperatures.resample('h').max()\n"
            "n_over = int((hourly_max > temp_null_threshold).sum())\n"
            'print(f"Hours exceeding {temp_null_threshold}°C: {n_over}")'
        ),
        nbformat.v4.new_code_cell(
            "temp_null_lines = build_temp_null_lines(\n"
            "    temp_result.temperatures,\n"
            "    threshold=temp_null_threshold,\n"
            "    prior_temp=prior_temp,\n"
            "    next_temp=next_temp,\n"
            ")\n"
            'print(f"Temperature null lines: {len(temp_null_lines)}")\n'
            "temp_null_lines"
        ),

        # --- Ambient screening ---
        nbformat.v4.new_markdown_cell("## 11. Ambient screening"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.screening import (\n"
            "    check_ratios, check_overrange_values, check_daily_max_tnmhc\n"
            ")\n\n"
            "# Compound ratio screening (EPA TAD Table 10-1)\n"
            "# Note: check_ratios uses the first MDL period for threshold comparisons.\n"
            "# If MDLs changed mid-month, split the ambient DataFrame by period manually.\n"
            "ratios = check_ratios(ds.data, mdl_periods)\n"
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

        # --- Reprocess Plan ---
        nbformat.v4.new_markdown_cell("## 12. Reprocess Plan"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports import fill_reprocess_plan\n\n"
            "fill_reprocess_plan(\n"
            "    ds.data, mdvr_path, mdvr_path, year, month,\n"
            "    overrange=overrange, daily_tnmhc=daily_tnmhc,\n"
            ")"
        ),

        # --- MDVR ---
        nbformat.v4.new_markdown_cell("## 13. MDVR qualifier generation"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports import (\n"
            "    build_blank_qualifier_lines,\n"
            "    build_precision_qualifier_lines,\n"
            "    build_qc_qualifier_lines,\n"
            "    write_mdvr_to_excel,\n"
            ")\n\n"
            "# Optional: timestamps of the nearest blank/QC sample from adjacent months.\n"
            "# Set these when the first or last sample of the month fails its check so\n"
            "# that the flagged interval extends to the correct boundary rather than the\n"
            "# dataset edge. Leave as None if not applicable.\n"
            "prior_blank = None  # e.g. pd.Timestamp('2026-01-31 01:00')\n"
            "next_blank  = None  # e.g. pd.Timestamp('2026-03-01 01:00')\n"
            "prior_cvs   = None\n"
            "next_cvs    = None\n"
            "prior_lcs   = None\n"
            "next_lcs    = None\n\n"
            "blank_quals = build_blank_qualifier_lines(\n"
            "    ds.data, mdl_failures, threshold_failures,\n"
            "    prior_blank=prior_blank, next_blank=next_blank,\n"
            ")\n"
            'print(f"Blank qualifier lines: {len(blank_quals)}")\n\n'
            "cvs_quals = build_qc_qualifier_lines(\n"
            "    ds.data, cvs_failures, 'c', prior_qc=prior_cvs, next_qc=next_cvs,\n"
            ")\n"
            "lcs_quals = build_qc_qualifier_lines(\n"
            "    ds.data, lcs_failures, 'e', prior_qc=prior_lcs, next_qc=next_lcs,\n"
            ")\n"
            'print(f"QC qualifier lines — CVS: {len(cvs_quals)}, LCS: {len(lcs_quals)}")\n\n'
            "precision_quals = build_precision_qualifier_lines(\n"
            "    ds.data, precision_failures, cvs_precision_pairs,\n"
            "    prior_qc=prior_cvs, next_qc=next_cvs,\n"
            ")\n"
            'print(f"Precision qualifier lines: {len(precision_quals)}")'
        ),
        nbformat.v4.new_markdown_cell("### Export qualifiers to Excel"),
        nbformat.v4.new_code_cell(
            "all_quals = pd.concat(\n"
            "    [blank_quals, cvs_quals, lcs_quals, precision_quals, temp_null_lines],\n"
            "    ignore_index=True,\n"
            ")\n"
            'print(f"Total qualifier lines: {len(all_quals)}")\n'
            "all_quals"
        ),
        nbformat.v4.new_code_cell(
            "write_mdvr_to_excel(all_quals, mdvr_path, mdvr_path)\n"
            f'print(f"Qualifiers written to {{mdvr_path}}")'
        ),

        # --- Monthly report ---
        nbformat.v4.new_markdown_cell(
            "## 14. Monthly validation report\n\n"
            "Run this cell once you have finished reviewing the full month and "
            "are satisfied with the data qualification.  "
            "The generated `.qmd` file can be rendered to a self-contained HTML "
            "report with:\n\n"
            "```\n"
            f"quarto render {site}{yyyymm}_report.qmd\n"
            "```"
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports.monthly_report import generate_monthly_report\n\n"
            f"report_path = generate_monthly_report(result, '{site}', year, month)\n"
            f'print(f"Report template written to {{report_path}}")'
        ),
    ]

    notebook_path = result.base_dir / f"{site}{yyyymm}.ipynb"
    nbformat.write(nb, str(notebook_path))
    logger.info("Notebook created: %s", notebook_path)
    return notebook_path


def _generate_checklist(
    result: WorkspaceResult,
    site: str,
    year: int,
    month: int,
) -> Path:
    """Generate a monthly validation checklist inside the workspace.

    Creates a Markdown file with checkbox sections for each week and
    for month-level tasks.

    Args:
        result: WorkspaceResult from create_workspace (must have base_dir set).
        site: Site name code (e.g. "RB").
        year: Year.
        month: Month number (1-12).

    Returns:
        Path to the created checklist file.
    """
    yyyymm = f"{year}{month:02d}"

    content = f"""# {site} {yyyymm} Validation Checklist

## Monthly
- [ ] Import and process data files
- [ ] Load dataset and verify sample counts
- [ ] Query MDLs and canister concentrations
- [ ] Run blank QC checks
- [ ] Run recovery checks (CVS, LCS, RTS)
- [ ] Write QC Review table to MDVR spreadsheet
- [ ] Run ambient screening (ratios, overrange, TNMHC)
- [ ] Generate MDVR qualifiers
- [ ] Submit AQS files
- [ ] File MDVR

## Week 1
- [ ] Review data completeness
- [ ] Check for missing or corrupted files
- [ ] Notes:

## Week 2
- [ ] Review data completeness
- [ ] Check for missing or corrupted files
- [ ] Notes:

## Week 3
- [ ] Review data completeness
- [ ] Check for missing or corrupted files
- [ ] Notes:

## Week 4
- [ ] Review data completeness
- [ ] Check for missing or corrupted files
- [ ] Notes:
"""

    checklist_path = result.base_dir / f"{site}{yyyymm}_checklist.md"
    checklist_path.write_text(content)
    logger.info("Checklist created: %s", checklist_path)
    return checklist_path


def _copy_mdvr_template(
    result: WorkspaceResult,
    site: str,
    year: int,
    month: int,
    project_dir: Path,
) -> None:
    """Copy the site MDVR template into the workspace MDVR folder.

    Looks for ``templates/mdvr/{site}_MDVR_template.xlsx`` in the project
    root. Logs a warning if the template does not exist rather than raising.
    """
    yyyymm = f"{year}{month:02d}"
    template_path = project_dir / "templates" / "mdvr" / f"{site}_MDVR_template.xlsx"

    if not template_path.exists():
        logger.warning("MDVR template not found for site %s: %s", site, template_path)
        return

    dest = result.base_dir / "MDVR" / f"{site}{yyyymm}_MDVR.xlsx"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(template_path, dest)
    logger.info("Copied MDVR template to %s", dest)


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
      - Copies ``templates/mdvr/{site}_MDVR_template.xlsx`` to the workspace

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
        result.data_dir = data_dir
        if result.base_dir is not None:
            result.save()

        # Generate notebook, checklist, and copy MDVR template
        if result.base_dir is not None:
            _generate_notebook(result, site, year, month)
            _generate_checklist(result, site, year, month)
            _copy_mdvr_template(result, site, year, month, project_dir)

        results[site] = result
        logger.info("Site %s setup complete", site)

    return results
