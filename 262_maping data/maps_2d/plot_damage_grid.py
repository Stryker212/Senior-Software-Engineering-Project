from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm

from common import (
    Paths, ensure_outdir,
    load_damage_grid, make_map_figure, add_basemap, set_extent
)


def plot_damage_grid_qgis_like(ax, grid, value_col: str):
    """
    QGIS-like styling:
    - classified bins (quantiles)
    - Reds ramp
    - NO rendering of zero / nodata cells
    - borders only for visible cells
    """

    # Work on a copy
    grid = grid.copy()

    # Treat zero or negative as NoData
    grid[value_col] = grid[value_col].astype(float)
    grid = grid[grid[value_col] > 0]

    # If nothing left, just return silently
    if grid.empty:
        return

    vals = grid[value_col]

    # Quantile breaks (similar to QGIS "Equal Count")
    q = [0.0, 0.12, 0.25, 0.38, 0.50, 0.62, 0.75, 0.88, 0.96, 1.0]
    breaks = np.quantile(vals, q)
    breaks = np.unique(breaks)

    # Fallback if quantiles collapse
    if len(breaks) < 3:
        mn, mx = float(vals.min()), float(vals.max())
        breaks = np.linspace(mn, mx, 10)

    cmap = plt.cm.Reds
    norm = BoundaryNorm(breaks, ncolors=cmap.N, clip=True)

    # ---- Fill (ONLY non-zero cells) ----
    grid.plot(
        ax=ax,
        column=value_col,
        cmap=cmap,
        norm=norm,
        alpha=0.65,
        linewidth=0.0
    )

    # ---- Borders (ONLY non-zero cells) ----
    grid.boundary.plot(
        ax=ax,
        linewidth=0.25,
        color="black",
        alpha=0.55
    )

    # ---- Legend (range-based, QGIS-like) ----
    handles = []
    labels = []

    for i in range(len(breaks) - 1):
        lo, hi = float(breaks[i]), float(breaks[i + 1])
        mid = (lo + hi) / 2.0
        color = cmap(norm(mid))

        handles.append(
            plt.Line2D(
                [0], [0],
                marker="s",
                linestyle="",
                markersize=10,
                markerfacecolor=color,
                markeredgecolor="black",
                markeredgewidth=0.3
            )
        )
        labels.append(f"${lo:,.0f} – ${hi:,.0f}")

    ax.legend(
        handles, labels,
        title="Estimated Damage (USD)\nper 10km² cell",
        loc="lower left",
        framealpha=0.95
    )

def main():
    paths = Paths()
    ensure_outdir(paths)

    grid = load_damage_grid(paths)

    fig, ax = make_map_figure("Oregon — Estimated Damage (grid)")
    set_extent(ax, grid)
    add_basemap(ax, zoom=7)

    plot_damage_grid_qgis_like(ax, grid, paths.damage_value_col)

    out = paths.out_dir / "oregon_damage_grid.png"
    fig.savefig(out, dpi=240, bbox_inches="tight")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
