import json
from io import BytesIO
from zipfile import ZipFile
import numpy as np
import pandas as pd
import requests
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def load_owid_generation_by_source(country_code="BGD"):
    url = f"https://ourworldindata.org/grapher/electricity-prod-source-stacked.csv?country=~{country_code}"
    df = pd.read_csv(url)
    if "Year" in df.columns:
        df = df.rename(columns={"Year": "year"})
    if "year" not in df.columns:
        if "date" in df.columns:
            df["year"] = pd.to_datetime(df["date"]).dt.year
        else:
            raise ValueError("No year column")
    df["year"] = df["year"].astype(int)
    drop_cols = set(["Entity", "Code", "date"])
    value_cols = [c for c in df.columns if c not in drop_cols and c != "year"]
    for c in value_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.groupby("year", as_index=False)[value_cols].sum()
    return df

def holt_forecast_yearly(values, periods):
    y = pd.Series(values).astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    if len(y) < 4:
        last = float(y.iloc[-1]) if len(y) else 0.0
        return np.array([last] * periods, dtype=float)
    idx = pd.date_range("2000-01-01", periods=len(y), freq="YS")
    s = pd.Series(y.to_numpy(), index=idx)
    model = ExponentialSmoothing(s, trend="add", seasonal=None, initialization_method="estimated")
    fit = model.fit(optimized=True)
    fc = fit.forecast(periods)
    return np.array(fc, dtype=float)

def forecast_mix(df_yearly, horizon=15):
    df = df_yearly.copy()
    years = df["year"].astype(int).values
    last_year = int(years.max())
    future_years = np.arange(last_year + 1, last_year + horizon + 1, dtype=int)
    out = pd.DataFrame({"year": np.concatenate([years, future_years])})
    value_cols = [c for c in df.columns if c != "year"]
    for col in value_cols:
        hist = df[col].astype(float).values
        fc = holt_forecast_yearly(hist, len(future_years))
        full = np.concatenate([hist, np.clip(fc, 0, None)])
        out[col] = full
    return out

def compute_adequacy(forecast_df, demand_growth=0.045, reserve_margin=0.15):
    df = forecast_df.copy()
    gen_cols = [c for c in df.columns if c != "year"]
    df["total_generation"] = df[gen_cols].sum(axis=1)
    base_year = int(df["year"].min())
    base_total = float(df.loc[df["year"] == base_year, "total_generation"].iloc[0])
    base_peak = base_total / (1.0 + reserve_margin) if base_total > 0 else 1.0
    df["peak_demand"] = base_peak * ((1.0 + demand_growth) ** (df["year"] - base_year))
    df["available_supply"] = df["total_generation"]
    df["adequacy_index"] = (df["available_supply"] - df["peak_demand"]) / df["peak_demand"]
    df["adequacy_index"] = df["adequacy_index"].clip(-0.5, 0.5)
    return df[["year", "adequacy_index", "available_supply", "peak_demand", "total_generation"]]

def download_eia_bulk_manifest():
    url = "http://api.eia.gov/bulk/manifest.txt"
    r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    lines = [ln.strip() for ln in r.text.splitlines() if ln.strip()]
    rows = []
    for ln in lines:
        try:
            rows.append(json.loads(ln))
        except Exception:
            pass
    return rows

def download_eia_bulk_dataset(access_url):
    r = requests.get(access_url, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    zf = ZipFile(BytesIO(r.content))
    names = [n for n in zf.namelist() if n.lower().endswith(".txt")]
    if not names:
        return []
    data = []
    with zf.open(names[0]) as f:
        for line in f:
            try:
                data.append(json.loads(line.decode("utf-8").strip()))
            except Exception:
                pass
    return data
