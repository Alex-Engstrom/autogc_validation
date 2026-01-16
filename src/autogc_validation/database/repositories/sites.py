# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:05:41 2026

@author: aengstrom
"""

from dataclasses import astuple
from typing import List
from ..connection.manager import get_connection, transaction
from ..models.site import Site
def insert_site(database: str, site: Site)-> None:
    sql = "INSERT OR IGNORE INTO sites (site_id, name_short, name_long, lat, long, date_started) VALUES (?,?,?,?,?,?)"
    site_tuple =  astuple(site)
    
    with transaction(database) as conn:
        conn.execute(sql, site_tuple)

def get_all_sites(database: str) -> List[Site]:
    """Get all VOC information as list of VOCInfo objects."""
    sql = "SELECT * FROM sites"
    
    with get_connection(database) as conn:
        cursor = conn.execute(sql)
        return [Site.from_dict(dict(row)) for row in cursor.fetchall()]