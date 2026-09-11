# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A procedural, code-only recreation of Carsten Höller's *Upside Down Mushroom Room* — giant fly-agaric
sculptures hanging from the ceiling of a gallery, inverted: the stipe runs *up* to the ceiling, the
convex red cap faces the *floor*, and the gills face the *ceiling*. There is no build system, package
manager, dependency manifest, or test suite. Each file is a self-contained script/page that generates
the entire scene from scratch at runtime — no imported meshes, no image assets, no `node_modules`.

Two independent implementations of the same subject live side by side:

- **Blender/Cycles scripts** (`blender-mushroom-room.py`, `blender-mushroom-room2.py`) — offline path-traced stills.
- **three.js web pages** (`mushroom-room-fp.html`, `mushroom-room-fp2.html`) — real-time, walkable, in-browser.

### What `2` actually means (read this before editing)

`2` means "later iteration of that one file", **not** "second half of a matched pair". The two tracks
are at different generations and the naming hides it:

| File | Status |
| --- | --- |
| `blender-mushroom-room2.py` | **Byte-identical** to `blender-mushroom-room.py` (`md5 cd2ed624…`). The `2` is a copy, not a revision. |
| `mushroom-room-fp2.html` | A genuine, substantial revision of `mushroom-room-fp.html`. |

So `blender-*2.py` is generationally **behind** `mushroom-room-fp2.html`, not parallel to it:

| | Blender (both files) & `fp.html` | `fp2.html` |
| --- | --- | --- |
| Room | 26 × 18 × 10 m (invented hall) | 14 × 7 × 4.6 m (Fondazione Prada figures) |
| Mushrooms | 12, one generic stage | 9, four developmental stages (`button`/`hemispherical`/`convex`/`mature`) |
| Lighting key | ceiling softboxes, bright white hall | **inverted** — floor luminaire slits key the scene, slate-grey ceiling, caps lit from below |
| Cap surface | flat red material + sphere "spots" | canvas-painted `makeCapTexture()` + instanced pyramidal warts |
| Gills | uniform sine corrugation | alternating full lamellae / short lamellulae |
| Stipe | straight, noise-lumped | `bend` curvature, volva + annulus (partial veil) |
| Player | stand only | stand + crouch, auto-duck driven by real cap-underside clearance |

When asked to improve "the room," **ask which track** (Blender stills, web walkthrough, or both). For
the web track edit `mushroom-room-fp2.html`. For the Blender track, note that editing
`blender-mushroom-room2.py` silently diverges it from its identical twin — decide explicitly whether
to also update `blender-mushroom-room.py` or to collapse the duplicate.

## Running things

**Blender scripts** — need a local Blender (3.6 LTS – 4.x); nothing else:

```bash
blender --background --python blender-mushroom-room2.py
blender --background --python blender-mushroom-room2.py -- --samples 64 --res 1280
blender --background --python blender-mushroom-room2.py -- --no-render     # geometry only, seconds not minutes
```

Writes `mushroom_room.blend` and `mushroom_room.png` next to the script. The script resets from factory
settings, so re-running is safe. `--no-render` is the fast iteration loop when changing geometry —
open the `.blend` to inspect. Rendering falls back CYCLES → EEVEE automatically. Cycles is pinned to
**CPU** (`compute_device_type = 'NONE'`); switch to `'OPTIX'`/`'CUDA'` for GPU.

**HTML/three.js pages** — no build step:

```bash
python3 -m http.server 8000   # then open http://localhost:8000/mushroom-room-fp2.html
```

three.js and its addons come from an `importmap` pinned to `three@0.169.0` on `unpkg.com`, so an
internet connection is required. Opening via `file://` also works since there is no fetch of local
assets, but serving is safer for module resolution.

There is no linter, formatter, or test command. Validate Blender changes by running with `--no-render`
and inspecting the `.blend`; validate web changes by loading the page in a browser and walking the
aisle. Mind the perf budget: `fp2.html` builds ~1–3 M triangles of gills at desktop `Q`.

## Architecture

Both tracks reimplement the *same* geometry independently. A fix to the underlying math — the
spherical-bowl cap profile, the stipe flare, the gill offset — generally needs porting to both
`cap_geometry()` (Python) and the inline cap block in `makeMushroom()` (JS) to keep them consistent,
unless the change is deliberately track-specific.

**Coordinate conventions differ and are easy to get wrong:**

- Blender is **Z-up**; mushrooms are parented to an empty at `z = ROOM_H` and grow downward in −Z.
- three.js is **Y-up**; `makeMushroom` works in a local frame with `y = 0` at the ceiling, the cap rim
  at `y = -stemH`, and the cap apex — the lowest point — at `y = -stemH - capH`.
- In both, the cap profile is generated **rim-at-origin, apex-negative**, then translated down the stipe.

### Blender scripts

Single flat script, top to bottom, no imports beyond `bpy`/`bmesh`/`mathutils`/stdlib:

1. **Config block** (`SEED`, `ROOM_W/D/H`, `SAMPLES`, `RES_X/Y`) — CLI args after `--` override it.
2. **Helpers**: `mat_simple()` builds a Principled BSDF tolerant of 3.x/4.x socket-name differences;
   `new_object()`/`revolve()` build meshes from raw vertex/face data (`revolve()` sweeps a
   `(radius, z)` profile around Z); `radial_displace()` and `rough_displace()` perturb vertices
   sinusoidally for gill corrugation and stem lumpiness.
3. **Mushroom generation**: `cap_geometry(R, H)` derives a spherical bowl from target half-width `R`
   and depth `H` (sphere centre `y0 = (R² − H²)/2H`, radius `Rs = y0 + H`); `build_mushroom()`
   assembles stem + cap + gills + scattered veil spots + ceiling collar under one parented empty.
   The `MUSHROOMS` list of `(x, y, R, H, stem_h, stem_r, tilt_x, tilt_y)` tuples is the primary
   layout lever.
4. **Room shell, floor light strips, two dark figures, area lights, camera, render settings** follow
   in sequence, each a self-contained block.

### three.js pages

Single file, numbered `/* == N. TITLE == */` banners. Section numbers differ between the two files —
read the banners in the target file first. `fp2.html`:

| § | Contents |
| --- | --- |
| 0 | Device/quality — `IS_TOUCH`, geometry density scalar `Q`, `USE_BLOOM` |
| 1 | Utilities — `mulberry32` seeded RNG, sine-sum `noise2`, `revolve()` (JS analogue of the Blender helper; arc-length V coords) |
| 2 | Room envelope constants (`ROOM = {w:14, d:7, h:4.6}`) |
| 3 | Renderer/scene/camera — ACES tone mapping, `FogExp2`, FOV derived from a 24 mm-equivalent 74° *horizontal* FOV, low-intensity `RoomEnvironment` IBL |
| 4 | Room shell — white plaster walls, polished floor, **slate-grey ceiling** |
| 5 | Floor luminaire slits — 11 transverse emissive slots; the installation's primary key |
| 6 | Mushroom materials — `makeCapTexture()` paints a canvas (blotchy pigment + gold marginal striations) instead of loading an image |
| 7 | `makeMushroom(cfg)` — stipe, pileus, hymenium, warts, annulus, volva/collar; returns `{group, stemCollider, dome}` |
| 8 | The installation — `S` stage-proportion table + `PLAN` placement array (the `MUSHROOMS` equivalent) |
| 9 | Lighting — hemisphere (dark cool above, warm below) + point lights in the slits |
| 10 | Post — `EffectComposer` + `UnrealBloomPass` + `OutputPass`, desktop only |
| 11 | Player — eye 1.62 m standing / 0.92 m crouched |
| 12 | Walk · collide · duck — `clearanceUnder(dome, x, z)` evaluates the real cap underside so the player auto-ducks under low caps |
| 13 | Render loop |
| 14 | HUD wiring — start panel, touch joystick, hint bar |

Route all new geometry generation through `Q` so touch devices stay performant, and prefer
`InstancedMesh` for anything scattered (the warts already are).

## Known issues / rough edges

Confirmed by reading, not speculation — worth fixing when touching nearby code:

- **`fp2.html:428-430` — dead/degenerate gill code.** `a` is computed only to be tested against `0`;
  its `Math.sin((th*FINS/FINS)*Math.PI*2*FINS/FINS + finIndex*0)` reduces to `sin(2π·th)`, which zeroes
  the gill displacement along a handful of arbitrary angles, cutting flat radial seams across the
  hymenium. The `d = a === 0 ? 0 : …` guard should just be `d = amp * (isLong ? 1 : 0.62) * fade * wave`.
- **`fp2.html:764,771` — `ShiftRight` is bound to both duck and run**, so right-shift produces a
  duck-run. Probably unintended.
- **No shadows in either web page** — `renderer.shadowMap` is never enabled and nothing casts. With a
  floor-keyed scene this is the largest single realism gap: no contact shadow under the stipes, no
  occlusion in the gills.
- **Nothing rotates.** The real installation's mushrooms turn slowly on motors; neither track animates.
- **Blender: `SPOT_MESH` is assigned twice**; the first `bpy.data.meshes.new("SpotProto")` is orphaned
  immediately.
- **Blender gills are expensive and alias** — a 720-segment revolve carrying a 240-period sine is
  only 3 samples per gill.
- **`README.md` is a single title line**, and there is no `.gitignore`, so `mushroom_room.blend` /
  `mushroom_room.png` land untracked in the repo root after every Blender run.
