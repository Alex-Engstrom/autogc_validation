# -*- coding: utf-8 -*-
"""
Dataset — the central data container for AutoGC validation.

Loads chromatogram samples from a folder of CDF files and builds
concentration and retention time DataFrames for downstream QC analysis.
"""

import logging
from datetime import timedelta
from pathlib import Path
from typing import Dict, List

import pandas as pd

from autogc_validation.database.enums import CompoundAQSCode, SampleTypeLetter, SampleTypeLong, LETTER_TO_LONG_NAMES, LONG_NAME_CANONICAL, UNID_CODES, TOTAL_CODES
from autogc_validation.io.samples import Sample, load_samples_from_folder

logger = logging.getLogger(__name__)


_SAMPLE_COLLECTION_OFFSET = pd.Timedelta(minutes=20)
"""Samples are collected for 40 minutes before injection; the midpoint (and
therefore the labelled sample hour) is 20 minutes before injection."""


def sample_hour(injection_time: pd.Timestamp) -> pd.Timestamp:
    """Return the sample hour for a given injection timestamp.

    The AutoGC collects ambient air for 40 minutes before injecting into the
    GC. The midpoint of collection — and therefore the hour that should be
    associated with the result — is 20 minutes before the injection time,
    floored to the whole hour.

    Example: injection at 10:05 → sample hour 09:00.

    Args:
        injection_time: The datetime when the sample was injected into the GC.

    Returns:
        Timestamp representing the sample hour (minute/second zeroed out).
    """
    return (injection_time - _SAMPLE_COLLECTION_OFFSET).floor("h")


def _collection_overlap(injection_time: pd.Timestamp, sample_hour_ts: pd.Timestamp) -> float:
    """Minutes of the 40-minute collection window that fall within the labeled sample hour.

    The collection window runs from injection_time - 40 min to injection_time.
    The labeled hour spans [sample_hour_ts, sample_hour_ts + 1h).

    Args:
        injection_time: Raw injection timestamp.
        sample_hour_ts: The sample_hour label for that injection (floor of
            injection_time - 20 min).

    Returns:
        Overlap duration in minutes (0.0 to 40.0).
    """
    collection_start = injection_time - pd.Timedelta(minutes=40)
    collection_end   = injection_time
    hour_end         = sample_hour_ts + pd.Timedelta(hours=1)
    overlap_start    = max(collection_start, sample_hour_ts)
    overlap_end      = min(collection_end,   hour_end)
    delta = overlap_end - overlap_start
    return max(0.0, delta.total_seconds() / 60)


def resolve_duplicate_sample_hours(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Resolve duplicate sample_hour index values, keeping the best sample per hour.

    When two samples share the same sample_hour label, the one whose 40-minute
    collection window has greater overlap with that hour is retained. The other
    is returned in a separate DataFrame so the caller can log or inspect it.

    Typical usage::

        ambient, removed = resolve_duplicate_sample_hours(ds.ambient)
        if not removed.empty:
            print("Dropped duplicate hour samples:", removed["filename"].tolist())

    Args:
        df: DataFrame with a DatetimeIndex named ``sample_hour`` and a
            ``date_time`` column holding the raw injection timestamp. As
            returned by any Dataset typed property (e.g. ``ds.ambient``).

    Returns:
        ``(kept_df, removed_df)`` — both have the same schema as *df*.
        *removed_df* is empty when no duplicates are present.
    """
    if not df.index.duplicated().any():
        return df.copy(), pd.DataFrame(columns=df.columns)

    kept_rows    = []
    removed_rows = []

    for sh_val, group in df.groupby(level=0):
        if len(group) == 1:
            kept_rows.append(group)
            continue

        overlaps = group["date_time"].apply(
            lambda dt: _collection_overlap(pd.Timestamp(dt), pd.Timestamp(sh_val))
        )
        best_pos = int(overlaps.values.argmax())
        for i, (_, row_df) in enumerate(group.iterrows()):
            target = kept_rows if i == best_pos else removed_rows
            target.append(group.iloc[[i]])

    kept_df = pd.concat(kept_rows).sort_index() if kept_rows else df.iloc[:0].copy()
    removed_df = pd.concat(removed_rows).sort_index() if removed_rows else df.iloc[:0].copy()
    return kept_df, removed_df


class Dataset:
    """Collection of chromatogram samples with concentration and retention time tables.

    Attributes:
        folder: Path to the directory of CDF files.
        samples: List of Sample objects (paired front/back chromatograms).
        data: Concentration DataFrame (ppbC), all sample types.
        rt: Retention time DataFrame, all sample types.

    All DataFrames use a DatetimeIndex named ``sample_hour`` — the injection
    time minus 20 minutes, floored to the whole hour. The raw injection
    timestamp is preserved as a ``date_time`` column. See ``sample_hour()``.

    Because sample_hour is derived by flooring, two samples can share the same
    index value. Use ``resolve_duplicate_sample_hours()`` to reduce a typed
    DataFrame to one sample per hour before passing it to AQS or qualifier
    functions.

    Typed concentration properties (filter data by sample type):
        ambient, blanks, cvs, rts, lcs, mdl, calibration, experimental

    Typed retention time properties (filter rt by sample type):
        ambient_rt, blanks_rt, cvs_rt, rts_rt, lcs_rt, mdl_rt,
        calibration_rt, experimental_rt
    """

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.samples = load_samples_from_folder(self.folder)
        self._data: pd.DataFrame | None = None
        self._rt: pd.DataFrame | None = None
        self._areas: pd.DataFrame | None = None
        self._totals: pd.DataFrame | None = None
        self._typed_data: Dict[SampleTypeLetter, pd.DataFrame] = {}
        self._typed_rt: Dict[SampleTypeLetter, pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # Combined DataFrames
    # ------------------------------------------------------------------

    @property
    def data(self) -> pd.DataFrame:
        """Concentration data, lazily generated on first access.

        Indexed by ``sample_hour`` (injection time − 20 min, floored to the
        hour). Raw injection timestamps are in the ``date_time`` column.
        """
        if self._data is None:
            self._data = self._generate_data()
        return self._data

    @property
    def rt(self) -> pd.DataFrame:
        """Retention time data, lazily generated on first access.

        Indexed by ``sample_hour`` (injection time − 20 min, floored to the
        hour). Raw injection timestamps are in the ``date_time`` column.
        """
        if self._rt is None:
            self._rt = self._generate_rt()
        return self._rt

    @property
    def areas(self) -> pd.DataFrame:
        """Peak area data, lazily generated on first access.

        Same structure as ``data`` but values are raw integrated peak areas
        rather than concentrations. Used for calibration factor calculation.
        Indexed by ``sample_hour``. TNMHC/TNMTC totals are not included.
        """
        if self._areas is None:
            self._areas = self._generate_areas()
        return self._areas

    @property
    def totals(self) -> pd.DataFrame:
        """Front and back chromatogram totals, lazily generated on first access.

        Columns: ``tnmhc_front``, ``tnmhc_back``, ``tnmtc_front``, ``tnmtc_back``
        (ppbC), plus ``date_time``, ``sample_type``, ``filename``.
        Indexed by ``sample_hour``. Unlike ``data``, totals are kept separate
        per chromatogram rather than summed.
        """
        if self._totals is None:
            self._totals = self._generate_totals_split()
        return self._totals

    # ------------------------------------------------------------------
    # Typed concentration properties
    # ------------------------------------------------------------------

    @property
    def ambient(self) -> pd.DataFrame:
        """Concentration data for ambient field samples."""
        return self._get_typed(SampleTypeLetter.AMBIENT)

    @property
    def blanks(self) -> pd.DataFrame:
        """Concentration data for blank samples."""
        return self._get_typed(SampleTypeLetter.BLANK)

    @property
    def cvs(self) -> pd.DataFrame:
        """Concentration data for canister verification standard samples."""
        return self._get_typed(SampleTypeLetter.CVS)

    @property
    def rts(self) -> pd.DataFrame:
        """Concentration data for retention time standard samples."""
        return self._get_typed(SampleTypeLetter.RTS)

    @property
    def lcs(self) -> pd.DataFrame:
        """Concentration data for laboratory control standard samples."""
        return self._get_typed(SampleTypeLetter.LCS)

    @property
    def mdl(self) -> pd.DataFrame:
        """Concentration data for method detection limit samples."""
        return self._get_typed(SampleTypeLetter.MDL_POINT)

    @property
    def calibration(self) -> pd.DataFrame:
        """Peak area data for calibration standard samples."""
        cache = self._typed_data
        key = SampleTypeLetter.CALIBRATION_POINT
        if key not in cache:
            df = self.areas[self.areas["sample_type"] == key.value]
            df.attrs["sample_type"] = key
            cache[key] = df
        return cache[key]

    @property
    def experimental(self) -> pd.DataFrame:
        """Concentration data for experimental samples."""
        return self._get_typed(SampleTypeLetter.EXPERIMENTAL)

    # ------------------------------------------------------------------
    # Typed retention time properties
    # ------------------------------------------------------------------

    @property
    def ambient_rt(self) -> pd.DataFrame:
        """Retention time data for ambient field samples."""
        return self._get_typed(SampleTypeLetter.AMBIENT, use_rt=True)

    @property
    def blanks_rt(self) -> pd.DataFrame:
        """Retention time data for blank samples."""
        return self._get_typed(SampleTypeLetter.BLANK, use_rt=True)

    @property
    def cvs_rt(self) -> pd.DataFrame:
        """Retention time data for canister verification standard samples."""
        return self._get_typed(SampleTypeLetter.CVS, use_rt=True)

    @property
    def rts_rt(self) -> pd.DataFrame:
        """Retention time data for retention time standard samples."""
        return self._get_typed(SampleTypeLetter.RTS, use_rt=True)

    @property
    def lcs_rt(self) -> pd.DataFrame:
        """Retention time data for laboratory control standard samples."""
        return self._get_typed(SampleTypeLetter.LCS, use_rt=True)

    @property
    def mdl_rt(self) -> pd.DataFrame:
        """Retention time data for method detection limit samples."""
        return self._get_typed(SampleTypeLetter.MDL_POINT, use_rt=True)

    @property
    def calibration_rt(self) -> pd.DataFrame:
        """Retention time data for calibration standard samples."""
        return self._get_typed(SampleTypeLetter.CALIBRATION_POINT, use_rt=True)

    @property
    def experimental_rt(self) -> pd.DataFrame:
        """Retention time data for experimental samples."""
        return self._get_typed(SampleTypeLetter.EXPERIMENTAL, use_rt=True)

    # ------------------------------------------------------------------
    # Public filter method
    # ------------------------------------------------------------------

    def check_filename_hour_alignment(self) -> pd.DataFrame:
        """Check whether each sample's filename hour matches its injection-derived sample hour.

        The filename hour is programmed into the GC sequence before samples are
        run. If the sequence is configured incorrectly the filename letter may
        not correspond to the actual collection time. This method compares the
        filename-encoded hour against the sample hour derived from the injection
        timestamp (injection time − 20 minutes, floored to the hour).

        Returns:
            DataFrame with columns:
                filename       — filename_base for each sample
                filename_hour  — integer hour (0-23) decoded from the filename letter
                sample_hour    — integer hour (0-23) derived from injection time
                injection_time — raw injection datetime (timezone-naive)
                aligned        — True if filename_hour == sample_hour

            Only samples with a readable injection datetime and a valid filename
            hour letter are included. Rows where ``aligned`` is False indicate a
            likely GC sequence configuration error.
        """
        from datetime import timedelta
        records = []
        for s in self.samples:
            fname_hour = s.filename_hour
            dt = s.datetime
            if dt is None or fname_hour is None:
                continue
            dt_naive = dt.replace(tzinfo=None)
            actual_hour = (dt_naive - timedelta(minutes=20)).hour
            if actual_hour != fname_hour:
                records.append({
                    "filename": s.filename_base,
                    "filename_hour": fname_hour,
                    "sample_hour": actual_hour,
                    "injection_time": dt_naive
                })
        return pd.DataFrame(records)
    
    def check_long_and_letter_sample_types(self) -> pd.DataFrame:
        """Compare the filename-derived sample type against the CDF sample_id for each sample.

        Returns:
            DataFrame of mismatches with columns:
                filename, injection_time, letter_sampletype, long_sampletype.
            Empty DataFrame (same columns) if all samples agree.
        """
        columns = ["filename", "injection_time", "letter_sampletype", "long_sampletype", "issue"]
        records = []
        for s in self.samples:
            long_type = s.sample_type_long  # lazy property — opens CDF file
            if long_type is None:
                records.append({
                    "filename":          s.filename_base,
                    "injection_time":    s.datetime,
                    "letter_sampletype": s.sample_type_letter,
                    "long_sampletype":   s.sample_type_long_raw,
                    "issue":             "unrecognised sample_id",
                })
                continue
            letter_name = s.sample_type_letter.name
            compatible  = LETTER_TO_LONG_NAMES.get(letter_name, frozenset())
            if long_type.name not in compatible:
                records.append({
                    "filename":          s.filename_base,
                    "injection_time":    s.datetime,
                    "letter_sampletype": s.sample_type_letter,
                    "long_sampletype":   long_type,
                    "issue":             "incompatible sample types",
                })
        if records:
            return pd.DataFrame(records)
        return pd.DataFrame(columns=columns)

    def filter_by_type(self, sample_type: SampleTypeLetter, use_rt: bool = False) -> pd.DataFrame:
        """Return rows matching a sample type from the concentration or RT DataFrame.

        Args:
            sample_type: The sample type to filter by.
            use_rt: If True, filter the retention time DataFrame instead.
        """
        source = self.rt if use_rt else self.data
        return source[source["sample_type"] == sample_type.value]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_typed(self, sample_type: SampleTypeLetter, use_rt: bool = False) -> pd.DataFrame:
        """Return a cached per-type DataFrame, computing it on first access."""
        cache = self._typed_rt if use_rt else self._typed_data
        if sample_type not in cache:
            df = self.filter_by_type(sample_type, use_rt=use_rt)
            df.attrs["sample_type"] = sample_type
            cache[sample_type] = df
        return cache[sample_type]

    def _get_chem_cols(self, include_totals: bool = True) -> List[int]:
        """AQS codes to use as DataFrame columns.

        Args:
            include_totals: If True (default), include TOTAL_CODES (TNMHC,
                TNMTC). Pass False for the RT frame where totals are never
                populated.
        """
        exclude = UNID_CODES if include_totals else UNID_CODES | TOTAL_CODES
        return [code for code in CompoundAQSCode if code not in exclude]

    def _filter_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove UnID and total codes from a peak table."""
        return df[~df['peak_name'].isin(UNID_CODES | TOTAL_CODES)]

    def _filter_totals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Select only TNMHC/TNMTC rows from a peak table."""
        return df[df['peak_name'].isin(TOTAL_CODES)]

    def _sum_totals(
        self, front_totals: pd.DataFrame, back_totals: pd.DataFrame
    ) -> pd.DataFrame:
        """Sum TNMHC and TNMTC values from front and back chromatograms."""
        merged = front_totals.merge(
            back_totals, on="peak_name", suffixes=("_front", "_back")
        )
        merged["peak_amount"] = (
            merged["peak_amount_front"] + merged["peak_amount_back"]
        )
        return merged[["peak_name", "peak_amount"]]

    def _build_amount_dict(
        self, front_df: pd.DataFrame, back_df: pd.DataFrame
    ) -> dict:
        """Build a dict mapping AQS code -> peak amount (ppbC)."""
        front_target = self._filter_targets(front_df)
        back_target = self._filter_targets(back_df)

        front_totals = self._filter_totals(front_df)
        back_totals = self._filter_totals(back_df)

        summed = self._sum_totals(front_totals, back_totals)

        voc_amounts = pd.concat(
            [front_target, back_target, summed], ignore_index=True
        )
        return voc_amounts.set_index("peak_name")["peak_amount"].to_dict()

    def _build_area_dict(
        self, front_df: pd.DataFrame, back_df: pd.DataFrame
    ) -> dict:
        """Build a dict mapping AQS code -> peak area."""
        front_target = self._filter_targets(front_df)
        back_target = self._filter_targets(back_df)
        voc_areas = pd.concat([front_target, back_target], ignore_index=True)
        return voc_areas.set_index("peak_name")["peak_area"].to_dict()

    def _build_rt_dict(
        self, front_df: pd.DataFrame, back_df: pd.DataFrame
    ) -> dict:
        """Build a dict mapping AQS code -> retention time."""
        front_target = self._filter_targets(front_df)
        back_target = self._filter_targets(back_df)

        voc_rt = pd.concat([front_target, back_target], ignore_index=True)
        return voc_rt.set_index("peak_name")["peak_retention_time"].to_dict()

    def _validate_peak_df(self, df: pd.DataFrame, filename) -> None:
        """Raise if a peakamounts DataFrame is missing required columns."""
        if "peak_name" not in df or "peak_amount" not in df:
            raise ValueError(f"Malformed peakamounts table in {filename}")

    def _generate_frame(self, attr: str, builder, include_totals: bool = True) -> pd.DataFrame:
        """Generate a DataFrame by extracting an attribute from each sample.

        Args:
            attr: Chromatogram property name ('peakamounts' or 'peaklocations').
            builder: Method that converts front/back DataFrames into a
                {AQS code: value} dict (e.g. _build_amount_dict or _build_rt_dict).
            include_totals: Passed to _get_chem_cols — False for the RT frame
                where TNMHC/TNMTC are never populated.
        """
        chem_cols = self._get_chem_cols(include_totals=include_totals)
        rows = []
        errors = 0

        for sample in self.samples:
            try:
                if sample.front.datetime is None or sample.back.datetime is None:
                    logger.warning(
                        "%s: could not read datetime from CDF file, skipping",
                        sample.filename_base,
                    )
                    errors += 1
                    continue

                dt = sample.front.datetime.replace(tzinfo=None)
                dt_back = sample.back.datetime.replace(tzinfo=None)
                if abs((dt - dt_back).total_seconds()) > 1:
                    logger.warning(
                        "%s: front/back datetime mismatch", sample.filename_base
                    )
                    continue

                front_df = getattr(sample.front, attr)
                back_df = getattr(sample.back, attr)

                if attr == "peakamounts":
                    self._validate_peak_df(front_df, sample.front.filename)
                    self._validate_peak_df(back_df, sample.back.filename)

                value_dict = builder(front_df, back_df)

                long_type = sample.sample_type_long
                if long_type is not None:
                    long_name = LONG_NAME_CANONICAL.get(long_type.name, long_type.name)
                else:
                    long_name = sample.sample_type_long_raw or None

                row = {
                    "date_time": dt,
                    "sample_type": sample.sample_type_letter.value,
                    "sample_type_long": long_name,
                    "filename": sample.filename_base,
                    **{code: value_dict.get(code) for code in chem_cols},
                }
                rows.append(row)
            except Exception:
                logger.exception("Error processing %s", sample.filename_base)
                errors += 1
                continue

        if errors:
            logger.warning(
                "%d of %d samples failed to process", errors, len(self.samples)
            )

        if not rows:
            logger.warning("No samples were successfully processed — returning empty DataFrame")
            chem_cols = self._get_chem_cols(include_totals=include_totals)
            empty = pd.DataFrame(columns=["date_time", "sample_type", "filename"] + chem_cols)
            empty.index = pd.DatetimeIndex([], name="sample_hour")
            return empty

        df = pd.DataFrame(rows)
        df.index = df["date_time"].apply(sample_hour)
        df.index.name = "sample_hour"
        return df.sort_index()

    def _generate_data(self) -> pd.DataFrame:
        """Generate a DataFrame of VOC concentrations for all samples."""
        return self._generate_frame("peakamounts", self._build_amount_dict)

    def _generate_totals_split(self) -> pd.DataFrame:
        """Generate a DataFrame with separate front and back TNMHC/TNMTC totals."""
        tnmhc = CompoundAQSCode.C_TNMHC
        tnmtc = CompoundAQSCode.C_TNMTC
        rows = []
        errors = 0

        for sample in self.samples:
            try:
                if sample.front.datetime is None or sample.back.datetime is None:
                    logger.warning(
                        "%s: could not read datetime from CDF file, skipping",
                        sample.filename_base,
                    )
                    errors += 1
                    continue

                dt = sample.front.datetime.replace(tzinfo=None)
                dt_back = sample.back.datetime.replace(tzinfo=None)
                if abs((dt - dt_back).total_seconds()) > 1:
                    logger.warning(
                        "%s: front/back datetime mismatch", sample.filename_base
                    )
                    continue

                front = self._filter_totals(sample.front.peakamounts).set_index("peak_name")["peak_amount"]
                back = self._filter_totals(sample.back.peakamounts).set_index("peak_name")["peak_amount"]

                rows.append({
                    "date_time": dt,
                    "sample_type": sample.sample_type_letter.value,
                    "filename": sample.filename_base,
                    "tnmhc_front": front.get(tnmhc),
                    "tnmhc_back": back.get(tnmhc),
                    "tnmtc_front": front.get(tnmtc),
                    "tnmtc_back": back.get(tnmtc),
                })
            except Exception:
                logger.exception("Error processing %s", sample.filename_base)
                errors += 1
                continue

        if errors:
            logger.warning(
                "%d of %d samples failed to process", errors, len(self.samples)
            )

        _cols = ["date_time", "sample_type", "filename",
                 "tnmhc_front", "tnmhc_back", "tnmtc_front", "tnmtc_back"]
        if not rows:
            logger.warning("No samples processed — returning empty totals DataFrame")
            empty = pd.DataFrame(columns=_cols)
            empty.index = pd.DatetimeIndex([], name="sample_hour")
            return empty

        df = pd.DataFrame(rows)
        df.index = df["date_time"].apply(sample_hour)
        df.index.name = "sample_hour"
        return df.sort_index()

    def _generate_areas(self) -> pd.DataFrame:
        """Generate a DataFrame of peak areas for all samples."""
        return self._generate_frame("peakareas", self._build_area_dict, include_totals=False)

    def _generate_rt(self) -> pd.DataFrame:
        """Generate a DataFrame of retention times for all samples."""
        return self._generate_frame("peaklocations", self._build_rt_dict, include_totals=False)

    def __repr__(self):
        return f"Dataset({self.folder}, n_samples={len(self.samples)})"
