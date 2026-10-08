class_name FX
## Visual effects built entirely in code: laser beams, sparks, fire, smoke, explosions, KO stars.

static var _mats := {}
static var _soft: Texture2D
static var _meshes := {}

static func soft_tex() -> Texture2D:
	if _soft: return _soft
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1)); g.set_color(1, Color(1, 1, 1, 0))
	g.add_point(0.35, Color(1, 1, 1, 0.7))
	var t := GradientTexture2D.new()
	t.gradient = g; t.fill = GradientTexture2D.FILL_RADIAL
	t.fill_from = Vector2(0.5, 0.5); t.fill_to = Vector2(1.0, 0.5); t.width = 64; t.height = 64
	_soft = t
	return t

static func add_mat(col: Color, soft := true, billboard := false) -> StandardMaterial3D:
	var key := "%s%s%s" % [col.to_html(), soft, billboard]
	if _mats.has(key): return _mats[key]
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.albedo_color = col
	m.vertex_color_use_as_albedo = true
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.no_depth_test = false
	if soft: m.albedo_texture = soft_tex()
	if billboard:
		m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	_mats[key] = m
	return m

static func smoke_mat() -> StandardMaterial3D:
	if _mats.has("smoke"): return _mats["smoke"]
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = soft_tex()
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	_mats["smoke"] = m
	return m

static func quad(size: float) -> QuadMesh:
	var k := "q%.2f" % size
	if not _meshes.has(k):
		var q := QuadMesh.new(); q.size = Vector2(size, size); _meshes[k] = q
	return _meshes[k]

static func root() -> Node:
	return G.level if G.level else G.main

static func beam(from: Vector3, to: Vector3, col := Color(0.25, 1.0, 0.85), width := 0.035) -> void:
	var len := from.distance_to(to)
	if len < 0.05: return
	var n := Node3D.new()
	root().add_child(n)
	n.global_position = (from + to) * 0.5
	var dir := (to - from).normalized()
	var up := Vector3.UP if abs(dir.y) < 0.98 else Vector3.RIGHT
	n.look_at(to, up)
	for i in 2:
		var mi := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = width * (2.6 if i == 0 else 0.7); cm.bottom_radius = cm.top_radius
		cm.height = len; cm.radial_segments = 6; cm.rings = 1
		mi.mesh = cm
		mi.rotation.x = PI / 2
		mi.material_override = add_mat(col if i == 0 else Color(1, 1, 1), false)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		n.add_child(mi)
	var tw := n.create_tween()
	tw.tween_property(n, "scale", Vector3(0.1, 0.1, 1.0), 0.09)
	tw.tween_callback(n.queue_free)

static func particles(pos: Vector3, amount: int, col: Color, life := 0.4, speed := 5.0, size := 0.08, gravity := -9.0, spread := 180.0, dir := Vector3.UP, smoke := false) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	root().add_child(p)
	p.global_position = pos
	p.one_shot = true
	p.explosiveness = 0.95
	p.amount = amount
	p.lifetime = life
	p.mesh = quad(size)
	p.material_override = smoke_mat() if smoke else add_mat(col, true, true)
	p.direction = dir
	p.spread = spread
	p.initial_velocity_min = speed * 0.4
	p.initial_velocity_max = speed
	p.gravity = Vector3(0, gravity, 0)
	p.scale_amount_min = 0.6; p.scale_amount_max = 1.4
	var g := Gradient.new()
	g.set_color(0, col); g.set_color(1, Color(col.r, col.g, col.b, 0))
	p.color_ramp = g
	p.emitting = true
	var t := p.get_tree().create_timer(life + 0.3)
	t.timeout.connect(p.queue_free)
	return p

static func sparks(pos: Vector3, normal := Vector3.UP, col := Color(0.4, 1.0, 0.9), n := 14) -> void:
	particles(pos, n, col, 0.35, 6.0, 0.07, -12.0, 70.0, normal)

static func smoke(pos: Vector3, n := 8, col := Color(0.35, 0.33, 0.3, 0.6), size := 0.9) -> void:
	var p := particles(pos, n, col, 1.4, 1.2, size, 0.8, 60.0, Vector3.UP, true)
	p.explosiveness = 0.6

static func explosion(pos: Vector3, big := 1.0) -> void:
	particles(pos, int(30 * big), Color(1.0, 0.6, 0.15), 0.6, 10.0 * big, 0.5 * big, -4.0)
	particles(pos, int(20 * big), Color(1.0, 0.9, 0.5), 0.3, 6.0 * big, 0.3 * big, 0.0)
	smoke(pos + Vector3(0, 0.5, 0), int(10 * big), Color(0.2, 0.18, 0.16, 0.7), 2.0 * big)
	light_pulse(pos, Color(1.0, 0.6, 0.2), 6.0, 0.5, 14.0 * big)
	Audio.sfx3("explosion", pos, 2.0)
	if G.player: G.player.shake(clamp(1.2 - G.player.global_position.distance_to(pos) / 40.0, 0.0, 1.0) * big)

static func light_pulse(pos: Vector3, col: Color, energy: float, dur: float, rng := 6.0) -> void:
	var l := OmniLight3D.new()
	root().add_child(l)
	l.global_position = pos
	l.light_color = col; l.light_energy = energy; l.omni_range = rng
	l.shadow_enabled = false
	var tw := l.create_tween()
	tw.tween_property(l, "light_energy", 0.0, dur)
	tw.tween_callback(l.queue_free)

## persistent fire (returns the node). light: adds a flickering OmniLight.
static func fire(parent: Node, pos: Vector3, scale := 1.0, light := true) -> Node3D:
	var n := Node3D.new()
	n.set_script(preload("res://scripts/fire.gd"))
	parent.add_child(n)
	n.global_position = pos
	n.setup(scale, light)
	return n

static func stars(target: Node3D, h := 2.0) -> Node3D:
	var n := Node3D.new()
	target.add_child(n)
	n.position = Vector3(0, h, 0)
	for i in 4:
		var mi := MeshInstance3D.new()
		var sm := PrismMesh.new(); sm.size = Vector3(0.14, 0.14, 0.04)
		mi.mesh = sm
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.albedo_color = Color(1.0, 0.9, 0.3)
		mi.material_override = m
		mi.position = Vector3(cos(i * TAU / 4) * 0.35, 0, sin(i * TAU / 4) * 0.35)
		n.add_child(mi)
	var tw := n.create_tween().set_loops()
	tw.tween_property(n, "rotation:y", TAU, 1.2).from(0.0)
	return n

static func text3d(pos: Vector3, txt: String, col := Color.WHITE, size := 48) -> void:
	var l := Label3D.new()
	root().add_child(l)
	l.global_position = pos
	l.text = txt; l.modulate = col; l.font_size = size; l.outline_size = 10
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.pixel_size = 0.006
	var tw := l.create_tween()
	tw.tween_property(l, "global_position", pos + Vector3(0, 1.0, 0), 0.9)
	tw.parallel().tween_property(l, "modulate:a", 0.0, 0.9).set_delay(0.3)
	tw.tween_callback(l.queue_free)
