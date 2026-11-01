# Physical inactivity and diabetes across US counties

STA 556 Final Project — **Benjamin Owusu Acquah**, Northern Arizona University, Fall 2026

## Question

Across US counties, how strongly is the prevalence of physical inactivity associated with diabetes prevalence, after accounting for obesity and smoking?

## Data

| | |
|---|---|
| **Source** | CDC [PLACES: Local Data for Better Health](https://www.cdc.gov/places/), County Data, 2025 release. Public domain. |
| **Dataset ID** | `swc5-untb` on data.cdc.gov |
| **Access** | Socrata Open Data API (SODA): `https://data.cdc.gov/resource/swc5-untb.json`. No API key is needed. |
| **Unit of observation** | A US county in 48 states + DC (Kentucky and Pennsylvania have no estimates for these measures in the 2025 release) |
| **Measure type** | Age-adjusted prevalence (% of adults) |

| Variable | PLACES measure ID | Meaning | Role |
|---|---|---|---|
| `diabetes` | `DIABETES` | Diagnosed diabetes among adults | Response |
| `lpa` | `LPA` | No leisure-time physical activity among adults | Main predictor |
| `obesity` | `OBESITY` | Obesity among adults | Control |
| `csmoking` | `CSMOKING` | Current cigarette smoking among adults | Control |

The first run of `notebooks/01_data_processing.ipynb` downloads the data and saves it, unchanged, to `data/raw/places_county_2025.csv`, together with `data/raw/places_county_2025_provenance.json` (endpoint, query parameters, retrieval date). Later runs read the saved snapshot, so results stay the same even if the API changes. To download again, call `fetch_places(..., refresh=True)`.

## Repository layout

```
.
├── README.md
├── final_report.qmd              # Final report (Quarto source)
├── final_report.html             # Final report (rendered)
├── requirements.txt              # Python packages
├── .gitignore
├── .devcontainer/
│   └── devcontainer.json         # Codespace setup: Python 3.14, Quarto, packages, extensions
├── notebooks/
│   ├── 01_data_processing.ipynb  # Step 1: download, inspect, validate, clean, reshape, save
│   └── 02_analysis.ipynb         # Step 2: summaries, plots, least squares, bootstrap
├── src/
│   ├── __init__.py
│   ├── fetch.py                  # API download, raw-data cache, provenance record
│   ├── clean.py                  # validation, long-to-wide reshape, missingness
│   └── analysis.py               # summaries, least squares (NumPy), bootstrap
├── data/
│   ├── raw/                      # API snapshot + provenance (never edited by hand)
│   └── processed/                # county_analysis.csv: one row per county
└── figures/                      # all figures, saved by 02_analysis.ipynb
```

## Environment

- **Python 3.14.2**
- Package versions are pinned in `requirements.txt` (exact `==` versions used for this analysis).
- Quarto renders the final report.

## How to reproduce

Run everything from the repository root. All paths are relative, and the first code cell of each notebook switches to the repository root, so the notebooks also work when opened from `notebooks/`.

**In GitHub Codespaces (easiest):** click **Code → Codespaces → Create codespace on main**. Python, Quarto, the packages in `requirements.txt`, and the Python, Jupyter and Quarto extensions install automatically. Then, **in this order**:

1. Open `notebooks/01_data_processing.ipynb` and choose **Run All**. This downloads and cleans the data and saves `data/processed/county_analysis.csv`.
2. Open `notebooks/02_analysis.ipynb` and choose **Run All**. This runs the analysis and saves the figures.
3. Render the final report in the terminal:

```bash
quarto render final_report.qmd
```

**On your own computer:** install [Quarto](https://quarto.org/docs/get-started/), then from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace notebooks/01_data_processing.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/02_analysis.ipynb
quarto render final_report.qmd
```

## Data workflow

Steps 1–4 are carried out and documented in `notebooks/01_data_processing.ipynb`; step 5 is `notebooks/02_analysis.ipynb`. The final report (`final_report.qmd`) summarizes the question, data, methods, results and limitations, reading the processed data and figures.

1. **Download** (`src/fetch.py::fetch_places`): page through the API, save the raw rows and a provenance record.
2. **Validate** (`src/clean.py::validate_raw`): required columns present, all four measures returned, no duplicate county × measure rows, prevalences in [0, 100].
3. **Filter and reshape** (`tidy_places`): remove the national total and territories, convert text to numbers, and pivot from one row per county per measure (long) to one row per county (wide).
4. **Missingness** (`missingness_report`, `drop_incomplete`): report how many values are missing and where, then use complete cases. One county, Loving County, Texas (population 43), has all four estimates suppressed by the CDC and is removed.
5. **Analysis** (`src/analysis.py`): descriptive summaries, least squares with `np.linalg.lstsq`, diagnostics (R², condition number, residual plots), and a case bootstrap for coefficient confidence intervals.

## Method

Multiple linear regression of diabetes prevalence on physical inactivity, obesity and smoking, fit with NumPy linear algebra (no explicit matrix inverse). Uncertainty comes from a case (pairs) bootstrap that resamples counties with replacement, with B = 2000 resamples and a fixed seed (`np.random.default_rng(556)`).

## Figures

| File | Contents |
|---|---|
| `figures/eda_histograms.png` | Distribution of each measure across counties |
| `figures/eda_scatter.png` | Diabetes against each predictor |
| `figures/eda_pairplot.png` | Pair plot of all four measures (seaborn) |
| `figures/corr_heatmap.png` | Correlation heatmap (seaborn) |
| `figures/diagnostics.png` | Residuals vs fitted, normal Q-Q plot |
| `figures/bootstrap_lpa.png` | Bootstrap distribution of the physical-inactivity coefficient |
| `figures/communication_figure.png` | Main result |

## Results

Across 2,956 counties in 48 states and DC:

- Holding obesity and smoking fixed, a county with one percentage point more physical inactivity has, on average, **0.35 percentage points** higher diabetes prevalence (95% bootstrap CI 0.34 to 0.36). A 10-point difference in inactivity corresponds to about 3.5 points more diabetes.
- After accounting for inactivity, the associations with obesity (0.03, CI 0.02 to 0.05) and smoking (0.01, CI −0.02 to 0.04) are small; the smoking interval includes zero.
- The model explains **R² = 0.77** of the county-to-county variation in diabetes prevalence.
- Residual plots show mild curvature and unequal variance, so uncertainty is estimated with a case bootstrap (B = 2000); the bootstrap standard errors are larger than the classical ones, especially for smoking.

**Answer:** physical inactivity is strongly associated with county diabetes prevalence, even after accounting for obesity and smoking. See `final_report.html` for the full results.

## Limitations

- PLACES values are model-based small-area estimates, not direct county counts.
- The data are ecological: county-level associations do not describe individuals.
- The design is observational, so the results are associations, not causal effects; income, age structure, diet and access to care are not in the model.
- The measures are self-reported, and inactivity counts only leisure-time activity.
- Residuals show mild curvature and unequal variance, so a straight-line model does not fully capture the relationship.
- Neighbouring counties are similar, so the bootstrap (which treats counties as independent) likely understates uncertainty.
- Kentucky and Pennsylvania have no estimates for these measures, so results apply to 48 states + DC.

See the Limitations section of `final_report.qmd` for details.
