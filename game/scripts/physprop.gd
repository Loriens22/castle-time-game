class_name PhysProp
extends RigidBody3D
## Barrels, crates, pots and cabbages. Shoot them, push them, break them.

var kind := "barrel"
var hp := 30.0

func setup(k: String) -> void:
	kind = k
	add_to_group("physprops")
	collision_layer = 8
	collision_mask = 1 | 2 | 4 | 8
	var m := Actor.prop("P-" + k)
	add_child(m)
	var cs := CollisionShape3D.new()
	match k:
		"barrel":
			var c := CylinderShape3D.new(); c.radius = 0.42; c.height = 1.0; cs.shape = c; cs.position.y = 0.5; mass = 12.0; hp = 60
		"crate":
			var b := BoxShape3D.new(); b.size = Vector3(0.8, 0.8, 0.8); cs.shape = b; cs.position.y = 0.4; mass = 8.0; hp = 30
		"pot":
			var c2 := CylinderShape3D.new(); c2.radius = 0.28; c2.height = 0.6; cs.shape = c2; cs.position.y = 0.3; mass = 3.0; hp = 1
		_:
			var s := SphereShape3D.new(); s.radius = 0.2; cs.shape = s; cs.position.y = 0.2; mass = 1.0; hp = 999
	add_child(cs)
	can_sleep = true
	sleeping = true

func laser_hit(dmg: float, pos: Vector3, dir: Vector3, n: Vector3) -> String:
	apply_impulse(dir * (3.0 + mass * 0.4), pos - global_position)
	FX.sparks(pos, n, Color(1.0, 0.8, 0.5), 6)
	hp -= dmg
	match kind:
		"barrel": Audio.sfx3("barrel_hit", pos, -6)
		"cabbage": Audio.sfx3("splat", pos, -8)
	if hp <= 0.0 and kind != "barrel":
		_break()
		return "ko"
	return "hit"

func _break() -> void:
	var p := global_position + Vector3(0, 0.3, 0)
	if kind == "crate":
		Audio.sfx3("crate_break", p)
		FX.particles(p, 18, Color(0.55, 0.4, 0.25), 0.8, 5.0, 0.18, -14.0)
		if randf() < 0.5 and G.level.has_method("spawn_pickup"): G.level.spawn_pickup(["apple", "bread"][randi() % 2], p)
	elif kind == "pot":
		Audio.sfx3("pot_smash", p)
		FX.particles(p, 14, Color(0.65, 0.4, 0.3), 0.6, 4.0, 0.12, -14.0)
		if randf() < 0.3: G.level.spawn_pickup("apple", p)
	else:
		FX.particles(p, 14, Color(0.5, 0.8, 0.3), 0.5, 4.0, 0.12, -10.0)
	queue_free()
