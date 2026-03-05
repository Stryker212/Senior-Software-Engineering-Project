from __future__ import annotations

from pathlib import Path
import numpy as np
import rasterio
from rasterio.enums import Resampling
import matplotlib.pyplot as plt

from common import make_map_figure, add_basemap, ensure_outdir, Paths

SLOPE_RASTER = Path("Data/Raster/slope_2992.tif")
DOWNSAMPLE = 8


def main():
    paths = Paths()
    ensure_outdir(paths)

    with rasterio.open(SLOPE_RASTER) as src:
        out_h = src.height // DOWNSAMPLE
        out_w = src.width // DOWNSAMPLE

        slope = src.read(
            1,
            out_shape=(out_h, out_w),
            resampling=Resampling.bilinear,
        ).astype("float32")

        extent = (
            src.bounds.left,
            src.bounds.right,
            src.bounds.bottom,
            src.bounds.top,
        )

        nodata = src.nodata

    # Mask nodata
    if nodata is not None:
        slope[slope == nodata] = np.nan

    vmin = 0.0
    vmax = float(np.nanpercentile(slope, 99))

    fig, ax = make_map_figure("Oregon — Slope (degrees)")

    # 1) set extent BEFORE basemap
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])

    # 2) add basemap (it WILL reset things)
    add_basemap(ax, zoom=7)

    # 3) RESTORE extent after basemap (critical)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])

    # 4) draw slope on top
    im = ax.imshow(
        slope,
        extent=extent,
        cmap="YlOrRd",
        vmin=vmin,
        vmax=vmax,
        alpha=1.0,
        origin="upper",
        zorder=10,
        interpolation="nearest",
    )

    plt.colorbar(im, ax=ax, label="Slope (degrees)")

    out = paths.out_dir / "oregon_slope.png"
    fig.savefig(out, dpi=260, bbox_inches="tight")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
