# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:05:41 2026

@author: aengstrom
"""

from dataclasses import astuple
from typing import List
from .insert import insert
from ..models.site import Site
def insert_site(database: str, site: Site)-> None:
    insert(database, site)

def get_all_sites(database: str) -> List[Site]:
    """Get all VOC information as list of VOCInfo objects."""
    sql = "SELECT * FROM sites"
    
    with get_connection(database) as conn:
        cursor = conn.execute(sql)
        return [Site.from_dict(dict(row)) for row in cursor.fetchall()]