# -*- coding: utf-8 -*-
"""
Filename parsing utilities for AutoGC data files.

Provides functions for parsing AutoGC .dat filenames, converting
between the letter-based encoding used in filenames and numeric
values, and checking file modification dates.
"""

import logging
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from autogc_validation.database.enums import SampleType

logger = logging.getLogger(__name__)


# --- Network drive safety ---

def is_network_drive(path: os.PathLike) -> bool:
    """Check if a path resides on a network drive (Windows only).

    Returns False on non-Windows platforms where drive letters do not exist.
    """
    if sys.platform != "win32":
        return False
    import ctypes
    drive = os.path.splitdrive(os.path.abspath(path))[0] + "\\"
    DRIVE_REMOTE = 4
    return ctypes.windll.kernel32.GetDriveTypeW(drive) == DRIVE_REMOTE


def assert_local_drive(path: os.PathLike, allow_network: bool) -> None:
    """Raise RuntimeError if path is on a network drive and not allowed."""
    if not allow_network and is_network_drive(path):
        raise RuntimeError(f"Operation aborted: {path} is a network drive")


# --- Letter/number encoding ---

def letter_to_number(letter: str) -> Optional[int]:
    """Convert an AutoGC filename letter (a-x) to an integer (0-23).

    Args:
        letter: Single character a-x (case insensitive).

    Returns:
        Integer 0-23, or None if invalid.
    """
    if len(letter) != 1 or letter.lower() not in "abcdefghijklmnopqrstuvwx":
        logger.warning("Invalid letter '%s': must be a single character a-x", letter)
        return None
    return ord(letter.lower()) - ord('a')


def number_to_letter(number: int) -> Optional[str]:
    """Convert an integer (0-23) to an AutoGC filename letter (a-x).

    Args:
        number: Integer 0-23.

    Returns:
        Lowercase letter a-x, or None if out of range.
    """
    if number not in range(24):
        logger.warning("Invalid number %s: must be 0-23", number)
        return None
    return chr(ord('a') + number)


# --- File date checking ---

def check_mod_date(filename: os.PathLike) -> Optional[datetime]:
    """Get the modification datetime of a file in UTC-7.

    Args:
        filename: Path to file.

    Returns:
        Datetime with UTC-7 timezone, or None if file doesn't exist.
    """
    if not os.path.exists(filename):
        logger.warning("%s does not exist", filename)
        return None
    timestamp = os.path.getmtime(filename)
    return datetime.fromtimestamp(timestamp, tz=timezone(timedelta(hours=-7)))


# --- .dat filename parsing ---

_DAT_PATTERN = re.compile(
    r"(?P<site>[a-zA-Z]{2})"
    r"(?P<sample_type>[a-zA-Z])"
    r"(?P<month>[a-zA-Z])"
    r"(?P<day>\d{2})"
    r"(?P<hour>[a-zA-Z])"
    r"\.dat",
    re.IGNORECASE,
)


def parse_dat_file(
    filename: os.PathLike,
) -> Optional[Tuple[dict, Optional[Path]]]:
    """Parse a .dat filename and cross-check against its modification date.

    The AutoGC naming convention encodes site, sample type, month, day,
    and hour into the filename. This function parses those fields and
    validates them against the file's modification timestamp.

    Args:
        filename: Path to a .dat file.

    Returns:
        Tuple of (parsed_fields_dict, mismatched_path_or_None).
        None if the file cannot be parsed.
    """
    filename = Path(filename)

    if not filename.is_file():
        logger.info("%s is not a file, skipping", filename.name)
        return None

    match = _DAT_PATTERN.match(filename.name)
    if not match:
        logger.error("Could not parse .dat filename: %s", filename.name)
        return None

    from_filename = match.groupdict()

    # Get date from modification time, subtract 1 hour since .dat is
    # written in the hour after data collection
    mod_date = check_mod_date(filename)
    if mod_date is None:
        logger.error("Could not get modification date for %s", filename.name)
        return None

    mod_date = mod_date - timedelta(hours=1)

    mod_date_vals = [mod_date.month, mod_date.day, mod_date.hour]
    filename_vals = [
        letter_to_number(from_filename['month']) + 1,
        int(from_filename['day']),
        letter_to_number(from_filename['hour']),
    ]

    keys = ['month', 'day', 'hour']
    for key, mod_val, file_val in zip(keys, mod_date_vals, filename_vals):
        if mod_val != file_val:
            logger.warning(
                "%s mismatch between filename and modified date: %s",
                key, filename,
            )
            return from_filename, filename

    return from_filename, None


def list_by_sample_type(
    input_directory: os.PathLike,
    sample_type: SampleType,
    year: int,
    output_dir: Optional[os.PathLike] = None,
) -> list[Path]:
    """List .dat files matching a sample type and export to CSV.

    Args:
        input_directory: Directory containing .dat files.
        sample_type: SampleType enum value to filter by.
        year: Year for date formatting.
        output_dir: Directory for the CSV output. Defaults to input_directory.

    Returns:
        List of paths with filename/modification date mismatches.
    """
    rows = []
    mismatched_list = []
    input_directory = Path(input_directory)
    output_dir = Path(output_dir) if output_dir is not None else input_directory

    for file in input_directory.iterdir():
        result = parse_dat_file(file)
        if result is None:
            continue

        from_filename, mismatched = result
        if mismatched:
            mismatched_list.append(mismatched)

        if from_filename['sample_type'].lower() == sample_type.value:
            month = letter_to_number(from_filename['month']) + 1
            day = int(from_filename['day'])
            hour_int = letter_to_number(from_filename['hour'])
            rows.append({
                'date': f"{month:02d}/{day:02d}/{year:02d}",
                'hour': f"{hour_int:02d}:00",
                'filename': file.stem,
            })

    df = pd.DataFrame(rows)
    csv_path = output_dir / f"{sample_type.value}.csv"
    df.to_csv(csv_path, header=True, index=False)
    logger.info("Wrote %d rows to %s", len(df), csv_path)
    return mismatched_list
