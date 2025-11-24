ADR-02 — Using Plotly Scattermapbox for Map Visualization

Status: Accepted
Date: 2025-11-23

Context

The project requires:

An interactive geographic map

Panning, zooming, and toggling layers

Clean Oregon-centered display

Compatibility with Dash

Plotly’s Mapbox maps provide all these features natively.

Decision

Use Plotly Scattermapbox as the visualization engine for all spatial hazard layers.

Consequences
Positive

Excellent Dash compatibility.

Smooth toggling and interactivity.

Supports separate traces per layer.

Good visual quality and performance for point-based datasets.

Negative

Mapbox features require internet unless using custom tiles.

Scattermapbox does not support polygons/rasters as easily as points.

Less performant with very large datasets.

Alternatives Considered

Leaflet.js (via dash-leaflet)

More flexible, good for geospatial work

Slightly more setup; Plotly offered simpler integration.

Google Maps API

Not free for large usage; more overhead.

Static Matplotlib maps

Not interactive → rejected.