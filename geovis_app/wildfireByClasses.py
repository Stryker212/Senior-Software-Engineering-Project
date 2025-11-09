# python3 -m venv path/to/venv
    # source path/to/venv/bin/activate
# python3 -m pip install geopandas matplotlib contextily rasterio fiona shapely pyproj

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from shapely.geometry import Point
import contextily as ctx

def load_wildfire_data():
    df = pd.read_csv("geovis_app/data/ODF_Fire_Occurrence_Data_2000-2022_20251019.csv") 
    geometry = [Point(xy) for xy in zip(df['Long_DD'], df['Lat_DD'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    return gdf
    
def plot_fire_classes(ax=None):
    gdf = load_wildfire_data()

    # map colors to wildfire classes
    color_class = { 
    "A": '#FFFFB2',
    "B": '#FED976',
    "C": '#FEB24C',
    "D": '#FD8D3C',
    "E": '#FC4E2A',
    "F": '#E31A1C',
    "G": '#BD0026'
    }

    # https://www.researchgate.net/figure/The-NWCG-wildfire-classification-is-based-on-the-size-of-acres-covered-by-the-wildfire_tbl1_381173395
    size_ranges = {
        "A": "0.01-0.25 acres",
        "B": "0.26-9.9 acres",
        "C": "10.0-99.9 acres",
        "D": "100-299 acres",
        "E": "300-999 acres",
        "F": "1000-4999 acres",
        "G": ">5000 acres"
    }

    gdf['color'] = gdf['Size_class'].map(color_class) # assign colors
    gdf = gdf.to_crs(epsg=3857) # convert crs for basemap

    if ax is None: # create figure and axes if none given
        fig, ax = plt.subplots(figsize=(10,10))

    gdf.plot(
        ax=ax,
        color=gdf['color'],
        markersize = 3, # point size
        alpha = 0.4 # transparency of points
    )
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

    # create legend
    patches = [mpatches.Patch(color=color, label = f"{cls}: {size_ranges[cls]}") for cls, color in color_class.items()]
    ax.legend(handles=patches, title="Wilfire Class", loc='lower right')

    if ax is None:  
        plt.title("Wildfires by Size Class")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.show()
    
    return ax

if __name__ == "__main__":
    plot_fire_classes()
    plt.show()




