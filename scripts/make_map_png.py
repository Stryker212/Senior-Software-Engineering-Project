"""Render a choropleth map of estimated multi-hazard damages for Oregon."""

from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
from matplotlib_scalebar.scalebar import ScaleBar
import contextily as cx
import geopandas as gpd

# --- File paths ---
ROOT = Path(__file__).resolve().parents[1]
GPKG = ROOT / "data" / "grid_fire_slide_counts_2992.gpkg"
LAYER = "grid_counts"
OUT_PNG = ROOT / "data" / "Oregon_MultiHazard_EstDamage.png"

V_MIN = 0
V_MAX = 155_344_000  # dollars ($155.3M)

print("Loading GeoPackage…")
g = gpd.read_file(GPKG, layer=LAYER)
g3857 = g.to_crs(3857)

print("Drawing map…")
fig, ax = plt.subplots(figsize=(13, 9), dpi=200)

plot = g3857.plot(
    ax=ax,
    column="est_damage_usd",
    cmap="Reds",
    scheme="NaturalBreaks",
    k=9,
    alpha=0.7,
    edgecolor="black",
    linewidth=0.15,
    legend=False,
)

cx.add_basemap(ax, crs=g3857.crs, source=cx.providers.OpenStreetMap.Mapnik)

coll = plot.collections[0]
norm = mpl.colors.Normalize(vmin=V_MIN, vmax=V_MAX)
sm = mpl.cm.ScalarMappable(cmap=coll.cmap, norm=norm)
sm.set_array([])

cbar = fig.colorbar(sm, ax=ax, fraction=0.036, pad=0.02)
cbar.set_label("Estimated Damage (Million USD)", fontsize=10)

def fmt_millions(v, _):
    """Format colorbar ticks as millions of dollars."""
    return f"${v/1_000_000:,.0f}M"

cbar.ax.yaxis.set_major_formatter(FuncFormatter(fmt_millions))
cbar.ax.yaxis.set_major_locator(MaxNLocator(nbins=9))

ax.set_axis_off()
ax.set_title(
    "Oregon Multi-Hazard Estimated Damage (Wildfire + Landslide)\n2000–2022",
    fontsize=16,
    pad=12,
)
ax.add_artist(ScaleBar(1, units="m", location="lower left", box_alpha=0.6))

fig.tight_layout()
fig.savefig(OUT_PNG, bbox_inches="tight")
print(f"Wrote map: {OUT_PNG}")
