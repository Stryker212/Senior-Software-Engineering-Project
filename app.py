import dash
from dash import dcc, html
import plotly.graph_objects as go
import importlib
import os
import warnings
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPolygon

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", "GeoSeries.notna", UserWarning)

# ============================================================
# Helper: Convert polygon geometry → Plotly scatter outline coords
# ============================================================
def polygon_to_latlon_lists(geometry):
    """Convert Polygon or MultiPolygon into lat/lon lists for Plotly Scattermap."""
    if geometry.geom_type == "Polygon":
        polygons = [geometry]
    elif geometry.geom_type == "MultiPolygon":
        polygons = list(geometry.geoms)
    else:
        return [], []

    lat_list = []
    lon_list = []

    for poly in polygons:
        if poly.is_empty:
            continue
        x, y = poly.exterior.xy
        lon_list.extend(list(x) + [None])
        lat_list.extend(list(y) + [None])

    return lat_list, lon_list


# ============================================================
# Layer metadata
# ============================================================
layer_info = {
    "sample_wildfires": {
        "name": "Wildfire Occurrences",
        "description": "Points where wildfires occurred in Oregon."
    },
    "sample_landslides": {
        "name": "Landslides",
        "description": "Recorded landslides in Oregon."
    },
    "wildfire_polygons": {
        "name": "Wildfire Polygons",
        "description": "Polygon areas of large recorded wildfires."
    },
    #"wildfire_classes": {
        #"name": "Wildfires by Class",
        #"description": "Wildfires categorized by size (A–G classes)."
    #}
}

# ============================================================
# Load layer modules dynamically
# ============================================================
layer_modules = []
layer_gdfs = []
layer_cache = {}

for file in os.listdir("layers"):
    if file.endswith(".py") and file != "__init__.py":
        module_name = file[:-3]
        module = importlib.import_module(f"layers.{module_name}")

        gdf = module.load_layer()
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]

        layer_modules.append(module_name)
        layer_gdfs.append(gdf)
        layer_cache[module_name] = gdf


# ============================================================
# Build the base map
# ============================================================
fig = go.Figure()

for mod_name, gdf in zip(layer_modules, layer_gdfs):
    info = layer_info.get(mod_name, {})
    geom_types = gdf.geometry.geom_type.unique()
    '''
    # --- Wildfire-by-class: multiple traces for legend ---
    if mod_name == "wildfire_classes":
        # Clean values BEFORE color mapping
        gdf["Size_class"] = (
            gdf["Size_class"]
            .astype(str)
            .str.strip()
            .str.upper()
            )

        # Use the authoritative mapping FROM THE FILE, not from gdf
        color_map = {
            "A": "#FFFFB2",
            "B": "#FED976",
            "C": "#FEB24C",
            "D": "#FD8D3C",
            "E": "#FC4E2A",
            "F": "#E31A1C",
            "G": "#BD0026",
        }

        size_classes = sorted(gdf["Size_class"].unique())

        for cls in size_classes:
            cls_gdf = gdf[gdf["Size_class"] == cls]
            fig.add_trace(
                go.Scattermap(
                    lat=cls_gdf.geometry.y,
                    lon=cls_gdf.geometry.x,
                    mode="markers",
                    marker=dict(size=6, color=color_map.get(cls, "#000000")),
                    name=f"{cls} Class ({cls_gdf.shape[0]} points)",
                    visible=False
                )
            )
    '''
    # --- Simple point layers ---
    # elif all(g == "Point" for g in geom_types):
    if all(g == "Point" for g in geom_types):
        fig.add_trace(
            go.Scattermap(
                lat=gdf.geometry.y,
                lon=gdf.geometry.x,
                mode="markers",
                marker=dict(size=6, color="red"),
                name=info.get("name", mod_name),
                visible=False
            )
        )

    # --- Polygon layers ---
    else:
        all_lats, all_lons = [], []
        for geom_item in gdf.geometry:
            lats, lons = polygon_to_latlon_lists(geom_item)
            all_lats.extend(lats)
            all_lons.extend(lons)

        fig.add_trace(
            go.Scattermap(
                lat=all_lats,
                lon=all_lons,
                mode="lines",
                fill="toself",
                fillcolor="rgba(0,0,255,0.2)",
                line=dict(width=0.6, color="blue"),
                name=info.get("name", mod_name),
                visible=False
            )
        )

# ============================================================
# Default map view — CENTER ON OREGON
# ============================================================
fig.update_layout(
    map=dict(
        center=dict(lat=44.0, lon=-120.5),
        zoom=5.5,
        style="carto-positron"
    ),
    margin=dict(l=10, r=10, t=10, b=10)
)


# ============================================================
# DASH APP LAYOUT
# ============================================================
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Landslides and Wildfires Mapping in Oregon"),

    dcc.Checklist(
        id="layer_select",
        options=[
            {"label": layer_info[name]["name"], "value": i}
            for i, name in enumerate(layer_modules)
        ],
        value=[],
        labelStyle={'display': 'block'}
    ),

    html.Div(
        id="layer_info_div",
        style={
            "margin": "10px",
            "padding": "10px",
            "border": "1px solid #ccc",
            "display": "none"
        }
    ),

    dcc.Graph(id="map", figure=fig),
])


# ============================================================
# CALLBACK: Toggle layers + update metadata
# ============================================================
@app.callback(
    [
        dash.Output("map", "figure"),
        dash.Output("layer_info_div", "children"),
        dash.Output("layer_info_div", "style"),
    ],
    [dash.Input("layer_select", "value")]
)
def update_map(selected_layers):
    # Hide every layer initially
    for trace in fig.data:
        trace.visible = False

    info_text = ""

    if selected_layers:
        for idx in selected_layers:
            fig.data[idx].visible = True
            mod_name = layer_modules[idx]
            info = layer_info.get(mod_name, {})
            info_text += f"{info['name']}\n{info['description']}\n\n"

        return fig, info_text, {
            "display": "block",
            "whiteSpace": "pre-line",
            "margin": "10px",
            "padding": "10px",
            "border": "1px solid #ccc"
        }

    return fig, "", {"display": "none"}


# ============================================================
# RUN APP (Dash 3+)
# ============================================================
if __name__ == "__main__":
    app.run(debug=True)
