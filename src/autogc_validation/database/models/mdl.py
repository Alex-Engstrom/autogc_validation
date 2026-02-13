# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 15:38:12 2026

@author: aengstrom
"""
from pydantic.dataclasses import dataclass
from pydantic import field_validator, model_validator
from .base import BaseModel
from autogc_validation.database.enums import CompoundAQSCode

@dataclass
class MDL(BaseModel):
    """
    Method Detection Limit for a compound at a site.

    Attributes:
        site_id: Site identifier
        aqs_code: Compound AQS code
        concentration: MDL concentration in ppbv
        date_on: Date this MDL became effective
        date_off: Date this MDL was superseded
    """
    site_id: int
    aqs_code: CompoundAQSCode
    concentration: float
    date_on: str
    date_off: str

    __tablename__ = "mdls"

    __table_sql__ = """
                    CREATE TABLE IF NOT EXISTS mdls (
                        site_id INTEGER,
                        aqs_code INTEGER,
                        concentration REAL,
                        date_on TEXT,
                        date_off TEXT,
                        PRIMARY KEY (site_id, aqs_code, date_on),
                        FOREIGN KEY (site_id) REFERENCES sites(site_id),
                        FOREIGN KEY (aqs_code) REFERENCES voc_info(aqs_code)
                    );
                    """

    @field_validator('concentration')
    @classmethod
    def validate_concentration(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"concentration cannot be negative, got {v}")
        return v

    @field_validator('date_on', 'date_off')
    @classmethod
    def validate_date(cls, v: str) -> str:
        return BaseModel.validate_date_format(v)

    @model_validator(mode='after')
    def validate_date_order(self) -> 'MDL':
        """Validate that date_on is before date_off."""
        on = BaseModel.parse_date(self.date_on)
        off = BaseModel.parse_date(self.date_off)

        if on >= off:
            raise ValueError("date_on must be before date_off")

        return self
