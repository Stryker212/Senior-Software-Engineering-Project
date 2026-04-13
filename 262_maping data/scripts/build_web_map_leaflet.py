"""
build_web_map_leaflet.py
Fast Leaflet web map:
- Vector layers from GeoJSON
- Raster layers from XYZ tiles (QGIS "Generate XYZ Tiles" output)

Run:
  python scripts/build_web_map_leaflet.py

Output:
  outputs/web/index.html
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

# -------------------------
# CONFIG (edit these)
# -------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]

# Your structure (matches your screenshot)
OUTPUT_DIR = REPO_ROOT / "outputs" / "web"
INDEX_HTML = OUTPUT_DIR / "index.html"

DATA_DIR = REPO_ROOT / "Data"

# Vector layers (GeoJSON)
VECTOR_LAYERS: List[Dict[str, Any]] = [
    {
        "name": "Wildfires (2000–2022)",
        "path": DATA_DIR / "Events" / "wildfire_points_2000_2022.geojson",
        "type": "point",
        "color": "#ff3b30",
        "radius": 2,
        "opacity": 0.85,
        "default_on": True,
    },
    {
        "name": "Landslides",
        "path": DATA_DIR / "Events" / "landslide_points.geojson",
        "type": "point",
        "color": "#0a84ff",
        "radius": 2,
        "opacity": 0.85,
        "default_on": True,
    },
]

# Tile overlays (XYZ tiles)
# Your slope tiles are in outputs/web/tiles/slope/{z}/{x}/{y}.png
TILE_LAYERS: List[Dict[str, Any]] = [
    {
        "name": "Slope (tiles)",
        "tiles_dir": OUTPUT_DIR / "tiles" / "slope",
        "min_zoom": 5,
        "max_zoom": 9,
        "opacity": 0.70,
        "default_on": False,  # set True if you want it ON by default
    },
]

# Map start view (Oregon)
MAP_START = {"lat": 44.0, "lon": -120.5, "zoom": 6}

# -------------------------
# Helpers
# -------------------------

def _write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _rel_from_output_dir(target: Path) -> str:
    """Return a browser-friendly relative path from OUTPUT_DIR to target."""
    target = target.resolve()
    out = OUTPUT_DIR.resolve()
    # Build ../../ style relative path
    rel = target.relative_to(REPO_ROOT)
    # index.html sits in outputs/web, so relative from there is "../.." + rel
    # but since outputs/web is already under REPO_ROOT/outputs/web,
    # easiest: go up from outputs/web to repo root => ../..
    return str(Path("..") / ".." / rel).replace("\\", "/")


def _tiles_url_from_tiles_dir(tiles_dir: Path) -> str:
    """
    tiles_dir is expected to contain {z}/{x}/{y}.png
    Since index.html is inside OUTPUT_DIR, use a path relative to OUTPUT_DIR:
      tiles/slope/{z}/{x}/{y}.png
    """
    # Make it relative to OUTPUT_DIR if possible
    tiles_dir = tiles_dir.resolve()
    out = OUTPUT_DIR.resolve()

    if tiles_dir.is_relative_to(out):
        rel = tiles_dir.relative_to(out)
        return str(Path(rel) / "{z}" / "{x}" / "{y}.png").replace("\\", "/")
    else:
        # fallback (shouldn't happen for your setup)
        return _rel_from_output_dir(tiles_dir) + "/{z}/{x}/{y}.png"


# -------------------------
# HTML builder
# -------------------------

def write_index_html() -> None:
    # Build vector configs (fetch GeoJSON in browser)
    vector_configs = []
    for lyr in VECTOR_LAYERS:
        p = Path(lyr["path"])
        if not p.exists():
            raise FileNotFoundError(f"Missing GeoJSON: {p}")

        vector_configs.append(
            {
                "name": lyr["name"],
                "url": _rel_from_output_dir(p),
                "color": lyr.get("color", "#ff0000"),
                "radius": float(lyr.get("radius", 2)),
                "opacity": float(lyr.get("opacity", 0.8)),
                "defaultOn": bool(lyr.get("default_on", True)),
            }
        )

    # Build tile configs
    tile_configs = []
    for t in TILE_LAYERS:
        tiles_dir = Path(t["tiles_dir"])
        if not tiles_dir.exists():
            raise FileNotFoundError(f"Tile directory not found: {tiles_dir}")

        tile_configs.append(
            {
                "name": t["name"],
                "url": _tiles_url_from_tiles_dir(tiles_dir),
                "minZoom": int(t.get("min_zoom", 0)),
                "maxZoom": int(t.get("max_zoom", 18)),
                "opacity": float(t.get("opacity", 0.7)),
                "defaultOn": bool(t.get("default_on", False)),
            }
        )

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Oregon Multi-Layer Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>

  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""
  />

  <style>
    html, body {{ height: 100%; margin: 0; }}
    #map {{ height: 100%; width: 100%; }}
  </style>
</head>

<body>
  <div id="map"></div>

  <script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
    crossorigin=""
  ></script>

  <script>
    const MAP_START = {json.dumps(MAP_START)};
    const VECTOR_LAYERS = {json.dumps(vector_configs)};
    const TILE_LAYERS = {json.dumps(tile_configs)};

    const map = L.map("map").setView([MAP_START.lat, MAP_START.lon], MAP_START.zoom);

    const base = L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors"
    }}).addTo(map);

    const overlayMaps = {{}};

    // ---- Tile overlays ----
    TILE_LAYERS.forEach(t => {{
      const layer = L.tileLayer(t.url, {{
        minZoom: t.minZoom,
        maxZoom: t.maxZoom,
        opacity: t.opacity
      }});
      overlayMaps[t.name] = layer;
      if (t.defaultOn) layer.addTo(map);
    }});

    // ---- Vector overlays ----
    async function loadGeoJSONLayer(cfg) {{
      const res = await fetch(cfg.url);
      if (!res.ok) {{
        throw new Error("Failed to load " + cfg.name + ": " + cfg.url + " (" + res.status + ")");
      }}
      const gj = await res.json();

      const layer = L.geoJSON(gj, {{
        pointToLayer: (feature, latlng) => L.circleMarker(latlng, {{
          radius: cfg.radius,
          color: cfg.color,
          fillColor: cfg.color,
          fillOpacity: cfg.opacity,
          opacity: cfg.opacity,
          weight: 0
        }})
      }});

      return layer;
    }}

    (async () => {{
      for (const cfg of VECTOR_LAYERS) {{
        try {{
          const lyr = await loadGeoJSONLayer(cfg);
          overlayMaps[cfg.name] = lyr;
          if (cfg.defaultOn) lyr.addTo(map);
        }} catch (err) {{
          console.error(err);
          alert(err.message);
        }}
      }}

      L.control.layers({{ "OpenStreetMap": base }}, overlayMaps, {{ collapsed: false }}).addTo(map);
    }})();
  </script>
</body>
</html>
"""
    _write_file(INDEX_HTML, html)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_index_html()
    print(f"Wrote: {INDEX_HTML}")


if __name__ == "__main__":
    main()