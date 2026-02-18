# -*- coding: utf-8 -*-
"""Tests for database operations — init, insert, get_table, transaction."""

import sqlite3

import pytest
import pandas as pd

from autogc_validation.database.management.init_db import initialize_database
from autogc_validation.database.models import MODEL_REGISTRY, Site
from autogc_validation.database.operations import insert, get_table
from autogc_validation.database.conn import transaction


class TestInitializeDatabase:
    def test_creates_all_tables(self, temp_db):
        """All expected tables are created."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
        for tablename in MODEL_REGISTRY:
            assert tablename in tables

    def test_raises_if_exists_without_force(self, tmp_path):
        db_path = tmp_path / "test.db"
        initialize_database(str(db_path))
        with pytest.raises(FileExistsError):
            initialize_database(str(db_path))

    def test_force_recreates(self, tmp_path):
        db_path = tmp_path / "test.db"
        initialize_database(str(db_path))
        initialize_database(str(db_path), force=True)  # should not raise
        # Verify tables still exist
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
        assert "sites" in tables


class TestInsert:
    def test_returns_true_for_new_record(self, temp_db):
        site = Site(
            site_id=99, name_short="TS", name_long="Test Site",
            lat=34.0, long=-118.0, date_started="2026-01-01 00:00:00",
        )
        assert insert(temp_db, site) is True

    def test_returns_false_for_duplicate(self, temp_db):
        site = Site(
            site_id=99, name_short="TS", name_long="Test Site",
            lat=34.0, long=-118.0, date_started="2026-01-01 00:00:00",
        )
        insert(temp_db, site)
        assert insert(temp_db, site) is False

    def test_raises_for_unknown_type(self, temp_db):
        with pytest.raises(TypeError):
            insert(temp_db, {"not": "a model"})


class TestGetTable:
    def test_returns_dataframe(self, temp_db):
        result = get_table(temp_db, "voc_info")
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0  # VOC data was seeded

    def test_correct_columns(self, temp_db):
        result = get_table(temp_db, "sites")
        assert "site_id" in result.columns
        assert "name_short" in result.columns

    def test_unknown_table_raises(self, temp_db):
        with pytest.raises(ValueError, match="Unknown table"):
            get_table(temp_db, "nonexistent_table")


class TestTransaction:
    def test_commits_on_success(self, temp_db):
        with transaction(temp_db) as conn:
            conn.execute(
                "INSERT INTO sites (site_id, name_short, name_long, lat, long, date_started) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (88, "TX", "Transaction Test", 35.0, -119.0, "2026-01-01 00:00:00"),
            )
        # Verify persisted
        result = get_table(temp_db, "sites")
        assert 88 in result["site_id"].values

    def test_rolls_back_on_exception(self, temp_db):
        with pytest.raises(RuntimeError):
            with transaction(temp_db) as conn:
                conn.execute(
                    "INSERT INTO sites (site_id, name_short, name_long, lat, long, date_started) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (77, "RB", "Rollback Test", 36.0, -120.0, "2026-01-01 00:00:00"),
                )
                raise RuntimeError("Force rollback")
        # Verify not persisted
        result = get_table(temp_db, "sites")
        assert 77 not in result["site_id"].values
