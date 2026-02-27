# -*- coding: utf-8 -*-
"""
Visualization functions for station room temperature QC.
"""
import matplotlib.pyplot as plt

from autogc_validation.qc.room_temp import StationTempResult, check_station_temp


def plot_station_temp(
    station_name: str,
    month: int,
    year: int,
    upper_threshold: float = 25,
    lower_threshold: float = 16,
) -> StationTempResult:
    result = check_station_temp(
        station_name=station_name,
        month=month,
        year=year,
        upper_threshold=upper_threshold,
        lower_threshold=lower_threshold,
    )
    ax = result.temperatures.plot(color="green", label="Acceptable")
    if not result.flagged.empty:
        result.flagged.plot(ax=ax, color="red", marker="o", linestyle="none", label="Out of range")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title(f"{station_name} — Room Temperature {year}-{month:02d}")
    ax.axhline(upper_threshold, color="red", linestyle="--", linewidth=0.8, label=f"Upper ({upper_threshold}°C)")
    ax.axhline(lower_threshold, color="red", linestyle="--", linewidth=0.8, label=f"Lower ({lower_threshold}°C)")
    ax.legend()
    plt.tight_layout()
    return result
