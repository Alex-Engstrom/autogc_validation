# -*- coding: utf-8 -*-
"""
MDL query operations.

Retrieve active method detection limits for a site at a given date.
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
