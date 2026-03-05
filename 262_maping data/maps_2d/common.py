from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx

TARGET_EPSG = 2992  # Oregon Lambert


@dataclass
class Paths:
    # Events (points)
    wildfire_points: Path = Path("Data/Events/wildfire_points_2000_2022.geojson")
    landslide_points: Path = Path("Data/Events/landslide_points.geojson")

    # Derived damage grid WITH elevation
    # (This is the key change)
    damage_grid_gpkg: Path = Path("Data/Base/grid_fire_slide_counts_2992_with_elev.gpkg")
    damage_grid_layer: str = "grid_counts"

    # Columns in the grid
    damage_value_col: str = "est_damage_usd"
    elev_col_ft: str = "mean_elev_ft"   # <-- your grid should have this

    # Output
    out_dir: Path = Path("outputs/maps_2d")


def ensure_outdir(paths: Paths) -> None:
    paths.out_dir.mkdir(parents=True, exist_ok=True)


def load_points(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    return gdf.to_crs(epsg=TARGET_EPSG)


def load_damage_grid(paths: Paths) -> gpd.GeoDataFrame:
    grid = gpd.read_file(paths.damage_grid_gpkg, layer=paths.damage_grid_layer)
    if grid.crs is None:
        grid = grid.set_crs(epsg=TARGET_EPSG)
    return grid.to_crs(epsg=TARGET_EPSG)


def make_map_figure(title: str, figsize: Tuple[int, int] = (11, 11)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(title)
    ax.set_axis_off()
    return fig, ax


def add_basemap(ax, zoom: int = 7) -> None:
    cx.add_basemap(
        ax,
        crs=f"EPSG:{TARGET_EPSG}",
        source=cx.providers.CartoDB.Positron,
        zoom=zoom
    )


def set_extent(ax, gdf: gpd.GeoDataFrame, pad_ratio: float = 0.03) -> None:
    minx, miny, maxx, maxy = gdf.total_bounds
    dx = (maxx - minx) * pad_ratio
    dy = (maxy - miny) * pad_ratio
    ax.set_xlim(minx - dx, maxx + dx)
    ax.set_ylim(miny - dy, maxy + dy)
