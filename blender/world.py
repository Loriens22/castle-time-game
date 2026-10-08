"""Castle TIME - the 1283 world: farm, town of Valtorre, castle, keep interior, clock spire and dungeon.
Blender coords: +Y = north (towards the castle), Z up. Exported to game/assets/models/world.glb.
Named empties 'M-...' are gameplay markers read by game/scripts/world.gd; meshes named 'X-...' are movable parts."""
import bpy, math, sys, os, random
from mathutils import Vector
sys.path.insert(0, os.path.dirname(__file__))
from lib import *
import lib
import kit
from kit import *

reset(); kit.mats(); globals().update({k: v for k, v in kit.__dict__.items() if k.isupper()})
R = random.Random(17)
MARK = []
def mk(name, loc, rot=0, size=None):
    o = marker(name, loc, rot)
    if size: o.scale = size
    MARK.append(o); return o
MOVERS = []
def mover(name, objs):
    o = join('X-' + name, objs if isinstance(objs, list) else [objs]); MOVERS.append(o); return o

# ============================================================ helpers
def room(P, x0, x1, y0, y1, z0, h, wall_m, floor_m, ceil_m=None, t=0.5, gaps=(), ceiling=True, floor=True, skip=()):
    """box room. gaps: (side 'S','N','W','E', centre, width, height). Builds wall pieces around the gaps + collision."""
    if floor:
        solid(x1 - x0 + t * 2, y1 - y0 + t * 2, 0.4, ((x0 + x1) / 2, (y0 + y1) / 2, z0 - 0.2), floor_m); P.add(lib.act())
    if ceiling:
        solid(x1 - x0 + t * 2, y1 - y0 + t * 2, 0.4, ((x0 + x1) / 2, (y0 + y1) / 2, z0 + h + 0.2), ceil_m or wall_m); P.add(lib.act())
    for side in 'SNWE':
        if side in skip: continue
        if side in 'SN':
            y = y0 - t / 2 if side == 'S' else y1 + t / 2; a, b = x0 - t, x1 + t; horiz = True
        else:
            x = x0 - t / 2 if side == 'W' else x1 + t / 2; a, b = y0, y1; horiz = False
        gs = sorted([g for g in gaps if g[0] == side], key=lambda g: g[1]); cur = a
        segs = []
        for g in gs:
            segs.append((cur, g[1] - g[2] / 2, 0, h)); segs.append((g[1] - g[2] / 2, g[1] + g[2] / 2, g[3], h)); cur = g[1] + g[2] / 2
        segs.append((cur, b, 0, h))
        for s0, s1, zz0, zz1 in segs:
            if s1 - s0 < 0.01 or zz1 - zz0 < 0.01: continue
            c = (s0 + s1) / 2; L = s1 - s0; zc = z0 + (zz0 + zz1) / 2; hh = zz1 - zz0
            if horiz: o = solid(L, t, hh, (c, y, zc), wall_m)
            else: o = solid(t, L, hh, (x, c, zc), wall_m)
            P.add(o)

def stairs(P, x0, x1, y0, y1, z0, z1, m, axis='Y', col=True, side_walls=None):
    """straight staircase rising from (y0,z0) to (y1,z1) along axis; collision = ramp"""
    L = abs(y1 - y0); n = max(2, int(abs(z1 - z0) / 0.25)); w = x1 - x0; dirn = 1 if y1 > y0 else -1
    for k in range(n):
        yy = y0 + dirn * (k + 0.5) * L / n; zz = z0 + (k + 1) * (z1 - z0) / n
        hh = abs(zz - min(z0, z1)) + 0.2
        if axis == 'Y': P.add(box(w, L / n + 0.02, hh, ((x0 + x1) / 2, yy, min(z0, z1) + hh / 2 - 0.2), m))
        else: P.add(box(L / n + 0.02, w, hh, (yy, (x0 + x1) / 2, min(z0, z1) + hh / 2 - 0.2), m))
    if col:
        ang = math.atan2(z1 - z0, L) * dirn; Lr = math.hypot(L, z1 - z0)
        if axis == 'Y': colbox(w, Lr, 0.3, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2 - 0.12), (ang, 0, 0))
        else: colbox(Lr, w, 0.3, ((y0 + y1) / 2, (x0 + x1) / 2, (z0 + z1) / 2 - 0.12), (0, -ang, 0))

def pillar(P, x, y, z0, h, r=0.6, m=None):
    P.add(cyl(r, h, (x, y, z0 + h / 2), m or STONE, v=16), box(r * 2.6, r * 2.6, 0.5, (x, y, z0 + 0.25), STONE_D, bev=0.05),
          box(r * 2.6, r * 2.6, 0.5, (x, y, z0 + h - 0.25), STONE_D, bev=0.05))
    colbox(r * 2, r * 2, h, (x, y, z0 + h / 2))

def ground_patch(P, x0, x1, y0, y1, m, z=0.0, col=True, thick=0.4):
    o = box(x1 - x0, y1 - y0, thick, ((x0 + x1) / 2, (y0 + y1) / 2, z - thick / 2 + 0.0), m); P.add(o)
    if col: colbox(x1 - x0, y1 - y0, thick, ((x0 + x1) / 2, (y0 + y1) / 2, z - thick / 2))

def overlay(P, x0, x1, y0, y1, m, z=0.02):
    P.add(plane(x1 - x0, y1 - y0, ((x0 + x1) / 2, (y0 + y1) / 2, z), m))

# ============================================================ TERRAIN (backdrop hills + playable flats)
def terrain():
    P = Part('R-terrain')
    # playable flats (collision)
    ground_patch(P, -30, 30, -140, -4.2, GRASS)                 # farm+town south of moat
    # castle interior ground, with a hole over the dungeon stairwell (x -23.2..-19.8, y 58..70)
    for (gx0, gx1, gy0, gy1) in [(-36, 36, 2.7, 58), (-36, 36, 70, 80), (-36, -23.2, 58, 70), (-19.8, 36, 58, 70)]:
        ground_patch(P, gx0, gx1, gy0, gy1, GRASS)
    ground_patch(P, 30, 70, -140, -4.2, GRASS, col=False); ground_patch(P, -70, -30, -140, -4.2, GRASS, col=False)
    # moat trench + water
    ground_patch(P, -70, 70, -4.2, 2.7, MUD, z=-3.0)
    for yy in (-4.2, 2.7):
        P.add(box(140, 0.6, 3.0, (0, yy, -1.5), STONE_D)); colbox(140, 0.6, 3.0, (0, yy, -1.5))
    P.add(box(140, 6.9, 0.05, (0, -0.75, -1.3), WATER))
    mk('M-tr-moat', (0, -0.75, -2.2), size=(70, 3.4, 0.8))
    # surrounding hills (backdrop, no collision) - rolling grid mesh
    import bmesh
    bm = bmesh.new(); S = 64; ext = 420; vs = []
    for j in range(S + 1):
        row = []
        for i in range(S + 1):
            x = -ext / 2 + ext * i / S; y = -ext / 2 + ext * j / S - 30
            dist = max(0, max(abs(x) - 45, (abs(y + 40) - 130)))
            z = -0.6 + min(1, dist / 60) * (14 + 10 * math.sin(x * 0.03) * math.cos(y * 0.025) + 6 * math.sin(x * 0.07 + y * 0.05))
            if -75 < x < 75 and -150 < y < 95: z = -0.6
            row.append(bm.verts.new((x, y, z)))
        vs.append(row)
    for j in range(S):
        for i in range(S): bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    me = bpy.data.meshes.new('hills'); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new('hills', me); bpy.context.collection.objects.link(o)
    smooth(o, 180); setmat(o, GRASS); P.add(o)
    # bounding walls (invisible) for the outside area
    colbox(1, 140, 8, (-29.5, -72, 4)); colbox(1, 140, 8, (29.5, -72, 4)); colbox(60, 1, 8, (0, -139.5, 4))
    # far cypress rows & vineyards (Tuscany backdrop)
    for k in range(60):
        x = R.uniform(-160, 160); y = R.uniform(-200, 160)
        if abs(x) < 75 and -150 < y < 95: continue
        tree(P, x, y, R.uniform(1.0, 1.6), 'cypress' if R.random() < 0.6 else 'oak', seed=k, col=False)
    for row in range(10):
        for side in (-1, 1):
            P.add(box(30, 0.5, 0.9, (side * 60, -60 + row * 4, 0.0), LEAVES))
    return P.join()

# ============================================================ FARM (start)
def farm():
    P = Part('R-farm')
    overlay(P, -3, 3, -128, -76, DIRT)                                  # road north
    overlay(P, -14, 0, -126, -108, DIRT, 0.015)                         # yard
    # livestock shed: open front faces north, back wall south (player hides behind it)
    sx, sy = -8, -114
    P.add(solid(9, 0.3, 3.0, (sx, sy - 2.6, 1.5), WOOD_D))               # back wall
    for xx in (-4.5, 4.5): P.add(solid(0.3, 5.2, 3.0, (sx + xx, sy, 1.5), WOOD_D))
    for xx in (-4.4, -1.5, 1.5, 4.4): P.add(box(0.25, 0.25, 3.4, (sx + xx, sy + 2.5, 1.7), TIMBER))
    P.add(box(10, 6.4, 0.3, (sx, sy - 0.2, 3.5), THATCH, rot=(0.22, 0, 0))); P.add(box(10, 0.3, 0.3, (sx, sy + 2.6, 3.0), TIMBER))
    for k in range(4): P.add(box(0.2, 5.2, 0.12, (sx - 4.4 + k * 2.9, sy, 3.1), TIMBER, rot=(0.22, 0, 0)))
    for k in range(5): P.add(box(0.06, 0.3, 2.8, (sx - 4 + k * 2, sy - 2.78, 1.4), TIMBER))  # back planks battens
    P.add(*hay_bale(sx - 3, sy - 1.6), *hay_bale(sx - 3, sy - 1.6, 0.55, 8), *hay_bale(sx + 3, sy - 1.7, 0, -5))
    colbox(1.3, 0.7, 1.1, (sx - 3, sy - 1.6, 0.55)); colbox(1.3, 0.7, 0.6, (sx + 3, sy - 1.7, 0.3))
    P.add(trough(sx + 1, sy + 0.5)); colbox(2, 0.6, 0.5, (sx + 1, sy + 0.5, 0.25))
    P.add(box(1.4, 0.12, 1.2, (sx - 1, sy - 0.8, 0.6), WOOD, rot=(0, 0, 0.1)))  # stall divider
    mk('M-start', (sx - 1, sy - 5.5, 0), 0)                              # behind the shed, facing north
    mk('M-cp-farm', (sx - 1, sy - 5.5, 0), 0)
    mk('M-cam-shed1', (sx + 3.5, sy - 9, 1.6)); mk('M-cam-shed2', (sx + 7, sy + 7, 2.2))
    # pen with animals
    fence(P, (2, -122), (18, -122)); fence(P, (18, -122), (18, -104)); fence(P, (18, -104), (8, -104)); fence(P, (4, -104), (2, -104)); fence(P, (2, -104), (2, -122))
    P.add(trough(10, -119, 0)); colbox(2, 0.6, 0.5, (10, -119, 0.25)); overlay(P, 2.2, 17.8, -121.8, -104.2, MUD, 0.03)
    for i, (x, y) in enumerate([(6, -116), (9, -112), (13, -117), (15, -108)]): mk('M-an-pig-%d' % i, (x, y, 0), R.uniform(0, 360))
    for i, (x, y) in enumerate([(5, -108), (12, -107), (14, -113)]): mk('M-an-sheep-%d' % i, (x, y, 0), R.uniform(0, 360))
    for i in range(7): mk('M-an-chicken-%d' % i, (R.uniform(-14, 0), R.uniform(-125, -100), 0), R.uniform(0, 360))
    mk('M-an-cow-0', (-15, -110, 0), 80); mk('M-an-cow-1', (-18, -116, 0), 120)
    haystack(P, -18, -122); haystack(P, -21, -104, 0.8); cart(P, -2, -100, 20, 'hay')
    fence(P, (-26, -126), (-12, -126)); fence(P, (-26, -126), (-26, -98))
    P.add(well(P, -16, -98) or []) if False else well(P, -16, -96)
    # scarecrow easter egg
    sc = [box(0.1, 0.1, 2.6, (0, 0, 1.3), TIMBER), box(1.8, 0.1, 0.1, (0, 0, 2.0), TIMBER), sph(0.25, (0, 0, 2.5), HAY),
          box(0.6, 0.35, 0.8, (0, 0, 1.75), CLOTH_B), cyl(0.4, 0.05, (0, 0, 2.72), STRAW, v=12), cyl(0.18, 0.25, (0, 0, 2.85), STRAW, v=10, r2=0.1)]
    P.add(place(sc, 22, -96, 30)); colbox(0.5, 0.5, 2.6, (22, -96, 1.3)); mk('M-it-scarecrow', (22, -96, 1.5))
    for k in range(30):
        x = R.choice([R.uniform(-28, -20), R.uniform(20, 28)]); y = R.uniform(-138, -80)
        if -30 < x < -12 and -126 < y < -96: continue
        tree(P, x, y, R.uniform(0.8, 1.3), 'oak' if R.random() < 0.7 else 'cypress', seed=100 + k)
    for k in range(25): bush(P, R.choice([-27, 27]) + R.uniform(-1, 1), R.uniform(-138, -80), R.uniform(0.8, 1.4), seed=k)
    for k in range(12): rock(P, R.uniform(-27, 27), R.uniform(-138, -128), R.uniform(0.4, 1.0), seed=k)
    grass_tufts(P, -27, -138, 27, -78, 160, seed=3)
    # peasants working the farm
    for i, (x, y, a) in enumerate([(4, -98, 180), (-4, -104, 150), (10, -100, 200), (-12, -103, 120), (14, -96, 190)]):
        mk('M-en-%s-farm-%d' % ('peasant' if i % 2 == 0 else 'peasantf', i), (x, y, 0), a)
    mk('M-tr-leave_shed', (-8, -108, 1.5), size=(12, 3, 3))
    for i, p in enumerate([(-4, -112), (6, -98), (-10, -98)]): mk('M-pr-crate-f%d' % i, (*p, 0))
    for i, p in enumerate([(0, -109), (-5, -118), (1, -95)]): mk('M-pr-barrel-f%d' % i, (*p, 0))
    mk('M-pk-bread-f0', (-12, -117, 0.9)); mk('M-it-milkstool', (-15.5, -111.5, 0.3))
    mk('M-col-cmos-farm', (16.5, -120.5, 0.25))   # collectible anachronism hidden in the pen corner
    return P.join()

# ============================================================ TOWN of Valtorre
def town():
    P = Part('R-town')
    overlay(P, -4, 4, -76, -4.3, COBBLE)                                  # main street
    P.add(cyl(15, 0.04, (0, -42, 0.03), COBBLE, v=40))                     # market square
    overlay(P, -28, 28, -12, -4.3, DIRT, 0.025)                            # castle green
    # houses (x, y, w, d, rot, floors, style, roof)
    L = [(-11, -70, 8, 6, -90, 2, 'timber', 'thatch'), (-11, -61, 7, 6, -90, 2, 'timber', 'tile'), (-12, -53, 8, 7, -90, 3, 'stone', 'tile'),
         (-21, -28, 7, 6, -90, 2, 'timber', 'thatch'), (-11, -24, 8, 6, -90, 2, 'timber', 'tile'), (-11, -16, 7, 6, -90, 2, 'stone', 'tile'),
         (11, -70, 8, 6, 90, 2, 'timber', 'thatch'), (11, -61, 7, 6, 90, 3, 'timber', 'tile'), (12, -53, 8, 7, 90, 2, 'stone', 'tile'),
         (11, -24, 8, 6, 90, 2, 'timber', 'tile'), (11, -16, 7, 6, 90, 2, 'timber', 'thatch'), (21, -60, 7, 6, 90, 2, 'timber', 'thatch'),
         (-21, -62, 6, 6, -90, 1, 'timber', 'thatch'), (21, -18, 6, 6, 90, 1, 'timber', 'thatch')]
    for i, (x, y, w, d, a, fl, st, rf) in enumerate(L):
        house(P, x, y, w, d, a, fl, st, rf, seed=i, sign='tavern_sign' if i == 9 else None)
    # tavern
    mk('M-it-tavern', (7.2, -24, 1.2)); mk('M-it-wanted', (-7.8, -61, 1.7))
    P.add(box(0.05, 0.7, 0.9, (-7.6, -61, 1.7), M('D_wanted', '#ffffff', 0.8)))
    # church (facade + bell tower) west of square
    cx, cy = -22, -42
    P.add(solid(10, 16, 9, (cx, cy, 4.5), STONE_W)); rf = gable_roof(10, 16, 4, 9, TILE, over=0.4); P.add(rf)
    P.add(gable_wall(10, 4, 9, cy - 8, STONE_W, 0.5)) if False else None
    gw = gable_wall(10, 4, 9, 0, STONE_W, 0.5); gw.rotation_euler.z = math.pi / 2; gw.location = (cx + 5, cy, 0); P.add(gw)
    P.add(box(0.2, 2.2, 3.4, (cx + 5.05, cy, 1.7), WOOD)); P.add(cyl(1.2, 0.2, (cx + 5.1, cy, 6.5), GLASS, rot=(0, math.pi / 2, 0), v=16))
    P.add(tor(1.25, 0.12, (cx + 5.12, cy, 6.5), STONE_D, rot=(0, math.pi / 2, 0), maj=20, mn=6))
    P.add(solid(4, 4, 18, (cx, cy + 9, 9), STONE_W)); P.add(cyl(3.2, 5, (cx, cy + 9, 20.5), TILE, v=4, r2=0.05, rot=(0, 0, math.pi / 4)))
    P.add(box(1.4, 4.1, 2.0, (cx, cy + 9, 16), DARK), box(4.1, 1.4, 2.0, (cx, cy + 9, 16), DARK))
    mk('M-it-churchbell', (cx + 5.3, cy, 1.4))
    # market
    well(P, 0, -42); mk('M-it-well', (1.3, -42, 1.0))
    for i, (x, y, a, c, g) in enumerate([(-8, -36, 90, CLOTH_R, 'veg'), (-8, -48, 90, CLOTH_B, 'bread'), (8, -36, -90, CLOTH_G, 'fish'),
                                          (8, -48, -90, CLOTH_Y, 'pots'), (-5, -54, 0, CLOTH_R, 'veg')]):
        stall(P, x, y, a, c, g)
    # pillory / stocks easter egg
    st = [box(0.15, 0.15, 1.6, (sx_, 0, 0.8), TIMBER) for sx_ in (-0.8, 0.8)] + [box(1.9, 0.18, 0.35, (0, 0, 1.45), WOOD)]
    P.add(place(st, 6, -32, 10)); colbox(1.9, 0.4, 1.6, (6, -32, 0.8), (0, 0, math.radians(10))); mk('M-it-stocks', (6, -32.6, 1.2))
    # blacksmith (open forge)
    bx, by = 16, -40
    P.add(solid(6, 0.4, 3.2, (bx, by + 3, 1.6), STONE_D), box(7, 6.6, 0.25, (bx, by, 3.3), TILE, rot=(-0.12, 0, 0)))
    for xx in (-3, 3): P.add(box(0.3, 0.3, 3.2, (bx + xx, by - 3, 1.6), TIMBER))
    P.add(solid(2, 1.4, 1.0, (bx + 1.5, by + 1.8, 0.5), STONE_D), cyl(0.5, 0.15, (bx + 1.5, by + 1.8, 1.05), FIRE, v=10))
    P.add(lathe([(0.0, 0), (0.25, 0), (0.18, 0.5), (0.3, 0.6), (0.45, 0.75), (0.45, 0.85), (0.0, 0.85)], IRON, 'anvil', 12, (bx - 1, by, 0)))
    colbox(1, 1, 0.9, (bx - 1, by, 0.45)); mk('M-it-anvil', (bx - 1, by, 1.0)); mk('M-fx-fire-forge', (bx + 1.5, by + 1.8, 1.1))
    P.add(*barrel(bx - 2.5, by + 2.2, 0, 0.9, WATER), box(1.6, 0.1, 1.2, (bx - 1, by + 2.7, 1.8), IRON))
    # props & dressing
    for i in range(12):
        x = R.choice([-5.2, 5.2]) * R.uniform(0.95, 1.05); y = R.uniform(-74, -14)
        if -56 < y < -28: continue
        P.add(*barrel(x, y)) if R.random() < 0.5 else P.add(*crate(x, y, 0, 0.8, R.uniform(0, 90)))
        colbox(0.9, 0.9, 0.9, (x, y, 0.45))
    cart(P, 6, -66, -30, 'cabbage'); cart(P, -16, -40, 80, 'barrels')
    for i in range(6): P.add(bench(R.uniform(-3, 3) + (6 if i % 2 else -6), -42 + R.uniform(-6, 6), R.uniform(0, 180)))
    for k in range(18): tree(P, R.choice([-26, 26]) + R.uniform(-1.5, 1.5), R.uniform(-75, -14), R.uniform(0.9, 1.3), 'cypress' if R.random() < 0.5 else 'oak', seed=300 + k)
    # palisade behind houses
    for side in (-1, 1):
        for k in range(70):
            y = -76 + k; P.add(cyl(0.18, 3.2 + R.uniform(-.3, .3), (side * 28.5, y, 1.6), TIMBER, v=6))
    # town enemies (market ambush), cabbage lady, gate guards on the green
    for i, (x, y) in enumerate([(-2, -58), (3, -50), (-4, -38), (4, -34), (0, -30), (-3, -46)]):
        mk('M-en-%s-market-%d' % (['peasant', 'peasantf', 'peasant', 'torch', 'peasant', 'torch'][i], i), (x, y, 0), 180)
    mk('M-en-cabbage-market-6', (-8, -37.5, 0), 90); mk('M-en-cabbage-market-7', (8, -47, 0), -90)
    for i, (x, y) in enumerate([(-6, -9), (6, -9), (-12, -7), (12, -8), (0, -7)]): mk('M-en-%s-green-%d' % ('guard' if i < 4 else 'guard', i), (x, y, 0), 180)
    mk('M-cp-town', (0, -78, 0), 0); mk('M-cp-green', (0, -20, 0), 0)
    mk('M-tr-market', (0, -60, 1.5), size=(14, 3, 3)); mk('M-tr-green', (0, -16, 1.5), size=(20, 3, 3))
    for i, p in enumerate([(-6, -44), (6, -40), (-3, -56), (5, -57), (-7, -30), (9, -30)]): mk('M-pr-%s-t%d' % (['barrel', 'crate', 'pot'][i % 3], i), (*p, 0))
    for i in range(10): mk('M-pr-cabbage-t%d' % i, (-8 + R.uniform(-1, 1), -36 + R.uniform(-1, 1), 1.2))
    for i, p in enumerate([(-7.6, -68), (7.6, -60), (-7.6, -18)]): mk('M-pk-apple-t%d' % i, (*p, 0.5))
    mk('M-an-cat-town', (-9, -27, 0), 40); mk('M-it-cat_town', (-9, -27, 0.3))
    mk('M-col-earbud-town', (21, -64, 0.2)); mk('M-col-sunglasses-town', (-3.6, -15, 0.2))
    mk('M-cam-market1', (8, -66, 3.0)); mk('M-cam-green1', (0, -24, 4)); mk('M-cam-bridge', (14, -18, 6))
    return P.join()

# ============================================================ CASTLE exterior
def castle():
    P = Part('R-castle'); I = Part('R-courtyard')
    # curtain walls: x -36..36, y 6..78, thickness 3, height 10
    curtain(P, (-36, 6), (-3.2, 6)); curtain(P, (3.2, 6), (36, 6))
    curtain(P, (-36, 6), (-36, 78)); curtain(P, (36, 6), (36, 78)); curtain(P, (-36, 78), (36, 78))
    for x, y in ((-36, 6), (36, 6), (-36, 78), (36, 78)): round_tower(P, x, y, 5, 14)
    round_tower(P, -36, 42, 4, 13, cone=5); round_tower(P, 36, 42, 4, 13, cone=5)
    # gatehouse
    for sx in (-1, 1): round_tower(P, sx * 6.5, 6, 4.2, 15, cone=6)
    P.add(solid(9, 6, 6, (0, 6, 12), STONE)); merlons(P, (-4.5, 3.3), (4.5, 3.3), 15, 0.7, 1.1)
    P.add(box(6.4, 0.6, 1.0, (0, 3.0, 8.6), STONE_D))                       # arch lintel
    for k in range(9): a = math.pi * k / 8; P.add(box(0.8, 0.8, 0.7, (math.cos(a) * 3.2, 3.0, 7.6 + math.sin(a) * 1.4), STONE_D, rot=(0, -a + math.pi / 2, 0)))
    colbox(6.4, 6, 3, (0, 6, 10.5))
    P.add(box(6.4, 8, 0.3, (0, 6, 0.15), COBBLE)); colbox(6.4, 8, 0.3, (0, 6, -0.15) )
    P.add(box(0.4, 8.0, 9, (-3.4, 6, 4.5), STONE_D), box(0.4, 8.0, 9, (3.4, 6, 4.5), STONE_D))
    # portcullis (raised: bottom at z=5.6) + drawbridge (raised = vertical)
    pc = []
    for k in range(8): pc.append(box(0.12, 0.12, 6.0, (-2.8 + k * 0.8, 0, 3.0), IRON))
    for k in range(6): pc.append(box(6.2, 0.1, 0.12, (0, 0, 0.4 + k * 1.1), IRON))
    for k in range(8): pc.append(cyl(0.08, 0.3, (-2.8 + k * 0.8, 0, -0.1), IRON, r2=0.0, v=4, rot=(math.pi, 0, 0)))
    pco = mover('portcullis', pc); pco.location = (0, 4.2, 5.6)
    db = [box(6.2, 6.6, 0.35, (0, -3.3, 0.0), WOOD)]
    for k in range(5): db.append(box(6.3, 0.18, 0.1, (0, -0.6 - k * 1.4, 0.2), IRON))
    for sx in (-1, 1): db.append(tor(0.14, 0.03, (sx * 2.8, -6.3, 0.25), IRON, maj=10, mn=4))
    dbo = mover('drawbridge', db); dbo.location = (0, 2.6, 0.05); dbo.rotation_euler = (math.radians(88), 0, 0)
    for sx in (-1, 1):
        mk('M-it-chain%d' % (0 if sx < 0 else 1), (sx * 2.8, 2.6, 6.6))
        P.add(box(0.6, 0.6, 0.6, (sx * 2.9, 3.2, 9.6), STONE_D))
    mk('M-cam-gate', (10, -14, 3.5)); mk('M-cam-gate2', (0, -16, 1.6))
    # inner ground
    overlay(I, -34.5, 34.5, 7.5, 76.5, DIRT, 0.02); overlay(I, -3, 3, 7.5, 50, COBBLE, 0.03)
    # ramps up to the wall walk (south wall, both sides) & west wall
    for sx in (-1, 1):
        stairs(I, sx * 22 - 1.2, sx * 22 + 1.2, 18, 8.0, 0, 10, STONE_D) if False else None
    stairs(I, -16, -13.6, 21, 8.2, 0, 10, STONE_D); stairs(I, 13.6, 16, 21, 8.2, 0, 10, STONE_D)
    for sx in (-1, 1): I.add(solid(2.4, 2.0, 10, (sx * 14.8, 7.5, 5), STONE_D))
    for sx in (-1, 1): I.add(box(0.15, 13, 0.9, (sx * 14.8 + sx * -1.3, 14.5, 0), STONE_D, rot=(math.radians(37.5), 0, 0)))
    colbox(70, 3, 0.4, (0, 6, 10.0))   # wall-walk floor south (top of curtain)
    # trebuchet (the Count's toy) in the courtyard, aimed south over the wall
    tx, ty = -20, 30
    tb = []
    for sx in (-1, 1):
        tb.append(box(0.4, 7, 0.4, (sx * 1.6, 0, 0.3), TIMBER))
        tb.append(box(0.35, 0.35, 7.5, (sx * 1.6, 1.4, 3.6), TIMBER, rot=(0.38, 0, 0))); tb.append(box(0.35, 0.35, 7.5, (sx * 1.6, -1.4, 3.6), TIMBER, rot=(-0.38, 0, 0)))
    for yy in (-3.3, 3.3): tb.append(box(3.6, 0.4, 0.4, (0, yy, 0.3), TIMBER))
    tb.append(cyl(0.18, 3.6, (0, 0, 6.8), IRON, rot=(0, math.pi / 2, 0), v=10)); I.add(place(tb, tx, ty))
    arm = [box(0.35, 12, 0.35, (0, 2.5, 0), TIMBER), box(1.6, 1.6, 1.8, (0, -3.6, -1.2), WOOD_D, bev=0.05)]
    for k in range(3): arm.append(box(1.7, 0.1, 0.15, (0, -3.6, -0.6 - k * 0.5), IRON))
    arm.append(cyl(0.02, 3.0, (0, 8.5, -1.4), ROPE, v=4))
    ao = mover('trebuchet_arm', arm); ao.location = (tx, ty, 6.8); ao.rotation_euler = (math.radians(-35), 0, 0)
    colbox(3.6, 7, 3, (tx, ty, 1.5)); mk('M-cam-treb', (tx + 9, ty - 9, 3)); mk('M-cam-treb2', (tx - 6, ty + 10, 9)); mk('M-treb', (tx, ty, 0))
    I.add(*[o for k in range(5) for o in barrel(tx + 3 + k * 0.8, ty + 4, 0, 0.7, SOOT)])
    for k in range(4): I.add(sph(0.45, (tx - 3, ty - 2 + k, 0.45), STONE_D, seg=10, rings=7))
    # stables (east)
    I.add(solid(0.3, 22, 4, (34.3, 22, 2), WOOD_D)); I.add(box(6, 23, 0.25, (31.5, 22, 4.2), THATCH, rot=(0, -0.2, 0)))
    for k in range(6): I.add(box(0.25, 0.25, 3.6, (28.6, 11.5 + k * 4.2, 1.8), TIMBER)); colbox(0.4, 0.4, 3.6, (28.6, 11.5 + k * 4.2, 1.8))
    for k in range(5): I.add(box(5, 0.15, 1.4, (31.5, 13.6 + k * 4.2, 0.7), WOOD)); colbox(5, 0.3, 1.4, (31.5, 13.6 + k * 4.2, 0.7))
    for k in range(4): mk('M-an-horse-%d' % k, (32, 15.5 + k * 4.2, 0), -90)
    for k in range(5): I.add(*hay_bale(33, 12 + k * 4.2, 0, 90))
    # armory lean-to (west)
    I.add(solid(0.3, 16, 4, (-34.3, 26, 2), WOOD_D)); I.add(box(6, 17, 0.25, (-31.5, 26, 4.2), TILE, rot=(0, 0.2, 0)))
    for k in range(4):
        y = 20 + k * 3.5; rack = [box(2.4, 0.15, 0.15, (0, 0, 1.6), WOOD_D), box(2.4, 0.15, 0.15, (0, 0, 0.4), WOOD_D)]
        for j in range(5): rack.append(cyl(0.025, 2.6, (-1 + j * 0.5, 0.1, 1.3), WOOD_D, v=5)); rack.append(cyl(0.06, 0.3, (-1 + j * 0.5, 0.1, 2.7), IRON, r2=0.0, v=4))
        I.add(place(rack, -33.5, y, 90))
    mk('M-it-armory', (-32, 24, 1.2))
    # training yard: dummies & archery targets (easter egg)
    for i, (x, y) in enumerate([(-8, 36), (-5, 38), (-2, 36)]):
        dm = [box(0.12, 0.12, 2.0, (0, 0, 1.0), TIMBER), box(1.4, 0.12, 0.12, (0, 0, 1.5), TIMBER), sph(0.38, (0, 0, 1.25), HAY, s=(1, 0.8, 1.3)), sph(0.22, (0, 0, 2.0), CLOTH_W)]
        I.add(place(dm, x, y, 180)); mk('M-tg-dummy-%d' % i, (x, y, 1.4))
    for i, x in enumerate((12, 16, 20)):
        tg = [cyl(0.7, 0.2, (0, 0, 1.4), HAY, rot=(math.pi / 2, 0, 0), v=20)] + [cyl(r_, 0.22, (0, -0.01 * k, 1.4), [CLOTH_W, CLOTH_R, CLOTH_W, CLOTH_Y][k], rot=(math.pi / 2, 0, 0), v=20) for k, r_ in enumerate((0.6, 0.45, 0.3, 0.13))]
        tg += [box(0.1, 0.1, 1.6, (sx_ * 0.5, 0.2, 0.7), TIMBER, rot=(0.3, 0, 0)) for sx_ in (-1, 1)]
        I.add(place(tg, x, 44, 180)); mk('M-tg-archery-%d' % i, (x, 44.12, 1.4))
    well(I, 6, 26); mk('M-it-well2', (7.3, 26, 1.0))
    for i, p in enumerate([(-4, 14), (4, 16), (10, 30), (-12, 18), (22, 40), (-26, 44), (24, 12), (-24, 12)]): mk('M-pr-%s-c%d' % (['barrel', 'crate'][i % 2], i), (*p, 0))
    I.add(*[o for k in range(6) for o in barrel(-28 + (k % 3) * 0.8, 46 + (k // 3) * 0.8, 0)]); colbox(2.6, 1.8, 0.9, (-27.2, 46.4, 0.45))
    # enemies in courtyard + walls
    for i, (x, y, kd) in enumerate([(-6, 16, 'guard'), (6, 18, 'guard'), (-10, 26, 'guard'), (10, 24, 'knight'), (0, 32, 'guard'), (-14, 36, 'guard')]):
        mk('M-en-%s-yard-%d' % (kd, i), (x, y, 0), 180)
    for i, (x, y) in enumerate([(-20, 6.3), (20, 6.3), (-34.5, 30), (34.5, 30), (-8, 6.3)]):
        mk('M-en-archer-yard-%d' % (10 + i), (x, y, 10.0), 0 if y < 7 else (90 if x < 0 else -90))
    mk('M-cp-yard', (0, 11, 0), 0); mk('M-tr-yard', (0, 13, 1.5), size=(4, 2, 3))
    # the grate where the Maestro calls from (keep south wall at y=50, cell below)
    mk('M-it-grate', (11, 49.2, 0.3)); mk('M-tr-grate', (11, 46.5, 1.5), size=(4, 3, 3)); mk('M-cam-grate', (14, 44, 1.2))
    I.add(box(2.0, 0.3, 0.8, (11, 49.75, 0.35), DARK)); [I.add(box(0.06, 0.32, 0.8, (10.1 + k * 0.3, 49.7, 0.35), IRON)) for k in range(7)]
    mk('M-col-tamagotchi-yard', (33, 28.5, 0.3)); mk('M-pk-bread-y0', (-31.5, 18, 1.0)); mk('M-pk-apple-y1', (31, 26, 0.6))
    mk('M-it-horse', (31, 19.6, 1.4)); mk('M-cam-yard1', (0, 9, 6))
    return [P.join(), I.join()]

# ============================================================ KEEP (exterior shell + interior)
KX0, KX1, KY0, KY1 = -24, 20, 50, 74
def keep():
    P = Part('R-keep'); I = Part('R-hall'); E = Part('R-eastwing')
    H = 15
    # exterior shell walls (thick) with door gap south of the hall
    t = 1.5
    for (x0, y0, x1, y1, door) in [(KX0 - t, KY0 - t, KX1 + t, KY0, True), (KX0 - t, KY1, KX1 + t, KY1 + t, False),
                                   (KX0 - t, KY0, KX0, KY1, False), (KX1, KY0, KX1 + t, KY1, False)]:
        cx = (x0 + x1) / 2; cy = (y0 + y1) / 2; w = x1 - x0; d = y1 - y0
        if door:
            dx = -11; dw = 3.6; dh = 4.6
            for a, b in ((x0, dx - dw / 2), (dx + dw / 2, x1)): P.add(solid(b - a, d, H, ((a + b) / 2, cy, H / 2), STONE))
            P.add(solid(dw, d, H - dh, (dx, cy, dh + (H - dh) / 2), STONE))
        else: P.add(solid(w, d, H, (cx, cy, H / 2), STONE))
    P.add(box(KX1 - KX0 + 4, KY1 - KY0 + 4, 0.6, ((KX0 + KX1) / 2, (KY0 + KY1) / 2, H + 0.3), STONE_D))
    merlons(P, (KX0 - 1, KY0 - 1.2), (KX1 + 1, KY0 - 1.2), H + 0.6, 0.8, 1.2); merlons(P, (KX0 - 1, KY1 + 1.2), (KX1 + 1, KY1 + 1.2), H + 0.6, 0.8, 1.2)
    merlons(P, (KX0 - 1.2, KY0 - 1), (KX0 - 1.2, KY1 + 1), H + 0.6, 0.8, 1.2); merlons(P, (KX1 + 1.2, KY0 - 1), (KX1 + 1.2, KY1 + 1), H + 0.6, 0.8, 1.2)
    for sx in (KX0 - 0.5, KX1 + 0.5):
        for sy in (KY0 - 0.5, KY1 + 0.5): round_tower(P, sx, sy, 2.6, H + 3, cone=4, col=False)
    for k in range(6):   # tall windows on the south facade (dark glass)
        x = KX0 + 3 + k * 7.6
        if abs(x + 11) < 3: continue
        P.add(box(1.3, 0.2, 3.2, (x, KY0 - t - 0.05, 8.5), GLASS), box(1.7, 0.4, 0.3, (x, KY0 - t - 0.1, 6.8), STONE_D))
        P.add(cyl(0.65, 0.2, (x, KY0 - t - 0.05, 10.1), GLASS, rot=(math.pi / 2, 0, 0), v=16))
    P.add(*banner(-15.5, KY0 - t - 0.15, 9, 0), *banner(-6.5, KY0 - t - 0.15, 9, 0))
    P.add(box(5.5, 1.0, 0.8, (-11, KY0 - t - 0.3, 5.1), STONE_D))
    steps = [box(6 - k * 0.8, 1.0 + k * 0.0, 0.2, (-11, KY0 - t - 0.6 - (2 - k) * 0.6, 0.1 + k * 0.0), STONE_D) for k in range(1)]
    P.add(steps)
    # keep door (closed until the key)
    dm = []
    for sx in (-1, 1):
        q = door_mesh(1.75, 4.5, WOOD)
        for o in q: o.location.x += sx * 0.9
        dm += q
    kd = mover('keepdoor', dm); kd.location = (-11, KY0 - 0.75, 0.0)
    mk('M-keepdoor', (-11, KY0 - 2.6, 0)); mk('M-cam-keepdoor', (-5, 40, 3))
    # ---------------- interior: Great Hall x -24..2
    room(I, KX0, 2, KY0, KY1, 0, 8, STONE_W, FLAG, WOOD_D, t=0.3, gaps=[('S', -11, 3.6, 4.6), ('E', 56, 2.4, 3.2), ('E', 68, 2.4, 3.2)], floor=False)
    # floor with hole for the dungeon stairs (x -23..-20, y 58..70)
    for (x0, x1, y0, y1) in [(KX0, 2, KY0, 58), (KX0, 2, 70, KY1), (KX0, -23.2, 58, 70), (-19.8, 2, 58, 70)]:
        I.add(solid(x1 - x0, y1 - y0, 0.4, ((x0 + x1) / 2, (y0 + y1) / 2, -0.2), FLAG))
    I.add(box(0.3, 12, 1.0, (-19.65, 64, 0.5), STONE_D)); colbox(0.3, 12, 1.0, (-19.65, 64, 0.5))
    # dungeon gate at the top of the stairs (clock lock)
    dg = [box(0.12, 0.12, 3.0, (-1.3 + k * 0.33, 0, 1.5), IRON) for k in range(9)] + [box(3.0, 0.14, 0.14, (0, 0, z), IRON) for z in (0.3, 1.5, 2.8)]
    dg.append(cyl(0.35, 0.15, (0, -0.1, 1.5), GOLD, rot=(math.pi / 2, 0, 0), v=16))
    mover('dungeongate', dg).location = (-21.5, 58.2, 0); mk('M-it-dungeongate', (-21.5, 57.4, 1.2))
    for x in (-17, -9, -1):
        for y in (57, 67): pillar(I, x, y, 0, 8, 0.55, STONE_W)
    I.add(table(-9, 62, 90, 10, 1.4)); colbox(1.4, 10, 0.9, (-9, 62, 0.45))
    for k in range(8):
        for sx in (-1, 1): I.add(bench(-9 + sx * 1.3, 62 - 4.5 + k * 1.3, 90, 1.0)) if False else None
    for sx in (-1, 1): I.add(bench(-9 + sx * 1.2, 62, 90, 9)); colbox(0.5, 9, 0.5, (-9 + sx * 1.2, 62, 0.25))
    for k in range(10):  # feast
        y = 57.6 + k * 0.95
        I.add(cyl(0.2, 0.04, (-9 + (0.35 if k % 2 else -0.35), y, 0.9), M('plate', '#c9c2b0', 0.4, 0.3), v=12))
        I.add(cyl(0.05, 0.18, (-9 + (0.55 if k % 2 else -0.55), y + 0.2, 0.96), GOLD, v=8))
    for k in range(3): I.add(sph(0.3, (-9, 59 + k * 3, 1.1), M('roast', '#8a4a20', 0.5), s=(1.3, 0.9, 0.7), seg=12, rings=8))
    I.add(overlay(I, -20, 0, 52, 72, RUG, 0.01) or [])
    # throne dais (north)
    I.add(solid(8, 3, 0.6, (-9, 72.2, 0.3), STONE_D)); thr = [box(1.4, 1.0, 0.6, (0, 0, 0.9), WOOD_D), box(1.4, 0.2, 2.4, (0, 0.45, 1.8), WOOD_D), box(1.0, 0.05, 1.6, (0, 0.33, 1.9), CLOTH_R)]
    I.add(place(thr, -9, 72.4)); colbox(1.4, 1.0, 1.2, (-9, 72.4, 0.6)); mk('M-it-throne', (-9, 71.2, 1.0))
    # fireplace west wall
    I.add(box(1.0, 4.4, 4.0, (KX0 + 0.5, 64, 2.0), STONE_D), box(0.6, 3.0, 2.2, (KX0 + 0.75, 64, 1.1), SOOT), box(1.4, 4.8, 0.4, (KX0 + 0.7, 64, 4.1), STONE_D))
    colbox(1.4, 4.4, 4, (KX0 + 0.6, 64, 2)); mk('M-fx-fire-hearth', (KX0 + 1.0, 64, 0.4))
    for k in range(4): I.add(*banner(KX0 + 4 + k * 6.5, KY1 - 0.25, 5.2, 180, [CLOTH_R, CLOTH_B, CLOTH_R, CLOTH_G][k], 1.4, 3.2))
    for i, x in enumerate((-17, -9, -1)): mk('M-fx-chandelier-%d' % i, (x, 62, 6.8))
    for i, (x, y) in enumerate([(-23.6, 54), (-23.6, 70), (1.6, 52), (-4, 73.6)]): I.add(torch_bracket(x, y, 3.0, [90, 90, -90, 180][i])); mk('M-fx-torch-h%d' % i, (x + [0.3, 0.3, -0.3, 0][i], y + [0, 0, 0, -0.3][i], 3.45))
    # armour stands along the walls (some come alive? no - just a gag)
    for i, x in enumerate((-20, -14, -4)):
        mk('M-it-armour-%d' % i, (x, KY0 + 0.8, 0))
    for i, (x, y, kd) in enumerate([(-16, 60, 'knight'), (-2, 63, 'knight'), (-12, 70, 'guard'), (-6, 54, 'guard'), (-20, 66, 'guard')]):
        mk('M-en-%s-hall-%d' % (kd, i), (x, y, 0), 180)
    mk('M-cp-hall', (-11, 47.5, 0), 0); mk('M-tr-hall', (-11, 52, 1.5), size=(3, 2, 3)); mk('M-cam-hall1', (-1, 53, 5)); mk('M-cam-hall2', (-20, 70, 4))
    mk('M-pk-roast-h0', (-9, 66, 1.0)); mk('M-pk-apple-h1', (-9, 58.5, 1.0))
    for i, p in enumerate([(-22, 52), (0, 72), (-1, 52)]): mk('M-pr-%s-h%d' % (['barrel', 'crate', 'pot'][i], i), (*p, 0))
    # ---------------- east wing: library (S) + kitchen (N)
    room(E, 2, KX1, KY0, 62, 0, 7, STONE_W, WOOD, WOOD_D, t=0.3, gaps=[('W', 56, 2.4, 3.2)], skip='N')
    room(E, 2, KX1, 62, KY1, 0, 7, PLASTER, FLAG, WOOD_D, t=0.3, gaps=[('W', 68, 2.4, 3.2), ('S', 15, 2.4, 3.2)])
    for k in range(5):  # bookshelves (library)
        y = 51.5 + k * 2.3
        sh = [box(0.5, 1.9, 3.4, (0, 0, 1.7), WOOD_D)]
        for z in range(5): sh.append(box(0.55, 1.9, 0.06, (0, 0, 0.3 + z * 0.75), WOOD))
        for z in range(4):
            for b in range(8): sh.append(box(0.32, 0.16, R.uniform(0.45, 0.62), (0, -0.8 + b * 0.22, 0.6 + z * 0.75), M('book%d' % (b % 5), ['#7a2e2a', '#2c4a7a', '#4e6233', '#5a3a22', '#8a6f2e'][b % 5], 0.8)))
        E.add(place(sh, KX1 - 0.4, y)); colbox(0.6, 1.9, 3.4, (KX1 - 0.4, y, 1.7))
    E.add(table(9, 55, 0, 3, 1.4)); colbox(3, 1.4, 0.9, (9, 55, 0.45))
    for i, nm in enumerate(['heli', 'phone', 'clock', 'laser']):
        E.add(box(0.6, 0.45, 0.01, (8.0 + i * 0.7, 55, 0.88), M('D_sketch_' + nm, '#ffffff', 0.9), rot=(0, 0, R.uniform(-0.2, 0.2))))
        mk('M-it-sketch_%s' % nm, (8.0 + i * 0.7, 54.2, 1.0))
    E.add(cyl(0.3, 1.0, (4, 52.5, 0.5), WOOD_D, v=12)); E.add(sph(0.35, (4, 52.5, 1.35), M('globe', '#b89a5a', 0.6), seg=16, rings=10)); mk('M-it-globe', (4, 52.5, 1.3))
    mk('M-col-fidget-library', (16, 60, 0.3))
    colbox(0.7, 0.7, 1.7, (4, 52.5, 0.85))
    mk('M-it-flatearth', (4, 53.4, 1.3)) if False else None
    # kitchen
    E.add(box(1.4, 5, 3.2, (KX1 - 0.7, 68, 1.6), STONE_D), box(1.0, 3.6, 2.0, (KX1 - 1.1, 68, 1.0), SOOT)); colbox(1.6, 5, 3.2, (KX1 - 0.8, 68, 1.6))
    E.add(lathe([(0.0, 0.0), (0.5, 0.05), (0.6, 0.4), (0.55, 0.8), (0.0, 0.8)], IRON, 'cauldron', 16, (KX1 - 1.5, 68, 0.3))); mk('M-fx-fire-kitchen', (KX1 - 1.5, 68, 0.2))
    mk('M-it-cauldron', (KX1 - 2.4, 68, 1.0))
    E.add(table(10, 68, 90, 4, 1.2)); colbox(1.2, 4, 0.9, (10, 68, 0.45))
    for k in range(6): E.add(sph(0.12, (10 + R.uniform(-0.4, 0.4), 66.5 + k * 0.5, 0.95), M(['onion', 'carrot', 'cabbage'][k % 3], ['#d8c090', '#e07a2a', '#6f9e3a'][k % 3], 0.7), seg=8, rings=6))
    for k in range(4): E.add(*barrel(3.2, 63.5 + k * 0.9, 0, 0.9)); 
    colbox(1, 3.6, 0.9, (3.2, 64.85, 0.45))
    for k in range(5): E.add(cyl(0.04, 0.6, (6 + k * 0.6, KY1 - 0.4, 3.5), ROPE, v=4), sph(0.16, (6 + k * 0.6, KY1 - 0.4, 3.1), M('ham', '#a0603a', 0.6), s=(1, 1, 1.4)))
    mk('M-an-cat-kitchen', (8, 71, 0), 200); mk('M-it-cat_kitchen', (8, 71, 0.3)); mk('M-pk-roast-k0', (10, 69.5, 1.0)); mk('M-col-phonecase-kitchen', (17.5, 63, 0.2))
    mk('M-en-cook-kitchen-0', (12, 66, 0), 90)
    for i, p in enumerate([(5, 70), (14, 72)]): mk('M-pr-pot-k%d' % i, (*p, 0))
    E.add(torch_bracket(2.4, 58, 3.0, -90)); mk('M-fx-torch-l0', (2.7, 58, 3.45))
    return [P.join(), I.join(), E.join()]

# ============================================================ SPIRE (clock tower) - exterior spiral climb
TX, TY, TR, TH = 27, 60, 5.5, 40
def spire():
    P = Part('R-spire'); S = Part('R-spiral')
    P.add(cyl(TR, TH, (TX, TY, TH / 2), STONE, v=32)); [colbox((TR - 0.1) * 2, (TR - 0.1) * 2 * math.tan(math.pi / 16), TH, (TX, TY, TH / 2), (0, 0, k * math.pi / 8)) for k in range(8)]
    P.add(cyl(TR + 0.5, 1.6, (TX, TY, 0.8), STONE_D, v=32, r2=TR + 0.1))
    for k in range(10): P.add(box(0.25, 0.3, 1.6, (TX + math.cos(k * 2.4) * TR, TY + math.sin(k * 2.4) * TR, 4 + k * 3.4), DARK, rot=(0, 0, k * 2.4 + math.pi / 2)))
    # spiral ledge: starts at the south (angle -90deg) at ground, rises 10 m per turn, counter-clockwise
    GAPS = {14, 15, 30, 31, 50, 51, 66, 67, 86, 87, 100, 101, 116, 117, 129, 130}
    CLOCK = set(range(38, 47))                       # second turn, south-west face: ride the clock hand
    seg = 36; turns = 4; n = seg * turns + 2; r0, r1 = TR - 0.1, TR + 2.6; rise = TH / (seg * turns)
    for i in range(n):
        if i < 3: pass
        a0 = -math.pi / 2 + 2 * math.pi * i / seg; a1 = a0 + 2 * math.pi / seg; am = (a0 + a1) / 2
        z = 0.6 + i * rise
        if i in GAPS or i in CLOCK: continue
        rm = (r0 + r1) / 2; L = 2 * math.pi * rm / seg + 0.08; w = r1 - r0
        tilt = math.atan2(rise, 2 * math.pi * rm / seg)
        # build with explicit matrix: tangent along +X local, radial along Y local
        from mathutils import Matrix
        def seg_box(mat, extra=0.0):
            bpy.ops.mesh.primitive_cube_add(size=1); q = lib.act(); q.scale = (L, w, 0.45); bpy.ops.object.transform_apply(scale=True)
            q.matrix_world = Matrix.Translation((TX + math.cos(am) * rm, TY + math.sin(am) * rm, z)) @ Matrix.Rotation(am + math.pi / 2, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'Y').inverted()
            if mat: setmat(q, mat)
            return q
        S.add(seg_box(WOOD if (i // 6) % 3 == 0 else STONE_D)); COLS.append(seg_box(None))
        if i % 3 == 0:   # outer railing posts / supports
            S.add(cyl(0.08, 1.0, (TX + math.cos(am) * (r1 - 0.1), TY + math.sin(am) * (r1 - 0.1), z + 0.6), TIMBER, v=6))
            S.add(box(0.15, 0.15, 2.4, (TX + math.cos(am) * (r1 - 0.4), TY + math.sin(am) * (r1 - 0.4), z - 1.3), TIMBER, rot=(0, 0, am), ) )
        if i % 6 == 0: mk('M-sp-%03d' % i, (TX + math.cos(am) * rm, TY + math.sin(am) * rm, z + 0.3), math.degrees(am))
    # invisible outer guard rail except at gaps (prevents accidental falls on corners)
    for i in range(n):
        if i in GAPS or i in CLOCK or (i - 1) in GAPS or (i + 1) in GAPS or i >= 138 or i < 2: continue   # i<2: the entry stairs arrive from outside
        a = -math.pi / 2 + 2 * math.pi * (i + 0.5) / seg; z = 0.6 + i * rise
        colbox(0.25, 2 * math.pi * r1 / seg + 0.1, 1.2, (TX + math.cos(a) * (r1 + 0.1), TY + math.sin(a) * (r1 + 0.1), z + 0.8), (0, 0, a))
    # clock face on the tower (south-west, second turn) - its minute hand is a moving platform
    ca = -math.pi / 2 + 2 * math.pi * 42 / seg; cz = 0.6 + 42 * rise
    cxp, cyp = TX + math.cos(ca) * (TR + 0.05), TY + math.sin(ca) * (TR + 0.05)
    face = [cyl(3.2, 0.2, (0, 0, 0), M('clockface', '#e8dcc0', 0.6), rot=(math.pi / 2, 0, 0), v=40), tor(3.25, 0.18, (0, 0, 0), GOLD, rot=(math.pi / 2, 0, 0), maj=40, mn=6)]
    for k in range(12): face.append(box(0.18, 0.1, 0.6 if k % 3 == 0 else 0.35, (math.sin(k * math.pi / 6) * 2.7, -0.12, math.cos(k * math.pi / 6) * 2.7), DARK, rot=(0, k * math.pi / 6, 0)))
    for o in face: o.matrix_world = __import__('mathutils').Matrix.Translation((cxp, cyp, cz)) @ __import__('mathutils').Matrix.Rotation(ca - math.pi / 2, 4, 'Z') @ o.matrix_world
    P.add(face)
    hand = [box(0.9, 7.6, 0.35, (0, 3.2, 0), GOLD), box(1.4, 1.4, 0.35, (0, 0, 0), GOLD), sph(0.3, (0, 7.1, 0), GOLD)]
    ho = mover('clockhand', hand); ho.location = (cxp + math.cos(ca) * 0.25, cyp + math.sin(ca) * 0.25, cz); ho.rotation_euler = (0, 0, 0)
    mk('M-clock', (cxp, cyp, cz), math.degrees(ca))
    # rotating gear platforms (the clockwork bursting out of the tower) at the 3rd turn gaps
    for gi, i in enumerate((86, 100, 116)):
        a = -math.pi / 2 + 2 * math.pi * (i + 1) / seg; z = 0.6 + (i + 1) * rise - 0.2
        g = [cyl(1.5, 0.35, (0, 0, 0), M('bronze', '#a8742a', 0.35, 0.9), v=20)]
        for k in range(12): g.append(box(0.4, 0.5, 0.3, (math.cos(k * math.pi / 6) * 1.6, math.sin(k * math.pi / 6) * 1.6, 0), M('bronze', '#a8742a'), rot=(0, 0, k * math.pi / 6)))
        go = mover('gear%d' % gi, g); go.location = (TX + math.cos(a) * (TR + 1.3), TY + math.sin(a) * (TR + 1.3), z)
    # bucket lift (Maestro's invention) bridging gap 129-130
    # top terrace
    # terrace slab with an arc-shaped opening where the ledge arrives from below (south-west quadrant)
    P.add(cyl(TR, 1.0, (TX, TY, TH + 0.5), STONE_D, v=32)); colbox(TR * 1.38, TR * 1.38, 1.0, (TX, TY, TH + 0.5))
    for k in range(40):
        a = (k + 0.5) * 2 * math.pi / 40; ad = math.degrees(a)
        ri = 8.45 if 156 <= ad <= 294 else TR - 0.2
        ro = TR + 4.5; rmid = (ri + ro) / 2; L = 2 * math.pi * ro / 40 + 0.1
        P.add(box(ro - ri, L, 1.0, (TX + math.cos(a) * rmid, TY + math.sin(a) * rmid, TH + 0.5), STONE_D, rot=(0, 0, a)))
        colbox(ro - ri, L, 1.0, (TX + math.cos(a) * rmid, TY + math.sin(a) * rmid, TH + 0.5), (0, 0, a))
    for k in range(24):
        a = k / 24 * 2 * math.pi; ex = (TX + math.cos(a) * (TR + 4.2), TY + math.sin(a) * (TR + 4.2))
        if abs(math.atan2(math.sin(a + math.pi / 2), math.cos(a + math.pi / 2))) < 0.2: continue   # opening where the ledge arrives (south)
        P.add(box(1.1, 0.6, 1.2, (ex[0], ex[1], TH + 1.6), STONE, rot=(0, 0, a + math.pi / 2), bev=0.04))
    for k in range(48):
        a = k / 48 * 2 * math.pi; colbox(1.4, 0.4, 3, (TX + math.cos(a) * (TR + 4.4), TY + math.sin(a) * (TR + 4.4), TH + 2.5), (0, 0, a + math.pi / 2)) if abs(math.atan2(math.sin(a + math.pi / 2), math.cos(a + math.pi / 2))) > 0.2 else None
    for k in range(32): P.add(box(0.6, 0.8, 0.8, (TX + math.cos(k * math.pi / 16) * (TR + 4.2), TY + math.sin(k * math.pi / 16) * (TR + 4.2), TH - 0.3), STONE_D, rot=(0, 0, k * math.pi / 16)))
    for ad in (-65, -10, 45, 100, 145):  # spire roof on 5 pillars (none over the ledge opening 156..294 deg)
        a = math.radians(ad); pillar(P, TX + math.cos(a) * 6.2, TY + math.sin(a) * 6.2, TH + 1, 8, 0.5, STONE)
    P.add(cyl(8.2, 1.0, (TX, TY, TH + 9.5), STONE_D, v=32), cyl(8.0, 14, (TX, TY, TH + 17), TILE, v=32, r2=0.1), sph(0.5, (TX, TY, TH + 24.3), GOLD))
    P.add(box(0.3, 0.3, 4, (TX, TY, TH + 26), GOLD)) 
    bell = [lathe([(0.0, 3.0), (0.6, 2.95), (0.9, 2.6), (1.05, 1.6), (1.4, 0.5), (1.75, 0.05), (1.6, 0.0), (1.3, 0.4), (0.9, 1.6), (0.0, 2.6)], M('bellbronze', '#9a7a3a', 0.3, 1.0), 'bell', 32)]
    bell.append(sph(0.35, (0, 0, 0.3), IRON)); bell.append(cyl(0.06, 4, (0, 0, 4.6), IRON, v=6))
    bo = mover('bell', bell); bo.location = (TX, TY, TH + 4.2)
    mk('M-boss', (TX, TY + 4, TH + 1)); mk('M-cp-spiretop', (TX + 1.5, TY - 9.2, TH + 1), 0); mk('M-tr-spiretop', (TX, TY - 7.5, TH + 2), size=(2.5, 2, 2))
    mk('M-cam-boss1', (TX + 8, TY - 9, TH + 4)); mk('M-cam-boss2', (TX - 2, TY - 2, TH + 2.2))
    mk('M-zip-top', (TX - 2, TY - 9.6, TH + 2)); mk('M-zip-bottom', (-6, 42, 0.2))
    mk('M-cp-spire', (TX, TY - TR - 6.5, 0), 0); mk('M-tr-spire', (TX, TY - TR - 2, 1.5), size=(3, 2, 3))
    # ground start of the ledge
    stairs(S, TX - 1, TX + 1.6, TY - TR - 5.6, TY - TR - 2.55, 0, 0.76, STONE_D)   # meets the ledge's first segment flush
    # archers in the tower windows & on the ledges
    for i, k in enumerate((24, 60, 96, 122)):
        a = -math.pi / 2 + 2 * math.pi * k / seg; z = 0.6 + k * rise
        mk('M-en-archer-spire-%d' % i, (TX + math.cos(a) * (TR + 1.3), TY + math.sin(a) * (TR + 1.3), z + 0.3), math.degrees(a) + 90)
    for i, k in enumerate((10, 46, 76, 108)):
        a = -math.pi / 2 + 2 * math.pi * k / seg; z = 0.6 + k * rise
        mk('M-en-guard-spire-%d' % (10 + i), (TX + math.cos(a) * (TR + 1.3), TY + math.sin(a) * (TR + 1.3), z + 0.3), math.degrees(a) + 90)
    for i, k in enumerate((40, 80, 120)):
        a = -math.pi / 2 + 2 * math.pi * k / seg
        mk('M-pk-apple-s%d' % i, (TX + math.cos(a) * (TR + 1.3), TY + math.sin(a) * (TR + 1.3), 0.6 + k * rise + 0.8))
    for i, k in enumerate((36, 72, 108)):
        a = -math.pi / 2 + 2 * math.pi * k / seg; mk('M-cp-sp%d' % i, (TX + math.cos(a) * (TR + 1.3), TY + math.sin(a) * (TR + 1.3), 0.6 + k * rise + 0.3), math.degrees(a) + 90)
    a = -math.pi / 2 + 2 * math.pi * 64 / seg; mk('M-col-vr-spire', (TX + math.cos(a) * (TR + 2.2), TY + math.sin(a) * (TR + 2.2), 0.6 + 64 * rise + 0.5))
    return [P.join(), S.join()]

# ============================================================ DUNGEON (z = -6)
DZ = -6.0
def dungeon():
    D = Part('R-dungeon')
    stairs(D, -23.2, -19.8, 57.95, 70, 0, DZ, STONE_D)
    for xx in (-23.4, -19.6): D.add(solid(0.4, 12, 6.5, (xx, 64.1, DZ + 3.0), STONE_D))
    D.add(box(3.8, 12, 0.3, (-21.5, 64.1, DZ - 0.15), FLAG))
    # landing + corridor y 70..74, x -24..10
    room(D, -24, 10, 70, 74, DZ, 3.6, STONE_D, FLAG, STONE_D, t=0.5, gaps=[('W', 72, 0, 0), ('S', -21.5, 3.4, 3.6), ('S', -15, 2.2, 2.8), ('S', -6, 3.0, 2.8), ('S', 2, 3.0, 2.8), ('S', 8, 3.8, 3.2)], ceiling=True)
    # guard room south-west (x -18..-10, y 60..70)
    room(D, -18, -10, 60, 70, DZ, 3.6, STONE_D, FLAG, STONE_D, t=0.5, skip='N')
    D.add(table(-14, 64, 0, 2.2, 1.0)); colbox(2.2, 1.0, 0.9, (DZ and -14, 64, DZ + 0.45)) if False else colbox(2.2, 1.0, 0.9, (-14, 64, DZ + 0.45))
    D.add(*[o for o in place([box(2.2, 1.0, 0.1, (0, 0, 0.82), WOOD)], -14, 64, 0, DZ)]) if False else None
    for o in D.objs[-1:]: pass
    mk('M-it-dice', (-14, 63.6, DZ + 1.0)); mk('M-en-jailer-dungeon-0', (-13, 66, DZ), 0)
    # cells x -8..4 (two cells), barred fronts at y=70
    for ci, (x0, x1) in enumerate([(-9, -3), (-1, 5)]):
        room(D, x0, x1, 62, 70, DZ, 3.6, STONE_D, FLAG, STONE_D, t=0.5, skip='N')
        bars = [box(0.08, 0.08, 3.6, (x0 + 0.2 + k * 0.35, 70, DZ + 1.8), IRON) for k in range(int((x1 - x0) / 0.35))]
        D.add(bars); colbox(x1 - x0, 0.2, 3.6, ((x0 + x1) / 2, 70, DZ + 1.8))
        D.add(*hay_bale((x0 + x1) / 2, 63.5, DZ))
    # cell 1: Ser Rattlebones (skeleton gag); cell 2: prisoner Beppe
    mk('M-it-skeleton', (-6, 70.9, DZ + 0.8)); mk('M-npc-beppe', (2, 68.6, DZ), 180); mk('M-it-beppe', (2, 70.9, DZ + 1))
    # torture-ish "tickle room" west (x -24..-19.8, y 60..70 is the stair) -> rats & chains on corridor walls
    for k in range(6): D.add(torch_bracket(-20 + k * 5.5, 73.7, DZ + 2.2, 180)); mk('M-fx-torch-d%d' % k, (-20 + k * 5.5, 73.4, DZ + 2.65))
    for k in range(5): mk('M-an-rat-%d' % k, (-18 + k * 6, 72, DZ), R.uniform(0, 360))
    # passage south to the Maestro's cell: x 6..10, y 62..70 then cell x 4..18, y 51..62
    room(D, 6, 10, 62, 70, DZ, 3.6, STONE_D, FLAG, STONE_D, t=0.5, skip='N', gaps=[('S', 8, 3.0, 3.0)])
    room(D, 3, 18, 51, 62, DZ, 6.0, STONE_D, FLAG, WOOD_D, t=0.5, gaps=[('N', 8, 3.0, 3.0)])
    # the Maestro's lock (the clock key)
    mg = [box(0.1, 0.1, 3.0, (-1.3 + k * 0.33, 0, 1.5), IRON) for k in range(9)] + [box(3.0, 0.14, 0.14, (0, 0, z), IRON) for z in (0.3, 1.5, 2.8)]
    mg.append(cyl(0.4, 0.2, (0, 0.1, 1.5), GOLD, rot=(math.pi / 2, 0, 0), v=12))
    mover('cellgate', mg).location = (8, 62.1, DZ); mk('M-it-cellgate', (8, 63.0, DZ + 1.2))
    # workshop clutter
    D.add(table(10, 56, 0, 3.2, 1.3)); colbox(3.2, 1.3, 0.9, (10, 56, DZ + 0.45))
    D.add(place([box(3.2, 1.3, 0.1, (0, 0, 0.82), WOOD)], 0, 0)) if False else None
    for i, nm in enumerate(['traveller', 'trebuchet']):
        D.add(box(0.05, 1.2, 1.2, (3.05, 54 + i * 3, DZ + 2.6), M('D_sketch_' + nm, '#ffffff', 0.9))); mk('M-it-sketch_%s' % nm, (3.6, 54 + i * 3, DZ + 2.0))
    lect = [box(0.3, 0.3, 1.1, (0, 0, 0.55), WOOD_D), box(0.8, 0.6, 0.08, (0, 0, 1.15), WOOD, rot=(0.4, 0, 0))]
    D.add(place(lect, 15, 54, 0, DZ)); colbox(0.8, 0.6, 1.2, (15, 54, DZ + 0.6)); mk('M-scroll', (15, 54, DZ + 1.3))
    # flying machine model hanging
    fm = [box(0.2, 1.6, 0.2, (0, 0, 0), WOOD_D)]
    for sx in (-1, 1): fm.append(extrude_poly([(0, 0), (sx * 2.2, 0.3), (sx * 2.0, -0.5)], 0.03, M('T_cloth#sail', '#e8e2d0'), loc=(0, 0, 0), rot=(math.pi / 2, 0, 0)))
    D.add(place(fm, 11, 58, 20, DZ + 4.2)); mk('M-it-flyer', (11, 58, DZ + 1.5))
    D.add(*hay_bale(16.5, 60.5, DZ), *barrel(4, 52, DZ), *crate(4.2, 60.6, DZ, 0.8))
    mk('M-npc-maestro', (12, 58, DZ), 200); mk('M-cam-cell1', (5, 59, DZ + 1.8)); mk('M-cam-cell2', (14, 52.5, DZ + 1.6))
    mk('M-fx-candle-c0', (10.8, 56.2, DZ + 1.0)); mk('M-fx-candle-c1', (15, 54.2, DZ + 1.6))
    mk('M-cp-dungeon', (-21.5, 72, DZ), 90); mk('M-tr-dungeon', (-21.5, 69, DZ + 1.5), size=(2, 1, 2))
    mk('M-col-gameboy-dungeon', (-17, 61, DZ + 0.2)); mk('M-pk-bread-d0', (-14.5, 63.8, DZ + 1.0))
    for i, (x, y) in enumerate([(-2, 72), (6, 72), (8, 66)]): mk('M-en-guard-dungeon-%d' % (i + 1), (x, y, DZ), 90)
    return D.join()

# ============================================================ build + export
parts = [terrain(), farm(), town()] + castle() + keep() + spire() + [dungeon()]
col = finish_cols('WORLD')
for o in MARK:
    o.empty_display_size = 0.3
objs = [p for p in parts if p] + [col] + MOVERS + MARK
print('objects', len(objs), 'markers', len(MARK))
for p in parts:
    if p: print(p.name, len(p.data.polygons), 'faces')
export('world', anim=False, objs=objs)
