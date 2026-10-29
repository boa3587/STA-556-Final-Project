"""Validation, cleaning and reshaping of the raw PLACES data."""

import pandas as pd

REQUIRED_COLUMNS = ["stateabbr", "locationname", "locationid", "measureid",
                    "data_value_type", "data_value", "totalpopulation"]

# PLACES covers the 50 states + DC; drop any national or territory rows
EXCLUDE_STATES = {"US", "PR", "GU", "VI", "AS", "MP"}


def validate_raw(df: pd.DataFrame, measures: list[str]) -> dict:
    """Check the raw long-format data before cleaning. Raises ValueError on problems.

    Checks: required columns exist, all requested measures are present,
    no duplicate county x measure rows, and prevalences lie in [0, 100].
    Returns a small dict of facts for the report.
    """
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Raw data is missing columns: {missing_cols}. "
                         "Check the field names on the dataset's API page.")

    missing_measures = set(measures) - set(df["measureid"].unique())
    if missing_measures:
        raise ValueError(f"Measures not found in raw data: {sorted(missing_measures)}")

    dupes = df.duplicated(subset=["locationid", "measureid"]).sum()
    if dupes:
        raise ValueError(f"{dupes} duplicate county x measure rows found.")

    values = pd.to_numeric(df["data_value"], errors="coerce")
    out_of_range = ((values < 0) | (values > 100)).sum()
    if out_of_range:
        raise ValueError(f"{out_of_range} prevalence values outside [0, 100].")

    return {"n_rows": len(df),
            "n_counties": df["locationid"].nunique(),
            "n_states": df["stateabbr"].nunique(),
            "n_nonnumeric_values": int(values.isna().sum())}


def tidy_places(df: pd.DataFrame, measures: list[str]) -> pd.DataFrame:
    """Reshape long data (county x measure rows) to wide (one row per county).

    Steps
    -----
    1. Keep only the requested measures and the 50 states + DC.
    2. Convert data_value and totalpopulation to numbers.
    3. Pivot so each measure becomes a column named in lowercase.
    """
    out = df[df["measureid"].isin(measures)].copy()
    out = out[~out["stateabbr"].isin(EXCLUDE_STATES)]
    out["data_value"] = pd.to_numeric(out["data_value"], errors="coerce")
    out["totalpopulation"] = pd.to_numeric(
        out["totalpopulation"].astype(str).str.replace(",", ""), errors="coerce")

    # One row per county with its identifiers. Pivoting on locationid alone and
    # joining back keeps every county, even one whose name is blank or whose
    # values are all missing (pivot_table would silently drop those rows).
    ids = out.groupby("locationid")[["stateabbr", "locationname", "totalpopulation"]].first()
    values = (out.pivot_table(index="locationid", columns="measureid",
                              values="data_value", aggfunc="first")
                 .reindex(columns=measures))
    wide = ids.join(values, how="left").reset_index()
    wide.columns.name = None
    wide = wide[["locationid", "stateabbr", "locationname"] + measures + ["totalpopulation"]]
    return wide.rename(columns={m: m.lower() for m in measures})


def missingness_report(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Count and percent missing for each column (a table for the report)."""
    n_missing = df[columns].isna().sum()
    return pd.DataFrame({"n_missing": n_missing,
                         "pct_missing": (100 * n_missing / len(df)).round(2)})


def drop_incomplete(df: pd.DataFrame, columns: list[str]) -> tuple[pd.DataFrame, int]:
    """Complete-case analysis: drop counties missing any analysis variable.

    Returns the filtered frame and the number of rows dropped, so the
    decision is reported rather than hidden.
    """
    keep = df.dropna(subset=columns)
    return keep.reset_index(drop=True), len(df) - len(keep)
