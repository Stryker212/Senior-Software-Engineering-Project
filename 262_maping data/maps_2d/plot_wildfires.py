from __future__ import annotations

from common import (
    Paths, ensure_outdir,
    load_points, make_map_figure, add_basemap, set_extent
)


def main():
    paths = Paths()
    ensure_outdir(paths)

    fires = load_points(paths.wildfire_points)

    fig, ax = make_map_figure("Oregon — Wildfire Points (basemap)")
    set_extent(ax, fires)
    add_basemap(ax, zoom=7)

    fires.plot(ax=ax, markersize=2, alpha=0.6, label="Wildfires")

    ax.legend(loc="lower left")

    out = paths.out_dir / "oregon_wildfires_points.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
