"""Text normalisation for asset descriptions (P13).

Expands abbreviations, lowercases, tokenises, removes stop-words.
"""

from __future__ import annotations

import re
from functools import lru_cache

# Abbreviation expansion dictionary (common in estates/asset descriptions)
ABBREVIATIONS = {
    "ahu": "air handling unit",
    "ahu's": "air handling units",
    "ahus": "air handling units",
    "fcu": "fan coil unit",
    "fcu's": "fan coil units",
    "fcus": "fan coil units",
    "vav": "variable air volume",
    "hndlg": "handling",
    "hndl": "handling",
    "rm": "room",
    "rms": "rooms",
    "no": "number",
    "emerg": "emergency",
    "emer": "emergency",
    "vav's": "variable air volumes",
    "vavs": "variable air volumes",
    "prv": "pressure reducing valve",
    "prv's": "pressure reducing valves",
    "prvs": "pressure reducing valves",
    "mcc": "motor control centre",
    "mcc's": "motor control centres",
    "mccs": "motor control centres",
    "ups": "uninterruptible power supply",
    "ups's": "uninterruptible power supplies",
    "bms": "building management system",
    "bms's": "building management systems",
    "bmses": "building management systems",
    "chwp": "chilled water pump",
    "chwp's": "chilled water pumps",
    "chwps": "chilled water pumps",
    "hhwp": "heating hot water pump",
    "hhwp's": "heating hot water pumps",
    "hhwps": "heating hot water pumps",
    "ct": "cooling tower",
    "ct's": "cooling towers",
    "cts": "cooling towers",
    "ac": "air conditioning",
    "ac's": "air conditionings",
    "acs": "air conditionings",
    "acm": "air conditioning module",
    "acm's": "air conditioning modules",
    "acms": "air conditioning modules",
    "cctv": "closed circuit television",
    "cctv's": "closed circuit televisions",
    "cctvs": "closed circuit televisions",
    "hvac": "heating ventilation air conditioning",
    "hvac's": "heating ventilation air conditionings",
    "hvacs": "heating ventilation air conditionings",
    "pcu": "precision cooling unit",
    "pcu's": "precision cooling units",
    "pcus": "precision cooling units",
    "crac": "computer room air conditioning",
    "crac's": "computer room air conditionings",
    "cracs": "computer room air conditionings",
    "crh": "computer room handler",
    "crh's": "computer room handlers",
    "crhs": "computer room handlers",
    "cwu": "cold water unit",
    "cwu's": "cold water units",
    "cwus": "cold water units",
    "hwu": "hot water unit",
    "hwu's": "hot water units",
    "hwus": "hot water units",
    "boil": "boiler",
    "boil's": "boilers",
    "boils": "boilers",
    "chil": "chiller",
    "chil's": "chillers",
    "chils": "chillers",
    "pump": "pump",
    "pump's": "pumps",
    "pumps": "pumps",
    "fan": "fan",
    "fan's": "fans",
    "fans": "fans",
    "coil": "coil",
    "coil's": "coils",
    "coils": "coils",
    "valve": "valve",
    "valve's": "valves",
    "valves": "valves",
    "damper": "damper",
    "damper's": "dampers",
    "dampers": "dampers",
    "filter": "filter",
    "filter's": "filters",
    "filters": "filters",
    "sensor": "sensor",
    "sensor's": "sensors",
    "sensors": "sensors",
    "meter": "meter",
    "meter's": "meters",
    "meters": "meters",
    "panel": "panel",
    "panel's": "panels",
    "panels": "panels",
    "board": "board",
    "board's": "boards",
    "boards": "boards",
    "cabinet": "cabinet",
    "cabinet's": "cabinets",
    "cabinets": "cabinets",
    "rack": "rack",
    "rack's": "racks",
    "racks": "racks",
    "enclosure": "enclosure",
    "enclosure's": "enclosures",
    "enclosures": "enclosures",
    "duct": "duct",
    "duct's": "ducts",
    "ducts": "ducts",
    "pipe": "pipe",
    "pipe's": "pipes",
    "pipes": "pipes",
    "cable": "cable",
    "cable's": "cables",
    "cables": "cables",
    "wire": "wire",
    "wire's": "wires",
    "wires": "wires",
    "conduit": "conduit",
    "conduit's": "conduits",
    "conduits": "conduits",
    "transformer": "transformer",
    "transformer's": "transformers",
    "transformers": "transformers",
    "generator": "generator",
    "generator's": "generators",
    "generators": "generators",
    "compressor": "compressor",
    "compressor's": "compressors",
    "compressors": "compressors",
    "condenser": "condenser",
    "condenser's": "condensers",
    "condensers": "condensers",
    "evaporator": "evaporator",
    "evaporator's": "evaporators",
    "evaporators": "evaporators",
    "heat exchanger": "heat exchanger",
    "heat exchanger's": "heat exchangers",
    "heat exchangers": "heat exchangers",
    "cooling": "cooling",
    "heating": "heating",
    "ventilation": "ventilation",
    "air": "air",
    "water": "water",
    "hot": "hot",
    "cold": "cold",
    "chilled": "chilled",
    "hot water": "hot water",
    "chilled water": "chilled water",
    "condensate": "condensate",
    "condensate's": "condensates",
    "condensates": "condensates",
    "refrigerant": "refrigerant",
    "refrigerant's": "refrigerants",
    "refrigerants": "refrigerants",
    "gas": "gas",
    "oil": "oil",
    "fuel": "fuel",
    "electric": "electric",
    "electrical": "electrical",
    "mechanical": "mechanical",
    "control": "control",
    "control's": "controls",
    "controls": "controls",
    "monitor": "monitor",
    "monitor's": "monitors",
    "monitors": "monitors",
    "alarm": "alarm",
    "alarm's": "alarms",
    "alarms": "alarms",
    "indicator": "indicator",
    "indicator's": "indicators",
    "indicators": "indicators",
    "display": "display",
    "display's": "displays",
    "displays": "displays",
    "switch": "switch",
    "switch's": "switches",
    "switches": "switches",
    "breaker": "breaker",
    "breaker's": "breakers",
    "breakers": "breakers",
    "fuse": "fuse",
    "fuse's": "fuses",
    "fuses": "fuses",
    "relay": "relay",
    "relay's": "relays",
    "relays": "relays",
    "contactor": "contactor",
    "contactor's": "contactors",
    "contactors": "contactors",
    "starter": "starter",
    "starter's": "starters",
    "starters": "starters",
    "motor": "motor",
    "motor's": "motors",
    "motors": "motors",
    "drive": "drive",
    "drive's": "drives",
    "drives": "drives",
    "vfd": "variable frequency drive",
    "vfd's": "variable frequency drives",
    "vfds": "variable frequency drives",
    "inverter": "inverter",
    "inverter's": "inverters",
    "inverters": "inverters",
    "soft starter": "soft starter",
    "soft starter's": "soft starters",
    "soft starters": "soft starters",
}

# Stop words for tokenisation
STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "is",
    "it",
    "its",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "should",
    "could",
    "may",
    "might",
    "must",
    "shall",
    "can",
    "cannot",
    "this",
    "that",
    "these",
    "those",
    "my",
    "your",
    "his",
    "her",
    "their",
    "our",
    "we",
    "you",
    "he",
    "she",
    "they",
    "them",
    "us",
    "i",
    "me",
    "no",
    "not",
    "nor",
    "so",
    "if",
    "then",
    "else",
    "when",
    "where",
    "why",
    "how",
    "what",
    "which",
    "who",
    "whom",
    "whose",
    "there",
    "here",
    "now",
    "than",
    "also",
    "just",
    "only",
    "even",
    "still",
    "already",
    "yet",
    "again",
    "once",
    "twice",
    "first",
    "second",
    "third",
    "last",
    "next",
    "previous",
    "new",
    "old",
    "same",
    "different",
    "other",
    "another",
    "each",
    "every",
    "any",
    "some",
    "all",
    "both",
    "either",
    "neither",
    "much",
    "many",
    "few",
    "several",
    "more",
    "most",
    "less",
    "least",
    "very",
    "quite",
    "rather",
    "too",
    "enough",
    "such",
    "own",
}


def expand_abbreviations(text: str) -> str:
    """Expand known abbreviations in text."""
    words = text.split()
    expanded = []
    for word in words:
        lower = word.lower().rstrip(".,;:!?)(")
        if lower in ABBREVIATIONS:
            expanded.append(ABBREVIATIONS[lower])
        else:
            # Handle "AHU-03"-style tokens: strip trailing digits and re-check
            m = re.match(r"^([a-z][a-z']*)[-_]?\d+$", lower)
            if m and m.group(1) in ABBREVIATIONS:
                expanded.append(ABBREVIATIONS[m.group(1)])
            else:
                expanded.append(word)
    return " ".join(expanded)


def tokenise(text: str) -> list[str]:
    """Simple tokenisation: split on non-alphanumeric, keep alphanumeric tokens."""
    # Split on non-alphanumeric (but keep internal hyphens/underscores)
    tokens = re.findall(r"[a-zA-Z0-9]+(?:[-_][a-zA-Z0-9]+)*", text.lower())
    return tokens


def remove_stop_words(tokens: list[str]) -> list[str]:
    """Remove stop words from token list."""
    return [t for t in tokens if t not in STOP_WORDS]


def normalise(text: str) -> str:
    """Full normalisation pipeline: expand abbrevs, lowercase, tokenise, remove stop words, rejoin."""
    if not text or not isinstance(text, str):
        return ""
    text = expand_abbreviations(text)
    tokens = tokenise(text)
    tokens = remove_stop_words(tokens)
    return " ".join(tokens)


@lru_cache(maxsize=1024)
def normalise_cached(text: str) -> str:
    return normalise(text)


# --- Retrieval-time matching helpers (do NOT change normalise() behaviour) ---
# Location / tag tokens carry no type signal and let words like "roof" or
# "building" dominate embedding similarity (e.g. "led panel light roof" used to
# retrieve Roofs). matching_query() strips them; the raw description is kept
# for display and for prefix signals (AHU-03, FCU-05, ...).

LOCATION_TOKENS = {
    "l1",
    "l2",
    "l3",
    "roof",
    "plantroom",
    "basement",
    "room",
    "rooms",
    "rm",
    "rms",
    "corridor",
    "lab",
    "office",
    "warehouse",
    "building",
    "floor",
    "level",
    "plant",
}

MANUFACTURER_TOKENS = {
    "remeha",
    "hamworthy",
    "trane",
    "york",
    "worcester",
    "bosch",
    "daikin",
    "mitsubishi",
    "satchwell",
    "grundfos",
    "armstrong",
}

# Non-type room/function words that pollute retrieval ("pressure sensor duct"
# should match Sensors, not ducts).
NOISE_TOKENS = {
    "meeting",
    "conference",
    "server",
    "ceiling",
    "duct",
}

# Equipment-tag prefixes seen in messy descriptions. Maps to the code family
# (prefix of the Uniclass code) they signal. Used as a boost, not a rule.
PREFIX_FAMILIES = {
    "ahu": "Pr_50_20_10",
    "fcu": "Pr_50_20_40",
    "vav": "Pr_50_20_30",
    "chwp": "Pr_50_40_10",
    "hwp": "Pr_50_40_10",
    "hhwp": "Pr_50_40_10",
    "ch": "Pr_50_80_10",
    "db": "Pr_50_30_10",
    "mcc": "Pr_50_30_10",
    "ups": "Pr_50_30_10",
    "bms": "Pr_50_60_10",
    "spr": "Pr_50_50_20",
    "fe": "Pr_50_50_10",
    "gb": "Pr_50_70_10",
    "rad": "Pr_50_10_20",
    "hx": "Pr_50_40_20",
}

_TAG_RE = re.compile(r"^[a-z]{1,5}[-_]?\d+[a-z]?\d*$")
_NUM_RE = re.compile(r"^\d+[a-z]?$")


def extract_prefix_family(raw: str) -> str | None:
    """Return the signalled code family from a leading equipment tag, if any.

    Only the FIRST token signals: it is the asset's own tag ("AHU-03 ...",
    "FCU ...", "BMS ..."). Later tags name related plant ("BMS controller
    AHU-01" is a BMS controller serving AHU-01, not an air handling unit).
    """
    first = (raw.strip().split() or [""])[0].lower().rstrip(".,;:!?)(")
    m = re.match(r"^([a-z]{1,5})[-_]?\d+$", first)
    base = m.group(1) if m else first
    return PREFIX_FAMILIES.get(base)


def matching_query(text: str) -> str:
    """Normalised query with locations, tags, manufacturers and numbers stripped.

    Unlike normalise(), this keeps the original abbreviation token alongside its
    expansion (so "VAV" still matches the "VAV boxes" title) and maps bare/tagged
    "FCU" to "fan coil" without "unit" (the "fan coil unit" phrasing belongs to
    the Pr_50_20_20 / Ss_50_20_20 titles; see docs/error_analysis.md).
    """
    if not text or not isinstance(text, str):
        return ""
    # FCU first: "FCU-05" / "FCU" must not become "fan coil unit".
    text = re.sub(r"(?i)\bfcu[-_]?\d+\b", "fan coil", text)
    text = re.sub(r"(?i)\bfcus?\b", "fan coil", text)
    words = text.split()
    expanded_words: list[str] = []
    for word in words:
        lower = word.lower().rstrip(".,;:!?)(")
        if lower in ABBREVIATIONS and ABBREVIATIONS[lower] != lower:
            # Keep the abbrev token AND the expansion for title matching.
            expanded_words.append(lower)
            expanded_words.append(ABBREVIATIONS[lower])
            continue
        m = re.match(r"^([a-z][a-z']*)[-_]?\d+$", lower)
        if m and m.group(1) in ABBREVIATIONS:
            base = m.group(1)
            if base == "fcu":
                expanded_words.append("fan coil")
            else:
                expanded_words.append(base)
                expanded_words.append(ABBREVIATIONS[base])
            continue
        expanded_words.append(word)
    expanded = " ".join(expanded_words)
    tokens = tokenise(expanded)
    # Reverse-acronym: the written-out phrase implies its abbreviation token.
    # (Only VAV needs this: "VAV boxes" is the one title keyed on an acronym.)
    if {"variable", "air", "volume"}.issubset(set(tokens)) and "vav" not in tokens:
        tokens.append("vav")
    kept: list[str] = []
    for tok in tokens:
        if tok in STOP_WORDS:
            continue
        if tok in LOCATION_TOKENS or tok in MANUFACTURER_TOKENS or tok in NOISE_TOKENS:
            continue
        if _NUM_RE.match(tok):
            continue
        if any(c.isdigit() for c in tok) and tok not in ABBREVIATIONS and tok != "co2":
            # Model numbers / ratings ("11kv", "500kva") carry no type signal.
            continue
        if _TAG_RE.match(tok) and tok not in ABBREVIATIONS:
            # Equipment tag (ahu-03, db-01, fcu-05 ...): prefix signal is
            # captured separately; the tag itself adds noise.
            continue
        # Room numbers glued to words ("rm101") were split by tokenise into
        # ("rm101",); drop tokens that are a location word + digits.
        if re.match(r"^(rm|room|l|level|building|floor)\d+$", tok):
            continue
        kept.append(tok)
    return " ".join(kept)


if __name__ == "__main__":
    # Quick test
    test_cases = [
        "AHU-03 air hndlg unit L2",
        "Boiler no 2 (Remeha)",
        "FCU fan coil rm 214",
        "emerg lighting luminaire",
        "AHU-01 VAV box controller",
        "BMS controller for AHU-02",
        "CHWP-01 chilled water pump",
        "FCU-05 fan coil unit room 101",
    ]
    for tc in test_cases:
        print(f"Input:  {tc}")
        print(f"Output: {normalise(tc)}")
        print()
