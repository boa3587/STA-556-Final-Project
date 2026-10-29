"""Summaries, least squares via NumPy linear algebra, and a case bootstrap."""

import numpy as np
import pandas as pd


def describe(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Descriptive summary table for the analysis variables."""
    cols = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
    return df[columns].describe().T[cols].round(2)


def design_matrix(df: pd.DataFrame, xcols: list[str]) -> np.ndarray:
    """Build the n x (p+1) design matrix X with an intercept column first."""
    X = df[xcols].to_numpy(dtype=float)
    return np.column_stack([np.ones(len(X)), X])


def ols_fit(X: np.ndarray, y: np.ndarray) -> dict:
    """Ordinary least squares with np.linalg.lstsq (no explicit matrix inverse).

    Returns a dict with coefficients, classical standard errors, R^2,
    fitted values, residuals, the rank of X, and its condition number.
    """
    y = np.asarray(y, dtype=float)
    beta, _, rank, sing_vals = np.linalg.lstsq(X, y, rcond=None)
    fitted = X @ beta
    resid = y - fitted
    n, p = X.shape
    sigma2 = resid @ resid / (n - p)
    # Var(beta_hat) = sigma^2 (X'X)^{-1}, computed by solving a linear system
    cov = sigma2 * np.linalg.solve(X.T @ X, np.eye(p))
    r2 = 1 - (resid @ resid) / np.sum((y - y.mean()) ** 2)
    return {"beta": beta, "se": np.sqrt(np.diag(cov)), "r2": r2,
            "fitted": fitted, "resid": resid, "rank": rank,
            "cond": sing_vals.max() / sing_vals.min()}


def coef_table(fit: dict, names: list[str]) -> pd.DataFrame:
    """Tidy coefficient table."""
    return pd.DataFrame({"estimate": fit["beta"], "std_error": fit["se"]},
                        index=["intercept"] + list(names)).round(4)


def bootstrap_coefs(X: np.ndarray, y: np.ndarray, n_boot: int,
                    rng: np.random.Generator) -> np.ndarray:
    """Case (pairs) bootstrap: resample counties with replacement and refit OLS.

    Each replicate draws n rows of (x_i, y_i) with replacement, so we resample
    whole units (counties) rather than individual cells. Returns an
    (n_boot x p) array of coefficient estimates.
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    out = np.empty((n_boot, X.shape[1]))
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        out[b], *_ = np.linalg.lstsq(X[idx], y[idx], rcond=None)
    return out


def percentile_ci(boot: np.ndarray, level: float = 0.95) -> np.ndarray:
    """Percentile confidence intervals for each column of a bootstrap array."""
    alpha = (1 - level) / 2
    return np.quantile(boot, [alpha, 1 - alpha], axis=0).T
