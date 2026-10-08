class_name Animal
extends CharacterBody3D
## Farm animals (procedurally animated legs) and cats. Never harmed - shooting them only startles them.

var kind := "pig"
var model: Node3D
var actor: Actor
var legs: Array[Node3D] = []
var head: Node3D
var tail: Node3D
var home := Vector3.ZERO
var target := Vector3.ZERO
var wait := 0.0
var speed := 1.0
var scared := 0.0
var phase := 0.0
var face := 0.0
var radius := 5.0
var sound_t := 0.0
var follow := false

const SOUND := {"pig": "oink", "sheep": "baa", "chicken": "cluck", "cow": "moo", "horse": "neigh", "rat": "squeak", "cat": "meow"}

func setup(k: String, pos: Vector3, yaw: float) -> void:
	kind = k; home = pos; face = yaw
	position = pos
	target = pos

func _ready() -> void:
	add_to_group("animals")
	collision_layer = 8
	collision_mask = 1
	var cs := CollisionShape3D.new()
	var r := {"pig": 0.4, "sheep": 0.4, "chicken": 0.18, "cow": 0.6, "horse": 0.6, "rat": 0.1, "cat": 0.2}.get(kind, 0.3)
	var s := SphereShape3D.new(); s.radius = r; cs.shape = s; cs.position.y = r
	add_child(cs)
	if kind == "cat":
		actor = Actor.make("cat"); add_child(actor); actor.rotation.y = PI; actor.play("idle")
		speed = 1.2; radius = 3.0
	else:
		model = Actor.prop("P-" + kind)
		model.position.y = Actor.prop_xform("P-" + kind).origin.y
		add_child(model)
		for c in model.get_children():
			var n := String(c.name)
			if n.begins_with("leg"): legs.append(c)
			elif n.begins_with("head"): head = c
			elif n.begins_with("tail"): tail = c
		speed = {"pig": 1.1, "sheep": 0.9, "chicken": 1.5, "cow": 0.7, "horse": 0.8, "rat": 2.5}.get(kind, 1.0)
		radius = {"horse": 0.6, "rat": 6.0, "chicken": 4.0}.get(kind, 5.0)
	rotation.y = face
	wait = randf_range(0.5, 4.0)
	phase = randf() * TAU
	sound_t = randf_range(4, 20)

func scare(from: Vector3) -> void:
	if scared > 0.5: return
	scared = 2.5
	var away := global_position - from; away.y = 0
	target = global_position + away.normalized() * 6.0
	Audio.sfx3(SOUND.get(kind, "oink"), global_position, -2, randf_range(0.9, 1.15))

func laser_hit(_d: float, _pos: Vector3, _dir: Vector3, _n: Vector3) -> String:
	scare(G.player.global_position if G.player else global_position)
	return "none"

func _physics_process(dt: float) -> void:
	if G.paused: return
	scared -= dt
	sound_t -= dt
	if sound_t <= 0.0:
		sound_t = randf_range(8, 25)
		if G.player and G.player.global_position.distance_to(global_position) < 18.0:
			Audio.sfx3(SOUND.get(kind, "oink"), global_position, -10, randf_range(0.9, 1.1))
	var spd := speed * (3.0 if scared > 0.0 else 1.0)
	if follow and G.player:
		target = G.player.global_position + (global_position - G.player.global_position).normalized() * 2.0
	var to := target - global_position; to.y = 0
	var mv := Vector3.ZERO
	if to.length() > 0.3:
		mv = to.normalized() * spd
		face = lerp_angle(face, atan2(to.x, to.z), 1.0 - exp(-6.0 * dt))
	else:
		wait -= dt
		if wait <= 0.0 and not follow:
			wait = randf_range(2.0, 7.0)
			var a := randf() * TAU
			target = home + Vector3(cos(a), 0, sin(a)) * randf() * radius
	velocity.x = mv.x; velocity.z = mv.z
	velocity.y = -2.0 if is_on_floor() else velocity.y - 20.0 * dt
	move_and_slide()
	if is_on_wall(): target = global_position - to.normalized() * 1.5
	rotation.y = face
	# animation
	var moving := mv.length() > 0.1
	if actor:
		actor.play("walk" if moving else ("sit" if wait > 4.0 else "idle"))
	else:
		phase += dt * (8.0 + spd * 4.0) * (1.0 if moving else 0.0)
		for i in legs.size():
			legs[i].rotation.x = sin(phase + (PI if i % 2 == 0 else 0.0) + (PI * 0.5 if i >= 2 else 0.0)) * (0.5 if moving else 0.0)
		if head:
			head.rotation.x = (sin(Time.get_ticks_msec() * 0.002 + phase) * 0.15) if not moving else sin(phase * 2) * 0.05
			if kind == "chicken" and not moving: head.rotation.x = abs(sin(Time.get_ticks_msec() * 0.006)) * 0.6
		if tail: tail.rotation.z = sin(Time.get_ticks_msec() * 0.008) * 0.4
