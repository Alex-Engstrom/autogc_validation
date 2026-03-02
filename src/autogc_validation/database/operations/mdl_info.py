# -*- coding: utf-8 -*-
"""
MDL query operations.

Retrieve active method detection limits for a site at a given date,
or all MDL periods within a date range.
"""

import logging

import pandas as pd

from autogc_validation.database.conn import connection
from autogc_validation.database.enums import ConcentrationUnit
from autogc_validation.conversions import convert

logger = logging.getLogger(__name__)


def get_active_mdls(
    database: str,
    site_id: int,
    date: str,
    output_unit: ConcentrationUnit,
) -> pd.DataFrame:
    """Get MDLs active for a site on a specific date as a wide DataFrame.

    Finds all MDL records where date_on <= date < date_off, converts
    values to the requested unit, and returns a single-row wide DataFrame
    with one column per AQS code.

    Args:
        database: Path to SQLite database.
        site_id: Site identifier.
        date: Date string (YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS).
        output_unit: Concentration unit for the returned values.

    Returns:
        Single-row DataFrame with AQS codes as columns and MDL
        concentrations as values. Units stored in df.attrs['units'].
    """
    sql = """
        SELECT aqs_code, concentration, units
        FROM mdls
        WHERE site_id = ?
          AND date_on <= ?
          AND (date_off IS NULL OR date_off > ?)
    """

    with connection(database) as conn:
        cursor = conn.execute(sql, (site_id, date, date))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)

    df["concentration"] = df.apply(
        lambda row: convert(
            value=row["concentration"],
            aqs_code=row["aqs_code"],
            from_unit=row["units"],
            to_unit=output_unit,
        ),
        axis=1,
    )

    wide = pd.DataFrame([df.set_index("aqs_code")["concentration"].to_dict()])
    wide.attrs["units"] = output_unit
    return wide


def get_mdl_periods(
    database: str,
    site_id: int,
    start_date: str,
    end_date: str,
    output_unit: ConcentrationUnit,
) -> pd.DataFrame:
    """Get all MDL periods within [start_date, end_date] as a date-indexed wide DataFrame.

    Finds breakpoints where the active MDL set changes — the start of the range
    plus any date_on values that fall within (start_date, end_date]. For each
    breakpoint, retrieves the MDLs active at that date.

    Args:
        database: Path to SQLite database.
        site_id: Site identifier.
        start_date: Start of date range (YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS).
        end_date: End of date range (inclusive).
        output_unit: Concentration unit for returned values.

    Returns:
        Wide DataFrame with DatetimeIndex (one row per breakpoint) and AQS codes
        as columns. Units stored in df.attrs['units'].
        If MDLs do not change within the range, returns a single-row DataFrame
        indexed by start_date.
    """
    sql = """
        SELECT DISTINCT date_on
        FROM mdls
        WHERE site_id = ?
          AND date_on > ?
          AND date_on <= ?
        ORDER BY date_on
    """
    with connection(database) as conn:
        cursor = conn.execute(sql, (site_id, start_date, end_date))
        mid_breakpoints = [row[0] for row in cursor.fetchall()]

    breakpoints = [start_date] + mid_breakpoints

    period_rows = []
    for date in breakpoints:
        row_df = get_active_mdls(database, site_id, date, output_unit)
        row_df.index = pd.DatetimeIndex([date])
        period_rows.append(row_df)

    result = pd.concat(period_rows).sort_index()
    result.attrs["units"] = output_unit
    return result
