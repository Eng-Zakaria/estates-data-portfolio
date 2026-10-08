"""P16 settings (all synthetic unless BDG2 cache present; see docs)."""

from __future__ import annotations

from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
OUTPUTS = PROJECT / "outputs"
CACHE = Path("data/p16_bdg2")

SEED = 7
TARIFF_GBP_PER_KWH = 0.28  # illustrative configurable tariff (see docs/methodology.md)
OOH_THRESHOLD_PCT_PEAK = 0.5
LOOKBACK_DAYS_BASELINE = 28
MIN_TRAIN_DAYS = 14

# DESNZ 2025 factors (kWh -> kgCO2e), loaded from the P04 seed when present,
# else these script-read values from the official workbook (see DATA provenance).
FALLBACK_FACTORS = {"electricity": 0.177, "natural_gas": 0.2027}
