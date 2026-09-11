# -*- coding: utf-8 -*-
"""
Visualization functions for station room temperature QC.
"""
import matplotlib.pyplot as plt

from autogc_validation.qc.room_temp import StationTempResult


def plot_station_temp(
    result: StationTempResult,
    station_name: str,
    month: int,
    year: int,
    upper_threshold: float = 30,
    lower_threshold: float = 20,
) -> plt.Figure:
    """Plot a station's temperature series with acceptable-range thresholds.

    Takes a precomputed :class:`StationTempResult` (from
    ``qc.room_temp.check_station_temp``) rather than querying AirVision
    itself, so the same result can be reused for both plotting and
    downstream null-qualifier generation without a second query.

    Returns:
        The Matplotlib Figure.
    """
    fig, ax = plt.subplots()
    result.temperatures.plot(ax=ax, color="green", label="Acceptable")
    if not result.flagged.empty:
        result.flagged.plot(ax=ax, color="red", marker="o", linestyle="none", label="Out of range")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title(f"{station_name} — Room Temperature {year}-{month:02d}")
    ax.axhline(upper_threshold, color="red", linestyle="--", linewidth=0.8, label=f"Upper ({upper_threshold}°C)")
    ax.axhline(lower_threshold, color="red", linestyle="--", linewidth=0.8, label=f"Lower ({lower_threshold}°C)")
    ax.legend()
    fig.tight_layout()
    plt.close(fig)
    return fig
