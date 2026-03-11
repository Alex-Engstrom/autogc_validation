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
    toc-depth: 3
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
import plotly.io as pio
pio.renderers.default = "plotly_mimetype+png"

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
precision_failures, cvs_precision_pairs = check_cvs_precision(ds.cvs, cvs_periods)

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

# Section with a figure (has #| label and #| fig-cap).
_SECTION_TEMPLATE = """\
## {heading}

{description}

```{{python}}
#| label: {label}
#| fig-cap: "{caption}"
{code}
```

"""

# Section with code output but no figure label/caption (e.g. text summaries).
_CODE_SECTION_TEMPLATE = """\
## {heading}

{description}

```{{python}}
{code}
```

"""


def _build_section(section: dict) -> str:
    """Build a section string from a section dict.

    The dict may contain:
      heading, description — required
      level                — heading level (default 2 → ##, use 3 for ###)
      label, caption, code — for figure sections
      code (no label)      — for code-output sections
      pre_extra            — raw Quarto markdown inserted between description and code block
      extra                — raw Quarto markdown appended after the main block
    """
    code = section.get("code")
    pre_extra = section.get("pre_extra", "")
    extra = section.get("extra", "")
    hashes = "#" * section.get("level", 2)
    heading_line = f"{hashes} {section['heading']}"
    description = section["description"]
    pre = f"{pre_extra}\n\n" if pre_extra else ""

    if code is None:
        s = f"{heading_line}\n\n{description}\n\n"
    elif section.get("label"):
        s = (
            f"{heading_line}\n\n"
            f"{description}\n\n"
            f"{pre}"
            f"```{{python}}\n"
            f"#| label: {section['label']}\n"
            f"#| fig-cap: \"{section['caption']}\"\n"
            f"{code}\n"
            f"```\n\n"
        )
    else:
        s = (
            f"{heading_line}\n\n"
            f"{description}\n\n"
            f"{pre}"
            f"```{{python}}\n"
            f"{code}\n"
            f"```\n\n"
        )

    if extra:
        s += extra + "\n\n"
    return s


_BLANK_BULLET_EXTRA = (
    "\n```{python}\n"
    "from IPython.display import display, Markdown\n"
    "from autogc_validation.database.enums import aqs_to_name\n\n"
    "bl_compound_cols = [c for c in mdl_failures.columns if isinstance(c, int)]\n"
    "bl_lines = []\n"
    "for c in bl_compound_cols:\n"
    "    mdl_n    = int((mdl_failures[c] == 1).sum())\n"
    "    thresh_n = int((threshold_failures[c] == 1).sum()) if c in threshold_failures.columns else 0\n"
    "    if mdl_n > 0 or thresh_n > 0:\n"
    "        pl_m  = 's' if mdl_n != 1 else ''\n"
    "        pl_t  = 's' if thresh_n != 1 else ''\n"
    "        cname = aqs_to_name(c)\n"
    "        bl_lines.append(f'- **{cname}**: {mdl_n} MDL exceedance{pl_m}, {thresh_n} \u00d7 0.5\u00a0ppbC exceedance{pl_t}')\n"
    "if bl_lines:\n"
    '    display(Markdown("Blank failures for the month:\\n\\n" + "\\n".join(bl_lines)))\n'
    "else:\n"
    '    display(Markdown("No blank MDL or threshold exceedances this month."))\n'
    "```\n"
)

_CVS_BULLET_EXTRA = (
    "\n```{python}\n"
    "from IPython.display import display, Markdown\n"
    "from autogc_validation.database.enums import aqs_to_name\n\n"
    "cvs_cmpd_cols = [c for c in cvs_failures.columns if isinstance(c, int)]\n"
    "cvs_lines = []\n"
    "for c in cvs_cmpd_cols:\n"
    "    n = int((cvs_failures[c] != 0).sum())\n"
    "    if n > 0:\n"
    "        cvs_lines.append(f'- **{aqs_to_name(c)}**: {n} out of range result{\"s\" if n != 1 else \"\"}')\n"
    "if cvs_lines:\n"
    '    display(Markdown("Compounds with CVS failures during the month:\\n\\n" + "\\n".join(cvs_lines)))\n'
    "else:\n"
    '    display(Markdown("No CVS recovery failures this month."))\n'
    "```\n"
)

_LCS_BULLET_EXTRA = (
    "\n```{python}\n"
    "from IPython.display import display, Markdown\n"
    "from autogc_validation.database.enums import aqs_to_name\n\n"
    "lcs_cmpd_cols = [c for c in lcs_failures.columns if isinstance(c, int)]\n"
    "lcs_lines = []\n"
    "for c in lcs_cmpd_cols:\n"
    "    n = int((lcs_failures[c] != 0).sum())\n"
    "    if n > 0:\n"
    "        lcs_lines.append(f'- **{aqs_to_name(c)}**: {n} out of range result{\"s\" if n != 1 else \"\"}')\n"
    "if lcs_lines:\n"
    '    display(Markdown("Compounds with LCS failures during the month:\\n\\n" + "\\n".join(lcs_lines)))\n'
    "else:\n"
    '    display(Markdown("No LCS recovery failures this month."))\n'
    "```\n"
)

_MDL_TEXT_CODE = (
    "from IPython.display import display, Markdown\n\n"
    "mdl_idx = mdl_periods.index.sort_values()\n"
    "if len(mdl_idx) == 1:\n"
    "    start = mdl_idx[0]\n"
    "    display(Markdown(f'MDLs collected on {start.strftime(\"%Y-%m-%d\")} were applied for the full month.'))\n"
    "else:\n"
    "    lines = []\n"
    "    for i, start in enumerate(mdl_idx):\n"
    "        if i + 1 < len(mdl_idx):\n"
    "            end_ts = mdl_idx[i + 1] - pd.Timedelta(hours=1)\n"
    "            lines.append(f'MDLs collected on {start.strftime(\"%Y-%m-%d\")} were applied through {end_ts.strftime(\"%Y-%m-%d\")}.')\n"
    "        else:\n"
    "            lines.append(f'New MDLs collected on {start.strftime(\"%Y-%m-%d\")} were applied through end of month.')\n"
    "    display(Markdown('  \\n'.join(lines)))\n"
)

_SECTIONS = [
    dict(
        heading="Monthly Summary",
        description=(" "
        ),
        label="fig-monthly-summary",
        caption= "Breakdown of all sample hours collected during the month."
        "Valid ambient hours exclude nulled ambient samples"
        "QC standards (blanks, CVS, LCS, RTS) and PT/experimental runs are "
        "shown separately.",
        code=(
            "from autogc_validation.plots.summary import plot_monthly_hours_summary\n\n"
            "# ── Enter total nulled hours manually ─────────────────────────────────\n"
            "nulled_hours = 0  # ← update this value\n\n"
            "# ── Optional: override sample-type counts from the dataset ────────────\n"
            "# overrides = {'CVS': 4, 'Blanks': 2}  # label strings from _SAMPLE_TYPE_META\n\n"
            "plot_monthly_hours_summary(ds, sitename, year, month, nulled_hours=nulled_hours)\n"
            "# plot_monthly_hours_summary(ds, sitename, year, month, nulled_hours=nulled_hours, overrides=overrides)"
        ),
    ),
    dict(
        heading="Data Nullification Summary",
        description=(""
            
        ),
        label="fig-null-donut",
        caption="Ambient hours nulled during the month, broken down by nullification code.",
        code=(
            "import calendar\n"
            "from autogc_validation.plots.summary import plot_null_donut\n\n"
            "# ── Enter nulled hours by qualifier code ──────────────────────────────\n"
            "# Add or remove codes as needed. See QUALIFIER_CODES for valid null codes.\n"
            "nulled_hours_by_code = {\n"
            '    "AE": 0,\n'
            '    "AS": 0,\n'
            "}\n\n"
            "# ── Consistency check against Monthly Summary ─────────────────────────\n"
            "total_hours_in_month = calendar.monthrange(year, month)[1] * 24\n"
            "n_missing = total_hours_in_month - len(ds.data)\n"
            "expected_total = nulled_hours + n_missing\n"
            "actual_total = sum(nulled_hours_by_code.values())\n"
            "if actual_total != expected_total:\n"
            "    print(\n"
            "        f'WARNING: entries sum to {actual_total} h, '\n"
            "        f'expected {expected_total} '\n"
            "        f'(nulled_hours={nulled_hours}, missing_hours={n_missing})'\n"
            "    )\n\n"
            "plot_null_donut(nulled_hours_by_code, sitename, year, month)"
        ),
    ),
    dict(
        heading="Data Qualification Summary",
        description=(
            "Summary of data qualifiers issued this month."
        ),
        code=None,
    ),
    dict(
        heading="Blank Summary",
        description=(""
            
        
        ),
        label="fig-blank-totals",
        caption="TNMTC and TNMHC concentrations measured in blank samples over the month.",
        code=(
            "from autogc_validation.plots.summary import plot_blank_totals\n"
            "plot_blank_totals(ds, sitename, year, month)"
        ),
        pre_extra=_BLANK_BULLET_EXTRA,
    ),
    dict(
        heading="Calibrant Recovery",
        description=(""

        ),
        label="fig-calibrant-timeseries",
        caption=            "Propane (PLOT column) and Toluene (BP column) recovery for CVS, LCS, "
                    "and RTS standards over the month. Reference lines at 70 %, 100 %, and "
                    "130 % are shown.",
        code=(
            "from autogc_validation.plots.recovery import plot_combined_calibrant_timeseries\n"
            "plot_combined_calibrant_timeseries(\n"
            "    [\n"
            "        ('CVS', ds.cvs, cvs_periods),\n"
            "        ('LCS', ds.lcs, lcs_periods),\n"
            "        ('RTS', ds.rts, rts_periods),\n"
            "    ],\n"
            "    sitename, year, month,\n"
            ")"
        ),
    ),
    dict(
        heading="CVS Recovery",
        description=(
            "Calibration verification standard (CVS) recovery results for the month. "
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
        pre_extra=_CVS_BULLET_EXTRA,
    ),
    dict(
        heading="LCS Recovery",
        description=(
            "Laboratory control standard (LCS) recovery results for the month."
        ),
        label="fig-lcs-boxplot",
        caption="LCS recovery distribution by compound.",
        code=(
            "from autogc_validation.plots.recovery import plot_recovery_boxplot\n"
            "plot_recovery_boxplot(ds.lcs, lcs_periods, 'LCS', sitename, year, month)"
        ),
        pre_extra=_LCS_BULLET_EXTRA,
    ),
    dict(
        heading="RTS Recovery",
        description=(
            "Retention time standard (RTS) recovery results for the month. "
            "RTS failures are noted but do not result in data qualification."
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
            "Method Detection Limits (MDLs) applied during the month."
        ),
        code=_MDL_TEXT_CODE,
    ),
    dict(
        heading="Proficiency Testing (PT)",
        description="",
        code=None,
    ),
    dict(
        heading="Ambient Air Spikes",
        description="",
        code=None,
    ),
    dict(
        heading="Nonconformances",
        description="",
        code=None,
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
    title = f"{site} {yyyymm} Monthly Case Narrative"
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
        lines.append(_build_section(section))

    content = "\n".join(lines)

    report_path = result.base_dir / "VALIDATION DOCS" / f"{site}{yyyymm}_case_narrative.qmd"
    report_path.write_text(content, encoding="utf-8")
    logger.info("Monthly report generated: %s", report_path)
    return report_path


def render_monthly_report(qmd_path: Path) -> Path:
    """Render a generated QMD file with Quarto.

    Shells out to ``quarto render`` to produce HTML output.
    Call :func:`generate_monthly_report` first to produce the ``.qmd`` file,
    then call this function once you are satisfied with its contents.

    Args:
        qmd_path: Path to the ``.qmd`` file produced by
            :func:`generate_monthly_report`.

    Returns:
        Path to the rendered ``.html`` file.

    Raises:
        RuntimeError: If ``quarto render`` exits with a non-zero return code.
    """
    import subprocess

    logger.info("Running quarto render on %s", qmd_path)
    proc = subprocess.run(
        ["quarto", "render", str(qmd_path)],
        capture_output=True,
        text=True,
        cwd=str(qmd_path.parent),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"quarto render failed:\n{proc.stderr}")
    logger.info("Quarto render complete")
    return qmd_path.with_suffix(".html")
