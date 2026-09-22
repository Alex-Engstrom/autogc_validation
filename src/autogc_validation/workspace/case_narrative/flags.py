# -*- coding: utf-8 -*-
"""
Case-narrative sample/null-code accounting built on SampleSummary
(AQS upload file hour breakdown by null data code).
"""

import os
from dataclasses import dataclass, field

import matplotlib.pyplot as plt

from aqs_tools.processors import summarize_nulls_by_hour, summarize_qualifiers_by_hour, summarize_nulls_by_compound, summarize_qualifiers_by_compound
from aqs_tools.constants import TransactionType
from aqs_tools.parsers import generate_aqs_df

QC_NULL_CODES = frozenset({"AY", "TC", "DL", "AT"})


def summarize_nulls_by_hour_qmd(
    aqs_txtfile: os.PathLike,
    transaction_type: TransactionType,
    threshold: int = 55,
) -> dict:
    """qmd-local copy of aqs_tools.processors.summarize_nulls_by_hour.

    Same per-code hour counts, plus a 'total_hours' key (count of distinct
    sample periods in the file) needed for the donut plot's valid-ambient
    slice. Kept separate so edits here don't affect summarize_nulls_by_hour,
    which is still used as a validation-workflow check.
    """
    df = generate_aqs_df(aqs_txtfile, transaction_type)
    grouped = df.groupby("Null Data Code")
    by_code = {}
    for code, data in grouped:
        grp = data.groupby(["Sample Date", "Sample Begin Time"])["Parameter"].agg(len)
        by_code[code] = int((grp >= threshold).sum())

    by_code["total"] = sum(amt for amt in by_code.values() if amt > 0)
    by_code["total_hours"] = df.groupby(["Sample Date", "Sample Begin Time"]).ngroups
    return by_code


@dataclass
class SampleSummary:
    """Sample counts and null-code hour breakdown for one AQS upload file.

    All counts are derived in __post_init__ from the per-code hour
    breakdown returned by summarize_nulls_by_hour_qmd: total_qc_hours
    sums the QC_NULL_CODES-tagged hours, nulled_ambient is the
    remaining nulled hours, and ambient is total_hours minus all
    nulled hours.
    """
    aqs_txtfile: os.PathLike
    transaction_type: TransactionType = TransactionType.RD
    threshold: int = 55

    nulled_by_code: dict[str, int] = field(init=False, default_factory=dict)
    total_nulled_hours: int = field(init=False, default=0)
    total_qc_hours: int = field(init=False, default = 0)
    nulled_ambient: int = field(init = False, default = 0)
    ambient: int = field(init = False, default = 0)
    total_hours: int = field(init=False, default=0)
    def __post_init__(self) -> None:
        by_code = summarize_nulls_by_hour_qmd(
            self.aqs_txtfile, self.transaction_type, self.threshold
        )
        self.total_hours = by_code.pop("total_hours", 0)
        self.total_nulled_hours = by_code.pop("total", 0)
        self.nulled_by_code = by_code
        self.total_qc_hours = sum(
            count for code, count in self.nulled_by_code.items()
            if code in QC_NULL_CODES
        )
        self.nulled_ambient = self.total_nulled_hours - self.total_qc_hours
        self.ambient = self.total_hours - self.total_nulled_hours

_DONUT_COLORS = {
    "Valid Ambient": "#2196F3",
    "QC": "#FF9800",
    "Nulled Non-QC Hours": "#F44336",
    "PT/Experimental": "#795548",
}


def plot_monthly_hours_summary(ss: SampleSummary) -> plt.Figure:
    experimental_hours = ss.nulled_by_code.get("XX", 0)
    qc_hours = ss.total_qc_hours
    nulled_ambient_hours = ss.nulled_ambient - experimental_hours
    valid_ambient_hours = ss.total_hours - ss.total_nulled_hours

    counts = {
        "Valid Ambient": valid_ambient_hours,
        "QC": qc_hours,
        "Nulled Non-QC Hours": nulled_ambient_hours,
        "PT/Experimental": experimental_hours,
    }
    counts = {label: hrs for label, hrs in counts.items() if hrs > 0}
    labels = list(counts.keys())
    data = list(counts.values())
    colors = [_DONUT_COLORS[label] for label in labels]

    fig, ax = plt.subplots(figsize=(7, 5), subplot_kw=dict(aspect="equal"))
    wedges, _ = ax.pie(data, colors=colors, wedgeprops=dict(width=0.5, edgecolor = 'black'), startangle=-40)
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.legend(
        wedges,
        [f"{label}:\n{hrs} hrs" for label, hrs in zip(labels, data)],
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        ncol=1,
        fontsize = 14
    )
    ax.text(0, 0, f"{ss.total_hours}\nhours", ha="center", va="center", fontsize=16)
    fig.subplots_adjust(left=0.0, top=1.0, bottom=0.0, right=5 / 7)
    plt.close()
    return fig

def plot_null_summary(ss: SampleSummary) -> plt.Figure:
    null_by_hour = ss.nulled_by_code
    null_by_hour = dict(sorted(null_by_hour.items(), key=lambda item: item[1], reverse = True))
    null_by_hour = {k: v for k, v in null_by_hour.items() if v != 0 and k not in ["AY", "TC", "DL", "AT", "XX"]}
    labels = list(null_by_hour.keys())
    data = list(null_by_hour.values())
    cmap = plt.colormaps['tab10']
    colors = [cmap(i) for i in range(len(labels))]

    fig, ax = plt.subplots(figsize=(7, 5), subplot_kw=dict(aspect="equal"))
    wedges, _ = ax.pie(data, colors=colors, wedgeprops=dict(width=0.5, edgecolor = 'black'), startangle=-40)
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.legend(
        wedges,
        [f"{label}:\n{hrs} hrs" for label, hrs in zip(labels, data)],
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        ncol=1,
        fontsize = 14
    )
    ax.text(0, 0, f"{sum(data)}\nhours", ha="center", va="center", fontsize=16)
    fig.subplots_adjust(left=0.0, top=1.0, bottom=0.0, right=5 / 7)
    plt.close()
    return fig
