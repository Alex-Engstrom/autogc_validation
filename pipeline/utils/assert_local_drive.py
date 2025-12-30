# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 15:25:03 2025

@author: aengstrom
"""
from pathlib import Path
import os
import sys
import ctypes
from typing import Union
import logging

logger = logging.getLogger(__name__)

class NetworkDriveError(OSError):
    """Raised when operation is refused because the path is on a network drive."""
    pass

def _get_windows_drive_root(path: Path) -> str:
    """
    Return a Windows root suitable for GetDriveTypeW: e.g. 'C:\\' or '\\\\server\\share\\'.
    Raises ValueError if a drive/root cannot be determined.
    """
    # Resolve to absolute to handle relative paths and symlinks
    p = path if path.is_absolute() else path.resolve()
    # Path.drive returns 'C:' or '\\\\server\\share' for UNC
    drive = p.drive
    if not drive:
        raise ValueError(f"Could not determine drive for path: {path!s}")
    # ensure trailing backslash
    root = drive if drive.endswith("\\") else drive + "\\"
    return root

def is_network_drive(path: Union[str, os.PathLike, Path]) -> bool:
    """
    Return True if `path` is located on a network drive (DRIVE_REMOTE).
    This function only works on Windows; on other platforms it returns False.
    """
    # Non-windows: no mapped-drive concept — treat as not a network drive
    if sys.platform != "win32":
        return False

    path = Path(path)
    try:
        root = _get_windows_drive_root(path)
    except ValueError:
        # If we cannot determine a drive, assume not network (or choose to raise)
        return False

    # DRIVE_REMOTE == 4
    DRIVE_REMOTE = 4
    try:
        drive_type = ctypes.windll.kernel32.GetDriveTypeW(str(root))
    except AttributeError as exc:
        # kernel32 not available for some reason
        raise RuntimeError("Windows API not available to determine drive type") from exc

    return int(drive_type) == DRIVE_REMOTE

def assert_local_drive(path: Union[str, os.PathLike, Path], allow_network_drive: bool = False) -> None:
    """
    Raise NetworkDriveError if `path` is on a network drive and that is not allowed.
    On non-Windows systems this is a no-op (because drive letters don't apply).
    """
    if not allow_network_drive and is_network_drive(path):
        raise NetworkDriveError(f"Operation aborted: {path} is a network drive")