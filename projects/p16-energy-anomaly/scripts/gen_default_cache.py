"""Generate default-profile truth tables for P16 planted-finding verification.

Writes ONLY the tables P16 needs (meters, meter_readings_hh, weather,
buildings) plus ground_truth.yaml into data/p16_default/ (gitignored).
The shared small-profile data/ tree is left untouched.
"""

from __future__ import annotations

from pathlib import Path

from campus_synth.config import PROFILES
from campus_synth.generator import generate_all
from campus_synth.ground_truth import write_ground_truth

OUT = Path("data/p16_default")
WANT = ("meters", "meter_readings_hh", "weather", "buildings")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    profile = PROFILES["default"]
    print(f"generating profile=default seed={profile.seed} ...", flush=True)
    tables, gt = generate_all(profile)
    for name in WANT:
        tables[name].to_parquet(OUT / f"{name}.parquet", index=False)
        print(f"wrote {name}: {len(tables[name])} rows", flush=True)
    write_ground_truth(gt, [], OUT / "ground_truth.yaml")
    print("done", flush=True)


if __name__ == "__main__":
    main()
