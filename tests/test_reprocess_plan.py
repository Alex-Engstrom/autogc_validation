# -*- coding: utf-8 -*-
"""Tests for reports.reprocess_plan helper functions."""

import pandas as pd
import pytest

from autogc_validation.reports.reprocess_plan import (
    _build_outlier_lookup,
    _format_notes,
)


def _make_outliers_df(records):
    """Build a minimal outliers DataFrame like check_lognormal_outliers returns.

    records: list of (timestamp_str, compound_int, compound_name, value, threshold)
    """
    if not records:
        return pd.DataFrame(columns=["compound", "compound_name", "value", "threshold"])
    rows = []
    for ts, code, name, val, thr in records:
        rows.append({
            "timestamp": pd.Timestamp(ts),
            "compound": code,
            "compound_name": name,
            "value": val,
            "threshold": thr,
        })
    df = pd.DataFrame(rows).set_index("timestamp")
    df.index.name = None
    return df


class TestBuildOutlierLookup:
    def test_none_returns_empty_dict(self):
        assert _build_outlier_lookup(None) == {}

    def test_empty_df_returns_empty_dict(self):
        df = _make_outliers_df([])
        assert _build_outlier_lookup(df) == {}

    def test_single_entry_correct_day_key(self):
        df = _make_outliers_df([
            ("2026-01-15 14:00", 45201, "Benzene", 8.5, 4.0),
        ])
        result = _build_outlier_lookup(df)
        assert 15 in result
        assert len(result[15]) == 1

    def test_tuple_structure(self):
        df = _make_outliers_df([
            ("2026-01-15 14:00", 45201, "Benzene", 8.5, 4.0),
        ])
        result = _build_outlier_lookup(df)
        hour, name, val, thr = result[15][0]
        assert hour == 14
        assert name == "Benzene"
        assert val == pytest.approx(8.5)
        assert thr == pytest.approx(4.0)

    def test_groups_multiple_entries_by_day(self):
        df = _make_outliers_df([
            ("2026-01-15 08:00", 45201, "Benzene", 5.0, 3.0),
            ("2026-01-15 12:00", 43202, "Ethane", 7.0, 3.5),
            ("2026-01-16 10:00", 45201, "Benzene", 6.0, 3.0),
        ])
        result = _build_outlier_lookup(df)
        assert len(result[15]) == 2
        assert len(result[16]) == 1

    def test_timezone_stripped(self):
        """Timezone-aware index is handled without error."""
        records = [("2026-01-15 14:00", 45201, "Benzene", 8.5, 4.0)]
        df = _make_outliers_df(records)
        df.index = df.index.tz_localize("UTC")
        result = _build_outlier_lookup(df)
        assert 15 in result


class TestFormatNotes:
    def test_no_inputs_returns_empty_string(self):
        assert _format_notes(15, {}, {}) == ""

    def test_overrange_only(self):
        overrange_by_day = {15: [(8, "Benzene", 55.0)]}
        result = _format_notes(15, overrange_by_day, {})
        assert "Overrange" in result
        assert "Benzene" in result
        assert "08:00" in result

    def test_tnmhc_only(self):
        tnmhc_by_day = {15: (10, 125.3)}
        result = _format_notes(15, {}, tnmhc_by_day)
        assert "TNMHC" in result
        assert "125.3" in result
        assert "10:00" in result

    def test_outlier_only(self):
        outlier_by_day = {15: [(14, "Isoprene", 8.43, 6.21)]}
        result = _format_notes(15, {}, {}, outlier_by_day)
        assert "Outlier" in result
        assert "Isoprene" in result
        assert "14:00" in result
        assert "8.43" in result
        assert "6.21" in result

    def test_all_three_sections_present(self):
        overrange_by_day = {15: [(8, "Benzene", 55.0)]}
        tnmhc_by_day = {15: (10, 125.3)}
        outlier_by_day = {15: [(14, "Isoprene", 8.43, 6.21)]}
        result = _format_notes(15, overrange_by_day, tnmhc_by_day, outlier_by_day)
        assert "Overrange" in result
        assert "TNMHC" in result
        assert "Outlier" in result

    def test_outlier_day_mismatch_not_included(self):
        """Outliers on day 16 do not appear in notes for day 15."""
        outlier_by_day = {16: [(14, "Isoprene", 8.43, 6.21)]}
        result = _format_notes(15, {}, {}, outlier_by_day)
        assert "Outlier" not in result

    def test_empty_outlier_dict_no_outlier_lines(self):
        result = _format_notes(15, {}, {}, {})
        assert "Outlier" not in result

    def test_none_outlier_dict_no_outlier_lines(self):
        result = _format_notes(15, {}, {}, None)
        assert "Outlier" not in result

    def test_multiple_outliers_same_hour_grouped(self):
        """Multiple compounds at the same hour appear on one line."""
        outlier_by_day = {15: [
            (14, "Benzene", 8.43, 6.21),
            (14, "Toluene", 9.0, 5.5),
        ]}
        result = _format_notes(15, {}, {}, outlier_by_day)
        lines = result.strip().splitlines()
        outlier_lines = [l for l in lines if "Outlier" in l]
        assert len(outlier_lines) == 1  # grouped into one line
