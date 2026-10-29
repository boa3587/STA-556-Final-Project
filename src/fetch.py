"""Download county-level PLACES data from the CDC Socrata (SODA) API.

Ingestion is kept separate from analysis: the raw API response is saved to
data/raw/ the first time it is downloaded (with a provenance record), and every
later run reads that local snapshot instead of calling the API again.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

# PLACES: Local Data for Better Health, County Data, 2025 release
DATASET_ID = "swc5-untb"
BASE_URL = f"https://data.cdc.gov/resource/{DATASET_ID}.json"

# Measure IDs used in this project (see https://www.cdc.gov/places/measure-definitions/)
MEASURES = ["DIABETES", "LPA", "OBESITY", "CSMOKING"]


def fetch_places(
    measures: list[str],
    raw_path: str | Path,
    data_value_type: str = "Age-adjusted prevalence",
    page_size: int = 10_000,
    refresh: bool = False,
    timeout: int = 60,
) -> pd.DataFrame:
    """Return county-level PLACES rows for the given measures (long format).

    Parameters
    ----------
    measures : list of str
        PLACES measure IDs, e.g. ["DIABETES", "LPA"].
    raw_path : str or Path
        Where the raw CSV is cached, relative to the repository root.
    data_value_type : str
        "Age-adjusted prevalence" or "Crude prevalence".
    page_size : int
        Rows per API request. The API is paginated, so we keep requesting
        pages until a short page comes back.
    refresh : bool
        If True, download again even if a cached file exists.
    timeout : int
        Seconds to wait for each API response.

    Returns
    -------
    pandas.DataFrame with one row per county x measure.
    """
    raw_path = Path(raw_path)
    if raw_path.exists() and not refresh:
        return pd.read_csv(raw_path, dtype={"locationid": str})

    ids = ",".join(f"'{m}'" for m in measures)
    params = {"$where": f"measureid in({ids}) AND data_value_type='{data_value_type}'",
              "$limit": page_size, "$order": ":id"}

    pages, offset = [], 0
    while True:
        resp = requests.get(BASE_URL, params={**params, "$offset": offset}, timeout=timeout)
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            break
        pages.append(pd.DataFrame(rows))
        if len(rows) < page_size:
            break
        offset += page_size

    if not pages:
        raise RuntimeError("The API returned no rows; check the measure IDs and filter.")

    df = pd.concat(pages, ignore_index=True)
    # Drop the nested geometry column (a dict) so the snapshot is a flat CSV
    df = df.drop(columns=[c for c in ["geolocation"] if c in df.columns])
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(raw_path, index=False)
    write_provenance(raw_path, params, n_rows=len(df))
    return pd.read_csv(raw_path, dtype={"locationid": str})


def write_provenance(raw_path: Path, params: dict, n_rows: int) -> Path:
    """Record where the raw snapshot came from, next to the snapshot itself."""
    record = {
        "source": "CDC PLACES: Local Data for Better Health, County Data, 2025 release",
        "dataset_id": DATASET_ID,
        "endpoint": BASE_URL,
        "query_parameters": {k: v for k, v in params.items() if k != "$limit"},
        "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_rows": n_rows,
        "file": raw_path.name,
    }
    out = raw_path.with_name(raw_path.stem + "_provenance.json")
    out.write_text(json.dumps(record, indent=2))
    return out
