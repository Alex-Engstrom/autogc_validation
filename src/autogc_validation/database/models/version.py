# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 16:41:45 2026

@author: aengstrom
"""
from dataclasses import dataclass
from .base import BaseModel
@dataclass
class Version(BaseModel):
    version: int
    applied_on: str
    
    __tablename__ = "SchemaVersion"