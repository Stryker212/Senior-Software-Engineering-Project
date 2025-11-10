import geopandas as gpd
from shapely.geometry import Point

def load_layer():
    """
    Template for loading any GeoJSON layer.
    Automatically converts Polygons/Lines to centroids for plotting.
    """

    # --- Path to your GeoJSON file ---
    #geojson_path = r"C:\data_stryker\wildfire_points_epsg2992.geojson"
    geojson_path = r"data_stryker/wildfire_points_epsg2992.geojson"

    # --- Load GeoJSON into GeoDataFrame ---
    gdf = gpd.read_file(geojson_path)

    # --- Filter out empty or missing geometries ---
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()]

    # --- Convert CRS to WGS84 (lat/lon) for mapping ---
    gdf = gdf.to_crs(epsg=4326)

    # --- Ensure all geometries are Points (use centroids for polygons/lines) ---
    gdf["geometry"] = gdf.geometry.apply(lambda geom: geom.centroid if geom.geom_type != "Point" else geom)

    # --- Optional: add custom columns here ---
    # Example: categorize by YEAR field if exists
    # if "YEAR" in gdf.columns:
    #     gdf["Decade"] = gdf["YEAR"].apply(year_to_decade)

    return gdf
