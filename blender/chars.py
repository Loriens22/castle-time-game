"""Castle TIME characters. Shared humanoid skeleton + procedural meshes (see chars_base.py, adapted from
Steve The PC Repair Man). Every outfit piece, helmet and accessory below is generated from code.
run: blender -b -P blender/chars.py -- [names...]"""
import bpy, math, sys, os
from mathutils import Vector
sys.path.insert(0, os.path.dirname(__file__))
from lib import *
import chars_base as CB
from chars_base import (make_rig, weight, rigid, V, torso, arm, leg, skirt, head, bone_parent, wsel, _delete_selected,
                        keyframe_action, S, C, walkcycle, P_idle, P_talk, P_wave, P_nod, P_shrug, P_point, P_type, P_sit,
                        P_sitsleep, P_down, P_stunned, P_handsup, P_cheer, P_sad, P_think, P_lookaround, P_crouch, P_jump,
                        build_cat, HC, limb_rings, J, SEG)

def robe(c, m, z0=0.5, flare=1.0, name='robe', front_open=False):
    """generalised coat/tabard: lofted tube from z0 up to the shoulders, weighted like a skirt below the hips."""
    w = c.get('width', 1.0); b = c.get('belly', 1.0)
    prof = [(z0, .19 * flare, .15 * flare), (max(z0 + 0.1, 0.62), .2 * (0.5 + flare * 0.5), .15), (0.8, .19, .14), (0.95, .175, .13),
            (1.08, .17 * b, .13 * b), (1.2, .18, .135), (1.32, .195, .132), (1.4, .2, .122), (1.45, .17, .1), (1.49, .09, .075)]
    prof = [p for i, p in enumerate(prof) if i == 0 or p[0] > prof[0][0] + 0.05]
    o = loft([((0, 0.004, z), rx * w, ry * w) for z, rx, ry in prof], m, name, seg=24, cap=False)
    vg = {bn: o.vertex_groups.new(name=bn) for bn in ('hips', 'spine', 'chest', 'thigh_L', 'thigh_R')}
    for v in o.data.vertices:
        z = v.co.z
        if z > 0.95:
            cw = max(0, min(1, (z - 1.12) / 0.16)); vg['chest'].add([v.index], cw, 'REPLACE'); vg['spine'].add([v.index], 1 - cw, 'REPLACE')
        else:
            h = max(0, min(1, (0.95 - z) / 0.45)); side = 'thigh_L' if v.co.x > 0 else 'thigh_R'
            sw = h * min(1, abs(v.co.x) / 0.1) * 0.6
            vg['hips'].add([v.index], 1 - sw, 'REPLACE'); vg[side].add([v.index], sw, 'REPLACE')
    return o

def R(o, bone, parts): rigid(o, bone); parts.append(o); return o

def accessories(c, rig, parts, name):
    w = c.get('width', 1.0)
    # ---------------- 2026 traveller kit
    if c.get('hoodie'):
        hm = M('top_' + name, c['top'], 0.9)
        hood = tor(0.1, 0.045, (0, 0.06, 1.47), hm, rot=(0.5, 0, 0), maj=22, mn=10); hood.scale = (1.15, 1.0, 0.8); R(hood, 'chest', parts)
        hb = sph(0.09, (0, 0.13, 1.42), hm, (1.2, 0.6, 1.0)); R(hb, 'chest', parts)
        pk = box(0.2, 0.03, 0.12, (0, -0.135 * w * c.get('belly', 1), 1.06), hm, bev=0.015); weight(pk, ['spine', 'hips']); parts.append(pk)
        neon = M('neon_' + name, c.get('neon', '#39ffd0'), 0.3, emit=CB.hexc(c.get('neon', '#39ffd0')), estr=2.5)
        for sx in (1, -1):
            st = cyl(0.004, 0.16, (sx * 0.035, -0.11, 1.36), neon); R(st, 'chest', parts)
            tip = cyl(0.007, 0.02, (sx * 0.035, -0.112, 1.275), M('aglet', '#dddddd', 0.3, 0.8)); R(tip, 'chest', parts)
        stripe = box(0.2, 0.012, 0.012, (0, -0.172 * w, 1.3), neon); stripe.scale = (1, 1, 1); R(stripe, 'chest', parts)
        logo = box(0.075, 0.01, 0.075, (0.07, -0.168 * w, 1.33), M('T_logo_2026', '#ffffff', 0.6)); R(logo, 'chest', parts)
        for s, sx in (('L', 1), ('R', -1)):  # neon sleeve stripes
            el = Vector(J['el_' + s]); sh = Vector(J['sh_' + s])
            band = tor(0.06, 0.008, sh.lerp(el, 0.55), neon, rot=(0, 0, 0), maj=16, mn=6); R(band, 'upper_arm_' + s, parts)
    if c.get('headphones'):
        hp_ = M('phones_' + name, '#f2f2f2', 0.35)
        band = tor(0.11, 0.012, (0, 0.02, 1.47), hp_, rot=(0.25, 0, 0), maj=24, mn=8); band.scale = (1.0, 1.05, 1); R(band, 'chest', parts)
        for sx in (1, -1):
            cup = cyl(0.045, 0.03, (sx * 0.11, -0.03, 1.44), hp_, rot=(0, math.pi / 2, 0.3 * sx), v=20, bev=0.008); R(cup, 'chest', parts)
            pad = cyl(0.036, 0.012, (sx * 0.093, -0.035, 1.44), M('neon_' + name, c.get('neon')), rot=(0, math.pi / 2, 0.3 * sx), v=16); R(pad, 'chest', parts)
    if c.get('backpack'):
        bm_ = M('pack_' + name, '#1c1f26', 0.6)
        bag = box(0.27, 0.14, 0.36, (0, 0.2, 1.18), bm_, bev=0.04, seg=3); R(bag, 'chest', parts)
        flap = box(0.25, 0.03, 0.12, (0, 0.27, 1.28), M('pack2_' + name, '#2d6c8c', 0.5), bev=0.02); R(flap, 'chest', parts)
        led = box(0.12, 0.01, 0.012, (0, 0.287, 1.22), M('neon_' + name, c.get('neon'))); R(led, 'chest', parts)
        for sx in (1, -1):
            strap = box(0.045, 0.02, 0.32, (sx * 0.1, -0.12, 1.3), bm_, rot=(0.15, 0, 0)); R(strap, 'chest', parts)
    if c.get('smartwatch'):
        wr = Vector(J['wr_L']); el = Vector(J['el_L'])
        wt = box(0.04, 0.05, 0.012, wr + (el - wr).normalized() * 0.035 + V(0.03, 0, 0), M('watch_' + name, '#111111', 0.2), rot=(0, 1.4, 0))
        R(wt, 'forearm_L', parts)
    if c.get('sneakers'):
        neon = M('neon_' + name, c.get('neon'))
        for s in 'LR':
            an = Vector(J['an_' + s]); sl = box(0.104, 0.21, 0.016, (an.x, an.y - 0.035, 0.006), neon, bev=0.006); R(sl, 'foot_' + s, parts)
            sw = box(0.098, 0.05, 0.02, (an.x, an.y - 0.12, 0.05), M('swoosh', '#2b2f3a', 0.5), rot=(0.5, 0, 0)); R(sw, 'foot_' + s, parts)
    if c.get('cargo'):
        bm_ = M('bottom_' + name, c['bottom'])
        for s, sx in (('L', 1), ('R', -1)):
            kn = Vector(J['kn_' + s]); hp = Vector(J['hp_' + s])
            pc = box(0.035, 0.09, 0.11, hp.lerp(kn, 0.55) + V(sx * 0.075, 0, 0), bm_, bev=0.012); R(pc, 'thigh_' + s, parts)
    # ---------------- medieval kit
    if c.get('tabard'):
        cols = c['tabard']
        tb = robe(c, M('tabard_' + name, cols[0], 0.85), z0=c.get('tabard_z', 0.62), flare=1.05, name='tabard')
        tb.scale = (1.06, 1.06, 1.0); parts.append(tb)
        if len(cols) > 1:  # heraldic stripe + badge
            st = box(0.07, 0.01, 0.62, (0, -0.15 * w * c.get('belly', 1) - 0.005, 1.0), M('tabard2_' + name, cols[1], 0.8)); weight(st, ['spine', 'chest', 'hips']); parts.append(st)
            badge = cyl(0.06, 0.012, (0, -0.165 * w - 0.01, 1.26), M('T_crest', cols[1], 0.6), rot=(math.pi / 2, 0, 0), v=6); R(badge, 'chest', parts)
    if c.get('robe'):
        parts.append(robe(c, M('robe_' + name, c['robe'], 0.9), z0=0.05, flare=1.45))
        if c.get('robe_trim'):
            tr = tor(0.3, 0.025, (0, 0.004, 0.07), M('trim_' + name, c['robe_trim'], 0.9), maj=32, mn=8); tr.scale = (0.95, 0.78, 1)
            weight(tr, ['hips', 'thigh_L', 'thigh_R']); parts.append(tr)
    if c.get('rope_belt'):
        bl = tor(0.16 * w * c.get('belly', 1), 0.013, (0, 0.004, 0.99), M('rope', '#b8a07a', 0.95), maj=28, mn=6); bl.scale = (1, 0.8, 1)
        weight(bl, ['hips', 'spine']); parts.append(bl)
        tail = cyl(0.01, 0.25, (0.06, -0.13, 0.86), M('rope', '#b8a07a')); weight(tail, ['hips', 'thigh_L']); parts.append(tail)
    if c.get('apron'):
        ap = box(0.3, 0.02, 0.55, (0, -0.16 * w * c.get('belly', 1), 0.85), M('apron_' + name, c['apron'], 0.85), rot=(0.08, 0, 0))
        weight(ap, ['spine', 'hips', 'thigh_L', 'thigh_R']); parts.append(ap)
    if c.get('plate'):
        st = M('steel_' + name, c.get('steel', '#b8bec6'), 0.28, 0.9)
        bp = sph(0.2, (0, -0.02, 1.25), st, (1.0 * w, 0.75 * c.get('belly', 1), 1.15)); wsel(bp, lambda q: q.y > 0.04); _delete_selected(bp)
        if not c.get('tabard'): R(bp, 'chest', parts)
        else: bpy.data.objects.remove(bp, do_unlink=True)
        for s, sx in (('L', 1), ('R', -1)):
            pd = sph(0.1, Vector(J['sh_' + s]) + V(sx * 0.03, 0, 0.03), st, (1.1, 1.1, 0.8)); R(pd, 'upper_arm_' + s, parts)
            ridge = tor(0.085, 0.012, Vector(J['sh_' + s]) + V(sx * 0.03, 0, -0.02), st, maj=18, mn=6); R(ridge, 'upper_arm_' + s, parts)
            el = Vector(J['el_' + s]); wr = Vector(J['wr_' + s])
            gt = cyl(0.055, 0.14, el.lerp(wr, 0.62), st, v=14, r2=0.045); gt.rotation_euler = (0, 0, 0); R(gt, 'forearm_' + s, parts)
            elb = sph(0.055, el, st, (1, 1, 0.9)); R(elb, 'forearm_' + s, parts)
            kn = Vector(J['kn_' + s]); an = Vector(J['an_' + s])
            gv = cyl(0.068, 0.36, kn.lerp(an, 0.5), st, v=16, r2=0.055); R(gv, 'shin_' + s, parts)
            kp = sph(0.065, kn + V(0, -0.04, 0), st, (1, 0.8, 1)); R(kp, 'shin_' + s, parts)
            th = cyl(0.085, 0.3, Vector(J['hp_' + s]).lerp(kn, 0.5) + V(0, -0.01, 0), st, v=16, r2=0.07); R(th, 'thigh_' + s, parts)
            sab = box(0.11, 0.24, 0.09, (an.x, an.y - 0.05, 0.05), st, bev=0.03); R(sab, 'foot_' + s, parts)
        fauld = cyl(0.165 * w, 0.14, (0, 0.004, 0.86), st, v=24, r2=0.18 * w); weight(fauld, ['hips', 'spine']); parts.append(fauld)
    if c.get('chainmail_coif'):
        pass
    if c.get('cape'):
        cm = M('cape_' + name, c['cape'], 0.85)
        bmc = bmesh_cape(c, cm); parts.append(bmc)
    if c.get('quiver'):
        q = cyl(0.06, 0.55, (0.1, 0.17, 1.25), M('leather', '#6b4226', 0.7), rot=(0.25, -0.3, 0)); R(q, 'chest', parts)
        for i in range(5):
            a = i * 1.25; fl = box(0.03, 0.004, 0.08, (0.1 + 0.03 * math.cos(a) - 0.04, 0.24 + 0.03 * math.sin(a), 1.55), M('fletch', '#e8e2d0', 0.9), rot=(0.25, -0.3, a))
            R(fl, 'chest', parts)
        strap = box(0.04, 0.02, 0.55, (0.0, -0.13, 1.25), M('leather', '#6b4226'), rot=(0, 0.75, 0)); R(strap, 'chest', parts)
    if c.get('pouch'):
        p = box(0.1, 0.06, 0.1, (0.13, -0.08, 0.92), M('leather', '#6b4226', 0.7), bev=0.02); R(p, 'hips', parts)
    if c.get('keys'):
        for i in range(3):
            k = tor(0.03, 0.006, (-0.14, -0.06, 0.9 - i * 0.02), M('iron', '#4a4a4f', 0.5, 0.8), rot=(1.5, 0, i * 0.5), maj=12, mn=5); R(k, 'hips', parts)
            kk = box(0.01, 0.01, 0.1, (-0.14 + (i - 1) * 0.015, -0.07, 0.83), M('iron', '#4a4a4f')); R(kk, 'hips', parts)

def bmesh_cape(c, m):
    import bmesh
    w = c.get('width', 1.0); bm = bmesh.new(); rows = 8; cols = 7; vs = []
    for r in range(rows + 1):
        z = 1.46 - r * (1.46 - c.get('cape_z', 0.3)) / rows; spread = 0.17 * w + r * 0.03
        row = []
        for k in range(cols + 1):
            x = -spread + 2 * spread * k / cols; y = 0.12 * w + 0.02 + r * 0.025 + 0.03 * math.cos((k / cols - 0.5) * math.pi) * (r > 0)
            if r == 0: y = 0.09
            row.append(bm.verts.new((x, y, z)))
        vs.append(row)
    for r in range(rows):
        for k in range(cols): bm.faces.new((vs[r][k], vs[r][k + 1], vs[r + 1][k + 1], vs[r + 1][k]))
    me = bpy.data.meshes.new('cape'); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new('cape', me); bpy.context.collection.objects.link(o)
    sol = o.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.015; apply_mods(o); smooth(o, 180); setmat(o, m)
    vg = {bn: o.vertex_groups.new(name=bn) for bn in ('chest', 'spine', 'hips')}
    for v in o.data.vertices:
        z = v.co.z
        if z > 1.15: vg['chest'].add([v.index], 1, 'REPLACE')
        elif z > 0.9: f = (z - 0.9) / 0.25; vg['chest'].add([v.index], f, 'REPLACE'); vg['spine'].add([v.index], 1 - f, 'REPLACE')
        else: vg['hips'].add([v.index], 0.6, 'REPLACE'); vg['spine'].add([v.index], 0.4, 'REPLACE')
    return o

def headgear(c, name):
    """extra head meshes (rigid on 'head')."""
    objs = []; hs = c.get('head', 1.0); h = c.get('helm')
    if h == 'kettle':
        st = M('helm_' + name, '#9aa0a8', 0.35, 0.85)
        dome = sph(0.142 * hs, HC + V(0, 0.005, 0.03), st, (1, 1.02, 0.95)); wsel(dome, lambda q: q.z < HC.z + 0.02); _delete_selected(dome)
        brim = cyl(0.21, 0.012, HC + V(0, 0.005, 0.035), st, v=28, r2=0.15); objs += [dome, brim]
        ridge = box(0.012, 0.27, 0.03, HC + V(0, 0.005, 0.15), st, rot=(0, 0, 0)); objs.append(ridge)
        coif = sph(0.14 * hs, HC + V(0, 0.01, -0.02), M('T_chainmail', '#8b8f94', 0.5, 0.7), (1.02, 1.0, 1.15))
        wsel(coif, lambda q: (q.y < -0.06 and q.z > HC.z - 0.09) or q.z > HC.z + 0.05); _delete_selected(coif); objs.append(coif)
    elif h == 'greathelm':
        st = M('helm_' + name, c.get('steel', '#b8bec6'), 0.25, 0.9)
        cy = cyl(0.145 * hs, 0.33, HC + V(0, 0.0, 0.01), st, v=24, r2=0.14 * hs); objs.append(cy)
        top = cyl(0.14 * hs, 0.02, HC + V(0, 0, 0.18), st, v=24); objs.append(top)
        dk = M('slit', '#050505', 0.9)
        for sx in (1, -1): objs.append(box(0.1, 0.03, 0.016, HC + V(sx * 0.055, -0.14, 0.025), dk))
        objs.append(box(0.02, 0.02, 0.2, HC + V(0, -0.148, -0.02), st))
        cr = box(0.018, 0.01, 0.16, HC + V(0, -0.148, -0.04), M('helm_gold', '#d4a83a', 0.3, 0.9)); objs.append(cr)
        for i in range(8): objs.append(cyl(0.006, 0.02, HC + V(0.03 + (i % 4) * 0.02, -0.142, -0.07 - (i // 4) * 0.03), dk, rot=(math.pi / 2, 0, 0), v=6))
        if c.get('plume'):
            pm = M('plume_' + name, c['plume'], 0.95)
            for i in range(6): objs.append(sph(0.05 - i * 0.004, HC + V(0, 0.02 + i * 0.045, 0.24 - i * i * 0.008), pm, (0.6, 1.2, 1)))
    elif h == 'bell':
        st = M('helm_' + name, '#c9a54a', 0.22, 1.0)
        prof = [(0.0, 0.33), (0.06, 0.325), (0.11, 0.3), (0.14, 0.24), (0.15, 0.1), (0.17, -0.04), (0.2, -0.12), (0.215, -0.14), (0.2, -0.15)]
        bl = lathe([(r * hs, z) for r, z in prof], st, 'bell', seg=28, loc=HC + V(0, 0, -0.02)); objs.append(bl)
        dk = M('slit', '#050505', 0.9); objs.append(box(0.18, 0.03, 0.02, HC + V(0, -0.15, 0.03), dk))
        lip = tor(0.205 * hs, 0.012, HC + V(0, 0, -0.165), st, maj=28, mn=6); objs.append(lip)
        knob = sph(0.03, HC + V(0, 0, 0.32), st); objs.append(knob)
    elif h == 'cowl':
        cm = M('cowl_' + name, c.get('cowl', '#3f5a2e'), 0.9)
        cw = sph(0.155 * hs, HC + V(0, 0.02, 0.02), cm, (1.0, 1.05, 1.08)); wsel(cw, lambda q: q.y < -0.07 and q.z < HC.z + 0.09); _delete_selected(cw)
        tip = cyl(0.06, 0.2, HC + V(0, 0.15, 0.08), cm, rot=(1.9, 0, 0), r2=0.0, v=10); objs += [cw, tip]
        sh = cyl(0.2, 0.14, HC + V(0, 0.01, -0.22), cm, v=20, r2=0.11); objs.append(sh)
    elif h == 'beret':
        cm = M('beret_' + name, c.get('beret', '#a3262a'), 0.9)
        bt = cyl(0.16 * hs, 0.06, HC + V(0.015, 0.02, 0.12), cm, v=24, rot=(0.1, -0.15, 0)); bevel(bt, 0.025, 3); objs.append(bt)
        band = tor(0.127 * hs, 0.018, HC + V(0, 0.01, 0.075), cm, maj=24, mn=8, rot=(0.08, -0.1, 0)); objs.append(band)
    elif h == 'kerchief':
        cm = M('kerchief_' + name, c.get('kerchief', '#d9cdb0'), 0.95)
        kc = sph(0.138 * hs, HC + V(0, 0.012, 0.02), cm, (1, 1.04, 1.02)); wsel(kc, lambda q: (q.y < -0.065 and q.z < HC.z + 0.075) or q.z < HC.z - 0.08); _delete_selected(kc)
        knot = sph(0.03, HC + V(0, 0.13, -0.05), cm, (1.4, 1, 0.8)); objs += [kc, knot]
    elif h == 'coif':
        cm = M('coif_' + name, c.get('coif', '#e3d9c0'), 0.95)
        kc = sph(0.136 * hs, HC + V(0, 0.012, 0.02), cm); wsel(kc, lambda q: (q.y < -0.06 and q.z < HC.z + 0.06) or q.z < HC.z - 0.07); _delete_selected(kc); objs.append(kc)
    elif h == 'crown':
        gm = M('gold', '#e0b23a', 0.25, 1.0)
        objs.append(cyl(0.13 * hs, 0.05, HC + V(0, 0.01, 0.1), gm, v=24, cap=False))
        for i in range(8):
            a = i / 8 * 2 * math.pi
            objs.append(cyl(0.02, 0.06, HC + V(math.cos(a) * 0.13, 0.01 + math.sin(a) * 0.13, 0.15), gm, v=4, r2=0.0))
        objs.append(sph(0.016, HC + V(0, -0.135, 0.1), M('ruby', '#c0102a', 0.1, 0.2, emit=(0.4, 0, 0.02), estr=0.5)))
        hatm = M('hat_' + name, '#5a1f6b', 0.9); hh = sph(0.12, HC + V(0, 0.01, 0.12), hatm, (1, 1, 0.55)); objs.append(hh)
    if c.get('visor'):
        lm = M('visor_' + name, '#5ff5ff', 0.05, 0.2, emit=(0.15, 0.9, 1.0), estr=1.2)
        objs.append(box(0.2, 0.02, 0.04, HC + V(0, -0.125 * hs, 0.015), lm, bev=0.008))
        fm = M('frames_' + name, '#15171c', 0.3, 0.4)
        for sx in (1, -1): objs.append(box(0.008, 0.12, 0.012, HC + V(sx * 0.105, -0.065, 0.02), fm))
    if c.get('longbeard'):
        bm_ = M('hair_' + name, c.get('hair'), 0.95)
        bd = cyl(0.085, 0.3, HC + V(0, -0.075, -0.22), bm_, v=14, r2=0.012, rot=(-0.25, 0, 0)); objs.append(bd)
        mu = sph(0.045, HC + V(0, -0.118, -0.045), bm_, (1.6, 0.55, 0.5)); objs.append(mu)
        cheek = sph(0.11 * hs, HC + V(0, -0.02, -0.07), bm_, (1.0, 0.95, 0.8)); wsel(cheek, lambda q: q.z > HC.z - 0.03 or q.y > 0.02); _delete_selected(cheek); objs.append(cheek)
    if c.get('hairring'):
        hm = M('hair_' + name, c.get('hair'), 0.95)
        for i in range(9):
            a = math.pi * (-0.15 + 1.3 * i / 8)
            objs.append(sph(0.04, HC + V(math.cos(a) * 0.115, math.sin(a) * 0.1 + 0.02, -0.01), hm, (0.9, 0.9, 1.3), seg=10, rings=6))
    if c.get('ponytail'):
        hm = M('hair_' + name, c.get('hair'))
        pt = cyl(0.03, 0.18, HC + V(0, 0.15, 0.0), hm, rot=(0.5, 0, 0), r2=0.012, v=10); objs.append(pt)
        tie = tor(0.03, 0.008, HC + V(0, 0.12, 0.06), M('neon_' + name, c.get('neon', '#39ffd0')), rot=(0.5, 0, 0), maj=12, mn=5); objs.append(tie)
    if c.get('earring'):
        objs.append(tor(0.012, 0.003, HC + V(0.118, -0.005, -0.04), M('gold', '#e0b23a', 0.25, 1.0), rot=(0, math.pi / 2, 0), maj=10, mn=4))
    return objs

CHARS = {
  # the traveller: 2026 streetwear
  'juno': dict(skin='#c68d6c', hair='#2a1d33', hairstyle='slick', top='#2b2f3a', bottom='#56603f', shoe='#f2f2f2', sleeve='long',
               fem=1, width=0.92, hoodie=True, headphones=True, backpack=True, smartwatch=True, sneakers=True, cargo=True, visor=True,
               ponytail=True, neon='#39ffd0', earring=True, brow='#2a1d33', eyecol='#3a2412'),
  'maestro': dict(skin='#e2b593', hair='#ece8e0', hairstyle=None, top='#7a2e2a', bottom='#5a3a22', shoe='#3b2a1d', sleeve='long',
                  robe='#7a2e2a', robe_trim='#c9a54a', helm='beret', beret='#a3262a', longbeard=True, hairring=True, width=0.9,
                  brow='#d8d2c8', browthick=1.6, nose=1.35, rope_belt=True),
  'peasant': dict(skin='#d9a383', hair='#5a3d26', hairstyle='short', top='#8a6f4e', bottom='#5e5140', shoe='#3b2a1d', sleeve='long',
                  tabard=('#7d6a4a',), tabard_z=0.6, rope_belt=True, helm='coif', beard=True, width=1.02, belly=1.06),
  'peasant_f': dict(skin='#e7b896', hair='#7a4a2a', hairstyle='bun', top='#6f7d5a', bottom='#6f7d5a', shoe='#3b2a1d', sleeve='long',
                    skirt=True, fem=1, width=0.94, helm='kerchief', kerchief='#d9cdb0', apron='#cfc3a5', cheeks=True),
  'guard': dict(skin='#d6a07c', hair='#3a2a20', hairstyle=None, top='#8b8f94', bottom='#4a3d30', shoe='#2e2219', sleeve='long',
                tabard=('#a3262a', '#e0b23a'), helm='kettle', mustache='#3a2a20', width=1.08, belly=1.04, pouch=True),
  'archer': dict(skin='#e0ad8a', hair='#6b4a2f', hairstyle='short', top='#5a4128', bottom='#3d4a2a', shoe='#2e2219', sleeve='long',
                 helm='cowl', cowl='#3f5a2e', quiver=True, tabard=('#4e6233',), tabard_z=0.7, goatee=True),
  'knight': dict(skin='#d6a07c', hair='#3a2a20', hairstyle=None, top='#7d848c', bottom='#5d636b', shoe='#2e2219', sleeve='long',
                 plate=True, tabard=('#a3262a', '#e0b23a'), tabard_z=0.68, helm='greathelm', plume='#e0b23a', width=1.12, cape='#7a1a1e', cape_z=0.45),
  'bruno': dict(skin='#d6a07c', hair='#3a2a20', hairstyle=None, top='#6a6058', bottom='#4d4640', shoe='#2e2219', sleeve='long',
                plate=True, steel='#c8ccd2', tabard=('#2a2a33', '#c9a54a'), tabard_z=0.62, helm='bell', width=1.25, belly=1.15, cape='#1e1e28', cape_z=0.3),
  'count': dict(skin='#ecc0a0', hair='#3a2a20', hairstyle='slick', top='#5a1f6b', bottom='#a3262a', shoe='#2a1a14', sleeve='long',
                robe='#5a1f6b', robe_trim='#efe6d6', helm='crown', mustache='#3a2a20', width=1.15, belly=1.32, cheeks=True, cape='#8a2a9a', cape_z=0.15),
  'jailer': dict(skin='#d39a78', hair='#d39a78', hairstyle=None, top='#4a3a2c', bottom='#3a2f26', shoe='#2a1f18', sleeve='short',
                 apron='#3a2a1c', keys=True, mustache='#2a1f18', width=1.2, belly=1.28, browthick=2.0, browtilt=0.15, head=1.05),
}

def build_char(name):
    clear_scene(); c = dict(CHARS[name]); c['name'] = name
    rig = make_rig()
    skin = M('skin_' + name, c['skin'], 0.6); top = M('top_' + name, c['top'], 0.85); bot = M('bottom_' + name, c['bottom'], 0.85)
    if c.get('plate') or name == 'guard': top = M('T_chainmail_' + name, c['top'], 0.45, 0.7)
    shoe = M('shoe_' + name, c['shoe'], 0.5)
    parts = torso(c, top, bot if not c.get('skirt') else top)
    for s in 'LR':
        parts += arm(c, s, top, skin, M('glove_' + name, '#5a4128', 0.7) if c.get('plate') else skin)
        parts += leg(c, s, bot, shoe, M('tights', '#a08770', 0.7) if c.get('skirt') else skin)
    neck = loft([((0, 0.005, 1.44), 0.055, 0.052), ((0, 0.0, 1.6), 0.05, 0.048)], skin, 'neck', seg=14); weight(neck, ['chest', 'neck', 'head'])
    parts.append(neck)
    if c.get('skirt'): parts += skirt(c, bot)
    accessories(c, rig, parts, name)
    body = join('body', parts)
    md = body.modifiers.new('arm', 'ARMATURE'); md.object = rig; body.parent = rig
    hm, eyes, mouth, extra = head(c, skin)
    hg = headgear(c, name)
    if hg: hm = join('head', [hm] + hg)
    for o in [hm, mouth] + eyes + extra: bone_parent(o, rig, 'head')
    export(name, anim=False, objs=[rig, body, hm, mouth] + eyes + extra)

# ------------------------------------------------------------------ animations (shared by all humans)
def aim_arms(p, k=1.0, t=0.0):
    """two-handed blaster hold: right arm forward, left hand supporting."""
    p['upper_arm_R'] = (80 * k + 2 * S(t), 0, -6); p['forearm_R'] = (8 * k, 0, 0); p['hand_R'] = (0, 0, 0)
    p['upper_arm_L'] = (70 * k + 2 * S(t), 0, -28 * k); p['forearm_L'] = (40 * k, 0, -20 * k); return p
def P_aim(t):
    p = P_idle(t); aim_arms(p, 1, t); p['spine'] = (2, 0, 0); p['chest'] = (0, 8, 0); p['head'] = (0, -6, 0); return p
def P_hold(t):  # relaxed: blaster pointing down-forward
    p = P_idle(t); p['upper_arm_R'] = (28, 0, -10); p['forearm_R'] = (35, 0, 0); p['upper_arm_L'] = (30, 0, -15); p['forearm_L'] = (55, 0, -25); return p
def P_runaim(t):
    p = walkcycle(t, amp=1.4, lean=10, arm=0, knee=1.5, bounce=0.055); aim_arms(p, 1, t); p['chest'] = (-4, 6, 0); return p
def P_walkaim(t):
    p = walkcycle(t, amp=0.9, lean=3, arm=0); aim_arms(p, 1, t); return p
def P_backaim(t):
    p = walkcycle(1 - t, amp=0.9, lean=-2, arm=0); aim_arms(p, 1, t); return p
def P_strafe(t, side=1):
    p = {}; ph = 2 * math.pi * t
    for s, o, sx in (('L', 0, 1), ('R', math.pi, -1)):
        a = ph + o
        p['thigh_' + s] = (10 * max(0, math.sin(a)), 0, sx * side * 14 * math.sin(a) * sx); p['shin_' + s] = (-30 * max(0, math.sin(a)), 0, 0)
    p['hips@loc'] = (0, -abs(math.cos(ph)) * 0.03, 0); aim_arms(p, 1, t); return p
def P_strafeR(t): return P_strafe(t, -1)
def P_strafeL(t): return P_strafe(t, 1)
def P_jumpup(t):
    p = P_jump(t); aim_arms(p, 0.6, t); return p
def P_fall(t):
    p = walkcycle(0.1, amp=0.5); p['upper_arm_L'] = (10, 0, 60 + 8 * S(t * 2)); p['upper_arm_R'] = (10, 0, -60 - 8 * S(t * 2, .3))
    p['forearm_L'] = (30, 0, 0); p['forearm_R'] = (30, 0, 0); p['thigh_L'] = (35 + 10 * S(t * 2), 0, 0); p['shin_L'] = (-60, 0, 0)
    p['thigh_R'] = (10, 0, 0); p['shin_R'] = (-30 - 10 * S(t * 2), 0, 0); return p
def P_roll(t):  # dodge roll: tuck + root spin forward (root rotates a full turn)
    k = math.sin(math.pi * t)
    p = {'root': (-360 * t, 0, 0), 'root@loc': (0, 0.55 * k * 0.9, 0)}
    p['hips@loc'] = (0, -0.35 * k, 0)
    for s, sx in (('L', 1), ('R', -1)):
        p['thigh_' + s] = (100 * k, 0, sx * -6); p['shin_' + s] = (-130 * k, 0, 0); p['upper_arm_' + s] = (60 * k, 0, sx * 10); p['forearm_' + s] = (90 * k, 0, 0)
    p['spine'] = (30 * k, 0, 0); p['chest'] = (25 * k, 0, 0); p['neck'] = (25 * k, 0, 0); return p
def P_hit(t):
    k = math.sin(math.pi * min(1, t * 1.3))
    p = P_idle(0); p['spine'] = (-14 * k, 0, 6 * k); p['chest'] = (-10 * k, 0, 0); p['head'] = (-18 * k, 0, 10 * k)
    p['upper_arm_L'] = (20 * k, 0, 30 * k); p['upper_arm_R'] = (20 * k, 0, -30 * k); return p
def P_phone(t):
    p = P_idle(t); p['upper_arm_R'] = (42, 0, -14); p['forearm_R'] = (95, 10, 0); p['hand_R'] = (-20, 0, -10)
    p['upper_arm_L'] = (35, 0, 16); p['forearm_L'] = (80, -15, 0); p['head'] = (22, 0, 0); p['neck'] = (10, 0, 0)
    p['hand_L'] = (0, 0, 8 * max(0, S(t * 4))); return p
def P_climb(t):
    p = {}; ph = 2 * math.pi * t
    for s, o, sx in (('L', 0, 1), ('R', math.pi, -1)):
        a = ph + o
        p['upper_arm_' + s] = (150 + 25 * math.sin(a), 0, sx * 12); p['forearm_' + s] = (20 + 20 * max(0, -math.sin(a)), 0, 0)
        p['thigh_' + s] = (45 + 35 * math.sin(a + math.pi), 0, 0); p['shin_' + s] = (-60 - 30 * max(0, math.sin(a + math.pi)), 0, 0)
    p['head'] = (-15, 0, 0); return p
def P_pickup(t):
    k = math.sin(math.pi * t)
    p = P_idle(0); p['spine'] = (35 * k, 0, 0); p['chest'] = (20 * k, 0, 0); p['upper_arm_R'] = (70 * k, 0, -10); p['forearm_R'] = (20 * k, 0, 0)
    p['thigh_L'] = (45 * k, 0, 0); p['shin_L'] = (-70 * k, 0, 0); p['thigh_R'] = (45 * k, 0, 0); p['shin_R'] = (-70 * k, 0, 0)
    p['hips@loc'] = (0, -0.22 * k, 0.05 * k); return p
# ---------- enemy / NPC moves (weapon in right hand)
def P_eidle(t):
    p = P_idle(t); p['upper_arm_R'] = (20 + 2 * S(t), 0, -10); p['forearm_R'] = (55, 0, 0); p['hand_R'] = (0, 0, 0); return p
def P_ewalk(t):
    p = walkcycle(t, amp=0.85); p['upper_arm_R'] = (20, 0, -10); p['forearm_R'] = (55, 0, 0); return p
def P_echarge(t):
    p = walkcycle(t, amp=1.5, lean=16, arm=1.0, knee=1.5, bounce=0.06); p['upper_arm_R'] = (55, 0, -10); p['forearm_R'] = (40, 0, 0)
    p['upper_arm_L'] = (50, 0, -20); p['forearm_L'] = (50, 0, -20); return p
def P_thrust(t):  # windup 0-0.45, jab 0.45-0.6, recover
    if t < 0.45: k = -math.sin(t / 0.45 * math.pi / 2)
    elif t < 0.6: k = -1 + 2.2 * (t - 0.45) / 0.15
    else: k = 1.2 * (1 - (t - 0.6) / 0.4)
    p = P_eidle(0); p['upper_arm_R'] = (55 + 35 * k, 0, -10); p['forearm_R'] = (40 - 35 * k, 0, 0)
    p['upper_arm_L'] = (55 + 30 * k, 0, -25); p['forearm_L'] = (45 - 25 * k, 0, -15); p['spine'] = (8 * k, 0, -10 * k); p['chest'] = (6 * k, -12 * k, 0)
    p['thigh_L'] = (20 * max(0, k), 0, 0); p['shin_L'] = (-15 * max(0, k), 0, 0); return p
def P_swing(t):  # overhead sword chop
    if t < 0.45: k = math.sin(t / 0.45 * math.pi / 2)
    elif t < 0.6: k = 1 - 2.0 * (t - 0.45) / 0.15
    else: k = -1 + (t - 0.6) / 0.4
    p = P_eidle(0); p['upper_arm_R'] = (90 + 80 * k, 0, -10); p['forearm_R'] = (30 + 30 * max(0, k), 0, 0); p['hand_R'] = (-30 * k, 0, 0)
    p['spine'] = (-10 * k, 0, 0); p['chest'] = (-8 * k, 0, 0); p['thigh_L'] = (15, 0, 0); p['shin_L'] = (-10, 0, 0); return p
def P_slam(t):  # boss two-hand hammer slam
    if t < 0.5: k = math.sin(t / 0.5 * math.pi / 2)
    elif t < 0.62: k = 1 - 2.2 * (t - 0.5) / 0.12
    else: k = -1.2 + 1.2 * (t - 0.62) / 0.38
    p = P_eidle(0)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (100 + 75 * k, 0, -sx * 18); p['forearm_' + s] = (25 + 20 * max(0, k), 0, -sx * 10)
    p['spine'] = (-12 * k, 0, 0); p['chest'] = (-10 * k, 0, 0); p['hips@loc'] = (0, -0.12 * max(0, -k), 0)
    p['thigh_L'] = (25 * max(0, -k), 0, 0); p['shin_L'] = (-40 * max(0, -k), 0, 0); p['thigh_R'] = (-15 * max(0, -k), 0, 0); return p
def P_throw(t):
    if t < 0.5: k = math.sin(t / 0.5 * math.pi / 2)
    elif t < 0.65: k = 1 - 2 * (t - 0.5) / 0.15
    else: k = -1 + (t - 0.65) / 0.35
    p = P_idle(0); p['upper_arm_R'] = (60 + 100 * k, 0, -20); p['forearm_R'] = (50 + 40 * max(0, k), 0, 0)
    p['upper_arm_L'] = (60 - 20 * k, 0, 15); p['chest'] = (-6 * k, -20 * k, 0); p['spine'] = (0, -10 * k, 0); return p
def P_bow(t):  # draw 0-0.6, hold, release 0.75
    d = min(1, t / 0.6); rel = t > 0.75
    p = P_idle(0); p['upper_arm_L'] = (85, 0, 5); p['forearm_L'] = (0, 0, 0); p['hand_L'] = (0, 0, 0)
    p['upper_arm_R'] = (85, 0, -(20 + 40 * d) if not rel else -10); p['forearm_R'] = (40 + 100 * d if not rel else 20, 0, -30 * d)
    p['chest'] = (0, -25, 0); p['head'] = (0, 20, 0); return p
def P_block(t):
    p = P_eidle(t); p['upper_arm_L'] = (80 + 3 * S(t), 0, -10); p['forearm_L'] = (60, 0, -40); p['spine'] = (6, 0, 0); p['head'] = (8, 0, 0)
    p['thigh_L'] = (20, 0, 0); p['shin_L'] = (-25, 0, 0); p['hips@loc'] = (0, -0.04, 0); return p
def P_flee(t):
    p = walkcycle(t, amp=1.5, lean=10, arm=0, knee=1.6, bounce=0.06)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (0, 0, sx * (150 + 15 * S(t * 2, 0.25 if s == 'L' else 0))); p['forearm_' + s] = (30, 0, 0)
    p['head'] = (-10, 15 * S(t), 0); return p
def P_cower(t):
    p = P_crouch(t)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (60, 0, sx * 70); p['forearm_' + s] = (120, 0, 0)
    p['head'] = (25, 0, 0); p['chest'] = (15 + 3 * S(t * 4), 0, 0); return p
def P_taunt(t):
    p = P_eidle(t); p['upper_arm_L'] = (60 + 30 * abs(S(t * 2)), 0, 30); p['forearm_L'] = (90, 0, 0); p['head'] = (-8 + 6 * S(t * 2), 0, 0); return p
def P_write(t):
    p = P_sit(t); p['upper_arm_R'] = (40, 0, -10); p['forearm_R'] = (80, 0, 0); p['hand_R'] = (-10 + 6 * S(t * 5), 0, 8 * S(t * 3))
    p['upper_arm_L'] = (35, 0, 15); p['forearm_L'] = (70, 0, 0); p['head'] = (20, 4 * S(t), 0); p['spine'] = (8, 0, 0); return p
def P_excited(t):
    p = P_talk(t); k = abs(S(t * 2)); p['hips@loc'] = (0, 0.03 * k, 0)
    p['upper_arm_L'] = (40 + 40 * k, 0, 40); p['forearm_L'] = (60, 0, 0); p['upper_arm_R'] = (40 + 40 * abs(S(t * 2, .5)), 0, -40); return p
def P_kneel(t):
    p = {'hips@loc': (0, -0.4, 0.0), 'thigh_L': (90, 0, 0), 'shin_L': (-90, 0, 0), 'thigh_R': (0, 0, 0), 'shin_R': (-100, 0, 0), 'foot_R': (60, 0, 0)}
    p['spine'] = (15, 0, 0); p['head'] = (10, 0, 0); p['upper_arm_L'] = (20, 0, 10); p['forearm_L'] = (40, 0, 0); p['upper_arm_R'] = (20, 0, -10); p['forearm_R'] = (40, 0, 0)
    p['chest'] = (1.5 * S(t), 0, 0); return p
def P_hammerhold(t):
    p = P_idle(t)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (35, 0, -sx * 18); p['forearm_' + s] = (40, 0, -sx * 10)
    p['chest'] = (2 * S(t), 0, 0); return p
def P_hammerwalk(t):
    p = walkcycle(t, amp=0.9, arm=0, bounce=0.05)
    for s, sx in (('L', 1), ('R', -1)): p['upper_arm_' + s] = (35, 0, -sx * 18); p['forearm_' + s] = (40, 0, -sx * 10)
    return p
def P_dizzy(t):
    p = P_stunned(t); p['hips@loc'] = (0.04 * S(t), -0.05, 0.04 * C(t)); return p

ANIMS = [('idle', 48, P_idle), ('hold', 48, P_hold), ('aim', 48, P_aim), ('walk', 26, CB.P_walk), ('run', 16, CB.P_run),
         ('runaim', 16, P_runaim), ('walkaim', 24, P_walkaim), ('backaim', 24, P_backaim), ('strafeL', 18, P_strafeL), ('strafeR', 18, P_strafeR),
         ('jump', 12, P_jumpup), ('fall', 24, P_fall), ('roll', 14, P_roll), ('hit', 10, P_hit), ('phone', 48, P_phone), ('climb', 24, P_climb),
         ('pickup', 20, P_pickup), ('talk', 72, P_talk), ('wave', 24, P_wave), ('nod', 24, P_nod), ('shrug', 30, P_shrug), ('point', 48, P_point),
         ('type', 24, P_type), ('sit', 72, P_sit), ('sitsleep', 96, P_sitsleep), ('down', 72, P_down), ('stunned', 24, P_stunned),
         ('handsup', 48, P_handsup), ('cheer', 20, P_cheer), ('sad', 48, P_sad), ('think', 48, P_think), ('lookaround', 96, P_lookaround),
         ('crouch', 48, P_crouch), ('eidle', 48, P_eidle), ('ewalk', 26, P_ewalk), ('echarge', 16, P_echarge), ('thrust', 22, P_thrust),
         ('swing', 26, P_swing), ('slam', 36, P_slam), ('throw', 22, P_throw), ('bow', 40, P_bow), ('block', 48, P_block), ('flee', 16, P_flee),
         ('cower', 24, P_cower), ('taunt', 24, P_taunt), ('write', 48, P_write), ('excited', 36, P_excited), ('kneel', 48, P_kneel),
         ('hammerhold', 48, P_hammerhold), ('hammerwalk', 30, P_hammerwalk), ('dizzy', 30, P_dizzy)]

def build_anims():
    clear_scene(); rig = make_rig()
    bpy.context.scene.render.fps = 24
    for n, fr, fn in ANIMS: keyframe_action(rig, n, fr, fn)
    export('anims', anim=True, objs=[rig])

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    reset()
    todo = argv or list(CHARS) + ['cat', 'anims']
    for n in todo:
        if n == 'cat': build_cat('cat', '#c87a3a', '#f4e1c4')
        elif n == 'anims': build_anims()
        else: build_char(n)
