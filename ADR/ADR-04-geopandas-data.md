ADR-04 — Using GeoPandas for Data Loading and Cleaning

Status: Accepted
Date: 2025-11-23

Context

Spatial datasets come in file formats like:

Shapefiles

GeoJSON

CSV with lat/lon

GeoPandas provides a powerful, Pythonic way to load, clean, and validate these files before visualization.

Decision

Use GeoPandas inside each layer module to load data and clean invalid geometries using:

gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()]

Consequences
Positive

Prevents rendering errors caused by null or empty geometries.

Provides consistent geometry handling across all layers.

Native integration with pandas for attribute handling.

Negative

GeoPandas can be slower for very large datasets.

Adds complexity to environment setup (GDAL, Fiona).

Alternatives Considered

Pure pandas with manual lat/lon parsing
→ No geometric validation.

Shapely-only processing
→ Requires more custom code.

Database-based spatial storage (PostGIS)
→ Overkill for this project.