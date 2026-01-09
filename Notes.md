# Lap Time Decomposition & Performance Attribution

This document explains the engineering choices, assumptions, and limitations behind the lap delta and phase attribution pipeline.

The intent is to mirror how performance engineers reason about *where lap time is gained or lost* using telemetry-aligned comparisons, while keeping the system reproducible and testable with public data.

---

## Definitions and sign conventions

### Lap delta definition
We define the lap delta trace as:

Δt(s) = t_target(s) − t_reference(s)

where `s` is distance along the lap (meters) on a canonical distance grid.

- **Δt > 0** means the target lap is *slower* than the reference at that distance.
- **Δt < 0** means the target lap is *faster* than the reference at that distance.

### Corner attribution definition (3-phase)
For each corner segment, we sample Δt at key distances:

- `s0 = brake_start`
- `s1 = apex`
- `s2 = throttle_on`
- `s3 = exit_end`

The phase contributions are:

- **Braking loss** = Δt(s1) − Δt(s0)
- **Mid-corner loss** = Δt(s2) − Δt(s1)
- **Traction loss** = Δt(s3) − Δt(s2)
- **Corner total** = Δt(s3) − Δt(s0)

Conservation (numerical):

braking + mid-corner + traction ≈ total

with a small floating-point tolerance.

### Interpreting negative phase losses
Phase contributions can be negative. This is expected.

Example:
- Negative braking loss implies the target gained time relative to the reference during the braking-to-apex phase.
- Negative traction loss implies the target gained time relative to the reference from throttle-on to exit_end (e.g., better traction, better power deployment, cleaner line).

---

## Pipeline overview (what the code does)

1. **Ingest two laps** for the same session using FastF1.
2. **Resample telemetry onto a 1 m distance grid** to stabilize comparisons.
3. **Compute lap delta trace** Δt(s) from the resampled laps.
4. **Detect braking zones** on the reference lap.
5. **Build corner segments** per braking zone:
   - apex via minimum speed search
   - throttle-on via first sustained throttle threshold after apex
   - exit_end via fixed window capped at the next braking start to avoid overlap
6. **Compute attribution** by sampling Δt at segment keypoints.

This produces:
- Δt(s) plot
- corner segmentation table
- 3-phase corner attribution table
- debrief-style stacked bar visualization

---

## Key engineering choices (and why)

### 1) Distance-grid resampling (default 1 m)
Why:
- Telemetry sampling is irregular and differs between laps/drivers.
- Distance alignment makes point-wise comparisons stable and interpretable.

Tradeoff:
- Smaller step sizes increase compute and sensitivity to noise.
- Larger steps may smear short events (e.g., quick throttle lifts).

### 2) Braking zone detection (v1)
Current approach:
- Uses a brake signal to identify braking intervals.
- Merges nearby zones and filters very short zones.

Why it’s acceptable for v1:
- Produces interpretable segments quickly.
- Keeps the method simple and testable with public data.

Limitation:
- Brake flag availability/quality varies; some braking can be missed.
- A higher-fidelity method would use longitudinal acceleration / speed gradient.

### 3) Apex definition (minimum speed)
We approximate apex as the minimum speed point in a local window after braking start.

Why:
- Apex is often correlated with minimum speed in typical corners.
- Public telemetry lacks full vehicle dynamics states, so this is a robust heuristic.

Limitation:
- Complex corners/chicanes may have multiple minima.

### 4) Throttle-on definition (first stable threshold)
Throttle-on is defined as the first point after apex where throttle exceeds a threshold and remains above it for a small distance window.

Why:
- Reduces false triggers from brief pedal noise.
- Produces a stable split between mid-corner and traction phases.

Limitation:
- Public throttle is a proxy; in real environments you would prefer torque request / power unit deployment signals.

### 5) Corner windows do not partition the full lap (by design)
We currently attribute only within corner windows (brake_start → exit_end).

Result:
- Sum of corner totals does **not** necessarily equal full lap Δtime.

Why this is deliberate:
- v1 focuses on interpretable “corner performance” deltas, which is often what engineers care about first.
- Straights and other regions can be handled separately in a full-lap accounting pass.

---

## Validation and tests

We validate core invariants with unit tests:
- resampling produces monotonic distance grids and required columns
- segments do not overlap after capping exits
- v2 attribution conserves total within floating-point tolerance:
  
  braking + mid-corner + traction ≈ total

  This ensures refactors don’t silently break interpretation.

---

## Known limitations and failure modes (honest list)

- Braking zone detection depends on brake flag quality (can under-detect zones).
- Apex heuristic can be ambiguous in multi-apex corners.
- Throttle-on detection is sensitive to chosen thresholds (track/car dependent).
- Corner windows do not cover the full lap, so totals are not a full lap partition.
- Public telemetry omits many states (ride height, tyre state, ERS deployment, torque maps), limiting causal claims.

---

## What I would add with more time (or proprietary signals)

- Full-lap accounting: add straight segments and an “unattributed remainder” so totals match lap delta exactly.
- Braking detection via longitudinal acceleration and/or dv/ds thresholding (more robust than brake flag).
- Curvature-based corner detection using position/heading to avoid brake-only segmentation.
- Multi-lap statistics per driver (best/mean + confidence intervals).
- Track-normalized comparisons and driver style clustering across tracks.

