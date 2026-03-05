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

# Increase if needed (12/16 makes it lighter)
DOWNSAMPLE = 8


# NLCD classes commonly present in OR (AK-only classes excluded)
# Colors are NLCD-like (not exact official RGB, but close and readable).
NLCD_CLASSES = [
    (11, "Open Water",                "#466b9f"),
    (12, "Perennial Ice/Snow",        "#d1def8"),
    (21, "Developed, Open Space",     "#dec5c5"),
    (22, "Developed, Low Intensity",  "#d99282"),
    (23, "Developed, Medium Intensity","#eb0000"),
    (24, "Developed, High Intensity", "#ab0000"),
    (31, "Barren Land",               "#b3ac9f"),
    (41, "Deciduous Forest",          "#68ab5f"),
    (42, "Evergreen Forest",          "#1c5f2c"),
    (43, "Mixed Forest",              "#b5ca8f"),
    (51, "Dwarf Scrub*",              "#a68c30"),
    (52, "Shrub/Scrub",               "#ccb879"),
    (71, "Grassland/Herbaceous",      "#dfdfc2"),
    (81, "Pasture/Hay",               "#dcd939"),
    (82, "Cultivated Crops",          "#ab6c28"),
    (90, "Woody Wetlands",            "#b8d9eb"),
    (95, "Emergent Herbaceous Wetlands","#6c9fb8"),
]

# We'll treat 0 as "NoData/Outside" (transparent)
NODATA_VALUE = 0


def main():
    paths = Paths()
    ensure_outdir(paths)

    with rasterio.open(NLCD_RASTER) as src:
        out_h = max(1, src.height // DOWNSAMPLE)
        out_w = max(1, src.width // DOWNSAMPLE)

        # IMPORTANT: nearest resampling for categorical data
        nlcd = src.read(
            1,
            out_shape=(out_h, out_w),
            resampling=Resampling.nearest,
        )

        extent = (src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top)

        nodata = src.nodata

    # Convert nodata to 0 so it can be transparent
    nlcd = nlcd.astype("int32")
    if nodata is not None:
        nlcd[nlcd == nodata] = NODATA_VALUE

    # Build colormap aligned to the class codes we want to show
    class_codes = [c for c, _, _ in NLCD_CLASSES]
    class_names = [n for _, n, _ in NLCD_CLASSES]
    class_colors = [col for _, _, col in NLCD_CLASSES]

    # Create a mapping raster -> palette index
    # Any unknown class will become -1 and be transparent.
    index = np.full(nlcd.shape, -1, dtype=np.int16)
    for i, code in enumerate(class_codes):
        index[nlcd == code] = i

    # Mask unknowns and outside/nodata so they are invisible
    index_masked = np.ma.masked_where(index < 0, index)

    cmap = ListedColormap(class_colors)
    cmap.set_bad(alpha=0.0)  # masked pixels fully transparent

    # Norm: values are indices 0..N-1
    norm = BoundaryNorm(np.arange(-0.5, len(class_codes) + 0.5, 1), cmap.N)

    fig, ax = make_map_figure("Oregon — NLCD Land Cover (2016)")

    # Basemap underlay
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    add_basemap(ax, zoom=7)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])

    # NLCD overlay
    ax.imshow(
        index_masked,
        extent=extent,
        cmap=cmap,
        norm=norm,
        alpha=0.85,
        origin="upper",
        interpolation="nearest",
        zorder=10,
    )

    # Legend
    handles = [Patch(facecolor=class_colors[i], edgecolor="none", label=class_names[i])
               for i in range(len(class_names))]
    ax.legend(
        handles=handles,
        loc="lower left",
        fontsize=8,
        frameon=True,
        framealpha=0.9,
        ncol=2,
    )

    out = paths.out_dir / "oregon_nlcd_2016_landcover.png"
    fig.savefig(out, dpi=260, bbox_inches="tight")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
