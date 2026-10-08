class_name ShootTarget
extends StaticBody3D
## A shootable static thing (chains, bell, archery targets, dummies). on_hit(target, pos) -> String.

var on_hit: Callable
var hp := 1.0
var tag := ""

static func make(parent: Node, pos: Vector3, size: Vector3, cb: Callable, t := "") -> ShootTarget:
	var s := ShootTarget.new()
	s.on_hit = cb; s.tag = t
	s.collision_layer = 16
	s.collision_mask = 0
	var cs := CollisionShape3D.new(); var b := BoxShape3D.new(); b.size = size; cs.shape = b
	s.add_child(cs)
	parent.add_child(s)
	s.global_position = pos
	return s

func laser_hit(_dmg: float, pos: Vector3, dir: Vector3, n: Vector3) -> String:
	FX.sparks(pos, n, Color(1.0, 0.85, 0.5), 8)
	if on_hit.is_valid():
		var r = on_hit.call(self, pos)
		if r is String: return r
	return "hit"
