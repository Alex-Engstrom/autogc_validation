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
        nbformat.v4.new_markdown_cell("## Logging"),
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
            f'mdvr_path = workspace_dir / "MDVR" / "TAS-FORM-003_AutoGC_Monthly_Data_Validation_{site}{yyyymm}.xlsx"\n\n'
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

        # --- Query MDL and canister periods ---
        nbformat.v4.new_markdown_cell("## 2. Query MDL and canister concentration periods"),
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

        # --- Populate MDVR ---
        nbformat.v4.new_markdown_cell("## 3. Populate MDVR"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports import populate_mdvr\n\n"
            "populate_mdvr(mdvr_path, month, year, db_path=database, site_id=site_id)"
        ),

        # --- Load dataset ---
        nbformat.v4.new_markdown_cell("## 4. Load dataset"),
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
            "print('Number of QC samples:', qc)\n"
            "for sample in samples:\n"
            "    print(f\"{sample.attrs['sample_type'].value}: {len(sample)}\")\n\n"
            "# --- Filename hour alignment check ---\n"
            "hour_mismatches = ds.check_filename_hour_alignment()\n"
            "if hour_mismatches.empty:\n"
            '    print("Filename hour alignment: OK (no mismatches)")\n'
            "else:\n"
            '    print(f"WARNING: {len(hour_mismatches)} filename hour mismatches:")\n'
            "    display(hour_mismatches)\n\n"
            "# --- Sample type consistency check ---\n"
            "type_mismatches = ds.check_long_and_letter_sample_types()\n"
            "if type_mismatches.empty:\n"
            '    print("Sample type consistency: OK (no mismatches)")\n'
            "else:\n"
            '    print(f"WARNING: {len(type_mismatches)} sample type mismatches:")\n'
            "    display(type_mismatches)"
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

        # --- Nulled QC runs ---
        nbformat.v4.new_markdown_cell(
            "## 4a. Nulled QC runs\n\n"
            "List the filename stems of any nulled QC runs to exclude from qualifier "
            "interval computation. Use `ds.blanks['filename']`, `ds.cvs['filename']`, "
            "etc. to look up the filename stem for a given run."
        ),
        nbformat.v4.new_code_cell(
            "nulled_blanks = []\n"
            "nulled_cvs    = []\n"
            "nulled_lcs    = []\n"
            "nulled_rts    = []\n"
        ),

        # --- Weekly method optimization ---
        nbformat.v4.new_markdown_cell("## 5. Weekly method optimization"),

        nbformat.v4.new_markdown_cell("### Week 1"),
        nbformat.v4.new_markdown_cell("#### Ambient Checks"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.ambient import (\n"
            "    plot_ambient_comparisons, plot_voc_category_sums, plot_vs_totals,\n"
            ")\n\n"
            "ambient_w1 = ds.ambient.loc[weeks[1][0]:weeks[1][1]]"
        ),
        nbformat.v4.new_code_cell(
            f"plot_ambient_comparisons(ambient_w1, '{site}', {year}, {month}, label='Week 1')"
        ),
        nbformat.v4.new_code_cell(
            f"plot_voc_category_sums(ambient_w1, '{site}', {year}, {month}, label='Week 1')"
        ),
        nbformat.v4.new_code_cell(
            f"plot_vs_totals(ambient_w1, '{site}', {year}, {month})"
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
            f"rt_figs_w1 = plot_rt(rt_w1, data_w1, '{site}', {year}, {month}, samp_type='s')\n"
            "for _fig in rt_figs_w1:\n"
            "    display(_fig)\n"
            "rt_outliers_w1 = detect_rt_outliers(rt_w1[rt_w1['sample_type'] == 's'], rt_ref_cols, concentrations=data_w1, mdl_periods=mdl_periods)\n"
            "# rt_outliers_w1 = detect_rt_outliers(rt_w1[rt_w1['sample_type'] == 's'], rt_compound_cols, concentrations=data_w1, mdl_periods=mdl_periods)  # all compounds\n"
            'print(f"Week 1 RT outliers: {len(rt_outliers_w1)}")\n'
            "rt_outliers_w1"
        ),
        nbformat.v4.new_markdown_cell("#### Check Mis-IDed Reference Peaks"),
        nbformat.v4.new_code_cell(
            "reference = ['filename', name_to_aqs('n-pentane'), name_to_aqs('propane'), name_to_aqs('toluene'), name_to_aqs('benzene')]\n"
            "mask = (ambient_w1[name_to_aqs('n-pentane')] < 0.005) | (ambient_w1[name_to_aqs('propane')] < 0.005) | (ambient_w1[name_to_aqs('toluene')] < 0.005) | (ambient_w1[name_to_aqs('benzene')] < 0.005)\n"
            "misided = ambient_w1[reference][mask]\n"
            "misided.columns = [aqs_to_name(col) if col != 'filename' else col for col in misided.columns]\n"
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
            "    check_lognormal_outliers, compare_tnmtc_tnmhc,\n"
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
            "upper_cal_point_plot_w1 = None  # ← set to upper calibration point value (PLOT column)\n"
            "upper_cal_point_bp_w1 = None  # ← set to upper calibration point value (BP column)\n"
            "k = 3.5\n"
            "overrange_w1 = check_overrange_values(data_w1, upper_cal_point_plot_w1, upper_cal_point_bp_w1)\n"
            'print(f"Overrange values: {len(overrange_w1)}")\n'
            "if not overrange_w1.empty:\n"
            "    display(overrange_w1)\n\n"
            "outliers_w1 = check_lognormal_outliers(data_w1, mdl_periods, k=k)\n"
            'print(f"Lognormal outliers: {len(outliers_w1)}")\n'
            "if not outliers_w1.empty:\n"
            "    display(outliers_w1)\n\n"
            "totals_w1 = ds.totals.loc[weeks[1][0]:weeks[1][1]]\n"
            "daily_tnmhc_front_w1 = check_daily_max_tnmhc(totals_w1, \"tnmhc_front\")\n"
            "daily_tnmhc_back_w1  = check_daily_max_tnmhc(totals_w1, \"tnmhc_back\")\n"
            'print("Daily max TNMHC (Front):")\n'
            "display(daily_tnmhc_front_w1)\n"
            'print("Daily max TNMHC (Back):")\n'
            "display(daily_tnmhc_back_w1)\n\n"
            "tchc_diff_w1, tchc_ratio_w1 = compare_tnmtc_tnmhc(data_w1)\n"
            'print("TNMHC - TNMTC:")\n'
            "display(tchc_diff_w1)\n"
            'print("TNMHC / TNMTC:")\n'
            "display(tchc_ratio_w1)\n\n"
            "fill_reprocess_plan(\n"
            "    ds.data, mdvr_path, mdvr_path, year, month,\n"
            "    overrange=overrange_w1, daily_tnmhc_front=daily_tnmhc_front_w1, daily_tnmhc_back=daily_tnmhc_back_w1,\n"
            "    start_date=weeks[1][0], end_date=weeks[1][1],\n"
            ")"
        ),

        nbformat.v4.new_markdown_cell("### Week 2"),
        nbformat.v4.new_markdown_cell("#### Ambient Checks"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.ambient import (\n"
            "    plot_ambient_comparisons, plot_voc_category_sums, plot_vs_totals,\n"
            ")\n\n"
            "ambient_w2 = ds.ambient.loc[weeks[2][0]:weeks[2][1]]"
        ),
        nbformat.v4.new_code_cell(
            f"plot_ambient_comparisons(ambient_w2, '{site}', {year}, {month}, label='Week 2')"
        ),
        nbformat.v4.new_code_cell(
            f"plot_voc_category_sums(ambient_w2, '{site}', {year}, {month}, label='Week 2')"
        ),
        nbformat.v4.new_code_cell(
            f"plot_vs_totals(ambient_w2, '{site}', {year}, {month})"
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
            f"rt_figs_w2 = plot_rt(rt_w2, data_w2, '{site}', {year}, {month}, samp_type='s')\n"
            "for _fig in rt_figs_w2:\n"
            "    display(_fig)\n"
            "rt_outliers_w2 = detect_rt_outliers(rt_w2[rt_w2['sample_type'] == 's'], rt_ref_cols, concentrations=data_w2, mdl_periods=mdl_periods)\n"
            "# rt_outliers_w2 = detect_rt_outliers(rt_w2[rt_w2['sample_type'] == 's'], rt_compound_cols, concentrations=data_w2, mdl_periods=mdl_periods)  # all compounds\n"
            'print(f"Week 2 RT outliers: {len(rt_outliers_w2)}")\n'
            "rt_outliers_w2"
        ),
        nbformat.v4.new_markdown_cell("#### Check Mis-IDed Reference Peaks"),
        nbformat.v4.new_code_cell(
            "reference = ['filename', name_to_aqs('n-pentane'), name_to_aqs('propane'), name_to_aqs('toluene'), name_to_aqs('benzene')]\n"
            "mask = (ambient_w2[name_to_aqs('n-pentane')] < 0.005) | (ambient_w2[name_to_aqs('propane')] < 0.005) | (ambient_w2[name_to_aqs('toluene')] < 0.005) | (ambient_w2[name_to_aqs('benzene')] < 0.005)\n"
            "misided = ambient_w2[reference][mask]\n"
            "misided.columns = [aqs_to_name(col) if col != 'filename' else col for col in misided.columns]\n"
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
            "    check_lognormal_outliers, compare_tnmtc_tnmhc,\n"
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
            "upper_cal_point_plot_w2 = None  # ← set to upper calibration point value (PLOT column)\n"
            "upper_cal_point_bp_w2 = None  # ← set to upper calibration point value (BP column)\n"
            "k = 3.5\n"
            "overrange_w2 = check_overrange_values(data_w2, upper_cal_point_plot_w2, upper_cal_point_bp_w2)\n"
            'print(f"Overrange values: {len(overrange_w2)}")\n'
            "if not overrange_w2.empty:\n"
            "    display(overrange_w2)\n\n"
            "outliers_w2 = check_lognormal_outliers(data_w2, mdl_periods, k=k)\n"
            'print(f"Lognormal outliers: {len(outliers_w2)}")\n'
            "if not outliers_w2.empty:\n"
            "    display(outliers_w2)\n\n"
            "totals_w2 = ds.totals.loc[weeks[2][0]:weeks[2][1]]\n"
            "daily_tnmhc_front_w2 = check_daily_max_tnmhc(totals_w2, \"tnmhc_front\")\n"
            "daily_tnmhc_back_w2  = check_daily_max_tnmhc(totals_w2, \"tnmhc_back\")\n"
            'print("Daily max TNMHC (Front):")\n'
            "display(daily_tnmhc_front_w2)\n"
            'print("Daily max TNMHC (Back):")\n'
            "display(daily_tnmhc_back_w2)\n\n"
            "tchc_diff_w2, tchc_ratio_w2 = compare_tnmtc_tnmhc(data_w2)\n"
            'print("TNMHC - TNMTC:")\n'
            "display(tchc_diff_w2)\n"
            'print("TNMHC / TNMTC:")\n'
            "display(tchc_ratio_w2)\n\n"
            "fill_reprocess_plan(\n"
            "    ds.data, mdvr_path, mdvr_path, year, month,\n"
            "    overrange=overrange_w2, daily_tnmhc_front=daily_tnmhc_front_w2, daily_tnmhc_back=daily_tnmhc_back_w2,\n"
            "    start_date=weeks[2][0], end_date=weeks[2][1],\n"
            ")"
        ),

        nbformat.v4.new_markdown_cell("### Week 3"),
        nbformat.v4.new_markdown_cell("#### Ambient Checks"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.ambient import (\n"
            "    plot_ambient_comparisons, plot_voc_category_sums, plot_vs_totals,\n"
            ")\n\n"
            "ambient_w3 = ds.ambient.loc[weeks[3][0]:weeks[3][1]]"
        ),
        nbformat.v4.new_code_cell(
            f"plot_ambient_comparisons(ambient_w3, '{site}', {year}, {month}, label='Week 3')"
        ),
        nbformat.v4.new_code_cell(
            f"plot_voc_category_sums(ambient_w3, '{site}', {year}, {month}, label='Week 3')"
        ),
        nbformat.v4.new_code_cell(
            f"plot_vs_totals(ambient_w3, '{site}', {year}, {month})"
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
            f"rt_figs_w3 = plot_rt(rt_w3, data_w3, '{site}', {year}, {month}, samp_type='s')\n"
            "for _fig in rt_figs_w3:\n"
            "    display(_fig)\n"
            "rt_outliers_w3 = detect_rt_outliers(rt_w3[rt_w3['sample_type'] == 's'], rt_ref_cols, concentrations=data_w3, mdl_periods=mdl_periods)\n"
            "# rt_outliers_w3 = detect_rt_outliers(rt_w3[rt_w3['sample_type'] == 's'], rt_compound_cols, concentrations=data_w3, mdl_periods=mdl_periods)  # all compounds\n"
            'print(f"Week 3 RT outliers: {len(rt_outliers_w3)}")\n'
            "rt_outliers_w3"
        ),
        nbformat.v4.new_markdown_cell("#### Check Mis-IDed Reference Peaks"),
        nbformat.v4.new_code_cell(
            "reference = ['filename', name_to_aqs('n-pentane'), name_to_aqs('propane'), name_to_aqs('toluene'), name_to_aqs('benzene')]\n"
            "mask = (ambient_w3[name_to_aqs('n-pentane')] < 0.005) | (ambient_w3[name_to_aqs('propane')] < 0.005) | (ambient_w3[name_to_aqs('toluene')] < 0.005) | (ambient_w3[name_to_aqs('benzene')] < 0.005)\n"
            "misided = ambient_w3[reference][mask]\n"
            "misided.columns = [aqs_to_name(col) if col != 'filename' else col for col in misided.columns]\n"
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
            "    check_lognormal_outliers, compare_tnmtc_tnmhc\n"
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
            "upper_cal_point_plot_w3 = None  # ← set to upper calibration point value (PLOT column)\n"
            "upper_cal_point_bp_w3 = None  # ← set to upper calibration point value (BP column)\n"
            "k = 3.5\n"
            "overrange_w3 = check_overrange_values(data_w3, upper_cal_point_plot_w3, upper_cal_point_bp_w3)\n"
            'print(f"Overrange values: {len(overrange_w3)}")\n'
            "if not overrange_w3.empty:\n"
            "    display(overrange_w3)\n\n"
            "outliers_w3 = check_lognormal_outliers(data_w3, mdl_periods, k=k)\n"
            'print(f"Lognormal outliers: {len(outliers_w3)}")\n'
            "if not outliers_w3.empty:\n"
            "    display(outliers_w3)\n\n"
            "totals_w3 = ds.totals.loc[weeks[3][0]:weeks[3][1]]\n"
            "daily_tnmhc_front_w3 = check_daily_max_tnmhc(totals_w3, \"tnmhc_front\")\n"
            "daily_tnmhc_back_w3  = check_daily_max_tnmhc(totals_w3, \"tnmhc_back\")\n"
            'print("Daily max TNMHC (Front):")\n'
            "display(daily_tnmhc_front_w3)\n"
            'print("Daily max TNMHC (Back):")\n'
            "display(daily_tnmhc_back_w3)\n\n"
            "tchc_diff_w3, tchc_ratio_w3 = compare_tnmtc_tnmhc(data_w3)\n"
            'print("TNMHC - TNMTC:")\n'
            "display(tchc_diff_w3)\n"
            'print("TNMHC / TNMTC:")\n'
            "display(tchc_ratio_w3)\n\n"
            "fill_reprocess_plan(\n"
            "    ds.data, mdvr_path, mdvr_path, year, month,\n"
            "    overrange=overrange_w3, daily_tnmhc_front=daily_tnmhc_front_w3, daily_tnmhc_back=daily_tnmhc_back_w3,\n"
            "    start_date=weeks[3][0], end_date=weeks[3][1],\n"
            ")"
        ),

        nbformat.v4.new_markdown_cell("### Week 4"),
        nbformat.v4.new_markdown_cell("#### Ambient Checks"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.ambient import (\n"
            "    plot_ambient_comparisons, plot_voc_category_sums, plot_vs_totals,\n"
            ")\n\n"
            "ambient_w4 = ds.ambient.loc[weeks[4][0]:weeks[4][1]]"
        ),
        nbformat.v4.new_code_cell(
            f"plot_ambient_comparisons(ambient_w4, '{site}', {year}, {month}, label='Week 4')"
        ),
        nbformat.v4.new_code_cell(
            f"plot_voc_category_sums(ambient_w4, '{site}', {year}, {month}, label='Week 4')"
        ),
        nbformat.v4.new_code_cell(
            f"plot_vs_totals(ambient_w4, '{site}', {year}, {month})"
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
            f"rt_figs_w4 = plot_rt(rt_w4, data_w4, '{site}', {year}, {month}, samp_type='s')\n"
            "for _fig in rt_figs_w4:\n"
            "    display(_fig)\n"
            "rt_outliers_w4 = detect_rt_outliers(rt_w4[rt_w4['sample_type'] == 's'], rt_ref_cols, concentrations=data_w4, mdl_periods=mdl_periods)\n"
            "# rt_outliers_w4 = detect_rt_outliers(rt_w4[rt_w4['sample_type'] == 's'], rt_compound_cols, concentrations=data_w4, mdl_periods=mdl_periods)  # all compounds\n"
            'print(f"Week 4 RT outliers: {len(rt_outliers_w4)}")\n'
            "rt_outliers_w4"
        ),
        nbformat.v4.new_markdown_cell("#### Check Mis-IDed Reference Peaks"),
        nbformat.v4.new_code_cell(
            "reference = ['filename', name_to_aqs('n-pentane'), name_to_aqs('propane'), name_to_aqs('toluene'), name_to_aqs('benzene')]\n"
            "mask = (ambient_w4[name_to_aqs('n-pentane')] < 0.005) | (ambient_w4[name_to_aqs('propane')] < 0.005) | (ambient_w4[name_to_aqs('toluene')] < 0.005) | (ambient_w4[name_to_aqs('benzene')] < 0.005)\n"
            "misided = ambient_w4[reference][mask]\n"
            "misided.columns = [aqs_to_name(col) if col != 'filename' else col for col in misided.columns]\n"
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
            "    check_lognormal_outliers, compare_tnmtc_tnmhc,\n"
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
            "upper_cal_point_plot_w4 = None  # ← set to upper calibration point value (PLOT column)\n"
            "upper_cal_point_bp_w4 = None  # ← set to upper calibration point value (BP column)\n"
            "k = 3.5\n"
            "overrange_w4 = check_overrange_values(data_w4, upper_cal_point_plot_w4, upper_cal_point_bp_w4)\n"
            'print(f"Overrange values: {len(overrange_w4)}")\n'
            "if not overrange_w4.empty:\n"
            "    display(overrange_w4)\n\n"
            "outliers_w4 = check_lognormal_outliers(data_w4, mdl_periods, k=k)\n"
            'print(f"Lognormal outliers: {len(outliers_w4)}")\n'
            "if not outliers_w4.empty:\n"
            "    display(outliers_w4)\n\n"
            "totals_w4 = ds.totals.loc[weeks[4][0]:weeks[4][1]]\n"
            "daily_tnmhc_front_w4 = check_daily_max_tnmhc(totals_w4, \"tnmhc_front\")\n"
            "daily_tnmhc_back_w4  = check_daily_max_tnmhc(totals_w4, \"tnmhc_back\")\n"
            'print("Daily max TNMHC (Front):")\n'
            "display(daily_tnmhc_front_w4)\n"
            'print("Daily max TNMHC (Back):")\n'
            "display(daily_tnmhc_back_w4)\n\n"
            "tchc_diff_w4, tchc_ratio_w4 = compare_tnmtc_tnmhc(data_w4)\n"
            'print("TNMHC - TNMTC:")\n'
            "display(tchc_diff_w4)\n"
            'print("TNMHC / TNMTC:")\n'
            "display(tchc_ratio_w4)\n\n"
            "fill_reprocess_plan(\n"
            "    ds.data, mdvr_path, mdvr_path, year, month,\n"
            "    overrange=overrange_w4, daily_tnmhc_front=daily_tnmhc_front_w4, daily_tnmhc_back=daily_tnmhc_back_w4,\n"
            "    start_date=weeks[4][0], end_date=weeks[4][1],\n"
            ")"
        ),
        # --- Special samples ---
        nbformat.v4.new_markdown_cell("## 6. Special Samples"),
        nbformat.v4.new_markdown_cell(
            "### 6a. Ambient Spikes\n\n"
            "Set `spike_hour` to the sample_hour timestamp of the ambient spike run "
            "and `ambient_hours` to the two surrounding ambient hours. "
            "If no ambient spike was run this month, skip this section."
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.recovery import check_ambient_spike_recovery\n\n"
            "# ← Set these manually\n"
            "spike_hour    = pd.Timestamp('YYYY-MM-DD HH:00')  # sample_hour of the spike run\n"
            "ambient_hours = [pd.Timestamp('YYYY-MM-DD HH:00'),  # hour before\n"
            "                 pd.Timestamp('YYYY-MM-DD HH:00')]  # hour after\n"
            "spike_canister_periods = rts_periods  # or cvs_periods, depending on which canister was used\n\n"
            "spike_df   = exp.loc[[spike_hour]]\n"
            "ambient_df = ambient.loc[ambient_hours]\n\n"
            "spike_recovery = check_ambient_spike_recovery(spike_df, ambient_df, spike_canister_periods)\n"
            "display(spike_recovery)"
        ),
        nbformat.v4.new_code_cell(
            "# Export spike recovery to CSV for pasting into MDVR.\n"
            "spike_recovery_csv = spike_recovery.rename(\n"
            "    columns={c: aqs_to_name(c) for c in spike_recovery.columns if isinstance(c, int)}\n"
            ")\n"
            f"spike_csv_path = workspace_dir / 'ambient_spike_recovery.csv'\n"
            "spike_recovery_csv.to_csv(spike_csv_path)\n"
            'print(f"Written to {spike_csv_path}")'
        ),
        nbformat.v4.new_markdown_cell("### 6b. Calibrations"),
        nbformat.v4.new_code_cell(""),
        nbformat.v4.new_markdown_cell("### 6c. MDLs"),
        nbformat.v4.new_code_cell(""),

        # --- Blank QC ---
        nbformat.v4.new_markdown_cell("## 7. Blank check"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.blanks import compounds_above_mdl\n\n"
            "mdl_failures, threshold_failures = compounds_above_mdl(ds.blanks, mdl_periods)\n\n"
            'print("--- Compounds exceeding MDL ---")\n'
            'print_failures(mdl_failures, "MDL exceedances")\n\n'
            'print("\\n--- Compounds exceeding 0.5 ppbC ---")\n'
            'print_failures(threshold_failures, "Threshold exceedances")\n'
            'mdl_sum = mdl_failures.iloc[:,1:].sum(axis=0)\n'
            'mdl_sum_text = [f"{aqs_to_name(col).lower()} ({count} exceedances)" for col, count in mdl_sum.items() if count > 1]\n'
            'print(", ".join(mdl_sum_text))'
            
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
            'print_failures(rts_failures, "RTS")\n\n'
            "# Number of failing hours for each QC run, by compound (excluding nulled runs)\n"
            'qc_summary = {"CVS": (nulled_cvs, cvs_failures), "LCS": (nulled_lcs, lcs_failures), "RTS": (nulled_rts, rts_failures)}\n\n'
            "for qc, (nulls, fails) in qc_summary.items():\n"
            "    null = ~fails['filename'].isin(nulls)\n"
            "    total = fails[null].iloc[:, 1:].sum(axis=0)\n"
            '    sum_text = [f"{aqs_to_name(col).lower()} ({abs(count)} failures)" for col, count in total.items() if abs(count) > 1]\n'
            '    print(f"{qc}: {", ".join(sum_text) if sum_text else \"no failures\"}")\n'
        ),

        nbformat.v4.new_code_cell(
            "from autogc_validation.plots.qc import plot_qc_recovery"
        ),
        nbformat.v4.new_code_cell(
            f"plot_qc_recovery(ds.cvs, cvs_periods, 'CVS', '{site}', {year}, {month})"
        ),
        nbformat.v4.new_code_cell(
            f"plot_qc_recovery(ds.lcs, lcs_periods, 'LCS', '{site}', {year}, {month})"
        ),
        nbformat.v4.new_code_cell(
            f"plot_qc_recovery(ds.rts, rts_periods, 'RTS', '{site}', {year}, {month})"
        ),
        nbformat.v4.new_code_cell(
            f"plot_qc_recovery(ds.mdl, rts_periods, 'MDL', '{site}', {year}, {month})"
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.precision import check_cvs_precision\n\n"
            "precision_failures, cvs_precision_pairs = check_cvs_precision(ds.cvs, cvs_periods, nulled_filenames = nulled_cvs)\n"
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
            "from autogc_validation.qc.recovery import check_qc_recovery\n\n"
            "cvs_failures = check_qc_recovery(ds.cvs, cvs_periods)\n"
            "lcs_failures = check_qc_recovery(ds.lcs, lcs_periods)\n"
            "rts_failures = check_qc_recovery(ds.rts, rts_periods)\n\n"
            "from autogc_validation.qc.precision import check_cvs_precision\n\n"
            "precision_failures, cvs_precision_pairs = check_cvs_precision(ds.cvs, cvs_periods, nulled_filenames = nulled_cvs)\n"
            "from autogc_validation.reports import(\n"
            "    build_blank_qc_table, build_precision_qc_table,\n"
            "    build_recovery_qc_table, build_experimental_table, write_qc_table_to_excel,\n"
            ")\n\n"
            "# Adjust these start rows to match the merged-cell ranges in the MDVR template.\n"
            "blank_start_row       = 77\n"
            "cvs_start_row         = 22\n"
            "lcs_start_row         = 15\n"
            "rts_start_row         = 7\n"
            "precision_start_row   = 66\n"
            "experimental_start_row = 126\n\n"
            "blank_table       = build_blank_qc_table(mdl_failures, threshold_failures, nulled_filenames=nulled_blanks or None)\n"
            "cvs_table         = build_recovery_qc_table(cvs_failures, 'CVS', nulled_filenames=nulled_cvs or None)\n"
            "lcs_table         = build_recovery_qc_table(lcs_failures, 'LCS', nulled_filenames=nulled_lcs or None)\n"
            "rts_table         = build_recovery_qc_table(rts_failures, 'RTS')\n"
            "precision_table   = build_precision_qc_table(precision_failures, nulled_filenames=nulled_cvs or None)\n"
            "experimental_table = build_experimental_table(exp)\n\n"
            "write_qc_table_to_excel(blank_table,        mdvr_path, mdvr_path, 'Blanks',         blank_start_row)\n"
            "write_qc_table_to_excel(cvs_table,          mdvr_path, mdvr_path, 'CVS',            cvs_start_row)\n"
            "write_qc_table_to_excel(lcs_table,          mdvr_path, mdvr_path, 'LCS',            lcs_start_row)\n"
            "write_qc_table_to_excel(rts_table,          mdvr_path, mdvr_path, 'RTS',            rts_start_row)\n"
            "write_qc_table_to_excel(precision_table,    mdvr_path, mdvr_path, 'CVS Precision',  precision_start_row)\n"
            "write_qc_table_to_excel(experimental_table, mdvr_path, mdvr_path, 'Exp. Or Test Sample', experimental_start_row)\n"
            f'print(f"QC Review table written to {{mdvr_path}}")'
        ),

        # --- Station temperature ---
        nbformat.v4.new_markdown_cell(
            "## 10. Station temperature check\n\n"
            "Requires an AirVision database connection. "
            "Hours where station temperature exceeds 30\u00b0C are nulled with flag AE."
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.qc.room_temp import check_station_temp\n"
            "from autogc_validation.plots.room_temp import plot_station_temp\n"
            "from autogc_validation.reports import build_temp_null_lines\n\n"
            "# Temperature threshold for AE null qualification (°C).\n"
            "temp_null_threshold = 30.0\n\n"
            f"temp_result = check_station_temp('{site}', {month}, {year}, upper_threshold=temp_null_threshold)\n"
            "hourly_max = temp_result.temperatures.resample('h').max()\n"
            "n_over = int((hourly_max > temp_null_threshold).sum())\n"
            'print(f"Hours exceeding {temp_null_threshold}°C: {n_over}")'
        ),
        nbformat.v4.new_code_cell(
            f"plot_station_temp(temp_result, '{site}', {month}, {year}, upper_threshold=temp_null_threshold)"
        ),
        nbformat.v4.new_code_cell(
            "temp_null_lines = build_temp_null_lines(\n"
            "    temp_result.temperatures,\n"
            "    threshold=temp_null_threshold,\n"
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
            "upper_cal_point_plot = None  # ← set to upper calibration point value (PLOT column)\n"
            "upper_cal_point_bp = None  # ← set to upper calibration point value (BP column)\n"
            "k = 3.5\n"
            "overrange = check_overrange_values(ds.data, upper_cal_point_plot, upper_cal_point_bp)\n"
            'print(f"\\nOverrange values: {len(overrange)}")\n'
            "if not overrange.empty:\n"
            "    display(overrange)\n\n"
            "# Log-normal outlier detection\n"
            "outliers = check_lognormal_outliers(ds.data, mdl_periods, k=k)\n"
            'print(f"\\nLognormal outliers: {len(outliers)}")\n'
            "if not outliers.empty:\n"
            "    display(outliers)\n\n"
            "# Daily max TNMHC\n"
            "daily_tnmhc_front = check_daily_max_tnmhc(ds.totals, \"tnmhc_front\")\n"
            "daily_tnmhc_back  = check_daily_max_tnmhc(ds.totals, \"tnmhc_back\")\n"
            'print("\\nDaily max TNMHC (Front):")\n'
            "display(daily_tnmhc_front)\n"
            'print("Daily max TNMHC (Back):")\n'
            "daily_tnmhc_back"
        ),

        # --- Reprocess Plan ---
        nbformat.v4.new_markdown_cell("## 12. Reprocess Plan"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports import fill_reprocess_plan\n\n"
            "fill_reprocess_plan(\n"
            "    ds.data, mdvr_path, mdvr_path, year, month,\n"
            "    overrange=overrange, daily_tnmhc_front=daily_tnmhc_front, daily_tnmhc_back=daily_tnmhc_back,\n"
            ")"
        ),

        # --- QC Calculations ---
        nbformat.v4.new_markdown_cell("## 13. Populate QC calculations"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports import add_qc_to_mdvr\n\n"
            "add_qc_to_mdvr(mdvr_path, cvs)\n"
            "add_qc_to_mdvr(mdvr_path, lcs)\n"
            "add_qc_to_mdvr(mdvr_path, rts)"
        ),

        # --- MDVR ---
        nbformat.v4.new_markdown_cell("## 14. MDVR qualifier generation"),
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
            "#Manual entry for qualifier/null rows.\n"
            "from autogc_validation.reports import make_col_row\n"
            "_month_start = pd.Timestamp(start_date)\n"
            "_month_end   = pd.Timestamp(end_date)\n\n"

            "static_quals = pd.DataFrame([\n"
            "    make_col_row('alpha-pinene, beta-pinene, 2-methyl-1-pentene',   'No QC gas available','LJ', _month_start, _month_end, 'No QC gas available'),\n"
            "    make_col_row('isoprene, 1-hexene, n-dodecane',          'Inaccuracy in measurements', 'LJ', _month_start, _month_end,  'Due to uncertainty in measurements at the end of the column'),\n"
            "    make_col_row('m-diethylbenzene, p-diethylbenzene', 'Peak misidentification issues', 'LJ', _month_start, _month_end, 'Due to potential issues in peak identification at low levels'),\n"
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
        # --- QC recovery comparison to Orsat MAX ---
        nbformat.v4.new_markdown_cell(
            "## 15. QC Recovery Verification\n\n"
            "Compares locally-computed QC recovery against an independently-exported "
            "ORSAT MAX recovery figure CSV, one file per QC type. Set `cvs_path`, "
            "`lcs_path`, and `rts_path` below to the exported CSV for each QC type."
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports import compare_qc_recovery\n\n"
            "thresh = 0.005\n"
            'cvs_path = r""  # ← set path to ORSAT MAX CVS recovery export\n'
            'lcs_path = r""  # ← set path to ORSAT MAX LCS recovery export\n'
            'rts_path = r""  # ← set path to ORSAT MAX RTS recovery export\n\n'
            '#CVS\n'
            'diff_cvs = compare_qc_recovery(cvs, cvs_periods, cvs_path, thresh=thresh)\n'
            'print(f"CVS rows with |dataset - MAX| > {thresh}: {len(diff_cvs)}")\n'
            '#LCS\n'
            'diff_lcs = compare_qc_recovery(lcs, lcs_periods, lcs_path, thresh=thresh)\n'
            'print(f"LCS rows with |dataset - MAX| > {thresh}: {len(diff_lcs)}")\n'
            '#RTS\n'
            'diff_rts = compare_qc_recovery(rts, rts_periods, rts_path, thresh=thresh)\n'
            'print(f"RTS rows with |dataset - MAX| > {thresh}: {len(diff_rts)}")'
        ),
        # --- AQS verification ---
        nbformat.v4.new_markdown_cell("## 16. AQS upload verification"),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports.aqs import compare_aqs_to_dataset, compare_aqs_blanks_to_dataset\n\n"
            "from aqs_tools.processors import summarize_nulls_by_hour, summarize_qualifiers_by_hour, summarize_nulls_by_compound, summarize_qualifiers_by_compound\n"
            "from aqs_tools.parsers import generate_aqs_df\n"
            "from aqs_tools.utils import combine_quals\n"
            f"aqs_file = r\"\"  # ← set path to AQS RD upload file\n\n"
            "differences = compare_aqs_to_dataset(aqs_file, ds.ambient.copy())\n"
            'print(f"Rows with |dataset - AQS| > 0.001: {len(differences)}")\n'
            "differences\n"
            'nbh = summarize_nulls_by_hour(aqs_file, "RD", threshold = 34)\n'
            "display(nbh)\n"
            'qbh = summarize_qualifiers_by_hour(aqs_file, "RD", threshold = 34)\n'
            "display(qbh)\n"
            "pd.set_option('display.max_columns', None)\n"
            'nbc = summarize_nulls_by_compound(aqs_file, "RD")\n'
            "nbc_df = pd.DataFrame(nbc)\n"
            "display(nbc_df)\n"
            'qbc = summarize_qualifiers_by_compound(aqs_file, "RD")\n'
            "qbc_df = pd.DataFrame(qbc)\n"
            "display(qbc_df)\n\n"
            f"aqs_blank_file = r\"\"  # ← set path to AQS RB (field blank) upload file\n\n"
            "blank_differences = compare_aqs_blanks_to_dataset(aqs_blank_file, ds.blanks.copy())\n"
            'print(f"Blank rows with |dataset - AQS| > 0.001: {len(blank_differences)}")\n'
            "blank_differences\n"
        ),
        nbformat.v4.new_code_cell(
            "from autogc_validation.reports import check_eh, check_nd, check_md, check_sq\n\n"
            "upper_cal_point_plot = None  # ← set to upper calibration point value (PLOT column)\n"
            "upper_cal_point_bp = None  # ← set to upper calibration point value (BP column)\n\n"
            "eh = check_eh(aqs_file, upper_cal_point_plot, upper_cal_point_bp)\n"
            'print(f"EH false positives: {len(eh[\'false_positive\'])}, false negatives: {len(eh[\'false_negative\'])}")\n'
            "display(eh['false_positive'])\n"
            "display(eh['false_negative'])\n\n"
            "nd = check_nd(aqs_file)\n"
            'print(f"ND false positives: {len(nd[\'false_positive\'])}, false negatives: {len(nd[\'false_negative\'])}")\n'
            "display(nd['false_positive'])\n"
            "display(nd['false_negative'])\n\n"
            "md = check_md(aqs_file, mdl_periods)\n"
            'print(f"MD false positives: {len(md[\'false_positive\'])}, false negatives: {len(md[\'false_negative\'])}")\n'
            "display(md['false_positive'])\n"
            "display(md['false_negative'])\n\n"
            "sq = check_sq(aqs_file, mdl_periods)\n"
            'print(f"SQ false positives: {len(sq[\'false_positive\'])}, false negatives: {len(sq[\'false_negative\'])}")\n'
            "display(sq['false_positive'])\n"
            "display(sq['false_negative'])\n"
        ),


        # --- Transfer to network ---
        nbformat.v4.new_markdown_cell(
            "## 17. Transfer to network\n\n"
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
