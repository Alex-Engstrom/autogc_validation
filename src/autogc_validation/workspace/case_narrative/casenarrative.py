# -*- coding: utf-8 -*-
"""
Quarto (.qmd) case-narrative generation for monthly AutoGC validation workspaces.
"""

import calendar
import logging
import shutil
from pathlib import Path
from string import Template

from autogc_validation.database.enums import Sites
from autogc_validation.database.operations import get_table
from autogc_validation.workspace.result import WorkspaceResult

logger = logging.getLogger(__name__)

# Resolve paths relative to the project root (4 levels up from this file:
# case_narrative/ -> workspace/ -> autogc_validation/ -> src/ -> project root)
_PROJECT_ROOT = Path(__file__).parents[4]
_DBPATH = str(_PROJECT_ROOT / "data" / "autogc.db")
_LOGO_TEMPLATE = _PROJECT_ROOT / "templates" / "case_narrative" / "logo.png"


_QMD_TEMPLATE = """---
title: " "
format:
    typst:
        toc: true
        font-heading: "Times New Roman"
        mainfont: "Times New Roman"
        minimal: true
        include-in-header:
          text: |
            #set page(
              margin: (left: 2.5cm, right: 2.5cm, top: 3cm, bottom: 2.5cm),
              header: grid(
                columns: (1fr, 1fr),
                align: (left, right),
                text(14pt, fill: gray)[$site_name_long ($site) $month_name $year      Case Narrative],
                box(height: 1.5cm, image("logo.png"))
              )
            )
            #show figure.caption: it => align(left, it)
            #show figure.where(kind: image): it => figure(
              it.body,
              caption: it.caption,
              kind: "quarto-float-fig",
              supplement: "Figure",
            )
crossref:
  fig-prefix: "Fig."

execute:
  echo: false
  warning: false
jupyter: python3
---

```{python}
# imports
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

from autogc_validation.database.enums import aqs_to_name, name_to_aqs
workspace_dir = Path(r"$workspace_dir")
data_dir = Path(r"$data_dir")
site_id = $site_id
year  = $year
month = $month
database = Path(r"$database")
start_date = "$start_date"
end_date   = "$end_date"
```

```{python}
#| echo: false
# Dataset
from autogc_validation.dataset import Dataset
ds = Dataset(data_dir)

ambient = ds.ambient
blank   = ds.blanks
cvs     = ds.cvs
lcs     = ds.lcs
rts     = ds.rts
exp     = ds.experimental
cal     = ds.calibration
mdl     = ds.mdl

from autogc_validation.database.operations import (
    get_mdl_periods, get_canister_periods
)
from autogc_validation.database.enums import ConcentrationUnit

mdl_periods = get_mdl_periods(database, site_id, start_date, end_date, ConcentrationUnit.PPBC)


cvs_periods = get_canister_periods(database, site_id, "CVS", start_date, end_date, ConcentrationUnit.PPBC)
lcs_periods = get_canister_periods(database, site_id, "LCS", start_date, end_date, ConcentrationUnit.PPBC)
rts_periods = get_canister_periods(database, site_id, "RTS", start_date, end_date, ConcentrationUnit.PPBC)

from autogc_validation.workspace.case_narrative import plots, flags
AQS_TXTFILE = Path(r"___")  # TODO: fill in path to this month's AQS RD upload .txt file
sample_summary = flags.SampleSummary(AQS_TXTFILE)
```

# General Monthly Summary

::::: {layout="[1,1]"}
::: {#text-col}
\\

- Collection Rate: **___%**

- Overall Data Completeness: **`{python} f"{sample_summary.ambient/sample_summary.total_hours*100:.1f}%"`**

- QC-Adjusted Data Completeness: **`{python} f"{(sample_summary.ambient+sample_summary.total_qc_hours)/sample_summary.total_hours*100:.1f}%"`**

- A total of **`{python} sample_summary.total_nulled_hours - sample_summary.total_qc_hours - sample_summary.nulled_by_code.get("XX", 0)`** full ambient hours were nulled.

- A total of **___** hours were lost.
:::

::: {#plot-col}
```{python}
#| label: sample-type-summary
#| fig-cap: Sample Type Summary
flags.plot_monthly_hours_summary(sample_summary)

```

:::
:::::

_Describe this month's events here: instrument issues, QC recovery trends, calibrant failures, and any other notable occurrences._

# Data Null Summary

::::: {layout="[1,1]"}
::: {null-bullets}

A total of **___** full ambient hours were nulled with the following codes:

- CODE (Description) **___ hours**: Explanation of cause and how the null was applied.
:::

::: {null-plot}
```{python}
#| label: null-summary
#| fig-cap: Nulled Full Ambient Hours by Null Code
flags.plot_null_summary(sample_summary)
```

:::
:::::

<!-- Delete the paragraphs below if no column-specific nulls occurred this month. -->

Only PLOT column compounds were nulled for total of **___** hours with the following code(s):

>* CODE (Description) **___ hours**: Explanation.

Only BP column compounds were nulled for total of **___** hours with the following code(s):

>* CODE (Description) **___ hours**: Explanation.

# Data Qualification Summary

LJ (Estimated Value): _List compounds qualified LJ this month and why._

QX (Does not Meet QC Criteria): _List compounds qualified QX this month and why. See MDVR spreadsheet for greater detail._

# QA Summary

## Blank Response

```{python}
#| output: asis
print(plots.exceedance_summary_text(blank, mdl_periods))
```

```{python}
#| label: blank-tnmhc
#| fig-cap: Total Non Methane Hydrocarbon concentration in Blanks
plots.plot_tnmhc(blank)
```

## CVS

```{python}
cvs_stats = plots.recovery_stats(cvs, cvs_periods)

```

```{python}
#| output: asis
print(plots.exceedance_summary_text(cvs, cvs_periods))
```

Average CVS propane recovery for the month was **`{python} f'{cvs_stats.loc["Propane","mean"]:.1f}'`** $$\\pm$$ **`{python} f'{cvs_stats.loc["Propane","stdev"]:.1f}'`**% (1 stdev). Average toluene recovery for the month was **`{python} f'{cvs_stats.loc["Toluene","mean"]:.1f}'`** $$\\pm$$ **`{python} f'{cvs_stats.loc["Toluene","stdev"]:.1f}'`**% (1 stdev).

```{python}
#| label: calibrant-cvs-recoveries
#| fig-cap: Calibrant CVS recovery timeseries (left) and box-and-whisker plot (right)
plots.recovery_plot(cvs, cvs_periods)

```

## LCS

```{python}
lcs_stats = plots.recovery_stats(lcs, lcs_periods)

```

```{python}
#| output: asis
print(plots.exceedance_summary_text(lcs, lcs_periods))
```

Average LCS propane recovery for the month was **`{python} f'{lcs_stats.loc["Propane","mean"]:.1f}'`** $$\\pm$$ **`{python} f'{lcs_stats.loc["Propane","stdev"]:.1f}'`**% (1 stdev). Average toluene recovery for the month was **`{python} f'{lcs_stats.loc["Toluene","mean"]:.1f}'`** $$\\pm$$ **`{python} f'{lcs_stats.loc["Toluene","stdev"]:.1f}'`**% (1 stdev).

```{python}
#| label: calibrant-lcs-recoveries
#| fig-cap: Calibrant LCS recovery timeseries (left) and box-and-whisker plot (right)
plots.recovery_plot(lcs, lcs_periods)

```

## RTS

```{python}
rts_stats = plots.recovery_stats(rts, rts_periods)

```

Average RTS propane recovery for the month was **`{python} f'{rts_stats.loc["Propane","mean"]:.1f}'`** $$\\pm$$ **`{python} f'{rts_stats.loc["Propane","stdev"]:.1f}'`**% (1 stdev). Average toluene recovery for the month was **`{python} f'{rts_stats.loc["Toluene","mean"]:.1f}'`** $$\\pm$$ **`{python} f'{rts_stats.loc["Toluene","stdev"]:.1f}'`**% (1 stdev).

```{python}
#| label: calibrant-rts-recoveries
#| fig-cap: Calibrant RTS recovery timeseries (left) and box-and-whisker plot (right)
plots.recovery_plot(rts, rts_periods)

```

# Calibrations

| Date run   | PLOT RF | BP RF |
|------------|---------|-------|
| ___        | ___     | ___   |

Table 1. Calibrations over time

# Method Detection Limit (MDL)

None performed this month.

# Proficiency Testing (PT)

None performed this month.

# Ambient Air Spikes

None performed this month.

# Nonconformances

None.
"""


def _generate_case_narrative(
    result: WorkspaceResult,
    site: str,
    year: int,
    month: int,
) -> Path:
    """Generate a pre-filled Quarto case-narrative (.qmd) in the workspace.

    Mirrors the hand-built test.qmd template, with paths and computed
    monthly stats filled in for the given site and month. Narrative
    sections (monthly summary, null-code explanations, qualification
    summary) are left as sentence skeletons for manual fill-in, since
    they describe month-specific events that can't be generated.
    AQS_TXTFILE is also left as a manual fill-in, since the AQS upload
    file isn't tracked anywhere the generator can discover it from.

    Args:
        result: WorkspaceResult from create_workspace (must have base_dir
            and data_dir set).
        site: Site name code (e.g. "EQ").
        year: Year.
        month: Month number (1-12).

    Returns:
        Path to the created .qmd file.
    """
    num_days = calendar.monthrange(year, month)[1]
    yyyymm = f"{year}{month:02d}"
    site_id = int(Sites[site])

    sites_df = get_table(_DBPATH, "sites").set_index("site_id")
    site_name_long = sites_df.loc[site_id, "name_long"]

    start_date_str = f"{year}-{month:02d}-01 00:00"
    end_date_str = f"{year}-{month:02d}-{num_days} 23:59"

    content = Template(_QMD_TEMPLATE).substitute(
        site=site,
        site_name_long=site_name_long,
        month_name=calendar.month_name[month],
        year=year,
        month=month,
        workspace_dir=str(result.base_dir),
        data_dir=str(result.data_dir),
        site_id=site_id,
        database=_DBPATH,
        start_date=start_date_str,
        end_date=end_date_str,
    )

    narrative_path = result.base_dir / f"{site}{yyyymm}_case_narrative.qmd"
    narrative_path.write_text(content)
    logger.info("Case narrative created: %s", narrative_path)

    _copy_logo(result.base_dir)

    return narrative_path


def _copy_logo(base_dir: Path) -> None:
    """Copy logo.png into the workspace so Typst can resolve image("logo.png").

    Typst sandboxes file access to the rendered document's own directory,
    so the logo must live next to the .qmd rather than at its shared
    template location. Logs a warning if the template logo is missing
    rather than raising.
    """
    if not _LOGO_TEMPLATE.exists():
        logger.warning("Case narrative logo template not found: %s", _LOGO_TEMPLATE)
        return

    dest = base_dir / "logo.png"
    shutil.copy2(_LOGO_TEMPLATE, dest)
    logger.info("Copied case narrative logo to %s", dest)
