# ============================================================
# Oregon Landslide Integrated Visualization
# Author: Umna Khawaja
# Description:
#   One-map view of historic Oregon landslides, showing both
#   decade (categorical) and elevation (continuous) with two legends.
# ============================================================

import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
import rasterio
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.patches as mpatches

# --- Load Landslide Data ---
gdb_path = r"C:\Users\umnak\Downloads\SLIDO_Release_4p5_wMetadata.gdb\SLIDO_Release_4p5_wMetadata.gdb"
gdf = gpd.read_file(gdb_path, layer="Historic_Landslide_Points")
gdf = gdf.dropna(subset=["geometry", "YEAR"])

# Convert CRS for basemap
if gdf.crs != "EPSG:3857":
    gdf = gdf.to_crs(epsg=3857)

# --- Add Decade ---
def year_to_decade(year):
    if year < 1950: return "Before 1950"
    elif year < 1960: return "1950s"
    elif year < 1970: return "1960s"
    elif year < 1980: return "1970s"
    elif year < 1990: return "1980s"
    elif year < 2000: return "1990s"
    elif year < 2010: return "2000s"
    elif year < 2020: return "2010s"
    else: return "2020s"

gdf["Decade"] = gdf["YEAR"].apply(year_to_decade)

# --- Elevation (raster DEM) ---
dem = rasterio.open(r"C:\Users\umnak\Downloads\OR_DEM_10M.gdb\OR_DEM_10M.gdb")
coords = [(x, y) for x, y in zip(gdf.geometry.x, gdf.geometry.y)]
gdf["Elevation"] = [val[0] for val in dem.sample(coords)]

# --- Fallbacks ---
if "Soil_Type" not in gdf.columns:
    gdf["Soil_Type"] = "Unknown"

# ============================================================
# PLOT MAP
# ============================================================

fig, ax = plt.subplots(figsize=(11, 11))

# --- Color by Decade (categorical) ---
decade_colors = {
    "Before 1950": "#e41a1c",
    "1950s": "#377eb8",
    "1960s": "#4daf4a",
    "1970s": "#984ea3",
    "1980s": "#ff7f00",
    "1990s": "#ffff33",
    "2000s": "#a65628",
    "2010s": "#f781bf",
    "2020s": "#999999"
}
gdf["Decade_Color"] = gdf["Decade"].map(decade_colors)

# --- Plot points (color = decade, size = elevation) ---
gdf.plot(
    ax=ax,
    color=gdf["Decade_Color"],
    markersize=(gdf["Elevation"] / gdf["Elevation"].max()) * 100,
    alpha=0.7,
    edgecolor="black",
    linewidth=0.2
)

# --- Add continuous elevation legend ---
cmap = plt.cm.Greens
norm = Normalize(vmin=gdf["Elevation"].min(), vmax=gdf["Elevation"].max())
sm = ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.6)
cbar.set_label("Elevation (tens of meters)", fontsize=12)

# --- Add categorical legend for decade ---
patches = [mpatches.Patch(color=color, label=decade) for decade, color in decade_colors.items()]
ax.legend(handles=patches, title="Decade", loc="upper left")

# Add base map
cx.add_basemap(ax, source=cx.providers.OpenStreetMap.Mapnik)
ax.set_title("Historic Oregon Landslides (Decade + Elevation)", fontsize=15)
ax.set_xlabel("Longitude (meters in Web Mercator)")
ax.set_ylabel("Latitude (meters in Web Mercator)")

plt.tight_layout()
plt.show()
