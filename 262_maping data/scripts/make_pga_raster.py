import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.crs import CRS


def csv_grid_to_array(df, value_col="PGA"):
    lats = np.sort(df["Latitude"].unique())
    lons = np.sort(df["Longitude"].unique())

    dx = float(np.round(lons[1] - lons[0], 5))
    dy = float(np.round(lats[1] - lats[0], 5))

    # north-up array: row 0 = max latitude
    lat_to_row = {lat: i for i, lat in enumerate(lats[::-1])}
    lon_to_col = {lon: j for j, lon in enumerate(lons)}

    arr = np.full((len(lats), len(lons)), np.nan, dtype="float32")
    for lat, lon, val in zip(df["Latitude"].values, df["Longitude"].values, df[value_col].values):
        arr[lat_to_row[lat], lon_to_col[lon]] = val

    west = lons.min() - dx / 2
    north = lats.max() + dy / 2
    transform = from_origin(west, north, dx, dy)

    return arr, transform


def main():
    # INPUTS (edit paths for your repo)
    uh_csv = "Data/Events/Seismic/uh_siteB.csv"
    p84_csv = "Data/Events/Seismic/pga84_siteB.csv"
    dll_csv = "Data/Events/Seismic/dll.csv"

    # OUTPUTS
    out_4326 = "Data/Derived/pga_m_oregon_siteB_4326.tif"
    out_5070 = "Data/Derived/pga_m_oregon_siteB_5070_1km.tif"

    uh = pd.read_csv(uh_csv)
    p84 = pd.read_csv(p84_csv)
    dll = pd.read_csv(dll_csv)

    dll_val = float(dll.loc[dll["Site Class"] == "B", "PGA"].iloc[0])

    df = uh.merge(p84, on=["Latitude", "Longitude"], suffixes=("_UH", "_84"))
    df["PGA_M"] = np.minimum(df["PGA_UH"], np.maximum(df["PGA_84"], dll_val))

    # Oregon bbox (quick clip; you can later mask using an Oregon boundary polygon)
    lat_min, lat_max = 41.8, 46.5
    lon_min, lon_max = -124.9, -116.3
    df_or = df[
        (df["Latitude"] >= lat_min) & (df["Latitude"] <= lat_max) &
        (df["Longitude"] >= lon_min) & (df["Longitude"] <= lon_max)
    ].copy()

    arr, transform = csv_grid_to_array(df_or, value_col="PGA_M")

    # Write EPSG:4326 raster
    profile = {
        "driver": "GTiff",
        "height": arr.shape[0],
        "width": arr.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": transform,
        "nodata": np.nan,
    }
    with rasterio.open(out_4326, "w", **profile) as dst:
        dst.write(arr, 1)

    # Reproject to EPSG:5070 (~1km)
    dst_crs = CRS.from_epsg(5070)
    with rasterio.open(out_4326) as src:
        transform2, width2, height2 = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds, resolution=1000
        )
        profile2 = src.profile.copy()
        profile2.update(
            crs=dst_crs,
            transform=transform2,
            width=width2,
            height=height2,
            nodata=-9999.0,
        )

        dest = np.empty((height2, width2), dtype="float32")
        reproject(
            source=rasterio.band(src, 1),
            destination=dest,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform2,
            dst_crs=dst_crs,
            resampling=Resampling.bilinear,
            src_nodata=np.nan,
            dst_nodata=-9999.0,
        )

        with rasterio.open(out_5070, "w", **profile2) as dst:
            dst.write(dest, 1)

    print("Wrote:", out_4326)
    print("Wrote:", out_5070)


if __name__ == "__main__":
    main()
