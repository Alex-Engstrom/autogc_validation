# -*- coding: utf-8 -*-
"""
Canister concentration query operations.

Retrieve active site canister concentrations (diluted) for a site,
canister type, and date.
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
