"""
read gNATSGO geodatabase and list layers
"""
import fiona 

GDB_PATH = "../data/gNATSGO_OR.gdb"
txt_file = "gNATSGO_info.txt"
layers = fiona.listlayers(GDB_PATH)
with open(txt_file, "w", encoding="utf-8") as f:
    for layer in layers:
        f.write(layer + "\n")

# read a layer: replace "" with a valid layer name from the printed list
#gdf = gpd.read_file(gdb_path, layer="chorizon")
#print(gdf.head())
