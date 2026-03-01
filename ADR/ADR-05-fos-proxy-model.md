Context
The project aims to assess landslide susceptibility across Oregon using statewide spatial datasets such as:
-Slope derived from DEM
-Clay percentage (0–100 cm)
-Bulk density (0–100 cm)
-Saturated hydraulic conductivity (ksat)

Vegetation density
A full geotechnical slope stability simulation would require detailed site-specific inputs including:
Soil cohesion values
Effective friction angle measurements
Time-dependent pore pressure modeling
Rainfall infiltration modeling
These inputs are not available at consistent statewide resolution and would significantly increase computational complexity beyond project scope.

Decision
Use a simplified Factor of Safety (FoS)-based stability proxy model built from available statewide soil and slope parameters.
The model will:
Use slope gradients and derived soil rasters
Produce a relative stability index
Be clearly labeled as a proxy model, not an engineering-certified stability calculation

Consequences

Positive
Enables a physically grounded slope stability approximation.
Computationally feasible at statewide scale.
Integrates directly with existing soil parameter layers.
Maintains interpretability of model inputs.

Negative
Oversimplifies real geotechnical processes.
Does not model time-dependent rainfall infiltration.
May be misinterpreted without clear labeling.



Simple multi-layer overlay index
→ Lacks physical grounding in slope stability theory.
