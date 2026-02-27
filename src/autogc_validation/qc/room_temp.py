# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 11:24:42 2026

@author: aengstrom
"""
import calendar
from typing import NamedTuple

import pandas as pd

from autogc_validation.database.airvision.station_temp import query_av_rtemp


class StationTempResult(NamedTuple):
    temperatures: pd.Series  # full monthly temperature series
    flagged: pd.Series        # values outside acceptable thresholds


def check_station_temp(
    station_name: str,
    month: int,
    year: int,
    upper_threshold: float = 25,
    lower_threshold: float = 16,
) -> StationTempResult:
    _, num_days = calendar.monthrange(year, month)
    start_date = pd.Timestamp(year=year, month=month, day=1)
    end_date = pd.Timestamp(year=year, month=month, day=num_days, hour=23, minute=59, second=59)
    temperatures = query_av_rtemp(start_date=start_date, end_date=end_date, site=station_name)
    mask = (temperatures > upper_threshold) | (temperatures < lower_threshold)
    return StationTempResult(temperatures=temperatures, flagged=temperatures[mask])
