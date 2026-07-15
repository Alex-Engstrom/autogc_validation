"""Process .tx1 chromatogram files into sample-type crosstab CSVs.

This module is the autogc_validation integration point for the AutoGC
instrument's text output format.  Parsing logic lives in autogc_core.txt;
this module adds the validation-side concerns: sample-type classification
via SampleTypeLetter and AQS-coded CSV output.
"""

import csv
import logging
from pathlib import Path

import pandas as pd

from autogc_core.enums import CompoundAQSCode, CompoundName
from autogc_core.txt import find_txt_files, parse_txt_file, run_to_df_amt

from autogc_validation.database.enums import SampleTypeLetter

logger = logging.getLogger(__name__)

# Site display names used in CSV column headers.
# Format matches the MAX crosstab convention so files are readable by
# autogc_core.max.crosstab_to_df.  Verify names against the sites table.
_SITE_DISPLAY_NAMES: dict[str, str] = {
    "BV": "SITE-BV_BountifulVista",
    "HW": "SITE-HW_Hawthorne",
    "LP": "SITE-LP_LakePark",
    "EQ": "SITE-EQ_EastQuarter",
    "RB": "SITE-RB_RedButte",
    "ED": "SITE-ED_Erda",
}


def _compound_to_aqs(name: str) -> int | None:
    """Look up the AQS code for a capitalized compound name string."""
    try:
        return CompoundAQSCode[CompoundName(name).name].value
    except ValueError:
        logger.warning("No AQS code for compound: %s", name)
        return None


def write_txt_csv(df: pd.DataFrame, site: str, path: Path) -> None:
    """Write a compound-amount DataFrame to a three-row-header crosstab CSV.

    Row 0: ``{COMPOUND}({site_display}) PPBC`` — matches MAX figure format.
    Row 1: capitalized compound name (or TNMHC / TNMTC as-is).
    Row 2: AQS parameter code — used as the header by crosstab_to_df.
    """
    display = _SITE_DISPLAY_NAMES.get(site.upper(), f"SITE-{site.upper()}")
    write_df = df.replace(0, "")
    cols = df.columns.tolist()

    first_header = [""] + [f"{col.upper()}({display}) PPBC" for col in cols]
    second_header = [""] + [col if col in ("TNMHC", "TNMTC") else col.capitalize() for col in cols]
    third_header = ["DATE/TIME"] + [_compound_to_aqs(col) for col in cols]

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(first_header)
        writer.writerow(second_header)
        writer.writerow(third_header)
        for idx, row in write_df.iterrows():
            writer.writerow([idx] + row.tolist())


def process_txt_to_csv(site: str, txt_folder: Path, csv_output_folder: Path) -> None:
    """Parse all .tx1 files in *txt_folder* and write per-sample-type CSVs.

    One CSV is written for each SampleTypeLetter that has at least one run.
    Output files are named ``amount_crosstab_run_[{LETTER}].csv``.

    Args:
        site: Two-letter site code (e.g. "RB", "LP").
        txt_folder: Directory containing raw .tx1 instrument files.
        csv_output_folder: Directory to write output CSVs into.
    """
    paths = find_txt_files(Path(txt_folder))
    if not paths:
        logger.warning("No .tx1 files found in %s", txt_folder)
        return

    df = pd.concat(
        [run_to_df_amt(parse_txt_file(p)) for p in paths],
        ignore_index=False,
    )

    for letter in SampleTypeLetter:
        subset = df[df["sample_type"] == letter.value].drop("sample_type", axis=1)
        if subset.empty:
            continue
        out_path = Path(csv_output_folder) / f"amount_crosstab_run_[{letter.value.upper()}].csv"
        write_txt_csv(subset, site, out_path)
        logger.info("Wrote %s (%d runs)", out_path.name, len(subset))
