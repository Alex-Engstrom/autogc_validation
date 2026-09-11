# -*- coding: utf-8 -*-
"""
Retention time distribution plots for AutoGC validation.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from autogc_validation.database.enums import ColumnType, aqs_to_name, get_codes_by_column


def plot_rt(
    rt_df: pd.DataFrame,
    conc_df: pd.DataFrame,
    sitename: str,
    year: int,
    month: int,
    samp_type: str | None = None,
) -> list[go.Figure]:
    """Plot retention time distributions for each sample type.

    For each sample type (or a single type if samp_type is given), produces
    a violin + strip plot with one violin per compound. Strip points are
    coloured by their concentration percentile within the sample type group,
    so shifts correlated with high or low concentration are immediately visible.

    The number of figures produced depends on how many sample types are
    present, so this returns a list rather than a fixed number of figures —
    display each element yourself, e.g. ``for fig in figs: display(fig)``.

    Args:
        rt_df: Dataset.rt DataFrame — DatetimeIndex, integer AQS code columns,
            sample_type and filename columns.
        conc_df: Dataset.data DataFrame — same shape as rt_df but with
            concentration values. Used to compute percentile colouring.
        sitename: Site name string for the plot title (e.g. 'EQ').
        year: Year (for the plot title).
        month: Month number (for the plot title).
        samp_type: If given, only plot this sample_type value. Otherwise all
            sample types are plotted in separate figures.

    Returns:
        A list of Plotly Figures, one per sample type plotted.
    """
    figures: list[go.Figure] = []
    # Build ordered compound code and name lists (elution order).
    plot_codes = get_codes_by_column(ColumnType.PLOT)
    bp_codes   = get_codes_by_column(ColumnType.BP)

    # Keep only codes present in the DataFrame.
    all_codes = [c for c in plot_codes + bp_codes if c in rt_df.columns]
    all_names = [aqs_to_name(c) for c in all_codes]
    plot_names = [aqs_to_name(c) for c in plot_codes if c in rt_df.columns]

    # Rename to compound names for display — don't mutate the originals.
    name_map = {c: aqs_to_name(c) for c in all_codes}
    rt_display   = rt_df.rename(columns=name_map)
    conc_display = conc_df.rename(columns=name_map)

    # Concentration percentiles within each sample type group.
    percentiles = (
        conc_display
        .groupby("sample_type")[all_names]
        .transform(lambda x: (x.rank(pct=True) - 1 / len(x)) / (1 - 1 / len(x)))
    )

    # Subtract per-group median so each violin is centred on zero.
    normalized = rt_display.copy()
    normalized[all_names] = (
        rt_display
        .groupby("sample_type")[all_names]
        .transform(lambda x: x - x.median())
    )

    for sampletype, df in normalized.groupby("sample_type"):
        if samp_type and samp_type != sampletype:
            continue

        df_long = (
            df.reset_index()
            .melt(
                id_vars=["sample_hour", "date_time", "sample_type", "sample_type_long", "filename"],
                var_name="compound",
                value_name="rt",
            )
            .dropna(subset=["rt"])
        )

        pct_long = (
            percentiles
            .assign(
                sample_type=conc_display["sample_type"],
                sample_type_long=conc_display["sample_type_long"],
            )
            .reset_index()
            .melt(
                id_vars=["sample_hour", "sample_type", "sample_type_long"],
                var_name="compound",
                value_name="percentile",
            )
        )

        df_long = df_long.merge(
            pct_long, on=["sample_hour", "sample_type", "compound"], how="left"
        )

        df_long["compound"] = pd.Categorical(
            df_long["compound"], categories=all_names, ordered=True
        )
        df_long = df_long.sort_values("compound")

        present_names = [n for n in all_names if n in set(df_long["compound"])]
        compound_pos = {name: i for i, name in enumerate(present_names)}

        rng = np.random.default_rng(42)
        x_jittered = (
            df_long["compound"].map(compound_pos).astype(float)
            + rng.uniform(-0.3, 0.3, size=len(df_long))
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_jittered,
            y=df_long["rt"],
            mode="markers",
            marker=dict(
                size=2.5,
                color=df_long["percentile"],
                colorscale="RdBu_r",
                cmin=0,
                cmax=1,
                colorbar=dict(title="Concentration<br>Percentile"),
                opacity=0.7,
            ),
            text=df_long["filename"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "RT offset: %{y:.4f}<br>"
                "Percentile: %{marker.color:.2f}"
                "<extra></extra>"
            ),
            showlegend=False,
        ))

        fig.update_xaxes(
            tickvals=list(range(len(present_names))),
            ticktext=present_names,
            tickangle=90,
        )
        fig.update_yaxes(title_text="Normalized RT (RT \u2212 median RT)")
        fig.update_layout(
            title=f"{sitename} {year}-{month:02d} \u2014 RT Distribution ({sampletype})",
            height=500,
            width=max(900, 25 * len(present_names)),
        )
        figures.append(fig)

    return figures
