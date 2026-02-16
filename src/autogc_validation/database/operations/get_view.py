# -*- coding: utf-8 -*-
"""
Created on Fri Feb 13 19:48:23 2026

@author: aengstrom
"""
import logging

import pandas as pd

from autogc_validation.database.conn import connection

logger = logging.getLogger(__name__)


def get_site_canister_concentrations(database: str, site_canister_id: str) -> pd.DataFrame:
    sql = """
        SELECT SC.site_canister_id,
               CC.concentration * SC.dilution_ratio AS adjusted_concentration
        FROM site_canisters AS SC
        JOIN primary_canister_concentration AS CC
            ON SC.primary_canister_id = CC.primary_canister_id
        WHERE SC.site_canister_id = ?
    """
    logger.debug("Querying concentrations for site canister %s", site_canister_id)
    with connection(database) as conn:
        return pd.read_sql_query(sql, conn, params=[site_canister_id])
    