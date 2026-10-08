"""BDG2 open-data fetch (Zenodo DOI 10.5281/zenodo.3887306, CC-BY 4.0).

Verified live 2026-10-07 on the Zenodo record page: Creative Commons
Attribution 4.0 International, 3,053 meters / 1,636 buildings, hourly
2016-2017, md5 44393dc4cf61e84dec105e955368c890 (matches pinned ZIP_MD5).

Archive layout (verified by inspection, not memory): a GitHub snapshot
whose meter series are WIDE cleaned CSVs (timestamp + one column per
building) plus a single weather.csv keyed by site_id. We therefore extract
metadata + weather + the electricity wide table once, then load only the
chosen education-building columns. Nothing is committed (data/ is
gitignored; *.parquet is gitignored too).
"""

from __future__ import annotations

import hashlib
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from .config import CACHE

DOI_URL = "https://doi.org/10.5281/zenodo.3887306"
ZIP_URL = "https://zenodo.org/records/3887306/files/buds-lab/building-data-genome-project-2-v1.0.zip?download=1"
ZIP_MD5 = "44393dc4cf61e84dec105e955368c890"
LICENCE = "CC-BY 4.0 International (Zenodo record 3887306; Miller et al., Sci Data 7:368, 2020)"

N_BUILDINGS_MIN, N_BUILDINGS_MAX = 20, 50
PER_SITE_MAX = 25


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_zip(dest: Path | None = None) -> Path:
    dest = dest or (CACHE / "bdg2-v1.0.zip")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and _md5(dest) == ZIP_MD5:
        print(f"cache hit {dest}")
        return dest
    print(f"downloading 595 MB {ZIP_URL} ...")
    urllib.request.urlretrieve(ZIP_URL, dest)
    digest = _md5(dest)
    if digest != ZIP_MD5:
        raise ValueError(f"md5 mismatch: {digest} != {ZIP_MD5}")
    print(f"verified {dest}")
    return dest


def _prefix(names: list[str]) -> str:
    meta = next(n for n in names if n.endswith("data/metadata/metadata.csv"))
    return meta[: -len("data/metadata/metadata.csv")]


def select_subset(zip_path: Path) -> dict[str, object]:
    """Choose education buildings with electricity meters at the top-2 sites.

    Building IDs look like Panther_education_Rosalie (site_use_name).
    Returns {"buildings": [...], "sites": [...], "timezones": {...}}.
    """
    zf = zipfile.ZipFile(zip_path)
    names = zf.namelist()
    prefix = _prefix(names)
    with zf.open(prefix + "data/metadata/metadata.csv") as f:
        meta = pd.read_csv(f)
    edu = meta[
        meta["primaryspaceusage"].str.contains("education", case=False, na=False) & meta["electricity"].notna()
    ].copy()
    # keep only buildings that actually have a column in the electricity table
    with zf.open(prefix + "data/meters/cleaned/electricity_cleaned.csv") as f:
        header = f.readline().decode()
    have = set(header.strip().split(","))
    edu = edu[edu["building_id"].isin(have)]
    sites = edu.groupby("site_id").size().sort_values(ascending=False).head(2).index.tolist()
    chosen: list[str] = []
    for site in sites:
        chosen += sorted(edu[edu.site_id == site]["building_id"].tolist())[:PER_SITE_MAX]
    chosen = chosen[:N_BUILDINGS_MAX]
    if len(chosen) < N_BUILDINGS_MIN:
        raise ValueError(f"only {len(chosen)} education buildings with electricity columns")
    tz = {s: str(edu[edu.site_id == s]["timezone"].mode().iloc[0]) for s in sites}
    return {"buildings": chosen, "sites": sites, "timezones": tz, "prefix": prefix}


def extract_subset(zip_path: Path, out: Path | None = None) -> Path:
    """Extract metadata + weather + electricity wide table + provenance files."""
    out = out or (CACHE / "subset")
    out.mkdir(parents=True, exist_ok=True)
    sel = select_subset(zip_path)
    assert isinstance(sel["buildings"], list)
    prefix = str(sel["prefix"])
    zf = zipfile.ZipFile(zip_path)
    for member in (
        "data/metadata/metadata.csv",
        "data/weather/weather.csv",
        "data/meters/cleaned/electricity_cleaned.csv",
        "LICENSE",
        "README.md",
    ):
        target = out / Path(member).name
        if not target.exists():
            with zf.open(prefix + member) as src, open(target, "wb") as dst:
                dst.write(src.read())
    manifest = out / "MANIFEST.txt"
    manifest.write_text(
        f"source: {DOI_URL}\nlicence: {LICENCE}\nzip_md5: {ZIP_MD5}\n"
        f"buildings: {len(sel['buildings'])}\nsites: {sel['sites']}\n"
        f"timezones: {sel['timezones']}\n",
        encoding="utf-8",
    )
    (out / "buildings.csv").write_text("building_id\n" + "\n".join(sel["buildings"]) + "\n", encoding="utf-8")
    print(f"extracted {len(sel['buildings'])} buildings {sel['sites']} -> {out}")
    return out


def load_bdg2_subset(subset: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Long-format readings (building, site, ts_utc, value kWh) + hourly weather.

    Timestamps in the release are site-local naive; they are localised with the
    site timezone from metadata, then converted to UTC (daylight transitions
    kept, never fabricated).
    """
    subset = subset or (CACHE / "subset")
    buildings = pd.read_csv(subset / "buildings.csv")["building_id"].tolist()
    meta = pd.read_csv(subset / "metadata.csv")
    meta = meta[meta.building_id.isin(buildings)].set_index("building_id")
    elec = pd.read_csv(subset / "electricity_cleaned.csv", usecols=["timestamp", *buildings])
    frames = []
    for site, grp in meta.groupby("site_id"):
        tz = str(grp["timezone"].mode().iloc[0])
        cols = [b for b in grp.index if b in elec.columns]
        long = elec[["timestamp", *cols]].melt(id_vars="timestamp", var_name="building", value_name="value")
        long["ts_utc"] = (
            pd.to_datetime(long["timestamp"])
            .dt.tz_localize(tz, ambiguous="NaT", nonexistent="shift_forward")
            .dt.tz_convert("UTC")
        )
        long["site"] = site
        frames.append(long.drop(columns=["timestamp"]))
    readings = pd.concat(frames, ignore_index=True).dropna(subset=["ts_utc"])
    wx = pd.read_csv(subset / "weather.csv")
    wx = wx[wx.site_id.isin(meta["site_id"].unique())].copy()
    tz_of = meta.reset_index().drop_duplicates("site_id").set_index("site_id")["timezone"].to_dict()
    wx_frames = []
    for site, g in wx.groupby("site_id"):
        g = g.copy()
        g["ts_utc"] = (
            pd.to_datetime(g["timestamp"])
            .dt.tz_localize(tz_of[site], ambiguous="NaT", nonexistent="shift_forward")
            .dt.tz_convert("UTC")
        )
        g["temp_c"] = pd.to_numeric(g["airTemperature"], errors="coerce")
        g["site"] = site
        wx_frames.append(g[["site", "ts_utc", "temp_c"]])
    weather = pd.concat(wx_frames, ignore_index=True).dropna(subset=["ts_utc"])
    readings["value"] = pd.to_numeric(readings["value"], errors="coerce")
    return (
        readings.sort_values(["building", "ts_utc"]).reset_index(drop=True),
        weather.sort_values(["site", "ts_utc"]).reset_index(drop=True),
    )
