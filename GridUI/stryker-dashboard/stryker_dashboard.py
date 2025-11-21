"""
Stryker dashboard: Oregon multi-hazard by elevation band.

This Dash app shows either:
  - wildfire + landslide EVENT COUNTS on the 10 km grid, or
  - estimated DAMAGE (USD) on the same 10 km grid.

Event mode:
  * Filtered by mean elevation bands (0–1k, 1–2k, 2–3k, 3–4k, 4k+ feet)
  * Color = total_events = fire_count + slide_count per 10 km cell

Damage mode:
  * Ignores elevation band and event range (all 10 km cells)
  * Color = est_damage_usd per 10 km cell
"""

from pathlib import Path
import json

import geopandas as gpd
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# -------------------------------------------------------------------
# Paths and data loading
# -------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data_stryker"

# 10 km grid with fire_count, slide_count, mean_elev_ft, est_damage_usd
GRID_GPKG = DATA_DIR / "grid_fire_slide_counts_2992_with_elev.gpkg"
GRID_LAYER = "grid_counts"

print("Loading 10 km grid with elevation + damage…")
g = gpd.read_file(GRID_GPKG, layer=GRID_LAYER)

# Make sure we have the columns we expect
for col in ("fire_count", "slide_count", "mean_elev_ft", "est_damage_usd"):
    if col not in g.columns:
        raise RuntimeError(
            f"Expected column '{col}' in {GRID_GPKG}, layer={GRID_LAYER}"
        )

# Clean + derive fields
g["fire_count"] = g["fire_count"].fillna(0).astype(int)
g["slide_count"] = g["slide_count"].fillna(0).astype(int)
g["total_events"] = g["fire_count"] + g["slide_count"]
g["est_damage_usd"] = g["est_damage_usd"].fillna(0).astype(float)

# Reproject to WGS84 for Mapbox
g4326 = g.to_crs(4326)

# Event range for sliders
raw_evt_min = int(g4326["total_events"].min())
EVT_MIN = max(1, raw_evt_min)  # force minimum of 1
EVT_MAX = int(g4326["total_events"].max())

# Damage range for color scale (we'll also compute a 99th percentile below)
DAMAGE_MIN = 0
DAMAGE_MAX = float(g4326["est_damage_usd"].max())
DAMAGE_P99 = float(g4326["est_damage_usd"].quantile(0.99))

# Map center from bounds
minx, miny, maxx, maxy = g4326.total_bounds
MAP_CENTER = {"lat": (miny + maxy) / 2.0, "lon": (minx + maxx) / 2.0}

# Elevation bands (feet) – used only in EVENT mode
ELEV_BANDS = [
    ("0–1,000 ft", 0, 1000),
    ("1,000–2,000 ft", 1000, 2000),
    ("2,000–3,000 ft", 2000, 3000),
    ("3,000–4,000 ft", 3000, 4000),
    ("≥ 4,000 ft", 4000, None),
]


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------

def _to_geojson(df: gpd.GeoDataFrame) -> tuple[pd.DataFrame, dict]:
    """Convert GeoDataFrame to (plain DataFrame + geojson dict) with gid index."""
    df = df.copy().reset_index().rename(columns={"index": "gid"})
    geojson = json.loads(df.to_json())
    return df, geojson


def _filter_by_band(df: gpd.GeoDataFrame, band_label: str) -> gpd.GeoDataFrame:
    """Subset df to one elevation band."""
    try:
        _, lo, hi = next(b for b in ELEV_BANDS if b[0] == band_label)
    except StopIteration:
        band_label, lo, hi = ELEV_BANDS[0]

    mask = df["mean_elev_ft"] >= lo
    if hi is not None:
        mask &= df["mean_elev_ft"] < hi
    return df[mask]


def make_elevation_events_figure(band_label: str, event_range: list[int]):
    """
    Choropleth of total_events filtered by elevation band + event range.

    Uses a band-specific 99th percentile for the colorbar max so we
    actually see variation instead of almost all cells being white.
    """
    df = _filter_by_band(g4326, band_label)

    # Event-range filter (slider)
    if event_range is not None and len(event_range) == 2:
        emin, emax = event_range
        df = df[(df["total_events"] >= emin) & (df["total_events"] <= emax)]

    # If band+range leaves nothing, just return an empty figure
    if df.empty:
        empty_df, empty_geojson = _to_geojson(df)
        fig = px.choropleth_mapbox(
            empty_df,
            geojson=empty_geojson,
            locations="gid",
            featureidkey="properties.gid",
            color="total_events",
            color_continuous_scale="Reds",
            mapbox_style="carto-positron",
            zoom=5.3,
            center=MAP_CENTER,
            opacity=0.75,
        )
        fig.update_layout(
            margin={"l": 0, "r": 0, "t": 60, "b": 0},
            title="No cells match this elevation band / event-range filter",
        )
        return fig

    # Band-specific 99th percentile for better contrast
    evt_p99_band = float(df["total_events"].quantile(0.99))
    evt_max_band = max(evt_p99_band, EVT_MIN + 1)

    df_plain, geojson = _to_geojson(df)

    fig = px.choropleth_mapbox(
        df_plain,
        geojson=geojson,
        locations="gid",
        featureidkey="properties.gid",
        color="total_events",
        color_continuous_scale="Reds",
        range_color=(EVT_MIN, evt_max_band),
        mapbox_style="carto-positron",
        zoom=5.3,
        center=MAP_CENTER,
        opacity=0.75,
        labels={"total_events": "Events per 10 km cell"},
    )

    fig.update_coloraxes(
        colorbar_title="Wildfire + landslide<br>events per 10 km cell",
    )

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 60, "b": 0},
        title=(
            "Oregon Multi-Hazard Event Counts (Wildfire + Landslide)<br>"
            f"Cells with Mean Elevation {band_label}"
        ),
    )
    return fig


def make_damage_all_figure():
    """
    Choropleth of estimated damage using ALL 10 km cells (no elevation filter).

    We use 0 → 99th percentile as the color range so patterns are visible
    instead of almost all cells being white due to a few extreme outliers.
    """
    df_plain, geojson = _to_geojson(g4326)

    fig = px.choropleth_mapbox(
        df_plain,
        geojson=geojson,
        locations="gid",
        featureidkey="properties.gid",
        color="est_damage_usd",
        color_continuous_scale="Reds",
        range_color=(DAMAGE_MIN, DAMAGE_P99),
        mapbox_style="carto-positron",
        zoom=5.3,
        center=MAP_CENTER,
        opacity=0.75,
        labels={"est_damage_usd": "Damage (USD)"},
    )

    tickvals = [0, 25_000_000, 50_000_000, 100_000_000, 150_000_000]
    ticktext = ["$0M", "$25M", "$50M", "$100M", "$150M"]

    fig.update_coloraxes(
        colorbar_title="Estimated damage<br>(Million USD)",
        colorbar=dict(
            tickvals=tickvals,
            ticktext=ticktext,
        ),
    )

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 60, "b": 0},
        title=(
            "Estimated Multi-Hazard Damage (Wildfire + Landslide)<br>"
            "All 10 km grid cells, 2000–2022"
        ),
    )
    return fig


# -------------------------------------------------------------------
# Dash app layout
# -------------------------------------------------------------------

app = Dash(__name__)
server = app.server  # for deployment

app.layout = html.Div(
    style={"fontFamily": "system-ui, -apple-system, BlinkMacSystemFont, sans-serif"},
    children=[
        html.H1(
            "Oregon Multi-Hazard Elevation Explorer",
            style={"textAlign": "center", "marginBottom": "0.25rem"},
        ),
        html.P(
            "10 km grid, 2000–2022. Toggle between event counts and damage estimates.",
            style={"textAlign": "center", "marginTop": "0"},
        ),

        html.Div(
            style={"maxWidth": "1100px", "margin": "1rem auto"},
            children=[
                html.Label("Metric:", style={"fontWeight": 600}),
                dcc.RadioItems(
                    id="metric",
                    value="events",
                    options=[
                        {
                            "label": "Event counts (wildfire + landslide)",
                            "value": "events",
                        },
                        {
                            "label": "Estimated damage (USD)",
                            "value": "damage",
                        },
                    ],
                    labelStyle={"display": "inline-block", "marginRight": "1.5rem"},
                    style={"marginBottom": "1rem"},
                ),

                html.Label(
                    "Elevation band (mean_elev_ft, EVENT mode only):",
                    style={"fontWeight": 600},
                ),
                dcc.Dropdown(
                    id="elev-band",
                    value=ELEV_BANDS[0][0],
                    options=[{"label": lbl, "value": lbl} for (lbl, _, _) in ELEV_BANDS],
                    clearable=False,
                    style={"marginBottom": "1rem"},
                ),

                html.Label(
                    "Event count range (wildfire + landslide per cell, EVENT mode only):",
                    style={"fontWeight": 600},
                ),
                dcc.RangeSlider(
                    id="event-range",
                    min=EVT_MIN,
                    max=EVT_MAX,
                    value=[EVT_MIN, EVT_MAX],
                    step=1,
                    marks={
                        EVT_MIN: str(EVT_MIN),
                        EVT_MAX: str(EVT_MAX),
                    },
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ],
        ),

        dcc.Graph(id="map", style={"height": "80vh"}),
    ],
)

# -------------------------------------------------------------------
# Callbacks
# -------------------------------------------------------------------

@app.callback(
    Output("map", "figure"),
    Input("metric", "value"),
    Input("elev-band", "value"),
    Input("event-range", "value"),
)
def update_map(metric, elev_band, event_range):
    """
    Update map when metric, elevation band, or event-range slider changes.

    * EVENT mode: use elevation band + event range
    * DAMAGE mode: ignore those controls and show all 10 km cells
    """
    if metric == "events":
        if elev_band is None:
            elev_band = ELEV_BANDS[0][0]
        if not event_range:
            event_range = [EVT_MIN, EVT_MAX]
        return make_elevation_events_figure(elev_band, event_range)

    # Damage mode ignores elevation band and event_range
    return make_damage_all_figure()


# -------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
