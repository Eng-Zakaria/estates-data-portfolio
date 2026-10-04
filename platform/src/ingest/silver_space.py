"""Silver: space_register → silver.spaces (+ quarantine, unmapped report)."""

from __future__ import annotations

import pandas as pd

from .refs import building_crosswalk, load_map, suggest
from .silver_common import clean_area, dedupe, quarantine


def transform_space(
    bronze: pd.DataFrame, truth_buildings: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = bronze.copy()
    df = df.rename(columns={c: c.strip() for c in df.columns})
    # drop fully blank rows (exported blank-row defect) → quarantine
    blank = df[["building_name", "Room"]].isna().all(axis=1)
    valid, q_blank = quarantine(df, blank, "nulls_in_mandatory:blank_row")
    # mandatory nulls
    miss = valid["building_name"].isna() | valid["Room"].isna()
    valid, q_null = quarantine(valid, miss, "nulls_in_mandatory")
    # clean
    valid["building_name"] = valid["building_name"].astype(str).str.strip()
    valid["Room"] = valid["Room"].astype(str).str.strip()
    valid["nia_m2"] = clean_area(valid["area_text"])
    valid["capacity_seats"] = pd.to_numeric(valid["Seats"], errors="coerce")
    # category map
    cat_map = load_map("space_category_map.csv")
    valid["space_category_raw"] = valid["category_messy"].astype(str).str.strip()
    valid["space_category"] = valid["space_category_raw"].map(cat_map)
    unmapped_cat = valid[valid.space_category.isna()][["category_messy"]].drop_duplicates()
    unmapped_cat["suggestion"] = unmapped_cat["category_messy"].map(
        lambda v: ",".join(suggest(str(v), sorted(set(cat_map))))
    )
    valid, q_cat = quarantine(valid, valid.space_category.isna(), "unmapped:space_category")
    # building crosswalk
    xwalk = building_crosswalk(truth_buildings)
    valid["building_id"] = valid["building_name"].map(xwalk)
    unmapped_b = valid[valid.building_id.isna()][["building_name"]].drop_duplicates()
    unmapped_b["suggestion"] = unmapped_b["building_name"].map(lambda v: ",".join(suggest(str(v), sorted(xwalk))))
    valid, q_b = quarantine(valid, valid.building_id.isna(), "orphan_fk:building_name")
    # area range
    bad_area = valid["nia_m2"].isna() | (valid["nia_m2"] <= 0) | (valid["nia_m2"] >= 2000)
    valid, q_area = quarantine(valid, bad_area, "out_of_range:nia_m2")
    # dedupe by Room
    valid, q_dup = dedupe(valid, ["Room"])
    silver = valid[["Room", "building_id", "building_name", "space_category", "nia_m2", "capacity_seats"]].rename(
        columns={"Room": "room_code"}
    )
    quarantine_all = (
        pd.concat([q_blank, q_null, q_cat, q_b, q_area, q_dup], ignore_index=True)
        if any(len(q) for q in [q_blank, q_null, q_cat, q_b, q_area, q_dup])
        else valid.iloc[0:0].copy()
    )
    unmapped = pd.concat(
        [unmapped_cat.assign(field="space_category"), unmapped_b.assign(field="building_name")], ignore_index=True
    )
    return silver.reset_index(drop=True), quarantine_all.reset_index(drop=True), unmapped
