import geopandas as gpd
import pandas as pd
from pathlib import Path

# --- Paths ---
ROOT = Path(__file__).resolve().parents[1]
data = ROOT / "data"

grid_fp = data / "grid_10km_2992ft.gpkg"
fire_fp = data / "wildfire_points_2000_2022.geojson"
slide_fp = data / "landslide_points.geojson"
out_gpkg = data / "grid_fire_slide_counts_2992.gpkg"
out_csv = data / "grid_counts_summary.csv"

# --- Load ---
print("Loading layers…")
grid = gpd.read_file(grid_fp).to_crs(2992)
fire = gpd.read_file(fire_fp).to_crs(2992)
slide = gpd.read_file(slide_fp).to_crs(2992)

# --- Add grid ID ---
print("ℹAdding cell_id to grid…")
if "cell_id" not in grid.columns:
    grid["cell_id"] = range(1, len(grid) + 1)

# --- Spatial joins ---
print("Counting events per cell… (this may take a moment)")
fire_join = gpd.sjoin(fire, grid, predicate="within")
slide_join = gpd.sjoin(slide, grid, predicate="within")

fire_counts = fire_join["cell_id"].value_counts().rename("fire_count")
slide_counts = slide_join["cell_id"].value_counts().rename("slide_count")

# --- Merge counts ---
grid = grid.merge(fire_counts, on="cell_id", how="left").merge(slide_counts, on="cell_id", how="left")
grid["fire_count"] = grid["fire_count"].fillna(0).astype(int)
grid["slide_count"] = grid["slide_count"].fillna(0).astype(int)

# --- Estimated damage (USD) ---
grid["est_damage_usd"] = (grid["fire_count"] * 90000) + (grid["slide_count"] * 146000)

# --- Save ---
print(f"Writing {out_gpkg}")
grid.to_file(out_gpkg, layer="grid_counts", driver="GPKG")

summary = grid[["cell_id", "fire_count", "slide_count", "est_damage_usd"]]
summary.to_csv(out_csv, index=False)

print(f"Wrote summary: {out_csv}")
print("Done. Add the GeoPackage to QGIS to symbolize 'fire_count', 'slide_count', or 'est_damage_usd'.")
