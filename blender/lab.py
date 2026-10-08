"""Castle TIME - Juno's 2026 bedroom lab. -> game/assets/models/lab.glb"""
import bpy, math, sys, os, random
from mathutils import Vector
sys.path.insert(0, os.path.dirname(__file__))
from lib import *
import lib, kit
from kit import Part, place, crate
reset(); kit.mats(); globals().update({k: v for k, v in kit.__dict__.items() if k.isupper()})
R = random.Random(2026); MARK = []; MOVERS = []
def mk(name, loc, rot=0):
    o = marker(name, loc, rot); MARK.append(o); return o
def neon(name, col, e=3.0): c = hexc(col); return M('neon_' + name, col, 0.3, emit=c, estr=e)
PANEL = M('T_panel', '#ffffff'); LFLOOR = M('T_labfloor', '#ffffff'); WHITE = M('lab_white', '#e8ebef', 0.35)
BLACK = M('lab_black', '#16181d', 0.4, 0.2); ALU = M('alu', '#b8bcc4', 0.3, 0.9); CYAN = neon('cyan', '#39ffd0'); PINK = neon('pink', '#ff4fa8')
PURP = neon('purple', '#9a5aff', 2.5); WOODL = M('T_wood#light', '#f0d8b8')
P = Part('R-lab')
W, D, H = 10, 8, 3.4
# shell
P.add(solid(W + 1, D + 1, 0.4, (0, 0, -0.2), LFLOOR), solid(W + 1, D + 1, 0.4, (0, 0, H + 0.2), PANEL))
for (sx, sy, cx, cy) in ((W + 1, 0.5, 0, -D / 2 - 0.25), (W + 1, 0.5, 0, D / 2 + 0.25), (0.5, D, -W / 2 - 0.25, 0), (0.5, D, W / 2 + 0.25, 0)):
    P.add(solid(sx, sy, H, (cx, cy, H / 2), PANEL))
for y in (-D / 2 + 0.03, D / 2 - 0.03): P.add(box(W, 0.04, 0.05, (0, y, 0.05), CYAN), box(W, 0.04, 0.05, (0, y, H - 0.05), PURP))
for x in (-W / 2 + 0.03, W / 2 - 0.03): P.add(box(0.04, D, 0.05, (x, 0, H - 0.05), PURP))
for k in range(3): P.add(box(0.15, 6, 0.04, (-3 + k * 3, 0, H - 0.02), M('ledpanel', '#ffffff', 0.3, emit=(1, 1, 1), estr=1.5)))
# north: window + desk + 3 monitors
P.add(box(4.6, 0.06, 1.8, (0, D / 2 - 0.02, 2.0), M('D_window_city', '#ffffff', 0.2, emit=(0.6, 0.6, 0.7), estr=0.6)))
for x in (-2.35, 2.35): P.add(box(0.1, 0.12, 1.9, (x, D / 2 - 0.06, 2.0), BLACK))
P.add(box(4.8, 0.12, 0.1, (0, D / 2 - 0.06, 2.95), BLACK), box(4.8, 0.25, 0.08, (0, D / 2 - 0.12, 1.08), BLACK))
P.add(solid(3.6, 0.9, 0.06, (0, D / 2 - 0.65, 0.78), WOODL))
for x in (-1.7, 1.7): P.add(box(0.06, 0.8, 0.76, (x, D / 2 - 0.65, 0.39), ALU))
colbox(3.6, 0.9, 0.8, (0, D / 2 - 0.65, 0.4))
for i, (x, a, scr) in enumerate([(-1.05, 0.35, 'screen_code'), (0, 0, 'screen_map'), (1.05, -0.35, 'screen_sibyl')]):
    mon = [box(0.95, 0.04, 0.56, (0, 0, 0.42), BLACK, bev=0.01), box(0.9, 0.01, 0.51, (0, -0.025, 0.42), M('D_' + scr, '#ffffff', 0.2, emit=(1, 1, 1), estr=1.0)),
           box(0.06, 0.06, 0.3, (0, 0.05, 0.15), ALU), box(0.3, 0.2, 0.02, (0, 0.05, 0.01), ALU)]
    P.add(place(mon, x, D / 2 - 0.55, math.degrees(a), 0.81)); mk('M-it-monitor%d' % i, (x, D / 2 - 1.0, 1.2))
P.add(box(0.5, 0.16, 0.025, (0, D / 2 - 0.95, 0.82), BLACK), box(0.48, 0.14, 0.01, (0, D / 2 - 0.95, 0.835), M('rgbkeys', '#ff4fa8', 0.4, emit=(0.6, 0.2, 1.0), estr=1.2)))
P.add(cyl(0.05, 0.11, (0.9, D / 2 - 0.9, 0.87), M('mug', '#f4f4f4', 0.3), v=12)); mk('M-it-mug', (0.9, D / 2 - 1.1, 1.0))
for k in range(4): P.add(cyl(0.033, 0.13, (-1.5 + k * 0.08, D / 2 - 0.4, 0.875), M('can', '#39ffd0', 0.2, 0.8), v=10))
# the teleport phone on its charging dock
P.add(box(0.14, 0.1, 0.03, (1.5, D / 2 - 0.85, 0.825), BLACK), box(0.05, 0.012, 0.012, (1.5, D / 2 - 0.9, 0.845), CYAN))
mk('M-phone', (1.5, D / 2 - 0.85, 0.85), 180); mk('M-it-phone', (1.5, D / 2 - 1.3, 1.0))
# gaming chair (movable)
ch = [box(0.55, 0.55, 0.1, (0, 0, 0.5), BLACK, bev=0.03), box(0.55, 0.1, 0.8, (0, 0.28, 0.95), BLACK, bev=0.04), box(0.4, 0.11, 0.6, (0, 0.27, 0.95), PINK),
      cyl(0.04, 0.4, (0, 0, 0.27), ALU, v=8)] + [box(0.35, 0.05, 0.04, (math.cos(k * 1.256) * 0.17, math.sin(k * 1.256) * 0.17, 0.05), ALU, rot=(0, 0, k * 1.256)) for k in range(5)]
c = join('X-chair', ch); c.location = (0, 2.4, 0); MOVERS.append(c)
# east wall: server rack, 3D printer bench, pegboard
P.add(solid(0.8, 1.0, 2.2, (W / 2 - 0.45, 1.8, 1.1), BLACK))
for k in range(9):
    P.add(box(0.02, 0.9, 0.18, (W / 2 - 0.86, 1.8, 0.25 + k * 0.22), M('rackface', '#24262c', 0.4, 0.5)))
    for j in range(5): P.add(box(0.02, 0.025, 0.025, (W / 2 - 0.875, 1.45 + j * 0.06, 0.25 + k * 0.22), [CYAN, PINK, M('led_g', '#40ff60', 0.3, emit=(0.2, 1, 0.3), estr=3)][(k + j) % 3]))
mk('M-it-server', (W / 2 - 1.3, 1.8, 1.2)); mk('M-light-rack', (W / 2 - 1.2, 1.8, 1.0))
P.add(solid(0.9, 2.2, 0.06, (W / 2 - 0.5, -1.0, 0.85), WOODL)); colbox(0.9, 2.2, 0.85, (W / 2 - 0.5, -1.0, 0.42))
for y in (-2.0, 0.0): P.add(box(0.8, 0.06, 0.82, (W / 2 - 0.5, y, 0.41), ALU))
pr = [box(0.5, 0.5, 0.06, (0, 0, 0.03), BLACK), box(0.5, 0.5, 0.06, (0, 0, 0.6), BLACK)] + [box(0.04, 0.04, 0.6, (sx * 0.23, sy * 0.23, 0.3), ALU) for sx in (-1, 1) for sy in (-1, 1)]
pr += [box(0.08, 0.08, 0.08, (0, 0, 0.45), CYAN), cyl(0.12, 0.12, (0, 0, 0.12), STONE, v=4, r2=0.06)]
P.add(place(pr, W / 2 - 0.5, -1.4, 0, 0.88)); mk('M-it-printer', (W / 2 - 1.0, -1.4, 1.2))
P.add(box(0.03, 1.8, 1.0, (W / 2 - 0.03, -1.0, 1.8), M('pegboard', '#c8a878', 0.8)))
for k in range(6): P.add(box(0.03, 0.04, 0.3, (W / 2 - 0.07, -1.7 + k * 0.28, 1.8), [IRON, PINK, ALU][k % 3]))
P.add(box(0.3, 0.25, 0.2, (W / 2 - 0.5, -0.4, 0.98), BLACK), box(0.01, 0.2, 0.12, (W / 2 - 0.655, -0.4, 1.0), M('scope', '#40ff60', 0.3, emit=(0.2, 1, 0.3), estr=1.5)))
mk('M-it-scope', (W / 2 - 1.0, -0.4, 1.1))
# west wall: bed with underglow, cat tree, posters, corkboard
P.add(solid(2.0, 3.0, 0.45, (-W / 2 + 1.05, -1.6, 0.25), BLACK), box(1.9, 2.9, 0.2, (-W / 2 + 1.05, -1.6, 0.57), M('duvet', '#2c3a5a', 0.9)))
P.add(box(1.9, 0.6, 0.18, (-W / 2 + 1.05, -2.8, 0.75), WHITE, bev=0.06), box(2.0, 3.0, 0.03, (-W / 2 + 1.05, -1.6, 0.02), PURP))
mk('M-it-bed', (-W / 2 + 2.3, -1.6, 0.8))
P.add(box(0.03, 0.8, 1.1, (-W / 2 + 0.02, -1.0, 1.9), M('D_poster_time', '#ffffff', 0.6))); mk('M-it-poster', (-W / 2 + 0.6, -1.0, 1.7))
P.add(box(0.04, 1.4, 0.9, (-W / 2 + 0.03, 1.4, 1.7), M('cork', '#b08a5a', 0.9)), box(0.045, 0.3, 0.2, (-W / 2 + 0.03, 1.15, 1.85), M('D_card_steve', '#ffffff', 0.7)))
for k in range(5): P.add(box(0.045, 0.18, 0.22, (-W / 2 + 0.03, 1.5 + (k % 3) * 0.3, 1.5 + (k // 3) * 0.4), M('note%d' % (k % 3), ['#ffe066', '#ff9ec8', '#9ee6ff'][k % 3], 0.8), rot=(R.uniform(-0.1, 0.1), 0, 0)))
mk('M-it-steve', (-W / 2 + 0.6, 1.15, 1.7))
ct = [cyl(0.08, 1.4, (0, 0, 0.7), ROPE, v=10), cyl(0.35, 0.08, (0, 0, 0.04), M('carpet', '#7a6aa8', 0.95), v=16), cyl(0.3, 0.08, (0, 0, 0.8), M('carpet', '#7a6aa8'), v=16), cyl(0.32, 0.08, (0.1, 0, 1.42), M('carpet', '#7a6aa8'), v=16)]
P.add(place(ct, -W / 2 + 0.6, 3.2)); colbox(0.7, 0.7, 1.4, (-W / 2 + 0.6, 3.2, 0.7)); mk('M-an-cat-lab', (-W / 2 + 0.7, 3.2, 1.47), 120); mk('M-it-cat', (-W / 2 + 1.2, 3.0, 1.2))
# south wall: door, whiteboard, fridge, bookshelf
P.add(box(1.1, 0.08, 2.2, (-2.6, -D / 2 + 0.06, 1.1), WHITE), box(0.05, 0.1, 0.05, (-2.2, -D / 2 + 0.12, 1.05), ALU)); mk('M-it-door', (-2.6, -D / 2 + 0.7, 1.2))
P.add(box(2.0, 0.04, 1.1, (0.4, -D / 2 + 0.03, 1.6), M('D_whiteboard', '#ffffff', 0.3))); mk('M-it-whiteboard', (0.4, -D / 2 + 0.7, 1.4))
P.add(solid(0.6, 0.6, 0.9, (2.1, -D / 2 + 0.35, 0.45), M('fridge', '#ff4fa8', 0.3, 0.2)), box(0.55, 0.02, 0.05, (2.1, -D / 2 + 0.66, 0.8), ALU)); mk('M-it-fridge', (2.1, -D / 2 + 1.0, 0.8))
P.add(solid(1.6, 0.4, 2.0, (3.6, -D / 2 + 0.22, 1.0), WOODL))
for z in range(4):
    for b in range(9): P.add(box(0.13, 0.28, R.uniform(0.3, 0.4), (3.0 + b * 0.15, -D / 2 + 0.25, 0.3 + z * 0.45), M('lbook%d' % (b % 4), ['#ff4fa8', '#39ffd0', '#f4f4f4', '#2a2f3a'][b % 4], 0.6)))
P.add(sph(0.12, (3.4, -D / 2 + 0.25, 2.12), M('steel', '#b8bec6', 0.25, 0.9), s=(1, 1, 1.2))); mk('M-it-books', (3.6, -D / 2 + 0.9, 1.3))
# centre: holo table (SIBYL projector)
P.add(cyl(0.6, 0.85, (0, 0, 0.425), BLACK, v=32), tor(0.6, 0.03, (0, 0, 0.86), CYAN, maj=32, mn=6), cyl(0.5, 0.02, (0, 0, 0.87), M('hologlass', '#0a2a30', 0.05, emit=(0.05, 0.4, 0.45), estr=1.0), v=32))
colbox(1.2, 1.2, 0.86, (0, 0, 0.43)); mk('M-sibyl', (0, 0, 1.55)); mk('M-it-sibyl', (0, -0.9, 1.2))
# failed time ring prototype (corner)
P.add(tor(0.9, 0.12, (-3.6, 2.8, 1.05), ALU, rot=(math.pi / 2, 0, 0.6), maj=32, mn=10), tor(0.9, 0.03, (-3.6, 2.8, 1.05), PINK, rot=(math.pi / 2, 0, 0.6), maj=32, mn=6))
P.add(box(0.8, 0.5, 0.1, (-3.6, 2.8, 0.05), BLACK), box(0.4, 0.02, 0.15, (-3.6, 2.55, 0.15), M('sign_v1', '#ffcc00', 0.5))); colbox(1.2, 0.6, 2.0, (-3.6, 2.8, 1.0), (0, 0, 0.6)); mk('M-it-ring', (-3.0, 2.2, 1.2))
# plant Gerald + robot vacuum
P.add(cyl(0.18, 0.35, (3.3, 3.4, 0.175), WHITE, v=14, r2=0.14)); [P.add(sph(0.15, (3.3 + math.cos(k) * 0.12, 3.4 + math.sin(k) * 0.12, 0.5 + (k % 2) * 0.12), LEAVES, s=(0.6, 0.6, 1.4))) for k in range(6)]
mk('M-it-plant', (3.3, 2.9, 0.7)); colbox(0.4, 0.4, 0.8, (3.3, 3.4, 0.4))
vac = [cyl(0.17, 0.08, (0, 0, 0.05), BLACK, v=20), cyl(0.05, 0.01, (0, -0.08, 0.095), CYAN, v=10)]
v = join('X-vacuum', vac); v.location = (2.0, -1.0, 0); MOVERS.append(v); mk('M-it-vacuum', (2.0, -1.0, 0.3))
# rug
P.add(cyl(1.8, 0.01, (0, 0, 0.005), M('labrug', '#2a2240', 0.95), v=40), tor(1.75, 0.02, (0, 0, 0.01), PURP, maj=40, mn=4))
mk('M-start', (-1.2, -1.5, 0), 20); mk('M-cam-intro1', (3.8, -3.2, 2.6)); mk('M-cam-intro2', (-0.6, 1.2, 1.5)); mk('M-cam-phone', (1.1, 2.3, 1.3)); mk('M-cam-wide', (-4.2, -3.5, 2.9))
mk('M-light-desk', (0, 3.2, 2.2)); mk('M-light-bed', (-3.8, -1.6, 0.6)); mk('M-light-main', (0, 0, 3.0))
col = finish_cols('LAB')
export('lab', anim=False, objs=[P.join(), col] + MOVERS + MARK)
