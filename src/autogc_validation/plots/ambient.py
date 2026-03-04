# -*- coding: utf-8 -*-
"""
Ambient compound comparison and category sum plots for AutoGC validation.
"""

import matplotlib.pyplot as plt
import pandas as pd

from autogc_validation.database.enums import (
    VOCCategory,
    get_codes_by_category,
    name_to_aqs,
)

# Default compound pairs/groups to plot against each other.  The first element
# of each tuple is the x-axis compound; the rest are plotted against it.
_DEFAULT_COMPARISONS: list[tuple[str, ...]] = [
    ("Benzene", "Toluene", "Ethane"),
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


def plot_ambient_comparisons(
    ambient_df: pd.DataFrame,
    sitename: str,
    year: int,
    month: int,
    label: str = "Full Month",
    comparisons: list[tuple[str, ...]] | None = None,
) -> None:
    """Plot compound comparison scatter plots and VOC category sum scatter plots.

    Produces two figures:

    1. A grid of scatter plots for the specified compound pairs/groups.  The
       first compound in each tuple is the x-axis; the remainder are each
       plotted against it as separate series.  Groups where fewer than two
       compounds are present in *ambient_df* are silently skipped.

    2. Three scatter plots of alkane sum vs alkene, aromatic, and terpene sums.

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
    """
    if ambient_df.empty:
        print(f"No ambient data to plot ({label}).")
        return

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

    title_base = f"{sitename} {year}-{month:02d} — {label}"

    # ------------------------------------------------------------------
    # Figure 1: compound comparison scatter plots
    # ------------------------------------------------------------------
    if valid_groups:
        ncols = 3
        nrows = -(-len(valid_groups) // ncols)
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(20, 4 * nrows))
        axes = axes.flatten()

        for i, group in enumerate(valid_groups):
            ax = axes[i]
            x_code, x_name = group[0]
            for y_code, y_name in group[1:]:
                ax.scatter(
                    ambient_df[x_code],
                    ambient_df[y_code],
                    alpha=0.5,
                    s=12,
                    label=f"{x_name} vs {y_name}",
                )
            ax.set_xlabel(x_name)
            ax.set_ylabel("Comparison Compound")
            ax.legend(fontsize=8)

        for j in range(len(valid_groups), len(axes)):
            axes[j].set_visible(False)

        fig.suptitle(f"{title_base} — Compound Comparisons", fontsize=12)
        plt.tight_layout()
        plt.show()

    # ------------------------------------------------------------------
    # Figure 2: VOC category sums
    # ------------------------------------------------------------------
    alkane_sum = _cat_sum(ambient_df, VOCCategory.ALKANE)

    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(18, 5))
    for ax, (_, y_cat) in zip(axes, _CATEGORY_PAIRS):
        y_sum = _cat_sum(ambient_df, y_cat)
        ax.scatter(alkane_sum, y_sum, alpha=0.5, s=12)
        ax.set_xlabel(alkane_sum.name)
        ax.set_ylabel(y_sum.name)
        ax.set_title(f"{alkane_sum.name} vs {y_sum.name}")

    fig.suptitle(f"{title_base} — VOC Category Sums", fontsize=12)
    plt.tight_layout()
    plt.show()
