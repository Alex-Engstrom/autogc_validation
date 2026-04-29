# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 14:13:39 2026

@author: aengstrom
"""
from autogc_validation.database.enums import CALIBRANT_COMPOUNDS
from autogc_validation.database.operations import (get_primary_canister_concentrations, 
                                                    evaluate_calibration, 
                                                    ColumnResult, 
                                                    CalibrationResult)
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)



def calculate_rfs(calibration_runs: pd.DataFrame, dilution_ratios: list = None, calibration_canister: str = None, database: str = None) ->pd.DataFrame:
    columns =  CALIBRANT_COMPOUNDS
    calibrant_df = calibration_runs.set_index("sample_type_long")[columns]
    concentrations = get_primary_canister_concentrations(database = database, canister_id = calibration_canister, output_unit = "ppbC")
    
    conc_series = concentrations.iloc[0][columns]
    conc_df = pd.DataFrame(
        np.outer(dilution_ratios, conc_series.values),
        index=calibrant_df.index,
        columns=columns,
    )
    rf_df = calibrant_df / conc_df
    return calibrant_df, conc_df, rf_df