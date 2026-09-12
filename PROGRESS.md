# Where this stands

Branch `mushroom-detail-1to1`. Goal: bring `mushroom-room-fp2.html` to 1:1 with the
Fondazione Prada installation, driven by reference photography in
`agnes-chee-fondazione-prada-photos/` (gitignored — local only).

## Commits
- `ae92537` CLAUDE.md + .gitignore
- `5435aab` Phase 1 — foundations
- `2247634` Phase 2 — biconvex lens
- `fd2f8dd` Phase 2 review revisions

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

## Next: Phase 3 — the veil crust ("the bulbs")

**The algorithm is already solved and calibrated** — do not re-derive it. It is NOT scattered
instanced warts; it is one cracked crust thresholded from a noise field, at different coverage
and feature size per stage. Working prototype logic:

```js
bands = (5.5 + 5.5*t) * max(0.55, scale*0.75)
warp  = 3.1*noise(th*4.5, t*2.2, seed) + 1.5*noise(th*9.1, t*4.4, seed+7)  // breaks rings into arcs
ring  = sin(t*PI*bands + warp)
isle  = 0.62*noise(th*2.6s, t*4.2s, seed+11) + 0.30*noise(th*5.9s, t*9.1s, seed+29)
      + 0.14*noise(th*11.3s, t*17.7s, seed+53)
field = tang*0.80*ring + (1 - 0.40*tang)*isle
belt  = 0.94 + 0.13*sin(PI*t^0.8)        // gaps widest mid-cap
crust = (field/belt) > thr
```
`t` = normalised apex→margin. `noise` = the existing `noise2`. Thresholds were calibrated by
bisection to hit target coverage:

| stage      | coverage | scale | tang | thr     |
|------------|----------|-------|------|---------|
| peppercorn | 0.38     | 3.4   | 0.12 |  0.1032 |
| button     | 0.52     | 2.2   | 0.35 | -0.0168 |
| crust      | 0.50     | 1.30  | 0.72 |  0.0142 |
| expanding  | 0.28     | 0.95  | 0.45 |  0.2149 |
| mature     | 0.15     | 0.70  | 0.12 |  0.3323 |

Coverage is NOT monotonic with expansion — the photographs' smallest buttons are red with ~38%
fine white dotting; there is no fully-white stage. Coverage and feature size must stay
independent parameters. Plaque profile is flat-topped with a hard UNDERCUT (they overhang the
skin), relief ~10-15% of the plaque's own width, warm bone-white with dark speckling.

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
- **Nothing has been rendered in a browser.** Geometry is unit-tested and the cap texture was
  verified via an offline PNG re-render, but the assembled scene — shadows, AO, the lens in
  perspective — is unconfirmed. Serve with `python3 -m http.server` and look before trusting it.
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
