# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 09:16:28 2026

@author: aengstrom
"""

from autogc_validation.database.models.calibration import Calibration
import statistics as stats
import numpy as np
from sklearn.linear_model import LinearRegression
def _calculate_RF(area: float, concentration: float) -> float:
    return area/concentration

def _calculate_rsd(rfs: list) -> float:
    stdev = stats.stdev(rfs)
    avg = stats.mean(rfs)
    rsd = stdev/avg*100
    return rsd

def _compare_to_regression(data: list[tuple]) -> dict:
    conc, area = zip(*data)
    conc1 =  np.array(conc).reshape(-1, 1)
    area1 = np.array(area)
    reg1 = LinearRegression().fit(conc1, area1)

    slope = reg1.coef_[0]
    intercept = reg1.intercept_
    r2 = reg1.score(conc1, area1)
    rfs_actual = [_calculate_RF(ar, con) for con, ar in data]
    rsd = _calculate_rsd(rfs_actual)
    conc2 =  np.array(conc)
    area2 = np.array(area).reshape(-1, 1)    
    reg2 = LinearRegression().fit(area2, conc2)
    rfs_regression = reg2.predict(area2)
    conc_dev = (rfs_regression / conc2)*100 
    y_int_slope = abs(intercept/slope)
    return {"rfs": list(rfs_actual), 
            "rsd": 
            "slope": float(slope), 
            "intercept": float(intercept),
            "r2": float(r2), 
            "abs_int_slope": float(y_int_slope),
            
            "regression_comparison": {level: float(comp) for level, comp in zip(["L1","L2","L3","L4"], conc_dev)}}
    
    