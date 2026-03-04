# -*- coding: utf-8 -*-
"""
QC recovery time-series and distribution plots for AutoGC validation.

Provides a two-panel calibrant/endpoint time-series and a box-and-whisker
distribution plot for CVS, LCS, and RTS recovery data.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from autogc_validation.database.enums import (
    ColumnType,
    aqs_to_name,
    get_codes_by_column,
    name_to_aqs,
)
from autogc_validation.qc.recovery import compute_recovery
from autogc_validation.qc.utils import get_compound_cols

# Highlight compounds shown in the recovery time-series.
# Format: (calibrant, lightest, heaviest) — looked up via name_to_aqs at call time.
_PLOT_HIGHLIGHT_NAMES = ("Propane", "Ethane", "1-Hexene")

_BP_HIGHLIGHT_NAMES: dict[str, tuple[str, str, str]] = {
    "CVS": ("Toluene", "N-hexane", "p-Diethylbenzene"),
    "LCS": ("Toluene", "N-hexane", "p-Diethylbenzene"),
    "RTS": ("Toluene", "N-hexane", "N-dodecane"),
}

_RECOVERY_LOWER = 70.0
_RECOVERY_UPPER = 130.0

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

_LAYOUT_STYLE = dict(plot_bgcolor="white", paper_bgcolor="white")


def _apply_theme(fig: go.Figure) -> None:
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)
    fig.update_layout(**_LAYOUT_STYLE)


def _resolve_highlight_codes(
    names: tuple[str, str, str],
    available: set[int],
) -> list[tuple[int, str]]:
    """Convert compound name strings to (code, label) pairs, skipping unknowns."""
    result = []
    for name in names:
        try:
            code = name_to_aqs(name)
            if code in available:
                result.append((code, aqs_to_name(code)))
        except (KeyError, ValueError):
            pass
    return result


def _ordered_codes(available: set[int]) -> list[int]:
    """Return *available* codes in PLOT-then-BP elution order."""
    return [
        c for c in
        get_codes_by_column(ColumnType.PLOT) + get_codes_by_column(ColumnType.BP)
        if c in available
    ]


def plot_recovery_timeseries(
    qc_df: pd.DataFrame,
    canister_periods: pd.DataFrame,
    qc_type: str,
    sitename: str,
    year: int,
    month: int,
    plot_highlight_names: tuple[str, str, str] | None = None,
    bp_highlight_names: tuple[str, str, str] | None = None,
) -> None:
    """Plot a two-panel recovery time-series for selected PLOT and BP compounds.

    The top panel shows PLOT-column recovery (calibrant + lightest + heaviest
    compound by default).  The bottom panel shows the same for BP.  This
    gives a focused view of column health without the clutter of all compounds.

    Reference lines are drawn at 70%, 100%, and 130% recovery.

    Args:
        qc_df: Typed QC concentration DataFrame (Dataset.cvs / .lcs / .rts).
        canister_periods: Expected concentrations from get_canister_periods.
        qc_type: Label — 'CVS', 'LCS', or 'RTS'.
        sitename: Site name string for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.
        plot_highlight_names: Override the default PLOT highlight triple
            (calibrant, lightest, heaviest) as compound name strings.
        bp_highlight_names: Override the default BP highlight triple.
    """
    if qc_df.empty:
        print(f"No {qc_type} samples to plot.")
        return

    recovery_df = compute_recovery(qc_df, canister_periods)
    compound_cols = set(get_compound_cols(recovery_df))

    plot_names = plot_highlight_names or _PLOT_HIGHLIGHT_NAMES
    bp_names = bp_highlight_names or _BP_HIGHLIGHT_NAMES.get(qc_type, _PLOT_HIGHLIGHT_NAMES)

    plot_highlights = _resolve_highlight_codes(plot_names, compound_cols)
    bp_highlights = _resolve_highlight_codes(bp_names, compound_cols)

    panels = [
        (plot_highlights, "PLOT column"),
        (bp_highlights, "BP column"),
    ]
    panels = [(codes, label) for codes, label in panels if codes]

    if not panels:
        print(f"No highlight compounds found in {qc_type} data.")
        return

    timestamps = list(recovery_df.index)
    n_panels = len(panels)
    _COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    fig = make_subplots(
        rows=n_panels, cols=1,
        shared_xaxes=True,
        subplot_titles=[label for _, label in panels],
        vertical_spacing=0.15 / max(n_panels, 1),
    )

    for panel_idx, (highlights, _) in enumerate(panels):
        row = panel_idx + 1
        for i, (code, label) in enumerate(highlights):
            y = recovery_df[code].tolist() if code in recovery_df.columns else [None] * len(timestamps)
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=y,
                    mode="lines+markers",
                    name=label,
                    line=dict(color=_COLORS[i % len(_COLORS)], width=1.8),
                    marker=dict(size=7),
                    hovertemplate=(
                        f"<b>{label}</b><br>"
                        "Date: %{x|%Y-%m-%d %H:%M}<br>"
                        "Recovery: %{y:.1f}%<extra></extra>"
                    ),
                    legendgroup=label,
                    showlegend=(panel_idx == 0),
                ),
                row=row, col=1,
            )

        fig.add_hline(y=100, line_color="black", line_width=0.8, row=row, col=1)
        for bound in (_RECOVERY_LOWER, _RECOVERY_UPPER):
            fig.add_hline(y=bound, line_color="red", line_width=0.8,
                          line_dash="dash", row=row, col=1)
        fig.add_hrect(y0=_RECOVERY_LOWER, y1=_RECOVERY_UPPER,
                      fillcolor="green", opacity=0.05,
                      layer="below", line_width=0, row=row, col=1)
        fig.update_yaxes(title_text="Recovery (%)", row=row, col=1)

    fig.update_xaxes(title_text="Date", row=n_panels, col=1)
    fig.update_layout(
        title=f"{sitename} {year}-{month:02d} {qc_type} Recovery — Key Compounds",
        height=380 * n_panels,
        hovermode="closest",
    )
    _apply_theme(fig)
    fig.show()


def plot_recovery_boxplot(
    qc_df: pd.DataFrame,
    canister_periods: pd.DataFrame,
    qc_type: str,
    sitename: str,
    year: int,
    month: int,
) -> None:
    """Plot a box-and-whisker distribution of recovery for all QC compounds.

    One box per compound, in PLOT-then-BP elution order.  Compounds with
    fewer than two data points are shown as individual markers.  Reference
    lines at 70%, 100%, and 130% are drawn across the full plot.

    Args:
        qc_df: Typed QC concentration DataFrame (Dataset.cvs / .lcs / .rts).
        canister_periods: Expected concentrations from get_canister_periods.
        qc_type: Label — 'CVS', 'LCS', or 'RTS'.
        sitename: Site name string for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.
    """
    if qc_df.empty:
        print(f"No {qc_type} samples to plot.")
        return

    recovery_df = compute_recovery(qc_df, canister_periods)
    compound_cols = set(get_compound_cols(recovery_df))
    ordered = _ordered_codes(compound_cols)

    if not ordered:
        print(f"No compounds to plot for {qc_type}.")
        return

    plot_set = set(get_codes_by_column(ColumnType.PLOT))
    fig = go.Figure()

    for code in ordered:
        values = recovery_df[code].dropna().tolist()
        name = aqs_to_name(code)
        color = "#1f77b4" if code in plot_set else "#ff7f0e"
        fig.add_trace(go.Box(
            y=values,
            name=name,
            marker_color=color,
            line_color=color,
            boxpoints="all",
            jitter=0.3,
            pointpos=0,
            hovertemplate=f"<b>{name}</b><br>Recovery: %{{y:.1f}}%<extra></extra>",
        ))

    fig.add_hline(y=100, line_color="black", line_width=0.8)
    for bound in (_RECOVERY_LOWER, _RECOVERY_UPPER):
        fig.add_hline(y=bound, line_color="red", line_width=0.8, line_dash="dash")
    fig.add_hrect(y0=_RECOVERY_LOWER, y1=_RECOVERY_UPPER,
                  fillcolor="green", opacity=0.05, layer="below", line_width=0)

    fig.update_layout(
        title=f"{sitename} {year}-{month:02d} {qc_type} Recovery Distribution",
        yaxis_title="Recovery (%)",
        xaxis_title="Compound (PLOT = blue, BP = orange)",
        height=500,
        showlegend=False,
        **_LAYOUT_STYLE,
    )
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)
    fig.show()
