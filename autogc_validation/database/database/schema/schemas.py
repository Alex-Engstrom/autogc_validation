# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:05:06 2026

@author: aengstrom
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class TableSchema:
    name: str
    sql: str

SCHEMAS: dict[str, TableSchema] = {
    "schema_version": TableSchema(
        name="SchemaVersion",
        sql="""
        CREATE TABLE IF NOT EXISTS SchemaVersion (
            version TEXT PRIMARY KEY,
            applied_on TEXT
        );
        """
    ),
    "voc_info": TableSchema(
        name="voc_info",
        sql="""
        CREATE TABLE IF NOT EXISTS voc_info (
            aqs_code INTEGER PRIMARY KEY,
            compound TEXT,
            category TEXT,
            carbon_count INTEGER,
            molecular_weight REAL,
            column TEXT,
            elution_order INTEGER,
            priority BOOLEAN
        );
        """
    ),
}
