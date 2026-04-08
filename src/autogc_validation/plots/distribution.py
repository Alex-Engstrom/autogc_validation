# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 10:05:26 2026

@author: aengstrom
"""

import calendar

import numpy as np
import pandas as pd
import plotly.colors
import plotly.graph_objects as go

from autogc_validation.database.enums import PLOT_CODES, aqs_to_name
from autogc_validation.qc.utils import get_compound_cols, get_ordered_codes, to_aqs_indexed_series

_LAYOUT_STYLE = dict(plot_bgcolor="white", paper_bgcolor="white", font=dict(color="black"))

_AXIS_STYLE = dict(
    showgrid=False,
    showline=True,
    linecolor="black",
    linewidth=1,
    mirror=True,
    ticks="outside",
    ticklen=5,
    tickcolor="black",
)

def plot_ambient_boxplot(
    ambient_df: pd.DataFrame,
    sitename: str,
    year: int,
    month: int,
    ) -> None:
    if ambient_df.empty:
        print("No samples to plot.")
        return
    
    compound_cols = set(get_compound_cols(ambient_df))
    ordered = get_ordered_codes(compound_cols)

    fig = go.Figure()

    for code in ordered:
        values = ambient_df[code].dropna().tolist()
        name = aqs_to_name(code)
        color = "#1f77b4" if code in PLOT_CODES else "#ff7f0e"
        fig.add_trace(go.Box(
            y=values,
            name=name,
            marker_color=color,
            line_color=color,
            boxpoints="outliers",
            marker_outliercolor="black",
            jitter=0.3,
            pointpos=0,
            marker_size=5,
            hovertemplate=f"<b>{name}</b><br>Concentration: %{{y:.2f}} ppbC<extra></extra>",
        ))

    all_names = [aqs_to_name(c) for c in ordered]
    fig.update_layout(
        title=f"{sitename} Concentrations — {calendar.month_name[month]} {year}",
        yaxis_title="Concentration (ppbC)",
        xaxis_title="Compound (PLOT = blue, BP = orange)",
        height=750,
        showlegend=False,
        **_LAYOUT_STYLE,
    )
    fig.update_xaxes(
        **_AXIS_STYLE,
        tickmode="array",
        tickvals=all_names,
        ticktext=all_names,
        tickangle=90,
    )
    fig.update_yaxes(**_AXIS_STYLE)
    fig.show()


def plot_lognormal_boxplot(
    ambient_df: pd.DataFrame,
    sitename: str,
    year: int,
    month: int,
    label: str = "",
    mdls=None,
    floor: float = 0.25,
) -> None:
    """Boxplot of log-transformed concentrations for all compounds.

    Values are clipped to a per-compound floor before log-transformation so
    that zeros and near-zero readings don't produce -inf. When *mdls* is
    provided the floor is MDL/2 for each compound, falling back to *floor*
    for any compound whose MDL is missing or zero. Useful as a quick
    diagnostic for peak misidentifications or contaminants.

    Args:
        ambient_df: Ambient-only DataFrame with AQS code columns.
        sitename: Site name for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.
        label: Optional label appended to the title (e.g. "Week 1").
        mdls: MDL values keyed by AQS code or compound name, or a
            period-indexed MDL DataFrame (first period used). Optional.
        floor: Fallback floor applied when mdls is None or a compound's
            MDL is missing or zero. Defaults to 0.25.
    """
    if ambient_df.empty:
        print("No samples to plot.")
        return

    if mdls is not None:
        mdl_series = to_aqs_indexed_series(mdls)
        mdl_series.index = mdl_series.index.map(int)
    else:
        mdl_series = None

    compound_cols = set(get_compound_cols(ambient_df))
    ordered = get_ordered_codes(compound_cols)

    fig = go.Figure()

    for code in ordered:
        raw = ambient_df[code].dropna()
        if raw.empty:
            continue
        if mdl_series is not None:
            mdl = mdl_series.get(code, None)
            compound_floor = (mdl / 2.0) if (mdl is not None and mdl > 0) else floor
        else:
            compound_floor = floor
        values = np.log(raw.clip(lower=compound_floor)).tolist()
        name = aqs_to_name(code)
        color = "#1f77b4" if code in PLOT_CODES else "#ff7f0e"
        fig.add_trace(go.Box(
            y=values,
            name=name,
            marker_color=color,
            line_color=color,
            boxpoints="outliers",
            marker_outliercolor="black",
            jitter=0.3,
            pointpos=0,
            marker_size=5,
            hovertemplate=f"<b>{name}</b><br>log(Concentration): %{{y:.2f}}<extra></extra>",
        ))

    title_suffix = f" — {label}" if label else ""
    all_names = [aqs_to_name(c) for c in ordered]
    fig.update_layout(
        title=f"{sitename} Log-Normal Concentrations — {calendar.month_name[month]} {year}{title_suffix}",
        yaxis_title="log(Concentration) [ppbC]",
        xaxis_title="Compound (PLOT = blue, BP = orange)",
        height=750,
        showlegend=False,
        **_LAYOUT_STYLE,
    )
    fig.update_xaxes(
        **_AXIS_STYLE,
        tickmode="array",
        tickvals=all_names,
        ticktext=all_names,
        tickangle=90,
    )
    fig.update_yaxes(**_AXIS_STYLE)
    fig.add_hline(y=np.log(0.5), line_dash="dash", line_color="red", line_width=1)
    fig.show()