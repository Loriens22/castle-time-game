class_name Pickup
extends Node3D
## Food (heals) and anachronism collectibles.

var kind := "apple"
var heal := 10.0
var mesh: Node3D
var t := 0.0
var collect_id := ""
var base_y := 0.0

func setup(k: String, pos: Vector3) -> void:
	kind = k
	if k.begins_with("col_"):
		collect_id = k.substr(4)
		mesh = Actor.prop("P-col_" + collect_id)
		mesh.scale = Vector3.ONE * 1.6
		var l := OmniLight3D.new(); l.light_color = Color(0.4, 1.0, 0.9); l.light_energy = 0.8; l.omni_range = 2.5
		add_child(l); l.position.y = 0.4
		var ring := MeshInstance3D.new(); var tm := TorusMesh.new(); tm.inner_radius = 0.32; tm.outer_radius = 0.36
		ring.mesh = tm; ring.material_override = FX.add_mat(Color(0.3, 1.0, 0.85, 0.8), false)
		add_child(ring)
		var beam := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 0.02; cm.bottom_radius = 0.25; cm.height = 3.0
		beam.mesh = cm; beam.material_override = FX.add_mat(Color(0.2, 0.9, 0.8, 0.25), false); beam.position.y = 1.5
		add_child(beam)
	else:
		mesh = Actor.prop("P-" + k)
		heal = {"apple": 12.0, "bread": 20.0, "roast": 40.0}.get(k, 10.0)
		mesh.scale = Vector3.ONE * 1.3
	add_child(mesh)
	position = pos
	base_y = pos.y

func _ready() -> void:
	base_y = position.y

func _process(dt: float) -> void:
	t += dt
	mesh.rotation.y += dt * 1.8
	mesh.position.y = 0.15 + sin(t * 2.5) * 0.08
	var p := G.player
	if p and not p.dead and p.global_position.distance_to(global_position) < 1.25 and not p.input_locked:
		if collect_id != "":
			if G.add_collect(collect_id):
				G.add_secret("col_" + collect_id)
				Audio.sfx("collect")
				G.ui.toast("ANACHRONISM %d / %d" % [G.save["collect"].size(), G.COLLECT_IDS.size()], Color(1.0, 0.85, 0.3))
				G.level.say_line("col_" + collect_id)
			queue_free()
		elif p.hp < p.max_hp - 1:
			p.heal(heal)
			Audio.sfx("eat", -3)
			FX.particles(global_position, 8, Color(1.0, 0.9, 0.5), 0.4, 2.0, 0.08, -4.0)
			if randf() < 0.25: G.level.bark("bk_food")
			queue_free()
