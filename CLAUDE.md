# CLAUDE.md

Guidance for Claude Code working in this repository.

> **Active work:** branch `mushroom-detail-1to1` is a six-phase 1:1 rebuild of
> `mushroom-room-fp2.html` against real reference photography. **Read `PROGRESS.md` first** —
> it holds phase-by-phase state, the remaining specs, and open questions. This file describes
> the repo; `PROGRESS.md` describes the work in flight.

## What this is

A procedural, code-only recreation of Carsten Höller's *Upside Down Mushroom Room* — giant
fly-agaric sculptures hanging from a gallery ceiling, inverted: the stipe runs *up* to the
ceiling, the convex red cap faces the *floor*, the gills face the *ceiling*. No build system,
package manager, dependency manifest, or test suite. Each file generates the entire scene from
scratch at runtime — no imported meshes, no image assets, no `node_modules`.

- **Blender/Cycles** (`blender-mushroom-room.py`, `blender-mushroom-room2.py`) — offline stills.
- **three.js** (`mushroom-room-fp.html`, `mushroom-room-fp2.html`) — real-time, walkable.

### What `2` means (read before editing)

`2` is "later iteration of that file", **not** "second half of a pair".
`blender-mushroom-room2.py` is **byte-identical** to `blender-mushroom-room.py` — a copy, not a
revision. `mushroom-room-fp2.html` is a genuine revision of `fp.html`, and is now far ahead of
both Blender scripts (different room dimensions, inverted lighting key, five developmental
stages, a real veil-crust system). **The Blender track has not been touched by the rebuild and
is generationally well behind.** Treat CLAUDE.md's old claim that fixes should be ported to both
tracks as aspirational: they no longer depict the same room.

When asked to improve "the room," **ask which track**. For the web track edit `fp2.html`.

## Running things

```bash
python3 -m http.server 8765
```
then open `http://localhost:8765/mushroom-room-fp2.html`. three.js loads from an `importmap`
pinned to `three@0.169.0` on unpkg, so an internet connection is required.

**`?debug` is the only way to inspect geometry.** Without pointer lock the render loop pins the
camera to the threshold. Append `?debug` and use:

```js
window.__room.look(x, y, z, yaw, pitch)   // free camera; also exposes scene, camera, renderer, MAT
```
Room is 14 (x) × 7 (z) × 4.6 m (y); eye height 1.62. Useful viewpoints are listed in `PROGRESS.md`.

Blender: `blender --background --python blender-mushroom-room2.py -- --no-render` for a fast
geometry-only pass; writes `mushroom_room.blend`/`.png` next to the script.

There is no linter, formatter, or test command. **Validate web changes by rendering them in a
browser** — see "Lessons" below for why this is not optional.

## Architecture — `mushroom-room-fp2.html`

Single file, numbered `/* == N. TITLE == */` banners.

| § | Contents |
| --- | --- |
| 0 | Device/quality — `IS_TOUCH`, density scalar `Q`, `USE_BLOOM` |
| 1 | Utilities — `mulberry32`, `noise2`, `revolve()` |
| 2 | Room envelope (`ROOM = {w:14, d:7, h:4.6}`) |
| 3 | Renderer/scene/camera — ACES, exposure 0.55, `FogExp2`, 74° hfov, VSM shadows |
| 4 | Room shell |
| 5 | Floor luminaires |
| 6 | Cap materials — `CRUST`, `pnoise`, `crustField`, `crustGrid`, `makeCapTexture`, `capMaterial` |
| 7 | `capGeometry()`, `shapeCap()`, `WART_GEO`, `makeMushroom(cfg)` |
| 8 | `S` stage table + `PLAN` placement array |
| 9 | Lighting |
| 10 | Post — GTAO → UnrealBloom → Output |
| 11–14 | Player, walk/collide/duck, render loop, HUD |

**Measured budget** (Q=1, all 9 caps, read off the live scene — do not trust prose figures):
scene total ~533 K triangles, of which the gill meshes are ~131 K and the cap lenses ~281 K.
Measure with a `scene.traverse` sum rather than `renderer.info`, which the composer confuses.

**Coordinates:** Blender is Z-up; three.js is Y-up. `makeMushroom` works in a local frame with
`y = 0` at the ceiling, the cap rim at `y = -stemH`, apex at `y = -stemH - capH`.

### Key systems

- **`capGeometry(R, H, rings, gillRise, gillFlat)`** returns one closed **biconvex lens**
  profile (red apex → rim roll → gill apex) plus explicit `uvV`. The red skin bulges down; the
  gill envelope bulges **up** on a flatter profile; they close to a knife edge at the margin.
- **`shapeCap()`** breaks the surface of revolution — 9–12 lobes plus one dominant asymmetric
  notch, weighted `(r/R)^1.5` so the stipe attachment stays put.
- **The cap texture is painted along `v` across the whole cross-section**, giving the four-band
  margin: red skin → thin hard dark line → cream lip → mauve gill-side flesh.
- **`buildHymenium()`** builds the gill blades as one merged `BufferGeometry` per cap.
  Deliberately NOT instanced: the cap warp varies along a blade's own length and an instance
  matrix cannot express that. Any new surface that must stay glued to the cap has to call the
  same `capWarp(th, r)` closure.
- **`crustField()` + `crustGrid()`** — the universal veil as ONE cracked crust thresholded from
  a noise field, baked into the colour and bump maps, with instanced flat-topped plaques placed
  by rejection-sampling the same field. Per-stage `{cov, scale, tang}` in `CRUST`; thresholds
  are **solved at runtime** from target coverage, never hard-coded.

## Lessons from this rebuild — do not relearn these

- **Render before trusting anything.** Geometry that unit-tested correctly and textures that
  looked right as flat PNGs were both wrong in perspective: the scene was blown out to
  near-white, `revolve()` had a seam artefact on every surface, and the cap lobing read as a
  Pringle. None of it was visible outside a browser.
- **Angular noise must use integer harmonics of θ.** `noise2`'s internal multipliers
  (1.7/3.3/6.1) are irrational w.r.t. 2π, so anything driven by an angle will not close around
  a revolved surface. Use `pnoise()`.
- **Don't hard-code calibrated constants.** A table of bisection-calibrated thresholds went
  stale the instant the underlying field changed. Solve them at runtime.
- **`PCFSoftShadowMap` ignores `shadow.radius`** — there is no softness control under it. This
  scene uses `VSMShadowMap` deliberately.
- **Colour: correct the accent layers, not the base.** The cap red read as rust through four
  rounds of base correction; the base was already a correct 5.8° scarlet. The fault was accent
  layers at 15–22° hue stacking ~34 deep.
- **Fixed harmonics alias into visible lattices** at texel scale. Use a hash for speckle.
- **Never drive a surface pattern from polar (θ, t) noise.** Every blob near the pole
  stretches into a wedge and the cap renders a pinwheel. Evaluate in Cartesian disc
  coordinates `(t·cosθ, t·sinθ)` — uniform features, and θ-periodicity for free.
- **Check texture orientation against the uv rect.** The crust grid was drawn inside out for
  a whole phase: apex painted at the margin. It looked plausible enough to survive review.
- **Suspect inherited proportions.** The stipe was 2× too thick and its profile flared 2.3×
  toward the ceiling; both came from the original file and made every Phase 4 form read
  wrong until they were fixed.

## Reference material

Six photographs in `agnes-chee-fondazione-prada-photos/` — **gitignored, local to this machine
only**. Most design decisions in the rebuild are only justifiable by looking at them. Crop with
`sips -c <h> <w> --cropOffset <y> <x> src.jpg --out crop.jpg` (originals are 3072×4096);
`PROGRESS.md` lists the load-bearing crops and their coordinates.

## Known issues

- **Nothing rotates.** The real installation's mushrooms turn slowly on motors; neither track animates.
- **Blender track is stale** — see above. Also: `SPOT_MESH` is assigned twice (the first mesh is
  orphaned), and the 720-segment gill revolve carrying a 240-period sine is only 3 samples per gill.
- `README.md` is a single title line.
