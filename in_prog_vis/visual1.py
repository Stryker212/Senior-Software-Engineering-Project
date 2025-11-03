# python3 -m venv path/to/venv
    # source path/to/venv/bin/activate
# python3 -m pip install geopandas matplotlib contextily rasterio fiona shapely pyproj

import geopandas as gpd # geospatial data
import pandas as pd # csv data 
import matplotlib.pyplot as plt # plot maps and graphs
from shapely.geometry import Point # convert coordinates to geometric points
import contextily as ctx # add basemaps
import matplotlib.patches as mpatches

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

fig, ax = plt.subplots(figsize=(12, 8))
gdf_wildfires.plot(
    ax = ax, 
    color=gdf_wildfires['color'],
    alpha = 0.5 # transparency of points
    )

ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

legend_patches = [mpatches.Patch(color=color, label=cls) for cls, color in wildfire_size_class.items()]
ax.legend(handles=legend_patches, title="Wildfire Class")

plt.title("Wildfires by Location and Size_class")
#plt.xlabel("Longitude")
#plt.ylabel("Latitude")
plt.show()