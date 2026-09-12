# Where this stands

Branch `mushroom-detail-1to1`. Goal: bring `mushroom-room-fp2.html` to 1:1 with the
Fondazione Prada installation, driven by reference photography in
`agnes-chee-fondazione-prada-photos/` (gitignored — local only).

## Commits
- `ae92537` CLAUDE.md + .gitignore
- `5435aab` Phase 1 — foundations
- `2247634` Phase 2 — biconvex lens
- `fd2f8dd` Phase 2 review revisions
- `e010ba7` revolve seam, lobing, exposure
- Phase 3 — veil crust

## Done

**Phase 1.** `capGeometry()` extracted to mirror the Python `cap_geometry()`. Fixed the
degenerate gill expression that was cutting flat radial seams across the hymenium. Unbound
ShiftRight from duck. Shadows enabled — three upward spots at x = -5/0/5 spanning the plan,
slit point lights left shadowless to shape. **`VSMShadowMap`, not PCFSoft** — PCFSoftShadowMap
silently ignores `shadow.radius`, so there is no working softness control under it, and soft
low-contrast edges are this room's signature. GTAO at 0.11 m (not the 0.25 default) to bite at
gill/wart scale. Warts do not cast: 1-3 cm cannot resolve on the map, AO seats them.

**Phase 2.** The pileus is now one closed biconvex lens — red skin bulging down, gill envelope
bulging UP on a flatter profile, closing to a knife edge at the margin. The old code offset the
gill surface a constant distance inside the red bowl so both faces bulged the same way; that was
the single biggest form error. Stage table retuned (mature was 33% as thick as wide, now ~22%).
`shapeCap()` breaks the surface of revolution with 12-15 lobes at 3-5% of radius. Cap texture
repainted along v across the whole cross-section to give the four-band margin.

## Phase 3 done — the veil crust

Implemented as one cracked crust thresholded from a noise field, baked into the cap
colour map plus a matching bump map, with instanced flat-topped plaques for silhouette
placed by rejection-sampling the SAME field so geometry and paint agree.

Two corrections made during implementation, both only visible once rendered:
- **The field must be periodic in theta.** `noise2`'s internal multipliers (1.7/3.3/6.1)
  are irrational w.r.t. 2*pi, so feeding it an angle left a hard discontinuity at the
  revolve seam. Replaced with `pnoise()` using integer harmonics of theta.
- **Thresholds are now solved at runtime**, not hard-coded. `crustGrid()` builds the
  field once per stage and takes the quantile for the target coverage. The old table of
  calibrated constants is gone and should not be reinstated — it silently went stale the
  moment the field changed.

Stage -> crust mapping lives in the `S` table (`crust:` key). Feature `scale` had to go
up substantially for mature/expanding versus the flat prototype: features render much
coarser on the actual cap than the (theta,t) ASCII preview suggested.

## Then
- **Phase 4 — stipe.** Onion/teardrop ceiling bulb, 2-2.5x shaft, wrapped in 5-8 concentric
  bands of recurved scales tightening downward. Separate discrete torn annulus lower down the
  bare shaft, projecting only ~10-15% of shaft radius, ragged lower edge, sagging one side.
  Current code models a wide drooping skirt — wrong. Lean 0-15°, not more.
- **Phase 5 — gills.** Instanced radial blades, ~150-200, parallel-sided fins, sharp edges,
  lamellulae only in the outer 25-35%, stopping short of the stipe at a smooth boss. Replaces
  the corrugated revolve and is cheaper than it.
- **Phase 6 — room.** Recessed splayed light wells, white reflector, TWO tubes each, long axis
  along the room's length, grid layout. Terracotta floor (currently polished near-white).
  Keep the wall gradient as a lighting result, not baked albedo.

## Open / unverified
- Rendering is now verified in-browser. `?debug` exposes `window.__room.look(x,y,z,yaw,pitch)`
  for a free camera; without it the render loop pins the view to the threshold.
- **Lighting needs a final pass after Phase 6.** Exposure is 0.55 against a near-white floor;
  a terracotta floor absorbs far more and the scene will darken. Also every floor luminaire
  currently sits at z = 0 in one central row, so caps at z = +/-1.78 are underlit — the real
  layout is a grid, which Phase 6 introduces.
- Cap red is **resolved**. Four rounds of correcting the base hex were fighting the wrong
  variable: the base at 5.8 deg hue was already a correct cool scarlet. The fault was the
  accent layers at 15-22 deg hue stacking ~34 deep. Cooled and thinned those instead; the
  base is unchanged at `#d32a18` mature / `#b01c15` young. Do not re-correct the base.
- Unresolved from the photos: whether gills are truly free of the stipe, and what the
  through-holes in the largest caps are (rigging access vs. sculptural intent).

## Regenerating the reference crops
Scratchpad crops are gone with the session. Recreate from the photo folder with:
`sips -c <h> <w> --cropOffset <y> <x> <src>.jpg --out crop.jpg` (photos are 3072x4096).
The load-bearing ones were: a mature cap edge-on from `05` (y1638 x478 h615 w887), the gill fan
from `06` (y2799 x1024 h820 w2048), the cracked crust button from `03` (y1092 x512 h956 w990),
and the stipe bulb from `06` (y1638 x1604 h956 w512).
