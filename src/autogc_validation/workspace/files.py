# -*- coding: utf-8 -*-
"""
File operations for workspace management.

Provides functions for unzipping, moving, sorting, renaming, and
converting data files as part of the monthly validation workflow.
"""

import calendar
import logging
import os
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Union

from autogc_validation.workspace.parsing import assert_local_drive, parse_dat_file

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Unzip
# ---------------------------------------------------------------------------

def unzip_files(
    source_directory: Union[str, Path],
    destination_directory: Union[str, Path],
    delete_zip_after_extract: bool = False,
    create_subfolders: bool = True,
    allow_network_drive: bool = False,
) -> list[Path]:
    """Unzip all .zip files from source to destination, preserving modification dates.

    Args:
        source_directory: Directory containing .zip files.
        destination_directory: Directory for extracted contents.
        delete_zip_after_extract: Delete zip files after successful extraction.
        create_subfolders: Create a subfolder per zip file (named after the zip).
        allow_network_drive: Allow operation on network drives.

    Returns:
        List of successfully extracted zip file paths.
    """
    src = Path(source_directory)
    dest = Path(destination_directory)

    for path in [src, dest]:
        assert_local_drive(path, allow_network_drive)

    if not src.exists():
        raise FileNotFoundError(f"Source directory does not exist: {src}")
    if not src.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {src}")

    dest.mkdir(parents=True, exist_ok=True)

    if not os.access(dest, os.W_OK):
        raise PermissionError(f"Destination directory not writable: {dest}")

    zip_files = list(src.glob("*.zip"))
    if not zip_files:
        logger.info("No zip files found in %s", src)
        return []

    logger.info("Found %d zip file(s) in %s", len(zip_files), src)

    successfully_extracted: list[Path] = []

    for zip_file in zip_files:
        try:
            logger.info("Processing: %s", zip_file.name)

            extract_path = (
                dest / zip_file.stem if create_subfolders else dest
            )
            extract_path.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                logger.info("Found %d file(s) in zip", len(file_list))

                for file_info in zip_ref.infolist():
                    zip_ref.extract(file_info, extract_path)
                    extracted_path = extract_path / file_info.filename

                    if not file_info.is_dir():
                        timestamp = datetime(*file_info.date_time).timestamp()
                        os.utime(extracted_path, (timestamp, timestamp))

                logger.info("Extracted %d file(s) from %s", len(file_list), zip_file.name)

            successfully_extracted.append(zip_file)

            if delete_zip_after_extract:
                zip_file.unlink()
                logger.info("Deleted zip file: %s", zip_file.name)

        except zipfile.BadZipFile:
            logger.exception("%s is not a valid zip file", zip_file.name)
        except PermissionError:
            logger.exception("Permission denied processing %s", zip_file.name)
        except Exception:
            logger.exception("Error processing %s", zip_file.name)

    logger.info(
        "Unzip complete: %d/%d extracted successfully",
        len(successfully_extracted), len(zip_files),
    )
    return successfully_extracted


# ---------------------------------------------------------------------------
# Move / copy files
# ---------------------------------------------------------------------------

def move_files_by_extension(
    source_directory: Union[str, Path],
    destination_directory: Union[str, Path],
    ext: str,
    dump_folder_name: str,
    allow_network_drive: bool = False,
) -> Tuple[Path, dict]:
    """Copy files of a given extension from source to destination.

    Duplicates (by stem) are placed in a 'copies' subfolder.

    Args:
        source_directory: Directory to search recursively.
        destination_directory: Parent directory for the output folder.
        ext: File extension to match (e.g. ".dat", ".tx1").
        dump_folder_name: Name of the subfolder to create in destination.
        allow_network_drive: Allow operation on network drives.

    Returns:
        Tuple of (output_folder_path, summary_dict).
        Summary dict has keys: found, copied, duplicates, errors —
        each mapping to (count, list_of_filenames).
    """
    src = Path(source_directory).resolve()
    dest = Path(destination_directory).resolve()

    for path in [src, dest]:
        assert_local_drive(path, allow_network_drive)

    if dest in src.parents or dest == src:
        raise RuntimeError("Destination folder cannot be inside the source folder")

    output_folder = dest / dump_folder_name
    copies_folder = output_folder / "copies"
    output_folder.mkdir(mode=0o755, exist_ok=True)
    copies_folder.mkdir(mode=0o755, exist_ok=True)

    file_paths = [p for p in src.rglob("*") if p.suffix.lower() == ext.lower()]
    logger.info("Found %d %s files under %s", len(file_paths), ext, src)

    existing_stems = {
        f.stem.lower().strip() for f in output_folder.iterdir() if f.is_file()
    }

    copied, duplicates, errors = 0, 0, 0
    copied_lst, duplicates_lst, errors_lst = [], [], []

    for path in file_paths:
        try:
            dest_path = output_folder / path.name
            if path.resolve() == dest_path.resolve():
                continue

            stem = path.stem.lower().strip()
            if stem not in existing_stems:
                shutil.copy2(path, output_folder)
                existing_stems.add(stem)
                copied += 1
                copied_lst.append(path.name)
            else:
                shutil.copy2(path, copies_folder)
                duplicates += 1
                duplicates_lst.append(path.name)
                logger.info("Duplicate: %s -> copies/", path.name)
        except Exception:
            logger.exception("Error copying %s", path.name)
            errors += 1
            errors_lst.append(path.name)

    summary = {
        "found": (len(file_paths), [p.name for p in file_paths]),
        "copied": (copied, copied_lst),
        "duplicates": (duplicates, duplicates_lst),
        "errors": (errors, errors_lst),
    }

    logger.info(
        "%s copy complete: %d found, %d copied, %d duplicates, %d errors",
        ext, len(file_paths), copied, duplicates, errors,
    )
    return output_folder, summary


def move_dat_files(
    src: Union[str, Path], dest: Union[str, Path],
) -> Tuple[Path, dict]:
    """Copy .dat files from source to destination."""
    return move_files_by_extension(src, dest, ".dat", "original_dat_files")


def move_tx1_files(
    src: Union[str, Path], dest: Union[str, Path],
) -> Tuple[Path, dict]:
    """Copy .tx1 files from source to destination."""
    return move_files_by_extension(src, dest, ".tx1", "original_tx1_files")


def move_files_by_week(
    dat_folder: Union[str, Path],
    destination_directory: Union[str, Path],
    month: int,
    year: int,
) -> dict[str, int]:
    """Sort .dat files into week folders based on the day in the filename.

    Week boundaries: 1-7, 8-14, 15-21, 22-end of month.

    Args:
        dat_folder: Directory containing .dat files.
        destination_directory: Parent directory for week folders.
        month: Month number (1-12).
        year: Year (for determining days in month).

    Returns:
        Dict mapping week name to number of files placed.
    """
    _, days_in_month = calendar.monthrange(year, month)
    week_ranges = {
        "week 1": range(1, 8),
        "week 2": range(8, 15),
        "week 3": range(15, 22),
        "week 4": range(22, days_in_month + 1),
    }
    week_counts = {name: 0 for name in week_ranges}

    dat_folder = Path(dat_folder)
    destination_directory = Path(destination_directory)

    week_paths = {}
    for week_name in week_ranges:
        path = destination_directory / week_name
        path.mkdir(parents=True, exist_ok=True)
        week_paths[week_name] = path

    for file in dat_folder.iterdir():
        if not file.is_file():
            continue

        result = parse_dat_file(file)
        if not result:
            continue

        parsed, _ = result

        try:
            file_day = int(parsed['day'])
        except ValueError:
            logger.warning("Invalid day '%s' in file %s", parsed['day'], file.name)
            continue

        placed = False
        for week_name, day_range in week_ranges.items():
            if file_day in day_range:
                shutil.copy2(str(file), str(week_paths[week_name] / file.name))
                week_counts[week_name] += 1
                placed = True
                break

        if not placed:
            logger.warning("Day %d from %s is out of range", file_day, file.name)

    logger.info("Files sorted by week: %s", week_counts)
    return week_counts


# ---------------------------------------------------------------------------
# Rename
# ---------------------------------------------------------------------------

def rename_dattxt_files_to_txt(
    source_directory: Union[str, Path],
    destination_directory: Union[str, Path] = None,
) -> int:
    """Rename .dat.tx1 files to .tx1, optionally moving to a destination.

    Args:
        source_directory: Directory containing .dat.tx1 files.
        destination_directory: Where renamed files go (defaults to source).

    Returns:
        Number of files renamed.
    """
    src = Path(source_directory)
    dest = Path(destination_directory) if destination_directory else src

    dest.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        logger.warning("Source directory does not exist: %s", src)
        return 0

    counter = 0
    overwritten = 0

    for filename in src.iterdir():
        if filename.is_dir() or not filename.name.endswith(".dat.tx1"):
            continue

        newname = filename.name.replace(".dat", "", 1)
        dest_path = dest / newname

        if dest_path.exists():
            logger.info("Overwriting existing file: %s", dest_path.name)
            dest_path.unlink(missing_ok=True)
            overwritten += 1

        try:
            filename.rename(dest_path)
            counter += 1
        except OSError:
            shutil.move(str(filename), str(dest_path))
            counter += 1

    logger.info(
        "Renamed %d .dat.tx1 files (%d overwritten) -> %s",
        counter, overwritten, dest,
    )
    return counter


# ---------------------------------------------------------------------------
# PDF conversion
# ---------------------------------------------------------------------------

_DEFAULT_SOFFICE = Path(r"C:\Program Files\LibreOffice\program\soffice.exe")


def convert_file_to_pdf(
    source_path: Union[str, Path],
    destination_path: Union[str, Path],
    soffice_path: Union[str, Path] = _DEFAULT_SOFFICE,
    allow_network_drive: bool = False,
) -> Path:
    """Convert a DOCX, XLSX, or XLSM file to PDF using LibreOffice.

    Skips conversion if the destination PDF already exists.

    Args:
        source_path: Path to the source file.
        destination_path: Desired path for the output PDF.
        soffice_path: Path to the LibreOffice soffice executable.
        allow_network_drive: Allow operation on network drives.

    Returns:
        Path to the output PDF.
    """
    src = Path(source_path).resolve()
    dest = Path(destination_path).resolve()
    soffice = Path(soffice_path)

    for path in [src, dest]:
        assert_local_drive(path, allow_network_drive)

    if not src.exists():
        raise FileNotFoundError(f"Source file does not exist: {src}")
    if not soffice.exists():
        raise FileNotFoundError(f"LibreOffice not found: {soffice}")

    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        logger.info("PDF already exists, skipping: %s", dest.name)
        return dest

    try:
        subprocess.run(
            [str(soffice), "--headless", "--convert-to", "pdf",
             "--outdir", str(dest.parent), str(src)],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to convert {src} to PDF: {e.stderr}")

    temp_pdf = dest.parent / f"{src.stem}.pdf"
    if not temp_pdf.exists():
        raise RuntimeError(f"Converted PDF not found: {temp_pdf}")

    if not dest.exists():
        temp_pdf.rename(dest)
    else:
        temp_pdf.unlink()

    logger.info("Converted %s -> %s", src.name, dest.name)
    return dest


def convert_folder_contents_to_pdf(
    source_directory: Union[str, Path],
    destination_directory: Union[str, Path],
    copy_original: bool = True,
    soffice_path: Union[str, Path] = _DEFAULT_SOFFICE,
    allow_network_drive: bool = False,
) -> list[Path]:
    """Batch-convert DOCX/XLSX/XLSM files to PDF.

    Output filenames include the source file's modification timestamp
    to distinguish versions.

    Args:
        source_directory: Directory to search recursively.
        destination_directory: Directory for output PDFs.
        copy_original: Also copy the original file alongside the PDF.
        soffice_path: Path to LibreOffice soffice executable.
        allow_network_drive: Allow operation on network drives.

    Returns:
        List of converted PDF paths.
    """
    src = Path(source_directory).resolve()
    dest = Path(destination_directory).resolve()

    for path in [src, dest]:
        assert_local_drive(path, allow_network_drive)

    if not src.exists() or not src.is_dir():
        raise NotADirectoryError(f"Source folder invalid: {src}")

    dest.mkdir(parents=True, exist_ok=True)

    convertible = []
    for ext in ("*.docx", "*.xlsx", "*.xlsm"):
        convertible.extend(src.rglob(ext))

    converted = []
    for file in convertible:
        try:
            ts = datetime.fromtimestamp(file.stat().st_mtime).strftime(
                "%Y-%m-%d-%H-%M-%S"
            )
            pdf_path = dest / f"{file.stem} modified {ts}.pdf"

            result = convert_file_to_pdf(
                file, pdf_path, soffice_path=soffice_path,
                allow_network_drive=allow_network_drive,
            )
            if result:
                converted.append(result)

            if copy_original:
                original_copy = dest / f"{file.stem} modified {ts}{file.suffix}"
                if not original_copy.exists():
                    shutil.copy2(file, original_copy)

        except Exception:
            logger.exception("Failed processing file: %s", file)

    logger.info("Converted %d/%d files to PDF", len(converted), len(convertible))
    return converted
