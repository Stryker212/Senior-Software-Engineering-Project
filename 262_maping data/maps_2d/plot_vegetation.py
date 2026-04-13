from __future__ import annotations

import rasterio
import matplotlib.pyplot as plt

from common import make_map_figure, add_basemap

NLCD_RASTER = "Data/Vegetation/NLCD_2016_Land_Cover_OR.img"

def main():
    with rasterio.open(NLCD_RASTER) as src:
        nlcd = src.read(1)
        extent = [
            src.bounds.left,
            src.bounds.right,
            src.bounds.bottom,
            src.bounds.top,
        ]

    fig, ax = make_map_figure("Oregon — Vegetation / Land Cover")
    ax.imshow(
        nlcd,
        extent=extent,
        cmap="tab20",
        alpha=0.75,
        origin="upper"
    )
    add_basemap(ax, zoom=7)

    fig.savefig("outputs/maps_2d/oregon_vegetation.png", dpi=260, bbox_inches="tight")

if __name__ == "__main__":
    main()
