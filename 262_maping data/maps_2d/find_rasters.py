from __future__ import annotations

from pathlib import Path

RASTER_EXTS = {".tif", ".tiff", ".img"}

def main():
    root = Path(".").resolve()
    print(f"Searching under: {root}\n")

    hits = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in RASTER_EXTS:
            hits.append(p)

    if not hits:
        print("No .tif/.tiff/.img rasters found anywhere under this folder.")
        return

    print(f"Found {len(hits)} raster(s):\n")
    for p in sorted(hits):
        print(p)

if __name__ == "__main__":
    main()
