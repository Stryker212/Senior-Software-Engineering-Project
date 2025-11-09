import geopandas as gpd
import fiona 

gdb_path = "../data/gNATSGO_OR.gdb"
layers = fiona.listlayers(gdb_path)
with open("gNATSGO_info.txt", "w") as f:
    for layer in layers:
        f.write(layer + "\n")

# read a layer: replace "" with a valid layer name from the printed list
#gdf = gpd.read_file(gdb_path, layer="chorizon")
#print(gdf.head())
