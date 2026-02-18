# -*- coding: utf-8 -*-
"""
NetCDF chromatogram file reader.

Reads .cdf files produced by AutoGC chromatographic analysis software
and extracts signal data, peak amounts, peak windows, and peak locations.
"""

import logging
from datetime import datetime
from pathlib import Path

import netCDF4 as ncdf
import numpy as np
import pandas as pd
from dateutil import parser

from autogc_validation.database.enums import (
    CompoundAQSCode,
    PLOT_UNID_CODE,
    BP_UNID_CODE,
    UNID_CODES,
    name_to_aqs,
)

logger = logging.getLogger(__name__)

# Mapping from CDF file peak name strings to synthetic UNID codes.
# This is I/O-specific: it's how the AutoGC software labels unidentified
# peaks in the NetCDF file. The codes themselves are defined in the enums package.
_UNID_NAME_MAP = {
    "Plot unid": PLOT_UNID_CODE,
    "Bp unid": BP_UNID_CODE,
}


def _map_peak_name(name: str) -> int:
    """Map a peak name string from a CDF file to an AQS code.

    Handles standard compounds via the CompoundAQSCode enum and
    unidentified peaks via the _UNID_NAME_MAP.
    """
    capitalized = name.strip().capitalize()
    if capitalized in _UNID_NAME_MAP:
        return _UNID_NAME_MAP[capitalized]
    return name_to_aqs(capitalized)


class Chromatogram:
    """Reads chromatogram data from a single .cdf (NetCDF) file."""

    def __init__(self, filename, dataformat="cdf"):
        self.format = dataformat
        self.filename = Path(filename)
        self._datetime = None
        self._chromatogram = None
        self._peakamounts = None
        self._peakwindows = None
        self._peaklocations = None

    @property
    def datetime(self):
        if self._datetime is None:
            self._datetime = self._get_datetime()
        return self._datetime

    @property
    def chromatogram(self):
        if self._chromatogram is None:
            self._chromatogram = self._generate_chrom()
        return self._chromatogram

    @property
    def peakamounts(self):
        if self._peakamounts is None:
            self._peakamounts = self._generate_class_attributes('peakamounts')
        return self._peakamounts

    @property
    def peakwindows(self):
        if self._peakwindows is None:
            self._peakwindows = self._generate_class_attributes('peakwindows')
        return self._peakwindows

    @property
    def peaklocations(self):
        if self._peaklocations is None:
            self._peaklocations = self._generate_class_attributes('peaklocations')
        return self._peaklocations

    def _get_datetime(self):
        """Extract datetime from CDF file metadata."""
        try:
            with ncdf.Dataset(self.filename, "r", format="NETCDF3_CLASSIC") as rootgrp:
                if 'dataset_date_time_stamp' in rootgrp.ncattrs():
                    date_string = rootgrp.dataset_date_time_stamp
                    return parser.parse(date_string)
                else:
                    return datetime.fromtimestamp(self.filename.stat().st_mtime)
        except Exception as e:
            logger.error("Error getting datetime from %s: %s", self.filename, e)
            return None

    def _generate_chrom(self):
        """Extract raw chromatogram signal and retention time axis."""
        try:
            with ncdf.Dataset(self.filename, "r", format="NETCDF3_CLASSIC") as rootgrp:
                required_vars = [
                    "ordinate_values",
                    "actual_run_time_length",
                    "actual_delay_time",
                    "actual_sampling_interval",
                ]
                for var in required_vars:
                    if var not in rootgrp.variables:
                        raise KeyError(f"Missing '{var}' in {self.filename}")

                signal = np.array(rootgrp.variables["ordinate_values"][:])
                runtime = float(rootgrp.variables["actual_run_time_length"][0])
                starttime = float(rootgrp.variables["actual_delay_time"][0])
                interval = float(rootgrp.variables["actual_sampling_interval"][0])
                rt = np.arange(starttime, runtime, interval)
                return np.vstack((rt, signal))
        except Exception as e:
            logger.error("Error reading chromatogram from %s: %s", self.filename, e)
            return None

    def _generate_class_attributes(self, attribute: str):
        """Extract peak data (amounts, windows, or locations) from CDF file."""
        attribute_guide = {
            'peaklocations': [
                "peak_name", "baseline_start_time", "baseline_stop_time",
                "baseline_start_value", "baseline_stop_value", "peak_retention_time",
            ],
            'peakamounts': ["peak_name", "peak_amount"],
            'peakwindows': [
                "peak_name", "peak_start_time", "peak_end_time", "peak_retention_time",
            ],
        }
        try:
            with ncdf.Dataset(self.filename, "r", format="NETCDF3_CLASSIC") as rootgrp:
                required_vars = attribute_guide[attribute]
                for var in required_vars:
                    if var not in rootgrp.variables:
                        raise KeyError(f"Missing '{var}' in {self.filename}")

                data = {
                    var: ncdf.chartostring(rootgrp.variables[var][:])
                    if var == "peak_name"
                    else rootgrp.variables[var][:]
                    for var in required_vars
                }
                df = pd.DataFrame(data)
                mask = df['peak_name'].str.len() > 0
                df = df[mask]

                df['peak_name'] = df['peak_name'].map(_map_peak_name)
                if df['peak_name'].isna().any():
                    raise ValueError(
                        f"Unmapped compounds detected in {self.filename}"
                    )

                if attribute == 'peakamounts':
                    mask = ~df['peak_name'].isin(UNID_CODES)
                    tnmtc = df[mask]['peak_amount'].sum()
                    tnmhc = df['peak_amount'].sum()
                    totals = pd.DataFrame({
                        "peak_name": [
                            CompoundAQSCode.C_TNMHC,
                            CompoundAQSCode.C_TNMTC,
                        ],
                        "peak_amount": [tnmhc, tnmtc],
                    })
                    df = pd.concat([df, totals], ignore_index=True)
                    df = df.astype({'peak_name': int})

                return df

        except Exception as e:
            logger.error("Error reading %s from %s: %s", attribute, self.filename, e)
            return None

    def list_netcdf_variables(self):
        """List all variables in the NetCDF file."""
        with ncdf.Dataset(self.filename, "r", format="NETCDF3_CLASSIC") as rootgrp:
            return rootgrp.variables.keys()

    def list_netcdf_attributes(self):
        """List all global attributes in the NetCDF file."""
        with ncdf.Dataset(self.filename, "r", format="NETCDF3_CLASSIC") as rootgrp:
            return rootgrp.__dict__

    def examine_netcdf_variable(self, variable):
        """Return the data and metadata for a specific NetCDF variable."""
        with ncdf.Dataset(self.filename, "r", format="NETCDF3_CLASSIC") as rootgrp:
            return rootgrp.variables[variable][:], rootgrp.variables[variable].__dict__

    def examine_netcdf_attribute(self, attribute):
        """Return the value of a specific NetCDF global attribute."""
        with ncdf.Dataset(self.filename, "r", format="NETCDF3_CLASSIC") as rootgrp:
            return getattr(rootgrp, attribute)

    def __repr__(self):
        return f"Chromatogram({self.filename.name})"
