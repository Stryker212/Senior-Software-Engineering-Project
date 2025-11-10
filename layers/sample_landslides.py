import geopandas as gpd
import rasterio

def load_layer():
    # --- Load Landslide Data ---
    gdb_path = r"C:\Users\umnak\Downloads\SLIDO_Release_4p5_wMetadata.gdb\SLIDO_Release_4p5_wMetadata.gdb"
    gdf = gpd.read_file(gdb_path, layer="Historic_Landslide_Points")
    gdf = gdf.dropna(subset=["geometry", "YEAR"])

    # Convert CRS for stacking on same map
    gdf = gdf.to_crs(epsg=4326)

    # --- Add decade ---
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

    # --- Elevation ---
    dem = rasterio.open(r"C:\Users\umnak\Downloads\OR_DEM_10M.gdb\OR_DEM_10M.gdb")
    coords = [(x, y) for x, y in zip(gdf.geometry.x, gdf.geometry.y)]
    gdf["Elevation"] = [v[0] for v in dem.sample(coords)]

    return gdf
