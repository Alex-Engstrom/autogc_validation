# -*- coding: utf-8 -*-
"""Tests for database.models — Pydantic model validation."""

import pytest
from pydantic import ValidationError

from autogc_validation.database.models import Site, MDL, SiteCanister
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


class TestMDLDateOff:
    def test_active_mdl_no_date_off(self):
        """MDL with no date_off represents a currently-active MDL."""
        mdl = MDL(
            site_id=1, aqs_code=45201, concentration=0.05,
            date_on="2025-01-01 00:00:00",
        )
        assert mdl.date_off is None

    def test_retired_mdl_with_date_off(self):
        mdl = MDL(
            site_id=1, aqs_code=45201, concentration=0.05,
            date_on="2025-01-01 00:00:00", date_off="2026-01-01 00:00:00",
        )
        assert mdl.date_off == "2026-01-01 00:00:00"

    def test_date_off_before_date_on_raises(self):
        with pytest.raises(ValidationError):
            MDL(
                site_id=1, aqs_code=45201, concentration=0.05,
                date_on="2026-01-01 00:00:00", date_off="2025-01-01 00:00:00",
            )


class TestSiteCanisterIsActive:
    def test_active_when_no_date_off(self):
        sc = SiteCanister(
            site_canister_id="SC-001", site_id=1,
            primary_canister_id="CAN-001", dilution_ratio=0.5,
            blend_date="2025-01-01 00:00:00", date_on="2025-01-01 00:00:00",
        )
        assert sc.is_active is True

    def test_inactive_when_date_off_set(self):
        sc = SiteCanister(
            site_canister_id="SC-001", site_id=1,
            primary_canister_id="CAN-001", dilution_ratio=0.5,
            blend_date="2025-01-01 00:00:00", date_on="2025-01-01 00:00:00",
            date_off="2026-01-01 00:00:00",
        )
        assert sc.is_active is False


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
