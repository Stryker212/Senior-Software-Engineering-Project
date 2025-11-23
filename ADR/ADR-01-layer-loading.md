ADR-01 — Modular Layer Loading from layers/ Directory

Status: Accepted
Date: 2025-11-23

Context

The project needs to support multiple spatial datasets (e.g., wildfires, landslides).
New layers should be easy to add without editing app.py.

The application already uses files inside layers/ where each file provides a load_layer() function that returns a GeoDataFrame.

Decision

We standardized the architecture so every spatial dataset is stored as a Python module inside the layers/ folder, and each must implement:

def load_layer() -> GeoDataFrame


app.py automatically detects all .py files in this directory, imports them, and loads each dataset without any manual modification.

Consequences
Positive

New layers can be added by simply dropping a new file in the layers/ folder.

Reduces duplicate code for loading GeoDataFrames.

Keeps app.py small and maintainable.

Automatically scales as more datasets are incorporated.

Negative

Requires each layer module to follow the correct API.

Mistakes in a single layer file (bad import, invalid geometry) can prevent the entire app from loading unless error handling is added.

Alternatives Considered

Hardcoding all layers in app.py
→ Rejected due to poor scalability and maintainability.

JSON config file describing layers
→ More overhead, unnecessary for small projects.

Database-backed layer storage
→ Too heavy for project scope.