# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 2026

@author: aengstrom
"""
from autogc_validation.database.conn import transaction, connection
from autogc_validation.database.models.base import BaseModel
import logging

logger = logging.getLogger(__name__)


def retire_site_canister(database: str, site_canister_id: str, date_off: str) -> bool:
    """
    Set date_off and mark a site canister as no longer in use.

    Args:
        database: Path to the database file.
        site_canister_id: The canister to retire.
        date_off: Date the canister was removed (YYYY-MM-DD HH:MM:SS).

    Returns:
        True if the record was updated, False if not found.

    Raises:
        ValueError: If date_off format is invalid or date_off is before date_on.
    """
    date_off = BaseModel.validate_date_format(date_off)

    # Verify the canister exists and check date_on
    with connection(database) as conn:
        row = conn.execute(
            "SELECT date_on FROM site_canisters WHERE site_canister_id = ?",
            (site_canister_id,)
        ).fetchone()

    if row is None:
        logger.warning("Site canister not found: %s", site_canister_id)
        return False

    date_on = BaseModel.parse_date(row["date_on"])
    off = BaseModel.parse_date(date_off)
    if off <= date_on:
        raise ValueError(
            f"date_off ({date_off}) must be after date_on ({row['date_on']})"
        )

    with transaction(database) as conn:
        conn.execute(
            "UPDATE site_canisters SET date_off = ?, in_use = 0 WHERE site_canister_id = ?",
            (date_off, site_canister_id)
        )
        logger.info("Retired site canister %s on %s", site_canister_id, date_off)

    return True


def retire_mdl(database: str, site_id: int, aqs_code: int, date_on: str, date_off: str) -> bool:
    """
    Set date_off on an MDL record.

    Args:
        database: Path to the database file.
        site_id: Site identifier.
        aqs_code: Compound AQS code.
        date_on: The date_on of the MDL to update (part of the primary key).
        date_off: Date the MDL was superseded (YYYY-MM-DD HH:MM:SS).

    Returns:
        True if the record was updated, False if not found.

    Raises:
        ValueError: If date formats are invalid or date_off is before date_on.
    """
    date_on = BaseModel.validate_date_format(date_on)
    date_off = BaseModel.validate_date_format(date_off)

    on = BaseModel.parse_date(date_on)
    off = BaseModel.parse_date(date_off)
    if off <= on:
        raise ValueError(
            f"date_off ({date_off}) must be after date_on ({date_on})"
        )

    with connection(database) as conn:
        row = conn.execute(
            "SELECT 1 FROM mdls WHERE site_id = ? AND aqs_code = ? AND date_on = ?",
            (site_id, aqs_code, date_on)
        ).fetchone()

    if row is None:
        logger.warning(
            "MDL not found: site_id=%s, aqs_code=%s, date_on=%s",
            site_id, aqs_code, date_on
        )
        return False

    with transaction(database) as conn:
        conn.execute(
            "UPDATE mdls SET date_off = ? WHERE site_id = ? AND aqs_code = ? AND date_on = ?",
            (date_off, site_id, aqs_code, date_on)
        )
        logger.info(
            "Set date_off=%s for MDL (site_id=%s, aqs_code=%s, date_on=%s)",
            date_off, site_id, aqs_code, date_on
        )

    return True
