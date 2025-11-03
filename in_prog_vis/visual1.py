# python3 -m venv path/to/venv
    # source path/to/venv/bin/activate
# python3 -m pip install geopandas matplotlib contextily rasterio fiona shapely pyproj

import geopandas as gpd # geospatial data
import pandas as pd # csv data 
import matplotlib.pyplot as plt # plot maps and graphs
from shapely.geometry import Point # convert coordinates to geometric points
import contextily as ctx # add basemaps
import matplotlib.patches as mpatches
import fiona

# load wildfire data
df = pd.read_csv("data/ODF_Fire_Occurrence_Data_2000-2022_20251103.csv") # reads csv into table df
geometry = [Point(xy) for xy in zip(df['Long_DD'], df['Lat_DD'])] # coordinate for wildfire
gdf_wildfires = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

# map colors to wildfire classes
wildfire_size_class = { 
    "A": '#FFFFB2',
    "B": '#FED976',
    "C": '#FEB24C',
    "D": '#FD8D3C',
    "E": '#FC4E2A',
    "F": '#E31A1C',
    "G": '#BD0026'
}

gdf_wildfires['color'] = gdf_wildfires['Size_class'].map(wildfire_size_class) # color column based on class
gdf_wildfires = gdf_wildfires.to_crs(epsg=3857) # for basemap

# load soil data
gdb_path = "data/gNATSGO_OR.gdb"
layers = fiona.listlayers(gdb_path)
#print("available layers:", layers)
gdf_soil = gpd.read_file(gdb_path, layer="MUPOLYGON", driver="OpenFileGDB", METHOD="SKIP")
gdf_soil = gdf_soil.to_crs(epsg=3857)
#print(gdf_soil['MUSYM'].unique())  # see all distinct soil types
#print(gdf_soil[['MUSYM', 'Shape_Area']].head())  # show a couple rows

soil_colors = {
    '31E': '#a6cee3',
    '27': '#1f78b4',
    '71B': '#b2df8a',
    '21D': '#33a02c',
    'W': '#fb9a99',
    's6512': '#fdbf6f',
    's2226': '#e31a1c'
}

gdf_soil['color'] = gdf_soil['MUSYM'].map(soil_colors).fillna('lightgreen')

# plot soil polygons then wildfires on top
fig, ax = plt.subplots(figsize=(12, 8))
gdf_soil.plot(
    ax=ax, 
    color=gdf_soil['color'], 
    edgecolor='black', 
    linewidth=0.1,
    alpha = 0.7
)
gdf_wildfires.plot(
    ax=ax, 
    color=gdf_wildfires['color'],
    alpha=0.4 # transparency of points
    )

ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

# create legends
soil_patches = [mpatches.Patch(color=color, label=cls) for cls, color in soil_colors.items()]
wildfire_patches = [mpatches.Patch(color=color, label=soil) for soil, color in wildfire_size_class.items()]

# add legends
legend_soil = ax.legend(handles=soil_patches, title="Soil Types", loc='lower right')
ax.add_artist(legend_soil)

legend_wildfire = ax.legend(handles=wildfire_patches, title="Wildfire Class", loc='upper right')

plt.title("Wildfires over Soil Map")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.show()
