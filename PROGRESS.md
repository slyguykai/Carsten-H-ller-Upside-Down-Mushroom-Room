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
- `d7062c2` Phase 3 — veil crust
- Phase 4 + Phase 3 review fixes

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

## Phase 4 done — the stipe

- **Ceiling bulb** is now an onion: widest a third of the way down, the dome curving back
  IN where it meets the ceiling, wrapped in 5-8 concentric bands of recurved scales that
  tighten downward and fade over the dome. Was a spiky flaring trumpet.
- **Annulus** is a tight torn ring on the bare shaft, ~16% projection, clean upper edge,
  tattered lower edge, sagging one side. Was a wide drooping skirt.
- **Shaft** is near-cylindrical with faint longitudinal fibre.

**The megaphone was never the bulb.** The stem profile itself was
`0.78 + 1.15*exp(-4.6u)` — 1.93x stemR at the ceiling against 0.85x at the cap, a 2.3x
flare. Now `0.93 + 0.20*exp(-3.2u)`.

**Stipe radius was badly over-scaled** in the inherited stage table: `r` was 0.29 of capR
when the reference stipe is ~1/7 of the cap WIDTH, i.e. ~0.15. Everything hanging off the
stipe (bulb, annulus) inherited the error and read as furniture.

## Phase 3 review — fixes applied

A design review that drove the browser and measured pixels found several things:

- **Polar pinwheel.** A field evaluated in (theta, t) turns every blob near t=0 into a wedge,
  because all theta map to the same 3D point at the pole. Fixed by evaluating the island
  noise in **Cartesian disc coordinates** `(t*cos, t*sin)` — uniform feature size across the
  disc, and periodicity in theta for free. *Prefer this to any pole-fade hack.*
- **The crust grid was drawn vertically inverted** — `t=0` (apex) landed at `v=0.70` (margin).
  This put the margin-frequency field on the converging pole and inverted the belt, which is
  why the reviewer measured "flat coverage, no rise toward the rim". The texture rect runs
  margin-at-top to apex-at-bottom; read the grid bottom-up.
- **`belt` was +/-13%** and measured as noise. Now `1.16 - 0.44*t^2.2`, monotonic, with the
  apex lift removed (the reference shows no apex concentration).
- **Clearcoat was bleeding onto the painted crust** — skin and veil share one material, so
  the "fully matte" crust caught specular streaks. Added a `clearcoatMap` mask keyed off the
  same field.
- **Plaque count starved small caps** (11-14 measured vs 40-70 intended) because of a
  `capR/0.9` term; the reference buttons are the most densely covered of all. Floored at 30.
- **Plaques now sample the baked grid**, not the analytic field — same function, but the two
  discretisations disagreed enough to read as two independent scatters.
- `CRUST.button` was dead code (never referenced by `S`); removed.
- Plaque outline jittered off a clean polygon; mature `tang` dropped to 0.05; top isle
  octaves rebalanced for fatter, more confluent worms.

## Phase 5 done — the hymenium

Real lamellae replace the sine-corrugated revolve, which topologically could never open a
gap between blades and so could not self-shadow. Built by `buildHymenium()`.

**Merged BufferGeometry per cap, NOT InstancedMesh.** The cap's margin warp is
`(r/capR)^1.5`, which varies ALONG a single blade's own length — an instance matrix is one
affine transform, so instanced blades would float off the flesh at the margin or tear away
at the hub. This is why `capWarp()` was factored out first; the blade builder calls the same
closure the flesh does.

Structure, settled by two specialists who initially disagreed by 5x and reconciled:
- **Depth `capR * 0.05`** (band 0.04-0.07). The first estimate of 16-45% turned out to be the
  gill DOME's rise off the rim plane (`T/R = h*gr`, 13.5-93.5% in the `S` table) — a real,
  large, already-modelled quantity — mistaken for individual blade standoff. Cross-check that
  settled it: at ~176 lamellae the margin spacing is 3.6% of R, and the reference grooves read
  roughly as deep as they are wide; 16-45% would need grooves 4-13x deeper than wide.
- **Tiered lamellulae**: long gills throughout, one lamellula between each pair over the outer
  two-thirds, a third shorter tier near the rim. Gives 1-1 at mid-radius, ~1-3-1 at the margin.
  Third tier is gated behind `!IS_TOUCH`.
- **Blind-ending, not forking.** The sculpture forks its ribs; we deliberately depart, because
  a forked rib needs a clean Y-joint or it reads as a graphics trick up close.
- **Blunt free edge, not knife-sharp** — this is a stylisation to KEEP. A sharp edge reads as
  papery; the rounded tooth reads as cast plaster, which is what the object is.
- Free collar 10-15% of R; blades taper to a point at both ends; per-blade jitter, wander and
  edge micro-irregularity, because perfectly even spacing is the giveaway of a procedural fan.
- Four separate face strips per blade so cross-section corners stay hard while the length
  stays smooth. Sharing vertices around the section averages the corner normals to mush.

**Albedo `#C9BEB6`.** Both specialists converged on this independently. The old `0xc9b6bb`
had correct S and L but a hue of 344 deg (pink-violet); this is a pure rotation to 25 deg.
Do NOT bake the mauve read into albedo — it is warm key light plus valley AO doing that, and
baking it breaks the moment Phase 6 changes the lighting.

Budget: gill triangles 131,384 -> 88,600; scene 532,966 -> 490,182.

## Phase 6 done — the room (West Village, per the user's direction)

A **deliberate departure from the Fondazione Prada reference**, chosen by the user:

| | Prada reference | built |
| --- | --- | --- |
| floor | warm terracotta, satin | pale wide-plank oak, canvas-painted grain and butt joints |
| walls | warm pink-white | warm gallery white + painted baseboard |
| ceiling | slate blue-grey | plain white |
| luminaires | recessed troughs, two tubes | same — kept, they are the key light |

**The white ceiling is also the more physically honest choice.** With the key at floor level a
white ceiling renders as a dim cool grey on its own; the Prada slate was partly the lighting,
and painting it grey would double-count. Same principle as the gill albedo.

- Floor is a `THREE.Shape` with the wells punched out as holes, so the troughs are real
  recesses rather than decals on the boards.
- Each well is a splayed white reflector box with two emissive tubes, plus a **`RectAreaLight`**
  — which is what a recessed trough physically is, and unlike a point light it throws the
  elongated specular streak a satin floor should show. Needs
  `RectAreaLightUniformsLib.init()` or it silently does nothing. It cannot cast shadows, which
  costs nothing here because casting was already routed through the upward spots.
- Lighting rebalanced for the new albedos: exposure 0.54, hemisphere 0.18, env 0.14.

**Known trade-off of going West Village:** the pale gills had good contrast against Prada's
slate ceiling and have less against white, and the warm terracotta bounce that tinted the
whole reference palette is gone. The room reads brighter and cooler than the photographs. That
is the look the user asked for, not a defect — but if it ever feels too clinical, the levers
are ceiling albedo and the `RectAreaLight` colour temperature, not the mushroom materials.

## Then
## Direction from the user (2026-09-12)

- **The room should read like a West Village NYC gallery**, not a literal copy of the Prada
  space. Fold into Phase 6. **Note the tension:** the reference photographs show a warm
  terracotta floor and a slate-lavender ceiling, which is *not* a white-box NYC gallery. A
  West Village room means white or near-white walls, pale oak or polished concrete underfoot,
  crisp unmoulded corners, and no coving. Decide explicitly which way to go and say so —
  going NYC means deliberately departing from the reference on floor and ceiling colour, and
  the floor-keyed lighting will need rebalancing again because a pale floor bounces far more
  than terracotta. The luminaire geometry (recessed splayed wells, two tubes, long axis along
  the room, grid layout) is worth keeping either way.
- **The mushrooms still need more work** beyond the remaining phases. Additional reference
  photography from the web was suggested — particularly for gill structure (Phase 5), which
  the six local photos only show from below and at a grazing angle. Nothing has been
  downloaded; that needs the user's go-ahead.

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

## Web reference photography

`reference-web/` (gitignored) holds four Wikimedia Commons photographs of real
*Amanita muscaria*, with provenance in `reference-web/SOURCES.txt`. `w1_gills_macro.jpg` is
the important one — a macro of the gills edge-on, which the six Prada photographs never show.

It settled an open question: **the gills are FREE** — they do not reach the stipe. Sources
also confirm crowded lamellae with short intermediate lamellulae and a minutely powdery gill
edge. Remember these show the ORGANISM; the project recreates the painted SCULPTURE, so use
them for structure and the Prada photos for colour and stylisation.

## Regenerating the reference crops
Scratchpad crops are gone with the session. Recreate from the photo folder with:
`sips -c <h> <w> --cropOffset <y> <x> <src>.jpg --out crop.jpg` (photos are 3072x4096).
The load-bearing ones were: a mature cap edge-on from `05` (y1638 x478 h615 w887), the gill fan
from `06` (y2799 x1024 h820 w2048), the cracked crust button from `03` (y1092 x512 h956 w990),
and the stipe bulb from `06` (y1638 x1604 h956 w512).
