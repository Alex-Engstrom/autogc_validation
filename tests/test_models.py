# -*- coding: utf-8 -*-
"""Tests for database.models — Pydantic model validation."""

import pytest
from pydantic import ValidationError

from autogc_validation.database.models import Site
from autogc_validation.database.models.base import BaseModel


class TestSiteValidation:
    def test_valid_creation(self):
        site = Site(
            site_id=1, name_short="HW", name_long="Hawthorne",
            lat=33.9, long=-118.3, date_started="2026-01-01 00:00:00",
        )
        assert site.site_id == 1
        assert site.name_short == "HW"

    def test_invalid_lat_raises(self):
        with pytest.raises(ValidationError):
            Site(
                site_id=1, name_short="HW", name_long="Hawthorne",
                lat=91.0, long=-118.3, date_started="2026-01-01 00:00:00",
            )

    def test_invalid_long_raises(self):
        with pytest.raises(ValidationError):
            Site(
                site_id=1, name_short="HW", name_long="Hawthorne",
                lat=33.9, long=181.0, date_started="2026-01-01 00:00:00",
            )

    def test_empty_name_short_raises(self):
        with pytest.raises(ValidationError):
            Site(
                site_id=1, name_short="", name_long="Hawthorne",
                lat=33.9, long=-118.3, date_started="2026-01-01 00:00:00",
            )

    def test_negative_site_id_raises(self):
        with pytest.raises(ValidationError):
            Site(
                site_id=-1, name_short="HW", name_long="Hawthorne",
                lat=33.9, long=-118.3, date_started="2026-01-01 00:00:00",
            )


class TestToDictFromDict:
    def test_roundtrip(self):
        site = Site(
            site_id=1, name_short="HW", name_long="Hawthorne",
            lat=33.9, long=-118.3, date_started="2026-01-01 00:00:00",
        )
        d = site.to_dict()
        restored = Site.from_dict(d)
        assert restored.site_id == site.site_id
        assert restored.name_short == site.name_short
        assert restored.lat == site.lat

    def test_from_dict_ignores_extra_keys(self):
        d = {
            "site_id": 1, "name_short": "HW", "name_long": "Hawthorne",
            "lat": 33.9, "long": -118.3, "date_started": "2026-01-01 00:00:00",
            "extra_key": "ignored",
        }
        site = Site.from_dict(d)
        assert site.site_id == 1


class TestValidateDateFormat:
    def test_accepts_full_format(self):
        result = BaseModel.validate_date_format("2026-01-01 00:00:00")
        assert result == "2026-01-01 00:00:00"

    def test_accepts_short_format(self):
        result = BaseModel.validate_date_format("2026-01-01 00:00")
        assert result == "2026-01-01 00:00"

    def test_rejects_bad_format(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            BaseModel.validate_date_format("01/01/2026")

    def test_rejects_date_only(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            BaseModel.validate_date_format("2026-01-01")
