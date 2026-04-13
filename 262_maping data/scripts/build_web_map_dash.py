import geopandas as gpd
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

import pandas as pd
import numpy as np
import rasterio
from rasterio.warp import transform_bounds, transform
from rasterio.enums import Resampling


# ============================================================
# CONFIG (EDIT THIS)
# ============================================================

TARGET_CRS = "EPSG:4326"

# Event points (already working)
WILDFIRE_PATH = "Data/Events/wildfire_points_2000_2022.geojson"
LANDSLIDE_PATH = "Data/Events/landslide_points.geojson"

# Optional vector layers you want to toggle on/off
# Add more here (gpkg / geojson / shapefile)
VECTOR_LAYERS = [
    # Example:
    # {"name": "Soil polygons (muaggatt)", "path": "Data/Derived/soil_muaggatt.gpkg"},
]

# Optional raster layers you want to visualize (as sampled points)
# Add your rasters here:
RASTER_LAYERS = [
    {"name": "Slope", "path": "Data/Raster/slope_2992.tif", "sample_step": 10},
    {"name": "NLCD 2016", "path": "Data/Vegetation/nlcd_2016_2992.tif", "sample_step": 12},
    {"name": "Bulk density 0-100cm", "path": "Data/Soil/bulk_density_100cm_oregon.tif", "sample_step": 12},
    # Add more:
    # {"name": "Clay 0-100cm", "path": "Data/Derived/clay_0_100cm.tif", "sample_step": 12},
    # {"name": "Ksat 0-100cm", "path": "Data/Derived/ksat_0_100cm.tif", "sample_step": 12},
]

# Safety/perf guardrails
MAX_VECTOR_POINTS = 30000          # per layer (points only)
MAX_RASTER_POINTS = 60000          # per raster layer

# ============================================================
# Helpers
# ============================================================

def load_vector_layer(path: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path).to_crs(TARGET_CRS)
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
    return gdf

def vector_to_trace(gdf: gpd.GeoDataFrame, name: str) -> go.Scattermap:
    # Points only (fast + straightforward)
    # If you have polygons/lines, we can add support, but points are easiest.
    geom_type = gdf.geometry.geom_type.unique()
    if not all(t in ("Point", "MultiPoint") for t in geom_type):
        # For now: convert non-point to representative points (centroids)
        gdf = gdf.copy()
        gdf["geometry"] = gdf.geometry.representative_point()

    if len(gdf) > MAX_VECTOR_POINTS:
        gdf = gdf.sample(MAX_VECTOR_POINTS, random_state=42)

    return go.Scattermap(
        lat=gdf.geometry.y,
        lon=gdf.geometry.x,
        mode="markers",
        marker=dict(size=5),
        name=name,
    )

def sample_raster_to_points(path: str, sample_step: int) -> pd.DataFrame:
    """
    Returns a dataframe with columns: lat, lon, val
    - Reads raster in native CRS
    - Downsamples by sample_step
    - Transforms pixel centers to lon/lat (EPSG:4326)
    """
    with rasterio.open(path) as src:
        band = src.read(1, masked=True)

        # Downsample by slicing
        band_ds = band[::sample_step, ::sample_step]

        # Build row/col indices in the downsampled grid
        rows = np.arange(0, band.shape[0], sample_step)
        cols = np.arange(0, band.shape[1], sample_step)
        rr, cc = np.meshgrid(rows, cols, indexing="ij")

        # Convert row/col -> x/y in raster CRS
        xs, ys = rasterio.transform.xy(src.transform, rr, cc, offset="center")
        xs = np.array(xs).reshape(-1)
        ys = np.array(ys).reshape(-1)
        vals = band_ds.reshape(-1)

        # Mask nodata
        valid = ~vals.mask if np.ma.isMaskedArray(vals) else np.isfinite(vals)
        xs = xs[valid]
        ys = ys[valid]
        vals = np.array(vals[valid], dtype=np.float32)

        # Transform to lon/lat
        lons, lats = transform(src.crs, TARGET_CRS, xs.tolist(), ys.tolist())

        df = pd.DataFrame({"lon": lons, "lat": lats, "val": vals})

        # Hard cap for speed
        if len(df) > MAX_RASTER_POINTS:
            df = df.sample(MAX_RASTER_POINTS, random_state=42)

        return df

def raster_points_to_trace(df: pd.DataFrame, name: str) -> go.Scattermap:
    return go.Scattermap(
        lat=df["lat"],
        lon=df["lon"],
        mode="markers",
        marker=dict(
            size=4,
            color=df["val"],
            showscale=True,
        ),
        name=name,
    )

def compute_map_center(traces):
    # Try to center based on first visible trace with data
    for tr in traces:
        if hasattr(tr, "lat") and tr.lat is not None and len(tr.lat) > 0:
            return float(np.mean(tr.lat)), float(np.mean(tr.lon))
    return 44.0, -120.5


# ============================================================
# Load data ONCE at startup
# ============================================================

layers = []  # list of dicts: {name, type, trace}

# Wildfires + Landslides (points)
wild = load_vector_layer(WILDFIRE_PATH)
slide = load_vector_layer(LANDSLIDE_PATH)

layers.append({"name": "Wildfires", "trace": vector_to_trace(wild, "Wildfires")})
layers.append({"name": "Landslides", "trace": vector_to_trace(slide, "Landslides")})

# Extra vector layers
for item in VECTOR_LAYERS:
    gdf = load_vector_layer(item["path"])
    layers.append({"name": item["name"], "trace": vector_to_trace(gdf, item["name"])})

# Raster layers (sample -> points)
for item in RASTER_LAYERS:
    df = sample_raster_to_points(item["path"], sample_step=item.get("sample_step", 10))
    layers.append({"name": item["name"], "trace": raster_points_to_trace(df, item["name"])})


# ============================================================
# Dash app
# ============================================================

app = dash.Dash(__name__)

# initial figure: show just the two event layers
initial_visible = {"Wildfires", "Landslides"}

fig = go.Figure()
for lyr in layers:
    tr = lyr["trace"]
    tr.visible = (lyr["name"] in initial_visible)
    fig.add_trace(tr)

center_lat, center_lon = compute_map_center([l["trace"] for l in layers])

fig.update_layout(
    map_style="carto-positron",
    map_center={"lat": center_lat, "lon": center_lon},
    map_zoom=6.2,
    margin=dict(l=0, r=0, t=0, b=0),
    legend=dict(orientation="h"),
)

app.layout = html.Div(
    [
        html.H2("Oregon Multi-Layer Map (No Choropleth)"),
        dcc.Checklist(
            id="layer_select",
            options=[{"label": l["name"], "value": l["name"]} for l in layers],
            value=["Wildfires", "Landslides"],
            labelStyle={"display": "block"},
        ),
        dcc.Graph(id="map", figure=fig, style={"height": "85vh"}),
    ]
)

@app.callback(
    Output("map", "figure"),
    Input("layer_select", "value"),
)
def update_map(selected):
    selected = set(selected or [])
    out = go.Figure(fig)  # copy layout & traces

    for i, lyr in enumerate(layers):
        out.data[i].visible = (lyr["name"] in selected)

    return out


if __name__ == "__main__":
    app.run(debug=True)