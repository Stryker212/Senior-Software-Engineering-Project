ADR-03 — Dash Callbacks for Layer Toggling & Metadata Display

Status: Accepted
Date: 2025-11-23

Context

The interface requires:

Turning layers on/off

Showing metadata about selected datasets

Updating the map reactively

Dash's callback system is the intended mechanism for interactive UI updates.

Decision

Use a single Dash callback that responds to the layer_select checklist input and updates:

The map's trace visibility

The metadata display text

The metadata panel’s CSS (to show/hide it)

Consequences
Positive

Clean separation between UI and logic.

Easy to expand if additional UI components are added.

Maintains responsiveness even with multiple layers.

Negative

Complex callbacks can become harder to debug.

Requires careful indexing to ensure metadata matches the layer.

Alternatives Considered

Multiple callbacks for each layer
→ Rejected as redundant and harder to maintain.

Client-side callbacks (JavaScript)
→ More complex, unnecessary for this project.

Pre-rendering all combinations
→ Inefficient and inflexible.