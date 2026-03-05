# maps_2d/build_damage_grid.py
"""
Build the 10km damage grid (wildfire + landslide counts + estimated damages).
Outputs:
  - Data/Base/grid_fire_slide_counts_2992.gpkg (layer: grid_counts)
  - Data/Base/grid_counts_summary.csv
"""

from __future__ import annotations

from pathlib import Path
import geopandas as gpd

TARGET_EPSG = 2992

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Data"

GRID_FP = DATA / "Base" / "grid_10km_2992ft.gpkg"
FIRE_FP = DATA / "Events" / "wildfire_points_2000_2022.geojson"
SLIDE_FP = DATA / "Events" / "landslide_points.geojson"

OUT_GPKG = DATA / "Base" / "grid_fire_slide_counts_2992.gpkg"
OUT_CSV = DATA / "Base" / "grid_counts_summary.csv"


def main():
    print("Loading layers…")
    grid = gpd.read_file(GRID_FP).to_crs(TARGET_EPSG)
    fire = gpd.read_file(FIRE_FP)
    slide = gpd.read_file(SLIDE_FP)

    if fire.crs is None:
        fire = fire.set_crs(epsg=4326)
    if slide.crs is None:
        slide = slide.set_crs(epsg=4326)

    fire = fire.to_crs(TARGET_EPSG)
    slide = slide.to_crs(TARGET_EPSG)

    print("Adding cell_id to grid…")
    if "cell_id" not in grid.columns:
        grid["cell_id"] = range(1, len(grid) + 1)

    print("Counting events per cell…")
    fire_join = gpd.sjoin(fire, grid, predicate="within")
    slide_join = gpd.sjoin(slide, grid, predicate="within")

    fire_counts = fire_join["cell_id"].value_counts().rename("fire_count")
    slide_counts = slide_join["cell_id"].value_counts().rename("slide_count")

    grid = (
        grid.merge(fire_counts, on="cell_id", how="left")
            .merge(slide_counts, on="cell_id", how="left")
    )
    grid["fire_count"] = grid["fire_count"].fillna(0).astype(int)
    grid["slide_count"] = grid["slide_count"].fillna(0).astype(int)

    # Estimated damage (USD) — keep your constants for now
    grid["est_damage_usd"] = (grid["fire_count"] * 90_000) + (grid["slide_count"] * 146_000)

    print(f"Writing {OUT_GPKG}")
    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    grid.to_file(OUT_GPKG, layer="grid_counts", driver="GPKG")

    summary = grid[["cell_id", "fire_count", "slide_count", "est_damage_usd"]]
    summary.to_csv(OUT_CSV, index=False)

    print(f"Wrote: {OUT_CSV}")
    print("Done.")


if __name__ == "__main__":
    main()
