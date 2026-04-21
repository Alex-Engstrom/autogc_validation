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
from pathlib import Path
from typing import Dict, List, Optional

from autogc_validation.database.enums import SampleTypeLetter, SampleTypeLong
from autogc_validation.io.cdf import Chromatogram

logger = logging.getLogger(__name__)


@dataclass
class Sample:
    """A paired front/back chromatogram with metadata."""
    front: Chromatogram
    back: Chromatogram
    sample_type_letter: SampleTypeLetter
    site: str
    month: str
    day: str
    hour: str
    filename_base: str

    @property
    def datetime(self):
        """Return datetime from front chromatogram."""
        return self.front.datetime

    @property
    def sample_type_long(self) -> SampleTypeLong | None:
        """Long-form sample type read from the CDF ``sample_id`` attribute.

        Reads from the front chromatogram lazily (opens the file on first
        access). Returns None and logs a warning if the value is not
        a recognised ``SampleTypeLong`` member.

        If the front and back chromatograms report different ``sample_id``
        values a warning is logged and the front value is used.
        """
        front_raw = self.front.sampletype
        back_raw  = self.back.sampletype
        if front_raw != back_raw:
            logger.warning(
                "%s: front/back sample_id mismatch (%r vs %r) — using front",
                self.filename_base, front_raw, back_raw,
            )
        try:
            return SampleTypeLong(front_raw)
        except ValueError:
            logger.warning(
                "%s: unrecognised sample_id %r", self.filename_base, front_raw
            )
            return None

    @property
    def filename_hour(self) -> int | None:
        """Integer hour (0-23) encoded in the filename letter (a=0 … x=23).

        Returns None if the letter is outside the expected a-x range.
        Note: this is the hour that was programmed into the GC sequence before
        the run, which may not match the actual injection time if the sequence
        was configured incorrectly. Use check_filename_hour_alignment() to
        compare against the injection-derived sample hour.
        """
        val = ord(self.hour.lower()) - ord("a")
        return val if 0 <= val <= 23 else None


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

    Expected pattern: {site}{sample_type_letter}{month}{day}{hour}...-{column}.cdf
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
            sample_type_letter = SampleTypeLetter(sample_type_char.lower())
        except ValueError:
            logger.warning("Unknown sample type '%s' for run %s", sample_type_char, run_key)
            continue

        sample = Sample(
            front=Chromatogram(front_path),
            back=Chromatogram(back_path),
            sample_type_letter=sample_type_letter,
            site=site,
            month=month,
            day=day,
            hour=hour,
            filename_base=f"{site}{sample_type_char}{month}{day}{hour}",
        )
        # sample_type_long is a lazy property — not set at construction time.
        samples.append(sample)

    return samples


