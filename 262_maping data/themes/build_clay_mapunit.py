from __future__ import annotations

from pathlib import Path
from collections import defaultdict
from typing import Iterable, Dict, Any

import fiona
import geopandas as gpd
import numpy as np


# -----------------------
# User settings
# -----------------------

GDB_PATH = Path("Data/Soil/gNATSGO_OR.gdb")  # <-- set this to your real .gdb folder

# Layer names we *want* (we will resolve case-insensitively)
MUPOLYGON_LAYER = "MUPOLYGON"
COMPONENT_LAYER = "component"
CHORIZON_LAYER = "chorizon"

OUT_GPKG = Path("Data/Derived/clay_mapunit.gpkg")
OUT_LAYER = "clay_mapunit"

# Depth interval (cm)
DEPTH_TOP_CM = 0
DEPTH_BOTTOM_CM = 30


# -----------------------
# Helpers
# -----------------------

def resolve_layer(gdb_path: Path, desired: str) -> str:
    """Find a layer name in the GDB matching desired (case-insensitive)."""
    layers = fiona.listlayers(str(gdb_path))
    for lyr in layers:
        if lyr.lower() == desired.lower():
            return lyr
    raise ValueError(f"Layer '{desired}' not found. Available layers include: {layers[:25]} ...")


def stream_table_case_insensitive(
    gdb_path: Path, layer: str, desired_fields: list[str]
) -> Iterable[dict[str, Any]]:
    """
    Stream records from a GDB layer/table, selecting fields by name case-insensitively.
    desired_fields should be given in lowercase (e.g., ['cokey','hzdept_r']).
    """
    layer_real = resolve_layer(gdb_path, layer)

    with fiona.open(str(gdb_path), layer=layer_real) as src:
        # fiona schema keys are the real field names (often uppercase)
        props_schema = src.schema.get("properties", {})
        field_map = {k.lower(): k for k in props_schema.keys()}  # lower -> real

        # Map requested fields to actual field names
        real_fields = {}
        for f in desired_fields:
            rf = field_map.get(f.lower())
            if rf is not None:
                real_fields[f.lower()] = rf

        # If we are missing any key field, fail loudly so we don't silently compute zeros
        missing = [f for f in desired_fields if f.lower() not in real_fields]
        if missing:
            raise KeyError(
                f"Missing fields in layer '{layer_real}': {missing}. "
                f"Example available fields: {list(props_schema.keys())[:30]}"
            )

        for feat in src:
            props = feat["properties"]
            out = {}
            for low, real in real_fields.items():
                out[low] = props.get(real)
            yield out


def overlap_thickness(a_top: float, a_bot: float, b_top: float, b_bot: float) -> float:
    """Thickness of overlap between [a_top,a_bot] and [b_top,b_bot]."""
    top = max(a_top, b_top)
    bot = min(a_bot, b_bot)
    return max(0.0, bot - top)


def compute_cokey_clay(gdb_path: Path, depth_top: float, depth_bottom: float) -> dict[str, float]:
    """
    Horizon-thickness-weighted mean clay% per component (cokey) over depth interval.
    """
    needed = ["cokey", "hzdept_r", "hzdepb_r", "claytotal_r"]

    sum_clay_x_thk = defaultdict(float)
    sum_thk = defaultdict(float)

    for row in stream_table_case_insensitive(gdb_path, CHORIZON_LAYER, needed):
        cokey = row["cokey"]
        if cokey is None:
            continue

        hz_top = row["hzdept_r"]
        hz_bot = row["hzdepb_r"]
        clay = row["claytotal_r"]

        if hz_top is None or hz_bot is None or clay is None:
            continue

        try:
            hz_top = float(hz_top)
            hz_bot = float(hz_bot)
            clay = float(clay)
        except Exception:
            continue

        if hz_bot <= hz_top:
            continue

        thk = overlap_thickness(hz_top, hz_bot, depth_top, depth_bottom)
        if thk <= 0:
            continue

        sum_clay_x_thk[str(cokey)] += clay * thk
        sum_thk[str(cokey)] += thk

    cokey_clay = {}
    for cokey, thk in sum_thk.items():
        if thk > 0:
            cokey_clay[cokey] = sum_clay_x_thk[cokey] / thk

    return cokey_clay


def compute_mukey_clay(gdb_path: Path, cokey_clay: dict[str, float]) -> dict[str, float]:
    """
    Component-percent weighted mean clay% per mapunit (mukey).
    """
    needed = ["mukey", "cokey", "comppct_r"]

    sum_clay_x_pct = defaultdict(float)
    sum_pct = defaultdict(float)

    for row in stream_table_case_insensitive(gdb_path, COMPONENT_LAYER, needed):
        mukey = row["mukey"]
        cokey = row["cokey"]
        pct = row["comppct_r"]

        if mukey is None or cokey is None or pct is None:
            continue

        clay = cokey_clay.get(str(cokey))
        if clay is None:
            continue

        try:
            pct = float(pct)
        except Exception:
            continue

        if pct <= 0:
            continue

        mukey = str(mukey)
        sum_clay_x_pct[mukey] += clay * pct
        sum_pct[mukey] += pct

    mukey_clay = {}
    for mukey, pct in sum_pct.items():
        if pct > 0:
            mukey_clay[mukey] = sum_clay_x_pct[mukey] / pct

    return mukey_clay


def main():
    if not GDB_PATH.exists():
        raise FileNotFoundError(f"Missing gdb: {GDB_PATH.resolve()}")

    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)

    print(f"Using GDB: {GDB_PATH}")
    print(f"Depth interval (cm): {DEPTH_TOP_CM}–{DEPTH_BOTTOM_CM}")

    print("Computing clay per component (cokey) from horizons...")
    cokey_clay = compute_cokey_clay(GDB_PATH, DEPTH_TOP_CM, DEPTH_BOTTOM_CM)
    print(f"  cokey clay computed: {len(cokey_clay):,}")

    if len(cokey_clay) == 0:
        raise RuntimeError(
            "Computed 0 cokey clay values. This usually means the CHORIZON table fields "
            "aren't what we expect or values are missing. (But the script should now error earlier if fields missing.)"
        )

    print("Computing clay per map unit (mukey) from components...")
    mukey_clay = compute_mukey_clay(GDB_PATH, cokey_clay)
    print(f"  mukey clay computed: {len(mukey_clay):,}")

    if len(mukey_clay) == 0:
        raise RuntimeError(
            "Computed 0 mukey clay values. This usually means COMPONENT table join fields "
            "or component percents are not matching."
        )

    print("Loading MUPOLYGON geometry...")
    mup_layer_real = resolve_layer(GDB_PATH, MUPOLYGON_LAYER)
    mups = gpd.read_file(GDB_PATH, layer=mup_layer_real)

    # Normalize column names to lowercase for consistency
    mups.columns = [c.lower() for c in mups.columns]

    if "mukey" not in mups.columns:
        raise KeyError(
            f"MUPOLYGON is missing 'mukey'. Available columns include: {list(mups.columns)[:40]}"
        )

    mups["mukey"] = mups["mukey"].astype(str)
    mups["clay_pct"] = mups["mukey"].map(lambda k: mukey_clay.get(k))

    mups["depth_cm_top"] = DEPTH_TOP_CM
    mups["depth_cm_bot"] = DEPTH_BOTTOM_CM

    # Save
    if OUT_GPKG.exists():
        OUT_GPKG.unlink()

    mups.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG")
    print(f"Saved: {OUT_GPKG} (layer={OUT_LAYER})")
    print("Done.")


if __name__ == "__main__":
    main()
