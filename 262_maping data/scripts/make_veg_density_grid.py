"""
make_veg_density_grid.py

Compute vegetation density per grid cell using NLCD raster.
Outputs:
  Data/Derived/grid_veg_density_2992.gpkg  (grid polygons with veg_density field)

Run:
  python scripts/make_veg_density_grid.py
"""

from pathlib import Path
import geopandas as gpd
import rasterio
from rasterstats import zonal_stats

GRID_GPKG = Path("Data/Base/grid_fire_slide_counts_2992.gpkg")
GRID_LAYER = None  # set if needed
NLCD_RASTER = Path("Data/Vegetation/nlcd_2016_2992.tif")

OUT_GPKG = Path("Data/Derived/grid_veg_density_2992.gpkg")

# NLCD "vegetation-ish" classes
VEG_CLASSES = {41, 42, 43, 52, 71, 81, 82, 90, 95}


def main():
    grid = gpd.read_file(GRID_GPKG, layer=GRID_LAYER) if GRID_LAYER else gpd.read_file(GRID_GPKG)
    grid = grid[grid.geometry.notna() & ~grid.geometry.is_empty].copy()

    with rasterio.open(NLCD_RASTER) as src:
        raster_crs = src.crs

    if grid.crs != raster_crs:
        grid = grid.to_crs(raster_crs)

    # Count pixels per class inside each polygon
    stats = zonal_stats(
        grid,
        NLCD_RASTER,
        categorical=True,
        nodata=0,
        all_touched=False,
    )

    veg_density = []
    for d in stats:
        if not d:
            veg_density.append(None)
            continue
        total = sum(d.values())
        veg = sum(v for k, v in d.items() if int(k) in VEG_CLASSES)
        veg_density.append(veg / total if total > 0 else None)

    grid["veg_density"] = veg_density

    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    grid.to_file(OUT_GPKG, driver="GPKG")
    print(f"Wrote: {OUT_GPKG}")


if __name__ == "__main__":
    main()