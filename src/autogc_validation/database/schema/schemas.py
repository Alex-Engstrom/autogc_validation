# -*- coding: utf-8 -*-
"""
Created on Tue Jan 13 14:05:06 2026

@author: aengstrom
"""

from pydantic.dataclasses import dataclass
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
    "sites": TableSchema(
        name="sites",
        sql = """
        CREATE TABLE IF NOT EXISTS sites (
            site_id INTEGER PRIMARY KEY,
            name_short TEXT UNIQUE,
            name_long TEXT UNIQUE,
            lat REAL,
            long REAL,
            date_started TEXT
        );
        """
        ),
    "canister_types": TableSchema(
        name = "canister_types",
        sql = """
        CREATE TABLE IF NOT EXISTS canister_types (
            canister_type TEXT PRIMARY KEY
        );
        """
        ),
    "primary_canisters": TableSchema(
        name = "primary_canisters",
        sql = """
        CREATE TABLE IF NOT EXISTS primary_canisters (
            primary_canister_id TEXT PRIMARY KEY,
            canister_type TEXT NOT NULL,
            certification_date TEXT NOT NULL,
            expiration_date TEXT NOT NULL,
            FOREIGN KEY(canister_type) REFERENCES canister_types(canister_type)
        );
        """
        ),
    "primary_canister_concentration": TableSchema(
        name = "primary_canister_concentration",
        sql = """
        CREATE TABLE IF NOT EXISTS primary_canister_concentration (
            primary_canister_id TEXT,
            aqs_code INTEGER,
            concentration REAL,
            canister_type TEXT,
            PRIMARY KEY (primary_canister_id, aqs_code),
            FOREIGN KEY (primary_canister_id) REFERENCES primary_canisters(primary_canister_id),
            FOREIGN KEY (aqs_code) REFERENCES voc_info(aqs_code),
            FOREIGN KEY (canister_type) REFERENCES canister_types(canister_type)
        );
        """
        ),
    "site_canisters": TableSchema(
        name = "site_canisters",
        sql = """
        CREATE TABLE IF NOT EXISTS site_canisters (
            site_canister_id TEXT PRIMARY KEY,
            site_id INTEGER NOT NULL,
            primary_canister_id TEXT NOT NULL,
            dilution_ratio REAL,
            blend_date TEXT,
            date_on TEXT,
            date_off TEXT,                   -- timestamp when returned
            in_use INTEGER DEFAULT 0,        -- 0 = not in use, 1 = in use        
            FOREIGN KEY (site_id) REFERENCES sites(site_id),
            FOREIGN KEY (primary_canister_id) REFERENCES primary_canisters(primary_canister_id)
        );
        """
        ),
    "mdls": TableSchema(
        name = "mdls",
        sql = """
        CREATE TABLE IF NOT EXISTS mdls (
            site_id INTEGER,
            date_applied TEXT,
            aqs_code INTEGER,
            concentration REAL,
            PRIMARY KEY (site_id, aqs_code, date_applied),
            FOREIGN KEY (site_id) REFERENCES sites(site_id),
            FOREIGN KEY (aqs_code) REFERENCES voc_info(aqs_code)
        );
        """
        ),
    "site_canister_concentration_view": TableSchema(
        name = "site_canister_concentration_view",
            sql = """
        CREATE VIEW IF NOT EXISTS site_canister_concentration AS
        SELECT
            s.site_canister_id,
            s.primary_canister_id,
            c.canister_type,
            s.dilution_ratio,
            s.date_on,
            s.date_off,
            c.expiration_date,
            p.aqs_code,
            v.compound,
            --v.cas_number,
            p.concentration * s.dilution_ratio AS diluted_concentration_ppbv,
            p.concentration * s.dilution_ratio * v.carbon_count AS diluted_concentration_ppbC
        FROM site_canisters s
        JOIN primary_canister_concentration p
            ON s.primary_canister_id = p.primary_canister_id
        JOIN voc_info v
            ON p.aqs_code = v.aqs_code
        JOIN primary_canisters c
            ON p.primary_canister_id = c.primary_canister_id;
            """
                )
}
