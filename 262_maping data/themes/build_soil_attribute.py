from __future__ import annotations

from pathlib import Path
import geopandas as gpd
import pandas as pd
import fiona

GDB = Path("Data/Soil/gNATSGO_OR.gdb")  # <-- point to whichever GDB you want
POLY_LAYER = "MUPOLYGON"
ATTR_LAYER = "muaggatt"

OUT_GPKG = Path("Data/Derived/soil_muaggatt.gpkg")
OUT_LAYER = "soil_muaggatt"


def main():
    if not GDB.exists():
        raise FileNotFoundError(f"Missing GDB: {GDB.resolve()}")

    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)

    print("Loading polygons...")
    polys = gpd.read_file(GDB, layer=POLY_LAYER)
    polys.columns = [c.lower() for c in polys.columns]

    print("Loading muaggatt attributes...")
    # muaggatt is a non-spatial table, but geopandas can read it as a dataframe-like table
    attrs = gpd.read_file(GDB, layer=ATTR_LAYER)
    attrs.columns = [c.lower() for c in attrs.columns]

    if "mukey" not in polys.columns:
        raise KeyError(f"{POLY_LAYER} has no 'mukey'. Columns: {list(polys.columns)[:30]}")
    if "mukey" not in attrs.columns:
        raise KeyError(f"{ATTR_LAYER} has no 'mukey'. Columns: {list(attrs.columns)[:30]}")

    polys["mukey"] = polys["mukey"].astype(str)
    attrs["mukey"] = attrs["mukey"].astype(str)

    keep_cols = ["mukey"]

    # Add common useful columns *if they exist*
    candidates = [
        "hydgrpdcd",     # Hydrologic Soil Group (A/B/C/D)
        "slopegradwta",  # soil slope gradient weighted avg
        "drclassdcd",    # drainage class
        "kwfact",        # K-factor (sometimes in muaggatt, sometimes not)
        "aws0_25wta",    # available water storage 0-25cm
        "wtdepannmin",   # water table depth
    ]
    for c in candidates:
        if c in attrs.columns:
            keep_cols.append(c)

    attrs2 = attrs[keep_cols].copy()

    print("Joining attributes to polygons...")
    out = polys.merge(attrs2, on="mukey", how="left")

    # Save
    if OUT_GPKG.exists():
        OUT_GPKG.unlink()
    out.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG")

    print(f"Saved: {OUT_GPKG} (layer={OUT_LAYER})")
    print("Columns saved:", keep_cols)


if __name__ == "__main__":
    main()
