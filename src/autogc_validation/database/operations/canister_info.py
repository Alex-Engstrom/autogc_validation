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

    output_unit = ConcentrationUnit(str(output_unit).lower())

    with connection(database) as conn:
        cursor = conn.execute(sql, (site_id, canister_type, date, date))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)

    if df.empty:
        logger.warning(
            "No canister concentrations found for type=%s on %s", canister_type, date
        )
        wide = pd.DataFrame([{}])
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

def get_primary_canister_concentrations(
    database: str,
    canister_id: int,
    output_unit: ConcentrationUnit,
) -> pd.DataFrame:
    """Get concentrations for all compounds in a primary canister.

    Args:
        database: Path to SQLite database.
        canister_id: Primary canister ID.
        output_unit: Concentration unit for the returned values.

    Returns:
        Wide single-row DataFrame with AQS codes as columns and concentrations
        as values. Units stored in df.attrs['units'].
    """
    sql = """
        SELECT aqs_code, concentration, units
        FROM primary_canister_concentration
        WHERE primary_canister_id = ?
    """
    output_unit = ConcentrationUnit(str(output_unit).lower())

    with connection(database) as conn:
        cursor = conn.execute(sql, (canister_id,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)

    if df.empty:
        logger.warning("No concentrations found for primary_canister_id=%s", canister_id)
        wide = pd.DataFrame([{}])
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
    include_install_info: bool = False,
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
        include_install_info: If True, the first row is indexed by the actual date_on
            of the canister active at start_date (rather than start_date itself), and
            'primary_canister_id' and 'dilution_ratio' columns are added to the
            returned DataFrame. Defaults to False.

    Returns:
        Wide DataFrame with DatetimeIndex (one row per breakpoint) and AQS codes
        as columns. Units stored in df.attrs['units'].
        If the canister does not change within the range, returns a single-row
        DataFrame indexed by start_date (or the install date if include_install_info=True).
    """
    sql = """
        SELECT sc.date_on
        FROM site_canisters sc
        JOIN primary_canisters p
          ON sc.primary_canister_id = p.primary_canister_id
        WHERE sc.site_id = ?
          AND p.canister_type = ?
          AND sc.date_on > ?
          AND sc.date_on <= ?
        ORDER BY sc.date_on
    """
    sql_with_info = """
        SELECT sc.date_on, sc.primary_canister_id, sc.dilution_ratio
        FROM site_canisters sc
        JOIN primary_canisters p
          ON sc.primary_canister_id = p.primary_canister_id
        WHERE sc.site_id = ?
          AND p.canister_type = ?
          AND sc.date_on > ?
          AND sc.date_on <= ?
        ORDER BY sc.date_on
    """
    install_date_sql = """
        SELECT sc.date_on, sc.primary_canister_id, sc.dilution_ratio
        FROM site_canisters sc
        JOIN primary_canisters p
          ON sc.primary_canister_id = p.primary_canister_id
        WHERE sc.site_id = ?
          AND p.canister_type = ?
          AND sc.date_on <= ?
          AND (sc.date_off IS NULL OR sc.date_off > ?)
        ORDER BY sc.date_on DESC
        LIMIT 1
    """
    output_unit = ConcentrationUnit(str(output_unit).lower())

    with connection(database) as conn:
        if include_install_info:
            cursor = conn.execute(sql_with_info, (site_id, canister_type, start_date, end_date))
            mid_data = cursor.fetchall()
            mid_breakpoints = [row[0] for row in mid_data]
            cursor = conn.execute(install_date_sql, (site_id, canister_type, start_date, start_date))
            first_row = cursor.fetchone()
            first_index = first_row[0] if first_row else start_date
            first_canister_id = first_row[1] if first_row else None
            first_dilution_ratio = first_row[2] if first_row else None
        else:
            cursor = conn.execute(sql, (site_id, canister_type, start_date, end_date))
            mid_breakpoints = [row[0] for row in cursor.fetchall()]
            first_index = start_date

    breakpoints = [start_date] + mid_breakpoints

    period_rows = []
    for i, date in enumerate(breakpoints):
        row_df = get_active_canister_concentrations(
            database, site_id, canister_type, date, output_unit
        )
        index_date = first_index if i == 0 else date
        row_df.index = pd.DatetimeIndex([index_date])
        period_rows.append(row_df)

    result = pd.concat(period_rows).sort_index()
    result.attrs["units"] = output_unit

    if include_install_info:
        install_info = {
            pd.Timestamp(first_index): (first_canister_id, first_dilution_ratio),
            **{pd.Timestamp(date): (cid, ratio) for date, cid, ratio in mid_data},
        }
        result.insert(0, "dilution_ratio", result.index.map(lambda d: install_info[d][1]))
        result.insert(0, "primary_canister_id", result.index.map(lambda d: install_info[d][0]))

    return result
