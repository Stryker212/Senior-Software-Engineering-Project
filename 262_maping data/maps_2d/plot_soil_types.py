from __future__ import annotations

import geopandas as gpd

from common import make_map_figure, add_basemap, set_extent

SOIL_GPKG = "Data/Soil/gNATSGO_OR.gpkg"
SOIL_LAYER = "MUPOLYGON"
SOIL_FIELD = "hydgrpdcd"   # change if you prefer another

def main():
    soil = gpd.read_file(SOIL_GPKG, layer=SOIL_LAYER)
    soil = soil.to_crs(epsg=2992)

    fig, ax = make_map_figure("Oregon — Soil Hydrologic Groups")
    set_extent(ax, soil)
    add_basemap(ax, zoom=7)

    soil.plot(
        ax=ax,
        column=SOIL_FIELD,
        categorical=True,
        legend=True,
        alpha=0.65,
        linewidth=0
    )

    fig.savefig("outputs/maps_2d/oregon_soil_types.png", dpi=260, bbox_inches="tight")

if __name__ == "__main__":
    main()
