from pathlib import Path
import fiona

GDB = Path("Data/Soil/gNATSGO_OR.gdb")

def main():
    if not GDB.exists():
        raise FileNotFoundError(f"Missing: {GDB.resolve()}")

    layers = list(fiona.listlayers(str(GDB)))
    print(f"GDB: {GDB}")
    print(f"Layers: {len(layers)}\n")

    clay_hits = []
    for lyr in layers:
        try:
            with fiona.open(str(GDB), layer=lyr) as src:
                cols = list(src.schema.get("properties", {}).keys())
        except Exception:
            continue

        clay_cols = [c for c in cols if "clay" in c.lower()]
        if clay_cols:
            clay_hits.append((lyr, clay_cols))

    if not clay_hits:
        print("No 'clay' fields found in any layer.")
        print("Next step: we will compute clay from texture class tables instead (still valid).")
        return

    print("Found clay fields:\n")
    for lyr, cols in clay_hits:
        print(f"- {lyr}: {cols}")

if __name__ == "__main__":
    main()
