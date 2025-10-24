# ============================================================
# Oregon Landslide Initial Visualization: Capstone
# Author: Umna Khawaja 
# Description:
#   Creates maps and charts for historic Oregon landslides
#   using DOGAMI SLIDO-4.5 geodatabase data.
# ============================================================

import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
import pandas as pd

# Path to your local SLIDO geodatabase (.gdb)
gdb_path = r"C:\Users\umnak\Downloads\SLIDO_Release_4p5_wMetadata.gdb\SLIDO_Release_4p5_wMetadata.gdb"  # ⬅️ change this to your actual path

# Load layer — "Historic_Landslide_Points" contains event data
gdf = gpd.read_file(gdb_path, layer="Historic_Landslide_Points")

print("Columns:", gdf.columns)
print("Number of records:", len(gdf))

# Drop missing geometry or year values
gdf = gdf.dropna(subset=["geometry", "YEAR"])

# Convert coordinate reference system to Web Mercator (for basemap)
if gdf.crs != "EPSG:3857":
    gdf = gdf.to_crs(epsg=3857)

# --- Create a new column for decade groupings ---
def year_to_decade(year):
    if year < 1950:
        return "Before 1950"
    elif year < 1960:
        return "1950s"
    elif year < 1970:
        return "1960s"
    elif year < 1980:
        return "1970s"
    elif year < 1990:
        return "1980s"
    elif year < 2000:
        return "1990s"
    elif year < 2010:
        return "2000s"
    elif year < 2020:
        return "2010s"
    else:
        return "2020s"

gdf["Decade"] = gdf["YEAR"].apply(year_to_decade)

# --- Visualization 1: Map of landslides by decade ---
fig, ax = plt.subplots(figsize=(10, 10))
gdf.plot(ax=ax, column="Decade", legend=True, cmap="Set1", markersize=5)
ax.set_title("Historic Landslides in Oregon (Grouped by Decade)", fontsize=14)
ax.set_xlabel("Longitude (meters in Web Mercator)", fontsize=12)
ax.set_ylabel("Latitude (meters in Web Mercator)", fontsize=12)

# Add base map
cx.add_basemap(ax, source=cx.providers.OpenStreetMap.Mapnik)

plt.tight_layout()
plt.show()

# --- Visualization 2: Bar chart of number of landslides per decade ---
decade_counts = gdf["Decade"].value_counts().reindex([
    "Before 1950", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"
])

plt.figure(figsize=(10, 6))
decade_counts.plot(kind="bar", color="seagreen")
plt.title("Number of Landslides per Decade", fontsize=14)
plt.xlabel("Decade", fontsize=12)
plt.ylabel("Number of Landslides", fontsize=12)
plt.xticks(rotation=45)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()