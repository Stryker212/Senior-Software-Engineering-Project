"""
plot_vegetation_nlcd2016.py

Creates a statewide vegetation map from NLCD 2016 (categorical raster).
- Fast: downsamples raster for display
- Groups NLCD classes into simple vegetation categories

Run:
  python scripts/plot_vegetation_nlcd2016.py
"""

from pathlib import Path
import numpy as np
import rasterio
from rasterio.enums import Resampling
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

NLCD_RASTER = Path("Data/Vegetation/nlcd_2016_2992.tif")
OUT_PNG = Path("outputs/maps_2d/oregon_vegetation_nlcd2016.png")

# Bigger = faster + blurrier. 8 or 10 is usually good.
DOWNSAMPLE = 8

# Vegetation-focused groups
VEG_GROUPS = [
    ("Trees (Forest)", {41, 42, 43}, "#1c5f2c"),
    ("Shrub/Scrub", {52}, "#ccb879"),
    ("Grass/Herbaceous", {71}, "#dfdfc2"),
    ("Pasture/Hay", {81}, "#dcd939"),
    ("Cultivated Crops", {82}, "#ab6c28"),
]

def main():
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(NLCD_RASTER) as src:
        out_h = max(1, src.height // DOWNSAMPLE)
        out_w = max(1, src.width // DOWNSAMPLE)

        nlcd = src.read(
            1,
            out_shape=(out_h, out_w),
            resampling=Resampling.nearest,   # correct for categorical NLCD
        ).astype("int32")

        extent = (src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top)
        nodata = src.nodata

    if nodata is not None:
        nlcd[nlcd == nodata] = -9999

    # Build grouped index raster (0..N-1), -1 for non-veg
    idx = np.full(nlcd.shape, -1, dtype=np.int16)
    for i, (_, codes, _) in enumerate(VEG_GROUPS):
        idx[np.isin(nlcd, list(codes))] = i

    idx = np.ma.masked_where(idx < 0, idx)

    colors = [c for _, _, c in VEG_GROUPS]
    labels = [n for n, _, _ in VEG_GROUPS]

    cmap = ListedColormap(colors)
    cmap.set_bad(alpha=0.0)
    norm = BoundaryNorm(np.arange(-0.5, len(colors) + 0.5, 1), cmap.N)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title("Oregon — Vegetation (NLCD 2016)")

    ax.imshow(
        idx,
        extent=extent,
        cmap=cmap,
        norm=norm,
        alpha=0.90,
        origin="upper",
        interpolation="nearest",
    )

    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    handles = [Patch(facecolor=colors[i], edgecolor="none", label=labels[i]) for i in range(len(labels))]
    ax.legend(handles=handles, loc="lower left", fontsize=9, frameon=True, framealpha=0.92)

    fig.savefig(OUT_PNG, dpi=260, bbox_inches="tight")
    print(f"Saved: {OUT_PNG}")

if __name__ == "__main__":
    main()