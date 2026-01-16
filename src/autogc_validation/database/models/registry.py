# -*- coding: utf-8 -*-
"""
Created on Fri Jan 16 16:35:59 2026

@author: aengstrom
"""
from typing import Dict, Type
from .canister import PrimaryCanister, CanisterConcentration, SiteCanister
from .site import Site
from .mdl import MDL
from .voc import VOCInfo
from .version import Version

MODEL_REGISTRY: Dict[str, Type] = {
    Site.__tablename__: Site,
    VOCInfo.__tablename__: VOCInfo,
    PrimaryCanister.__tablename__: PrimaryCanister,
    CanisterConcentration.__tablename__: CanisterConcentration,
    SiteCanister.__tablename__: SiteCanister,
    MDL.__tablename__: MDL,
    Version.__tablename__: Version,
}
