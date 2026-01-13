# -*- coding: utf-8 -*-
"""
Created on Thu Oct 16 13:02:20 2025

@author: aengstrom
"""
import pandas as pd
import sqlite3
import os
import logging
from datetime import datetime
from typing import Iterable, Mapping, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if logger.hasHandlers():
    logger.handlers.clear()

#File handler
file_handler = logging.FileHandler('PAMS_VOC.log', mode = 'a')
file_handler.setLevel(logging.DEBUG)

# Formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                              datefmt = "%Y-%m-%d %H:%M")
file_handler.setFormatter(formatter)


# Add handlers
logger.addHandler(file_handler)
VOC_DATA = [
    {"compound": "Ethane", "aqs_code": 43202, "category": "Alkane", "carbon_count": 2, 'molecular_weight': 30.07, 'column': 'PLOT', 'elution_order': 1, 'priority': 1},
    {"compound": "Ethylene", "aqs_code": 43203, "category": "Alkene", "carbon_count": 2, 'molecular_weight': 28.05, 'column': 'PLOT', 'elution_order': 2, 'priority': 1},
    {"compound": "Propane", "aqs_code": 43204, "category": "Alkane", "carbon_count": 3, 'molecular_weight': 44.097, 'column': 'PLOT', 'elution_order': 3, 'priority': 1},
    {"compound": "Propylene", "aqs_code": 43205, "category": "Alkene", "carbon_count": 3, 'molecular_weight': 42.081, 'column': 'PLOT', 'elution_order': 4, 'priority': 1},
    {"compound": "Iso-butane", "aqs_code": 43214, "category": "Alkane", "carbon_count": 4, 'molecular_weight': 58.12, 'column': 'PLOT', 'elution_order': 5, 'priority': 1},
    {"compound": "N-butane", "aqs_code": 43212, "category": "Alkane", "carbon_count": 4, 'molecular_weight': 58.12, 'column': 'PLOT', 'elution_order': 6, 'priority': 1},
    {"compound": "Acetylene", "aqs_code": 43206, "category": "Alkyne", "carbon_count": 2, 'molecular_weight': 26.038, 'column': 'PLOT', 'elution_order': 7, 'priority': 0},
    {"compound": "Trans-2-butene", "aqs_code": 43216, "category": "Alkene", "carbon_count": 4, 'molecular_weight': 56.11, 'column': 'PLOT', 'elution_order': 8, 'priority': 1},
    {"compound": "1-butene", "aqs_code": 43280, "category": "Alkene", "carbon_count": 4, 'molecular_weight': 56.11, 'column': 'PLOT', 'elution_order': 9, 'priority': 1},
    {"compound": "Cis-2-butene", "aqs_code": 43217, "category": "Alkene", "carbon_count": 4, 'molecular_weight': 56.11, 'column': 'PLOT', 'elution_order': 10, 'priority': 1},
    {"compound": "Cyclopentane", "aqs_code": 43242, "category": "Alkane", "carbon_count": 5, 'molecular_weight': 70.13, 'column': 'PLOT', 'elution_order': 11, 'priority': 0},
    {"compound": "Iso-pentane", "aqs_code": 43221, "category": "Alkane", "carbon_count": 5, 'molecular_weight': 72.15, 'column': 'PLOT', 'elution_order': 12, 'priority': 1},
    {"compound": "N-pentane", "aqs_code": 43220, "category": "Alkane", "carbon_count": 5, 'molecular_weight': 72.15, 'column': 'PLOT', 'elution_order': 13, 'priority': 1},
    {"compound": "1,3-butadiene", "aqs_code": 43218, "category": "Alkene", "carbon_count": 4, 'molecular_weight': 54.0916, 'column': 'PLOT', 'elution_order': 14, 'priority': 0},
    {"compound": "Trans-2-pentene", "aqs_code": 43226, "category": "Alkene", "carbon_count": 5, 'molecular_weight': 70.13, 'column': 'PLOT', 'elution_order': 15, 'priority': 0},
    {"compound": "1-pentene", "aqs_code": 43224, "category": "Alkene", "carbon_count": 5, 'molecular_weight': 70.134, 'column': 'PLOT', 'elution_order': 16, 'priority': 0},
    {"compound": "Cis-2-pentene", "aqs_code": 43227, "category": "Alkene", "carbon_count": 5, 'molecular_weight': 70.134, 'column': 'PLOT', 'elution_order': 17, 'priority': 0},
    {"compound": "2,2-dimethylbutane", "aqs_code": 43244, "category": "Alkane", "carbon_count": 6, 'molecular_weight': 86.17, 'column': 'PLOT', 'elution_order': 18, 'priority': 0},
    {"compound": "2,3-dimethylbutane", "aqs_code": 43284, "category": "Alkane", "carbon_count": 6, 'molecular_weight': 86.17, 'column': 'PLOT', 'elution_order': 19, 'priority': 0},
    {"compound": "2-methylpentane", "aqs_code": 43285, "category": "Alkane", "carbon_count": 6, 'molecular_weight': 86.18, 'column': 'PLOT', 'elution_order': 20, 'priority': 0},
    {"compound": "3-methylpentane", "aqs_code": 43230, "category": "Alkane", "carbon_count": 6, 'molecular_weight': 86.18, 'column': 'PLOT', 'elution_order': 21, 'priority': 0},
    {"compound": "Isoprene", "aqs_code": 43243, "category": "Terpene", "carbon_count": 5, 'molecular_weight': 68.12, 'column': 'PLOT', 'elution_order': 22, 'priority': 1},
    {"compound": "2-methyl-1-pentene", "aqs_code": 43246, "category": "Alkene", "carbon_count": 6,'molecular_weight': 84.16, 'column': 'PLOT', 'elution_order': 23, 'priority': 0},
    {"compound": "1-hexene", "aqs_code": 43245, "category": "Alkene", "carbon_count": 6,'molecular_weight':84.1608, 'column': 'PLOT', 'elution_order': 24, 'priority': 0},
    {"compound": "N-hexane", "aqs_code": 43231, "category": "Alkane", "carbon_count": 6,'molecular_weight': 86.17848, 'column': 'BP', 'elution_order': 1, 'priority': 1},
    {"compound": "Methylcyclopentane", "aqs_code": 43262, "category": "Alkane", "carbon_count": 6,'molecular_weight':84.16, 'column': 'BP', 'elution_order': 2, 'priority': 0},
    {"compound": "2,4-dimethylpentane", "aqs_code": 43247, "category": "Alkane", "carbon_count": 7,'molecular_weight': 100.2, 'column': 'BP', 'elution_order': 3, 'priority': 0},
    {"compound": "Benzene", "aqs_code": 45201, "category": "Aromatic", "carbon_count": 6,'molecular_weight':78.11, 'column': 'BP', 'elution_order': 4, 'priority': 1},
    {"compound": "Cyclohexane", "aqs_code": 43248, "category": "Alkane", "carbon_count": 6,'molecular_weight':84.16, 'column': 'BP', 'elution_order': 5, 'priority': 0},
    {"compound": "2-methylhexane", "aqs_code": 43263, "category": "Alkane", "carbon_count": 7,'molecular_weight':100.2, 'column': 'BP', 'elution_order': 6, 'priority': 0},
    {"compound": "2,3-dimethylpentane", "aqs_code": 43291, "category": "Alkane", "carbon_count": 7,'molecular_weight':100.2, 'column': 'BP', 'elution_order': 7, 'priority': 0},
    {"compound": "3-methylhexane", "aqs_code": 43249, "category": "Alkane", "carbon_count": 7,'molecular_weight':100.2, 'column': 'BP', 'elution_order': 8, 'priority': 0},
    {"compound": "2,2,4-trimethylpentane", "aqs_code": 43250, "category": "Alkane", "carbon_count": 8,'molecular_weight':114.23, 'column': 'BP', 'elution_order': 9, 'priority': 1},
    {"compound": "N-heptane", "aqs_code": 43232, "category": "Alkane", "carbon_count": 7,'molecular_weight':100.21, 'column': 'BP', 'elution_order': 10, 'priority': 0},
    {"compound": "Methylcyclohexane", "aqs_code": 43261, "category": "Alkane", "carbon_count": 7,'molecular_weight':98.186, 'column': 'BP', 'elution_order': 11, 'priority': 0},
    {"compound": "2,3,4-trimethylpentane", "aqs_code": 43252, "category": "Alkane", "carbon_count": 8,'molecular_weight':114.23, 'column': 'BP', 'elution_order': 12, 'priority': 0},
    {"compound": "Toluene", "aqs_code": 45202, "category": "Aromatic", "carbon_count": 7,'molecular_weight':92.14, 'column': 'BP', 'elution_order': 13, 'priority': 1},
    {"compound": "2-methylheptane", "aqs_code": 43960, "category": "Alkane", "carbon_count": 8,'molecular_weight':114.23, 'column': 'BP', 'elution_order': 14, 'priority': 0},
    {"compound": "3-methylheptane", "aqs_code": 43253, "category": "Alkane", "carbon_count": 8,'molecular_weight':114.23, 'column': 'BP', 'elution_order': 15, 'priority': 0},
    {"compound": "N-octane", "aqs_code": 43233, "category": "Alkane", "carbon_count": 8,'molecular_weight':114.23, 'column': 'BP', 'elution_order': 16, 'priority': 0},
    {"compound": "Ethylbenzene", "aqs_code": 45203, "category": "Aromatic", "carbon_count": 8,'molecular_weight':106.167, 'column': 'BP', 'elution_order': 17, 'priority': 1},
    {"compound": "M&p-xylene", "aqs_code": 45109, "category": "Aromatic", "carbon_count": 8,'molecular_weight': 106.16, 'column': 'BP', 'elution_order': 18, 'priority': 1},
    {"compound": "Styrene", "aqs_code": 45220, "category": "Aromatic", "carbon_count": 8,'molecular_weight':104.15, 'column': 'BP', 'elution_order': 19, 'priority': 1},
    {"compound": "O-xylene", "aqs_code": 45204, "category": "Aromatic", "carbon_count": 8,'molecular_weight':106.16, 'column': 'BP', 'elution_order': 20, 'priority': 1},
    {"compound": "N-nonane", "aqs_code": 43235, "category": "Alkane", "carbon_count": 9,'molecular_weight':128.2, 'column': 'BP', 'elution_order': 21, 'priority': 0},
    {"compound": "Iso-propylbenzene", "aqs_code": 45210, "category": "Aromatic", "carbon_count": 9,'molecular_weight':120.19, 'column': 'BP', 'elution_order': 22, 'priority': 0},
    {"compound": "Alpha-pinene", "aqs_code": 43256, "category": "Terpene", "carbon_count": 10,'molecular_weight':136.23, 'column': 'BP', 'elution_order': 23, 'priority': 0},
    {"compound": "N-propylbenzene", "aqs_code": 45209, "category": "Aromatic", "carbon_count": 9,'molecular_weight':120.2, 'column': 'BP', 'elution_order': 24, 'priority': 0},
    {"compound": "M-ethyltoluene", "aqs_code": 45212, "category": "Aromatic", "carbon_count": 9,'molecular_weight':120.19, 'column': 'BP', 'elution_order': 25, 'priority': 1},
    {"compound": "P-ethyltoluene", "aqs_code": 45213, "category": "Aromatic", "carbon_count": 9,'molecular_weight':120.19, 'column': 'BP', 'elution_order': 26, 'priority': 1},
    {"compound": "1,3,5-tri-m-benzene", "aqs_code": 45207, "category": "Aromatic", "carbon_count": 9,'molecular_weight':120.19, 'column': 'BP', 'elution_order': 27, 'priority': 0},
    {"compound": "O-ethyltoluene", "aqs_code": 45211, "category": "Aromatic", "carbon_count": 9,'molecular_weight':120.19, 'column': 'BP', 'elution_order': 28, 'priority': 1},
    {"compound": "Beta-pinene", "aqs_code": 43257, "category": "Terpene", "carbon_count": 10,'molecular_weight':136.23, 'column': 'BP', 'elution_order': 29, 'priority': 0},
    {"compound": "1,2,4-tri-m-benzene", "aqs_code": 45208, "category": "Aromatic", "carbon_count": 9,'molecular_weight':120.19, 'column': 'BP', 'elution_order': 30, 'priority': 1},
    {"compound": "N-decane", "aqs_code": 43238, "category": "Alkane", "carbon_count": 10,'molecular_weight':142.28, 'column': 'BP', 'elution_order': 31, 'priority': 0},
    {"compound": "1,2,3-tri-m-benzene", "aqs_code": 45225, "category": "Aromatic", "carbon_count": 9,'molecular_weight':120.19, 'column': 'BP', 'elution_order': 32, 'priority': 1},
    {"compound": "M-diethylbenzene", "aqs_code": 45218, "category": "Aromatic", "carbon_count": 10,'molecular_weight':134.22, 'column': 'BP', 'elution_order': 33, 'priority': 0},
    {"compound": "P-diethylbenzene", "aqs_code": 45219, "category": "Aromatic", "carbon_count": 10,'molecular_weight':134.22, 'column': 'BP', 'elution_order': 34, 'priority': 0},
    {"compound": "N-undecane", "aqs_code": 43954, "category": "Alkane", "carbon_count": 11,'molecular_weight':156.31, 'column': 'BP', 'elution_order': 35, 'priority': 0},
    {"compound": "N-dodecane", "aqs_code": 43141, "category": "Alkane", "carbon_count": 12,'molecular_weight':170.34, 'column': 'BP', 'elution_order': 36, 'priority': 0}
]
#%% File management functions
def csv_to_list_of_dicts(concentration_csv: os.PathLike) -> list[dict]:
    df = pd.read_csv(concentration_csv)
    return df.to_dict(orient='records')

#%% Helper functions
def _connect(database: str) -> sqlite3.Connection:
    """Return a sqlite3 connection with foreign keys enabled."""
    conn = sqlite3.connect(database)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def check_date_format(date_str: str) -> bool:
    """Allow a couple of common formats used in timestamps."""
    formats = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M")
    for fmt in formats:
        try:
            datetime.strptime(date_str, fmt)
            return True
        except ValueError:
            continue
    return False


        
    
#%% SQL Utility functions
def delete_row_from_table(database: str, table_name: str, where_column: str, where_value) -> None:
    """
    Safely delete rows with a single equality condition.
    Avoids interpolating arbitrary condition strings.
    """
    if not table_name.isidentifier() or not where_column.isidentifier():
        raise ValueError("Invalid table or column name provided.")
    sql = f"DELETE FROM {table_name} WHERE {where_column} = ?"
    try:
        with _connect(database) as conn:
            conn.execute(sql, (where_value,))
            conn.commit()
            logger.debug("Deleted rows from %s where %s=%s", table_name, where_column, where_value)
    except sqlite3.Error as e:
        logger.exception("Error deleting rows from %s: %s", table_name, e)
        raise
def drop_table(database: str, table_name: str) ->None:
    if not table_name.isidentifier():
        raise ValueError("Invalid table name provided.")
    sql = f"DROP TABLE IF EXISTS {table_name}"
    try:
        with _connect(database) as conn:
            conn.execute(sql)
            conn.commit()
            logger.debug("Deleted table %s", table_name)
    except sqlite3.Error as e:
        logger.exception("Error deleting table %s: %s", table_name, e)
        raise
def drop_view(database: str, view_name: str) ->None:
    if not view_name.isidentifier():
        raise ValueError("Invalid table name provided.")
    sql = f"DROP VIEW IF EXISTS {view_name}"
    try:
        with _connect(database) as conn:
            conn.execute(sql)
            conn.commit()
            logger.debug("Deleted view %s", view_name)
    except sqlite3.Error as e:
        logger.exception("Error deleting view %s: %s", view_name, e)
        raise
def delete_all_table_entries(database: str, table_name: str) -> None:
    if not table_name.isidentifier():
        raise ValueError("Invalid table name provided.")
    sql = f"DELETE FROM {table_name}"
    try:
        with _connect(database) as conn:
            conn.execute(sql)
            conn.commit()
            logger.debug("Deleted all entries from %s", table_name)
    except sqlite3.Error as e:
        logger.exception("Error truncating table %s: %s", table_name, e)
        raise
def fetch_table(database: str, table_name: str) -> pd.DataFrame:
    if not table_name.isidentifier():
        raise ValueError("Invalid table name.")
    with _connect(database) as conn:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
#%% Schema version table
def create_schema_version_table(database: str) -> None:
    sql = """CREATE TABLE IF NOT EXISTS SchemaVersion (
    version TEXT PRIMARY KEY,
    applied_on TEXT
    );"""
    try:
        with _connect(database) as conn:
            conn.execute(sql)
            conn.commit()
            logger.info("Created schema_version table")
    except sqlite3.Error as e:
        logger.exception(f"Error creating schema_version table {e}")
        raise
#%% VOCinfo table functions       
def create_voc_info_table(database: str) -> None:
    sql = """
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
    with _connect(database) as conn:
        conn.execute(sql)
        conn.commit()
        logger.info("Created VOCInfo table")

def fill_voc_info_table(database: str, data: Iterable[Mapping]) -> None:
    """
    Uses INSERT OR IGNORE to make repeated runs idempotent.
    """
    sql = """
    INSERT OR IGNORE INTO voc_info (aqs_code, compound, category, carbon_count, molecular_weight, column, elution_order, priority)
    VALUES (:aqs_code, :compound, :category, :carbon_count, :molecular_weight, :column, :elution_order, :priority)
    """
    try:
        with _connect(database) as conn:
            conn.executemany(sql, list(data))
            conn.commit()
            logger.info("Inserted VOC info (or ignored duplicates).")
    except sqlite3.Error as e:
        logger.exception("Failed to fill VOCinfo: %s", e)
        raise
#%% Sites table functions
def create_sites_table(database: str) -> None:
    """
    """
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
    with _connect(database) as conn:
        conn.execute(sql)
        conn.commit()

def add_site(database: str, site_id: int, name_short: str, name_long: str, lat: float, long: float, date_started: str) -> None:
    if not check_date_format(date_started):
        logger.exception("Date must use one of the formats: %%Y-%%m-%%d %%H:%%M[:%%S]")
        raise ValueError("Use %Y-%m-%d %H:%M:%S or %Y-%m-%d %H:%M format")
    sql = "INSERT OR IGNORE INTO sites (site_id, name_short, name_long, lat, long, date_started) VALUES (?,?,?,?,?,?)"
    try:
        with _connect(database) as conn:
            conn.execute(sql, (site_id, name_short, name_long, lat, long, date_started))
            conn.commit()
            logger.info("Added site %s (%s).", name_short, site_id)
    except sqlite3.IntegrityError as e:
        logger.exception("Integrity error adding site %s: %s", site_id, e)
        raise
    except sqlite3.Error as e:
        logger.exception("DB error adding site %s: %s", site_id, e)
        raise
#%% Primary canisters
def create_canister_types_table(database: str) -> None:
    sql = """
    CREATE TABLE IF NOT EXISTS canister_types (
        canister_type TEXT PRIMARY KEY
    );
    """
    try:
        with _connect(database) as conn:
            conn.execute(sql)
            conn.commit()
            logger.info("Created canister_types table")
    except sqlite3.OperationalError as e:
        logger.exception("Operational error creating canister_types table: %s", e)
        raise
    except sqlite3.Error as e:
        logger.exception("Unexpected SQLite error creating canister_types table: %s", e)
        raise
def add_canister_type(database:str, canister_type: str) -> None:
    """ Add Canister type (CVS, RTS, LCS, etc) to canister_types table"""
    sql = "INSERT OR IGNORE INTO canister_types (canister_type) VALUES (?)"
    try:
        with _connect(database) as conn:
            conn.execute(sql, (canister_type,))
            conn.commit()
            logger.info(f"Added canister type: {canister_type}")
    except sqlite3.IntegrityError as e:
        logger.exception(f"Integrity error adding canister type: {canister_type}. {e}")
        raise
    except sqlite3.Error as e:
        logger.exception(f"DB error adding canister type: {canister_type}. {e}")
        raise
def create_primary_canisters_table(database: str) -> None:
    sql = """
    CREATE TABLE IF NOT EXISTS primary_canisters (
        primary_canister_id TEXT PRIMARY KEY,
        canister_type TEXT NOT NULL,
        FOREIGN KEY(canister_type) REFERENCES canister_types(canister_type)
    );
    """
    with _connect(database) as conn:
        conn.execute(sql)
        conn.commit()
def add_primary_canister(database: str, primary_canister_id: str, canister_type: str)-> None:
    """ Add primary canister to primary_canisters_table"""
    sql = "INSERT OR IGNORE INTO primary_canisters (primary_canister_id, canister_type) VALUES (?,?)"
    try:
        with _connect(database) as conn:
            conn.execute(sql, (primary_canister_id, canister_type))
            conn.commit()
            logger.info(f"Added primary_canister: {primary_canister_id}")
    except sqlite3.IntegrityError as e:
        logger.exception(f"Integrity error adding primary_canister: {primary_canister_id}. {e}")
        raise
    except sqlite3.Error as e:
        logger.exception(f"DB error adding primary_canister: {primary_canister_id}. {e}")
        raise
def create_primary_canister_concentration_table(database: str) -> None:
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
    with _connect(database) as conn:
        conn.execute(sql)
        conn.commit()
def add_primary_canister_concentration(database: str, data: Iterable[Mapping], units: str) -> None:
    """
    Inserts primary canister concentrations into the database.
    Supports units: ppbv, ppmv, ppbC, ppmC.
    All concentrations are stored as ppbv (by volume).
    """
    acceptable_units = ['ppbv', 'ppmv', 'ppbc', 'ppmc']
    units = units.lower()

    if units not in acceptable_units:
        logger.error(f"Incorrect units. Units must be one of: {', '.join(acceptable_units)}")
        raise ValueError("Invalid units.")

    # Connect to DB and fetch carbon counts for compounds
    with _connect(database) as conn:
        cur = conn.cursor()
        cur.execute("SELECT aqs_code, carbon_count FROM voc_info;")
        carbon_counts = dict(cur.fetchall())  # {aqs_code: carbon_count}

    # Determine conversion factor for ppm → ppb
    ppm_to_ppb = 1000 if 'ppm' in units else 1

    # Apply conversions row-by-row
    converted_data = []
    for row in data:
        aqs = row["aqs_code"]
        conc = row["concentration"]

        if aqs not in carbon_counts:
            logger.warning(f"AQS code {aqs} not found in voc_info. Skipping.")
            continue

        carbon_count = carbon_counts[aqs]
        if carbon_count <= 0:
            logger.warning(f"Invalid carbon count for AQS code {aqs}. Skipping.")
            continue

        # Convert based on unit type
        if 'c' in units:  # ppbC or ppmC
            conc = conc / carbon_count  # convert from carbon-based to volume-based
        conc = conc * ppm_to_ppb  # convert ppm → ppb if needed

        # Update concentration and add to final list
        row = dict(row)
        row['concentration'] = conc
        converted_data.append(row)

    # Insert into database
    sql = """
    INSERT OR IGNORE INTO primary_canister_concentration
    (primary_canister_id, aqs_code, concentration, canister_type)
    VALUES (:primary_canister_id, :aqs_code, :concentration, :canister_type)
    """

    try:
        with _connect(database) as conn:
            conn.executemany(sql, converted_data)
            conn.commit()
            logger.info(f"Added {len(converted_data)} canister concentrations in {units}.")
    except sqlite3.IntegrityError as e:
        logger.exception(f"Integrity error adding canister concentrations: {e}")
        raise
    except sqlite3.Error as e:
        logger.exception(f"Database error adding canister concentrations: {e}")
        raise
#%% Site canisters◘
def create_site_canisters_table(database: str) -> None:
    """
    Create the site_canisters table.

    Tracks which primary canisters are at which site,
    including dilution ratios, expiration, and usage status.
    """
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
    try:
        with _connect(database) as conn:
            conn.execute(sql)
            conn.commit()
            logger.info("Created or verified site_canisters table successfully.")
    except sqlite3.OperationalError as e:
        logger.exception("Operational error creating site_canisters table: %s", e)
        raise
    except sqlite3.Error as e:
        logger.exception("Unexpected SQLite error creating site_canisters table: %s", e)
        raise
def add_site_canister(database: str, site_canister_id: str, site_id: int, primary_canister_id: str,
                      dilution_ratio: float, blend_date: str, date_on: str, date_off: Optional[str] = None,
                      in_use: int = 0 ) -> None:
    """
    Add a canister to a site.
    in_use: 0 = not in use, 1 = in use
    date_off: optional timestamp when canister returned
    """
    sql = """
    INSERT OR IGNORE INTO site_canisters
        (site_canister_id, site_id, primary_canister_id, dilution_ratio, blend_date,date_on, date_off, in_use)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        with _connect(database) as conn:
            conn.execute(sql, (site_canister_id, site_id, primary_canister_id, dilution_ratio, blend_date, date_on, date_off, in_use))
            conn.commit()
            logger.info("Added site_canister: %s", site_canister_id)
    except sqlite3.IntegrityError as e:
        logger.exception("Integrity error adding site_canister %s: %s", site_canister_id, e)
        raise
    except sqlite3.Error as e:
        logger.exception("DB error adding site_canister %s: %s", site_canister_id, e)
        raise


def set_site_canister_in_use(database: str, site_canister_id: str, in_use: int = 1) -> None:
    """
    Update the in_use status of a site_canister.
    in_use: 0 = not in use, 1 = in use
    """
    sql = "UPDATE site_canisters SET in_use = ? WHERE site_canister_id = ?"
    try:
        with _connect(database) as conn:
            conn.execute(sql, (in_use, site_canister_id))
            conn.commit()
            logger.info("Updated in_use for %s to %d", site_canister_id, in_use)
    except sqlite3.Error as e:
        logger.exception("Error updating in_use for %s: %s", site_canister_id, e)
        raise


def set_canister_date_off(database: str, site_canister_id: str, date_off: str) -> None:
    """
    Set or update the date_off timestamp for a site_canister.
    """
    if not check_date_format(date_off):
        logger.error("Date must be in %Y-%m-%d %H:%M:%S or %Y-%m-%d %H:%M format")
        raise ValueError("Invalid date format")
    
    sql = "UPDATE site_canisters SET date_off = ? WHERE site_canister_id = ?"
    try:
        with _connect(database) as conn:
            conn.execute(sql, (date_off, site_canister_id))
            conn.commit()
            logger.info("Updated date_off for %s to %s", site_canister_id, date_off)
    except sqlite3.Error as e:
        logger.exception("Error updating date_off for %s: %s", site_canister_id, e)
        raise
def create_site_canister_concentration_view(database: str) -> None:
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
    try:
        with _connect(database) as conn:
            conn.execute(sql)
            conn.commit()
            logger.info("Created canister_types view")
    except sqlite3.OperationalError as e:
        logger.exception("Operational error creating site_canister_concentration_view: %s", e)
        raise
    except sqlite3.Error as e:
        logger.exception("Unexpected SQLite error creating site_canister_concentration_view: %s", e)
        raise
#%% MDLs table and functions
def create_mdls_table(database: str) -> None:
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
    with _connect(database) as conn:
        conn.execute(sql)
        conn.commit()

#def add_many_mdls(database: str, mdls:Iterable[Mapping]) -> None:
    

if __name__ == "__main__":
    database = "PAMS_VOC.db"

    # -----------------------------
    # 1️⃣ VOC info
    # -----------------------------
    create_voc_info_table(database)
    fill_voc_info_table(database, VOC_DATA)
    voc_df = fetch_table(database, "voc_info")
    
    # -----------------------------
    # 2️⃣ Sites
    # -----------------------------
    create_sites_table(database)
    add_site(
        database,
        site_id=490353014,
        name_short='LP',
        name_long="Lake Park",
        lat=40.709905,
        long=-112.008684,
        date_started='2025-02-06 10:00:00'
    )
    sites_df = fetch_table(database, 'sites')
    
    # -----------------------------
    # 3️⃣ Canister types
    # -----------------------------
    create_canister_types_table(database)
    for canister_type in ['CVS', 'LCS', 'RTS']:
        add_canister_type(database, canister_type)
    canister_type_df = fetch_table(database, 'canister_types')
    
    # -----------------------------
    # 4️⃣ Drop old tables/views
    # -----------------------------
    drop_view(database, 'site_canister_concentration')
    drop_table(database, 'site_canisters')
    drop_table(database, 'primary_canister_concentration')
    drop_table(database, 'primary_canisters')
    
    # -----------------------------
    # 5️⃣ Primary canisters
    # -----------------------------
    create_primary_canisters_table(database)
    add_primary_canister(
        database,
        primary_canister_id='CC177206-0125',
        canister_type='LCS',
        certification_date='2023-01-31 00:00:00',
        expiration_date='2025-01-31 00:00:00'
    )
    add_primary_canister(
        database,
        primary_canister_id='CC524930-0626',
        canister_type='CVS',
        certification_date='2024-06-14 00:00:00',
        expiration_date='2025-06-14 00:00:00'
    )
    add_primary_canister(
        database,
        primary_canister_id='CC731198-0126',
        canister_type='RTS',
        certification_date='2024-01-25 00:00:00',
        expiration_date='2026-01-25 00:00:00'
    )
    primary_canister_table_df = fetch_table(database, 'primary_canisters')
    
    # -----------------------------
    # 6️⃣ Primary canister concentrations
    # -----------------------------
    create_primary_canister_concentration_table(database)
    
    CC177206_0125 = csv_to_list_of_dicts('CC177206_0125.csv')
    CC524930_0626 = csv_to_list_of_dicts('CC524930_0626.csv')
    CC731198_0126 = csv_to_list_of_dicts('CC731198_0126.csv')
    
    add_primary_canister_concentration(database, CC177206_0125, units='ppmv')
    add_primary_canister_concentration(database, CC524930_0626, units='ppmv')
    add_primary_canister_concentration(database, CC731198_0126, units='ppbc')
    
    primary_canister_concentration_df = fetch_table(database, 'primary_canister_concentration')
    
    # -----------------------------
    # 7️⃣ Site canisters
    # -----------------------------
    create_site_canisters_table(database)
    
    add_site_canister(
        database,
        site_canister_id='3732',
        primary_canister_id='CC177206-0125',
        site_id=490353014,           # ensure int
        dilution_ratio=0.005,
        blend_date='2024-09-10 15:20:00',
        date_on='2025-02-06 00:00:00',
        date_off='2025-06-27 12:59:59',
        in_use=0
    )
    
    add_site_canister(
        database,
        site_canister_id='3803',
        primary_canister_id='CC524930-0626',
        site_id=490353014,
        dilution_ratio=0.00148,
        blend_date='2024-08-13 00:00:00',
        date_on='2025-02-06 00:00:00',
        date_off='2025-07-16 09:59:59',
        in_use=0
    )
    
    add_site_canister(
        database,
        site_canister_id='50668',
        primary_canister_id='CC731198-0126',
        site_id=490353014,
        dilution_ratio=0.00135,
        blend_date='2024-07-25 00:00:00',
        date_on='2025-02-06 00:00:00',
        in_use=1  # currently in use
    )
    
    # -----------------------------
    # 8️⃣ Create view for site canister concentrations
    # -----------------------------
    create_site_canister_concentration_view(database)
    site_canister_concentration_df = fetch_table(database, 'site_canister_concentration')
    # database = "PAMS_VOC.db"
    # #Delete tables to avoid errors when rerunning code block
    # drop_view(database = database, view_name = 'site_canister_concentration')
    # drop_table(database = database, table_name = 'site_canisters')
    # drop_table(database = database, table_name = 'primary_canister_concentration')
    # drop_table(database = database, table_name = 'primary_canisters')
    
    # create_voc_info_table(database = database)
    # fill_voc_info_table(database = database, data = VOC_DATA)
    # voc_df = fetch_table(database = database, table_name = "voc_info")
    # create_sites_table(database = database)
    # add_site(database = database, site_id = 490353014, name_short = 'LP', name_long = "Lake Park", lat = 40.709905, long = -112.008684, date_started = '2025-02-06 10:00:00')
    # sites_df =fetch_table(database = database, table_name = 'sites')
    # create_canister_types_table(database)
    # canister_types = ['CVS', 'LCS', 'RTS']
    # for canister_type in canister_types:
    #     add_canister_type(database, canister_type = canister_type)
    # canister_type_df = fetch_table(database = database, table_name = 'canister_types')

    
    # create_primary_canisters_table(database = database)
    # add_primary_canister(database = database, 
    #                      primary_canister_id = 'CC177206-0125', 
    #                      canister_type = 'LCS', 
    #                      certification_date = '2023-01-31 00:00:00',
    #                      expiration_date = '2025-01-31 00:00:00')
    # primary_canister_table_df = fetch_table(database = database, table_name = 'primary_canisters')
    # create_primary_canister_concentration_table(database = database)
    # #primary_canisters 
    # CC177206_0125 = csv_to_list_of_dicts('CC177206_0125.csv')
    # CC524930_0626 = csv_to_list_of_dicts('CC524930_0626.csv')
    # CC731198_0126 = csv_to_list_of_dicts('CC731198_0126.csv')
    # add_primary_canister_concentration(database = database, data = CC177206_0125, units = 'ppmv')
    # add_primary_canister_concentration(database = database, data = CC524930_0626, units = 'ppmv')
    # add_primary_canister_concentration(database = database, data = CC731198_0126, units = 'ppbc')
    # primary_canister_concentration_df = fetch_table(database = database, table_name = 'primary_canister_concentration')
    # create_site_canisters_table(database = database)
    # add_site_canister(database = database, 
    #                   site_canister_id = '3732', 
    #                   primary_canister_id = 'CC177206-0125', 
    #                   site_id = 490353014, 
    #                   dilution_ratio = .005, 
    #                   blend_date = '2024-09-10 15:20:00', 
    #                   date_on = '2025-02-06 00:00:00', 
    #                   date_off = '2025-06-27 12:59:59')
    # add_site_canister(database = database, 
    #                   site_canister_id = '3803', 
    #                   primary_canister_id = 'CC524930-0626', 
    #                   site_id = 490353014, 
    #                   dilution_ratio = 0.00148, 
    #                   blend_date = '2024-08-13 15:20:00', 
    #                   date_on = '2025-02-06 00:00:00', 
    #                   date_off = '2025-07-16 09:59:59')
    # add_site_canister(database = database, 
    #                   site_canister_id = '50668', 
    #                   primary_canister_id = 'CC731198-0126', 
    #                   site_id = 490353014, 
    #                   dilution_ratio = .005, 
    #                   blend_date = '2024-07-25 00:00:00', 
    #                   date_on = '2025-02-06 00:00:00')
    # set_site_canister_in_use(database, '50668', True)
    # create_site_canister_concentration_view(database = database)
    # site_canister_concentration_df = fetch_table(database = database, table_name = 'site_canister_concentration')
    
    
    