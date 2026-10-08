"""Castle TIME modelling kit: medieval buildings, castle parts, nature and props (all procedural)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
from lib import *

# shared materials ('T_' = textured triplanar in Godot, colour = tint)
def mats():
    g = globals()
    g.update(dict(
        STONE=M('T_stone', '#ffffff'), STONE_D=M('T_stone#dark', '#9a948c'), STONE_W=M('T_stone#warm', '#e8dcc6'),
        COBBLE=M('T_cobble', '#ffffff'), FLAG=M('T_flag', '#ffffff'), DIRT=M('T_dirt', '#ffffff'), GRASS=M('T_grass', '#ffffff'),
        PLASTER=M('T_plaster', '#ffffff'), PLASTER_Y=M('T_plaster#ochre', '#f0d9a8'), TIMBER=M('T_timber', '#ffffff'),
        WOOD=M('T_wood', '#ffffff'), WOOD_D=M('T_wood#dark', '#8a7a6a'), THATCH=M('T_thatch', '#ffffff'), TILE=M('T_rooftile', '#ffffff'),
        HAY=M('T_hay', '#ffffff'), BARK=M('T_bark', '#ffffff'), LEAVES=M('T_leaves', '#ffffff'), LEAVES2=M('T_leaves#autumn', '#e6b070'),
        RUG=M('T_rug', '#ffffff'), IRON=M('iron', '#2e2e33', 0.45, 0.85), GOLD=M('gold', '#e0b23a', 0.25, 1.0),
        DARK=M('dark', '#0a0908', 0.95), GLASS=M('glass_lead', '#3a4a52', 0.15, 0.3), CLOTH_R=M('T_cloth#red', '#a3262a'),
        CLOTH_Y=M('T_cloth#yellow', '#e0b23a'), CLOTH_B=M('T_cloth#blue', '#2c4a7a'), CLOTH_G=M('T_cloth#green', '#4e6233'),
        CLOTH_W=M('T_cloth#white', '#e8e2d0'), ROPE=M('rope', '#b8a07a', 0.95), WATER=M('W_water', '#2a4a50', 0.05),
        FIRE=M('fire', '#ffaa33', 0.5, emit=(1.0, 0.45, 0.08), estr=4.0), CANDLE=M('candle', '#efe6c8', 0.6),
        SOOT=M('soot', '#1a1614', 0.95), PARCH=M('T_parchment', '#ffffff'), CREST=M('D_crest', '#ffffff', 0.8),
        MUD=M('T_dirt#mud', '#6a5a48'), STRAW=M('T_hay#straw', '#ffffff')))
R = random.Random(1283)

def rot2(v, a):
    c, s = math.cos(a), math.sin(a); return Vector((v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2] if len(v) > 2 else 0))

class Part:
    """collects objects for one region; join() merges them into a single multi-material mesh"""
    def __init__(self, name): self.name = name; self.objs = []
    def add(self, *os_):
        for o in os_:
            if isinstance(o, (list, tuple)): self.add(*o)
            elif o is not None: self.objs.append(o)
        if len(self.objs) > 120:   # keep the scene small: Blender ops get slow with thousands of objects
            self.objs = [join(self.name + '_acc', self.objs)]
            import lib as _l; _l.compact_cols()
        return os_[0] if len(os_) == 1 else os_
    def join(self):
        if not self.objs: return None
        o = join(self.name, self.objs); self.objs = []; return o

def place(objs, x, y, a=0.0, z=0.0):
    """rotate (deg) about origin then move a list of objects"""
    m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(a), 4, 'Z')
    for o in objs: o.matrix_world = m @ o.matrix_world
    return objs

def apply_all(objs):
    select(objs); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# ---------------------------------------------------------------- roofs & houses
def gable_roof(w, d, h, z, m, over=0.5, thick=0.25):
    """roof ridge along Y. returns objects (two slabs + gable ends filled by caller)"""
    hw = w / 2 + over; L = d + over * 2; slope = math.atan2(h, w / 2); sl = math.hypot(w / 2 + over, h + over * math.tan(slope))
    out = []
    for sx in (1, -1):
        o = box(sl, L, thick, (sx * (w / 4 + over / 2), 0, z + h / 2 - over * math.tan(slope) / 2), m, rot=(0, -sx * slope, 0))
        out.append(o)
    ridge = box(0.3, L, 0.3, (0, 0, z + h + 0.05), m, rot=(0, math.pi / 4, 0)); out.append(ridge)
    return out

def gable_wall(w, h, z, y, m, thick=0.3):
    return extrude_poly([(-w / 2, z), (w / 2, z), (0, z + h)], thick, m, loc=(0, y, 0))

def window(x, y, z, w, h, a, m_frame, shutters=None, thick=0.3):
    """flat dark window with frame (and optional open shutters) on a wall facing angle a (deg, 0 = -Y)"""
    objs = [box(w, 0.06, h, (0, -thick / 2 - 0.02, 0), DARK)]
    objs += [box(w + 0.16, 0.12, 0.1, (0, -thick / 2 - 0.05, -h / 2 - 0.03), m_frame), box(w + 0.1, 0.1, 0.08, (0, -thick / 2 - 0.05, h / 2 + 0.03), m_frame)]
    objs += [box(0.06, 0.08, h, (0, -thick / 2 - 0.05, 0), m_frame)]
    if shutters:
        for sx in (1, -1): objs.append(box(w / 2, 0.05, h, (sx * (w * 0.75 + 0.06), -thick / 2 - 0.08, 0), shutters, rot=(0, 0, sx * 0.35)))
    for o in objs: o.location = rot2(o.location, math.radians(a)) + Vector((x, y, z)); o.rotation_euler.z += math.radians(a)
    return objs

def door_mesh(w, h, m, studs=True):
    objs = [box(w, 0.12, h, (0, 0, h / 2), m)]
    for k in range(int(w / 0.22)): objs.append(box(0.03, 0.14, h - 0.1, (-w / 2 + 0.11 + k * 0.22, 0, h / 2), WOOD_D))
    for z in (0.5, h - 0.5): objs.append(box(w - 0.1, 0.16, 0.08, (0, 0, z), IRON))
    objs.append(tor(0.07, 0.015, (w * 0.3, -0.1, h * 0.5), IRON, rot=(math.pi / 2, 0, 0), maj=10, mn=5))
    return objs

def house(P, x, y, w, d, a=0, floors=2, style='timber', roof='thatch', door_side=1, seed=0, col=True, sign=None):
    """medieval town house. local frame: front faces -Y (door). a = rotation deg."""
    r = random.Random(seed); objs = []; fh = 2.8; H = floors * fh
    wall_m = r.choice([PLASTER, PLASTER, PLASTER_Y]) if style == 'timber' else STONE_W
    base_m = STONE_D
    objs.append(box(w, d, 0.6, (0, 0, 0.3), base_m, bev=0.04))           # plinth
    objs.append(box(w - 0.04, d - 0.04, H - 0.6, (0, 0, 0.6 + (H - 0.6) / 2), wall_m))
    if style == 'timber':                                                 # timber framing on long faces
        for side in (-1, 1):
            yy = side * (d / 2 + 0.03)
            for k in range(int(w / 1.4) + 1):
                xx = -w / 2 + 0.1 + k * (w - 0.2) / max(1, int(w / 1.4)); objs.append(box(0.18, 0.08, H - 0.6, (xx, yy, 0.6 + (H - 0.6) / 2), TIMBER))
            for f in range(floors + 1): objs.append(box(w + 0.1, 0.1, 0.2, (0, yy, 0.6 + f * (H - 0.6) / floors), TIMBER))
            for k in range(int(w / 1.4)):
                xx = -w / 2 + 0.1 + (k + 0.5) * (w - 0.2) / max(1, int(w / 1.4))
                if r.random() < 0.6: objs.append(box(0.14, 0.07, 1.9, (xx, yy, 0.6 + fh * 1.5 - 0.2), TIMBER, rot=(0, (0.6 if k % 2 else -0.6), 0)))
        for side in (-1, 1):
            xx = side * (w / 2 + 0.03)
            for yy in (-d / 2 + 0.1, d / 2 - 0.1, 0): objs.append(box(0.08, 0.18, H - 0.6, (xx, yy, 0.6 + (H - 0.6) / 2), TIMBER))
    # gables + roof
    rh = d * 0.5 if roof == 'thatch' else d * 0.38
    for side in (-1, 1):
        gw = gable_wall(d - 0.04, rh, H, 0, wall_m); gw.rotation_euler.z = math.pi / 2; gw.location = (side * (w / 2 - 0.15), 0, 0); objs.append(gw)
    objs.append(box(w, d, 0.2, (0, 0, H + 0.1), TIMBER))
    rf = gable_roof(d, w, rh, H, THATCH if roof == 'thatch' else TILE, over=0.55, thick=0.45 if roof == 'thatch' else 0.22)
    for o in rf: o.rotation_euler.z += math.pi / 2; o.location = Vector((-o.location.y, o.location.x, o.location.z))  # ridge along X
    objs += rf
    # chimney
    if r.random() < 0.7:
        cx = r.uniform(-w / 3, w / 3); objs.append(box(0.7, 0.7, rh + 1.4, (cx, d * 0.15, H + rh / 2 + 0.6), STONE_D, bev=0.03))
        objs.append(box(0.85, 0.85, 0.15, (cx, d * 0.2, H + rh + 1.3), STONE_D))
    # door + windows on the front (-Y)
    dx = r.uniform(-w / 4, w / 4)
    dm = door_mesh(1.1, 2.2, WOOD); [setattr(o, 'location', o.location + Vector((dx, -d / 2 - 0.02, 0.55))) for o in dm]; objs += dm
    objs.append(box(1.4, 0.2, 0.2, (dx, -d / 2 - 0.05, 2.85), TIMBER))
    for f in range(floors):
        for k in range(max(1, int(w / 2.6))):
            wx = -w / 2 + (k + 0.5) * w / max(1, int(w / 2.6))
            if f == 0 and abs(wx - dx) < 1.3: continue
            objs += window(wx, -d / 2, 0.6 + f * fh + 1.5, 0.75, 0.95, 0, TIMBER, shutters=r.choice([WOOD, CLOTH_G, CLOTH_B, CLOTH_R]) if r.random() < 0.6 else None)
        for k in range(max(1, int(d / 3))):
            wy = -d / 2 + (k + 0.5) * d / max(1, int(d / 3))
            objs += window(-w / 2, wy, 0.6 + f * fh + 1.5, 0.6, 0.85, -90, TIMBER)
            objs += window(w / 2, wy, 0.6 + f * fh + 1.5, 0.6, 0.85, 90, TIMBER)
    if sign:
        objs.append(box(0.08, 1.4, 0.08, (dx + 1.3, -d / 2 - 0.7, 3.4), IRON))
        objs.append(box(1.2, 0.08, 0.7, (dx + 1.3, -d / 2 - 1.15, 2.95), M('D_' + sign, '#ffffff', 0.8), rot=(0, 0, math.pi / 2)))
    if r.random() < 0.5:   # flower box / barrel by the door
        objs.append(cyl(0.35, 0.8, (dx + 1.2 * (1 if r.random() < .5 else -1), -d / 2 - 0.5, 0.4), WOOD_D, v=12))
    place(objs, x, y, a); P.add(objs)
    if col: colbox(w + 0.1, d + 0.1, H + rh, (x, y, (H + rh) / 2), (0, 0, math.radians(a)))

# ---------------------------------------------------------------- nature
def tree(P, x, y, s=1.0, kind='oak', seed=0, col=True):
    r = random.Random(seed); objs = []
    th = (3.2 if kind == 'oak' else 6.0) * s
    tr = cyl(0.28 * s, th, (0, 0, th / 2), BARK, v=10, r2=0.18 * s); objs.append(tr)
    if kind == 'oak':
        for k in range(5):
            a = k / 5 * 6.28 + r.random(); rr = r.uniform(1.2, 1.9) * s
            objs.append(sph(rr, (math.cos(a) * 1.1 * s, math.sin(a) * 1.1 * s, th + r.uniform(0.2, 1.4) * s), LEAVES if r.random() < 0.8 else LEAVES2, seg=10, rings=7))
        objs.append(sph(1.9 * s, (0, 0, th + 1.6 * s), LEAVES, seg=12, rings=8))
        for k in range(3):
            a = k * 2.1 + r.random(); objs.append(cyl(0.1 * s, 1.6 * s, (math.cos(a) * 0.5 * s, math.sin(a) * 0.5 * s, th * 0.85), BARK, rot=(math.cos(a) * 0.9, -math.sin(a) * 0.9, 0), v=6))
    else:  # cypress (Tuscany!)
        objs.append(cyl(1.0 * s, 7.5 * s, (0, 0, th * 0.35 + 3.75 * s), LEAVES, v=10, r2=0.05))
        objs.append(sph(1.05 * s, (0, 0, th * 0.35 + 0.6 * s), LEAVES, s=(1, 1, 1.2), seg=10, rings=6))
    place(objs, x, y, r.uniform(0, 360)); P.add(objs)
    if col: colbox(0.6 * s, 0.6 * s, th + 2, (x, y, (th + 2) / 2))

def rock(P, x, y, s=1.0, seed=0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=s, location=(x, y, s * 0.3)); o = act()
    r = random.Random(seed)
    for v in o.data.vertices: v.co *= r.uniform(0.75, 1.15); v.co.z *= 0.7
    setmat(o, STONE_D); smooth(o, 30); P.add(o)

def bush(P, x, y, s=1.0, seed=0):
    r = random.Random(seed)
    for k in range(3): P.add(sph(r.uniform(0.6, 0.9) * s, (x + r.uniform(-.5, .5) * s, y + r.uniform(-.5, .5) * s, 0.5 * s), LEAVES, seg=8, rings=6))

def grass_tufts(P, x0, y0, x1, y1, n, seed=0, m=None):
    r = random.Random(seed)
    for i in range(n):
        x, y = r.uniform(x0, x1), r.uniform(y0, y1)
        P.add(cyl(0.14, 0.4, (x, y, 0.15), m or LEAVES, v=5, r2=0.0))

# ---------------------------------------------------------------- farm & town props
def fence(P, p0, p1, h=1.1, post=2.0, colh=1.3):
    p0 = V3(p0); p1 = V3(p1); d = p1 - p0; L = d.length; a = math.atan2(d.y, d.x); n = max(1, int(L / post))
    for k in range(n + 1):
        q = p0 + d * (k / n); P.add(box(0.14, 0.14, h + 0.2, (q.x, q.y, (h + 0.2) / 2 - 0.1), TIMBER, rot=(0, 0, a + 0.1 * math.sin(k * 7))))
    for z in (h * 0.45, h * 0.9):
        c = (p0 + p1) / 2; P.add(box(L, 0.07, 0.12, (c.x, c.y, z), WOOD, rot=(0, 0, a)))
    c = (p0 + p1) / 2; colbox(L, 0.3, colh, (c.x, c.y, colh / 2), (0, 0, a))

def haystack(P, x, y, s=1.0, col=True):
    P.add(sph(1.4 * s, (x, y, 0.9 * s), HAY, s=(1, 1, 1.15), seg=14, rings=9), cyl(0.9 * s, 0.6 * s, (x, y, 2.4 * s), HAY, r2=0.1, v=12))
    if col: colbox(2.2 * s, 2.2 * s, 2.4 * s, (x, y, 1.2 * s))

def hay_bale(x, y, z=0.0, a=0):
    o = box(1.2, 0.6, 0.55, (x, y, z + 0.275), HAY, rot=(0, 0, math.radians(a)), bev=0.06); return [o, box(1.21, 0.04, 0.56, (x, y, z + 0.275), ROPE, rot=(0, 0, math.radians(a)))]

def barrel(x, y, z=0.0, s=1.0, m=None):
    o = lathe([(0.0, 0), (0.3 * s, 0), (0.36 * s, 0.25 * s), (0.38 * s, 0.45 * s), (0.36 * s, 0.65 * s), (0.3 * s, 0.9 * s), (0.0, 0.9 * s)], m or WOOD_D, 'barrel', seg=16, loc=(x, y, z))
    hoops = [tor(r_ * s, 0.018 * s, (x, y, z + zz * s), IRON, maj=16, mn=4) for r_, zz in ((0.33, 0.12), (0.375, 0.32), (0.375, 0.58), (0.33, 0.78))]
    return [o] + hoops

def crate(x, y, z=0.0, s=1.0, a=0):
    o = [box(0.9 * s, 0.9 * s, 0.9 * s, (0, 0, 0.45 * s), WOOD, bev=0.02)]
    for sx in (1, -1):
        o.append(box(0.94 * s, 0.94 * s, 0.1 * s, (0, 0, (0.45 + sx * 0.38) * s), WOOD_D))
    o.append(box(0.94 * s, 0.1 * s, 0.94 * s, (0, 0, 0.45 * s), WOOD_D, rot=(0, 0.78, 0)))
    return place(o, x, y, a, z)

def cart(P, x, y, a=0, load='hay', col=True):
    o = [box(1.6, 2.8, 0.12, (0, 0, 0.8), WOOD)]
    for sx in (1, -1): o.append(box(0.08, 2.8, 0.5, (sx * 0.78, 0, 1.05), WOOD_D))
    for yy in (1.4, -1.4): o.append(box(1.6, 0.08, 0.5, (0, yy, 1.05), WOOD_D))
    for sx in (1, -1):
        o.append(cyl(0.6, 0.12, (sx * 0.95, -0.3, 0.6), WOOD_D, rot=(0, math.pi / 2, 0), v=16))
        o.append(tor(0.58, 0.04, (sx * 0.95, -0.3, 0.6), IRON, rot=(0, math.pi / 2, 0), maj=20, mn=4))
        o.append(box(0.08, 2.4, 0.08, (sx * 0.45, -2.6, 0.72), WOOD_D, rot=(0.12, 0, 0)))
    if load == 'hay': o.append(sph(1.0, (0, 0, 1.3), HAY, s=(0.8, 1.35, 0.5), seg=12, rings=8))
    elif load == 'barrels': o += barrel(0.35, 0.6, 0.86) + barrel(-0.35, -0.4, 0.86)
    elif load == 'cabbage':
        for k in range(14): o.append(sph(0.16, ((k % 4) * 0.34 - 0.5, (k // 4) * 0.5 - 0.8, 1.0), M('cabbage', '#6f9e3a', 0.8), seg=8, rings=6))
    P.add(place(o, x, y, a))
    if col: colbox(2.0, 3.0, 1.6, (x, y, 0.8), (0, 0, math.radians(a)))

def well(P, x, y, col=True):
    o = [lathe([(1.0, 0), (1.05, 0.9), (0.85, 0.9), (0.8, -0.2)], STONE, 'well', seg=20)]
    o.append(cyl(0.82, 0.05, (0, 0, 0.3), WATER, v=20))
    for sx in (1, -1): o.append(box(0.15, 0.15, 2.4, (sx * 0.95, 0, 1.2), TIMBER))
    o.append(box(2.2, 0.12, 0.12, (0, 0, 2.3), TIMBER)); o.append(cyl(0.12, 1.5, (0, 0, 2.0), WOOD_D, rot=(0, math.pi / 2, 0), v=10))
    o.append(cyl(0.01, 1.3, (0, 0, 1.3), ROPE, v=4)); o += barrel(0, 0, 0.5, 0.45)
    rf = gable_roof(2.2, 1.6, 0.8, 2.35, TILE, over=0.25, thick=0.12)
    for q in rf: q.rotation_euler.z += math.pi / 2; q.location = Vector((q.location.y, q.location.x, q.location.z))
    o += rf; P.add(place(o, x, y)); 
    if col: colbox(2.2, 2.2, 1.0, (x, y, 0.5))

def stall(P, x, y, a=0, cloth=None, goods='veg', col=True):
    cloth = cloth or CLOTH_R; o = [box(2.6, 1.2, 0.1, (0, 0, 0.95), WOOD), box(2.6, 0.08, 0.9, (0, -0.56, 0.48), WOOD_D)]
    for sx in (1, -1):
        for sy in (1, -1): o.append(box(0.1, 0.1, 2.4 if sy > 0 else 2.1, (sx * 1.25, sy * 0.55, 1.2 if sy > 0 else 1.05), TIMBER))
    for k in range(6):  # striped awning
        o.append(box(2.8 / 6, 1.7, 0.04, (-1.4 + (k + 0.5) * 2.8 / 6, -0.1, 2.25), cloth if k % 2 == 0 else CLOTH_W, rot=(-0.3, 0, 0)))
    gm = {'veg': [M('cabbage', '#6f9e3a', 0.8), M('carrot', '#e07a2a', 0.7), M('turnip', '#d9c0d0', 0.7)], 'fish': [M('fish', '#9aa8b0', 0.3, 0.4)],
          'bread': [M('bread', '#c8904a', 0.8)], 'pots': [M('pot', '#a0522d', 0.7)]}[goods]
    for k in range(10): o.append(sph(0.13, (-1.1 + (k % 5) * 0.5, -0.25 + (k // 5) * 0.35, 1.08), gm[k % len(gm)], s=(1, 1, 0.8 if goods != 'fish' else 0.4), seg=8, rings=6))
    o += crate(0.9, 0.95, 0, 0.7, 10) + barrel(-1.0, 0.9, 0, 0.8)
    P.add(place(o, x, y, a))
    if col: colbox(2.8, 1.4, 1.2, (x, y, 0.6), (0, 0, math.radians(a)))

def trough(x, y, a=0):
    o = [box(2.0, 0.6, 0.5, (0, 0, 0.25), WOOD_D, bev=0.03), box(1.85, 0.45, 0.05, (0, 0, 0.42), WATER)]
    return place(o, x, y, a)

def torch_bracket(x, y, z, a=0):
    o = [box(0.06, 0.3, 0.06, (0, 0.15, 0), IRON), cyl(0.05, 0.5, (0, 0.3, 0.15), WOOD_D, v=6), cyl(0.08, 0.15, (0, 0.3, 0.42), FIRE, v=6, r2=0.02)]
    return place(o, x, y, a, z)

def bench(x, y, a=0, L=2.0):
    o = [box(L, 0.4, 0.08, (0, 0, 0.45), WOOD)]
    for sx in (1, -1): o.append(box(0.08, 0.36, 0.45, (sx * (L / 2 - 0.2), 0, 0.22), WOOD_D))
    return place(o, x, y, a)

def table(x, y, a=0, L=2.4, W=0.9):
    o = [box(L, W, 0.1, (0, 0, 0.82), WOOD, bev=0.02)]
    for sx in (1, -1):
        for sy in (1, -1): o.append(box(0.12, 0.12, 0.8, (sx * (L / 2 - 0.15), sy * (W / 2 - 0.12), 0.4), WOOD_D))
    return place(o, x, y, a)

def banner(x, y, z, a=0, m=None, w=1.2, h=3.0):
    o = [box(w + 0.3, 0.08, 0.08, (0, 0, h / 2 + 0.1), WOOD_D), box(w, 0.04, h, (0, 0, 0), m or CLOTH_R)]
    o.append(cyl(w * 0.32, 0.03, (0, -0.04, h * 0.12), CREST, rot=(math.pi / 2, 0, 0), v=20))
    o.append(extrude_poly([(-w / 2, -h / 2), (0, -h / 2 - 0.5), (w / 2, -h / 2)], 0.04, m or CLOTH_R))
    return place(o, x, y, a, z)

# ---------------------------------------------------------------- castle
def V3(p): return Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0))
def merlons(P, p0, p1, z, t=1.0, mh=1.0, mw=1.0, gap=1.0, m=None):
    p0 = V3(p0); p1 = V3(p1); d = p1 - p0; L = d.length; a = math.atan2(d.y, d.x); n = int(L / (mw + gap))
    for k in range(n):
        q = p0 + d * ((k + 0.5) / n); P.add(box(mw, t, mh, (q.x, q.y, z + mh / 2), m or STONE, rot=(0, 0, a), bev=0.03))

def curtain(P, p0, p1, h=10, t=3.0, walk=True, col=True, m=None, merl=True):
    p0 = V3(p0); p1 = V3(p1); d = p1 - p0; L = d.length; a = math.atan2(d.y, d.x); c = (p0 + p1) / 2
    P.add(box(L, t, h, (c.x, c.y, h / 2), m or STONE, rot=(0, 0, a)))
    P.add(box(L, t + 0.6, 1.2, (c.x, c.y, 0.6), STONE_D, rot=(0, 0, a)))  # batter
    n = Vector((-math.sin(a), math.cos(a), 0))
    if merl:
        for side in (1, -1): merlons(P, p0 + n * side * (t / 2 - 0.35), p1 + n * side * (t / 2 - 0.35), h, 0.7, 1.1, 1.0, 0.9, m)
    if col: colbox(L, t, h, (c.x, c.y, h / 2), (0, 0, a))

def round_tower(P, x, y, r, h, roof=True, m=None, col=True, cone=None):
    P.add(cyl(r, h, (x, y, h / 2), m or STONE, v=28), cyl(r + 0.35, 1.4, (x, y, 0.7), STONE_D, v=28, r2=r + 0.1))
    P.add(cyl(r + 0.45, 0.6, (x, y, h - 0.3), STONE_D, v=28))  # corbel ring
    for k in range(12):
        a = k / 12 * 6.283; P.add(box(1.0, 0.7, 1.1, (x + math.cos(a) * (r + 0.1), y + math.sin(a) * (r + 0.1), h + 0.55), m or STONE, rot=(0, 0, a + math.pi / 2), bev=0.03))
    for k in range(4):   # arrow slits
        a = k / 4 * 6.283 + 0.4
        for zz in (h * 0.35, h * 0.7): P.add(box(0.18, 0.2, 1.4, (x + math.cos(a) * r, y + math.sin(a) * r, zz), DARK, rot=(0, 0, a + math.pi / 2)))
    if roof:
        P.add(cyl(r + 0.6, cone or r * 1.6, (x, y, h + 1.1 + (cone or r * 1.6) / 2), TILE, v=24, r2=0.05))
    if col: colbox(r * 1.8, r * 1.8, h + 1.2, (x, y, (h + 1.2) / 2))
