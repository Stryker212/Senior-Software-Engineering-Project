from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds

GDB_PATH = Path("Data/Soil/gNATSGO_OR.gdb")
OUT_RASTER = Path("Data/Derived/bulk_density_0_100cm.tif")

DEPTH_TOP = 0
DEPTH_BOTTOM = 100

PARAM_FIELD = "dbovendry_r"   # change to ksat_r or dbovendry_r

def compute_weighted_parameter():

    print("Loading chorizon table...")
    horizons = gpd.read_file(GDB_PATH, layer="chorizon")

    horizons.columns = horizons.columns.str.lower()

    # Keep only needed columns
    horizons = horizons[
        ["cokey", "hzdept_r", "hzdepb_r", PARAM_FIELD]
    ].dropna()

    # Convert to numeric
    horizons["hzdept_r"] = pd.to_numeric(horizons["hzdept_r"])
    horizons["hzdepb_r"] = pd.to_numeric(horizons["hzdepb_r"])
    horizons[PARAM_FIELD] = pd.to_numeric(horizons[PARAM_FIELD])

    # Clip to 0–100cm interval
    horizons["top"] = horizons["hzdept_r"].clip(lower=DEPTH_TOP)
    horizons["bottom"] = horizons["hzdepb_r"].clip(upper=DEPTH_BOTTOM)

    horizons["thickness"] = horizons["bottom"] - horizons["top"]
    horizons = horizons[horizons["thickness"] > 0]

    # Weighted mean per cokey
    horizons["weighted"] = horizons[PARAM_FIELD] * horizons["thickness"]

    grouped = horizons.groupby("cokey").agg(
        total_weighted=("weighted", "sum"),
        total_thickness=("thickness", "sum")
    )

    grouped["value_0_100"] = grouped["total_weighted"] / grouped["total_thickness"]

    return grouped["value_0_100"].reset_index()


def join_to_polygons(param_df):

    print("Loading MUPOLYGON...")
    polygons = gpd.read_file(GDB_PATH, layer="MUPOLYGON")
    polygons.columns = polygons.columns.str.lower()

    polygons["mukey"] = polygons["mukey"].astype(str)

    print("Loading component table...")
    comp = gpd.read_file(GDB_PATH, layer="component")
    comp.columns = comp.columns.str.lower()

    comp = comp[["mukey", "cokey", "comppct_r"]]
    comp["comppct_r"] = pd.to_numeric(comp["comppct_r"])

    param_df["cokey"] = param_df["cokey"].astype(str)
    comp["cokey"] = comp["cokey"].astype(str)

    merged = comp.merge(param_df, on="cokey", how="left")

    merged["weighted"] = merged["value_0_100"] * merged["comppct_r"]

    mukey_values = merged.groupby("mukey").agg(
        total_weighted=("weighted", "sum"),
        total_pct=("comppct_r", "sum")
    )

    mukey_values["final_value"] = (
        mukey_values["total_weighted"] / mukey_values["total_pct"]
    )

    polygons = polygons.merge(
        mukey_values["final_value"],
        left_on="mukey",
        right_index=True,
        how="left"
    )

    return polygons


def rasterize_polygon(gdf):

    print("Rasterizing...")

    bounds = gdf.total_bounds
    width = 2000
    height = 2000

    transform = from_bounds(*bounds, width, height)

    shapes = ((geom, value) for geom, value in zip(gdf.geometry, gdf["final_value"]))

    raster = rasterize(
        shapes,
        out_shape=(height, width),
        transform=transform,
        fill=np.nan,
        dtype="float32"
    )

    with rasterio.open(
        OUT_RASTER,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="float32",
        crs=gdf.crs,
        transform=transform,
    ) as dst:
        dst.write(raster, 1)

    print(f"Saved: {OUT_RASTER}")


def main():
    param_df = compute_weighted_parameter()
    gdf = join_to_polygons(param_df)
    rasterize_polygon(gdf)


if __name__ == "__main__":
    main()
