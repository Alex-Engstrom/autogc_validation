# -*- coding: utf-8 -*-
"""
Calibration regression analysis and evaluation.

Fits a linear regression to multi-level calibration data and evaluates
how well each level's measured area conforms to the fitted curve.
"""

from dataclasses import dataclass

import numpy as np
import statistics as stats
from sklearn.linear_model import LinearRegression

from autogc_validation.database.models.calibration import Calibration

_LEVELS = ("L1", "L2", "L3", "L4")

CalData = list[tuple[float, float]]  # (concentration, area) pairs


@dataclass
class ColumnResult:
    """Regression analysis result for a single GC column (PLOT or BP)."""
    rfs: list[float]
    rsd: float
    slope: float
    intercept: float
    r2: float
    abs_int_slope: float
    pct_deviation: dict[str, float]


@dataclass
class CalibrationResult:
    """Regression analysis results for a full calibration run."""
    date_run: str
    PLOT: ColumnResult
    BP: ColumnResult


def _calculate_rf(area: float, concentration: float) -> float:
    return area / concentration


def _calculate_rsd(rfs: list[float]) -> float:
    return stats.stdev(rfs) / stats.mean(rfs) * 100


def _compare_to_regression(data: CalData) -> ColumnResult:
    """Fit a linear regression to (conc, area) pairs and evaluate each level.

    Fits conc → area to get slope, intercept, and R². Then fits the inverse
    (area → conc) and computes percent deviation of each predicted concentration
    from its nominal value: (predicted − actual) / actual × 100.
    """
    conc, area = zip(*data)

    conc_arr = np.array(conc).reshape(-1, 1)
    area_arr = np.array(area)
    reg = LinearRegression().fit(conc_arr, area_arr)

    slope = reg.coef_[0]
    intercept = reg.intercept_
    r2 = reg.score(conc_arr, area_arr)

    rfs = [_calculate_rf(ar, con) for con, ar in data]
    rsd = _calculate_rsd(rfs)

    area_col = np.array(area).reshape(-1, 1)
    conc_col = np.array(conc)
    inv_reg = LinearRegression().fit(area_col, conc_col)
    predicted_conc = inv_reg.predict(area_col)
    pct_deviation = (predicted_conc - conc_col) / conc_col * 100

    return ColumnResult(
        rfs=rfs,
        rsd=float(rsd),
        slope=float(slope),
        intercept=float(intercept),
        r2=float(r2),
        abs_int_slope=float(abs(intercept / slope)),
        pct_deviation={level: float(dev) for level, dev in zip(_LEVELS, pct_deviation)},
    )


def evaluate_calibration(cal: Calibration) -> CalibrationResult:
    """Run regression analysis on a Calibration record.

    Evaluates both the PLOT and BP columns independently and returns
    typed ColumnResult objects for each.
    """
    plot_data: CalData = [
        (cal.l1_conc_PLOT, cal.l1_area_PLOT),
        (cal.l2_conc_PLOT, cal.l2_area_PLOT),
        (cal.l3_conc_PLOT, cal.l3_area_PLOT),
        (cal.l4_conc_PLOT, cal.l4_area_PLOT),
    ]
    bp_data: CalData = [
        (cal.l1_conc_BP, cal.l1_area_BP),
        (cal.l2_conc_BP, cal.l2_area_BP),
        (cal.l3_conc_BP, cal.l3_area_BP),
        (cal.l4_conc_BP, cal.l4_area_BP),
    ]
    return CalibrationResult(
        date_run=cal.date_run,
        PLOT=_compare_to_regression(plot_data),
        BP=_compare_to_regression(bp_data),
    )
