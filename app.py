import dash
from dash import dcc, html
import plotly.graph_objects as go
import importlib
import os
import warnings
import pandas as pd

# Ignore harmless rasterio warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings('ignore', 'GeoSeries.notna', UserWarning)

# ------------------------------------
# Load all layers automatically from layers/
# Each layer file must define a `load_layer()` function returning a GeoDataFrame
# ------------------------------------
layer_modules = []
gdfs = []

for file in os.listdir("layers"):
    if file.endswith(".py") and file != "__init__.py":
        module_name = file[:-3]
        module = importlib.import_module(f"layers.{module_name}")
        gdf = module.load_layer()
        # Filter out empty or missing geometries
        gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()]
        layer_modules.append(module_name)
        gdfs.append(gdf)

# ------------------------------------
# Build the interactive map
# ------------------------------------
fig = go.Figure()

for gdf in gdfs:
    fig.add_trace(
        go.Scattermap(
            lat=gdf.geometry.y,
            lon=gdf.geometry.x,
            mode="markers",
            marker=dict(size=6),
            visible=False
        )
    )

# Oregon bounding box (default)
oregon_bounds = {"west": -124.7, "east": -116.5, "south": 41.9, "north": 46.3}

# Compute bounds from layers if any exist
if gdfs:
    all_lats = pd.concat([gdf.geometry.y for gdf in gdfs])
    all_lons = pd.concat([gdf.geometry.x for gdf in gdfs])
    bounds = {
        "west": all_lons.min(),
        "east": all_lons.max(),
        "south": all_lats.min(),
        "north": all_lats.max()
    }
else:
    bounds = oregon_bounds

# Map layout focusing on Oregon
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_center={"lat": 44.0, "lon": -120.5},  # Oregon center
    mapbox_zoom=6.5,  # Close-in zoom
    mapbox=dict(bounds=bounds),
    margin=dict(l=0, r=0, t=0, b=0)
)

# ------------------------------------
# Dash App Layout
# ------------------------------------
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Oregon Multi-Layer Map"),

    # Checklist for stacking layers
    dcc.Checklist(
        id="layer_select",
        options=[{"label": name, "value": i} for i, name in enumerate(layer_modules)],
        value=[],  # start with no layers
        labelStyle={'display': 'block'}
    ),

    dcc.Graph(id="map", figure=fig)
])

# ------------------------------------
# Callback to toggle layers
# ------------------------------------
@app.callback(
    dash.Output("map", "figure"),
    dash.Input("layer_select", "value")
)
def update_map(selected_layers):
    # hide all layers first
    for trace in fig.data:
        trace.visible = False

    # show selected layers
    for i in selected_layers:
        fig.data[i].visible = True

    return fig

# ------------------------------------
# Run the app
# ------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
