# -*- coding: utf-8 -*-
"""Shared test fixtures for autogc_validation."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from autogc_validation.database.enums import CompoundAQSCode, name_to_aqs
from autogc_validation.database.management.init_db import initialize_database


# ---------------------------------------------------------------------------
# A small set of real AQS codes used across test fixtures
# ---------------------------------------------------------------------------
TEST_COMPOUNDS = {
    "Ethane": CompoundAQSCode.C_ETHANE,       # 43202 (PLOT)
    "Benzene": CompoundAQSCode.C_BENZENE,     # 45201 (BP)
    "Toluene": CompoundAQSCode.C_TOLUENE,     # 45202 (BP)
    "Propane": CompoundAQSCode.C_PROPANE,      # 43204 (PLOT)
    "Ethylene": CompoundAQSCode.C_ETHYLENE,    # 43203 (PLOT)
}


@pytest.fixture
def sample_aqs_codes():
    """A small dict of {name: AQS code} for test DataFrames."""
    return dict(TEST_COMPOUNDS)


@pytest.fixture
def sample_mdls():
    """MDL values (ppbC) for the 5 test compounds."""
    return {
        CompoundAQSCode.C_ETHANE: 0.10,
        CompoundAQSCode.C_BENZENE: 0.05,
        CompoundAQSCode.C_TOLUENE: 0.08,
        CompoundAQSCode.C_PROPANE: 0.12,
        CompoundAQSCode.C_ETHYLENE: 0.07,
    }


@pytest.fixture
def sample_canister_conc():
    """Canister concentrations for recovery tests (before dilution)."""
    return {
        CompoundAQSCode.C_ETHANE: 10.0,
        CompoundAQSCode.C_BENZENE: 10.0,
        CompoundAQSCode.C_TOLUENE: 10.0,
        CompoundAQSCode.C_PROPANE: 10.0,
        CompoundAQSCode.C_ETHYLENE: 10.0,
    }


@pytest.fixture
def make_dataset_df():
    """Factory fixture that builds a fake Dataset.data-shaped DataFrame.

    Usage:
        df = make_dataset_df(sample_type="b", values={43202: 0.5, 45201: 0.01})
    """
    def _make(
        sample_type="s",
        values=None,
        n_rows=1,
        start_time="2026-01-15 08:00:00",
    ):
        if values is None:
            values = {code.value: 0.0 for code in TEST_COMPOUNDS.values()}

        timestamps = pd.date_range(start_time, periods=n_rows, freq="h")
        rows = []
        for i, ts in enumerate(timestamps):
            row = {
                "date_time": ts,
                "sample_type": sample_type,
                "filename": f"TEST{sample_type.upper()}A{i:02d}A",
            }
            row.update(values)
            rows.append(row)

        df = pd.DataFrame(rows).set_index("date_time")
        return df

    return _make


@pytest.fixture
def blank_df(make_dataset_df, sample_mdls):
    """Pre-built DataFrame with blank rows — all below MDL by default."""
    values = {code: 0.01 for code in sample_mdls}
    return make_dataset_df(sample_type="b", values=values, n_rows=3)


@pytest.fixture
def ambient_df(make_dataset_df, sample_mdls):
    """Pre-built DataFrame with ambient rows."""
    codes = list(TEST_COMPOUNDS.values())
    all_codes = [c for c in CompoundAQSCode if c not in {CompoundAQSCode.C_TNMHC, CompoundAQSCode.C_TNMTC}]
    values = {int(c): 1.0 for c in all_codes}
    # Set TNMHC and TNMTC
    values[int(CompoundAQSCode.C_TNMHC)] = 50.0
    values[int(CompoundAQSCode.C_TNMTC)] = 55.0
    return make_dataset_df(sample_type="s", values=values, n_rows=3)


@pytest.fixture
def qc_df(make_dataset_df, sample_canister_conc):
    """Pre-built DataFrame with QC (CVS) rows — 100% recovery by default."""
    blend_ratio = 1.0
    values = {int(code): conc * blend_ratio for code, conc in sample_canister_conc.items()}
    return make_dataset_df(sample_type="c", values=values, n_rows=2)


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary initialized SQLite database, yield path, clean up."""
    db_path = tmp_path / "test.db"
    initialize_database(str(db_path))
    yield str(db_path)


@pytest.fixture
def temp_root(tmp_path):
    """Provides a temporary root folder for file ops tests."""
    return tmp_path
