"""Build dbt seeds from synthetic truth + refs (deterministic, no external data)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DBT = Path(__file__).resolve().parents[1]
SEEDS = DBT / "seeds"


def build_category_map() -> None:
    src = Path("platform/refs/space_category_map.csv")
    df = pd.read_csv(src, dtype=str)
    df = df.rename(columns={"messy": "raw_category", "canonical": "return_category"})
    df["map_version"] = "v1"
    df.to_csv(SEEDS / "seed_space_category_map.csv", index=False)
    print(f"category map: {len(df)} rows")


def build_calendar() -> None:
    df = pd.read_parquet("data/truth/academic_calendar.parquet")
    df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)
    df[["date", "term", "teaching_week", "is_holiday", "is_weekend"]].to_csv(
        SEEDS / "seed_academic_calendar.csv", index=False
    )
    print(f"calendar: {len(df)} rows")


def main() -> None:
    SEEDS.mkdir(parents=True, exist_ok=True)
    build_category_map()
    build_calendar()


if __name__ == "__main__":
    main()
