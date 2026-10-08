class_name Projectile
extends Area3D
## Thrown/shot things: cabbages, arrows, pots, trebuchet fireballs. They can be shot out of the air.

var kind := "cabbage"
var vel := Vector3.ZERO
var grav := 18.0
var dmg := 8.0
var life := 6.0
var mesh: Node3D
var owner_node: Node
var spin := Vector3.ZERO

func launch(k: String, from: Vector3, target: Vector3, damage: float, who: Node = null) -> void:
	kind = k; dmg = damage; owner_node = who
	collision_layer = 16
	collision_mask = 0
	monitoring = false
	var cs := CollisionShape3D.new(); var s := SphereShape3D.new(); s.radius = 0.35; cs.shape = s; add_child(cs)
	global_position = from
	match k:
		"arrow":
			mesh = Actor.prop("P-arrow"); grav = 4.0
			var t := from.distance_to(target) / 30.0
			vel = (target - from) / t + Vector3(0, 0.5 * grav * t, 0)
		"fireball":
			mesh = Actor.prop("P-fireball"); grav = 9.0
			FX.fire(self, from, 1.2, true)
			vel = Vector3.ZERO
		_:
			mesh = Actor.prop("P-cabbage" if k == "cabbage" else "P-pot"); grav = 16.0
			var flat := Vector3(target.x - from.x, 0, target.z - from.z)
			var t: float = clamp(flat.length() / 13.0, 0.45, 1.4)
			vel = flat / t
			vel.y = (target.y - from.y + 0.5 * grav * t * t) / t
			spin = Vector3(randf_range(-8, 8), randf_range(-8, 8), 0)
	add_child(mesh)

func _physics_process(dt: float) -> void:
	life -= dt
	if life <= 0.0: queue_free(); return
	vel.y -= grav * dt
	var from := global_position
	var to := from + vel * dt
	var q := PhysicsRayQueryParameters3D.create(from, to, 1 | 2 | 8)
	if owner_node and owner_node is CollisionObject3D: q.exclude = [owner_node.get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(q)
	if hit:
		_impact(hit.position, hit.collider)
		return
	global_position = to
	if kind == "arrow":
		if vel.length() > 0.1: mesh.look_at(global_position + vel, Vector3.UP); mesh.rotate_object_local(Vector3.RIGHT, -PI / 2)
	else:
		mesh.rotation += spin * dt
	# near-miss forgiveness: also hit the player capsule if very close
	if G.player and kind != "fireball":
		var pc := G.player.global_position + Vector3(0, 0.9, 0)
		if pc.distance_to(global_position) < 0.55: _impact(global_position, G.player)

func _impact(pos: Vector3, col: Object) -> void:
	if col is Player:
		col.damage(dmg, pos - vel.normalized())
	match kind:
		"cabbage":
			FX.particles(pos, 14, Color(0.5, 0.8, 0.3), 0.5, 4.0, 0.12, -10.0); Audio.sfx3("splat", pos, -2)
		"pot":
			FX.particles(pos, 12, Color(0.6, 0.4, 0.3), 0.5, 4.0, 0.1, -12.0); Audio.sfx3("pot_smash", pos, -2)
		"arrow":
			FX.sparks(pos, -vel.normalized(), Color(1.0, 0.8, 0.5), 5); Audio.sfx3("arrow_hit", pos, -6)
			if not (col is Player):
				var stuck := Actor.prop("P-arrow")
				get_parent().add_child(stuck)
				stuck.global_transform = mesh.global_transform
				stuck.global_position = pos
				get_tree().create_timer(8.0).timeout.connect(stuck.queue_free)
		"fireball":
			FX.explosion(pos, 1.6)
	queue_free()

func laser_hit(_dmg: float, pos: Vector3, _dir: Vector3, _n: Vector3) -> String:
	if kind == "fireball": return "none"
	FX.particles(pos, 10, Color(0.5, 1.0, 0.9), 0.3, 4.0, 0.1, -8.0)
	_impact(pos, null)
	return "hit"
