import os
import geopandas as gpd

def load_layer():
    """
    Loads preprocessed wildfire polygons (GeoJSON) for fast display.
    """

    geojson_file = "geovis_app/data/wildfire_polygons_clean.geojson"
    geojson_path = os.path.join(os.path.dirname(__file__), "..", geojson_file)
    gdf = gpd.read_file(geojson_path)

    return gdf
