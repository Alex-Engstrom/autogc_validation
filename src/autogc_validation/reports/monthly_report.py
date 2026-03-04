# -*- coding: utf-8 -*-
"""
Monthly validation report generator for AutoGC.

Produces a self-contained Quarto Markdown (.qmd) document that can be
rendered to HTML with ``quarto render <file>.qmd``.  The document re-runs
the full validation analysis and presents each result section with an
associated figure.
"""

import calendar
import logging
from pathlib import Path
from typing import Union

from autogc_validation.database.enums import Sites
from autogc_validation.workspace import WorkspaceResult

logger = logging.getLogger(__name__)

# Quarto front matter (HTML output, embedded resources, TOC, code hidden).
_FRONT_MATTER = """\
---
title: "{title}"
date: "{date}"
format:
  html:
    embed-resources: true
    toc: true
    toc-depth: 2
    theme: flatly
execute:
  echo: false
  warning: false
  message: false
jupyter: python3
---
"""

_SETUP_CELL = '''\
```{{python}}
#| label: setup
import pandas as pd
from pathlib import Path

from autogc_validation.dataset import Dataset
from autogc_validation.database.operations import get_mdl_periods, get_canister_periods
from autogc_validation.database.enums import ConcentrationUnit
from autogc_validation.qc.blanks import compounds_above_mdl
from autogc_validation.qc.recovery import check_qc_recovery
from autogc_validation.qc.precision import check_cvs_precision
from autogc_validation.reports.qualifiers import (
    build_blank_qualifier_lines,
    build_precision_qualifier_lines,
    build_qc_qualifier_lines,
    build_temp_null_lines,
)

# ── Configuration ──────────────────────────────────────────────────────────────
workspace_dir = Path(r"{workspace_dir}")
data_dir      = Path(r"{data_dir}")
database      = Path(r"{database}")
site_id       = {site_id}
year          = {year}
month         = {month}
sitename      = "{site}"
start_date    = "{start_date}"
end_date      = "{end_date}"

# ── Dataset ────────────────────────────────────────────────────────────────────
ds = Dataset(data_dir)

# ── MDL / canister periods ─────────────────────────────────────────────────────
mdl_periods  = get_mdl_periods(database, site_id, start_date, end_date, ConcentrationUnit.PPBC)
cvs_periods  = get_canister_periods(database, site_id, "CVS", start_date, end_date, ConcentrationUnit.PPBC)
lcs_periods  = get_canister_periods(database, site_id, "LCS", start_date, end_date, ConcentrationUnit.PPBC)
rts_periods  = get_canister_periods(database, site_id, "RTS", start_date, end_date, ConcentrationUnit.PPBC)

# ── QC checks ─────────────────────────────────────────────────────────────────
mdl_failures, threshold_failures = compounds_above_mdl(ds.blanks, mdl_periods)
cvs_failures = check_qc_recovery(ds.cvs, cvs_periods)
lcs_failures = check_qc_recovery(ds.lcs, lcs_periods)
rts_failures = check_qc_recovery(ds.rts, rts_periods)
precision_failures, cvs_precision_pairs = check_cvs_precision(ds.cvs)

# ── Qualifier lines ────────────────────────────────────────────────────────────
blank_quals     = build_blank_qualifier_lines(ds.data, mdl_failures, threshold_failures)
cvs_quals       = build_qc_qualifier_lines(ds.data, cvs_failures, "c")
lcs_quals       = build_qc_qualifier_lines(ds.data, lcs_failures, "e")
precision_quals = build_precision_qualifier_lines(ds.data, precision_failures, cvs_precision_pairs)

all_quals = pd.concat(
    [blank_quals, cvs_quals, lcs_quals, precision_quals],
    ignore_index=True,
)
```
'''

_SECTION_TEMPLATE = """\
## {heading}

{description}

```{{python}}
#| label: {label}
#| fig-cap: "{caption}"
{code}
```

"""

_SECTIONS = [
    dict(
        heading="Monthly Summary",
        description=(
            "Breakdown of all sample hours collected during the month. "
            "Valid ambient hours exclude samples nulled by data qualification "
            "codes AS (concentration above threshold) and AE (equipment malfunction). "
            "QC standards (blanks, CVS, LCS, RTS) and PT/experimental runs are "
            "shown separately."
        ),
        label="fig-monthly-summary",
        caption="Monthly sample hours breakdown.",
        code=(
            "from autogc_validation.plots.summary import plot_monthly_hours_summary\n"
            "plot_monthly_hours_summary(ds, all_quals, sitename, year, month)"
        ),
    ),
    dict(
        heading="Data Qualification Summary",
        description=(
            "Total number of qualifier lines issued this month, grouped by qualifier "
            "code. Each qualifier line represents one compound–interval combination. "
            "**LB** = blank above MDL; **AS** = blank above 0.5 ppbC threshold; "
            "**QX** = QC recovery outside 70–130 %; **LL/LK** = calibrant recovery "
            "low/high (whole-column flag); **AE** = equipment malfunction null."
        ),
        label="fig-qual-summary",
        caption="Qualifier lines by code.",
        code=(
            "from autogc_validation.plots.summary import plot_qual_summary\n"
            "plot_qual_summary(all_quals, sitename, year, month)"
        ),
    ),
    dict(
        heading="Data Nullification Summary",
        description=(
            "Ambient hours nulled during the month, broken down by nullification "
            "reason. Nulled hours are estimated by intersecting the null qualifier "
            "intervals with the ambient sample timestamps."
        ),
        label="fig-null-summary",
        caption="Nulled ambient hours by reason.",
        code=(
            "from autogc_validation.plots.summary import plot_null_summary\n"
            "plot_null_summary(all_quals, ds, sitename, year, month)"
        ),
    ),
    dict(
        heading="Blank Summary",
        description=(
            "TNMTC and TNMHC concentrations measured in field blank samples over "
            "the month. Elevated values indicate potential contamination that may "
            "affect ambient data quality."
        ),
        label="fig-blank-totals",
        caption="Blank TNMTC and TNMHC concentrations.",
        code=(
            "from autogc_validation.plots.summary import plot_blank_totals\n"
            "plot_blank_totals(ds, sitename, year, month)"
        ),
    ),
    dict(
        heading="CVS Recovery — Key Compounds",
        description=(
            "Recovery time series for the PLOT-column calibrant (Propane) and the "
            "lightest and heaviest PLOT compounds (Ethane and 1-Hexene), and the "
            "BP-column calibrant (Toluene) with N-Hexane and p-Diethylbenzene. "
            "Reference lines at 70 %, 100 %, and 130 % are shown."
        ),
        label="fig-cvs-timeseries",
        caption="CVS recovery time series for key PLOT and BP compounds.",
        code=(
            "from autogc_validation.plots.recovery import plot_recovery_timeseries\n"
            "plot_recovery_timeseries(ds.cvs, cvs_periods, 'CVS', sitename, year, month)"
        ),
    ),
    dict(
        heading="CVS Recovery — All Compounds",
        description=(
            "Distribution of CVS recovery across all compounds for the month. "
            "Each box shows the median, interquartile range, and full spread. "
            "Individual run values are overlaid as points. "
            "Blue boxes are PLOT-column compounds; orange are BP-column compounds."
        ),
        label="fig-cvs-boxplot",
        caption="CVS recovery distribution by compound.",
        code=(
            "from autogc_validation.plots.recovery import plot_recovery_boxplot\n"
            "plot_recovery_boxplot(ds.cvs, cvs_periods, 'CVS', sitename, year, month)"
        ),
    ),
    dict(
        heading="LCS Recovery — Key Compounds",
        description=(
            "Recovery time series for LCS standards. Same compound selection as "
            "the CVS time-series plot."
        ),
        label="fig-lcs-timeseries",
        caption="LCS recovery time series for key PLOT and BP compounds.",
        code=(
            "from autogc_validation.plots.recovery import plot_recovery_timeseries\n"
            "plot_recovery_timeseries(ds.lcs, lcs_periods, 'LCS', sitename, year, month)"
        ),
    ),
    dict(
        heading="LCS Recovery — All Compounds",
        description=(
            "Distribution of LCS recovery across all compounds for the month."
        ),
        label="fig-lcs-boxplot",
        caption="LCS recovery distribution by compound.",
        code=(
            "from autogc_validation.plots.recovery import plot_recovery_boxplot\n"
            "plot_recovery_boxplot(ds.lcs, lcs_periods, 'LCS', sitename, year, month)"
        ),
    ),
    dict(
        heading="RTS Recovery — Key Compounds",
        description=(
            "Recovery time series for RTS standards. The BP panel shows Toluene "
            "(calibrant), N-Hexane (lightest), and N-Dodecane (heaviest) — "
            "reflecting the heavier compound range targeted by RTS canisters."
        ),
        label="fig-rts-timeseries",
        caption="RTS recovery time series for key PLOT and BP compounds.",
        code=(
            "from autogc_validation.plots.recovery import plot_recovery_timeseries\n"
            "plot_recovery_timeseries(ds.rts, rts_periods, 'RTS', sitename, year, month)"
        ),
    ),
    dict(
        heading="RTS Recovery — All Compounds",
        description=(
            "Distribution of RTS recovery across all compounds for the month."
        ),
        label="fig-rts-boxplot",
        caption="RTS recovery distribution by compound.",
        code=(
            "from autogc_validation.plots.recovery import plot_recovery_boxplot\n"
            "plot_recovery_boxplot(ds.rts, rts_periods, 'RTS', sitename, year, month)"
        ),
    ),
    dict(
        heading="Calibration Summary",
        description=(
            "PLOT and BP column response factors over the month. "
            "\n\n"
            "> **Placeholder** — calibration data has not yet been added to the "
            "database. This section will be populated once calibration records are "
            "available."
        ),
        label="fig-calibration",
        caption="Calibration response factors (placeholder).",
        code='print("Calibration data not yet available.")',
    ),
    dict(
        heading="MDL Summary",
        description=(
            "Method Detection Limits (MDLs) active during the month, shown in "
            "compound elution order. PLOT-column compounds are shown in blue; "
            "BP-column compounds in orange."
        ),
        label="fig-mdl",
        caption="Active MDL values by compound.",
        code=(
            "import plotly.graph_objects as go\n"
            "from autogc_validation.database.enums import ColumnType, aqs_to_name, get_codes_by_column\n\n"
            "# Use the first MDL period if multiple periods exist.\n"
            "mdl_row = mdl_periods.iloc[0]\n"
            "plot_set = set(get_codes_by_column(ColumnType.PLOT))\n"
            "ordered = [\n"
            "    c for c in get_codes_by_column(ColumnType.PLOT) + get_codes_by_column(ColumnType.BP)\n"
            "    if c in mdl_row.index and not pd.isna(mdl_row[c])\n"
            "]\n"
            "fig_mdl = go.Figure(go.Bar(\n"
            "    x=[aqs_to_name(c) for c in ordered],\n"
            "    y=[mdl_row[c] for c in ordered],\n"
            "    marker_color=['#1f77b4' if c in plot_set else '#ff7f0e' for c in ordered],\n"
            "    hovertemplate='<b>%{x}</b><br>MDL: %{y:.4f} ppbC<extra></extra>',\n"
            "))\n"
            "fig_mdl.update_layout(\n"
            "    title=f'{sitename} {year}-{month:02d} Method Detection Limits',\n"
            "    yaxis_title='MDL (ppbC)',\n"
            "    xaxis_title='Compound (PLOT = blue, BP = orange)',\n"
            "    height=450,\n"
            "    plot_bgcolor='white', paper_bgcolor='white',\n"
            ")\n"
            "fig_mdl.show()"
        ),
    ),
    dict(
        heading="Data Quality Summary",
        description=(
            "Retention time distribution and ambient compound comparison plots "
            "for the full month. Retention time outliers help identify potential "
            "misidentifications. Compound scatter plots confirm expected chemical "
            "relationships in the ambient air."
        ),
        label="fig-dq-rt",
        caption="Retention time distribution — ambient samples.",
        code=(
            "from autogc_validation.plots.rt import plot_rt\n"
            "from autogc_validation.database.enums import RT_REFERENCE_CODES\n"
            "rt_ref_cols = [c for c in RT_REFERENCE_CODES if c in ds.rt.columns]\n"
            f"plot_rt(ds.rt, ds.data, sitename, year, month, samp_type='s')"
        ),
    ),
    dict(
        heading="Ambient Compound Comparisons",
        description=(
            "Scatter plots of key compound pairs and VOC category sums for "
            "ambient samples. Deviations from expected relationships can indicate "
            "contamination, instrument issues, or unusual source contributions."
        ),
        label="fig-dq-ambient",
        caption="Ambient compound comparison scatter plots.",
        code=(
            "from autogc_validation.plots.ambient import plot_ambient_comparisons\n"
            f"plot_ambient_comparisons(ds.ambient, sitename, year, month)"
        ),
    ),
]


def generate_monthly_report(
    result: WorkspaceResult,
    site: str,
    year: int,
    month: int,
    database: str | None = None,
) -> Path:
    """Generate a Quarto Markdown monthly validation report.

    The produced ``.qmd`` file is self-contained: it re-runs the full
    validation analysis and embeds all figures.  Render it with::

        quarto render <site><YYYYMM>_report.qmd

    Args:
        result: WorkspaceResult from create_workspace (must have base_dir and
            data_dir set).
        site: Site name code (e.g. ``'EQ'``).
        year: Year.
        month: Month number (1–12).
        database: Optional path to the SQLite database.  Defaults to the
            standard project-relative path.

    Returns:
        Path to the generated ``.qmd`` file.
    """
    from autogc_validation.workspace import _DBPATH

    db_path = database or _DBPATH
    num_days = calendar.monthrange(year, month)[1]
    yyyymm = f"{year}{month:02d}"
    site_code: int = Sites[site]

    workspace_dir = str(result.base_dir)
    data_dir = str(result.data_dir)
    start_date = f"{year}-{month:02d}-01 00:00"
    end_date = f"{year}-{month:02d}-{num_days} 23:59"
    title = f"{site} {yyyymm} Monthly Validation Report"
    import datetime
    date_str = datetime.date.today().isoformat()

    lines = [
        _FRONT_MATTER.format(title=title, date=date_str),
        _SETUP_CELL.format(
            workspace_dir=workspace_dir,
            data_dir=data_dir,
            database=db_path,
            site_id=site_code,
            year=year,
            month=month,
            site=site,
            start_date=start_date,
            end_date=end_date,
        ),
    ]

    for section in _SECTIONS:
        lines.append(_SECTION_TEMPLATE.format(**section))

    content = "\n".join(lines)

    report_path = result.base_dir / f"{site}{yyyymm}_report.qmd"
    report_path.write_text(content, encoding="utf-8")
    logger.info("Monthly report generated: %s", report_path)
    return report_path
