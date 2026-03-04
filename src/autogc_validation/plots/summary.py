# -*- coding: utf-8 -*-
"""
Monthly report summary plots for AutoGC validation.

Provides figures for the monthly validation report: sample hours breakdown,
data qualification and nullification summaries, and blank TNMTC/TNMHC
time series.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from autogc_validation.database.enums import CompoundAQSCode, SampleType, aqs_to_name

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

_LAYOUT_STYLE = dict(plot_bgcolor="white", paper_bgcolor="white")

# Human-readable labels and colours for each sample type value.
_SAMPLE_TYPE_META: dict[str, tuple[str, str]] = {
    SampleType.AMBIENT.value:           ("Valid Ambient",   "#2196F3"),
    SampleType.BLANK.value:             ("Field Blank",     "#FF9800"),
    SampleType.CVS.value:               ("CVS",             "#4CAF50"),
    SampleType.LCS.value:               ("LCS",             "#8BC34A"),
    SampleType.RTS.value:               ("RTS",             "#CDDC39"),
    SampleType.MDL_POINT.value:         ("MDL Point",       "#9C27B0"),
    SampleType.CALIBRATION_POINT.value: ("Calibration",     "#E91E63"),
    SampleType.EXPERIMENTAL.value:      ("PT/Experimental", "#795548"),
}

# Null qualifier codes (these nullify data, unlike flag qualifiers).
_NULL_CODES = frozenset({"AS", "AE"})


def _expand_null_hours(null_df: pd.DataFrame) -> set[pd.Timestamp]:
    """Expand qualifier null intervals into a set of hourly timestamps."""
    nulled: set[pd.Timestamp] = set()
    for _, row in null_df.iterrows():
        try:
            start = pd.Timestamp(f"{row['startdate']} {row['starthour']}")
            end = pd.Timestamp(f"{row['enddate']} {row['endhour']}")
            for ts in pd.date_range(start, end, freq="h"):
                nulled.add(ts)
        except Exception:
            pass
    return nulled


def plot_monthly_hours_summary(
    ds,
    all_quals: pd.DataFrame,
    sitename: str,
    year: int,
    month: int,
) -> None:
    """Plot a donut chart breaking down sample hours by type for the month.

    Shows valid ambient, QC standards, PT/experimental, and nulled ambient
    hours.  Nulled ambient hours are estimated by intersecting the null
    qualifier intervals (AS/AE codes) with ambient sample timestamps.

    Args:
        ds: Dataset object (must have .data and .ambient already loaded).
        all_quals: Combined qualifier DataFrame from the MDVR workflow.
            Must have columns: CODE, startdate, starthour, enddate, endhour.
        sitename: Site name string for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.
    """
    counts = ds.data["sample_type"].value_counts()

    # Determine nulled ambient hours.
    null_df = all_quals[all_quals["CODE"].isin(_NULL_CODES)] if not all_quals.empty else pd.DataFrame()
    nulled_ts = _expand_null_hours(null_df)
    ambient_ts = set(ds.ambient.index)
    n_nulled = len(nulled_ts & ambient_ts)
    n_valid_ambient = counts.get(SampleType.AMBIENT.value, 0) - n_nulled

    labels, values, colors = [], [], []

    labels.append("Valid Ambient")
    values.append(max(n_valid_ambient, 0))
    colors.append("#2196F3")

    if n_nulled > 0:
        labels.append("Nulled Ambient")
        values.append(n_nulled)
        colors.append("#F44336")

    for st_val, (label, color) in _SAMPLE_TYPE_META.items():
        if st_val == SampleType.AMBIENT.value:
            continue
        n = counts.get(st_val, 0)
        if n > 0:
            labels.append(label)
            values.append(n)
            colors.append(color)

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        hole=0.45,
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Hours: %{value}<br>%{percent}<extra></extra>",
    ))

    total = sum(values)
    fig.update_layout(
        title=f"{sitename} {year}-{month:02d} Sample Hours Summary",
        annotations=[dict(
            text=f"{total}<br>hours",
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False,
        )],
        height=480,
        paper_bgcolor="white",
    )
    fig.show()


def plot_qual_summary(
    all_quals: pd.DataFrame,
    sitename: str,
    year: int,
    month: int,
) -> None:
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
    """
    if all_quals.empty:
        print("No qualifiers to summarise.")
        return

    code_counts = all_quals["CODE"].value_counts().sort_values()

    fig = go.Figure(go.Bar(
        x=code_counts.values.tolist(),
        y=code_counts.index.tolist(),
        orientation="h",
        marker_color="#1f77b4",
        hovertemplate="<b>%{y}</b><br>Lines: %{x}<extra></extra>",
    ))

    fig.update_layout(
        title=f"{sitename} {year}-{month:02d} Data Qualification Summary",
        xaxis_title="Number of qualifier lines",
        yaxis_title="Qualifier code",
        height=max(300, 60 * len(code_counts)),
        **_LAYOUT_STYLE,
    )
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)
    fig.show()


def plot_null_summary(
    all_quals: pd.DataFrame,
    ds,
    sitename: str,
    year: int,
    month: int,
) -> None:
    """Plot a bar chart of nulled ambient hours by nullification reason.

    Expands each null qualifier interval (AS/AE) to individual hours,
    intersects with ambient sample timestamps, and reports totals grouped
    by qualifier code and reason.

    Args:
        all_quals: Combined qualifier DataFrame.
        ds: Dataset object.
        sitename: Site name string for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.
    """
    null_df = all_quals[all_quals["CODE"].isin(_NULL_CODES)] if not all_quals.empty else pd.DataFrame()

    if null_df.empty:
        print("No null qualifiers found — no nulled hours to summarise.")
        return

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
    _CODE_COLOR = {"AS": "#FF9800", "AE": "#F44336"}

    fig = go.Figure(go.Bar(
        x=summary["hours"].tolist(),
        y=labels,
        orientation="h",
        marker_color=[_CODE_COLOR.get(c, "#9E9E9E") for c in summary["code"]],
        hovertemplate="<b>%{y}</b><br>Nulled ambient hours: %{x}<extra></extra>",
    ))

    fig.update_layout(
        title=f"{sitename} {year}-{month:02d} Data Nullification Summary",
        xaxis_title="Nulled ambient hours",
        yaxis_title="",
        height=max(300, 60 * len(summary)),
        **_LAYOUT_STYLE,
    )
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)
    fig.show()


def plot_blank_totals(
    ds,
    sitename: str,
    year: int,
    month: int,
) -> None:
    """Plot blank TNMTC and TNMHC concentrations over the month.

    Both total columns are shown on the same axis. If neither column is
    present in the blank DataFrame, a message is printed and the function
    returns without plotting.

    Args:
        ds: Dataset object (uses ds.blanks).
        sitename: Site name string for the plot title.
        year: Year for the plot title.
        month: Month number for the plot title.
    """
    blank_df = ds.blanks
    if blank_df.empty:
        print("No blank samples to plot.")
        return

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
        return

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
        title=f"{sitename} {year}-{month:02d} Blank Total Hydrocarbons",
        xaxis_title="Date",
        yaxis_title="Concentration (ppbC)",
        height=420,
        hovermode="closest",
        **_LAYOUT_STYLE,
    )
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)
    fig.show()
