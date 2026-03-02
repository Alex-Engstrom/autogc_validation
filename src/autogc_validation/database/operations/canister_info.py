# -*- coding: utf-8 -*-
"""
Canister concentration query operations.

Retrieve active site canister concentrations (diluted) for a site,
canister type, and date, or all periods within a date range.
"""

import logging
import pandas as pd
from typing import Dict

from autogc_validation.database.conn import connection
from autogc_validation.database.enums import ConcentrationUnit
from autogc_validation.conversions import convert 

logger = logging.getLogger(__name__)


def get_active_canister_concentrations(
    database: str,
    site_id: int,
    canister_type: str,
    date: str,
    output_unit: ConcentrationUnit,
) -> pd.DataFrame:
    """Get diluted canister concentrations active for a site on a specific date.

    Joins site_canisters to primary_canister_concentration and applies
    the dilution ratio to get effective concentrations, then converts to
    the requested unit.

    Args:
        database: Path to SQLite database.
        site_id: Site identifier.
        canister_type: Canister type ('CVS', 'RTS', or 'LCS').
        date: Date string (YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS).
        output_unit: Concentration unit for the returned values.

    Returns:
        Single-row DataFrame with AQS codes as columns and diluted
        concentrations as values. Units stored in df.attrs['units'].
    """
    sql = """
        SELECT pc.aqs_code, pc.concentration * sc.dilution_ratio AS concentration, pc.units
        FROM site_canisters sc
        JOIN primary_canisters p
          ON sc.primary_canister_id = p.primary_canister_id
        JOIN primary_canister_concentration pc
          ON sc.primary_canister_id = pc.primary_canister_id
        WHERE sc.site_id = ?
          AND p.canister_type = ?
          AND sc.date_on <= ?
          AND (sc.date_off IS NULL OR sc.date_off > ?)
    """

    with connection(database) as conn:
        cursor = conn.execute(sql, (site_id, canister_type, date, date))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)

    if df.empty:
        wide = pd.DataFrame()
        wide.attrs["units"] = output_unit
        return wide

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


def get_canister_periods(
    database: str,
    site_id: int,
    canister_type: str,
    start_date: str,
    end_date: str,
    output_unit: ConcentrationUnit,
) -> pd.DataFrame:
    """Get all canister concentration periods within [start_date, end_date].

    Finds breakpoints where the active site canister changes — the start of
    the range plus any date_on values in site_canisters that fall within
    (start_date, end_date]. For each breakpoint, retrieves the diluted
    concentrations active at that date.

    Args:
        database: Path to SQLite database.
        site_id: Site identifier.
        canister_type: Canister type ('CVS', 'RTS', or 'LCS').
        start_date: Start of date range (YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS).
        end_date: End of date range (inclusive).
        output_unit: Concentration unit for returned values.

    Returns:
        Wide DataFrame with DatetimeIndex (one row per breakpoint) and AQS codes
        as columns. Units stored in df.attrs['units'].
        If the canister does not change within the range, returns a single-row
        DataFrame indexed by start_date.
    """
    sql = """
        SELECT DISTINCT sc.date_on
        FROM site_canisters sc
        JOIN primary_canisters p
          ON sc.primary_canister_id = p.primary_canister_id
        WHERE sc.site_id = ?
          AND p.canister_type = ?
          AND sc.date_on > ?
          AND sc.date_on <= ?
        ORDER BY sc.date_on
    """
    with connection(database) as conn:
        cursor = conn.execute(sql, (site_id, canister_type, start_date, end_date))
        mid_breakpoints = [row[0] for row in cursor.fetchall()]

    breakpoints = [start_date] + mid_breakpoints

    period_rows = []
    for date in breakpoints:
        row_df = get_active_canister_concentrations(
            database, site_id, canister_type, date, output_unit
        )
        row_df.index = pd.DatetimeIndex([date])
        period_rows.append(row_df)

    result = pd.concat(period_rows).sort_index()
    result.attrs["units"] = output_unit
    return result
