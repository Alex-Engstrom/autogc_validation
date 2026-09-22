# -*- coding: utf-8 -*-
"""
Monthly report summary plots for AutoGC validation.

Provides figures for the monthly validation report: sample hours breakdown,
data qualification and nullification summaries, and blank TNMTC/TNMHC
time series.
"""

import calendar

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from autogc_validation.database.enums import (
    CompoundAQSCode,
    NULL_CODES,
    SampleTypeLetter,
    aqs_to_name,
)

_TNMHC_CODE = CompoundAQSCode.C_TNMHC.value
_TNMTC_CODE = CompoundAQSCode.C_TNMTC.value

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

_LAYOUT_STYLE = dict(plot_bgcolor="white", paper_bgcolor="white", font=dict(color="black"))

# Human-readable labels and colours for each sample type value.
_SAMPLE_TYPE_META: dict[str, tuple[str, str]] = {
    SampleTypeLetter.AMBIENT.value:           ("Valid Ambient",   "#2196F3"),
    SampleTypeLetter.BLANK.value:             ("Blanks",          "#FF9800"),
    SampleTypeLetter.CVS.value:               ("CVS",             "#4CAF50"),
    SampleTypeLetter.LCS.value:               ("LCS",             "#8BC34A"),
    SampleTypeLetter.RTS.value:               ("RTS",             "#CDDC39"),
    SampleTypeLetter.MDL_POINT.value:         ("MDL Point",       "#9C27B0"),
    SampleTypeLetter.CALIBRATION_POINT.value: ("Calibration",     "#E91E63"),
    SampleTypeLetter.EXPERIMENTAL.value:      ("PT/Experimental", "#795548"),
}

# Reverse map: human-readable label → SampleTypeLetter value string.
_LABEL_TO_ST_VAL: dict[str, str] = {
    label: st_val for st_val, (label, _) in _SAMPLE_TYPE_META.items()
}


def plot_monthly_hours_summary(
    ds,
    sitename: str,
    year: int,
    month: int,
    nulled_hours: int = 0,
    overrides: dict[str, int] | None = None,
) -> go.Figure:
    """Plot a donut chart breaking down sample hours by type for the month.

    Shows valid ambient, QC standards, PT/experimental, and nulled ambient
    hours.

    Args:
        ds: Dataset object (must have .data already loaded).
        sitename: Site name string for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.
        nulled_hours: Number of ambient hours nulled this month. Subtracted
            from the ambient count and shown as a separate "Nulled Non-QC"
            slice. Default 0.
        overrides: Optional dict mapping sample-type label strings to integer
            counts, replacing the values derived from *ds*.  Labels must match
            keys in _SAMPLE_TYPE_META, e.g. ``{"CVS": 4, "Blanks": 2}``.

    Returns:
        The Plotly Figure.
    """
    raw_counts: dict = ds.data["sample_type"].value_counts().to_dict()

    if overrides:
        for label, count in overrides.items():
            st_val = _LABEL_TO_ST_VAL.get(label)
            if st_val is not None:
                raw_counts[st_val] = count

    n_ambient = raw_counts.get(SampleTypeLetter.AMBIENT.value, 0)
    n_valid_ambient = max(n_ambient - nulled_hours, 0)

    labels, values, colors = [], [], []

    labels.append("Valid Ambient")
    values.append(n_valid_ambient)
    colors.append("#2196F3")

    if nulled_hours > 0:
        labels.append("Nulled Non-QC")
        values.append(nulled_hours)
        colors.append("#F44336")

    for st_val, (label, color) in _SAMPLE_TYPE_META.items():
        if st_val == SampleTypeLetter.AMBIENT.value:
            continue
        n = raw_counts.get(st_val, 0)
        if n > 0:
            labels.append(label)
            values.append(n)
            colors.append(color)

    qc_hours = sum(
        raw_counts.get(st_val, 0)
        for st_val in _SAMPLE_TYPE_META
        if st_val != SampleTypeLetter.AMBIENT.value
    )

    total_hours_in_month = calendar.monthrange(year, month)[1] * 24
    n_missing = total_hours_in_month - sum(values)
    if n_missing > 0:
        labels.append("Missing Data")
        values.append(n_missing)
        colors.append("#9E9E9E")

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        marker=dict(line=dict(color="white", width=2)),
        hole=0.45,
        texttemplate="%{label}: %{value}/%{percent:.1%}",
        textfont=dict(color="black"),
        hovertemplate="<b>%{label}</b><br>Hours: %{value}<br>%{percent}<extra></extra>",
    ))

    fig.update_layout(
        annotations=[dict(
            text=f"{total_hours_in_month}<br>hours",
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False,
        )],
        height=480,
        paper_bgcolor="white",
    )

    completeness_raw = n_valid_ambient / total_hours_in_month * 100
    denominator_qc_excl = total_hours_in_month - qc_hours
    completeness_qc_excl = (n_valid_ambient / denominator_qc_excl * 100) if denominator_qc_excl > 0 else 0.0
    print(f"Raw Data Completeness (QC included):  {completeness_raw:.1f}%")
    print(f"Data Completeness (QC excluded):       {completeness_qc_excl:.1f}%")

    return fig


def plot_qual_summary(
    all_quals: pd.DataFrame,
    sitename: str,
    year: int,
    month: int,
) -> go.Figure:
    """Plot a horizontal bar chart of data qualification by qualifier code.

    Each bar represents one qualifier code and shows the total number of
    qualifier lines (compound–interval combinations) carrying that code.
    This gives an at-a-glance picture of what proportion of the data was
    affected and by what cause.

    Args:
        all_quals: Combined qualifier DataFrame (from build_*_qualifier_lines).
            Must have a 'CODE' column.
        sitename: Site name string for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.

    Returns:
        The Plotly Figure, or an empty ``go.Figure()`` if there was no data to plot.
    """
    if all_quals.empty:
        print("No qualifiers to summarise.")
        return go.Figure()

    code_counts = all_quals["CODE"].value_counts().sort_values()

    fig = go.Figure(go.Bar(
        x=code_counts.values.tolist(),
        y=code_counts.index.tolist(),
        orientation="h",
        marker_color="#1f77b4",
        hovertemplate="<b>%{y}</b><br>Lines: %{x}<extra></extra>",
    ))

    fig.update_layout(
        xaxis_title="Number of qualifier lines",
        yaxis_title="Qualifier code",
        height=max(300, 60 * len(code_counts)),
        **_LAYOUT_STYLE,
    )
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)
    return fig


def plot_null_summary(
    all_quals: pd.DataFrame,
    ds,
    sitename: str,
    year: int,
    month: int,
) -> go.Figure:
    """Plot a bar chart of nulled ambient hours by nullification reason.

    Expands each null qualifier interval (any code in NULL_CODES, e.g.
    AS/AE) to individual hours, intersects with ambient sample timestamps,
    and reports totals grouped by qualifier code and reason.

    Args:
        all_quals: Combined qualifier DataFrame.
        ds: Dataset object.
        sitename: Site name string for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.

    Returns:
        The Plotly Figure, or an empty ``go.Figure()`` if there was no data to plot.
    """
    null_df = all_quals[all_quals["CODE"].isin(NULL_CODES)] if not all_quals.empty else pd.DataFrame()

    if null_df.empty:
        print("No null qualifiers found — no nulled hours to summarise.")
        return go.Figure()

    ambient_ts = set(ds.ambient.index)
    rows = []
    for _, row in null_df.iterrows():
        try:
            start = pd.Timestamp(f"{row['startdate']} {row['starthour']}")
            end = pd.Timestamp(f"{row['enddate']} {row['endhour']}")
            n_hours = sum(
                1 for ts in pd.date_range(start, end, freq="h") if ts in ambient_ts
            )
        except Exception:
            n_hours = 0

        reason = row.get("COMPOUND(S) or WHOLE HOUR(S) - REASON", row["CODE"])
        rows.append({"code": row["CODE"], "reason": reason, "hours": n_hours})

    summary = (
        pd.DataFrame(rows)
        .groupby(["code", "reason"])["hours"]
        .sum()
        .reset_index()
        .sort_values("hours", ascending=True)
    )

    labels = [f"{r['code']}: {r['reason']}" for _, r in summary.iterrows()]

    fig = go.Figure(go.Bar(
        x=summary["hours"].tolist(),
        y=labels,
        orientation="h",
        hovertemplate="<b>%{y}</b><br>Nulled ambient hours: %{x}<extra></extra>",
    ))

    fig.update_layout(
        xaxis_title="Nulled ambient hours",
        yaxis_title="",
        height=max(300, 60 * len(summary)),
        **_LAYOUT_STYLE,
    )
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)
    return fig


def plot_null_donut(
    nulled_by_code: dict[str, int],
    sitename: str,
    year: int,
    month: int,
) -> go.Figure:
    """Plot a donut chart of nulled ambient hours by null qualifier code.

    Each slice represents one qualifier code (e.g. AS, AE) and its associated
    nulled ambient hours. If no codes have any hours, a message is printed and
    the function returns without plotting.

    Args:
        nulled_by_code: Mapping of qualifier code → number of nulled ambient hours.
            Zero-valued entries are silently skipped.
        sitename: Site name string for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.

    Returns:
        The Plotly Figure, or an empty ``go.Figure()`` if there was no data to plot.
    """
    labels, values = [], []
    for code, hrs in nulled_by_code.items():
        if hrs > 0:
            labels.append(code)
            values.append(hrs)

    if not labels:
        print("No nulled hours to plot.")
        return go.Figure()

    total = sum(values)

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        marker=dict(line=dict(color="white", width=2)),
        hole=0.45,
        texttemplate="%{label}: %{value}/%{percent:.1%}",
        textfont=dict(color="black"),
        hovertemplate="<b>%{label}</b><br>Hours: %{value}<br>%{percent}<extra></extra>",
    ))

    fig.update_layout(
        annotations=[dict(
            text=f"{total}<br>nulled",
            x=0.5, y=0.5,
            font_size=14,
            showarrow=False,
        )],
        height=420,
        paper_bgcolor="white",
    )
    return fig


def plot_blank_totals(
    ds,
    sitename: str,
    year: int,
    month: int,
) -> go.Figure:
    """Plot blank TNMTC and TNMHC concentrations over the month.

    Both total columns are shown on the same axis. If neither column is
    present in the blank DataFrame, a message is printed and the function
    returns without plotting.

    Args:
        ds: Dataset object (uses ds.blanks).
        sitename: Site name string for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.

    Returns:
        The Plotly Figure, or an empty ``go.Figure()`` if there was no data to plot.
    """
    blank_df = ds.blanks
    if blank_df.empty:
        print("No blank samples to plot.")
        return go.Figure()

    series_to_plot = []
    for code, color, dash in [
        (_TNMTC_CODE, "#1f77b4", "solid"),
        (_TNMHC_CODE, "#ff7f0e", "dash"),
    ]:
        if code in blank_df.columns:
            name = aqs_to_name(code)
            series_to_plot.append((code, name, color, dash))

    if not series_to_plot:
        print("Neither TNMTC nor TNMHC found in blank samples.")
        return go.Figure()

    timestamps = list(blank_df.index)
    fig = go.Figure()

    for code, name, color, dash in series_to_plot:
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=blank_df[code].tolist(),
            mode="lines+markers",
            name=name,
            line=dict(color=color, width=1.8, dash=dash),
            marker=dict(size=7),
            hovertemplate=(
                f"<b>{name}</b><br>"
                "Date: %{x|%Y-%m-%d %H:%M}<br>"
                "Concentration: %{y:.4f} ppbC<extra></extra>"
            ),
        ))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Concentration (ppbC)",
        height=420,
        hovermode="closest",
        **_LAYOUT_STYLE,
    )
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)
    return fig
