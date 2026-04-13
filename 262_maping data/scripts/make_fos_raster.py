import os
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.warp import reproject, Resampling


# -----------------------------
# Input files
# -----------------------------
SLOPE_PATH = r"Data/Raster/slope_2992.tif"
BULK_PATH = r"Data/Derived/bulk_density_0_100cm_2992.tif"
CLAY_PATH = r"Data/Derived/clay_0_100cm_2992.tif"

# Output files
OUT_FOS = r"outputs/fos_map.tif"
OUT_RISK = r"outputs/fos_risk_map.tif"

# -----------------------------
# Model constants
# -----------------------------
SOIL_DEPTH_M = 1.0
FRICTION_ANGLE_DEG = 30.0

# Placeholder cohesion estimate from clay %
# 0.1 kPa per % clay
COHESION_FACTOR_KPA_PER_PERCENT = 0.1

# Whether slope raster is already in degrees
SLOPE_IS_DEGREES = True

# Block size for chunked processing
BLOCK_SIZE = 1024

# Output nodata
FOS_NODATA = np.float32(-9999.0)
RISK_NODATA = np.uint8(0)


# -----------------------------
# Helpers
# -----------------------------
def classify_fos(fos: np.ndarray) -> np.ndarray:
    """
    Risk classes:
      3 = High risk (FoS < 1.0)
      2 = Moderate risk (1.0 <= FoS < 1.3)
      1 = Stable (FoS >= 1.3)
      0 = NoData / invalid
    """
    out = np.zeros(fos.shape, dtype=np.uint8)
    valid = np.isfinite(fos)

    out[valid & (fos < 1.0)] = 3
    out[valid & (fos >= 1.0) & (fos < 1.3)] = 2
    out[valid & (fos >= 1.3)] = 1
    return out


def print_raster_info(name: str, src: rasterio.io.DatasetReader) -> None:
    print(f"{name}:")
    print("  shape:", src.height, src.width)
    print("  crs:", src.crs)
    print("  transform:", src.transform)
    print("  res:", src.res)
    print("  nodata:", src.nodata)
    print()


def build_valid_mask(arr: np.ndarray, nodata_value) -> np.ndarray:
    valid = np.isfinite(arr)
    if nodata_value is not None:
        valid &= arr != nodata_value
    return valid


def main():
    os.makedirs("outputs", exist_ok=True)

    with rasterio.open(SLOPE_PATH) as slope_src, \
         rasterio.open(BULK_PATH) as bulk_src, \
         rasterio.open(CLAY_PATH) as clay_src:

        print_raster_info("SLOPE", slope_src)
        print_raster_info("BULK", bulk_src)
        print_raster_info("CLAY", clay_src)

        if not (slope_src.crs == bulk_src.crs == clay_src.crs):
            raise ValueError("Input rasters do not have matching CRS.")

        profile_fos = slope_src.profile.copy()
        profile_fos.update(
            dtype="float32",
            count=1,
            compress="lzw",
            nodata=FOS_NODATA
        )

        profile_risk = slope_src.profile.copy()
        profile_risk.update(
            dtype="uint8",
            count=1,
            compress="lzw",
            nodata=RISK_NODATA
        )

        friction_angle_rad = np.float32(np.radians(FRICTION_ANGLE_DEG))

        total_valid_cells = 0
        total_cells = 0

        with rasterio.open(OUT_FOS, "w", **profile_fos) as fos_dst, \
             rasterio.open(OUT_RISK, "w", **profile_risk) as risk_dst:

            for row_off in range(0, slope_src.height, BLOCK_SIZE):
                win_h = min(BLOCK_SIZE, slope_src.height - row_off)

                for col_off in range(0, slope_src.width, BLOCK_SIZE):
                    win_w = min(BLOCK_SIZE, slope_src.width - col_off)
                    window = Window(col_off, row_off, win_w, win_h)

                    # Read slope directly from reference raster
                    slope = slope_src.read(1, window=window).astype(np.float32)

                    # Destination arrays for reprojected/resampled coarse rasters
                    bulk = np.full((win_h, win_w), bulk_src.nodata if bulk_src.nodata is not None else np.nan, dtype=np.float32)
                    clay = np.full((win_h, win_w), clay_src.nodata if clay_src.nodata is not None else np.nan, dtype=np.float32)

                    # Window transform on the slope grid
                    dst_transform = slope_src.window_transform(window)

                    # Reproject/resample BULK to match current slope window
                    reproject(
                        source=rasterio.band(bulk_src, 1),
                        destination=bulk,
                        src_transform=bulk_src.transform,
                        src_crs=bulk_src.crs,
                        src_nodata=bulk_src.nodata,
                        dst_transform=dst_transform,
                        dst_crs=slope_src.crs,
                        dst_nodata=bulk_src.nodata,
                        resampling=Resampling.bilinear,
                    )

                    # Reproject/resample CLAY to match current slope window
                    reproject(
                        source=rasterio.band(clay_src, 1),
                        destination=clay,
                        src_transform=clay_src.transform,
                        src_crs=clay_src.crs,
                        src_nodata=clay_src.nodata,
                        dst_transform=dst_transform,
                        dst_crs=slope_src.crs,
                        dst_nodata=clay_src.nodata,
                        resampling=Resampling.bilinear,
                    )

                    # Build validity mask
                    valid = (
                        build_valid_mask(slope, slope_src.nodata) &
                        build_valid_mask(bulk, bulk_src.nodata) &
                        build_valid_mask(clay, clay_src.nodata)
                    )

                    valid &= (bulk > 0)
                    valid &= (clay >= 0)

                    fos = np.full((win_h, win_w), np.nan, dtype=np.float32)

                    if np.any(valid):
                        # Convert slope to radians
                        if SLOPE_IS_DEGREES:
                            theta = np.radians(slope).astype(np.float32)
                        else:
                            theta = np.arctan(slope / 100.0).astype(np.float32)

                        valid &= np.isfinite(theta)
                        valid &= (theta > 0.001)
                        valid &= (theta < np.pi / 2.0)

                        if np.any(valid):
                            # Approximate unit weight gamma (N/m^3) from bulk density (kg/m^3)
                            gamma = bulk * 9.81

                            # Convert cohesion from kPa to Pa
                            cohesion_pa = clay * COHESION_FACTOR_KPA_PER_PERCENT * 1000.0

                            cos_t = np.cos(theta)
                            sin_t = np.sin(theta)

                            numerator = cohesion_pa + (
                                gamma * SOIL_DEPTH_M * (cos_t ** 2)
                            ) * np.tan(friction_angle_rad)

                            denominator = gamma * SOIL_DEPTH_M * sin_t * cos_t

                            local_valid = (
                                valid &
                                np.isfinite(numerator) &
                                np.isfinite(denominator) &
                                (denominator != 0)
                            )

                            fos[local_valid] = numerator[local_valid] / denominator[local_valid]

                    fos_out = np.where(np.isfinite(fos), fos, FOS_NODATA).astype(np.float32)
                    risk_out = classify_fos(fos).astype(np.uint8)

                    fos_dst.write(fos_out, 1, window=window)
                    risk_dst.write(risk_out, 1, window=window)

                    total_valid_cells += np.count_nonzero(np.isfinite(fos))
                    total_cells += fos.size

                    print(
                        f"Processed window row={row_off}:{row_off+win_h}, "
                        f"col={col_off}:{col_off+win_w}"
                    )

    print("\nDone.")
    print(f"Wrote:\n  {OUT_FOS}\n  {OUT_RISK}")
    print(f"Valid FoS cells: {total_valid_cells:,}")
    print(f"Total cells processed: {total_cells:,}")


if __name__ == "__main__":
    main()