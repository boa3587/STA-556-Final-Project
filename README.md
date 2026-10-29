# Physical inactivity and diabetes across US counties

STA 556 Final Project — *Benjamin owusu Acquah*, Northern Arizona University, Fall 2026

## Question

Across US counties, how strongly is the prevalence of physical inactivity associated with diabetes prevalence, after accounting for obesity and smoking?

## Data

- **Source:** CDC [PLACES: Local Data for Better Health](https://www.cdc.gov/places/), County Data, 2025 release (Socrata dataset `swc5-untb` on data.cdc.gov). Public domain.
- **Access:** the SODA API at `https://data.cdc.gov/resource/swc5-untb.json`. No API key is needed.
- **Query:** measures `DIABETES`, `LPA` (no leisure-time physical activity), `OBESITY`, `CSMOKING`; `data_value_type = 'Age-adjusted prevalence'`.
- **Unit of observation:** a US county (50 states + DC).

The first run of the notebook downloads the data and saves it, unchanged, to `data/raw/places_county_2025.csv`, together with `data/raw/places_county_2025_provenance.json` (endpoint, query parameters, retrieval date). Later runs read the saved snapshot, so results stay the same even if the API changes. To re-download, call `fetch_places(..., refresh=True)`.

## Repository layout

```
.
├── README.md
├── requirements.txt
├── .devcontainer/
│   └── devcontainer.json   # Codespace setup: Python 3.12, packages, extensions
├── analysis.ipynb          # the report: run top to bottom from the repo root
├── src/
│   ├── fetch.py            # API download + raw-data cache
│   ├── clean.py            # validation, long-to-wide reshape, missingness
│   └── analysis.py         # summaries, least squares (NumPy), bootstrap
├── data/
│   ├── raw/                # API response, never edited by hand
│   └── processed/          # one row per county, analysis-ready
└── figures/                # all figures saved by the notebook
```

## How to reproduce

**In GitHub Codespaces (easiest):** click **Code → Codespaces → Create codespace on main**. The packages in `requirements.txt` and the Python and Jupyter extensions install automatically. Open `analysis.ipynb` and choose **Run All**.

**On your own computer**, from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace analysis.ipynb
```

Or open `analysis.ipynb` in Jupyter and choose **Restart & Run All**. All paths are relative to the repository root.

## Data workflow

1. **Download** (`src/fetch.py`): page through the API and cache the raw rows.
2. **Validate** (`src/clean.py::validate_raw`): required columns, all measures present, no duplicate county × measure rows, prevalences in [0, 100].
3. **Reshape** (`tidy_places`): the API returns one row per county per measure; pivot to one row per county.
4. **Missingness** (`missingness_report`, `drop_incomplete`): report missing values, then use complete cases.
5. **Analysis** (`src/analysis.py`): least squares with `np.linalg.lstsq`, diagnostics, and a case bootstrap for coefficient CIs.

## Method

Multiple linear regression of diabetes prevalence on physical inactivity, obesity and smoking, fit with NumPy linear algebra. Uncertainty comes from a case (pairs) bootstrap over counties with B = 2000 resamples and a fixed seed (556).

## Limitations

See Section 7 of the notebook. In short: PLACES values are model-based estimates, the data are ecological, and the design is observational.