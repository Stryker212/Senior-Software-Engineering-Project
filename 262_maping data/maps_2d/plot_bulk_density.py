from __future__ import annotations

from pathlib import Path
import numpy as np
import rasterio

from common import make_map_figure, add_basemap, ensure_outdir, Paths


# Your raster path (based on your screenshot)
BULK_TIF = Path("Data/Soil/bulk_density_100cm_oregon.tif")
TITLE = "Oregon — Soil Bulk Density (0–100 cm)"
OUT_NAME = "oregon_bulk_density.png"


def main():
    paths = Paths()
    ensure_outdir(paths)

    if not BULK_TIF.exists():
        raise FileNotFoundError(f"Raster not found: {BULK_TIF.resolve()}")

    with rasterio.open(BULK_TIF) as src:
        data = src.read(1).astype("float32")
        nodata = src.nodata
        bounds = src.bounds
        crs = src.crs

    print("CRS:", crs)
    print("Bounds:", bounds)

    # Mask nodata
    if nodata is not None:
        data[data == nodata] = np.nan

    finite = data[np.isfinite(data)]
    print("Min:", np.min(finite))
    print("Max:", np.max(finite))

    fig, ax = make_map_figure(TITLE)

    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

    img = ax.imshow(
        data,
        extent=extent,
        origin="upper",
        cmap="viridis",
        alpha=0.75,
        zorder=10,
    )

    # Basemap
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    add_basemap(ax, zoom=7)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])

    cbar = fig.colorbar(img, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Bulk Density (g/cm³)")

    ax.set_axis_off()

    out = paths.out_dir / OUT_NAME
    fig.savefig(out, dpi=260, bbox_inches="tight")
    print("Saved:", out)


if __name__ == "__main__":
    main()
