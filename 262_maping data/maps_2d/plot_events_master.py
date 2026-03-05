from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

from common import (
    Paths, ensure_outdir,
    load_points, load_damage_grid,
    make_map_figure, add_basemap, set_extent
)


def plot_damage_grid_qgis_like(ax, grid, value_col: str):
    vals = grid[value_col].astype(float)
    vals = vals.where(vals > 0)

    grid = grid.copy()
    grid[value_col] = vals
    positive = vals.dropna()

    if len(positive) == 0:
        grid.boundary.plot(ax=ax, linewidth=0.25, color="black", alpha=0.5)
        return

    q = [0.0, 0.12, 0.25, 0.38, 0.50, 0.62, 0.75, 0.88, 0.96, 1.0]
    breaks = np.quantile(positive, q)
    breaks = np.unique(breaks)

    if len(breaks) < 3:
        mn, mx = float(positive.min()), float(positive.max())
        breaks = np.linspace(mn, mx, 10)

    cmap = plt.cm.Reds
    norm = BoundaryNorm(breaks, ncolors=cmap.N, clip=True)

    grid.plot(
        ax=ax,
        column=value_col,
        cmap=cmap,
        norm=norm,
        alpha=0.60,
        linewidth=0.0
    )
    grid.boundary.plot(ax=ax, linewidth=0.25, color="black", alpha=0.55)


def main():
    paths = Paths()
    ensure_outdir(paths)

    grid = load_damage_grid(paths)
    fires = load_points(paths.wildfire_points)
    slides = load_points(paths.landslide_points)

    fig, ax = make_map_figure("Oregon — Damage Grid + Wildfires + Landslides")
    set_extent(ax, grid)          # lock to Oregon grid extent
    add_basemap(ax, zoom=7)

    # Underlay: damage grid
    plot_damage_grid_qgis_like(ax, grid, paths.damage_value_col)

    # Overlay: points
    fires.plot(ax=ax, markersize=2, alpha=0.55, label="Wildfires")
    slides.plot(ax=ax, markersize=6, alpha=0.75, label="Landslides")

    ax.legend(loc="lower left", framealpha=0.95)

    out = paths.out_dir / "oregon_damage_grid_wildfires_landslides.png"
    fig.savefig(out, dpi=260, bbox_inches="tight")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
