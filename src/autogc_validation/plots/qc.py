# -*- coding: utf-8 -*-
"""
Interactive QC sample plots for AutoGC validation (Plotly).

Provides recovery time-series plots for CVS, LCS, and RTS standards and a
concentration time-series plot for blank samples. All plots render inline in
JupyterLab with hover tooltips showing compound name, date, and value.
"""

import numpy as np
import pandas as pd
import plotly.colors
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from autogc_validation.database.enums import (
    ColumnType,
    CompoundAQSCode,
    aqs_to_name,
    get_codes_by_column,
)
from autogc_validation.qc.utils import align_period_index, get_compound_cols

_TNMHC_CODE = CompoundAQSCode.C_TNMHC
_COLORS = plotly.colors.qualitative.Light24

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

_LAYOUT_STYLE = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
)


def _apply_theme(fig: go.Figure) -> None:
    """Apply white background, black borders, no grid, and outside tick marks."""
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)
    fig.update_layout(**_LAYOUT_STYLE)


def _ordered_codes(available: set[int]) -> list[int]:
    """Return *available* codes in PLOT-then-BP elution order."""
    return [
        c for c in get_codes_by_column(ColumnType.PLOT) + get_codes_by_column(ColumnType.BP)
        if c in available
    ]


def _split_by_column(codes: list[int]) -> tuple[list[int], list[int]]:
    """Split a code list into (PLOT, BP) groups preserving elution order."""
    plot_set = set(get_codes_by_column(ColumnType.PLOT))
    return (
        [c for c in codes if c in plot_set],
        [c for c in codes if c not in plot_set],
    )


def _color(i: int) -> str:
    return _COLORS[i % len(_COLORS)]


def plot_qc_recovery(
    qc_df: pd.DataFrame,
    canister_periods: pd.DataFrame,
    qc_type: str,
    sitename: str,
    year: int,
    month: int,
) -> None:
    """Plot recovery percentages over time for a QC standard (CVS, LCS, or RTS).

    Produces an interactive Plotly figure with PLOT-column compounds in the top
    panel and BP-column compounds in the bottom panel (panels with no compounds
    are omitted). Hover to see compound name, date, and recovery percentage.
    Click legend entries to show or hide individual compounds.

    Args:
        qc_df: Typed QC concentration DataFrame — DatetimeIndex, integer AQS
            code columns, filename column. E.g. Dataset.cvs.
        canister_periods: Wide DataFrame indexed by effective date with AQS
            codes as columns (expected concentrations after dilution), as
            returned by get_canister_periods.
        qc_type: Label for the standard type ('CVS', 'LCS', or 'RTS').
        sitename: Site name string for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.
    """
    if qc_df.empty:
        print(f"No {qc_type} samples to plot.")
        return

    canister_codes = {
        c for c in canister_periods.columns
        if isinstance(c, int) and canister_periods[c].notna().any()
    }
    data_codes = set(get_compound_cols(qc_df))
    plot_codes = _ordered_codes(canister_codes & data_codes)

    if not plot_codes:
        print(f"No compounds in common between {qc_type} data and canister standard.")
        return

    period_indices = align_period_index(qc_df, canister_periods)
    timestamps = list(qc_df.index)

    recoveries: dict[int, list[float]] = {c: [] for c in plot_codes}
    for i, (_, row) in enumerate(qc_df.iterrows()):
        expected = canister_periods.iloc[period_indices[i]]
        for code in plot_codes:
            obs = row.get(code)
            exp = expected.get(code)
            if pd.isna(obs) or pd.isna(exp) or float(exp) == 0:
                recoveries[code].append(None)
            else:
                recoveries[code].append(round(float(obs) / float(exp) * 100.0, 2))

    plot_grp, bp_grp = _split_by_column(plot_codes)
    panels = [(grp, lbl) for grp, lbl in [(plot_grp, "PLOT"), (bp_grp, "BP")] if grp]
    n_panels = len(panels)

    fig = make_subplots(
        rows=n_panels, cols=1,
        shared_xaxes=True,
        subplot_titles=[lbl for _, lbl in panels],
        vertical_spacing=0.12 / n_panels if n_panels > 1 else 0,
    )

    for panel_idx, (grp, _) in enumerate(panels):
        row = panel_idx + 1
        for i, code in enumerate(grp):
            name = aqs_to_name(code)
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=recoveries[code],
                    mode="lines+markers",
                    name=name,
                    line=dict(color=_color(i), width=1.5),
                    marker=dict(size=6),
                    hovertemplate=(
                        f"<b>{name}</b><br>"
                        "Date: %{x|%Y-%m-%d %H:%M}<br>"
                        "Recovery: %{y:.1f}%"
                        "<extra></extra>"
                    ),
                ),
                row=row, col=1,
            )

        # Reference lines and acceptance band.
        fig.add_hline(y=100, line_color="black", line_width=0.8, row=row, col=1)
        fig.add_hline(y=70,  line_color="red", line_width=0.8, line_dash="dash", row=row, col=1)
        fig.add_hline(y=130, line_color="red", line_width=0.8, line_dash="dash", row=row, col=1)
        fig.add_hrect(y0=70, y1=130, fillcolor="green", opacity=0.05,
                      layer="below", line_width=0, row=row, col=1)

        fig.update_yaxes(title_text="Recovery (%)", row=row, col=1)

    fig.update_xaxes(title_text="Date", row=n_panels, col=1)
    fig.update_layout(
        title=f"{sitename} {year}-{month:02d} {qc_type} Recovery",
        height=420 * n_panels,
        hovermode="closest",
        legend=dict(tracegroupgap=0),
    )
    _apply_theme(fig)
    fig.show()


def plot_blank_concentrations(
    blank_df: pd.DataFrame,
    mdl_failures: pd.DataFrame,
    sitename: str,
    year: int,
    month: int,
) -> None:
    """Plot blank sample concentrations over time for compounds with MDL exceedances.

    Compounds with at least one MDL exceedance are plotted as time series on
    the left y-axis (in elution order). TNMHC is plotted on a secondary right
    y-axis. Hover to see compound name, date, and concentration.

    Args:
        blank_df: Blank concentration DataFrame — DatetimeIndex, integer AQS
            code columns, filename column. E.g. Dataset.blanks.
        mdl_failures: Wide boolean DataFrame from compounds_above_mdl — 1 where
            MDL exceeded. Columns: filename + integer AQS codes.
        sitename: Site name string for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.
    """
    if blank_df.empty:
        print("No blank samples to plot.")
        return

    fail_codes = {
        c for c in mdl_failures.columns
        if isinstance(c, int) and (mdl_failures[c] == 1).any()
    }
    if not fail_codes:
        print("No MDL exceedances found — nothing to plot.")
        return

    plot_codes = _ordered_codes(fail_codes & set(blank_df.columns))
    has_tnmhc = _TNMHC_CODE in blank_df.columns
    timestamps = list(blank_df.index)

    fig = make_subplots(specs=[[{"secondary_y": has_tnmhc}]])

    for i, code in enumerate(plot_codes):
        name = aqs_to_name(code)
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=blank_df[code].tolist(),
                mode="lines+markers",
                name=name,
                line=dict(color=_color(i), width=1.5),
                marker=dict(size=6),
                hovertemplate=(
                    f"<b>{name}</b><br>"
                    "Date: %{x|%Y-%m-%d %H:%M}<br>"
                    "Concentration: %{y:.4f} ppbC"
                    "<extra></extra>"
                ),
            ),
            secondary_y=False,
        )

    if has_tnmhc:
        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=blank_df[_TNMHC_CODE].tolist(),
                mode="lines+markers",
                name="TNMHC",
                line=dict(color="black", width=1.5, dash="dash"),
                marker=dict(symbol="diamond", size=7),
                hovertemplate=(
                    "<b>TNMHC</b><br>"
                    "Date: %{x|%Y-%m-%d %H:%M}<br>"
                    "TNMHC: %{y:.3f} ppbC"
                    "<extra></extra>"
                ),
            ),
            secondary_y=True,
        )
        fig.update_yaxes(title_text="TNMHC (ppbC)", secondary_y=True)

    fig.update_yaxes(title_text="Concentration (ppbC)", secondary_y=False)
    fig.update_xaxes(title_text="Date")
    fig.update_layout(
        title=f"{sitename} {year}-{month:02d} Blank Concentrations — compounds above MDL",
        height=500,
        hovermode="closest",
    )
    _apply_theme(fig)
    fig.show()
