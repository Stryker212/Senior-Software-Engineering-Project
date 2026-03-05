from pathlib import Path
import numpy as np
import rasterio

IN_DIR = Path("Data/Derived")
OUT_DIR = Path("Data/Derived")

RAS = {
    "clay": "clay_0_100cm_2992.tif",
    "ksat": "ksat_0_100cm_2992.tif",
    "bulk_density": "bulk_density_0_100cm_2992.tif",
}

P_LOW = 2
P_HIGH = 98

def read_band(path: Path):
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float32")
        prof = src.profile
        nodata = src.nodata
    # treat zeros as nodata if your rasters use 0 as "no data"
    # comment this out if 0 is valid for your layer
    arr[arr == 0] = np.nan
    if nodata is not None:
        arr[arr == nodata] = np.nan
    return arr, prof

def norm_percentile(arr: np.ndarray):
    valid = arr[~np.isnan(arr)]
    lo = np.percentile(valid, P_LOW)
    hi = np.percentile(valid, P_HIGH)
    clipped = np.clip(arr, lo, hi)
    out = (clipped - lo) / (hi - lo)
    return out.astype("float32"), float(lo), float(hi)

def write_raster(path: Path, prof, arr01: np.ndarray):
    out = arr01.copy()
    out[np.isnan(out)] = prof.get("nodata", -9999)
    prof2 = prof.copy()
    prof2.update(dtype="float32", count=1, nodata=prof2.get("nodata", -9999), compress="lzw")
    with rasterio.open(path, "w", **prof2) as dst:
        dst.write(out, 1)

def main():
    # normalize each
    results = {}
    for name, fn in RAS.items():
        arr, prof = read_band(IN_DIR / fn)
        arr01, lo, hi = norm_percentile(arr)
        out_path = OUT_DIR / f"{name}_0_100cm_norm01.tif"
        write_raster(out_path, prof, arr01)
        results[name] = (out_path, lo, hi)
        print(f"{name}: saved {out_path} using P{P_LOW}={lo:.4f}, P{P_HIGH}={hi:.4f}")

    # invert Ksat so higher value means "worse" (optional but recommended)
    ksat_path = results["ksat"][0]
    with rasterio.open(ksat_path) as src:
        k = src.read(1).astype("float32")
        prof = src.profile
    nod = prof.get("nodata", -9999)
    k[k == nod] = np.nan
    k_inv = 1.0 - k
    out_path = OUT_DIR / "ksat_0_100cm_norm01_inverted.tif"
    write_raster(out_path, prof, k_inv)
    print(f"ksat inverted: saved {out_path}")

if __name__ == "__main__":
    main()
