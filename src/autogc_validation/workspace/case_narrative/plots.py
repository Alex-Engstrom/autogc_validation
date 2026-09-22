# -*- coding: utf-8 -*-
"""
Case-narrative plots and text summaries built from Dataset DataFrames
(ambient/blanks/cvs/lcs/rts, paired with MDL or canister periods).
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from autogc_validation.qc import compute_recovery
from autogc_validation.qc.recovery import qc_exceedance_counts
from autogc_validation.qc.blanks import blank_exceedance_counts
from autogc_validation.database.enums import aqs_to_name, name_to_aqs, SampleTypeLetter, CompoundAQSCode


def recovery_plot(qc_df: pd.DataFrame, qc_periods: pd.DataFrame, compounds: list[str] = ["Propane", "Toluene"]) -> plt.Figure:
    compound_codes = [name_to_aqs(comp) for comp in compounds]
    qc_recovery = compute_recovery(qc_df, qc_periods)
    qc_recovery.drop(columns = "filename", inplace = True)
    fig, axes = plt.subplots(ncols = 2,
                            nrows = 1,
                            sharey = True,
                            figsize = (20,5),
                            gridspec_kw={'width_ratios': [3,1],
                                'wspace': 0.05})
    ax1, ax2 = axes[0], axes[1]
    qc_recovery[compound_codes].plot(ax = ax1, marker='o', x_compat = True)
    colors = [line.get_color() for line in ax1.get_lines()]
    for line, code in zip(ax1.get_lines(), compound_codes):
        line.set_label(aqs_to_name(code))

    ax1.axhline(70, color = 'red', label = 'Lower Limit', zorder = 0)
    ax1.axhline(130, color = 'red', label = "Upper Limit", zorder = 0)
    ax1.axhline(100, color = 'black')
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval = 1))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter(''))
    ax1.xaxis.set_minor_locator(mdates.HourLocator(byhour = 12))
    ax1.xaxis.set_minor_formatter(mdates.DateFormatter('%d'))
    ax1.tick_params(axis = 'x', which = 'major', length = 4)
    ax1.tick_params(axis = 'x', which = 'minor', length = 0, rotation = 0)
    ax1.set_ylabel("Recovery (%)")
    ax1.set_xlabel("Day of the Month")
    ax1.legend()


    bp = qc_recovery[compound_codes].plot(ax = ax2, kind='box', color = 'black', patch_artist = True, return_type = 'dict')
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    ax2.axhline(70, color = 'red', label = 'Lower Limit', zorder = 0)
    ax2.axhline(130, color = 'red', label = "Upper Limit", zorder = 0)
    ax2.axhline(100, color = 'black')
    ax2.set_xticklabels([aqs_to_name(code) for code in compound_codes])
    ax2.set_xlabel("Compound")
    plt.close()
    return fig

def plot_tnmhc(blank: pd.DataFrame) -> plt.Figure:
    tnmhc_code = int(CompoundAQSCode.C_TNMHC)
    fig, ax = plt.subplots(figsize=(15, 4))
    blank[tnmhc_code].plot(ax=ax, marker='o', x_compat = True)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval = 1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter(''))
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour = 12))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%d'))
    ax.tick_params(axis = 'x', which = 'major', length = 4)
    ax.tick_params(axis = 'x', which = 'minor', length = 0, rotation = 0)
    ax.set_ylabel("TNMHC Concentration (ppbC)", color = "black")
    ax.set_xlabel("Day of the Month", color = "black")
    plt.close()
    return fig

def recovery_stats(qc_df: pd.DataFrame, qc_periods: pd.DataFrame, compounds: list[str] = ["Propane", "Toluene"]) ->pd.DataFrame:
    compound_codes = [name_to_aqs(comp) for comp in compounds]
    qc_recovery = compute_recovery(qc_df, qc_periods)
    qc_recovery.drop(columns = "filename", inplace = True)
    qc_recovery.columns = [aqs_to_name(col) for col in qc_recovery.columns]
    means = qc_recovery.mean(axis = 0)
    means.name = "mean"
    stdevs = qc_recovery.std(axis = 0)
    stdevs.name = "stdev"
    combo = pd.concat([means, stdevs], axis = 1)
    return combo.loc[compounds,:]


def _indented_bullets(series: pd.Series, indent: str) -> str:
    bullets = "\n".join(f"- {compound} ({int(n)} exceedances)" for compound, n in series.items())
    return f"```{{=typst}}\n#pad(left: {indent})[\n{bullets}\n]\n```"


def _blank_exceedance_text(blanks_df: pd.DataFrame, mdl_periods: pd.DataFrame, indent: str) -> str:
    counts = blank_exceedance_counts(blanks_df, mdl_periods)
    above_mdl = counts.loc["above_mdl"]
    above_mdl = above_mdl[above_mdl > 1].sort_values(ascending=False)

    if above_mdl.empty:
        return "No compounds exceeded their method detection limit (MDL) in any blank sample this month."

    return (
        "The following compounds exceeded their method detection limit (MDL) "
        f"in at least 2 blank samples:\n\n{_indented_bullets(above_mdl, indent)}"
    )


def exceedance_summary_text(qc_df: pd.DataFrame, qc_periods: pd.DataFrame, indent: str = "1.5em") -> str:
    """Bulleted narrative of compounds that failed QC bounds this month.

    Dispatches on ``qc_df.attrs["sample_type"]``: blanks (paired with
    mdl_periods) get an MDL-exceedance summary; CVS/LCS/RTS (paired with
    canister periods) get the usual high/low recovery-exceedance summary.

    Args:
        qc_df: Typed QC DataFrame (Dataset.blanks, .cvs, .lcs, or .rts).
        qc_periods: Expected values from get_mdl_periods (for blanks) or
            get_canister_periods (for CVS/LCS/RTS).
        indent: Typst length for how far the bullet lists are padded from
            the left margin (e.g. "1.5em", "2em", "20pt").

    Returns:
        Markdown text: an intro sentence plus one bullet per compound.
        For blanks: compounds that exceeded their MDL in at least 2 samples.
        For CVS/LCS/RTS: high (>130%) exceedances, then low (<70%)
        exceedances. The bullets are wrapped in a raw Typst ``#pad`` block
        so they render indented without affecting other lists in the
        document — a plain Div class doesn't survive Quarto's typst writer,
        so this is the reliable way to scope the indent to just this list.
        Sections/cases with no exceedances return a "none exceeded" sentence
        instead.
    """
    if qc_df.attrs.get("sample_type") == SampleTypeLetter.BLANK:
        return _blank_exceedance_text(qc_df, qc_periods, indent)

    counts = qc_exceedance_counts(qc_df, qc_periods)
    high = counts.loc["high"]
    high = high[high > 0].sort_values(ascending=False)
    low = counts.loc["low"]
    low = low[low > 0].sort_values(ascending=False)

    if high.empty and low.empty:
        return "All compounds remained within the 70-130% recovery range for every QC sample this month."

    sections = []
    if not high.empty:
        sections.append(
            "The following compounds exceeded the upper 130% recovery threshold "
            f"in at least 1 QC sample:\n\n{_indented_bullets(high, indent)}"
        )
    if not low.empty:
        sections.append(
            "The following compounds were below the lower 70% recovery threshold "
            f"in at least 1 QC sample:\n\n{_indented_bullets(low, indent)}"
        )
    return "\n\n".join(sections)
