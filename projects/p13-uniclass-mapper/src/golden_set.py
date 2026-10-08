"""Golden set builder for P13 Uniclass mapper.

Creates labelled examples (messy description → true code) for evaluation.
Generates review_sample.csv for human review.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import pandas as pd

# Golden set examples (messy description -> true code)
# These are synthetic but realistic examples based on the mock Uniclass data
GOLDEN_EXAMPLES = [
    # AHU / Air Handling Units
    ("AHU-03 air hndlg unit L2", "Pr_50_20_10", "Products"),
    ("AHU-01 air handling unit level 2", "Pr_50_20_10", "Products"),
    ("AHU-02 air handling unit roof", "Pr_50_20_10", "Products"),
    ("air handling unit 03", "Pr_50_20_10", "Products"),
    ("AHU no 3 air handler", "Pr_50_20_10", "Products"),
    ("air handling unit plantroom", "Pr_50_20_10", "Products"),
    # Boilers
    ("Boiler no 2 (Remeha)", "Pr_50_10_10", "Products"),
    ("Boiler no 1 (Hamworthy)", "Pr_50_10_10", "Products"),
    ("Boiler no 3 (Worcester Bosch)", "Pr_50_10_10", "Products"),
    ("oil boiler plantroom", "Pr_50_10_10", "Products"),
    ("condensing boiler 2", "Pr_50_10_10", "Products"),
    ("biomass boiler plant", "Pr_50_10_10", "Products"),
    # Fan Coil Units
    ("FCU fan coil rm 214", "Pr_50_20_40", "Products"),
    ("FCU fan coil rm 101", "Pr_50_20_40", "Products"),
    ("FCU-05 fan coil unit room 214", "Pr_50_20_20", "Products"),
    ("fan coil unit room 305", "Pr_50_20_20", "Products"),
    ("fan coil rm 214", "Pr_50_20_40", "Products"),
    # VAV Boxes
    ("VAV box controller", "Pr_50_20_30", "Products"),
    ("VAV box room 214", "Pr_50_20_30", "Products"),
    ("VAV-03 variable air volume", "Pr_50_20_30", "Products"),
    ("VAV box controller rm 102", "Pr_50_20_30", "Products"),
    ("variable air volume box", "Pr_50_20_30", "Products"),
    # Chillers
    ("chiller no 1 (Trane)", "Pr_50_80_10", "Products"),
    ("chiller no 2 (York)", "Pr_50_80_10", "Products"),
    ("chiller plant roof", "Pr_50_80_10", "Products"),
    ("absorption chiller", "Pr_50_80_10", "Products"),
    # Pumps
    ("CHWP-01 chilled water pump", "Pr_50_40_10", "Products"),
    ("HWP-02 heating water pump", "Pr_50_40_10", "Products"),
    ("condensate pump plantroom", "Pr_50_40_10", "Products"),
    ("boiler feed pump", "Pr_50_40_10", "Products"),
    ("circulation pump HWS", "Pr_50_40_10", "Products"),
    # Chillers / Refrigeration
    ("chiller no 1", "Pr_50_80_10", "Products"),
    ("chiller plant", "Pr_50_80_10", "Products"),
    # Fans
    ("supply fan AHU-01", "Pr_50_20_10", "Products"),
    ("extract fan plantroom", "Pr_50_20_10", "Products"),
    ("roof extract fan", "Pr_50_20_10", "Products"),
    # Heat Exchangers
    ("plate heat exchanger HWS", "Pr_50_20_10", "Products"),
    ("shell tube heat exchanger", "Pr_50_20_10", "Products"),
    # Lighting
    ("emerg lighting luminaire", "Pr_50_30_20", "Products"),
    ("LED panel light office", "Pr_50_30_20", "Products"),
    ("emergency light fitting", "Pr_50_30_20", "Products"),
    ("high bay luminaire warehouse", "Pr_50_30_20", "Products"),
    ("downlight LED office", "Pr_50_30_20", "Products"),
    # Electrical
    ("distribution board DB-01", "Pr_50_30_10", "Products"),
    ("MCC motor control centre", "Pr_50_30_10", "Products"),
    ("UPS unit server room", "Pr_50_30_10", "Products"),
    ("transformer 11kV/415V", "Pr_50_30_10", "Products"),
    ("generator set 500kVA", "Pr_50_30_10", "Products"),
    # Fire Protection
    ("fire extinguisher CO2", "Pr_50_50_10", "Products"),
    ("sprinkler head office", "Pr_50_50_20", "Products"),
    ("fire alarm panel", "Pr_50_50_10", "Products"),
    ("smoke detector ceiling", "Pr_50_60_20", "Products"),
    # Gas Equipment
    ("gas boiler plantroom", "Pr_50_70_10", "Products"),
    ("gas fired heater", "Pr_50_70_10", "Products"),
    # BMS / Controls
    ("BMS controller AHU-01", "Pr_50_60_10", "Products"),
    ("temperature sensor room 101", "Pr_50_60_20", "Products"),
    ("CO2 sensor conference room", "Pr_50_60_20", "Products"),
    ("pressure sensor duct", "Pr_50_60_20", "Products"),
    ("humidity sensor AHU", "Pr_50_60_20", "Products"),
    ("occupancy sensor meeting room", "Pr_50_60_20", "Products"),
    # Radiators / Heat Emitters
    ("panel radiator office", "Pr_50_10_20", "Products"),
    ("LTHW radiator corridor", "Pr_50_10_20", "Products"),
    ("underfloor heating manifold", "Pr_50_10_20", "Products"),
    # Water Systems
    ("cold water tank roof", "Pr_50_40", "Products"),
    ("hot water calorifier", "Pr_50_40_20", "Products"),
    ("water softener plantroom", "Pr_50_40", "Products"),
    ("dosing pot chemical", "Pr_50_40", "Products"),
    # Fire Protection
    ("fire damper duct", "Pr_50_50_20", "Products"),
    ("fire door hold open", "Pr_50_50", "Products"),
    # Systems (Ss) examples
    ("heating system building B", "Ss_50_10", "Systems"),
    ("ventilation system AHU-01", "Ss_50_20_10", "Systems"),
    ("air handling system plantroom", "Ss_50_20_10", "Systems"),
    ("VAV system floor 2", "Ss_50_20_30", "Systems"),
    ("boiler system plantroom", "Ss_50_10_10", "Systems"),
    ("chilled water system", "Ss_50_80_10", "Systems"),
    ("hot water system", "Ss_50_40_20", "Systems"),
    ("fire sprinkler system", "Ss_50_50_20", "Systems"),
    ("fire alarm system", "Ss_50_50", "Systems"),
    ("BMS system building", "Ss_50_60_10", "Systems"),
    ("lighting system office", "Ss_50_30_20", "Systems"),
    ("power distribution system", "Ss_50_30_10", "Systems"),
    ("lighting control system", "Ss_50_30_20", "Systems"),
    ("gas supply system", "Ss_50_70", "Systems"),
    ("refrigeration system", "Ss_50_80", "Systems"),
    ("chiller system", "Ss_50_80_10", "Systems"),
]


# Template-based expansion so the golden set reaches >= 300 labelled rows.
# Deterministic (seeded); each generated row is a plausible messy variant of a
# canonical type. Categories mirror the hand-written examples above.
_PRODUCT_TEMPLATES: list[tuple[str, str, list[str]]] = [
    ("Pr_50_20_10", "Products", ["air handling unit", "air hndling unit", "air handler", "ahu"]),
    ("Pr_50_10_10", "Products", ["boiler", "oil boiler", "condensing boiler", "biomass boiler", "boiler plant"]),
    ("Pr_50_20_20", "Products", ["fan coil unit"]),
    ("Pr_50_20_40", "Products", ["fan coil", "fcu"]),
    ("Pr_50_20_30", "Products", ["vav box", "variable air volume box", "vav"]),
    ("Pr_50_80_10", "Products", ["chiller", "absorption chiller", "air cooled chiller"]),
    ("Pr_50_40_10", "Products", ["chilled water pump", "heating water pump", "condensate pump", "boiler feed pump"]),
    ("Pr_50_30_20", "Products", ["luminaire", "led panel light", "emergency light", "downlight", "high bay light"]),
    ("Pr_50_30_10", "Products", ["distribution board", "mcc", "ups", "transformer", "generator"]),
    ("Pr_50_50_10", "Products", ["fire extinguisher", "fire alarm panel"]),
    ("Pr_50_50_20", "Products", ["sprinkler", "fire damper"]),
    ("Pr_50_60_10", "Products", ["bms controller"]),
    (
        "Pr_50_60_20",
        "Products",
        [
            "temperature sensor",
            "co2 sensor",
            "pressure sensor",
            "humidity sensor",
            "smoke detector",
            "occupancy sensor",
        ],
    ),
    ("Pr_50_70_10", "Products", ["gas boiler", "gas fired heater"]),
    ("Pr_50_10_20", "Products", ["radiator", "lthw radiator", "panel radiator", "underfloor heating"]),
    ("Pr_50_40_20", "Products", ["water heater", "hot water calorifier"]),
]

_SYSTEM_TEMPLATES: list[tuple[str, str, list[str]]] = [
    ("Ss_50_10_10", "Systems", ["boiler system"]),
    ("Ss_50_20_10", "Systems", ["air handling unit system", "ahu system", "air handling system"]),
    ("Ss_50_20_20", "Systems", ["fan coil unit system"]),
    ("Ss_50_20_40", "Systems", ["fan coil system", "fcu system"]),
    ("Ss_50_20_30", "Systems", ["vav box system", "vav system"]),
    ("Ss_50_30_10", "Systems", ["power distribution system", "electrical distribution system"]),
    ("Ss_50_30_20", "Systems", ["lighting system", "lighting control system"]),
    ("Ss_50_40_10", "Systems", ["pump system", "pumping system"]),
    ("Ss_50_50_20", "Systems", ["sprinkler system", "fire suppression system"]),
    ("Ss_50_60_10", "Systems", ["bms system", "building management system"]),
    ("Ss_50_70_10", "Systems", ["gas boiler system", "gas heating system"]),
    ("Ss_50_80", "Systems", ["refrigeration system"]),
    ("Ss_50_80_10", "Systems", ["chiller system", "chilled water system"]),
]

_LOCATIONS = [
    "L1",
    "L2",
    "L3",
    "roof",
    "plantroom",
    "basement",
    "rm 101",
    "rm 214",
    "rm 305",
    "room 110",
    "corridor",
    "lab",
]
_MANUFACTURERS = [
    "Remeha",
    "Hamworthy",
    "Trane",
    "York",
    "Worcester Bosch",
    "Daikin",
    "Mitsubishi",
    "Satchwell",
    "Grundfos",
    "Armstrong",
]
_PREFIXES = {
    "Pr_50_20_10": "AHU",
    "Pr_50_10_10": "B",
    "Pr_50_20_20": "FCU",
    "Pr_50_20_40": "FCU",
    "Pr_50_20_30": "VAV",
    "Pr_50_80_10": "CH",
    "Pr_50_40_10": "P",
    "Pr_50_30_20": "L",
    "Pr_50_30_10": "DB",
    "Pr_50_50_10": "FE",
    "Pr_50_50_20": "SPR",
    "Pr_50_60_10": "BMS",
    "Pr_50_60_20": "S",
    "Pr_50_70_10": "GB",
    "Pr_50_10_20": "RAD",
    "Pr_50_40_20": "HX",
}


def _expand_examples(seed: int = 42) -> list[tuple[str, str, str]]:
    rng = random.Random(seed)
    out: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    def _add(desc: str, code: str, table: str) -> None:
        if desc not in seen:
            seen.add(desc)
            out.append((desc, code, table))

    for code, table, names in _PRODUCT_TEMPLATES:
        prefix = _PREFIXES.get(code, "EQ")
        for name in names:
            for loc in _LOCATIONS:
                _add(f"{name} {loc}", code, table)
            for i in range(1, 4):
                _add(f"{prefix}-0{i} {name}", code, table)
                _add(f"{name} no {i}", code, table)
                brand = rng.choice(_MANUFACTURERS)
                _add(f"{name} no {i} ({brand})", code, table)

    for code, table, names in _SYSTEM_TEMPLATES:
        for name in names:
            for loc in _LOCATIONS[:6]:
                _add(f"{name} {loc}", code, table)
            _add(f"{name} building {rng.randint(1, 6)}", code, table)

    return out


GOLDEN_EXAMPLES = GOLDEN_EXAMPLES + _expand_examples()


def build_golden_set(output_path: str, review_fraction: float = 0.2, seed: int = 42) -> None:
    """Build golden set CSV and review sample."""
    random.seed(seed)

    # Convert to DataFrame
    df = pd.DataFrame(GOLDEN_EXAMPLES, columns=["description", "true_code", "table"])
    df["description"] = df["description"].astype(str)
    df["true_code"] = df["true_code"].astype(str)
    df["table"] = df["table"].astype(str)

    # Add normalised description
    from normaliser import normalise_cached

    df["description_norm"] = df["description"].apply(normalise_cached)

    # Save full golden set
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Golden set: {len(df)} examples -> {output_path}")

    # Generate review sample (≥ 20% — round up, truncation would land just under)
    review_size = max(math.ceil(len(df) * review_fraction), 1)
    review_indices = random.sample(range(len(df)), review_size)
    review_df = df.iloc[review_indices].copy()
    review_df["human_code"] = ""  # Empty for human to fill
    review_df["notes"] = ""

    review_path = output_path.parent / "review_sample.csv"
    review_df.to_csv(review_path, index=False)
    print(f"Review sample: {len(review_df)} examples -> {review_path}")
    print(f"  (Human must review >= 20% = {review_size} examples)")


def split_golden_set(
    df: pd.DataFrame,
    seed: int = 42,
    train_frac: float = 0.7,
    dev_frac: float = 0.15,
) -> dict[str, pd.DataFrame]:
    """Deterministic train/dev/test split (stratified by true_code).

    Thresholds are tuned on dev only; test is held out for final reporting.
    """
    rng = random.Random(seed)
    train_idx: list = []
    dev_idx: list = []
    test_idx: list = []
    for _code, group in df.groupby("true_code", sort=True):
        idx = group.index.tolist()
        rng.shuffle(idx)
        n = len(idx)
        n_train = int(n * train_frac)
        n_dev = int(n * dev_frac)
        train_idx.extend(idx[:n_train])
        dev_idx.extend(idx[n_train : n_train + n_dev])
        test_idx.extend(idx[n_train + n_dev :])
    # Any rows without a true_code (should not happen) go to train.
    return {
        "train": df.loc[sorted(train_idx)].reset_index(drop=True),
        "dev": df.loc[sorted(dev_idx)].reset_index(drop=True),
        "test": df.loc[sorted(test_idx)].reset_index(drop=True),
    }


def load_golden_set(path: str) -> pd.DataFrame:
    """Load golden set from CSV."""
    return pd.read_csv(path)


def load_review_decisions(path: str) -> pd.DataFrame:
    """Load human review decisions from CSV."""
    return pd.read_csv(path)


if __name__ == "__main__":
    output = Path("projects/p13-uniclass-mapper/data/golden_set.csv")
    build_golden_set(str(output))
    print(f"\nGolden set written to {output}")
    print(f"Total examples: {len(GOLDEN_EXAMPLES)}")
    print(f"Review sample: {max(math.ceil(len(GOLDEN_EXAMPLES) * 0.2), 1)} (>= 20%)")
