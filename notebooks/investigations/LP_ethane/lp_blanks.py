from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from autogc_core.max.parsers import crosstab_to_df

blk_path = Path(r"D:\autogc_validation\notebooks\investigations\LP_ethane\amount_crosstab_run_[B].csv")
blank_df = crosstab_to_df(blk_path)
PM = pd.Timestamp("2026-04-18 06:00:00")
TOC_REPLACED = pd.Timestamp("2026-07-07 10:00:00")


def plot_ethane_benzene_timeseries(
    blank_df: pd.DataFrame,
    ethane_mdl: float = 0.1893,
    benzene_mdl: float = 0.1097,
    threshold: float = 0.5,
    xlim_start: pd.Timestamp = pd.Timestamp("2026-04-15"),
    xlim_end: pd.Timestamp | None = pd.Timestamp("2026-07-18"),
    figsize: tuple[float, float] = (12, 6),
) -> plt.Figure:
    """Plot stacked ambient Ethane and Benzene timeseries with threshold and MDL reference lines."""
    fig, (ax_ethane, ax_benzene) = plt.subplots(2, 1, sharex=True, figsize=figsize)

    for ax, compound, mdl in [(ax_ethane, "Ethane", ethane_mdl), (ax_benzene, "Benzene", benzene_mdl)]:
        ax.plot(blank_df.index, blank_df[compound], color="tab:blue", linewidth=1)
        ax.axvline(TOC_REPLACED, color="red", linestyle="dashed", linewidth=1)
        ax.axvline(PM, color="orange", linestyle="dashed", linewidth=1)
        ax.axhline(threshold, color="black", linestyle=":", linewidth=1)
        ax.axhline(mdl, color="gray", linestyle="--", linewidth=1)
        ax.annotate(
            "MDL",
            xy=(1, mdl),
            xycoords=("axes fraction", "data"),
            xytext=(-4, 4),
            textcoords="offset points",
            fontsize=8,
            ha="right",
            color="gray",
        )
        ax.set_ylabel(f"{compound} (ppbC)")
        ax.set_title(f"{compound} Blanks", fontsize=16, fontweight="bold")

    ax_ethane.annotate(
        "TOC Generator Replaced",
        xy=(TOC_REPLACED, 1),
        xycoords=("data", "axes fraction"),
        xytext=(4, -4),
        textcoords="offset points",
        fontsize=8,
        color="red",
        rotation=90,
        va="top",
    )
    ax_ethane.annotate(
        "Annual Maintenance",
        xy=(PM, 1),
        xycoords=("data", "axes fraction"),
        xytext=(4, -4),
        textcoords="offset points",
        fontsize=8,
        color="orange",
        rotation=90,
        va="top",
    )

    ax_benzene.set_xlabel("Date")
    ax_ethane.set_xlim(left=xlim_start, right=xlim_end)
    ax_ethane.set_ylim(bottom= None, top = .65)
    fig.autofmt_xdate()
    fig.tight_layout()
    plt.close(fig)
    return fig

plot_ethane_benzene_timeseries(blank_df).show()