from __future__ import annotations

from common import (
    Paths, ensure_outdir,
    load_points, make_map_figure, add_basemap, set_extent
)


def main():
    paths = Paths()
    ensure_outdir(paths)

    slides = load_points(paths.landslide_points)

    fig, ax = make_map_figure("Oregon — Landslide Points (basemap)")
    set_extent(ax, slides)
    add_basemap(ax, zoom=7)

    slides.plot(ax=ax, markersize=6, alpha=0.75, label="Landslides")

    ax.legend(loc="lower left")

    out = paths.out_dir / "oregon_landslides_points.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
