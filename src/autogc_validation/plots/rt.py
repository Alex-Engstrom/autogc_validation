# -*- coding: utf-8 -*-
"""
Retention time distribution plots for AutoGC validation.
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from autogc_validation.database.enums import ColumnType, aqs_to_name, get_codes_by_column

# Percentile bin edges and labels used for strip-plot colouring.
_PCT_BINS = [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.0]


def plot_rt(
    rt_df: pd.DataFrame,
    conc_df: pd.DataFrame,
    sitename: str,
    year: int,
    month: int,
    samp_type: str | None = None,
) -> None:
    """Plot retention time distributions for each sample type.

    For each sample type (or a single type if samp_type is given), produces
    a violin + strip plot with one violin per compound. Strip points are
    coloured by their concentration percentile within the sample type group,
    so shifts correlated with high or low concentration are immediately visible.

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
    """
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
                id_vars=["date_time", "sample_type", "filename"],
                var_name="compound",
                value_name="rt",
            )
            .dropna(subset=["rt"])
        )

        pct_long = (
            percentiles
            .assign(sample_type=conc_display["sample_type"])
            .reset_index()
            .melt(
                id_vars=["date_time", "sample_type"],
                var_name="compound",
                value_name="percentile",
            )
        )

        df_long = df_long.merge(
            pct_long, on=["date_time", "sample_type", "compound"], how="left"
        )

        df_long["category"] = df_long["compound"].apply(
            lambda x: "PLOT" if x in plot_names else "BP"
        )
        df_long["pct_bin"] = pd.cut(
            df_long["percentile"],
            bins=[0.0] + _PCT_BINS,
            labels=_PCT_BINS,
        )
        df_long["pct_bin"] = df_long["pct_bin"].astype(
            pd.CategoricalDtype(categories=_PCT_BINS, ordered=True)
        )
        df_long["compound"] = pd.Categorical(
            df_long["compound"], categories=all_names, ordered=True
        )
        df_long = df_long.sort_values(["compound", "pct_bin"])

        plt.figure(figsize=(24, 6))
        sns.violinplot(
            data=df_long, x="compound", y="rt",
            inner=None, fill=False, color="black", linewidth=1,
        )
        sns.stripplot(
            data=df_long, x="compound", y="rt",
            hue="pct_bin", hue_order=_PCT_BINS,
            palette="coolwarm", size=2,
            edgecolor="black", linewidth=0.1,
            jitter=0.3, legend=True,
        )
        plt.xticks(rotation=90)
        plt.title(
            f"{sitename} {year}-{month:02d} "
            f"Retention Time Distributions — {sampletype}"
        )
        plt.legend(
            title="Concentration Percentile",
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
        )
        plt.ylabel("Normalized RT (RT \u2212 median RT)")
        plt.xlabel("Compound")
        plt.tight_layout()
        plt.show()
