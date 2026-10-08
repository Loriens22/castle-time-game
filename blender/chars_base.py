"""(Adapted from Steve The PC Repair Man.) Characters: one shared humanoid skeleton, per-character procedural meshes (lofted, subdivided),
distance-based skin weights, rigid bone-parented heads with animatable eyes/mouth.
Animations (shared by every human) are keyframed procedurally and exported to anims.glb."""
import bpy, math, sys, os
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(__file__))
from lib import *

# ------------------------------------------------------------------ skeleton (Blender: Z up, facing -Y)
J = dict(root=(0, 0, 0), hips=(0, 0, 0.96), spine=(0, 0, 1.08), chest=(0, 0, 1.26), neck=(0, 0, 1.46), head=(0, 0, 1.55),
         head_end=(0, 0, 1.82))
for s, sx in (('L', 1), ('R', -1)):
    J['sh_' + s] = (0.19 * sx, 0.0, 1.42); J['el_' + s] = (0.235 * sx, 0.02, 1.15); J['wr_' + s] = (0.265 * sx, 0.0, 0.91)
    J['hd_' + s] = (0.275 * sx, -0.01, 0.80)
    J['hp_' + s] = (0.095 * sx, 0.0, 0.93); J['kn_' + s] = (0.10 * sx, -0.01, 0.51); J['an_' + s] = (0.10 * sx, 0.02, 0.09)
    J['to_' + s] = (0.10 * sx, -0.13, 0.03)
BONES = [('root', 'root', None, (0, 0, 0.12)), ('hips', 'hips', 'root', 'spine'), ('spine', 'spine', 'hips', 'chest'),
         ('chest', 'chest', 'spine', 'neck'), ('neck', 'neck', 'chest', 'head'), ('head', 'head', 'neck', 'head_end')]
for s in 'LR':
    BONES += [('upper_arm_' + s, 'sh_' + s, 'chest', 'el_' + s), ('forearm_' + s, 'el_' + s, 'upper_arm_' + s, 'wr_' + s),
              ('hand_' + s, 'wr_' + s, 'forearm_' + s, 'hd_' + s), ('thigh_' + s, 'hp_' + s, 'hips', 'kn_' + s),
              ('shin_' + s, 'kn_' + s, 'thigh_' + s, 'an_' + s), ('foot_' + s, 'an_' + s, 'shin_' + s, 'to_' + s)]
SEG = {}  # bone -> (head, tail) vectors

def make_rig():
    ad = bpy.data.armatures.new('rig'); ob = bpy.data.objects.new('rig', ad); bpy.context.collection.objects.link(ob)
    select([ob]); bpy.ops.object.mode_set(mode='EDIT')
    for name, h, parent, t in BONES:
        b = ad.edit_bones.new(name); b.head = Vector(J[h]); b.tail = Vector(J[t]) if isinstance(t, str) else Vector(t)
        if name.startswith('foot'): b.align_roll(Vector((0, 0, 1)))
        else: b.align_roll(Vector((0, -1, 0)))
        if parent: b.parent = ad.edit_bones[parent]; b.use_connect = False
        SEG[name] = (b.head.copy(), b.tail.copy())
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob

def seg_dist(p, a, b):
    ab = b - a; t = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length

def weight(o, bones, sharp=4.0, bias=None):
    """distance based weights restricted to a bone list."""
    vg = {b: o.vertex_groups.new(name=b) for b in bones}
    for v in o.data.vertices:
        p = o.matrix_world @ v.co
        ws = []
        for b in bones:
            d = seg_dist(p, *SEG[b]) + 0.015
            w = 1 / d ** sharp
            if bias and b in bias: w *= bias[b]
            ws.append(w)
        tot = sum(ws); ws = [w / tot for w in ws]
        top = sorted(range(len(bones)), key=lambda i: -ws[i])[:3]
        s = sum(ws[i] for i in top)
        for i in top:
            if ws[i] / s > 0.02: vg[bones[i]].add([v.index], ws[i] / s, 'REPLACE')

def rigid(o, bone):
    vg = o.vertex_groups.new(name=bone); vg.add([v.index for v in o.data.vertices], 1.0, 'REPLACE')

def V(*a): return Vector(a)

def lerp(a, b, t): return Vector(a).lerp(Vector(b), t)

# ------------------------------------------------------------------ body part builders
def torso(c, m_top, m_bot):
    b = c.get('belly', 1.0); w = c.get('width', 1.0); fem = c.get('fem', 0)
    top = [(1.00, .150, .100), (1.10, .145 * b, .108 * b), (1.20, .155 * (1 + (b - 1) * .6), .112 * b), (1.30, .172, .112 + fem * .015),
           (1.38, .185, .105), (1.43, .175, .095), (1.475, .11, .07), (1.50, .058, .052)]
    bot = [(0.855, .05, .035), (0.875, .12, .075), (0.92, .155, .105), (1.00, .150, .100), (1.03, .15, .10)]
    def rings(lst): return [((0, 0.004, z), rx * w, ry * w) for z, rx, ry in lst]
    t = loft(rings(top), m_top, 'torso_top', seg=20); weight(t, ['hips', 'spine', 'chest', 'neck'])
    p = loft(rings(bot), m_bot, 'torso_bot', seg=20); weight(p, ['hips', 'spine', 'thigh_L', 'thigh_R'], bias={'hips': 3})
    return [t, p]

def limb_rings(pts, radii, n=10):
    out = []; P = [Vector(p) for p in pts]
    L = [0]
    for i in range(1, len(P)): L.append(L[-1] + (P[i] - P[i - 1]).length)
    for k in range(n + 1):
        d = L[-1] * k / n
        for i in range(1, len(P)):
            if d <= L[i] + 1e-9: break
        t = (d - L[i - 1]) / max(1e-9, L[i] - L[i - 1]); c = P[i - 1].lerp(P[i], t)
        r = radii[i - 1] + (radii[i] - radii[i - 1]) * t
        out.append((c, r, r * 0.92))
    return out

def arm(c, s, m_sleeve, m_skin, m_hand):
    w = c.get('width', 1.0); sl = c.get('sleeve', 'long')
    sh = Vector(J['sh_' + s]); el = Vector(J['el_' + s]); wr = Vector(J['wr_' + s]); hd = Vector(J['hd_' + s])
    start = sh + Vector((-0.02 * (1 if s == 'L' else -1), 0, 0.01))
    parts = []
    bones = ['chest', 'upper_arm_' + s, 'forearm_' + s, 'hand_' + s]
    if sl == 'long':
        a = loft(limb_rings([start, el, wr - (wr - el) * 0.02], [0.068 * w, 0.055 * w, 0.047 * w], 12), m_sleeve, 'arm', seg=14)
        cuff = loft(limb_rings([wr + (el - wr).normalized() * 0.04, wr + (el - wr).normalized() * 0.005], [0.047 * w, 0.047 * w], 2), m_sleeve, 'cuff', seg=14)
        weight(a, bones, bias={'chest': 0.4}); weight(cuff, bones); parts += [a, cuff]
        wrist = loft(limb_rings([wr + (el - wr).normalized() * 0.02, wr + (hd - wr) * 0.3], [0.034, 0.034], 2), m_skin, 'wrist', seg=12)
        weight(wrist, bones); parts.append(wrist)
    else:
        mid = sh.lerp(el, 0.55)
        slv = loft(limb_rings([start, mid], [0.068 * w, 0.06 * w], 5), m_sleeve, 'sleeve', seg=14)
        a = loft(limb_rings([sh.lerp(el, 0.3), el, wr + (hd - wr) * 0.3], [0.056, 0.049, 0.038], 10), m_skin, 'arm', seg=12)
        weight(slv, bones, bias={'chest': 0.4}); weight(a, bones); parts += [slv, a]
    # mitten hand + thumb
    d = (hd - wr).normalized(); hc = wr + d * 0.07
    h = sph(0.045, hc, m_hand, (1.0, 0.75, 1.35), seg=16, rings=10)
    th = sph(0.018, wr + d * 0.045 + Vector((0, -0.03, 0)), m_hand, (1, 1, 1.6), seg=10, rings=6)
    hand = join('hand', [h, th]); rigid(hand, 'hand_' + s); parts.append(hand)
    if c.get('watch') and s == 'L':
        wt = tor(0.038, 0.009, wr + (el - wr).normalized() * 0.03, M('watch', '#222222', 0.3, 0.6), rot=(0, 0, 0))
        rigid(wt, 'forearm_' + s); parts.append(wt)
    return parts

def leg(c, s, m_pants, m_shoe, m_skin):
    w = c.get('width', 1.0); hp = Vector(J['hp_' + s]); kn = Vector(J['kn_' + s]); an = Vector(J['an_' + s]); to = Vector(J['to_' + s])
    parts = []
    bones = ['hips', 'thigh_' + s, 'shin_' + s, 'foot_' + s]
    if c.get('skirt'):
        lg = loft(limb_rings([hp.lerp(kn, 0.5), kn, an + V(0, 0, 0.04)], [0.06, 0.05, 0.036], 10), m_skin, 'leg', seg=12)
    else:
        top = hp + V(0, 0, 0.06)
        lg = loft(limb_rings([top, kn, an + V(0, 0, 0.03)], [0.082 * w, 0.064 * w, 0.056 * w], 14), m_pants, 'leg', seg=14)
    weight(lg, bones, bias={'hips': 0.5}); parts.append(lg)
    sh = box(0.095, 0.2, 0.08, (an.x, an.y - 0.035, 0.045), m_shoe); bevel(sh, 0.03, 3)
    subsurf(sh, 1); rigid(sh, 'foot_' + s); parts.append(sh)
    sole = box(0.1, 0.205, 0.022, (an.x, an.y - 0.035, 0.011), M('sole', '#2a2522', 0.9)); bevel(sole, 0.008, 2); rigid(sole, 'foot_' + s)
    parts.append(sole)
    return parts

def skirt(c, m):
    prof = [(0.155, 1.0), (0.17, 0.92), (0.2, 0.75), (0.235, 0.55), (0.25, 0.46)]
    o = lathe([(r, z) for r, z in prof], m, 'skirt', seg=28)
    # open-ended lathe: remove caps by keeping as is (caps hidden inside)
    vg = {b: o.vertex_groups.new(name=b) for b in ('hips', 'thigh_L', 'thigh_R')}
    for v in o.data.vertices:
        h = max(0, min(1, (1.0 - v.co.z) / 0.5)); side = 'thigh_L' if v.co.x > 0 else 'thigh_R'
        sw = h * min(1, abs(v.co.x) / 0.12) * 0.7
        vg['hips'].add([v.index], 1 - sw, 'REPLACE'); vg[side].add([v.index], sw, 'REPLACE')
    return [o]

def coat(c, m):
    w = c.get('width', 1.0)
    prof = [(0.5, .19, .14), (0.62, .2, .15), (0.8, .19, .14), (0.95, .175, .125), (1.08, .17 * c.get('belly', 1), .125 * c.get('belly', 1)),
            (1.2, .18, .13), (1.32, .195, .13), (1.4, .2, .12), (1.45, .17, .1), (1.49, .09, .075)]
    o = loft([((0, 0.004, z), rx * w, ry * w) for z, rx, ry in prof], m, 'coat', seg=24, cap=False)
    vg = {b: o.vertex_groups.new(name=b) for b in ('hips', 'spine', 'chest', 'neck', 'thigh_L', 'thigh_R')}
    for v in o.data.vertices:
        z = v.co.z
        if z > 0.95:
            weight_list = [('chest', max(0, min(1, (z - 1.1) / 0.2))), ('spine', 0)]
            cw = max(0, min(1, (z - 1.12) / 0.16)); vg['chest'].add([v.index], cw, 'REPLACE'); vg['spine'].add([v.index], 1 - cw, 'REPLACE')
        else:
            h = max(0, min(1, (0.95 - z) / 0.45)); side = 'thigh_L' if v.co.x > 0 else 'thigh_R'
            sw = h * min(1, abs(v.co.x) / 0.1) * 0.6
            vg['hips'].add([v.index], 1 - sw, 'REPLACE'); vg[side].add([v.index], sw, 'REPLACE')
    # lapels / buttons
    return [o]

# ------------------------------------------------------------------ heads
HC = Vector((0, 0, 1.655))
def head(c, m_skin):
    objs = []; hs = c.get('head', 1.0)
    sk = sph(0.125 * hs, HC, m_skin, (0.95, 1.0, 1.1), seg=28, rings=18)
    jaw = sph(0.1 * hs, HC + V(0, -0.02, -0.06), m_skin, (0.95, 0.95, 0.8), seg=20, rings=12)
    nose = sph(0.024, HC + V(0, -0.128 * hs, -0.01), m_skin, (0.9, 1.1, 1.25 * c.get('nose', 1)), seg=14, rings=8)
    ears = [sph(0.03, HC + V(sx * 0.118 * hs, 0.0, 0), m_skin, (0.45, 0.8, 1.1), seg=12, rings=8) for sx in (1, -1)]
    objs += [sk, jaw, nose] + ears
    brow = M('brow_' + c['name'], c.get('brow', c.get('hair', '#333333')), 0.9)
    for sx in (1, -1):
        b = box(0.045, 0.014, 0.012 * c.get('browthick', 1), HC + V(sx * 0.046, -0.112 * hs, 0.045), brow, rot=(0, sx * -0.12 + c.get('browtilt', 0) * sx, 0))
        bevel(b, 0.005, 2); objs.append(b)
    if c.get('cheeks'):
        for sx in (1, -1): objs.append(sph(0.022, HC + V(sx * 0.07, -0.098, -0.03), M('blush', '#e89a96', 0.8), (1, 0.4, 0.8), seg=10, rings=6))
    hair = c.get('hairstyle'); hm = M('hair_' + c['name'], c.get('hair', '#333333'), 0.85)
    if hair == 'short':
        cap = sph(0.132 * hs, HC + V(0, 0.01, 0.018), hm, (0.98, 1.0, 1.0), seg=24, rings=14)
        wsel(cap, lambda p: not (((p.z > HC.z + 0.045) or (p.y > -0.02 and p.z > HC.z - 0.075 + max(0, -p.y) * 0.8)) and not (p.y < -0.07 and p.z < HC.z + 0.08)))
        _delete_selected(cap)
        quiff = sph(0.06, HC + V(0.02, -0.085, 0.105), hm, (1.4, 0.9, 0.55)); objs += [cap, quiff]
        if c.get('sideburns'):
            for sx in (1, -1): objs.append(box(0.02, 0.03, 0.05, HC + V(sx * 0.118, -0.03, 0.0), hm))
    elif hair == 'bun':
        cap = sph(0.134 * hs, HC + V(0, 0.012, 0.02), hm, (0.99, 1.0, 1.0), seg=24, rings=14)
        wsel(cap, lambda q: (q.z < HC.z - 0.01 - max(0, q.y) * 0.6) or (q.y < -0.07 and q.z < HC.z + 0.07))
        _delete_selected(cap)
        bun = sph(0.065, HC + V(0, 0.07, 0.11), hm, (1, 1, 0.85), seg=18, rings=10)
        curls = [sph(0.03, HC + V(math.cos(a) * 0.115, math.sin(a) * 0.1 + 0.01, 0.06), hm, seg=10, rings=6) for a in [i * math.pi / 5 + math.pi for i in range(6)]]
        objs += [cap, bun] + curls
    elif hair == 'slick':
        cap = sph(0.133 * hs, HC + V(0, 0.015, 0.025), hm, (0.98, 1.05, 0.98), seg=24, rings=14)
        wsel(cap, lambda q: (q.z < HC.z - max(0, q.y) * 0.7) or (q.y < -0.08 and q.z < HC.z + 0.085))
        _delete_selected(cap); objs.append(cap)
    elif hair == 'buzz':
        cap = sph(0.128 * hs, HC + V(0, 0.005, 0.012), hm, (0.97, 1.0, 1.0), seg=24, rings=14)
        wsel(cap, lambda q: (q.z < HC.z - 0.005 - max(0, q.y) * 0.6) or (q.y < -0.07 and q.z < HC.z + 0.08))
        _delete_selected(cap); objs.append(cap)
    elif hair == 'blonde_bun':
        cap = sph(0.134 * hs, HC + V(0, 0.012, 0.02), hm, (0.99, 1.0, 1.0), seg=24, rings=14)
        wsel(cap, lambda q: (q.z < HC.z - 0.03) or (q.y < -0.075 and q.z < HC.z + 0.06))
        _delete_selected(cap)
        objs += [cap, sph(0.055, HC + V(0, 0.115, 0.03), hm, (1, 0.9, 1))]
    if c.get('mustache'):
        mu = sph(0.04, HC + V(0, -0.118, -0.04), M('stache_' + c['name'], c.get('mustache'), 0.9), (1.6, 0.6, 0.45), seg=16, rings=8)
        objs.append(mu)
    if c.get('goatee'):
        objs.append(sph(0.025, HC + V(0, -0.1, -0.115), hm, (1, 0.7, 1.3), seg=12, rings=8))
    if c.get('beard'):
        bd = sph(0.11 * hs, HC + V(0, -0.025, -0.07), hm, (1.0, 0.95, 0.75), seg=22, rings=12)
        wsel(bd, lambda q: q.z > HC.z - 0.04 or q.y > 0.02)
        _delete_selected(bd); objs.append(bd)
    if c.get('hat') == 'beanie':
        hb = sph(0.137, HC + V(0, 0.005, 0.03), M('beanie', c.get('hatcol', '#22324a'), 0.95), (1, 1, 1.0), seg=24, rings=14)
        wsel(hb, lambda q: q.z < HC.z + 0.035)
        _delete_selected(hb)
        rim = tor(0.128, 0.018, HC + V(0, 0.005, 0.045), M('beanie', '#22324a'), maj=28, mn=8)
        pom = sph(0.03, HC + V(0, 0.0, 0.17), M('pom', '#e8e8e8', 1.0))
        objs += [hb, rim, pom]
        gm = M('goggle', '#ff9a2a', 0.15, 0.3)
        objs.append(box(0.17, 0.03, 0.04, HC + V(0, -0.115, 0.075), gm, bev=0.012))
    if c.get('hat') == 'cap_air':
        objs.append(cyl(0.085, 0.05, HC + V(0, 0.01, 0.13), M('uni', '#1f3a68', 0.6), rot=(0.25, 0, 0)))
    head_mesh = join('head', objs)
    # eyes (separate so they can blink), mouth (separate so it can talk)
    eyes = []
    for s, sx in (('L', 1), ('R', -1)):
        ec = HC + V(sx * 0.044, -0.104 * hs, 0.012)
        wh = sph(0.024, ec, M('eyewhite', '#f4f1ea', 0.3), (1, 0.7, 1.05), seg=14, rings=8)
        pu = sph(0.0125, ec + V(0, -0.016, 0.0), M('pupil', c.get('eyecol', '#2b1d14'), 0.2), (1, 0.6, 1.1), seg=12, rings=8)
        hl = sph(0.004, ec + V(0.004, -0.024, 0.006), M('eyehl', '#ffffff', 0.1, emit=(1, 1, 1), estr=0.6), seg=6, rings=4)
        e = join('eye_' + s, [wh, pu, hl], origin=ec); eyes.append(e)
    mouth = sph(0.028, HC + V(0, -0.11 * hs, -0.052), M('mouth', '#4a1c1a', 0.6), (1.15, 0.45, 0.22), seg=14, rings=8)
    mouth.name = 'mouth'; set_origin(mouth, HC + V(0, -0.11 * hs, -0.052))
    extra = []
    if c.get('glasses'):
        gm = M('frames_' + c['name'], c.get('glasses'), 0.3, 0.2)
        lens = M('lens', '#bcd6e0', 0.05, 0.0, alpha=0.25)
        rims = []; shape = c.get('glshape', 'round')
        for sx in (1, -1):
            ec = HC + V(sx * 0.046, -0.124 * hs, 0.012)
            if shape == 'round': rims.append(tor(0.03, 0.004, ec, gm, rot=(math.pi / 2, 0, 0), maj=20, mn=6))
            else:
                for dz in (0.02, -0.02): rims.append(box(0.066, 0.007, 0.006, ec + V(0, 0, dz), gm))
                for dx in (0.03, -0.03): rims.append(box(0.006, 0.007, 0.046, ec + V(dx, 0, 0), gm))
            if c.get('shades'):
                rims.append(box(0.062, 0.004, 0.038, ec + V(0, 0.001, 0), M('shades', '#111111', 0.1, 0.5)) if shape != 'round'
                            else cyl(0.029, 0.003, ec, M('shades', '#111111', 0.1, 0.5), rot=(math.pi / 2, 0, 0)))
            rims.append(box(0.006, 0.12, 0.006, HC + V(sx * 0.085, -0.065, 0.02), gm))
        rims.append(box(0.03, 0.006, 0.006, HC + V(0, -0.128 * hs, 0.02), gm))
        g = join('glasses', rims); extra.append(g)
    return head_mesh, eyes, mouth, extra

def wsel(o, fn):
    for v in o.data.vertices: v.select = bool(fn(o.matrix_world @ v.co))

def _delete_selected(o):
    import bmesh as _bm
    me = o.data; bm = _bm.new(); bm.from_mesh(me)
    sel = [v for v in bm.verts if me.vertices[v.index].select]
    _bm.ops.delete(bm, geom=sel, context='VERTS'); bm.to_mesh(me); bm.free()

def bone_parent(o, rig, bone):
    mw = o.matrix_world.copy(); o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update(); o.matrix_world = mw

# ------------------------------------------------------------------ cat (own rig)
def build_cat(name='cat', fur='#3a3a40', belly='#f2f2f2'):
    clear_scene()
    ad = bpy.data.armatures.new('catrig'); rig = bpy.data.objects.new('catrig', ad); bpy.context.collection.objects.link(rig)
    select([rig]); bpy.ops.object.mode_set(mode='EDIT')
    def bn(n, h, t, p=None):
        b = ad.edit_bones.new(n); b.head = Vector(h); b.tail = Vector(t); b.align_roll(Vector((0, 0, 1)) if abs(b.tail.z - b.head.z) < 0.5 * (b.tail - b.head).length else Vector((0, -1, 0)))
        if p: b.parent = ad.edit_bones[p]
        SEG[n] = (b.head.copy(), b.tail.copy())
    bn('c_root', (0, 0, 0), (0, 0, 0.05)); bn('c_hips', (0, 0.12, 0.2), (0, 0.0, 0.21), 'c_root'); bn('c_chest', (0, 0.0, 0.21), (0, -0.12, 0.22), 'c_hips')
    bn('c_neck', (0, -0.12, 0.22), (0, -0.16, 0.28), 'c_chest'); bn('c_head', (0, -0.16, 0.28), (0, -0.24, 0.3), 'c_neck')
    prev = 'c_hips'; tp = Vector((0, 0.14, 0.21))
    for i in range(4):
        nt = tp + Vector((0, 0.07, 0.035 + 0.01 * i)); bn('c_tail%d' % i, tp, nt, prev); prev = 'c_tail%d' % i; tp = nt
    for s, sx in (('L', 1), ('R', -1)):
        for fb, y, par in (('f', -0.1, 'c_chest'), ('b', 0.1, 'c_hips')):
            bn('c_%sleg1_%s' % (fb, s), (sx * 0.045, y, 0.19), (sx * 0.045, y, 0.1), par)
            bn('c_%sleg2_%s' % (fb, s), (sx * 0.045, y, 0.1), (sx * 0.045, y - 0.01, 0.015), 'c_%sleg1_%s' % (fb, s))
    bpy.ops.object.mode_set(mode='OBJECT')
    fm = M('fur_' + name, fur, 0.95); bm_ = M('furw_' + name, belly, 0.95)
    parts = []
    bodyo = loft([((0, 0.15, 0.2), .035, .04), ((0, 0.1, 0.205), .07, .075), ((0, 0.0, 0.21), .075, .08), ((0, -0.08, 0.22), .07, .078), ((0, -0.13, 0.23), .045, .05)], fm, 'cbody', seg=16)
    weight(bodyo, ['c_hips', 'c_chest', 'c_neck']); parts.append(bodyo)
    chestw = sph(0.05, (0, -0.1, 0.19), bm_, (0.9, 0.7, 1.1)); rigid(chestw, 'c_chest'); parts.append(chestw)
    tl = loft(limb_rings([Vector((0, 0.13, 0.21))] + [SEG['c_tail%d' % i][1] for i in range(4)], [0.022, 0.02, 0.019, 0.018, 0.016], 16), fm, 'tail', seg=10)
    weight(tl, ['c_hips', 'c_tail0', 'c_tail1', 'c_tail2', 'c_tail3'], sharp=6); parts.append(tl)
    tip = sph(0.017, SEG['c_tail3'][1], bm_); rigid(tip, 'c_tail3'); parts.append(tip)
    for s, sx in (('L', 1), ('R', -1)):
        for fb, y in (('f', -0.1), ('b', 0.1)):
            a, b_ = SEG['c_%sleg1_%s' % (fb, s)]; _, c2 = SEG['c_%sleg2_%s' % (fb, s)]
            lg = loft(limb_rings([a + Vector((0, 0, 0.02)), b_, c2], [0.026, 0.02, 0.016], 10), fm, 'leg', seg=10)
            weight(lg, ['c_hips' if fb == 'b' else 'c_chest', 'c_%sleg1_%s' % (fb, s), 'c_%sleg2_%s' % (fb, s)]); parts.append(lg)
            paw = sph(0.02, c2 + Vector((0, -0.01, 0.0)), bm_, (1, 1.3, 0.6)); rigid(paw, 'c_%sleg2_%s' % (fb, s)); parts.append(paw)
    body = join('cbody', parts); md = body.modifiers.new('arm', 'ARMATURE'); md.object = rig; body.parent = rig
    # head
    hc = Vector((0, -0.2, 0.3))
    hd = [sph(0.062, hc, fm, (1.1, 1.0, 0.92)), sph(0.03, hc + Vector((0, -0.045, -0.02)), bm_, (1.2, 0.9, 0.8))]
    for sx in (1, -1):
        ear = cyl(0.025, 0.05, hc + Vector((sx * 0.04, 0.0, 0.055)), fm, v=4, r2=0.0, rot=(0, sx * -0.3, 0)); hd.append(ear)
        hd.append(cyl(0.015, 0.03, hc + Vector((sx * 0.04, -0.006, 0.05)), M('earpink', '#e8a0a0', 0.8), v=4, r2=0, rot=(0, sx * -0.3, 0)))
    hd.append(sph(0.008, hc + Vector((0, -0.066, -0.005)), M('catnose', '#d77a85', 0.5)))
    for sx in (1, -1):
        for k in range(3):
            hd.append(box(0.07, 0.002, 0.002, hc + Vector((sx * 0.055, -0.05, -0.015 + k * 0.008)), M('whisk', '#eeeeee', 0.5), rot=(0, sx * (k - 1) * 0.15, sx * 0.1)))
    head_m = join('chead', hd)
    eyes = []
    for s, sx in (('L', 1), ('R', -1)):
        ec = hc + Vector((sx * 0.026, -0.052, 0.012))
        e1 = sph(0.014, ec, M('cateye', '#c8d84a', 0.15, emit=(0.4, 0.5, 0.05), estr=0.4), (1, 0.6, 1)); e2 = box(0.004, 0.01, 0.018, ec + Vector((0, -0.007, 0)), M('catpupil', '#050505', 0.2))
        eyes.append(join('eye_' + s, [e1, e2], origin=ec))
    for o in [head_m] + eyes: bone_parent(o, rig, 'c_head')
    # animations
    anim_cat(rig)
    export(name, anim=True, objs=[rig, body, head_m] + eyes)

# ------------------------------------------------------------------ animation helpers
FPS = 24
def keyframe_action(rig, name, frames, posefn, loop=True):
    act_ = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act_
    for pb in rig.pose.bones: pb.rotation_mode = 'XYZ'
    for f in range(frames + (1 if loop else 0)):
        t = f / frames
        for pb in rig.pose.bones: pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0)
        pose = posefn(t)
        for bname, val in pose.items():
            if bname.endswith('@loc'): continue
            pb = rig.pose.bones[bname]
            pb.rotation_euler = tuple(math.radians(a) for a in val)
        for bname, val in pose.items():
            if bname.endswith('@loc'): rig.pose.bones[bname[:-4]].location = val
        for pb in rig.pose.bones:
            pb.keyframe_insert('rotation_euler', frame=f + 1)
            if pb.name in ('root', 'hips', 'c_root', 'c_hips'): pb.keyframe_insert('location', frame=f + 1)
    tr = rig.animation_data.nla_tracks.new(); tr.name = name; st = tr.strips.new(name, 1, act_); act_.use_fake_user = True
    rig.animation_data.action = None

def S(t, ph=0.0): return math.sin(2 * math.pi * (t + ph))
def C(t, ph=0.0): return math.cos(2 * math.pi * (t + ph))
def mir(p):
    """mirror L pose values to R: negate Y and Z rotations."""
    out = dict(p)
    for k, v in p.items():
        if k.endswith('_L'): out[k[:-2] + '_R'] = (v[0], -v[1], -v[2])
    return out

def arms_rest(p, out=8):
    p.setdefault('upper_arm_L', (0, 0, out)); p.setdefault('upper_arm_R', (0, 0, -out))
    p.setdefault('forearm_L', (12, 0, 0)); p.setdefault('forearm_R', (12, 0, 0)); return p

def P_idle(t):
    b = S(t)
    return arms_rest({'chest': (1.5 * b, 0, 0), 'spine': (0.8 * b, 0, 0), 'neck': (-0.5 * b, 2 * S(t, .2), 0), 'head': (1 * S(t, .3), 3 * S(t * 0.5), 0),
            'upper_arm_L': (2 * b, 0, 7 + b), 'upper_arm_R': (2 * b, 0, -7 - b), 'hips@loc': (0.006 * S(t * 0.5), 0.003 * b, 0),
            'hips': (0, 0, 1.2 * S(t * 0.5))})

def walkcycle(t, amp=1.0, lean=4, arm=1.0, knee=1.0, bounce=0.03, crouch=0.0):
    p = {}
    ph = 2 * math.pi * t
    for s, o in (('L', 0), ('R', math.pi)):
        a = ph + o
        th = 26 * amp * math.sin(a)
        kn = -(8 + 50 * knee * max(0, math.sin(a + 1.6))) * amp - 4
        ft = -12 * amp * math.sin(a - 0.6)
        p['thigh_' + s] = (th + crouch * 40, 0, 0); p['shin_' + s] = (kn - crouch * 75, 0, 0); p['foot_' + s] = (ft + crouch * 30, 0, 0)
        sx = 1 if s == 'L' else -1
        p['upper_arm_' + s] = (-20 * arm * math.sin(a) + crouch * 20, 0, sx * 7); p['forearm_' + s] = (16 + 18 * arm * max(0, -math.sin(a)) + crouch * 30, 0, 0)
    p['hips@loc'] = (0, -abs(math.cos(ph)) * bounce + bounce * 0.5 - crouch * 0.25, 0)
    p['hips'] = (0, 6 * amp * math.sin(ph), 0); p['spine'] = (lean + crouch * 15, -4 * amp * math.sin(ph), 0); p['chest'] = (crouch * 10, -3 * amp * math.sin(ph), 0)
    p['neck'] = (-lean * 0.5 - crouch * 18, 3 * amp * math.sin(ph), 0); p['head'] = (-crouch * 6, 0, 0)
    return p

def P_walk(t): return walkcycle(t)
def P_run(t):
    p = walkcycle(t, amp=1.5, lean=12, arm=1.6, knee=1.6, bounce=0.06)
    for s in 'LR': p['forearm_' + s] = (75 + 20 * math.sin(2 * math.pi * t + (0 if s == 'L' else math.pi)), 0, 0)
    return p
def P_sneak(t):
    p = walkcycle(t, amp=0.7, lean=8, arm=0.3, knee=0.6, bounce=0.015, crouch=0.6)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (35, 0, sx * 14); p['forearm_' + s] = (70, 0, 0)
    return p
def P_crouch(t):
    p = walkcycle(0.0, amp=0.0, lean=8, crouch=0.6)
    p['chest'] = (6 + 1.5 * S(t), 0, 0)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (35, 0, sx * 14); p['forearm_' + s] = (70, 0, 0)
    return p
def P_talk(t):
    p = P_idle(t)
    g = max(0, S(t * 2)); g2 = max(0, S(t * 2, 0.5))
    p['upper_arm_R'] = (25 + 18 * g, 0, -14); p['forearm_R'] = (55 + 25 * g, 10, 0); p['hand_R'] = (0, 0, -20 * g)
    p['upper_arm_L'] = (10 + 12 * g2, 0, 10); p['forearm_L'] = (30 + 30 * g2, -10, 0)
    p['head'] = (4 * S(t * 3), 6 * S(t * 1), 3 * S(t * 2)); p['chest'] = (2 * S(t * 2), 3 * S(t), 0)
    return p
def P_wave(t):
    p = P_idle(t); p['upper_arm_R'] = (10, 0, -150); p['forearm_R'] = (20, 0, -25 + 25 * S(t * 3)); p['head'] = (0, -8, 6); return p
def P_nod(t):
    p = P_idle(0); p['head'] = (16 * max(0, S(t)) ** 0.7, 0, 0); p['neck'] = (6 * max(0, S(t)), 0, 0); return p
def P_shrug(t):
    p = P_idle(0); k = math.sin(math.pi * t) ** 2
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (10 * k, 0, sx * (8 + 22 * k)); p['forearm_' + s] = (12 + 70 * k, sx * -40 * k, 0)
    p['chest@loc'] = (0, 0.02 * k, 0); p['head'] = (0, 0, 10 * k); return p
def P_point(t):
    p = P_idle(t); p['upper_arm_R'] = (80, 0, -8); p['forearm_R'] = (6, 0, 0); p['head'] = (2, -6, 0); return p
def P_reach(t):  # working with hands at bench height
    p = P_idle(t)
    for s, sx, ph in (('L', 1, 0), ('R', -1, 0.5)):
        p['upper_arm_' + s] = (45 + 6 * S(t * 2, ph), 0, sx * 12); p['forearm_' + s] = (55 + 10 * S(t * 2, ph + .25), 0, 0); p['hand_' + s] = (0, 0, sx * 15 * S(t * 2, ph))
    p['spine'] = (8, 0, 0); p['neck'] = (10, 0, 0); p['head'] = (12, 4 * S(t), 0); return p
def P_type(t):
    p = P_idle(t)
    for s, sx, ph in (('L', 1, 0), ('R', -1, 0.33)):
        p['upper_arm_' + s] = (32, 0, sx * 16); p['forearm_' + s] = (72, 0, 0); p['hand_' + s] = (-10 + 8 * max(0, S(t * 6, ph)), 0, 0)
    p['spine'] = (6, 0, 0); p['head'] = (6, 2 * S(t), 0); return p
def P_carry(t):
    p = walkcycle(0, amp=0); p.update(P_idle(t))
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (42, 0, sx * 14); p['forearm_' + s] = (65, sx * 15, 0); p['hand_' + s] = (0, 0, sx * -10)
    p['spine'] = (-4, 0, 0); return p
def P_carrywalk(t):
    p = walkcycle(t, arm=0)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (42, 0, sx * 14); p['forearm_' + s] = (65, sx * 15, 0); p['hand_' + s] = (0, 0, sx * -10)
    p['spine'] = (-4, 0, 0); return p
def P_sit(t):
    p = {'hips@loc': (0, -0.43, 0.05)}
    for s, sx in (('L', 1), ('R', -1)):
        p['thigh_' + s] = (88, 0, sx * -4); p['shin_' + s] = (-88, 0, 0); p['upper_arm_' + s] = (28, 0, sx * 10); p['forearm_' + s] = (50, sx * 15, 0)
    p['chest'] = (1.5 * S(t), 0, 0); p['head'] = (3 * S(t, .3), 4 * S(t * 0.5), 0); p['spine'] = (-4, 0, 0); return p
def P_sitsleep(t):
    p = P_sit(t); p['head'] = (28 + 3 * S(t), 0, 18); p['neck'] = (12, 0, 6); p['chest'] = (-2 + 3 * S(t), 0, 0); p['spine'] = (-12, 0, 0)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (12, 0, sx * 22); p['forearm_' + s] = (30, 0, 0)
    return p
def P_down(t):  # unconscious, lying on back
    p = {'root': (-90, 0, 0), 'root@loc': (0, 0.0, 0), 'hips@loc': (0, 0, 0)}
    p['root@loc'] = (0, 0.12, 0.0)
    for s, sx in (('L', 1), ('R', -1)):
        p['upper_arm_' + s] = (-10, 0, sx * 60); p['forearm_' + s] = (40, 0, 0); p['thigh_' + s] = (8, 0, sx * 12); p['shin_' + s] = (-10, 0, 0)
    p['head'] = (-10, 0, 25); p['chest'] = (2 * S(t), 0, 0); return p
def P_stunned(t):
    p = P_idle(t)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (20 + 15 * S(t * 4), 0, sx * (40 + 10 * S(t * 5))); p['forearm_' + s] = (30, 0, 0)
    p['head'] = (8 * S(t * 2), 15 * S(t), 12 * S(t * 1.5)); p['spine'] = (4 * S(t * 2), 0, 6 * S(t)); return p
def P_handsup(t):
    p = P_idle(t)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (10, 0, sx * 155); p['forearm_' + s] = (10, 0, sx * 20)
    return p
def P_push(t):
    p = P_idle(t)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (78 + 3 * S(t * 4), 0, sx * 10); p['forearm_' + s] = (12, 0, 0); p['hand_' + s] = (-40, 0, 0)
    p['spine'] = (10, 0, 0); p['hips@loc'] = (0, -0.03, 0.02)
    p['thigh_L'] = (25, 0, 0); p['shin_L'] = (-30, 0, 0); p['thigh_R'] = (-15, 0, 0); p['shin_R'] = (-10, 0, 0); return p
def P_jump(t):
    p = walkcycle(0.25, amp=0.6)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (-20, 0, sx * 40); p['forearm_' + s] = (40, 0, 0)
    p['thigh_L'] = (40, 0, 0); p['shin_L'] = (-70, 0, 0); return p
def P_cheer(t):
    p = P_idle(t)
    k = abs(S(t)); p['hips@loc'] = (0, 0.04 * k, 0)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (0, 0, sx * (140 + 15 * k)); p['forearm_' + s] = (20, 0, 0)
    return p
def P_pet(t):  # crouched petting
    p = P_crouch(t); p['upper_arm_R'] = (60, 0, -6); p['forearm_R'] = (30 + 15 * S(t * 2), 0, 0); p['hand_R'] = (-20, 0, 0); p['head'] = (20, 0, 0); return p
def P_sad(t):
    p = P_idle(t); p['neck'] = (15, 0, 0); p['head'] = (12, 0, 0); p['chest'] = (8, 0, 0); return p
def P_think(t):
    p = P_idle(t); p['upper_arm_R'] = (30, 0, -10); p['forearm_R'] = (130, 0, 15); p['upper_arm_L'] = (15, 0, 20); p['forearm_L'] = (95, 0, -50)
    p['head'] = (-5, 8, 8 + 2 * S(t)); return p
def P_lookaround(t):
    p = P_idle(t); p['head'] = (0, 40 * S(t), 0); p['neck'] = (0, 15 * S(t), 0); p['chest'] = (0, 8 * S(t), 0); return p
def P_flashlight(t):
    p = walkcycle(t, amp=0.6, arm=0.4)
    p['upper_arm_R'] = (55, 0, -10); p['forearm_R'] = (25, 0, 0); return p
def P_flashidle(t):
    p = P_idle(t); p['upper_arm_R'] = (55, 0, -10); p['forearm_R'] = (25, 0, 0); p['head'] = (0, 25 * S(t * 0.5), 0); return p

def anim_cat(rig):
    def idle(t):
        p = {'c_chest': (1.5 * S(t), 0, 0), 'c_head': (3 * S(t, .2), 6 * S(t * 0.5), 0)}
        for i in range(4): p['c_tail%d' % i] = (6, 0, 14 * S(t, i * 0.12))
        return p
    def walk(t):
        p = idle(t)
        for leg, ph in (('fleg', 0), ('bleg', 0.5)):
            for s, o in (('L', 0), ('R', 0.5)):
                a = 2 * math.pi * (t + ph + o)
                p['c_%s1_%s' % (leg, s)] = (28 * math.sin(a), 0, 0); p['c_%s2_%s' % (leg, s)] = (-20 * max(0, math.sin(a + 1.4)), 0, 0)
        p['c_root@loc'] = (0, 0.008 * abs(S(t * 2)), 0); return p
    def sit(t):
        p = idle(t); p['c_hips'] = (-35, 0, 0); p['c_root@loc'] = (0, -0.04, 0.0); p['c_chest'] = (-25 + S(t), 0, 0); p['c_neck'] = (30, 0, 0)
        for s in 'LR': p['c_bleg1_' + s] = (70, 0, 0); p['c_bleg2_' + s] = (-120, 0, 0); p['c_fleg1_' + s] = (35, 0, 0)
        for i in range(4): p['c_tail%d' % i] = (-25 if i == 0 else 0, 0, 10 * S(t, i * 0.12))
        return p
    def sleep(t):
        p = {'c_root@loc': (0, -0.13, 0), 'c_chest': (2.5 * S(t), 0, 25), 'c_hips': (0, 0, -15), 'c_neck': (-10, 0, 40), 'c_head': (10, 0, 30)}
        for s in 'LR':
            for leg in ('fleg', 'bleg'): p['c_%s1_%s' % (leg, s)] = (-80 if leg == 'fleg' else 80, 0, 0); p['c_%s2_%s' % (leg, s)] = (-60 if leg == 'bleg' else 60, 0, 0)
        for i in range(4): p['c_tail%d' % i] = (0, 0, 30 + 3 * S(t))
        return p
    def purr(t):
        p = sit(t); p['c_head'] = (10 * S(t * 2), 25 * S(t), 15 * S(t)); p['c_neck'] = (30 + 5 * S(t * 2), 0, 0); return p
    def squirm(t):
        p = idle(t)
        for s in 'LR':
            for leg in ('fleg', 'bleg'): p['c_%s1_%s' % (leg, s)] = (40 * S(t * 3, 0.3 if s == 'L' else 0), 0, 0)
        for i in range(4): p['c_tail%d' % i] = (0, 0, 35 * S(t * 2, i * 0.1))
        return p
    for n, fr, fn in (('idle', 72, idle), ('walk', 18, walk), ('sit', 72, sit), ('sleep', 96, sleep), ('purr', 48, purr), ('squirm', 24, squirm)):
        keyframe_action(rig, n, fr, fn)

