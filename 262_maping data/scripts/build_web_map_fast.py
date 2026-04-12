"""
build_web_map_fast.py

FAST local webpage map:
- Samples huge point layers (browser-safe)
- Simplifies polygon layers (browser-safe)
- Adds REQ-36: Grid vegetation density choropleth (computed from NLCD raster)
- Adds optional raster XYZ tile toggles for:
    - slope
    - clay
    - bulk density
    - ksat
    - risk map

Run:
    python scripts/build_web_map_fast.py

Serve:
    python -m http.server 8000 --directory outputs/web
Open:
    http://localhost:8000
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask


# =========================
# CONFIG (edit these paths)
# =========================

# Point layers
WILDFIRE_POINTS = r"Data/Events/wildfire_points_2000_2022.geojson"
LANDSLIDE_POINTS = r"Data/Events/landslide_points.geojson"

# Grid polygons (vector)
GRID_GPKG = r"Data/Base/grid_fire_slide_counts_2992.gpkg"
GRID_LAYER_NAME = None

# Soil polygons (vector outline only)
SOIL_GPKG = r"Data/Derived/soil_muaggatt.gpkg"
SOIL_LAYER_NAME = None

# NLCD raster (categorical)
NLCD_RASTER = r"Data/Vegetation/nlcd_2016_2992.tif"

# Optional raster sources
SLOPE_RASTER = r"Data/Raster/slope_2992.tif"
CLAY_RASTER = r"Data/Derived/clay_0_100cm_2992.tif"
BULK_RASTER = r"Data/Derived/bulk_density_0_100cm_2992.tif"
KSAT_RASTER = r"Data/Derived/ksat_0_100cm_2992.tif"
RISK_RASTER = r"Data/Derived/risk_map.tif"

# Output web folder
OUT_DIR = Path("outputs/web")
DATA_DIR = OUT_DIR / "data"
TILES_DIR = OUT_DIR / "tiles"

# Performance knobs
MAX_POINTS_PER_LAYER = 150_000
MAX_POLYGONS_PER_LAYER = 60_000
MAX_GRID_CELLS = 100_000
POLY_SIMPLIFY_TOL_DEG = 0.0008

# Web map expects lat/lon GeoJSON
WEB_GEOJSON_CRS = "EPSG:4326"

# REQ-36 vegetation density settings
VEG_CODES = {41, 42, 43, 52, 71}
NLCD_DOWNSAMPLE = 8

# Raster tiling settings (only if GDAL CLI tools work)
BUILD_SLOPE_TILES = False
BUILD_CLAY_TILES = False
BUILD_BULK_TILES = False
BUILD_KSAT_TILES = False
BUILD_RISK_TILES = False

TILE_ZOOM_MIN = 5
TILE_ZOOM_MAX = 10

# If you already generated tiles in QGIS, leave BUILD_* False
USE_EXISTING_SLOPE_TILES = True
USE_EXISTING_CLAY_TILES = True
USE_EXISTING_BULK_TILES = True
USE_EXISTING_KSAT_TILES = True
USE_EXISTING_RISK_TILES = True


# =========================
# Helpers
# =========================
def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def load_vector_any(path: str, layer: str | None = None) -> gpd.GeoDataFrame:
    if layer:
        return gpd.read_file(path, layer=layer)
    return gpd.read_file(path)


def write_geojson(gdf: gpd.GeoDataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_path, driver="GeoJSON")
    print(f"Wrote: {out_path}")


def write_empty_geojson(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")
    print(f"Wrote empty: {out_path}")


def load_and_sample_points(path: str, max_points: int) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()

    if gdf.crs is None:
        print(f"WARNING: {path} has no CRS. Assuming EPSG:4326. Fix if wrong.")
        gdf.set_crs("EPSG:4326", inplace=True)

    if len(gdf) > max_points:
        gdf = gdf.sample(n=max_points, random_state=42)
        print(f"Sampled points: {path} -> {len(gdf)}")
    else:
        print(f"Loaded points: {path} -> {len(gdf)} (no sampling)")

    gdf = gdf.to_crs(WEB_GEOJSON_CRS)

    keep_cols = ["geometry"]
    for col in ["date", "year", "name", "fire_name", "acres", "id"]:
        if col in gdf.columns:
            keep_cols.append(col)

    return gdf[keep_cols].copy()


def load_and_simplify_polygons(path: str, layer: str | None, max_polys: int) -> gpd.GeoDataFrame:
    gdf = load_vector_any(path, layer)
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()

    if gdf.crs is None:
        raise ValueError(f"{path} has no CRS. Fix in QGIS and re-export.")

    if len(gdf) > max_polys:
        gdf = gdf.sample(n=max_polys, random_state=42)
        print(f"Sampled polygons: {path} -> {len(gdf)}")
    else:
        print(f"Loaded polygons: {path} -> {len(gdf)}")

    gdf = gdf.to_crs(WEB_GEOJSON_CRS)
    gdf["geometry"] = gdf.geometry.simplify(POLY_SIMPLIFY_TOL_DEG, preserve_topology=True)

    keep_cols = ["geometry"]
    for col in ["grid_id", "count", "slide_count", "fire_count", "elev", "mukey", "musym", "muname"]:
        if col in gdf.columns:
            keep_cols.append(col)

    return gdf[keep_cols].copy()


def try_run(cmd: list[str]) -> None:
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)


def build_xyz_tiles(input_raster: str, out_tiles_dir: Path, name: str) -> None:
    """
    Uses gdalwarp -> EPSG:3857 then gdal2tiles.py to create XYZ tiles.
    Requires GDAL CLI tools in PATH.
    """
    ensure_dir(out_tiles_dir)
    tmp_3857 = out_tiles_dir / f"_{name}_3857.tif"

    try_run([
        "gdalwarp",
        "-t_srs", "EPSG:3857",
        "-r", "bilinear",
        "-of", "GTiff",
        input_raster,
        str(tmp_3857)
    ])

    layer_tiles = out_tiles_dir / name
    ensure_dir(layer_tiles)

    try_run([
        "gdal2tiles.py",
        "-z", f"{TILE_ZOOM_MIN}-{TILE_ZOOM_MAX}",
        "-w", "none",
        str(tmp_3857),
        str(layer_tiles)
    ])

    print(f"Tiles created: {layer_tiles}")


# =========================
# REQ-36: Grid vegetation density
# =========================
def _open_nlcd_downsampled(nlcd_path: str, factor: int):
    with rasterio.open(nlcd_path) as src:
        out_h = max(1, src.height // factor)
        out_w = max(1, src.width // factor)

        arr = src.read(
            1,
            out_shape=(out_h, out_w),
            resampling=Resampling.nearest
        ).astype("int32")

        scale_x = src.width / out_w
        scale_y = src.height / out_h
        transform = src.transform * src.transform.scale(scale_x, scale_y)

        nodata = src.nodata
        crs = src.crs

    if nodata is not None:
        arr[arr == nodata] = -9999

    return arr, transform, nodata, crs


def compute_grid_veg_density(
    grid_gdf: gpd.GeoDataFrame,
    nlcd_path: str,
    veg_codes: set[int],
    downsample: int,
) -> gpd.GeoDataFrame:
    nlcd, nlcd_transform, _, nlcd_crs = _open_nlcd_downsampled(nlcd_path, downsample)

    if grid_gdf.crs is None:
        raise ValueError("Grid has no CRS. Assign EPSG:2992 in QGIS or in code.")
    if str(grid_gdf.crs) != str(nlcd_crs):
        grid_gdf = grid_gdf.to_crs(nlcd_crs)

    veg_codes_arr = np.array(sorted(list(veg_codes)), dtype=np.int32)

    densities = []
    total = len(grid_gdf)

    for i, geom in enumerate(grid_gdf.geometry):
        if geom is None or geom.is_empty:
            densities.append(np.nan)
            continue

        inside = ~geometry_mask([geom], transform=nlcd_transform, invert=False, out_shape=nlcd.shape)

        vals = nlcd[inside]
        vals = vals[vals != -9999]

        if vals.size == 0:
            densities.append(np.nan)
        else:
            densities.append(float(np.isin(vals, veg_codes_arr).mean()))

        if (i + 1) % 250 == 0:
            print(f"  veg density computed: {i+1}/{total}")

    out = grid_gdf.copy()
    out["veg_density"] = densities
    out["veg_pct"] = (out["veg_density"] * 100.0).round(2)
    return out


def load_grid_veg_density_web() -> gpd.GeoDataFrame:
    grid = load_vector_any(GRID_GPKG, GRID_LAYER_NAME)
    grid = grid[grid.geometry.notna() & ~grid.geometry.is_empty].copy()

    if grid.crs is None:
        raise ValueError(f"{GRID_GPKG} has no CRS. Fix in QGIS (EPSG:2992).")

    if len(grid) > MAX_GRID_CELLS:
        grid = grid.sample(n=MAX_GRID_CELLS, random_state=42)
        print(f"Sampled grid cells -> {len(grid)}")
    else:
        print(f"Loaded grid cells -> {len(grid)}")

    print("Computing vegetation density from NLCD...")
    grid_with = compute_grid_veg_density(grid, NLCD_RASTER, VEG_CODES, NLCD_DOWNSAMPLE)

    grid_web = grid_with.to_crs(WEB_GEOJSON_CRS)
    grid_web["geometry"] = grid_web.geometry.simplify(POLY_SIMPLIFY_TOL_DEG, preserve_topology=True)

    keep_cols = ["geometry", "veg_density", "veg_pct"]
    for col in ["grid_id", "id", "cell_id"]:
        if col in grid_web.columns:
            keep_cols.insert(1, col)
            break

    for col in ["fire_count", "slide_count", "count", "elev"]:
        if col in grid_web.columns and col not in keep_cols:
            keep_cols.append(col)

    return grid_web[keep_cols].copy()


# =========================
# HTML
# =========================
def write_index_html(
    out_path: Path,
    has_slope_tiles: bool,
    has_clay_tiles: bool,
    has_bulk_tiles: bool,
    has_ksat_tiles: bool,
    has_risk_tiles: bool,
) -> None:
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Oregon Multi-Layer Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    crossorigin=""
  />
  <script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    crossorigin=""
  ></script>

  <style>
    html, body {{ height: 100%; margin: 0; }}
    #map {{ height: 100%; width: 100%; }}
    .legend {{
      background: white;
      padding: 10px 12px;
      border-radius: 8px;
      box-shadow: 0 1px 8px rgba(0,0,0,0.25);
      font-family: sans-serif;
      font-size: 13px;
      line-height: 1.35;
      max-width: 360px;
    }}
    .swatch {{
      display: inline-block;
      width: 14px;
      height: 10px;
      margin-right: 6px;
      border: 1px solid rgba(0,0,0,0.25);
      vertical-align: middle;
    }}
    .legend-gradient {{
      width: 180px;
      height: 12px;
      border: 1px solid rgba(0,0,0,0.35);
      margin: 4px 0;
    }}
    .legend-small {{
      font-size: 11px;
      color: #444;
    }}
  </style>
</head>
<body>
<div id="map"></div>

<script>
  const map = L.map('map', {{
    center: [44.0, -120.5],
    zoom: 6
  }});

  const osm = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }}).addTo(map);

  // Groups
  const wildfireLayer = L.layerGroup();
  const landslideLayer = L.layerGroup();
  const gridOutlineLayer = L.layerGroup();
  const soilOutlineLayer = L.layerGroup();
  const vegGridLayer = L.layerGroup();

  // Optional raster tile layers
  const slopeTiles = {("L.tileLayer('tiles/slope/{z}/{x}/{y}.png', {maxZoom: 18, opacity: 0.65})" if has_slope_tiles else "null")};
  const clayTiles  = {("L.tileLayer('tiles/clay/{z}/{x}/{y}.png',  {maxZoom: 18, opacity: 0.65})" if has_clay_tiles else "null")};
  const bulkTiles  = {("L.tileLayer('tiles/bulk/{z}/{x}/{y}.png',  {maxZoom: 18, opacity: 0.65})" if has_bulk_tiles else "null")};
  const ksatTiles  = {("L.tileLayer('tiles/ksat/{z}/{x}/{y}.png',  {maxZoom: 18, opacity: 0.65})" if has_ksat_tiles else "null")};
  const riskTiles  = {("L.tileLayer('tiles/risk/{z}/{x}/{y}.png',  {maxZoom: 18, opacity: 0.60})" if has_risk_tiles else "null")};

  function addGeoJsonPoints(url, targetLayer, style) {{
    fetch(url)
      .then(r => r.json())
      .then(geo => {{
        const gj = L.geoJSON(geo, {{
          pointToLayer: (feature, latlng) => L.circleMarker(latlng, style)
        }});
        gj.addTo(targetLayer);
      }})
      .catch(err => console.error("Failed loading", url, err));
  }}

  function addGeoJsonOutlines(url, targetLayer, style) {{
    fetch(url)
      .then(r => r.json())
      .then(geo => {{
        const gj = L.geoJSON(geo, {{
          style: style
        }});
        gj.addTo(targetLayer);
      }})
      .catch(err => console.error("Failed loading", url, err));
  }}

  function vegColor(d) {{
    if (d == null || isNaN(d)) return '#00000000';
    if (d < 0.20) return '#f7fcf5';
    if (d < 0.40) return '#c7e9c0';
    if (d < 0.60) return '#74c476';
    if (d < 0.80) return '#238b45';
    return '#005a32';
  }}

  function addVegChoropleth(url) {{
    fetch(url)
      .then(r => r.json())
      .then(geo => {{
        const gj = L.geoJSON(geo, {{
          style: (feature) => {{
            const d = feature.properties.veg_density;
            return {{
              color: '#111827',
              weight: 0.6,
              fillColor: vegColor(d),
              fillOpacity: 0.55
            }};
          }},
          onEachFeature: (feature, layer) => {{
            const p = feature.properties || {{}};
            const pct = (p.veg_pct != null)
              ? p.veg_pct
              : (p.veg_density != null ? (p.veg_density * 100).toFixed(2) : 'n/a');
            const fire = (p.fire_count != null) ? p.fire_count : 'n/a';
            const slide = (p.slide_count != null) ? p.slide_count : 'n/a';
            layer.bindPopup(
              `<b>Grid cell</b><br/>
               Vegetation: <b>${{pct}}%</b><br/>
               Fire count: ${{fire}}<br/>
               Slide count: ${{slide}}`
            );
          }}
        }});
        gj.addTo(vegGridLayer);
      }})
      .catch(err => console.error("Failed loading", url, err));
  }}

  // Dynamic legend definitions
  const legendDefinitions = {{
    veg: `
      <b>Vegetation density</b><br/>
      <span class="swatch" style="background:#f7fcf5"></span> 0–20%<br/>
      <span class="swatch" style="background:#c7e9c0"></span> 20–40%<br/>
      <span class="swatch" style="background:#74c476"></span> 40–60%<br/>
      <span class="swatch" style="background:#238b45"></span> 60–80%<br/>
      <span class="swatch" style="background:#005a32"></span> 80–100%
    `,
    risk: `
      <b>Risk Map (relative index)</b><br/>
      <div class="legend-gradient" style="background:linear-gradient(to right, #fff5f0, #fb6a4a, #67000d);"></div>
      <span class="legend-small">Lower susceptibility &nbsp;&nbsp; Higher susceptibility</span>
    `,
    slope: `
      <b>Slope</b><br/>
      <div class="legend-gradient" style="background:linear-gradient(to right, #ffffcc, #fd8d3c, #800026);"></div>
      <span class="legend-small">Low slope &nbsp;&nbsp; Steep slope</span>
    `,
    clay: `
      <b>Clay %</b><br/>
      <div class="legend-gradient" style="background:linear-gradient(to right, #ffffcc, #c2a83e, #8c510a);"></div>
      <span class="legend-small">Low clay &nbsp;&nbsp; High clay</span>
    `,
    bulk: `
      <b>Bulk density</b><br/>
      <div class="legend-gradient" style="background:linear-gradient(to right, #edf8fb, #66c2a4, #238b45);"></div>
      <span class="legend-small">Low bulk &nbsp;&nbsp; High bulk</span>
    `,
    ksat: `
      <b>Ksat</b><br/>
      <div class="legend-gradient" style="background:linear-gradient(to right, #f7fcfd, #67a9cf, #023858);"></div>
      <span class="legend-small">Low drainage &nbsp;&nbsp; High drainage</span>
    `
  }};

  const activeLegends = new Set();

  const legend = L.control({{position: 'bottomleft'}});
  legend.onAdd = function(map) {{
    const div = L.DomUtil.create('div', 'legend');
    div.id = 'dynamic-legend';
    div.innerHTML = '<b>Legend</b><br/><small>Turn on a layer to see its value bar.</small>';
    return div;
  }};
  legend.addTo(map);

  function updateLegend() {{
    const div = document.getElementById('dynamic-legend');
    if (!div) return;

    let html = '<b>Legend</b><br/>';

    if (activeLegends.size === 0) {{
      html += '<small>Turn on a layer to see its value bar.</small>';
    }} else {{
      activeLegends.forEach(key => {{
        if (legendDefinitions[key]) {{
          html += legendDefinitions[key] + '<br/>';
        }}
      }});
    }}

    div.innerHTML = html;
  }}

  // Load layers
  addGeoJsonPoints('data/wildfires_sample.geojson', wildfireLayer, {{
    radius: 2,
    color: '#e74c3c',
    weight: 1,
    fillOpacity: 0.7
  }});

  addGeoJsonPoints('data/landslides_sample.geojson', landslideLayer, {{
    radius: 2,
    color: '#3b82f6',
    weight: 1,
    fillOpacity: 0.7
  }});

  addGeoJsonOutlines('data/grid_outline.geojson', gridOutlineLayer, {{
    color: '#111827',
    weight: 1,
    fillOpacity: 0.0
  }});

  addGeoJsonOutlines('data/soil_outline.geojson', soilOutlineLayer, {{
    color: '#16a34a',
    weight: 1,
    fillOpacity: 0.0
  }});

  addVegChoropleth('data/grid_veg_density.geojson');

  // Layer control
  const overlays = {{
    "Wildfires (sampled points)": wildfireLayer,
    "Landslides (sampled points)": landslideLayer,
    "Grid (outline only)": gridOutlineLayer,
    "Soil polygons (outline only)": soilOutlineLayer,
    "Vegetation density (grid choropleth)": vegGridLayer
  }};

  if (slopeTiles) overlays["Slope (tiles)"] = slopeTiles;
  if (clayTiles)  overlays["Clay % (tiles)"] = clayTiles;
  if (bulkTiles)  overlays["Bulk density (tiles)"] = bulkTiles;
  if (ksatTiles)  overlays["Ksat (tiles)"] = ksatTiles;
  if (riskTiles)  overlays["Risk Map"] = riskTiles;

  L.control.layers({{"OpenStreetMap": osm}}, overlays, {{collapsed: false}}).addTo(map);

  // Map active layers to legends
  const layerLegendMap = new Map();
  layerLegendMap.set(vegGridLayer, 'veg');
  if (slopeTiles) layerLegendMap.set(slopeTiles, 'slope');
  if (clayTiles) layerLegendMap.set(clayTiles, 'clay');
  if (bulkTiles) layerLegendMap.set(bulkTiles, 'bulk');
  if (ksatTiles) layerLegendMap.set(ksatTiles, 'ksat');
  if (riskTiles) layerLegendMap.set(riskTiles, 'risk');

  map.on('overlayadd', function(e) {{
    const key = layerLegendMap.get(e.layer);
    if (key) {{
      activeLegends.add(key);
      updateLegend();
    }}
  }});

  map.on('overlayremove', function(e) {{
    const key = layerLegendMap.get(e.layer);
    if (key) {{
      activeLegends.delete(key);
      updateLegend();
    }}
  }});

  // Start visible layers
  wildfireLayer.addTo(map);
  landslideLayer.addTo(map);
  vegGridLayer.addTo(map);

  // Start legend for visible layer(s)
  activeLegends.add('veg');
  updateLegend();
</script>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote: {out_path}")


def main() -> None:
    ensure_dir(OUT_DIR)
    ensure_dir(DATA_DIR)
    ensure_dir(TILES_DIR)

    # 1) Points
    wf = load_and_sample_points(WILDFIRE_POINTS, MAX_POINTS_PER_LAYER)
    ls = load_and_sample_points(LANDSLIDE_POINTS, MAX_POINTS_PER_LAYER)
    write_geojson(wf, DATA_DIR / "wildfires_sample.geojson")
    write_geojson(ls, DATA_DIR / "landslides_sample.geojson")

    # 2) Grid outline
    if os.path.exists(GRID_GPKG):
        grid_outline = load_and_simplify_polygons(GRID_GPKG, GRID_LAYER_NAME, MAX_POLYGONS_PER_LAYER)
        write_geojson(grid_outline, DATA_DIR / "grid_outline.geojson")
    else:
        print("Grid not found:", GRID_GPKG)
        write_empty_geojson(DATA_DIR / "grid_outline.geojson")

    # 3) Soil outline
    if os.path.exists(SOIL_GPKG):
        soil_outline = load_and_simplify_polygons(SOIL_GPKG, SOIL_LAYER_NAME, MAX_POLYGONS_PER_LAYER)
        write_geojson(soil_outline, DATA_DIR / "soil_outline.geojson")
    else:
        print("Soil not found:", SOIL_GPKG)
        write_empty_geojson(DATA_DIR / "soil_outline.geojson")

    # 4) Veg density choropleth
    if os.path.exists(GRID_GPKG) and os.path.exists(NLCD_RASTER):
        veg_grid = load_grid_veg_density_web()
        write_geojson(veg_grid, DATA_DIR / "grid_veg_density.geojson")
    else:
        print("Missing GRID or NLCD for veg density.")
        write_empty_geojson(DATA_DIR / "grid_veg_density.geojson")

    # 5) Optional tiles
    has_slope_tiles = False
    has_clay_tiles = False
    has_bulk_tiles = False
    has_ksat_tiles = False
    has_risk_tiles = False

    if BUILD_SLOPE_TILES and os.path.exists(SLOPE_RASTER):
        build_xyz_tiles(SLOPE_RASTER, TILES_DIR, "slope")
        has_slope_tiles = True

    if BUILD_CLAY_TILES and os.path.exists(CLAY_RASTER):
        build_xyz_tiles(CLAY_RASTER, TILES_DIR, "clay")
        has_clay_tiles = True

    if BUILD_BULK_TILES and os.path.exists(BULK_RASTER):
        build_xyz_tiles(BULK_RASTER, TILES_DIR, "bulk")
        has_bulk_tiles = True

    if BUILD_KSAT_TILES and os.path.exists(KSAT_RASTER):
        build_xyz_tiles(KSAT_RASTER, TILES_DIR, "ksat")
        has_ksat_tiles = True

    if BUILD_RISK_TILES and os.path.exists(RISK_RASTER):
        build_xyz_tiles(RISK_RASTER, TILES_DIR, "risk")
        has_risk_tiles = True

    if USE_EXISTING_SLOPE_TILES and (TILES_DIR / "slope").exists():
        has_slope_tiles = True

    if USE_EXISTING_CLAY_TILES and (TILES_DIR / "clay").exists():
        has_clay_tiles = True

    if USE_EXISTING_BULK_TILES and (TILES_DIR / "bulk").exists():
        has_bulk_tiles = True

    if USE_EXISTING_KSAT_TILES and (TILES_DIR / "ksat").exists():
        has_ksat_tiles = True

    if USE_EXISTING_RISK_TILES and (TILES_DIR / "risk").exists():
        has_risk_tiles = True

    # 6) Webpage
    write_index_html(
        OUT_DIR / "index.html",
        has_slope_tiles,
        has_clay_tiles,
        has_bulk_tiles,
        has_ksat_tiles,
        has_risk_tiles,
    )

    print("\nDONE.")
    print("Serve locally with:")
    print("  python -m http.server 8000 --directory outputs/web")
    print("Open:")
    print("  http://localhost:8000")


if __name__ == "__main__":
    main()