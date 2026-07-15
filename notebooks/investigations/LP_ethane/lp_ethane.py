from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from autogc_core.max.parsers import crosstab_to_df

DATA_DIR = Path(__file__).resolve().parent
TOC_REPLACED = pd.Timestamp("2026-07-07 10:00:00")

def load_data(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load blank/ambient/CVS/LCS/RTS crosstab CSVs into DataFrames keyed by dataset name."""
    paths = {
        "blank": data_dir / "amount_crosstab_run_[B].csv",
        "ambient": data_dir / "amount_crosstab_run_[S].csv",
        "cvs": data_dir / "amount_crosstab_run_[C].csv",
        "lcs": data_dir / "amount_crosstab_run_[E].csv",
        "rts": data_dir / "amount_crosstab_run_[Q].csv",
    }
    return {name: crosstab_to_df(path) for name, path in paths.items()}


def plot_reference_vs_ambient(
    reference_df: pd.DataFrame,
    ambient_df: pd.DataFrame,
    compound: str,
    reference_name: str,
    keep_below_threshold: bool = False,
    threshold: float = 1,
    calibration_point: float = 29.2,
    figsize: tuple[float, float] = (10, 4),
) -> plt.Figure:
    """Plot a reference dataset (blank/CVS/LCS/RTS) against ambient concentrations for one compound."""
    if keep_below_threshold:
        mask = reference_df[compound] < threshold
    else:
        mask = reference_df[compound] > threshold

    fig, ax_ambient = plt.subplots(figsize=figsize)
    ax_reference = ax_ambient.twinx()

    (line_ambient,) = ax_ambient.plot(
        ambient_df.index,
        ambient_df[compound],
        color="tab:blue",
        label=f"{compound} Ambient",
    )
    (line_reference,) = ax_reference.plot(
        reference_df.index[mask],
        reference_df.loc[mask, compound],
        color="tab:orange",
        label=f"{compound} {reference_name}",
    )
    line_toc_replaced = ax_ambient.axvline(
        x=TOC_REPLACED,
        label="TOC Generator Replaced",
        color="red",
        linestyle="dashed",
        linewidth=1,
    )
    ax_ambient.axhline(calibration_point, color="black", linestyle=":", linewidth=1)
    ax_ambient.annotate(
        "Upper calibration point",
        xy=(0, calibration_point),
        xycoords=("axes fraction", "data"),
        xytext=(4, 4),
        textcoords="offset points",
        fontsize=8,
    )

    ax_ambient.set_xlabel("Date")
    ax_ambient.set_ylabel(f"Ambient {compound} Concentration (ppbC)")
    ax_reference.set_ylabel(f"{compound} {reference_name} Concentration (ppbC)")
    ax_ambient.legend(
        [line_ambient, line_reference, line_toc_replaced],
        [line_ambient.get_label(), line_reference.get_label(), line_toc_replaced.get_label()],
        loc="upper left",
        frameon=False,
    )

    fig.autofmt_xdate()
    fig.tight_layout()
    plt.close(fig)
    return fig
