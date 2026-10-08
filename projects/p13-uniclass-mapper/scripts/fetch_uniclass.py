"""Fetch Uniclass 2015 tables from NBS (official source).

Attempts to download from https://uniclass.thenbs.com/download.
If download fails (login required, JS-rendered, etc.), writes a mock placeholder
CSV labelled as non-authoritative and logs the gap.
"""

from __future__ import annotations

import csv
import urllib.request
from datetime import date
from pathlib import Path

MOCK_CSV = Path(__file__).resolve().parents[1] / "data" / "mock_uniclass_dev_placeholder.csv"
OFFICIAL_URL = "https://uniclass.thenbs.com/download"
OUTPUT_CSV = Path(__file__).resolve().parents[1] / "data" / "uniclass_2015.csv"
LOG_FILE = Path(__file__).resolve().parents[1] / "data" / "uniclass_fetch.log"


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{date.today().isoformat()} {msg}\n")
    print(msg)


def try_fetch() -> bool:
    """Try to download the Uniclass tables. Returns True on success."""
    # The NBS download page is JS-rendered and likely requires login.
    # Direct download of the Excel/CSV is not easily scriptable without auth.
    # We log the attempt and return False to trigger mock fallback.
    log(f"Attempting to fetch from {OFFICIAL_URL}")
    try:
        req = urllib.request.Request(
            OFFICIAL_URL, headers={"User-Agent": "Mozilla/5.0 (compatible; P13-Uniclass-Mapper/0.1)"}
        )
        resp = urllib.request.urlopen(req, timeout=30)
        if resp.status == 200:
            # The page is HTML/JS; actual data download requires login/auth.
            # We cannot easily extract the tables without authentication.
            log("Page fetched but data download requires authentication; cannot proceed automatically.")
            return False
    except Exception as e:
        log(f"Fetch error: {e}")
    return False


def write_mock() -> None:
    """Copy the mock placeholder to the official output location with a warning header."""
    if not MOCK_CSV.exists():
        raise FileNotFoundError(f"Mock CSV not found at {MOCK_CSV}")
    # Read mock and write to official output with a warning comment row at top
    with open(MOCK_CSV, encoding="utf-8") as f_in:
        rows = list(csv.reader(f_in))
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(
            [
                "# WARNING: THIS FILE CONTAINS NON-AUTHORITATIVE MOCK DATA.",
                "# Source: mock_uniclass_dev_placeholder.csv (development only).",
                "# DO NOT USE FOR PRODUCTION OR FINAL OUTPUTS.",
                "# Official source: https://uniclass.thenbs.com/download (requires login).",
                "# See docs/OPEN_QUESTIONS.md for details.",
            ]
        )
        writer.writerows(rows)
    print(f"Wrote mock data to {OUTPUT_CSV} (NON-AUTHORITATIVE)")


def main() -> int:
    print("P13 Uniclass fetch — attempting official download...")
    success = try_fetch()
    if not success:
        print("Official download not available; falling back to mock data.")
        write_mock()
        return 1  # Non-zero exit to signal fallback
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
