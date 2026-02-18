# -*- coding: utf-8 -*-
"""
Canister concentration query operations.

Retrieve active site canister concentrations (diluted) for a site,
canister type, and date.
"""

import logging
from typing import Dict, Optional

from autogc_validation.database.conn import connection

logger = logging.getLogger(__name__)


def get_active_canister_concentrations(
    database: str,
    site_id: int,
    canister_type: str,
    date: str,
) -> Dict[int, float]:
    """Get diluted canister concentrations active for a site on a specific date.

    Joins site_canisters to primary_canister_concentration and applies
    the dilution ratio to get effective concentrations.

    Args:
        database: Path to SQLite database.
        site_id: Site identifier.
        canister_type: Canister type ('CVS', 'RTS', or 'LCS').
        date: Date string (YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS).

    Returns:
        Dict mapping AQS code (int) to diluted concentration (float).
    """
    sql = """
        SELECT pc.aqs_code, pc.concentration * sc.dilution_ratio AS concentration
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
        return {row["aqs_code"]: row["concentration"] for row in cursor.fetchall()}
