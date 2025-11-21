import os
import geopandas as gpd

# --- Paths ---
wildfire_file = "data/BLM_Fire_Poly/BLM_OR_Fire_Poly_Hub.shp"
state_file = "data/US_State_Boundaries/US_State_Boundaries.shp"
output_file = "data/wildfire_polygons_clean.geojson"

wildfire_path = os.path.join(wildfire_file)
state_path = os.path.join(state_file)

# --- Load data ---
gdf = gpd.read_file(wildfire_path)
states = gpd.read_file(state_path)

# --- Clip to Oregon ---
oregon = states[states["NAME"] == "Oregon"]
gdf = gpd.clip(gdf, oregon)

# --- Optional: Filter polygons by size (e.g., >10 acres) ---
# if 'GIS_ACRES' in gdf.columns:
#     gdf = gdf[gdf['GIS_ACRES'] > 10]

# --- Reproject to WGS84 for web map ---
gdf = gdf.to_crs(epsg=4326)

# --- Remove invalid geometries ---
gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]

# --- Save cleaned GeoJSON ---
gdf.to_file(output_file, driver="GeoJSON")
print(f"Saved preprocessed polygons to {output_file}")
