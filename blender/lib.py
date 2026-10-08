"""Procedural modelling helpers for Castle TIME (Blender 4.5, headless).
All geometry is generated from code. Materials are simple Principled BSDFs; material names starting with
'T_' are swapped at runtime in Godot for procedurally generated triplanar textures (see game/scripts/matlib.gd)."""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'game', 'assets', 'models'))
os.makedirs(OUT, exist_ok=True)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for m in list(bpy.data.materials): bpy.data.materials.remove(m)

def mat(name, col=(0.8, 0.8, 0.8), rough=0.7, metal=0.0, emit=None, estr=1.0, alpha=None):
    if name in bpy.data.materials: return bpy.data.materials[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = estr
    if alpha is not None:
        b.inputs['Alpha'].default_value = alpha; m.blend_method = 'BLEND'
    m.diffuse_color = (*col, 1)
    return m

def hexc(h):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(ch * 2 for ch in h)
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)  # sRGB -> linear

def M(name, h, rough=0.7, metal=0.0, **kw):
    return mat(name, hexc(h), rough, metal, **kw)

def setmat(o, m):
    if m is None or o.type != 'MESH': return
    o.data.materials.clear(); o.data.materials.append(m)

def act(): return bpy.context.active_object

def select(objs, active=None):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = active or objs[0]

def smooth(o, angle=40):
    for p in o.data.polygons: p.use_smooth = True
    try: o.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception: pass

def apply_mods(o):
    select([o])
    for md in list(o.modifiers):
        try: bpy.ops.object.modifier_apply(modifier=md.name)
        except Exception as e: print('mod fail', e)

def bevel(o, w, seg=2, angle=40):
    md = o.modifiers.new('bev', 'BEVEL'); md.width = w; md.segments = seg; md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(angle); md.harden_normals = False
    apply_mods(o); smooth(o, 45); return o

def subsurf(o, lvl=1):
    md = o.modifiers.new('sub', 'SUBSURF'); md.levels = lvl; md.render_levels = lvl
    apply_mods(o); smooth(o, 180); return o

def _fin(o, m, bev=0, seg=2, sm=False, name=None):
    if bev: bevel(o, bev, seg)
    elif sm: smooth(o)
    setmat(o, m)
    if name: o.name = name
    return o

def box(sx, sy, sz, loc=(0, 0, 0), m=None, rot=(0, 0, 0), bev=0, seg=2, name=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = act(); o.scale = (sx, sy, sz); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _fin(o, m, bev, seg, name=name)

def cyl(r, h, loc=(0, 0, 0), m=None, rot=(0, 0, 0), v=24, r2=None, bev=0, name=None, cap=True):
    if r2 is None: bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=v,
                                                       end_fill_type='NGON' if cap else 'NOTHING')
    else: bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=h, location=loc, rotation=rot, vertices=v)
    o = act(); _fin(o, m, bev, name=name)
    if not bev: smooth(o, 50)
    return o

def sph(r, loc=(0, 0, 0), m=None, s=(1, 1, 1), seg=24, rings=14, rot=(0, 0, 0), name=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=rings, rotation=rot)
    o = act(); o.scale = s; bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _fin(o, m, sm=True, name=name)

def tor(R, r, loc=(0, 0, 0), m=None, rot=(0, 0, 0), maj=28, mn=10, name=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot, major_segments=maj, minor_segments=mn)
    return _fin(act(), m, sm=True, name=name)

def plane(sx, sy, loc=(0, 0, 0), m=None, rot=(0, 0, 0), name=None):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = act(); o.scale = (sx, sy, 1); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _fin(o, m, name=name)

def loft(rings, m=None, name='loft', cap=True, seg=16):
    """rings: list of (center Vector/tuple, rx, ry[, z_axis_dir]) - builds a generalized cylinder along the centers."""
    bm = bmesh.new(); prev = None; verts_rings = []
    cs = [Vector(r[0]) for r in rings]
    for i, r in enumerate(rings):
        c = cs[i]
        d = (cs[min(i + 1, len(cs) - 1)] - cs[max(i - 1, 0)]).normalized()
        up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
        ax = up.cross(d).normalized(); ay = d.cross(ax).normalized()
        vr = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            vr.append(bm.verts.new(c + ax * math.cos(a) * r[1] + ay * math.sin(a) * r[2]))
        verts_rings.append(vr)
    for i in range(len(verts_rings) - 1):
        a, b = verts_rings[i], verts_rings[i + 1]
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    if cap:
        bm.faces.new(list(reversed(verts_rings[0]))); bm.faces.new(verts_rings[-1])
    me = bpy.data.meshes.new(name); bm.normal_update(); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    select([o]); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    smooth(o, 180); setmat(o, m); return o

def lathe(profile, m=None, name='lathe', seg=32, loc=(0, 0, 0)):
    """profile: list of (radius, z). Revolve around Z."""
    bm = bmesh.new(); rings = []
    for r, z in profile:
        rings.append([bm.verts.new((loc[0] + r * math.cos(2 * math.pi * k / seg), loc[1] + r * math.sin(2 * math.pi * k / seg), loc[2] + z)) for k in range(seg)])
    for i in range(len(rings) - 1):
        for k in range(seg):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % seg], rings[i + 1][(k + 1) % seg], rings[i + 1][k]))
    if profile[0][0] > 1e-4: bm.faces.new(list(reversed(rings[0])))
    if profile[-1][0] > 1e-4: bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    select([o]); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    smooth(o, 50); setmat(o, m); return o

def extrude_poly(pts, depth, m=None, name='poly', loc=(0, 0, 0), rot=(0, 0, 0)):
    """2D polygon (x,z) in XZ plane, extruded along Y by depth (centered)."""
    bm = bmesh.new()
    a = [bm.verts.new((x, -depth / 2, z)) for x, z in pts]; b = [bm.verts.new((x, depth / 2, z)) for x, z in pts]
    bm.faces.new(a); bm.faces.new(list(reversed(b)))
    n = len(pts)
    for i in range(n): bm.faces.new((a[i], b[i], b[(i + 1) % n], a[(i + 1) % n]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    select([o]); bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    setmat(o, m); return o

def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(o); o.location = loc
    if parent: parent_keep(o, parent)
    return o

def parent_keep(child, parent):
    mw = child.matrix_world.copy(); child.parent = parent; child.matrix_world = mw

def join(name, objs, origin=None):
    objs = [o for o in objs if o is not None]
    select(objs)
    if len(objs) > 1: bpy.ops.object.join()
    o = act(); o.name = name; o.data.name = name
    if origin is not None: set_origin(o, origin)
    return o

def set_origin(o, origin):
    bpy.context.scene.cursor.location = origin; select([o])
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); bpy.context.scene.cursor.location = (0, 0, 0)

def clear_scene():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes): bpy.data.meshes.remove(me)
    for a in list(bpy.data.armatures): bpy.data.armatures.remove(a)
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)

def export(name, anim=False, objs=None):
    path = os.path.join(OUT, name + '.glb')
    if objs is not None: select(objs)
    kw = dict(filepath=path, export_format='GLB', export_apply=True, export_yup=True, export_cameras=False,
              export_lights=False, export_animations=anim, use_selection=objs is not None, export_extras=True)
    if anim:
        kw.update(export_animation_mode='ACTIONS', export_force_sampling=True, export_frame_step=1,
                  export_optimize_animation_size=True, export_def_bones=False)
    bpy.ops.export_scene.gltf(export_image_format='NONE', **kw)
    print('EXPORTED', name, os.path.getsize(path) // 1024, 'KB')

# ---------------------------------------------------------------- Castle TIME additions
COLS = []   # collision proxy objects collected per export
def colbox(sx, sy, sz, loc=(0, 0, 0), rot=(0, 0, 0)):
    """invisible collision box (joined into one *-colonly mesh at export)"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = act(); o.scale = (sx, sy, sz); bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    COLS.append(o); compact_cols(); return o

def compact_cols(force=False):
    global COLS
    if len(COLS) > 120 or (force and len(COLS) > 1):
        for c in COLS: c.data.materials.clear()
        o = join('cols_acc', COLS); COLS[:] = [o]

def colobj(o):
    """use a copy of an existing mesh as collision"""
    c = o.copy(); c.data = o.data.copy(); bpy.context.collection.objects.link(c); COLS.append(c); return c

def solid(sx, sy, sz, loc=(0, 0, 0), m=None, rot=(0, 0, 0), bev=0, seg=2, name=None):
    """visible box + matching collision box"""
    colbox(sx, sy, sz, loc, rot); return box(sx, sy, sz, loc, m, rot, bev, seg, name)

def finish_cols(name='WORLD'):
    if not COLS: return None
    for c in COLS: c.data.materials.clear()
    o = join(name + '-colonly', list(COLS)); COLS[:] = []
    return o

def marker(name, loc, rot_z=0.0, **props):
    """named empty -> Node3D in Godot. rot_z in degrees (Blender Z = Godot Y)."""
    o = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (0, 0, math.radians(rot_z))
    for k, v in props.items(): o[k] = v
    return o

def merge_by_material(objs, name):
    """join a list of mesh objects (keeps per-face materials)"""
    objs = [o for o in objs if o is not None and o.type == 'MESH']
    if not objs: return None
    return join(name, objs)

def arr(fn, n, step, start=(0, 0, 0)):
    out = []
    for i in range(n):
        out.append(fn(i, Vector(start) + Vector(step) * i))
    return out
