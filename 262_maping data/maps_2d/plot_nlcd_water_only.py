from __future__ import annotations

from pathlib import Path
import numpy as np
import rasterio
from rasterio.enums import Resampling
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

from common import make_map_figure, add_basemap, ensure_outdir, Paths

NLCD_RASTER = Path("Data/Vegetation/nlcd_2016_2992.tif")
DOWNSAMPLE = 8

# Water-related NLCD classes
WATER_GROUPS = [
    ("Open Water", {11}, "#466b9f"),
    ("Woody Wetlands", {90}, "#b8d9eb"),
    ("Emergent Herbaceous Wetlands", {95}, "#6c9fb8"),
]

def main():
    paths = Paths()
    ensure_outdir(paths)

    with rasterio.open(NLCD_RASTER) as src:
        out_h = max(1, src.height // DOWNSAMPLE)
        out_w = max(1, src.width // DOWNSAMPLE)

        nlcd = src.read(1, out_shape=(out_h, out_w), resampling=Resampling.nearest).astype("int32")
        extent = (src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top)
        nodata = src.nodata

    if nodata is not None:
        nlcd[nlcd == nodata] = -9999

    idx = np.full(nlcd.shape, -1, dtype=np.int16)
    for i, (_, codes, _) in enumerate(WATER_GROUPS):
        idx[np.isin(nlcd, list(codes))] = i

    idx = np.ma.masked_where(idx < 0, idx)

    colors = [c for _, _, c in WATER_GROUPS]
    labels = [n for n, _, _ in WATER_GROUPS]

    cmap = ListedColormap(colors)
    cmap.set_bad(alpha=0.0)
    norm = BoundaryNorm(np.arange(-0.5, len(colors) + 0.5, 1), cmap.N)

    fig, ax = make_map_figure("Oregon — Water & Wetlands (NLCD 2016)")

    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    add_basemap(ax, zoom=7)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])

    ax.imshow(
        idx,
        extent=extent,
        cmap=cmap,
        norm=norm,
        alpha=0.95,
        origin="upper",
        interpolation="nearest",
        zorder=10,
    )

    handles = [Patch(facecolor=colors[i], edgecolor="none", label=labels[i]) for i in range(len(labels))]
    ax.legend(handles=handles, loc="lower left", fontsize=9, frameon=True, framealpha=0.92)

    out = paths.out_dir / "oregon_water_wetlands_nlcd2016.png"
    fig.savefig(out, dpi=260, bbox_inches="tight")
    print(f"Saved: {out}")

if __name__ == "__main__":
    main()
