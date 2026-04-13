from __future__ import annotations

from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from common import make_map_figure, add_basemap, ensure_outdir, Paths

IN_GPKG = Path("Data/Derived/soil_muaggatt.gpkg")
LAYER = "soil_muaggatt"

# Plot order so legend is stable
HSG_ORDER = ["A", "B", "C", "D", "A/D", "B/D", "C/D"]

# Colors (keep yours)
HSG_COLOR = {
    "A": "#2ca25f",
    "B": "#99d8c9",
    "C": "#fdae6b",
    "D": "#de2d26",
    "A/D": "#41ab5d",
    "B/D": "#7bccc4",
    "C/D": "#fd8d3c",
}

# Friendly display labels (data stays the same)
HSG_LABELS = {
    "A": "High Infiltration (Low Runoff)",
    "B": "Moderate Infiltration",
    "C": "Low Infiltration (High Runoff)",
    "D": "Very Low Infiltration (Very High Runoff)",
    "A/D": "High → Very Low (Drainage Dependent)",
    "B/D": "Moderate → Very Low (Drainage Dependent)",
    "C/D": "Low → Very Low (Drainage Dependent)",
}


def main():
    paths = Paths()
    ensure_outdir(paths)

    gdf = gpd.read_file(IN_GPKG, layer=LAYER)
    gdf.columns = [c.lower() for c in gdf.columns]

    if "hydgrpdcd" not in gdf.columns:
        raise KeyError("hydgrpdcd not found. Run build_soil_attribute.py and confirm muaggatt has it.")

    # Keep only known classes
    gdf["hsg"] = gdf["hydgrpdcd"].astype(str).str.strip()
    gdf = gdf[gdf["hsg"].isin(HSG_ORDER)].copy()

    fig, ax = make_map_figure("Oregon — Hydrologic Soil Group (gNATSGO muaggatt)")

    # Basemap underlay + extent restore
    xmin, ymin, xmax, ymax = gdf.total_bounds
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    add_basemap(ax, zoom=7)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    # Plot each category
    for cat in HSG_ORDER:
        sub = gdf[gdf["hsg"] == cat]
        if len(sub) == 0:
            continue
        sub.plot(ax=ax, color=HSG_COLOR.get(cat, "#999999"), linewidth=0, alpha=0.75, zorder=10)

    # Custom legend with friendly labels
    handles = []
    for c in HSG_ORDER:
        if (gdf["hsg"] == c).any():
            handles.append(Patch(facecolor=HSG_COLOR.get(c, "#999999"),
                                edgecolor="none",
                                label=HSG_LABELS.get(c, c)))

    legend = ax.legend(
        handles=handles,
        loc="lower right",
        bbox_to_anchor=(0.98, 0.04),  # keep it inside the frame with padding
        frameon=True,
        framealpha=0.95,
        facecolor="white",
        edgecolor="black",
        fontsize=9,
        title="Soil Runoff Class",
    )
    legend.set_zorder(20)

    ax.set_axis_off()
    out = paths.out_dir / "oregon_soil_hsg.png"

    # IMPORTANT: bbox_inches="tight" can clip legends; include it explicitly if you keep tight.
    fig.savefig(out, dpi=260, bbox_inches="tight", bbox_extra_artists=[legend])
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
