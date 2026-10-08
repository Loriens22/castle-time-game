"""Castle TIME props: weapons, gadgets, dynamic props, food, collectibles and rigid-part animals.
Each prop is a root object 'P-<name>' at the origin (children keep their names for animation).
run: blender -b -P blender/props.py   -> game/assets/models/props.glb"""
import bpy, math, sys, os
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(__file__))
from lib import *
import kit
from kit import barrel, crate
reset(); kit.mats(); globals().update({k: v for k, v in kit.__dict__.items() if k.isupper()})
ROOTS = []
def prop(name, objs, origin=(0, 0, 0)):
    o = join('P-' + name, [x for x in objs if x]); set_origin(o, origin); o.location = (0, 0, 0); ROOTS.append(o); return o
def rig_prop(name, body, parts):
    """root mesh + named child meshes (for procedural animation in Godot)"""
    b = join('P-' + name, body if isinstance(body, list) else [body]); ROOTS.append(b)
    for pn, (objs, pivot) in parts.items():
        c = join(pn, objs if isinstance(objs, list) else [objs]); set_origin(c, pivot); c.parent = b; c.matrix_parent_inverse = b.matrix_world.inverted()
    return b

NEON = M('neon_blaster', '#39ffd0', 0.3, emit=(0.22, 1.0, 0.82), estr=3.0); BODY = M('blaster_body', '#e8ebef', 0.25, 0.3)
DARKP = M('blaster_dark', '#1a1d24', 0.35, 0.5); RED = M('blaster_red', '#ff3b5c', 0.3, emit=(1.0, 0.15, 0.3), estr=2.0)
# ---------------------------------------------------------------- weapons & gadgets (grip at origin, barrel towards -Y)
b = [box(0.07, 0.34, 0.11, (0, -0.12, 0.08), BODY, bev=0.02), box(0.05, 0.09, 0.15, (0, 0.0, -0.02), DARKP, rot=(-0.3, 0, 0), bev=0.015),
     cyl(0.03, 0.2, (0, -0.33, 0.1), DARKP, rot=(math.pi / 2, 0, 0), v=14), tor(0.034, 0.008, (0, -0.42, 0.1), NEON, rot=(math.pi / 2, 0, 0), maj=14, mn=6),
     box(0.075, 0.2, 0.02, (0, -0.12, 0.14), NEON), cyl(0.022, 0.12, (0, -0.06, 0.16), RED, rot=(math.pi / 2, 0, 0), v=10),
     box(0.08, 0.06, 0.08, (0, 0.06, 0.09), DARKP, bev=0.01)]
for k in range(4): b.append(box(0.08, 0.012, 0.06, (0, -0.2 - k * 0.025, 0.06), DARKP))
prop('blaster', b)
empty('P-blaster_muzzle', (0, -0.44, 0.1)); ROOTS.append(bpy.data.objects['P-blaster_muzzle'])
# flip phone ('Motorola' teleport phone) - open
ph = [box(0.055, 0.012, 0.1, (0, 0, 0.05), DARKP, bev=0.004), box(0.055, 0.012, 0.1, (0, 0.03, 0.145), DARKP, rot=(-0.35, 0, 0), bev=0.004),
      box(0.045, 0.004, 0.065, (0, 0.022, 0.15), M('D_phone_screen', '#ffffff', 0.3, emit=(0.4, 1, 0.6), estr=1.2), rot=(-0.35, 0, 0)),
      box(0.04, 0.004, 0.06, (0, -0.007, 0.045), M('keys', '#9aa', 0.4, 0.6)), cyl(0.004, 0.05, (0.02, 0.0, 0.12), DARKP, v=6),
      box(0.03, 0.002, 0.008, (0, -0.007, 0.088), NEON)]
prop('phone', ph)
# medieval weapons (grip at origin, shaft along Z)
prop('pitchfork', [cyl(0.02, 1.9, (0, 0, 0.3), WOOD_D, v=8), box(0.24, 0.03, 0.03, (0, 0, 1.25), IRON)] + [cyl(0.012, 0.32, (x, 0, 1.4), IRON, v=6, r2=0.002) for x in (-0.11, 0, 0.11)])
prop('torch', [cyl(0.03, 0.7, (0, 0, 0.15), WOOD_D, v=8), cyl(0.05, 0.14, (0, 0, 0.52), M('rag', '#3a2a1a', 0.9), v=8)])
empty('P-torch_flame', (0, 0, 0.62)); ROOTS.append(bpy.data.objects['P-torch_flame'])
prop('spear', [cyl(0.018, 2.2, (0, 0, 0.5), WOOD_D, v=8), cyl(0.04, 0.3, (0, 0, 1.75), IRON, v=4, r2=0.0)])
prop('sword', [box(0.05, 0.012, 0.85, (0, 0, 0.55), M('blade', '#c8ccd2', 0.2, 0.95)), box(0.22, 0.03, 0.03, (0, 0, 0.12), GOLD),
               cyl(0.018, 0.16, (0, 0, 0.03), M('grip', '#3a2214', 0.8), v=8), sph(0.03, (0, 0, -0.06), GOLD)])
sh = [cyl(0.34, 0.05, (0, 0, 0), CLOTH_R, rot=(math.pi / 2, 0, 0), v=6), cyl(0.12, 0.06, (0, -0.02, 0), GOLD, rot=(math.pi / 2, 0, 0), v=6),
      tor(0.33, 0.02, (0, 0, 0), IRON, rot=(math.pi / 2, 0, 0), maj=6, mn=4)]
prop('shield', sh)
bw = []
for k in range(9):
    a = -0.9 + k * 0.225; bw.append(box(0.025, 0.025, 0.2, (0, -math.cos(a) * 0.1 + 0.1, math.sin(a) * 0.65), WOOD_D, rot=(-a, 0, 0)))
bw.append(cyl(0.003, 1.2, (0, 0.08, 0), ROPE, v=4))
prop('bow', bw)
prop('arrow', [cyl(0.008, 0.8, (0, 0, 0), WOOD, rot=(math.pi / 2, 0, 0), v=5), cyl(0.02, 0.07, (0, -0.42, 0), IRON, rot=(-math.pi / 2, 0, 0), v=4, r2=0.0),
               box(0.002, 0.1, 0.03, (0, 0.35, 0), CLOTH_W), box(0.03, 0.1, 0.002, (0, 0.35, 0), CLOTH_W)])
prop('hammer', [cyl(0.035, 1.8, (0, 0, 0.6), WOOD_D, v=8), box(0.55, 0.32, 0.32, (0, 0, 1.45), IRON, bev=0.04), cyl(0.18, 0.05, (0.3, 0, 1.45), GOLD, rot=(0, math.pi / 2, 0), v=6)])
prop('cleaver', [box(0.012, 0.16, 0.26, (0, -0.06, 0.22), M('blade', '#c8ccd2')), cyl(0.018, 0.14, (0, 0, 0.04), WOOD_D, v=6)])
prop('keyring', [tor(0.06, 0.008, (0, 0, 0), IRON, maj=12, mn=4)] + [box(0.012, 0.012, 0.12, (k * 0.02 - 0.02, 0, -0.08), IRON) for k in range(3)])
# the clock key (spire)
ck = [cyl(0.02, 0.32, (0, 0, 0), GOLD, rot=(0, math.pi / 2, 0), v=10), tor(0.06, 0.014, (-0.2, 0, 0), GOLD, rot=(math.pi / 2, 0, 0), maj=16, mn=6)]
for k in range(6): ck.append(box(0.012, 0.012, 0.03, (-0.2 + math.cos(k * 1.047) * 0.05, 0, math.sin(k * 1.047) * 0.05), GOLD))
ck += [box(0.03, 0.012, 0.06, (0.14, 0, -0.035), GOLD), box(0.025, 0.012, 0.04, (0.09, 0, -0.03), GOLD), sph(0.025, (-0.2, 0, 0), M('ruby', '#c0102a', 0.1, 0.2, emit=(0.5, 0, 0.05), estr=1.0))]
prop('key', ck)
# the scroll
sc = [cyl(0.05, 0.36, (0, 0, 0), M('D_scroll', '#ffffff', 0.85), rot=(0, math.pi / 2, 0), v=16)]
for sx in (-1, 1): sc += [cyl(0.015, 0.06, (sx * 0.21, 0, 0), WOOD_D, rot=(0, math.pi / 2, 0), v=8), sph(0.022, (sx * 0.24, 0, 0), GOLD)]
sc.append(tor(0.052, 0.008, (0, 0, 0), CLOTH_R, rot=(0, math.pi / 2, 0), maj=16, mn=4)); sc.append(cyl(0.02, 0.01, (0, -0.055, 0), M('seal', '#a0101a', 0.4), rot=(math.pi / 2, 0, 0), v=10))
prop('scroll', sc)
# ---------------------------------------------------------------- dynamic props
prop('barrel', barrel(0, 0, 0), (0, 0, 0.45))
prop('crate', crate(0, 0, 0, 0.9), (0, 0, 0.405))
prop('pot', [lathe([(0.0, 0), (0.18, 0), (0.28, 0.15), (0.3, 0.3), (0.2, 0.5), (0.14, 0.58), (0.17, 0.62), (0.12, 0.62)], M('pot', '#a0522d', 0.7), 'pot', 16)], (0, 0, 0.3))
prop('cabbage', [sph(0.16, (0, 0, 0), M('cabbage', '#6f9e3a', 0.8), seg=10, rings=7)] + [sph(0.13, (math.cos(a) * 0.05, math.sin(a) * 0.05, 0.02), M('cabbage2', '#8fc04a', 0.8), s=(1, 1, 0.6), seg=8, rings=5) for a in (0, 2.1, 4.2)])
prop('bread', [sph(0.12, (0, 0, 0), M('bread', '#c8904a', 0.8), s=(1.6, 0.9, 0.7), seg=12, rings=8)] + [box(0.02, 0.15, 0.02, (x, 0, 0.07), M('crust', '#8a5a2a', 0.8), rot=(0, 0, 0.4)) for x in (-0.08, 0, 0.08)])
prop('apple', [sph(0.07, (0, 0, 0), M('apple', '#c0242a', 0.4), seg=12, rings=8), cyl(0.006, 0.04, (0, 0, 0.07), WOOD_D, v=5), box(0.04, 0.005, 0.02, (0.02, 0, 0.08), M('leaf', '#4e8a2a', 0.7))])
prop('roast', [sph(0.12, (0, 0, 0), M('roast', '#8a4a20', 0.5), s=(1.4, 0.9, 0.8), seg=12, rings=8), cyl(0.025, 0.22, (0.2, 0, 0), M('bone', '#efe6d6', 0.6), rot=(0, math.pi / 2, 0), v=8), sph(0.035, (0.31, 0, 0), M('bone', '#efe6d6'))])
prop('fireball', [sph(0.5, (0, 0, 0), M('fireball', '#ffb040', 0.5, emit=(1.0, 0.5, 0.1), estr=5), seg=14, rings=10), sph(0.35, (0.1, 0.1, 0.15), FIRE, seg=10, rings=6)])
prop('debris', [box(0.4, 2.6, 0.4, (0, 0, 0), TIMBER), box(0.3, 0.6, 0.3, (0.1, 1.0, 0.2), SOOT)])
prop('chandelier', [tor(1.0, 0.06, (0, 0, 0), IRON, maj=24, mn=6)] + [cyl(0.04, 0.2, (math.cos(k * 0.785), math.sin(k * 0.785), 0.12), CANDLE, v=6) for k in range(8)]
     + [cyl(0.01, 1.4, (math.cos(k * 2.09) * 0.5, math.sin(k * 2.09) * 0.5, 0.65), IRON, rot=(math.sin(k * 2.09) * 0.36, -math.cos(k * 2.09) * 0.36, 0), v=4) for k in range(3)])
prop('armour_stand', [cyl(0.03, 1.8, (0, 0, 0.9), WOOD_D, v=6), cyl(0.3, 0.05, (0, 0, 0.02), WOOD_D, v=12), sph(0.25, (0, 0, 1.35), M('steel', '#b8bec6', 0.25, 0.9), s=(1.3, 0.8, 1.2)),
                      cyl(0.15, 0.32, (0, 0, 1.78), M('steel', '#b8bec6'), v=14), box(0.15, 0.02, 0.025, (0, -0.15, 1.8), DARK)] + [sph(0.12, (sx * 0.35, 0, 1.55), M('steel', '#b8bec6')) for sx in (-1, 1)])
# ---------------------------------------------------------------- collectibles: anachronisms that fell out of Juno's backpack
prop('col_cmos', [cyl(0.1, 0.03, (0, 0, 0), M('cmos', '#d0d4da', 0.2, 1.0), v=24), cyl(0.08, 0.032, (0, 0, 0.001), M('cmos_top', '#e8ebef', 0.15, 1.0), v=24), box(0.08, 0.002, 0.012, (0, -0.0, 0.017), M('cmos_txt', '#2a2a2a', 0.5))])
prop('col_earbud', [sph(0.06, (0, 0, 0), M('white_plastic', '#f4f4f4', 0.2), s=(1, 1, 1.2)), cyl(0.022, 0.12, (0, 0, -0.1), M('white_plastic', '#f4f4f4'), v=10)])
prop('col_sunglasses', [box(0.1, 0.02, 0.06, (sx * 0.06, 0, 0), M('shades', '#111111', 0.1, 0.5), bev=0.01) for sx in (-1, 1)] + [box(0.03, 0.01, 0.01, (0, 0, 0.02), M('shades', '#111111')), box(0.01, 0.14, 0.01, (0.11, 0.07, 0.02), M('shades', '#111111')), box(0.01, 0.14, 0.01, (-0.11, 0.07, 0.02), M('shades', '#111111'))])
prop('col_tamagotchi', [sph(0.08, (0, 0, 0), M('tama', '#ff6ab0', 0.3), s=(1, 0.5, 1.15)), box(0.07, 0.01, 0.06, (0, -0.04, 0.01), M('tama_scr', '#b8d0a0', 0.4, emit=(0.3, 0.45, 0.2), estr=0.5))] + [sph(0.01, (x, -0.04, -0.05), M('tama_btn', '#ffe040', 0.3)) for x in (-0.025, 0, 0.025)])
prop('col_vr', [box(0.22, 0.12, 0.12, (0, 0, 0), M('vr', '#f2f2f2', 0.3), bev=0.03), box(0.2, 0.02, 0.1, (0, -0.065, 0), M('vr_face', '#222222', 0.4)), tor(0.13, 0.012, (0, 0.06, 0), M('vr_strap', '#333333', 0.8), rot=(0, 0, 0), maj=16, mn=4)])
prop('col_phonecase', [box(0.09, 0.012, 0.17, (0, 0, 0), M('case', '#9a6aff', 0.3), bev=0.012), cyl(0.012, 0.014, (0.025, 0.004, 0.06), M('lens', '#111', 0.1), rot=(math.pi / 2, 0, 0), v=10)])
prop('col_gameboy', [box(0.1, 0.03, 0.16, (0, 0, 0), M('gb', '#c8c4be', 0.5), bev=0.01), box(0.07, 0.005, 0.055, (0, -0.016, 0.035), M('gb_scr', '#8a9a5a', 0.4, emit=(0.2, 0.25, 0.1), estr=0.4)),
                     box(0.03, 0.006, 0.01, (-0.025, -0.016, -0.03), DARK), box(0.01, 0.006, 0.03, (-0.025, -0.016, -0.03), DARK), sph(0.009, (0.03, -0.016, -0.025), M('gb_btn', '#a0204a', 0.4)), sph(0.009, (0.015, -0.016, -0.035), M('gb_btn', '#a0204a'))])
prop('col_fidget', [cyl(0.03, 0.015, (0, 0, 0), M('fid', '#30b0ff', 0.2, 0.6), v=16)] + [cyl(0.026, 0.015, (math.cos(k * 2.09) * 0.06, math.sin(k * 2.09) * 0.06, 0), M('fid', '#30b0ff'), v=16) for k in range(3)])
# ---------------------------------------------------------------- animals (rigid parts, animated in Godot)
def legs(m, pts, h, r):
    return {('leg%d' % i): ([cyl(r, h, (x, y, h / 2), m, v=8)], (x, y, h)) for i, (x, y) in enumerate(pts)}
pink = M('pig', '#e8a0a0', 0.7); pk = {'head': ([sph(0.22, (0, -0.55, 0.5), pink, s=(1, 1.1, 1)), cyl(0.09, 0.08, (0, -0.76, 0.47), M('snout', '#d98a8a', 0.6), rot=(math.pi / 2, 0, 0), v=12),
                                             cyl(0.08, 0.1, (0.12, -0.5, 0.68), pink, v=3, r2=0.0, rot=(0.3, 0.3, 0)), cyl(0.08, 0.1, (-0.12, -0.5, 0.68), pink, v=3, r2=0.0, rot=(0.3, -0.3, 0)),
                                             sph(0.025, (0.08, -0.72, 0.56), DARK), sph(0.025, (-0.08, -0.72, 0.56), DARK)], (0, -0.4, 0.5))}
pk.update(legs(pink, [(0.15, -0.3), (-0.15, -0.3), (0.15, 0.3), (-0.15, 0.3)], 0.3, 0.06))
pk['tail'] = ([tor(0.04, 0.012, (0, 0.5, 0.5), pink, maj=10, mn=4)], (0, 0.48, 0.5))
rig_prop('pig', [sph(0.33, (0, 0, 0.52), pink, s=(0.95, 1.6, 0.9), seg=16, rings=10)], pk)
wool = M('wool', '#efeae0', 0.95); sp = {'head': ([sph(0.14, (0, -0.55, 0.75), M('sheepface', '#3a3230', 0.7), s=(0.9, 1.4, 1)), box(0.2, 0.05, 0.08, (0, -0.5, 0.82), M('sheepface', '#3a3230'), rot=(0, 0, 0))], (0, -0.4, 0.7))}
sp.update(legs(M('sheepface', '#3a3230'), [(0.14, -0.28), (-0.14, -0.28), (0.14, 0.28), (-0.14, 0.28)], 0.4, 0.04))
rig_prop('sheep', [sph(0.35, (0, 0, 0.65), wool, s=(1, 1.4, 0.95), seg=14, rings=10)] + [sph(0.16, (math.cos(k) * 0.25, math.sin(k) * 0.35, 0.8), wool, seg=8, rings=6) for k in range(6)], sp)
hen = M('hen', '#f2ece0', 0.8); cr = {'head': ([sph(0.07, (0, -0.12, 0.38), hen), cyl(0.02, 0.05, (0, -0.19, 0.37), M('beak', '#f0a020', 0.5), rot=(math.pi / 2, 0, 0), v=6, r2=0), box(0.015, 0.06, 0.05, (0, -0.12, 0.45), M('comb', '#d01a1a', 0.6))], (0, -0.08, 0.3))}
cr.update(legs(M('beak', '#f0a020'), [(0.04, 0.0), (-0.04, 0.0)], 0.14, 0.012))
rig_prop('chicken', [sph(0.13, (0, 0.0, 0.24), hen, s=(0.9, 1.3, 1)), cyl(0.06, 0.12, (0, 0.15, 0.32), hen, rot=(-0.6, 0, 0), v=8, r2=0.02)], cr)
cowm = M('cow', '#f4f0ea', 0.7); spot = M('cowspot', '#2a2522', 0.7)
cw = {'head': ([box(0.3, 0.5, 0.35, (0, -1.15, 1.25), cowm, bev=0.08), box(0.32, 0.18, 0.2, (0, -1.38, 1.15), M('muzzle', '#e8b0a0', 0.6), bev=0.05),
                cyl(0.03, 0.2, (0.17, -1.05, 1.45), M('horn', '#e8e0c8', 0.5), rot=(0, 1.2, 0), v=6, r2=0.01), cyl(0.03, 0.2, (-0.17, -1.05, 1.45), M('horn', '#e8e0c8'), rot=(0, -1.2, 0), v=6, r2=0.01)], (0, -0.9, 1.2))}
cw.update(legs(cowm, [(0.25, -0.6), (-0.25, -0.6), (0.25, 0.6), (-0.25, 0.6)], 0.75, 0.08))
cw['tail'] = ([cyl(0.025, 0.7, (0, 0.95, 0.95), cowm, rot=(0.2, 0, 0), v=6)], (0, 0.92, 1.3))
rig_prop('cow', [box(0.75, 1.8, 0.75, (0, 0, 1.1), cowm, bev=0.18, seg=3), sph(0.25, (0.38, 0.2, 1.2), spot, s=(0.3, 1.2, 1)), sph(0.22, (-0.38, -0.3, 1.1), spot, s=(0.3, 1.1, 1.2)), sph(0.12, (0, 0.4, 0.68), M('udder', '#f0b0b0', 0.6))], cw)
brown = M('horse', '#6a4128', 0.6); mane = M('mane', '#1a1410', 0.9)
hs = {'head': ([box(0.25, 0.75, 0.3, (0, -1.35, 1.75), brown, rot=(0.8, 0, 0), bev=0.08), box(0.08, 0.6, 0.25, (0, -1.0, 1.75), mane, rot=(-0.6, 0, 0))], (0, -0.95, 1.45))}
hs.update(legs(brown, [(0.22, -0.65), (-0.22, -0.65), (0.22, 0.65), (-0.22, 0.65)], 0.95, 0.07))
hs['tail'] = ([cyl(0.06, 0.8, (0, 1.05, 1.0), mane, rot=(0.4, 0, 0), v=8, r2=0.02)], (0, 0.95, 1.35))
rig_prop('horse', [box(0.62, 1.9, 0.7, (0, 0, 1.3), brown, bev=0.2, seg=3), box(0.3, 0.6, 0.6, (0, -0.95, 1.55), brown, rot=(-0.7, 0, 0), bev=0.1)], hs)
ratm = M('rat', '#5a524c', 0.8)
rig_prop('rat', [sph(0.07, (0, 0, 0.07), ratm, s=(0.9, 1.7, 0.8)), sph(0.04, (0, -0.12, 0.08), ratm, s=(1, 1.4, 1)), sph(0.02, (0.03, -0.1, 0.12), M('ear', '#e0a0a0', 0.6)), sph(0.02, (-0.03, -0.1, 0.12), M('ear', '#e0a0a0'))],
         {'tail': ([cyl(0.01, 0.25, (0, 0.24, 0.05), M('ear', '#e0a0a0'), rot=(math.pi / 2, 0, 0), v=4, r2=0.003)], (0, 0.12, 0.06))})
for r_ in ROOTS: r_.select_set(True)
export('props', anim=False, objs=[o for o in bpy.data.objects])
