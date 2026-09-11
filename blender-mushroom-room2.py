# =============================================================================
#  upside_down_mushroom_room.py
#
#  Procedurally rebuilds the exhibit in the reference photo:  giant fly-agaric
#  caps hanging from the ceiling of a bright white hall, corrugated gills on
#  the up-facing side, rough white stems, glowing strips recessed in the floor
#  and two dark standing figures.
#
#  USAGE
#  -----
#    blender --background --python upside_down_mushroom_room.py
#    blender --background --python upside_down_mushroom_room.py -- --samples 64 --res 1280
#    blender --background --python upside_down_mushroom_room.py -- --no-render
#
#  Writes  ./mushroom_room.blend  and  ./mushroom_room.png  next to the script.
#  Targets Blender 3.6 LTS – 4.x (CYCLES, falls back to EEVEE).
# =============================================================================

import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

# -----------------------------------------------------------------------------
#  CONFIG
# -----------------------------------------------------------------------------
SEED        = 20260911
ROOM_W      = 26.0          # x
ROOM_D      = 18.0          # y
ROOM_H      = 10.0          # z (ceiling height)
SAMPLES     = 128
RES_X, RES_Y = 1920, 1080
DO_RENDER   = True

argv = sys.argv
if "--" in argv:
    a = argv[argv.index("--") + 1:]
    if "--no-render" in a: DO_RENDER = False
    if "--samples" in a:   SAMPLES = int(a[a.index("--samples") + 1])
    if "--res" in a:       RES_X = int(a[a.index("--res") + 1]); RES_Y = int(RES_X * 9 / 16)

random.seed(SEED)
HERE = os.path.dirname(os.path.abspath(bpy.data.filepath or __file__)) if "__file__" in dir() else os.getcwd()

# -----------------------------------------------------------------------------
#  SCENE RESET
# -----------------------------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

# -----------------------------------------------------------------------------
#  HELPERS
# -----------------------------------------------------------------------------
def mat_simple(name, rgb, rough=0.8, metal=0.0, emit=None, emit_str=0.0):
    """Principled material; tolerates 3.x / 4.x socket naming."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    s = bsdf.inputs
    s["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    s["Roughness"].default_value = rough
    s["Metallic"].default_value = metal
    if emit is not None:
        for key in ("Emission Color", "Emission"):
            if key in s:
                s[key].default_value = (emit[0], emit[1], emit[2], 1.0)
                break
        if "Emission Strength" in s:
            s["Emission Strength"].default_value = emit_str
    return m


def new_object(name, verts, faces, material=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate(verbose=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if material:
        me.materials.append(material)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def revolve(profile, segs, name, material=None, smooth=True):
    """profile: list of (radius, z) with z increasing  ->  surface of revolution
       about the world Z axis, normals pointing outward."""
    verts, faces = [], []
    n = len(profile)
    for j in range(n):
        r, z = profile[j]
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for j in range(n - 1):
        for i in range(segs):
            i2 = (i + 1) % segs
            a = j * segs + i
            b = j * segs + i2
            c = (j + 1) * segs + i
            d = (j + 1) * segs + i2
            faces.append((a, b, d, c))
    return new_object(name, verts, faces, material, smooth)


def radial_displace(ob, amp, freq, z_amp=0.0, seed=0.0):
    """Push every vertex in/out radially with a sine corrugation (gills, stems)."""
    me = ob.data
    for v in me.vertices:
        x, y, z = v.co
        r = math.hypot(x, y)
        if r < 1e-6:
            continue
        th = math.atan2(y, x)
        d = amp * math.sin(th * freq)
        v.co.x = x + d * x / r
        v.co.y = y + d * y / r
        if z_amp:
            v.co.z = z + z_amp * math.sin(th * freq * 0.5 + seed)
    me.update()


def rough_displace(ob, amp, scale, seed):
    """Organic lumpiness for the stems."""
    me = ob.data
    for v in me.vertices:
        x, y, z = v.co
        r = math.hypot(x, y)
        if r < 1e-6:
            continue
        th = math.atan2(y, x)
        n = (0.55 * math.sin(th * 2.3 * scale + z * 1.6 + seed) +
             0.30 * math.sin(th * 4.1 * scale - z * 2.4 + seed * 1.7) +
             0.15 * math.sin(th * 7.3 * scale + z * 4.1 + seed * 2.9))
        s = 1.0 + amp * n
        v.co.x = x * s
        v.co.y = y * s
        v.co.z = z + 0.03 * n
    me.update()

# -----------------------------------------------------------------------------
#  MATERIALS
# -----------------------------------------------------------------------------
M_WALL   = mat_simple("Wall_White",   (0.93, 0.925, 0.905), rough=0.95)
M_FLOOR  = mat_simple("Floor_White",  (0.95, 0.945, 0.93),  rough=0.32)
M_CAP    = mat_simple("Cap_Red",      (0.62, 0.115, 0.045), rough=0.62)
M_GILL   = mat_simple("Gills",        (0.90, 0.855, 0.79),  rough=0.80)
M_STEM   = mat_simple("Stem_White",   (0.90, 0.875, 0.83),  rough=0.92)
M_SPOT   = mat_simple("Spot_White",   (0.955, 0.93, 0.885), rough=0.88)
M_BODY   = mat_simple("Figure_Dark",  (0.035, 0.033, 0.040), rough=0.60)
M_GLOW   = mat_simple("Floor_Glow",   (1.0, 0.985, 0.95), rough=1.0,
                      emit=(1.0, 0.97, 0.92), emit_str=14.0)

# -----------------------------------------------------------------------------
#  THE ROOM
# -----------------------------------------------------------------------------
# A simple inward-facing shell: Cycles shades both sides, so a plain box works.
hw, hd = ROOM_W / 2.0, ROOM_D / 2.0
room_verts = [(-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
              (-hw, -hd, ROOM_H), (hw, -hd, ROOM_H), (hw, hd, ROOM_H), (-hw, hd, ROOM_H)]
room_faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
              (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
room = new_object("Room", room_verts, room_faces, M_WALL, smooth=False)
room.data.materials.append(M_FLOOR)     # slot 1 = floor
room.data.materials.append(M_WALL)      # slot 2 = ceiling
for poly in room.data.polygons:
    if poly.index == 0: poly.material_index = 1

# -----------------------------------------------------------------------------
#  MUSHROOMS
# -----------------------------------------------------------------------------
SPOT_MESH = bpy.data.meshes.new("SpotProto")
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=1.0, location=(0, 0, 0))
proto = bpy.context.object
SPOT_MESH = proto.data
bpy.data.objects.remove(proto, do_unlink=True)

CEIL = ROOM_H

def cap_geometry(R, H, rings=26, segs=96):
    """Spherical bowl hanging under the ceiling:
       rim at z = 0, apex (lowest point) at z = -H, half-width R."""
    y0 = (R * R - H * H) / (2.0 * H)          # centre of the sphere above the rim
    Rs = y0 + H
    phi_max = math.atan2(R, y0)
    prof = []
    for j in range(rings + 1):
        phi = phi_max * (j / rings)
        prof.append((Rs * math.sin(phi), y0 - Rs * math.cos(phi)))
    # rolled rim
    rim_t = max(0.05, R * 0.016)
    prof.append((R * 0.985, rim_t * 0.55))
    prof.append((R * 0.905, rim_t * 1.15))
    return prof, y0, Rs, phi_max


def build_mushroom(idx, x, y, R, H, stem_h, stem_r, tilt_x=0.0, tilt_y=0.0):
    phase = random.uniform(0, 20.0)
    parts = []

    # ---- stem -------------------------------------------------------------
    NS = 28
    stem_prof = []
    for j in range(NS + 1):                    # z increasing => outward normals
        u = 1.0 - j / NS                       # 1 = cap end, 0 = ceiling
        z = -stem_h * u
        r = stem_r * (0.80 + 1.05 * math.exp(-u * 5.0) + 0.10 * math.sin(u * 7.0))
        r *= 1.0 + 0.34 * math.exp(-((u - 1.0) / 0.085) ** 2)   # flare into the gills
        stem_prof.append((r, z))
    stem = revolve(stem_prof, 56, "Stem_%02d" % idx, M_STEM)
    rough_displace(stem, 0.085, 1.0, phase)
    parts.append(stem)

    # ---- cap --------------------------------------------------------------
    cap_prof, y0, Rs, phi_max = cap_geometry(R, H, rings=26, segs=96)
    cap = revolve(cap_prof, 96, "Cap_%02d" % idx, M_CAP)
    parts.append(cap)

    # ---- corrugated gills --------------------------------------------------
    off = 0.035 + R * 0.006
    r_in = max(0.05, stem_r * 1.02)
    phi_in = math.asin(min(0.999, r_in / Rs))
    NG = 20
    g_prof = []
    for j in range(NG + 1):
        phi = phi_in + (phi_max - phi_in) * (j / NG)
        r = Rs * math.sin(phi)
        z = y0 - Rs * math.cos(phi)
        nx, nz = math.sin(phi), -math.cos(phi)          # outward normal
        g_prof.append((r - nx * off, z - nz * off))
    gills = revolve(g_prof, 720, "Gills_%02d" % idx, M_GILL)
    radial_displace(gills, min(0.032, 0.006 + R * 0.005), 240.0, z_amp=0.010, seed=phase)
    parts.append(gills)

    # ---- white patches on the downward-facing surface ----------------------
    n_spots = int(random.uniform(16, 30) * min(1.6, R / 2.2))
    for k in range(n_spots):
        t = math.sqrt(random.random())
        th = random.uniform(0, 2 * math.pi)
        phi = phi_max * t
        rr = Rs * math.sin(phi)
        zz = y0 - Rs * math.cos(phi)
        nvec = Vector((math.sin(phi) * math.sin(th), math.sin(phi) * math.cos(th),
                       -math.cos(phi))).normalized()
        # normal in Blender is Z-up: dome points down => -Z component
        loc = Vector((rr * math.sin(th), rr * math.cos(th), zz)) + nvec * 0.012
        s = R * random.uniform(0.028, 0.055) * (1.0 + 0.5 * (1.0 - t))
        ob = bpy.data.objects.new("Spot_%02d_%03d" % (idx, k), SPOT_MESH)
        ob.location = loc
        ob.rotation_mode = 'QUATERNION'
        ob.rotation_quaternion = nvec.to_track_quat('Z', 'Y')
        ob.scale = (s * random.uniform(0.85, 1.25), s * random.uniform(0.85, 1.25), s * 0.34)
        bpy.context.collection.objects.link(ob)
        parts.append(ob)

    # ---- ceiling collar ----------------------------------------------------
    coll = []
    for j in range(11):
        u = j / 10.0
        coll.append((stem_r * (1.85 - 0.75 * u) * (1 + 0.06 * math.sin(u * 22 + phase)), -u * 0.55))
    collar = revolve(coll, 40, "Collar_%02d" % idx, M_STEM)
    parts.append(collar)

    # ---- group everything under one empty and hang it from the ceiling ------
    root = bpy.data.objects.new("Mushroom_%02d" % idx, None)
    root.empty_display_size = 0.5
    bpy.context.collection.objects.link(root)
    root.location = (x, y, CEIL)
    root.rotation_euler = (tilt_x, tilt_y, random.uniform(0, 2 * math.pi))
    for p in parts:
        p.parent = root
    return root


MUSHROOMS = [
    (-6.4, -4.6, 5.30, 0.78, 7.55, 0.62, -0.14,  0.00),
    ( 0.4, -6.6, 2.30, 0.95, 5.60, 0.40,  0.20,  0.00),
    ( 5.6, -4.2, 3.10, 1.05, 6.55, 0.46, -0.08,  0.10),
    (-2.4, -1.2, 0.95, 0.85, 3.15, 0.22,  0.00,  0.00),
    ( 2.3, -2.1, 1.50, 0.72, 4.35, 0.26,  0.16,  0.00),
    ( 8.4, -7.0, 2.10, 0.88, 5.85, 0.34,  0.00,  0.00),
    (-9.6,  2.0, 2.70, 0.92, 6.20, 0.42, -0.22,  0.00),
    (-3.1,  3.6, 1.90, 0.82, 5.00, 0.30,  0.00,  0.00),
    ( 3.6,  4.1, 3.50, 1.02, 6.85, 0.50,  0.07,  0.00),
    ( 9.2,  3.2, 1.65, 0.76, 4.60, 0.28,  0.00,  0.00),
    (-7.4,  8.0, 2.45, 0.86, 6.00, 0.38,  0.00,  0.13),
    ( 6.7,  8.3, 1.35, 0.70, 4.10, 0.24,  0.00,  0.00),
]
for i, args in enumerate(MUSHROOMS):
    build_mushroom(i, *args)

# -----------------------------------------------------------------------------
#  FLOOR LIGHT STRIPS
# -----------------------------------------------------------------------------
strip_w, strip_d = 1.95, 0.42
for col, cx in enumerate((-4.8, 1.6)):
    for i in range(7):
        cy = -6.3 + i * 2.1
        v = [(cx - strip_w / 2, cy - strip_d / 2, 0.012), (cx + strip_w / 2, cy - strip_d / 2, 0.012),
             (cx + strip_w / 2, cy + strip_d / 2, 0.012), (cx - strip_w / 2, cy + strip_d / 2, 0.012)]
        new_object("Strip_%d_%d" % (col, i), v, [(0, 1, 2, 3)], M_GLOW, smooth=False)

# -----------------------------------------------------------------------------
#  TWO DARK FIGURES
# -----------------------------------------------------------------------------
def build_figure(name, x, y, height, rot_z):
    k = height / 1.62
    pts = [(0.20, 0.00), (0.21, 0.30), (0.20, 0.62), (0.19, 0.86),
           (0.22, 0.98), (0.20, 1.12), (0.15, 1.24), (0.11, 1.32),
           (0.10, 1.40), (0.085, 1.46), (0.075, 1.52), (0.03, 1.56)]
    prof = [(r * k, z * k) for (r, z) in pts]
    body = revolve(prof, 24, name, M_BODY)
    body.location = (x, y, 0.0)
    body.rotation_euler = (0, 0, rot_z)
    return body

build_figure("Figure_A", -5.9, -2.5, 1.72, 0.35)
build_figure("Figure_B",  1.1, -1.9, 1.78, -2.6)

# -----------------------------------------------------------------------------
#  LIGHTING
# -----------------------------------------------------------------------------
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.92, 0.915, 0.91, 1.0)
bg.inputs[1].default_value = 1.1

def area_light(name, loc, size, power, rot=(0, 0, 0), color=(1.0, 0.97, 0.93)):
    ld = bpy.data.lights.new(name, type='AREA')
    ld.size = size
    ld.energy = power
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    ob.rotation_euler = rot
    bpy.context.collection.objects.link(ob)
    return ob

# broad ceiling fills (the room is lit almost like a softbox)
for i, (lx, ly) in enumerate([(-7, -5), (0, -3), (7, -5), (-6, 5), (2, 6), (9, 5)]):
    area_light("Ceil_%d" % i, (lx, ly, CEIL - 0.35), 9.0, 1600.0, rot=(math.pi, 0, 0))

# warm kick from the floor strips
for col, cx in enumerate((-4.8, 1.6)):
    area_light("Strip_Light_%d" % col, (cx, 0.0, 0.35), 3.0, 260.0,
               rot=(math.pi, 0, 0), color=(1.0, 0.93, 0.85))

# -----------------------------------------------------------------------------
#  CAMERA — matches the reference framing
# -----------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 24.0
cam_data.sensor_width = 36.0
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (-0.6, -7.9, 1.58)
target = Vector((0.6, 0.0, 3.1))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

# -----------------------------------------------------------------------------
#  RENDER SETTINGS
# -----------------------------------------------------------------------------
scene.render.resolution_x = RES_X
scene.render.resolution_y = RES_Y
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(HERE, "mushroom_room.png")

try:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.cycles.transmission_bounces = 4
    scene.cycles.use_adaptive_sampling = True
    prefs = bpy.context.preferences.addons.get("cycles")
    if prefs:
        prefs.preferences.compute_device_type = 'NONE'   # CPU by default; switch to 'OPTIX'/'CUDA' for GPU
        scene.cycles.device = 'CPU'
except Exception as e:
    print("[mushroom-room] Cycles unavailable (%s); using EEVEE" % e)
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            scene.render.engine = eng
            break
        except Exception:
            pass

# neutral filmic look
for vt in ('AgX', 'Filmic'):
    try:
        scene.view_settings.view_transform = vt
        break
    except Exception:
        pass
scene.view_settings.look = 'None' if scene.view_settings.look == 'None' else scene.view_settings.look

# -----------------------------------------------------------------------------
#  OUTPUT
# -----------------------------------------------------------------------------
blend_path = os.path.join(HERE, "mushroom_room.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("[mushroom-room] saved %s" % blend_path)

if DO_RENDER:
    print("[mushroom-room] rendering %dx%d @ %d samples …" % (RES_X, RES_Y, SAMPLES))
    bpy.ops.render.render(write_still=True)
    print("[mushroom-room] wrote %s" % scene.render.filepath)