# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 16:41:45 2026

@author: aengstrom
"""
from pydantic.dataclasses import dataclass
from .base import BaseModel

@dataclass
class Version(BaseModel):
    version: str
    applied_on: str

    __tablename__ = "SchemaVersion"

    __table_sql__ = """
                    CREATE TABLE IF NOT EXISTS SchemaVersion (
                        version TEXT PRIMARY KEY,
                        applied_on TEXT
                    );
                    """


