# -*- coding: utf-8 -*-
"""
MDL query operations.

Retrieve active method detection limits for a site at a given date.
"""

import logging
from typing import Dict, Optional

from autogc_validation.database.conn import connection

logger = logging.getLogger(__name__)


def get_active_mdls(
    database: str,
    site_id: int,
    date: str,
) -> Dict[int, float]:
    """Get MDLs active for a site on a specific date.

    Finds all MDL records where date_on <= date < date_off.

    Args:
        database: Path to SQLite database.
        site_id: Site identifier.
        date: Date string (YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS).

    Returns:
        Dict mapping AQS code (int) to MDL concentration (float).
    """
    sql = """
        SELECT aqs_code, concentration
        FROM mdls
        WHERE site_id = ?
          AND date_on <= ?
          AND date_off > ?
    """

    with connection(database) as conn:
        cursor = conn.execute(sql, (site_id, date, date))
        return {row["aqs_code"]: row["concentration"] for row in cursor.fetchall()}
