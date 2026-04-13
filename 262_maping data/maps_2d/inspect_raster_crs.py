from pathlib import Path
import rasterio

RASTERS = [
    Path("Data/Raster/oregon_dem_2992.tif"),
    Path("Data/Raster/slope_2992.tif"),
]

def main():
    for fp in RASTERS:
        print("\n---")
        print(f"File: {fp}")
        if not fp.exists():
            print("  NOT FOUND")
            continue

        with rasterio.open(fp) as src:
            print(f"  CRS: {src.crs}")
            print(f"  Pixel size: {src.transform.a:.2f} x {abs(src.transform.e):.2f}")
            print(f"  Nodata: {src.nodata}")
            print(f"  Bands: {src.count}")

if __name__ == "__main__":
    main()
