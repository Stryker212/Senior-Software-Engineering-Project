from __future__ import annotations

from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import Affine


# -----------------------------
# Inputs / Outputs
# -----------------------------
PGA_TIF = Path("Data/Derived/oregon_pgaM_siteB_epsg5070_1km.tif")
BULK_TIF = Path("Data/Derived/bulk_density_0_100cm.tif")  # or wherever yours lives

OUT_TIF = Path("Data/Derived/csr_z1m.tif")

# -----------------------------
# CSR parameters
# -----------------------------
Z_M = 1.0                 # depth (meters)
G = 9.81                  # m/s^2
GAMMA_W = 9810.0          # N/m^3 (unit weight of water)
CSR_COEFF = 0.65          # Seed & Idriss style coefficient

# Bulk density unit assumption:
# - If your bulk density raster is in g/cm^3 (common), use 1000.0 to convert to kg/m^3.
# - If it's already kg/m^3, set this to 1.0.
BULK_TO_KG_M3 = 1000.0


def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def read_as_float32(src, band: int = 1) -> np.ndarray:
    arr = src.read(band).astype(np.float32)
    nodata = src.nodata
    if nodata is not None:
        arr = np.where(arr == nodata, np.nan, arr)
    return arr


def warp_to_match(src_path: Path, match_profile: dict) -> np.ndarray:
    """
    Reproject+resample src_path to match:
      - CRS
      - transform
      - width/height
    Returns float32 array with np.nan for nodata.
    """
    with rasterio.open(src_path) as src:
        src_arr = read_as_float32(src)

        dst = np.full((match_profile["height"], match_profile["width"]), np.nan, dtype=np.float32)

        reproject(
            source=src_arr,
            destination=dst,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=match_profile["transform"],
            dst_crs=match_profile["crs"],
            resampling=Resampling.bilinear,
            src_nodata=np.nan,
            dst_nodata=np.nan,
        )
        return dst


def main():
    if not PGA_TIF.exists():
        raise FileNotFoundError(f"Missing PGA raster: {PGA_TIF}")
    if not BULK_TIF.exists():
        raise FileNotFoundError(f"Missing bulk density raster: {BULK_TIF}")

    ensure_parent(OUT_TIF)

    # Use PGA grid as the "master" grid
    with rasterio.open(PGA_TIF) as pga_src:
        pga = read_as_float32(pga_src)

        out_profile = pga_src.profile.copy()
        out_profile.update(
            dtype="float32",
            count=1,
            compress="deflate",
            predictor=3,
            nodata=-9999.0,
        )

        match_profile = {
            "crs": pga_src.crs,
            "transform": pga_src.transform,
            "width": pga_src.width,
            "height": pga_src.height,
        }

    # Load/warp bulk density onto PGA grid if needed
    with rasterio.open(BULK_TIF) as bulk_src:
        same_grid = (
            bulk_src.crs == match_profile["crs"]
            and bulk_src.transform == match_profile["transform"]
            and bulk_src.width == match_profile["width"]
            and bulk_src.height == match_profile["height"]
        )

    if same_grid:
        with rasterio.open(BULK_TIF) as bulk_src:
            bulk = read_as_float32(bulk_src)
    else:
        print("Bulk density raster grid does not match PGA grid — warping to match PGA...")
        bulk = warp_to_match(BULK_TIF, match_profile)

    # -----------------------------
    # Compute CSR at z = 1 m
    # -----------------------------
    # Convert bulk density to kg/m^3
    rho = bulk * BULK_TO_KG_M3  # kg/m^3

    # Unit weight gamma (N/m^3)
    gamma = rho * G

    # Total vertical stress (Pa) at z
    sigma_v = gamma * Z_M

    # Effective vertical stress (Pa) at z (simple saturated assumption)
    sigma_v_eff = (gamma - GAMMA_W) * Z_M

    # Avoid divide-by-zero / negative effective stress
    # If gamma <= gamma_w then sigma'_v <= 0 (water or unrealistic bulk density) -> mask out
    safe = np.isfinite(pga) & np.isfinite(bulk) & (sigma_v_eff > 0)

    csr = np.full_like(pga, np.nan, dtype=np.float32)
    csr[safe] = CSR_COEFF * pga[safe] * (sigma_v[safe] / sigma_v_eff[safe])

    # Write output (convert nan -> nodata)
    out = np.where(np.isfinite(csr), csr, out_profile["nodata"]).astype(np.float32)

    with rasterio.open(OUT_TIF, "w", **out_profile) as dst:
        dst.write(out, 1)

    print(f"Saved: {OUT_TIF}")
    print("Notes:")
    print(" - CSR computed at z=1.0m assuming saturated soil (sigma' = (gamma - gamma_w)*z).")
    print(" - If your bulk density units are NOT g/cm^3, set BULK_TO_KG_M3 accordingly.")


if __name__ == "__main__":
    main()
