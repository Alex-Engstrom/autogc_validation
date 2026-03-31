# -*- coding: utf-8 -*-
"""
Jupyter notebook generation for monthly AutoGC validation workspaces.
"""

import calendar
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import nbformat

from autogc_validation.database.enums import Sites

if TYPE_CHECKING:
    from autogc_validation.workspace import WorkspaceResult

logger = logging.getLogger(__name__)

# Resolve database path relative to the project root (3 levels up from this file:
# workspace/ -> autogc_validation/ -> src/ -> project root)
_DBPATH = str(Path(__file__).parents[3] / "data" / "autogc.db")


def _generate_notebook(
    result: "WorkspaceResult",
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
            "from autogc_validation.database.enums import aqs_to_name, name_to_aqs\n"
            f'workspace_dir = Path(r"{workspace_dir}")\n'
            f'data_dir = Path(r"{result.data_dir}")\n'
            f'site_id = {site_code}\n'
            f'year  = {year}\n'
            f'month = {month}\n'
            f'database = Path(r"{_DBPATH}")\n'
            f'start_date = "{start_date_str}"\n'
            f'end_date   = "{end_date_str}"\n'
            f'mdvr_path = workspace_dir / "MDVR" / "{site}{yyyymm}_MDVR.xlsx"\n\n'
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
            f"`{Path(workspace_dir).as_posix()}/TEMP`, then run the cell below."
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
            "display(ds.data.head())\n\n"
            "ambient = ds.ambient\n"
            "blank   = ds.blanks\n"
            "cvs     = ds.cvs\n"
            "lcs     = ds.lcs\n"
            "rts     = ds.rts\n"
            "exp     = ds.experimental\n"
            "cal     = ds.calibration\n"
            "mdl     = ds.mdl\n\n"
            "samples = [ambient, blank, cvs, lcs, rts, exp, cal, mdl]\n"
            "sample_amt = {sample.attrs['sample_type'].value: len(sample) for sample in samples}\n\n"
            "qc = 0\n"
            "for s, amt in sample_amt.items():\n"
            '    if s not in ["s", "x"]:\n'
            "        qc += amt\n\n"
            "for sample in samples:\n"
            "    print(f\"{sample.attrs['sample_type'].value}: {len(sample)}\")"
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

        # --- Query MDL and canister periods ---
        nbformat.v4.new_markdown_cell("## 3. Query MDL and canister concentration periods"),
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

        # --- Nulled QC runs ---
        nbformat.v4.new_markdown_cell(
            "## 3a. Nulled QC runs\n\n"
            "List the filename stems of any nulled QC runs to exclude from qualifier "
            "interval computation. Use `ds.blanks['filename']`, `ds.cvs['filename']`, "
            "etc. to look up the filename stem for a given run."
        ),
        nbformat.v4.new_code_cell(
            "nulled_blanks = []\n"
            "nulled_cvs    = []\n"
            "nulled_lcs    = []"
        ),

        # --- Weekly method optimization ---
        nbformat.v4.new_markdown_cell("## 4. Weekly method optimization"),

        nbformat.v4.new_markdown_cell("### Week 1"),
        nbformat.v4.new_markdown_cell("#### Ambient Checks"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.ambient import plot_ambient_comparisons\n\n"
            "ambient_w1 = ds.ambient.loc[weeks[1][0]:weeks[1][1]]\n"
            f"plot_ambient_comparisons(ambient_w1, '{site}', {year}, {month}, label='Week 1')"
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.distribution import plot_lognormal_boxplot\n\n"
            f"plot_lognormal_boxplot(ambient_w1, '{site}', {year}, {month}, label='Week 1', mdls=mdl_periods)"
        ),
        nbformat.v4.new_markdown_cell("#### RT Checks"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.rt import plot_rt\n"
            "from autogc_validation.qc.rt_outliers import detect_rt_outliers\n"
            "from autogc_validation.database.enums import RT_REFERENCE_CODES\n\n"
            "rt_ref_cols = [c for c in RT_REFERENCE_CODES if c in ds.rt.columns]\n"
            "# rt_compound_cols = get_compound_cols(ds.rt)  # uncomment to check all compounds\n\n"
            "rt_w1   = ds.rt.loc[weeks[1][0]:weeks[1][1]]\n"
            "data_w1 = ds.data.loc[weeks[1][0]:weeks[1][1]]\n"
            f"plot_rt(rt_w1, data_w1, '{site}', {year}, {month}, samp_type='s')\n"
            "rt_outliers_w1 = detect_rt_outliers(rt_w1[rt_w1['sample_type'] == 's'], rt_ref_cols)\n"
            "# rt_outliers_w1 = detect_rt_outliers(rt_w1[rt_w1['sample_type'] == 's'], rt_compound_cols)  # all compounds\n"
            'print(f"Week 1 RT outliers: {len(rt_outliers_w1)}")\n'
            "rt_outliers_w1"
        ),
        nbformat.v4.new_markdown_cell("#### Check Mis-IDed Reference Peaks"),
        nbformat.v4.new_code_cell(
            "mask = (ambient_w1[name_to_aqs('n-pentane')] == 0) | (ambient_w1[name_to_aqs('propane')] == 0) | (ambient_w1[name_to_aqs('toluene')] == 0) | (ambient_w1[name_to_aqs('benzene')] == 0)\n"
            "misided = ambient_w1[mask]\n"
            "display(misided)"
        ),
        nbformat.v4.new_markdown_cell("#### Convert txt"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.workspace.files import rename_dattxt_files_to_txt\n"
            'week_folder = workspace_dir / "FINAL" / "week 1"\n'
            'output_folder = week_folder / "MAX upload"\n'
            'files_renamed = rename_dattxt_files_to_txt(week_folder, output_folder)\n'
            'print(f"Renamed {files_renamed[\'written\']} file(s), {files_renamed[\'overwritten\']} overwritten")\n'
        ),
        nbformat.v4.new_markdown_cell("#### Screening and Reprocess Plan"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.screening import (\n"
            "    check_ratios, check_overrange_values, check_daily_max_tnmhc,\n"
            "    check_lognormal_outliers,\n"
            ")\n"
            "from autogc_validation.reports import fill_reprocess_plan\n\n"
            "# Re-run 'Load dataset' cell above if you added new files since last loading.\n"
            "data_w1 = ds.data.loc[weeks[1][0]:weeks[1][1]]\n\n"
            "# check_ratios requires mdl_periods — run section 6 first if needed.\n"
            "try:\n"
            "    ratios_w1 = check_ratios(data_w1, mdl_periods)\n"
            '    print(f"Ratio flags: {len(ratios_w1)}")\n'
            "    if not ratios_w1.empty:\n"
            "        display(ratios_w1)\n"
            "except NameError:\n"
            '    print("Skipping ratio check — run section 6 first to load mdl_periods.")\n\n'
            "upper_cal_point_w1 = None  # ← set to upper calibration point value\n"
            "overrange_w1 = check_overrange_values(data_w1, upper_cal_point_w1)\n"
            'print(f"Overrange values: {len(overrange_w1)}")\n'
            "if not overrange_w1.empty:\n"
            "    display(overrange_w1)\n\n"
            "outliers_w1 = check_lognormal_outliers(data_w1, mdl_periods)\n"
            'print(f"Lognormal outliers: {len(outliers_w1)}")\n'
            "if not outliers_w1.empty:\n"
            "    display(outliers_w1)\n\n"
            "daily_tnmhc_w1 = check_daily_max_tnmhc(data_w1)\n"
            'print("Daily max TNMHC:")\n'
            "display(daily_tnmhc_w1)\n\n"
            "fill_reprocess_plan(\n"
            "    ds.data, mdvr_path, mdvr_path, year, month,\n"
            "    overrange=overrange_w1, daily_tnmhc=daily_tnmhc_w1, outliers=outliers_w1,\n"
            "    start_date=weeks[1][0], end_date=weeks[1][1],\n"
            ")"
        ),

        nbformat.v4.new_markdown_cell("### Week 2"),
        nbformat.v4.new_markdown_cell("#### Ambient Checks"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.ambient import plot_ambient_comparisons\n\n"
            "ambient_w2 = ds.ambient.loc[weeks[2][0]:weeks[2][1]]\n"
            f"plot_ambient_comparisons(ambient_w2, '{site}', {year}, {month}, label='Week 2')"
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.distribution import plot_lognormal_boxplot\n\n"
            f"plot_lognormal_boxplot(ambient_w2, '{site}', {year}, {month}, label='Week 2', mdls=mdl_periods)"
        ),
        nbformat.v4.new_markdown_cell("#### RT Checks"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.rt import plot_rt\n"
            "from autogc_validation.qc.rt_outliers import detect_rt_outliers\n"
            "from autogc_validation.database.enums import RT_REFERENCE_CODES\n\n"
            "rt_ref_cols = [c for c in RT_REFERENCE_CODES if c in ds.rt.columns]\n"
            "# rt_compound_cols = get_compound_cols(ds.rt)  # uncomment to check all compounds\n\n"
            "rt_w2   = ds.rt.loc[weeks[2][0]:weeks[2][1]]\n"
            "data_w2 = ds.data.loc[weeks[2][0]:weeks[2][1]]\n"
            f"plot_rt(rt_w2, data_w2, '{site}', {year}, {month}, samp_type='s')\n"
            "rt_outliers_w2 = detect_rt_outliers(rt_w2[rt_w2['sample_type'] == 's'], rt_ref_cols)\n"
            "# rt_outliers_w2 = detect_rt_outliers(rt_w2[rt_w2['sample_type'] == 's'], rt_compound_cols)  # all compounds\n"
            'print(f"Week 2 RT outliers: {len(rt_outliers_w2)}")\n'
            "rt_outliers_w2"
        ),
        nbformat.v4.new_markdown_cell("#### Check Mis-IDed Reference Peaks"),
        nbformat.v4.new_code_cell(
            "mask = (ambient_w2[name_to_aqs('n-pentane')] == 0) | (ambient_w2[name_to_aqs('propane')] == 0) | (ambient_w2[name_to_aqs('toluene')] == 0) | (ambient_w2[name_to_aqs('benzene')] == 0)\n"
            "misided = ambient_w2[mask]\n"
            "display(misided)"
        ),
        nbformat.v4.new_markdown_cell("#### Convert txt"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.workspace.files import rename_dattxt_files_to_txt\n"
            'week_folder = workspace_dir / "FINAL" / "week 2"\n'
            'output_folder = week_folder / "MAX upload"\n'
            'files_renamed = rename_dattxt_files_to_txt(week_folder, output_folder)\n'
            'print(f"Renamed {files_renamed[\'written\']} file(s), {files_renamed[\'overwritten\']} overwritten")\n'
        ),
        nbformat.v4.new_markdown_cell("#### Screening and Reprocess Plan"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.screening import (\n"
            "    check_ratios, check_overrange_values, check_daily_max_tnmhc,\n"
            "    check_lognormal_outliers,\n"
            ")\n"
            "from autogc_validation.reports import fill_reprocess_plan\n\n"
            "# Re-run 'Load dataset' cell above if you added new files since last loading.\n"
            "data_w2 = ds.data.loc[weeks[2][0]:weeks[2][1]]\n\n"
            "# check_ratios requires mdl_periods — run section 6 first if needed.\n"
            "try:\n"
            "    ratios_w2 = check_ratios(data_w2, mdl_periods)\n"
            '    print(f"Ratio flags: {len(ratios_w2)}")\n'
            "    if not ratios_w2.empty:\n"
            "        display(ratios_w2)\n"
            "except NameError:\n"
            '    print("Skipping ratio check — run section 6 first to load mdl_periods.")\n\n'
            "upper_cal_point_w2 = None  # ← set to upper calibration point value\n"
            "overrange_w2 = check_overrange_values(data_w2, upper_cal_point_w2)\n"
            'print(f"Overrange values: {len(overrange_w2)}")\n'
            "if not overrange_w2.empty:\n"
            "    display(overrange_w2)\n\n"
            "outliers_w2 = check_lognormal_outliers(data_w2, mdl_periods)\n"
            'print(f"Lognormal outliers: {len(outliers_w2)}")\n'
            "if not outliers_w2.empty:\n"
            "    display(outliers_w2)\n\n"
            "daily_tnmhc_w2 = check_daily_max_tnmhc(data_w2)\n"
            'print("Daily max TNMHC:")\n'
            "display(daily_tnmhc_w2)\n\n"
            "fill_reprocess_plan(\n"
            "    ds.data, mdvr_path, mdvr_path, year, month,\n"
            "    overrange=overrange_w2, daily_tnmhc=daily_tnmhc_w2, outliers=outliers_w2,\n"
            "    start_date=weeks[2][0], end_date=weeks[2][1],\n"
            ")"
        ),

        nbformat.v4.new_markdown_cell("### Week 3"),
        nbformat.v4.new_markdown_cell("#### Ambient Checks"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.ambient import plot_ambient_comparisons\n\n"
            "ambient_w3 = ds.ambient.loc[weeks[3][0]:weeks[3][1]]\n"
            f"plot_ambient_comparisons(ambient_w3, '{site}', {year}, {month}, label='Week 3')"
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.distribution import plot_lognormal_boxplot\n\n"
            f"plot_lognormal_boxplot(ambient_w3, '{site}', {year}, {month}, label='Week 3', mdls=mdl_periods)"
        ),
        nbformat.v4.new_markdown_cell("#### RT Checks"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.rt import plot_rt\n"
            "from autogc_validation.qc.rt_outliers import detect_rt_outliers\n"
            "from autogc_validation.database.enums import RT_REFERENCE_CODES\n\n"
            "rt_ref_cols = [c for c in RT_REFERENCE_CODES if c in ds.rt.columns]\n"
            "# rt_compound_cols = get_compound_cols(ds.rt)  # uncomment to check all compounds\n\n"
            "rt_w3   = ds.rt.loc[weeks[3][0]:weeks[3][1]]\n"
            "data_w3 = ds.data.loc[weeks[3][0]:weeks[3][1]]\n"
            f"plot_rt(rt_w3, data_w3, '{site}', {year}, {month}, samp_type='s')\n"
            "rt_outliers_w3 = detect_rt_outliers(rt_w3[rt_w3['sample_type'] == 's'], rt_ref_cols)\n"
            "# rt_outliers_w3 = detect_rt_outliers(rt_w3[rt_w3['sample_type'] == 's'], rt_compound_cols)  # all compounds\n"
            'print(f"Week 3 RT outliers: {len(rt_outliers_w3)}")\n'
            "rt_outliers_w3"
        ),
        nbformat.v4.new_markdown_cell("#### Check Mis-IDed Reference Peaks"),
        nbformat.v4.new_code_cell(
            "mask = (ambient_w3[name_to_aqs('n-pentane')] == 0) | (ambient_w3[name_to_aqs('propane')] == 0) | (ambient_w3[name_to_aqs('toluene')] == 0) | (ambient_w3[name_to_aqs('benzene')] == 0)\n"
            "misided = ambient_w3[mask]\n"
            "display(misided)"
        ),
        nbformat.v4.new_markdown_cell("#### Convert txt"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.workspace.files import rename_dattxt_files_to_txt\n"
            'week_folder = workspace_dir / "FINAL" / "week 3"\n'
            'output_folder = week_folder / "MAX upload"\n'
            'files_renamed = rename_dattxt_files_to_txt(week_folder, output_folder)\n'
            'print(f"Renamed {files_renamed[\'written\']} file(s), {files_renamed[\'overwritten\']} overwritten")\n'
        ),
        nbformat.v4.new_markdown_cell("#### Screening and Reprocess Plan"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.screening import (\n"
            "    check_ratios, check_overrange_values, check_daily_max_tnmhc,\n"
            "    check_lognormal_outliers,\n"
            ")\n"
            "from autogc_validation.reports import fill_reprocess_plan\n\n"
            "# Re-run 'Load dataset' cell above if you added new files since last loading.\n"
            "data_w3 = ds.data.loc[weeks[3][0]:weeks[3][1]]\n\n"
            "# check_ratios requires mdl_periods — run section 6 first if needed.\n"
            "try:\n"
            "    ratios_w3 = check_ratios(data_w3, mdl_periods)\n"
            '    print(f"Ratio flags: {len(ratios_w3)}")\n'
            "    if not ratios_w3.empty:\n"
            "        display(ratios_w3)\n"
            "except NameError:\n"
            '    print("Skipping ratio check — run section 6 first to load mdl_periods.")\n\n'
            "upper_cal_point_w3 = None  # ← set to upper calibration point value\n"
            "overrange_w3 = check_overrange_values(data_w3, upper_cal_point_w3)\n"
            'print(f"Overrange values: {len(overrange_w3)}")\n'
            "if not overrange_w3.empty:\n"
            "    display(overrange_w3)\n\n"
            "outliers_w3 = check_lognormal_outliers(data_w3, mdl_periods)\n"
            'print(f"Lognormal outliers: {len(outliers_w3)}")\n'
            "if not outliers_w3.empty:\n"
            "    display(outliers_w3)\n\n"
            "daily_tnmhc_w3 = check_daily_max_tnmhc(data_w3)\n"
            'print("Daily max TNMHC:")\n'
            "display(daily_tnmhc_w3)\n\n"
            "fill_reprocess_plan(\n"
            "    ds.data, mdvr_path, mdvr_path, year, month,\n"
            "    overrange=overrange_w3, daily_tnmhc=daily_tnmhc_w3, outliers=outliers_w3,\n"
            "    start_date=weeks[3][0], end_date=weeks[3][1],\n"
            ")"
        ),

        nbformat.v4.new_markdown_cell("### Week 4"),
        nbformat.v4.new_markdown_cell("#### Ambient Checks"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.ambient import plot_ambient_comparisons\n\n"
            "ambient_w4 = ds.ambient.loc[weeks[4][0]:weeks[4][1]]\n"
            f"plot_ambient_comparisons(ambient_w4, '{site}', {year}, {month}, label='Week 4')"
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.distribution import plot_lognormal_boxplot\n\n"
            f"plot_lognormal_boxplot(ambient_w4, '{site}', {year}, {month}, label='Week 4', mdls=mdl_periods)"
        ),
        nbformat.v4.new_markdown_cell("#### RT Checks"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.rt import plot_rt\n"
            "from autogc_validation.qc.rt_outliers import detect_rt_outliers\n"
            "from autogc_validation.database.enums import RT_REFERENCE_CODES\n\n"
            "rt_ref_cols = [c for c in RT_REFERENCE_CODES if c in ds.rt.columns]\n"
            "# rt_compound_cols = get_compound_cols(ds.rt)  # uncomment to check all compounds\n\n"
            "rt_w4   = ds.rt.loc[weeks[4][0]:weeks[4][1]]\n"
            "data_w4 = ds.data.loc[weeks[4][0]:weeks[4][1]]\n"
            f"plot_rt(rt_w4, data_w4, '{site}', {year}, {month}, samp_type='s')\n"
            "rt_outliers_w4 = detect_rt_outliers(rt_w4[rt_w4['sample_type'] == 's'], rt_ref_cols)\n"
            "# rt_outliers_w4 = detect_rt_outliers(rt_w4[rt_w4['sample_type'] == 's'], rt_compound_cols)  # all compounds\n"
            'print(f"Week 4 RT outliers: {len(rt_outliers_w4)}")\n'
            "rt_outliers_w4"
        ),
        nbformat.v4.new_markdown_cell("#### Check Mis-IDed Reference Peaks"),
        nbformat.v4.new_code_cell(
            "mask = (ambient_w4[name_to_aqs('n-pentane')] == 0) | (ambient_w4[name_to_aqs('propane')] == 0) | (ambient_w4[name_to_aqs('toluene')] == 0) | (ambient_w4[name_to_aqs('benzene')] == 0)\n"
            "misided = ambient_w4[mask]\n"
            "display(misided)"
        ),
        nbformat.v4.new_markdown_cell("#### Convert txt"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.workspace.files import rename_dattxt_files_to_txt\n"
            'week_folder = workspace_dir / "FINAL" / "week 4"\n'
            'output_folder = week_folder / "MAX upload"\n'
            'files_renamed = rename_dattxt_files_to_txt(week_folder, output_folder)\n'
            'print(f"Renamed {files_renamed[\'written\']} file(s), {files_renamed[\'overwritten\']} overwritten")\n'
        ),
        nbformat.v4.new_markdown_cell("#### Screening and Reprocess Plan"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.screening import (\n"
            "    check_ratios, check_overrange_values, check_daily_max_tnmhc,\n"
            "    check_lognormal_outliers,\n"
            ")\n"
            "from autogc_validation.reports import fill_reprocess_plan\n\n"
            "# Re-run 'Load dataset' cell above if you added new files since last loading.\n"
            "data_w4 = ds.data.loc[weeks[4][0]:weeks[4][1]]\n\n"
            "# check_ratios requires mdl_periods — run section 6 first if needed.\n"
            "try:\n"
            "    ratios_w4 = check_ratios(data_w4, mdl_periods)\n"
            '    print(f"Ratio flags: {len(ratios_w4)}")\n'
            "    if not ratios_w4.empty:\n"
            "        display(ratios_w4)\n"
            "except NameError:\n"
            '    print("Skipping ratio check — run section 6 first to load mdl_periods.")\n\n'
            "upper_cal_point_w4 = None  # ← set to upper calibration point value\n"
            "overrange_w4 = check_overrange_values(data_w4, upper_cal_point_w4)\n"
            'print(f"Overrange values: {len(overrange_w4)}")\n'
            "if not overrange_w4.empty:\n"
            "    display(overrange_w4)\n\n"
            "outliers_w4 = check_lognormal_outliers(data_w4, mdl_periods)\n"
            'print(f"Lognormal outliers: {len(outliers_w4)}")\n'
            "if not outliers_w4.empty:\n"
            "    display(outliers_w4)\n\n"
            "daily_tnmhc_w4 = check_daily_max_tnmhc(data_w4)\n"
            'print("Daily max TNMHC:")\n'
            "display(daily_tnmhc_w4)\n\n"
            "fill_reprocess_plan(\n"
            "    ds.data, mdvr_path, mdvr_path, year, month,\n"
            "    overrange=overrange_w4, daily_tnmhc=daily_tnmhc_w4, outliers=outliers_w4,\n"
            "    start_date=weeks[4][0], end_date=weeks[4][1],\n"
            ")"
        ),

        # --- Monthly ambient compound plots ---
        nbformat.v4.new_markdown_cell("## 5. Monthly ambient compound plots"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.ambient import plot_ambient_comparisons\n\n"
            f"plot_ambient_comparisons(ds.ambient, '{site}', {year}, {month})"
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.distribution import plot_lognormal_boxplot\n\n"
            f"plot_lognormal_boxplot(ds.ambient, '{site}', {year}, {month}, mdls=mdl_periods)"
        ),

        # --- Monthly retention time validation ---
        nbformat.v4.new_markdown_cell("## 6. Monthly retention time validation"),
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
            "precision_failures, cvs_precision_pairs = check_cvs_precision(ds.cvs, cvs_periods)\n"
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
            "# Adjust these start rows to match the merged-cell ranges in the MDVR template.\n"
            "blank_start_row     = 73\n"
            "cvs_start_row       = 22\n"
            "lcs_start_row       = 15\n"
            "rts_start_row       = 7\n"
            "precision_start_row = 62\n\n"
            "blank_table     = build_blank_qc_table(mdl_failures, threshold_failures, nulled_filenames=nulled_blanks or None)\n"
            "cvs_table       = build_recovery_qc_table(cvs_failures, 'CVS', nulled_filenames=nulled_cvs or None)\n"
            "lcs_table       = build_recovery_qc_table(lcs_failures, 'LCS', nulled_filenames=nulled_lcs or None)\n"
            "rts_table       = build_recovery_qc_table(rts_failures, 'RTS')\n"
            "precision_table = build_precision_qc_table(precision_failures, nulled_filenames=nulled_cvs or None)\n\n"
            "write_qc_table_to_excel(blank_table,     mdvr_path, mdvr_path, 'Blanks',         blank_start_row)\n"
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
            "    check_ratios, check_overrange_values, check_daily_max_tnmhc,\n"
            "    check_lognormal_outliers,\n"
            ")\n\n"
            "# Compound ratio screening (EPA TAD Table 10-1)\n"
            "# Note: check_ratios uses the first MDL period for threshold comparisons.\n"
            "# If MDLs changed mid-month, split the ambient DataFrame by period manually.\n"
            "ratios = check_ratios(ds.data, mdl_periods)\n"
            'print(f"Ratio flags: {len(ratios)}")\n'
            "if not ratios.empty:\n"
            "    display(ratios)\n\n"
            "# Overrange detection\n"
            "upper_cal_point = None  # ← set to upper calibration point value\n"
            "overrange = check_overrange_values(ds.data, upper_cal_point)\n"
            'print(f"\\nOverrange values: {len(overrange)}")\n'
            "if not overrange.empty:\n"
            "    display(overrange)\n\n"
            "# Log-normal outlier detection\n"
            "outliers = check_lognormal_outliers(ds.data, mdl_periods)\n"
            'print(f"\\nLognormal outliers: {len(outliers)}")\n'
            "if not outliers.empty:\n"
            "    display(outliers)\n\n"
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
            "    overrange=overrange, daily_tnmhc=daily_tnmhc, outliers=outliers,\n"
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
            "prior_blank      = None\n"
            "next_blank       = None\n"
            "prior_cvs        = None\n"
            "next_cvs         = None\n"
            "prior_lcs        = None\n"
            "next_lcs         = None\n"
            "prior_precision  = None\n"
            "next_precision   = None\n\n"
            "blank_quals = build_blank_qualifier_lines(\n"
            "    ds.data, mdl_failures, threshold_failures,\n"
            "    prior_blank=prior_blank, next_blank=next_blank,\n"
            "    nulled_filenames=nulled_blanks or None,\n"
            ")\n"
            'print(f"Blank qualifier lines: {len(blank_quals)}")\n\n'
            "cvs_quals = build_qc_qualifier_lines(\n"
            "    ds.data, cvs_failures, 'c', prior_qc=prior_cvs, next_qc=next_cvs,\n"
            "    nulled_filenames=nulled_cvs or None,\n"
            ")\n"
            "lcs_quals = build_qc_qualifier_lines(\n"
            "    ds.data, lcs_failures, 'e', prior_qc=prior_lcs, next_qc=next_lcs,\n"
            "    nulled_filenames=nulled_lcs or None,\n"
            ")\n"
            'print(f"QC qualifier lines — CVS: {len(cvs_quals)}, LCS: {len(lcs_quals)}")\n\n'
            "precision_quals = build_precision_qualifier_lines(\n"
            "    ds.data, precision_failures, cvs_precision_pairs,\n"
            "    prior_qc=prior_precision, next_qc=next_precision,\n"
            ")\n"
            'print(f"Precision qualifier lines: {len(precision_quals)}")'
        ),
        nbformat.v4.new_markdown_cell("### Static monthly qualifiers"),
        nbformat.v4.new_code_cell(
            "# Static qualifiers applied to every month regardless of QC results.\n"
            "_month_start = pd.Timestamp(start_date)\n"
            "_month_end   = pd.Timestamp(end_date)\n\n"
            "def _static_row(name: str, reason: str, justification: str) -> dict:\n"
            "    return {\n"
            "        'Parameter(s)': aqs_to_name(name_to_aqs(name)),\n"
            "        'COMPOUND(S) or WHOLE HOUR(S) - REASON': reason,\n"
            "        'CODE': 'LJ',\n"
            "        'startdate': _month_start.strftime('%m/%d/%Y'),\n"
            "        'starthour': _month_start.strftime('%H:00'),\n"
            "        '-': '-',\n"
            "        'enddate': _month_end.strftime('%m/%d/%Y'),\n"
            "        'endhour': _month_end.strftime('%H:00'),\n"
            "        'Justification': justification,\n"
            "    }\n\n"
            "static_quals = pd.DataFrame([\n"
            "    _static_row('alpha-pinene',     'No QC gas available',           'No QC gas available'),\n"
            "    _static_row('beta-pinene',      'No QC gas available',           'No QC gas available'),\n"
            "    _static_row('isoprene',         'Inaccuracy in measurements',    'Due to uncertainty in measurements at the end of the column'),\n"
            "    _static_row('1-hexene',         'Inaccuracy in measurements',    'Due to uncertainty in measurements at the end of the column'),\n"
            "    _static_row('n-dodecane',       'Inaccuracy in measurements',    'Due to uncertainty in measurements at the end of the column'),\n"
            "    _static_row('m-diethylbenzene', 'Peak misidentification issues', 'Due to potential issues in peak identification at low levels'),\n"
            "    _static_row('p-diethylbenzene', 'Peak misidentification issues', 'Due to potential issues in peak identification at low levels'),\n"
            "])\n"
            "static_quals"
        ),
        nbformat.v4.new_markdown_cell("### Export qualifiers to Excel"),
        nbformat.v4.new_code_cell(
            "all_quals = pd.concat(\n"
            "    [blank_quals, cvs_quals, lcs_quals, precision_quals, temp_null_lines, static_quals],\n"
            "    ignore_index=True,\n"
            ")\n"
            'print(f"Total qualifier lines: {len(all_quals)}")\n'
            "all_quals"
        ),
        nbformat.v4.new_code_cell(
            "write_mdvr_to_excel(all_quals, mdvr_path, mdvr_path)\n"
            f'print(f"Qualifiers written to {{mdvr_path}}")'
        ),

        # --- AQS verification ---
        nbformat.v4.new_markdown_cell("## 14. AQS upload verification"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports.aqs import compare_aqs_to_dataset\n\n"
            f"aqs_file = r\"\"  # ← set path to AQS RD upload file\n\n"
            "differences = compare_aqs_to_dataset(aqs_file, ds.ambient.copy())\n"
            'print(f"Rows with |dataset - AQS| > 0.001: {len(differences)}")\n'
            "differences"
        ),

        # --- Monthly case narrative ---
        nbformat.v4.new_markdown_cell(
            "## 15. Monthly case narrative\n\n"
            "Run this cell once you have finished reviewing the full month and "
            "are satisfied with the data qualification.  "
            "The generated `.qmd` file renders to both a self-contained HTML report "
            "and a Word document. Word output requires `kaleido` (`pip install kaleido`) "
            "and must be rendered from a **non-elevated** shell (not Run as Administrator).\n\n"
            "```\n"
            f"quarto render VALIDATION\\ DOCS/{site}{yyyymm}_case_narrative.qmd\n"
            "```"
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports.monthly_report import generate_monthly_report\n\n"
            "# Set to True when ready to generate the case narrative QMD.\n"
            "_GENERATE = False\n\n"
            "if _GENERATE:\n"
            f"    qmd_path = generate_monthly_report(result, '{site}', year, month)\n"
            f'    print(f"Case narrative written to {{qmd_path}}")\n'
            "else:\n"
            '    print("Skipped. Set _GENERATE = True to run.")'
        ),
        nbformat.v4.new_markdown_cell(
            "Review and edit the `.qmd` file above before rendering. "
            "When satisfied, run the cell below to render to HTML and Word."
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports.monthly_report import render_monthly_report\n\n"
            "# Set to True when ready to render. Requires _GENERATE to have been run first.\n"
            "_RENDER = False\n\n"
            "if _RENDER:\n"
            f"    docx_path = render_monthly_report(qmd_path, '{site}', year, month)\n"
            f'    print(f"Word document: {{docx_path}}")\n'
            "else:\n"
            '    print("Skipped. Set _RENDER = True to run.")'
        ),

        # --- Transfer to network ---
        nbformat.v4.new_markdown_cell(
            "## 16. Transfer to network\n\n"
            "Copies AQS, FINAL, Original, and MDVR "
            "to the network drive. The destination folder must not already exist — "
            "delete it manually before re-running if you need to overwrite a previous transfer."
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.workspace.folders import transfer_to_network\n\n"
            "network_root = Path(r\"\")  # ← set network drive path\n\n"
            "dest = transfer_to_network(workspace_dir, network_root)\n"
            'print(f"Transferred to {dest}")'
        ),
    ]

    notebook_path = result.base_dir / f"{site}{yyyymm}.ipynb"
    nbformat.write(nb, str(notebook_path))
    logger.info("Notebook created: %s", notebook_path)
    return notebook_path
