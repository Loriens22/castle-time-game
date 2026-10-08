"""Quick Cycles preview of exported GLBs: one 3/4 view per file, montaged by tools/montage.
blender -b -P blender/preview.py -- outdir a.glb b.glb ... [--az=deg] [--el=deg]"""
import bpy, sys, os, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
outdir = argv[0]; files = [a for a in argv[1:] if '=' not in a and not a.startswith('--')]
opt = {a.lstrip('-').split('=')[0]: float(a.split('=')[1]) for a in argv if '=' in a}
for f in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f)
    bpy.context.view_layer.update()
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in bpy.data.objects:
        if o.type == 'MESH' and not o.name.endswith('colonly'):
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
        if o.name.endswith('-colonly'): o.hide_render = True
    ctr = (mn + mx) / 2; size = (mx - mn).length
    if 'cz' in opt: ctr = Vector((opt.get('cx', 0), opt.get('cy', 0), opt['cz'])); size = opt.get('size', 2.0)
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = int(opt.get('s', 20)); sc.cycles.device = 'CPU'
    sc.render.resolution_x = int(opt.get('w', 600)); sc.render.resolution_y = int(opt.get('h', 800))
    sc.render.filepath = os.path.join(outdir, os.path.basename(f).replace('.glb', '.png'))
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.6, 0.68, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    L = bpy.data.lights.new('sun', 'SUN'); L.energy = 3.0; lo = bpy.data.objects.new('sun', L); sc.collection.objects.link(lo); lo.rotation_euler = (0.7, 0.3, -0.7)
    bpy.ops.mesh.primitive_plane_add(size=500, location=(0, 0, mn.z))
    cam = bpy.data.cameras.new('c'); co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co
    cam.lens = opt.get('lens', 50); cam.clip_end = 2000
    az = math.radians(opt.get('az', -30)); el = math.radians(opt.get('el', 12)); d = size * opt.get('d', 1.6)
    co.location = ctr + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * d
    co.rotation_euler = (ctr - co.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.render.render(write_still=True)
