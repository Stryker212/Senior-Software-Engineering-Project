from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
from matplotlib_scalebar.scalebar import ScaleBar
import contextily as cx
import geopandas as gpd

# -----------------------
# Config / file locations
# -----------------------
ROOT = Path(__file__).resolve().parents[1]
GPKG = ROOT / "data" / "grid_fire_slide_counts_2992.gpkg"
LAYER = "grid_counts"
OUT_PNG = ROOT / "data" / "Oregon_MultiHazard_EstDamage.png"

# Fixed color scale (match your QGIS legend)
V_MIN = 0
V_MAX = 155_344_000  # dollars ($155,344,000)

# -------------
# Load & prep
# -------------
print("Loading GeoPackage…")
g = gpd.read_file(GPKG, layer=LAYER)

# Project to Web Mercator for the basemap
g3857 = g.to_crs(3857)

# -------------
# Draw the map
# -------------
print("Drawing map…")
fig, ax = plt.subplots(figsize=(13, 9), dpi=200)

# Grid polygons, no auto-legend (we’ll build our own)
plot = g3857.plot(
    ax=ax,
    column="est_damage_usd",
    cmap="Reds",
    scheme="NaturalBreaks",
    k=9,
    alpha=0.70,
    edgecolor="black",
    linewidth=0.15,
    legend=False,
)

# Basemap
cx.add_basemap(ax, crs=g3857.crs, source=cx.providers.OpenStreetMap.Mapnik)

# ------------------------------
# Manual colorbar ($0 → $155.344M)
# ------------------------------
# Use the same cmap but lock normalization to our fixed range
coll = plot.collections[0]
norm = mpl.colors.Normalize(vmin=V_MIN, vmax=V_MAX)
sm = mpl.cm.ScalarMappable(cmap=coll.cmap, norm=norm)
sm.set_array([])

cbar = fig.colorbar(sm, ax=ax, fraction=0.036, pad=0.02)
cbar.set_label("Estimated Damage (Million USD)", fontsize=10)

def fmt_millions(v, _):
    return f"${v/1_000_000:,.0f}M"

cbar.ax.yaxis.set_major_formatter(FuncFormatter(fmt_millions))
cbar.ax.yaxis.set_major_locator(MaxNLocator(nbins=9))  # ~9 ticks: 0M, 20M, …, 160M

# -------------
# Title & scale
# -------------
ax.set_axis_off()
ax.set_title(
    "Oregon Multi-Hazard Estimated Damage (Wildfire + Landslide)\n2000–2022",
    fontsize=16,
    pad=12,
)

# Scale bar (meters, since EPSG:3857)
ax.add_artist(ScaleBar(1, units="m", location="lower left", box_alpha=0.6))

fig.tight_layout()
fig.savefig(OUT_PNG, bbox_inches="tight")
print(f"Wrote map: {OUT_PNG}")
