# maps_2d/plot_damage_by_altitude.py
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

from common import (
    Paths, ensure_outdir,
    load_damage_grid, make_map_figure, add_basemap, set_extent
)


ALT_BANDS_FT = [
    (0, 1000, "0-1000ft"),
    (1000, 2000, "1000-2000ft"),
    (2000, 3000, "2000-3000ft"),
    (3000, 4000, "3000-4000ft"),
    (4000, None, "4000ft+"),
]


def plot_damage_grid_qgis_like(ax, grid, value_col: str):
    """
    QGIS-like styling:
    - classified bins (quantiles)
    - Reds ramp
    - NO rendering of zero / nodata cells
    - borders only for visible cells
    """
    grid = grid.copy()
    grid[value_col] = grid[value_col].astype(float)

    # Hide zeros/nodata entirely
    grid = grid[grid[value_col] > 0]
    if grid.empty:
        return

    vals = grid[value_col]

    # quantile breaks (good for skewed data)
    q = [0.0, 0.12, 0.25, 0.38, 0.50, 0.62, 0.75, 0.88, 0.96, 1.0]
    breaks = np.quantile(vals, q)
    breaks = np.unique(breaks)

    # fallback if quantiles collapse
    if len(breaks) < 3:
        mn, mx = float(vals.min()), float(vals.max())
        breaks = np.linspace(mn, mx, 10)

    cmap = plt.cm.Reds
    norm = BoundaryNorm(breaks, ncolors=cmap.N, clip=True)

    # fill
    grid.plot(
        ax=ax,
        column=value_col,
        cmap=cmap,
        norm=norm,
        alpha=0.65,
        linewidth=0.0
    )

    # borders
    grid.boundary.plot(ax=ax, linewidth=0.25, color="black", alpha=0.55)


def filter_grid_by_altitude(grid, elev_col: str, lo: float, hi: float | None):
    """
    Returns subset of grid where elevation is within [lo, hi) (or >= lo if hi is None).
    """
    g = grid.copy()
    g[elev_col] = g[elev_col].astype(float)

    if hi is None:
        return g[g[elev_col] >= lo]
    return g[(g[elev_col] >= lo) & (g[elev_col] < hi)]


def main():
    paths = Paths()
    ensure_outdir(paths)

    grid = load_damage_grid(paths)

    # Validate columns early (clear error if mismatched)
    if paths.elev_col_ft not in grid.columns:
        raise ValueError(
            f"Elevation column '{paths.elev_col_ft}' not found in grid. "
            f"Columns are: {list(grid.columns)}"
        )
    if paths.damage_value_col not in grid.columns:
        raise ValueError(
            f"Damage column '{paths.damage_value_col}' not found in grid. "
            f"Columns are: {list(grid.columns)}"
        )

    # Keep consistent extent across all outputs (full Oregon grid)
    extent_ref = grid

    for lo, hi, label in ALT_BANDS_FT:
        sub = filter_grid_by_altitude(grid, paths.elev_col_ft, lo, hi)

        title = f"Oregon — Estimated Damage ({label})"
        fig, ax = make_map_figure(title)

        set_extent(ax, extent_ref)
        add_basemap(ax, zoom=7)

        # Plot only cells within altitude band
        plot_damage_grid_qgis_like(ax, sub, paths.damage_value_col)

        out = paths.out_dir / f"oregon_damage_{label}.png"
        fig.savefig(out, dpi=260, bbox_inches="tight")
        print(f"Saved: {out}")


if __name__ == "__main__":
    main()
