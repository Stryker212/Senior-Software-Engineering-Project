import dash
from dash import dcc, html
import plotly.graph_objects as go
import importlib
import os
import warnings
import pandas as pd

# Ignore harmless warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings('ignore', 'GeoSeries.notna', UserWarning)

# ------------------------------------
# Load all layers automatically from layers/
# Each layer file must define a `load_layer()` function returning a GeoDataFrame
# ------------------------------------
layer_modules = []
gdfs = []

# Example metadata for each layer
layer_info = {
    "sample_wildfires": {"name": "Wildfire Occurrences", "description": "Points where wildfires occurred in Oregon."},
    "sample_landslides": {"name": "Landslides", "description": "Recorded landslides in Oregon."},
    # Add more layers with metadata here
}

for file in os.listdir("layers"):
    if file.endswith(".py") and file != "__init__.py":
        module_name = file[:-3]
        module = importlib.import_module(f"layers.{module_name}")
        gdf = module.load_layer()
        gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()]
        layer_modules.append(module_name)
        gdfs.append(gdf)

# ------------------------------------
# Build the interactive map
# ------------------------------------
fig = go.Figure()

for i, gdf in enumerate(gdfs):
    info = layer_info.get(layer_modules[i], {})
    fig.add_trace(
        go.Scattermapbox(
            lat=gdf.geometry.y,
            lon=gdf.geometry.x,
            mode="markers",
            marker=dict(size=6),
            name=info.get("name", layer_modules[i]),  # optional legend name
            visible=False
        )
    )

# Force map to Oregon
oregon_center = {"lat": 44.0, "lon": -120.5}
oregon_zoom = 5.5

fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_center=oregon_center,
    mapbox_zoom=oregon_zoom,
    margin=dict(l=10, r=10, t=10, b=10)
)

# ------------------------------------
# Dash App Layout
# ------------------------------------
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Landslides and Wildfires Mapping in Oregon"),

    # Checklist for toggling layers
    dcc.Checklist(
        id="layer_select",
        options=[{"label": name, "value": i} for i, name in enumerate(layer_modules)],
        value=[],  # start with no layers
        labelStyle={'display': 'block'}
    ),

    # Div that will show metadata about the selected layer
    html.Div(id="layer_info_div", style={"margin": "10px", "padding": "10px", "border": "1px solid #ccc", "display": "none"}),

    dcc.Graph(id="map", figure=fig)
])

# ------------------------------------
# Callback to toggle layers and show layer info
# ------------------------------------
@app.callback(
    [dash.Output("map", "figure"),
     dash.Output("layer_info_div", "children"),
     dash.Output("layer_info_div", "style")],
    [dash.Input("layer_select", "value")]
)
def update_map(selected_layers):
    # Hide all layers first
    for trace in fig.data:
        trace.visible = False

    # Show selected layers
    info_text = ""
    if selected_layers:
        for i in selected_layers:
            fig.data[i].visible = True
            layer_name = layer_modules[i]
            info = layer_info.get(layer_name, {})
            info_text += f"{info.get('name', layer_name)}: {info.get('description', '')} (Units: {info.get('units', 'N/A')})\n"

        div_style = {"margin": "10px", "padding": "10px", "border": "1px solid #ccc", "whiteSpace": "pre-line", "display": "block"}
    else:
        div_style = {"display": "none"}

    return fig, info_text, div_style

# ------------------------------------
# Run the app
# ------------------------------------
if __name__ == "__main__":
    app.run(debug=True)