from __future__ import annotations

import rasterio
import numpy as np
import matplotlib.pyplot as plt

from common import make_map_figure, add_basemap

NLCD_RASTER = "Data/Vegetation/NLCD_2016_Land_Cover_OR.img"
FOREST_CLASSES = [41, 42, 43]

def main():
    with rasterio.open(NLCD_RASTER) as src:
        nlcd = src.read(1)
        extent = [
            src.bounds.left,
            src.bounds.right,
            src.bounds.bottom,
            src.bounds.top,
        ]

    forest = np.isin(nlcd, FOREST_CLASSES)

    fig, ax = make_map_figure("Oregon — Forested Areas")
    ax.imshow(
        forest,
        extent=extent,
        cmap="Greens",
        alpha=0.75,
        origin="upper"
    )
    add_basemap(ax, zoom=7)

    fig.savefig("outputs/maps_2d/oregon_forest_cover.png", dpi=260, bbox_inches="tight")

if __name__ == "__main__":
    main()
