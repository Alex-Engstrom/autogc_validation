# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:05:34 2026

@author: aengstrom
"""
from dataclasses import astuple
from typing import List
from ..connection.manager import get_connection, transaction
from ..models.canister import PrimaryCanister, CanisterConcentration, SiteCanister

def insert_canister(database: str, canister: PrimaryCanister) -> None:
    sql = "INSERT OR IGNORE INTO primary_canisters (primary_canister_id, canister_type, certification_date, expiration_date) VALUES (?,?,?,?)"
    canister_tuple = astuple(canister)
    
    with transaction(database) as conn:
        conn.execute(sql, canister_tuple)