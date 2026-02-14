# -*- coding: utf-8 -*-
"""
Sample types and CDF file pairing.

Parses AutoGC filenames to extract metadata, pairs front/back
chromatograms, and creates Sample objects for downstream analysis.
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Dict, List, Optional

from autogc_validation.io.cdf import Chromatogram

logger = logging.getLogger(__name__)


class SampleType(StrEnum):
    """Sample type codes from AutoGC filename convention."""
    AMBIENT = "s"
    BLANK = "b"
    CVS = "c"
    RTS = "q"
    LCS = "e"
    MDL_POINT = "d"
    CALIBRATION_POINT = "m"
    EXPERIMENTAL = "x"


@dataclass
class Sample:
    """A paired front/back chromatogram with metadata."""
    front: Chromatogram
    back: Chromatogram
    sample_type: SampleType
    site: str
    month: str
    day: str
    hour: str
    filename_base: str

    @property
    def datetime(self):
        """Return datetime from front chromatogram."""
        return self.front.datetime


_FILENAME_PATTERN = re.compile(
    r"(?P<site>[A-Z]{2})"
    r"(?P<sample_type>[A-Z])"
    r"(?P<month>[A-Z])"
    r"(?P<day>\d{2})"
    r"(?P<hour>[A-Z])"
    r".*-(?P<column>Front Signal|Back Signal)",
    re.IGNORECASE,
)


def parse_filename_metadata(filename: Path) -> Optional[Dict[str, str]]:
    """Parse an AutoGC CDF filename to extract run metadata.

    Expected pattern: {site}{sample_type}{month}{day}{hour}...-{column}.cdf
    Example: RBSJ01A...-Front Signal.cdf

    Returns:
        Dict with keys: site, sample_type, month, day, hour, column.
        None if the filename doesn't match the expected pattern.
    """
    match = _FILENAME_PATTERN.match(Path(filename).stem)
    if match:
        return match.groupdict()
    logger.warning("Could not parse filename: %s", filename)
    return None


def load_samples_from_folder(folder: Path) -> List[Sample]:
    """Scan a folder for CDF files and pair front/back into Sample objects.

    Groups files by unique run key (site + sample_type + month + day + hour),
    then pairs front and back signal files into Sample objects.

    Args:
        folder: Path to directory containing .cdf files.

    Returns:
        List of Sample objects with paired chromatograms.
    """
    folder = Path(folder)
    if not folder.exists():
        logger.warning("Folder does not exist: %s", folder)
        return []

    files_by_run: Dict[tuple, Dict[str, Path]] = defaultdict(dict)
    for file in folder.rglob("*.cdf"):
        info = parse_filename_metadata(file)
        if not info or not info["sample_type"]:
            continue

        run_key = (
            info["site"],
            info["sample_type"],
            info["month"],
            info["day"],
            info["hour"],
        )

        column = info["column"].lower()
        if column == "front signal":
            files_by_run[run_key]["front"] = file
        elif column == "back signal":
            files_by_run[run_key]["back"] = file

    samples = []
    for run_key, paths in files_by_run.items():
        front_path = paths.get("front")
        back_path = paths.get("back")

        if not (front_path and back_path):
            logger.warning("Missing front or back file for run %s", run_key)
            continue

        site, sample_type_char, month, day, hour = run_key
        try:
            sample_type = SampleType(sample_type_char.lower())
        except ValueError:
            logger.warning("Unknown sample type '%s' for run %s", sample_type_char, run_key)
            continue

        sample = Sample(
            front=Chromatogram(front_path),
            back=Chromatogram(back_path),
            sample_type=sample_type,
            site=site,
            month=month,
            day=day,
            hour=hour,
            filename_base=f"{site}{sample_type_char}{month}{day}{hour}",
        )
        samples.append(sample)

    return samples
