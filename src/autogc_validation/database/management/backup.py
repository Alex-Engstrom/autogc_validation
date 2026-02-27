# -*- coding: utf-8 -*-
"""
Database backup and restore utilities.

Provides functions to dump a SQLite database to a .sql file and restore
it from that file, allowing the database to be regenerated if lost.
"""
import logging
import sqlite3
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def dump_database(database_path: Union[str, Path], output_path: Union[str, Path]) -> Path:
    """Dump a SQLite database to a SQL script file.

    Args:
        database_path: Path to the SQLite .db file.
        output_path: Path to write the .sql dump file.

    Returns:
        Path to the written .sql file.
    """
    database_path = Path(database_path)
    output_path = Path(output_path)

    if not database_path.exists():
        raise FileNotFoundError(f"Database not found: {database_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as conn:
        dump = "\n".join(conn.iterdump())

    output_path.write_text(dump, encoding="utf-8")
    logger.info("Database dumped to %s (%d bytes)", output_path, output_path.stat().st_size)
    return output_path


def restore_database(sql_path: Union[str, Path], database_path: Union[str, Path], force: bool = False) -> None:
    """Restore a SQLite database from a SQL dump file.

    Args:
        sql_path: Path to the .sql dump file.
        database_path: Path to write the restored .db file.
        force: If True, overwrite an existing database file.

    Raises:
        FileNotFoundError: If the SQL dump file does not exist.
        FileExistsError: If the database already exists and force=False.
    """
    sql_path = Path(sql_path)
    database_path = Path(database_path)

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL dump not found: {sql_path}")

    if database_path.exists() and not force:
        raise FileExistsError(
            f"Database already exists at {database_path}. Use force=True to overwrite."
        )

    if database_path.exists() and force:
        database_path.unlink()
        logger.info("Deleted existing database at %s", database_path)

    database_path.parent.mkdir(parents=True, exist_ok=True)
    sql = sql_path.read_text(encoding="utf-8")

    with sqlite3.connect(database_path) as conn:
        conn.executescript(sql)

    logger.info("Database restored to %s from %s", database_path, sql_path)
