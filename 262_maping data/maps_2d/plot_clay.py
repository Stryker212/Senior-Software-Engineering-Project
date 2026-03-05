from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np

# Basemap is optional (works if you already used it for fires/slides)
def try_add_basemap(ax, crs):
    try:
        import contextily as ctx
        ctx.add_basemap(ax, crs=crs, source=ctx.providers.CartoDB.Positron, zoom=7)
    except Exception:
        pass


IN_GPKG = Path("Data/Derived/clay_mapunit.gpkg")
LAYER = "clay_mapunit"
OUT_PNG = Path("outputs/maps_2d/oregon_clay_0_30cm.png")


def main():
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(IN_GPKG, layer=LAYER)

    # Drop missing clay
    gdf = gdf[~gdf["clay_pct"].isna()].copy()

    # Good display range: clip extreme outliers so map isn't washed out
    vals = gdf["clay_pct"].to_numpy()
    vmin = 0.0
    vmax = float(np.nanpercentile(vals, 99))  # 99th percentile

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_title("Oregon — Clay Content (0–30 cm, gNATSGO)", fontsize=16)

    # Plot polygons colored by clay %
    gdf.plot(
        column="clay_pct",
        ax=ax,
        cmap="YlOrBr",
        vmin=vmin,
        vmax=vmax,
        linewidth=0,
        alpha=0.80,
        legend=True,
        legend_kwds={"label": "Clay (%)", "shrink": 0.85},
    )

    try_add_basemap(ax, gdf.crs)

    ax.set_axis_off()
    fig.savefig(OUT_PNG, dpi=260, bbox_inches="tight")
    print(f"Saved: {OUT_PNG}")


if __name__ == "__main__":
    main()
