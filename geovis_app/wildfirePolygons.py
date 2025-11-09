# be in geovis_app directory to run -> cd geovis_app
# python3 wildfirePolygons.py
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import os

def load_wildfire_polygon_data():
    shapefile_path = os.path.join(os.path.dirname(__file__), "data/BLM_Fire_Poly/BLM_OR_Fire_Poly_Hub.shp")
    gdf = gpd.read_file(shapefile_path)
    gdf = gdf.to_crs(epsg=3857) # convert crs for basemap

    return gdf

def plot_wildfire_polygons(ax=None):
    gdf = load_wildfire_polygon_data()

    # filter dataset for Oregon only
    us_states_shapefile = os.path.join(os.path.dirname(__file__), "data/US_State_Boundaries/US_State_Boundaries.shp")
    states = gpd.read_file(us_states_shapefile)
    oregon = states[states['NAME'] == 'Oregon'].to_crs(epsg=3857)
    gdf = gpd.clip(gdf, oregon)

    if ax is None: # create figure and axes if none given
        fig, ax = plt.subplots(figsize=(10,10))

    gdf.plot(
        ax=ax,
        edgecolor="red", # polygon border color
        facecolor="#FFB6C1", # no fill color for polygons
        linewidth = 0.5, 
        alpha=0.6 # transparency of polygons
    )
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

    if ax is None:  
        plt.title("Wildfire Polygons")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.show()

    return ax

if __name__ == "__main__":
    plot_wildfire_polygons()
    plt.show()