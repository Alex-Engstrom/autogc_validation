# -*- coding: utf-8 -*-
"""
Ambient compound comparison and category sum plots for AutoGC validation.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
import numpy as np
from autogc_validation.database.enums import (
    VOCCategory,
    get_codes_by_category,
    name_to_aqs,
    aqs_to_name,
    CompoundAQSCode
)

logger = logging.getLogger(__name__)
# Default compound pairs/groups to plot against each other.  The first element
# of each tuple is the x-axis compound; the rest are plotted against it.
_DEFAULT_COMPARISONS: list[tuple[str, ...]] = [
    ("Benzene",  "Ethane"),
    ("Toluene", "Ethane"),
    ("Propane", "Propylene"),
    ("Propane", "TNMTC"),
    ("TNMTC", "TNMHC"),
    ("Ethylene", "Ethane"),
    ("O-xylene", "M&p-xylene"),
    ("2-methylhexane", "2,3-dimethylpentane"),
    ("Methylcyclopentane", "2,4-dimethylpentane"),
    ("Iso-pentane", "N-pentane", "Cyclopentane"),
    ("N-butane", "Iso-butane"),
]

_CATEGORY_PAIRS: list[tuple[VOCCategory, VOCCategory]] = [
    (VOCCategory.ALKANE, VOCCategory.ALKENE),
    (VOCCategory.ALKANE, VOCCategory.AROMATIC),
    (VOCCategory.ALKANE, VOCCategory.TERPENE),
]


def _cat_sum(ambient_df: pd.DataFrame, category: VOCCategory) -> pd.Series:
    """Sum all present compounds in a VOC category across each sample."""
    codes = [c for c in get_codes_by_category(category) if c in ambient_df.columns]
    if not codes:
        return pd.Series(0.0, index=ambient_df.index, name=category.value)
    return ambient_df[codes].sum(axis=1).rename(category.value)

def plot_vs_totals(ambient_df: pd.DataFrame,
        sitename: str,
        year: int,
        month: int) -> go.Figure:
    """Plot each compound vs TNMTC with a linear fit, one subplot per compound.

    Returns:
        The Plotly Figure, or an empty ``go.Figure()`` if there was no ambient data to plot.
    """
    if ambient_df.empty:
        logger.warning("No ambient data to plot.")
        return go.Figure()
    label = 'VOCs vs TNMTC'
    title_base = f"{sitename} {year}-{month:02d} — {label}"
    timestamps = ambient_df.index.strftime("%Y-%m-%d %H:%M")
    hover_text = ambient_df["filename"] + "<br>" + timestamps
    compounds = [col for col in ambient_df.columns if isinstance(col, CompoundAQSCode)]

    ncols = 4
    nrows = -(-len(compounds)//4)
    subplot_titles = [f"{aqs_to_name(col)} vs TNMTC" for col in compounds]
    fig1 = make_subplots(
        rows=nrows, cols=ncols,
        subplot_titles=subplot_titles,
        horizontal_spacing=0.08,
        vertical_spacing=min(0.02, 1 / nrows) if nrows > 1 else 0,
    )
    for i, compound in enumerate(compounds):
        row = i // ncols + 1
        col = i % ncols + 1
        comp_name = aqs_to_name(compound)
        fig1.add_trace(
            go.Scatter(
                x=ambient_df[43000],
                y=ambient_df[compound],
                mode="markers",
                marker=dict(size=5, opacity=0.5),
                name=f"{comp_name} vs TNMTC",
                text=hover_text,
                hovertemplate=(
                    f"{comp_name}: %{{y:.2f}}<br>"
                    f"TNMTC: %{{x:.2f}}<br>"
                    "%{text}<extra></extra>"
                ),
            ),
            row=row, col=col,
        )
        x = ambient_df[43000].values
        y = ambient_df[compound].values
  
        # Drop NaNs before fitting
        mask = np.isfinite(x) & np.isfinite(y)
        x_clean, y_clean = x[mask], y[mask]
  
        m, b = np.polyfit(x_clean, y_clean, deg=1)
        r2 = np.corrcoef(x_clean, y_clean)[0, 1] ** 2
  
        x_line = np.array([x_clean.min(), x_clean.max()])
        y_line = m * x_line + b
        
        # Regression line
        fig1.add_trace(go.Scatter(
            x=x_line,
            y=y_line,
            mode="lines",
            line=dict(color="black", width=1),
            showlegend=False,
            hoverinfo="skip",
        ), row=row, col=col)
   
        # Equation annotation
        fig1.add_annotation(
            text=f"y = {m:.3f}x + {b:.3f}<br>R² = {r2:.3f}",
            xref="x domain", yref="y domain",
            x=0.05, y=0.95,
            showarrow=False,
            align="left",
            font=dict(size=9),
            row=row, col=col,
        )
        fig1.update_xaxes(title_text="TNMTC", row=row, col=col)
        fig1.update_yaxes(title_text=comp_name, row=row, col=col)

    fig1.update_layout(
        title=f"{title_base} — Compound Comparisons",
        height=350 * nrows,
        width=1200,
        showlegend=False,
    )
    return fig1


def plot_ambient_comparisons(
    ambient_df: pd.DataFrame,
    sitename: str,
    year: int,
    month: int,
    label: str = "Full Month",
    comparisons: list[tuple[str, ...]] | None = None,
) -> go.Figure:
    """Plot a grid of compound comparison scatter plots.

    The first compound in each tuple is the x-axis; the remainder are each
    plotted against it as separate series.  Groups where fewer than two
    compounds are present in *ambient_df* are silently skipped.

    See also :func:`plot_voc_category_sums` for the companion VOC-category
    scatter plots.

    Args:
        ambient_df: Ambient concentration DataFrame — DatetimeIndex, integer
            AQS code columns.  Pass ``Dataset.ambient`` for the full month or
            a datetime-sliced subset for a single week.
        sitename: Site name string for plot titles (e.g. ``'EQ'``).
        year: Year for plot titles.
        month: Month number (1-12) for plot titles.
        label: Period label appended to each figure title, e.g. ``'Week 1'``
            or ``'Full Month'``.
        comparisons: List of compound name tuples.  Defaults to
            ``_DEFAULT_COMPARISONS``.  Compound names are matched
            case-insensitively via ``name_to_aqs``.

    Returns:
        The Plotly Figure, or an empty ``go.Figure()`` if there was no ambient
        data, or no comparison group had at least two compounds present.
    """
    if ambient_df.empty:
        logger.warning(f"No ambient data to plot ({label}).")
        return go.Figure()

    if comparisons is None:
        comparisons = _DEFAULT_COMPARISONS

    # Resolve compound names to AQS codes, skipping any that are absent.
    valid_groups: list[list[tuple[int, str]]] = []
    for group in comparisons:
        codes: list[tuple[int, str]] = []
        for cname in group:
            try:
                code = name_to_aqs(cname)
                if code in ambient_df.columns:
                    codes.append((code, cname))
            except (KeyError, ValueError):
                pass
        if len(codes) >= 2:
            valid_groups.append(codes)

    if not valid_groups:
        return go.Figure()

    title_base = f"{sitename} {year}-{month:02d} — {label}"
    timestamps = ambient_df.index.strftime("%Y-%m-%d %H:%M")
    hover_text = ambient_df["filename"] + "<br>" + timestamps

    ncols = 3
    nrows = -(-len(valid_groups) // ncols)
    subplot_titles = [group[0][1] for group in valid_groups] + [""] * (nrows * ncols - len(valid_groups))

    fig1 = make_subplots(
        rows=nrows, cols=ncols,
        subplot_titles=subplot_titles,
        horizontal_spacing=0.08,
        vertical_spacing=0.1,
    )

    for i, group in enumerate(valid_groups):
        row = i // ncols + 1
        col = i % ncols + 1
        x_code, x_name = group[0]
        for y_code, y_name in group[1:]:
            fig1.add_trace(
                go.Scatter(
                    x=ambient_df[x_code],
                    y=ambient_df[y_code],
                    mode="markers",
                    marker=dict(size=5, opacity=0.5),
                    name=f"{x_name} vs {y_name}",
                    text=hover_text,
                    hovertemplate=(
                        "%{text}<br>"
                        f"{x_name}: %{{x:.2f}}<br>"
                        f"{y_name}: %{{y:.2f}}<br>"
                        "<extra></extra>"
                    ),
                ),
                row=row, col=col,
            )
        fig1.update_xaxes(title_text=x_name, row=row, col=col)
        fig1.update_yaxes(title_text=y_name, row=row, col=col)

    fig1.update_layout(
        title=f"{title_base} — Compound Comparisons",
        height=350 * nrows,
        width=1200,
        showlegend=False,
    )
    return fig1


def plot_voc_category_sums(
    ambient_df: pd.DataFrame,
    sitename: str,
    year: int,
    month: int,
    label: str = "Full Month",
) -> go.Figure:
    """Plot alkane sum vs alkene, aromatic, and terpene sums as scatter plots.

    Companion figure to :func:`plot_ambient_comparisons` — split out as its
    own function because it is a conceptually distinct plot, not a variant
    of the compound-comparison grid.

    Args:
        ambient_df: Ambient concentration DataFrame — DatetimeIndex, integer
            AQS code columns.  Pass ``Dataset.ambient`` for the full month or
            a datetime-sliced subset for a single week.
        sitename: Site name string for the plot title (e.g. ``'EQ'``).
        year: Year for the plot title.
        month: Month number (1-12) for the plot title.
        label: Period label appended to the figure title, e.g. ``'Week 1'``
            or ``'Full Month'``.

    Returns:
        The Plotly Figure, or an empty ``go.Figure()`` if there was no ambient data to plot.
    """
    if ambient_df.empty:
        logger.warning(f"No ambient data to plot ({label}).")
        return go.Figure()

    title_base = f"{sitename} {year}-{month:02d} — {label}"
    timestamps = ambient_df.index.strftime("%Y-%m-%d %H:%M")
    alkane_sum = _cat_sum(ambient_df, VOCCategory.ALKANE)

    fig2 = make_subplots(
        rows=1, cols=3,
        subplot_titles=[f"{alkane_sum.name} vs {_cat_sum(ambient_df, y_cat).name}" for _, y_cat in _CATEGORY_PAIRS],
        horizontal_spacing=0.1,
    )

    for col_idx, (_, y_cat) in enumerate(_CATEGORY_PAIRS, start=1):
        y_sum = _cat_sum(ambient_df, y_cat)
        fig2.add_trace(
            go.Scatter(
                x=alkane_sum,
                y=y_sum,
                mode="markers",
                marker=dict(size=5, opacity=0.5),
                name=y_sum.name,
                text=timestamps,
                hovertemplate=(
                    f"{alkane_sum.name}: %{{x:.2f}}<br>"
                    f"{y_sum.name}: %{{y:.2f}}<br>"
                    "%{text}<extra></extra>"
                ),
            ),
            row=1, col=col_idx,
        )
        fig2.update_xaxes(title_text=alkane_sum.name, row=1, col=col_idx)
        fig2.update_yaxes(title_text=y_sum.name, row=1, col=col_idx)

    fig2.update_layout(
        title=f"{title_base} — VOC Category Sums",
        height=450,
        width=1200,
        showlegend=False,
    )
    return fig2
