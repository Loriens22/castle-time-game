class_name Player
extends CharacterBody3D
## Juno: third-person laser-blaster controller.

signal died

const SPEED := 6.6
const AIM_SPEED := 4.6
const GRAV := 22.0
const JUMP := 9.0
const ROLL_SPEED := 11.0
const ROLL_TIME := 0.45
const FIRE_RATE := 7.5
const HEAT_PER_SHOT := 8.0
const COOL_RATE := 42.0
const PULSE_CD := 6.0
const PULSE_R := 5.5
const L_WORLD := 1
const L_PLAYER := 2
const L_ENEMY := 4
const L_PROP := 8
const L_SHOOT := 16

var actor: Actor
var blaster: Node3D
var muzzle: Node3D
var cam_root: Node3D
var cam_pitch: Node3D
var spring: SpringArm3D
var cam: Camera3D
var col: CollisionShape3D
var capsule: CapsuleShape3D

var yaw := 0.0
var pitch := -0.12
var hp := 100.0
var max_hp := 100.0
var heat := 0.0
var overheated := 0.0
var pulse_cd := 0.0
var fire_cd := 0.0
var fire_buf := 0.0   # remembers a quick click/tap so it is never lost between physics frames
var since_fire := 9.0
var since_hurt := 9.0
var invuln := 0.0
var roll_t := 0.0
var roll_dir := Vector3.ZERO
var coyote := 0.0
var jump_buf := 0.0
var air_time := 0.0
var fall_start_y := 0.0
var step_t := 0.0
var input_locked := false
var weapon := true
var dead := false
var aiming := false
var trauma := 0.0
var shake_t := 0.0
var face_yaw := 0.0
var interact_target: Node3D = null
var interact_scan := 0.0
var zipping := false
var touch_move := Vector2.ZERO
var touch_look := Vector2.ZERO
var touch_fire := false
var touch_aim := false
var shot_count := 0
var cam_dist := 3.0
var crouch_blocked := false
var hurt_bark_t := 0.0
var auto_move := Vector3.ZERO   # used by tests / cutscenes

func _ready() -> void:
	G.player = self
	collision_layer = L_PLAYER
	collision_mask = L_WORLD | L_ENEMY | L_PROP
	floor_snap_length = 0.35
	floor_max_angle = deg_to_rad(50)
	safe_margin = 0.02
	capsule = CapsuleShape3D.new(); capsule.radius = 0.35; capsule.height = 1.75
	col = CollisionShape3D.new(); col.shape = capsule; col.position.y = 0.875
	add_child(col)
	actor = Actor.make("juno")
	add_child(actor)
	if weapon: equip(true)
	# camera rig (top level so it can be smoothed independently)
	cam_root = Node3D.new(); cam_root.top_level = true; add_child(cam_root)
	cam_pitch = Node3D.new(); cam_root.add_child(cam_pitch)
	spring = SpringArm3D.new(); spring.spring_length = 3.0; spring.collision_mask = L_WORLD
	var sph := SphereShape3D.new(); sph.radius = 0.22; spring.shape = sph; spring.margin = 0.05
	spring.add_excluded_object(get_rid())
	cam_pitch.add_child(spring)
	cam = Camera3D.new(); cam.fov = 72; cam.near = 0.08; cam.far = 600.0
	spring.add_child(cam)
	cam_root.global_position = global_position + Vector3(0, 1.55, 0)
	face_yaw = rotation.y; yaw = rotation.y; rotation.y = 0
	actor.rotation.y = face_yaw
	cam.current = true

func equip(on: bool) -> void:
	weapon = on
	if on and blaster == null:
		blaster = actor.attach("P-blaster", "hand_R", Vector3(0.0, 0.09, 0.03), Vector3(-90, 180, 0), 1.0)
		muzzle = Node3D.new(); blaster.add_child(muzzle)
		muzzle.position = Vector3(0, 0.1, 0.46)
	elif not on and blaster:
		actor.detach("P-blaster"); blaster = null; muzzle = null

func set_view(y: float, p := -0.12) -> void:
	yaw = y; pitch = p; face_yaw = y
	actor.rotation.y = y
	cam_root.global_position = global_position + Vector3(0, 1.55, 0)

func teleport(pos: Vector3, y := INF) -> void:
	global_position = pos
	velocity = Vector3.ZERO
	if y != INF: set_view(y)
	cam_root.global_position = pos + Vector3(0, 1.55, 0)
	fall_start_y = pos.y; air_time = 0.0

# ------------------------------------------------------------------ input
func _unhandled_input(e: InputEvent) -> void:
	if input_locked or G.paused: return
	if e.is_action_pressed("fire"): fire_buf = 0.25
	if e is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		var s: float = 0.0022 * G.settings["sens"]
		yaw -= e.relative.x * s
		pitch -= e.relative.y * s * (-1.0 if G.settings["invert"] else 1.0)
		pitch = clamp(pitch, -1.25, 0.95)
	elif e is InputEventMouseButton and e.pressed and e.device != -1 and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED and not G.is_touch:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func move_input() -> Vector2:
	var v := Input.get_vector("move_left", "move_right", "move_fwd", "move_back")
	if touch_move.length() > 0.05: v = touch_move
	return v.limit_length(1.0)

func _process(dt: float) -> void:
	# look (gamepad right stick + touch drags)
	if not input_locked and not G.paused:
		var look := Input.get_vector("look_left", "look_right", "look_up", "look_down")
		var s: float = G.settings["sens"]
		yaw -= look.x * 2.6 * dt * s
		pitch -= look.y * 1.8 * dt * s * (-1.0 if G.settings["invert"] else 1.0)
		if touch_look != Vector2.ZERO:
			yaw -= touch_look.x * 0.0045 * s
			pitch -= touch_look.y * 0.0045 * s * (-1.0 if G.settings["invert"] else 1.0)
			touch_look = Vector2.ZERO
		pitch = clamp(pitch, -1.25, 0.95)
	# camera follow
	var target := global_position + Vector3(0, 1.55 if roll_t <= 0 else 1.1, 0)
	var cp := cam_root.global_position
	cp.x = G.damp(cp.x, target.x, 30.0, dt); cp.z = G.damp(cp.z, target.z, 30.0, dt)
	cp.y = G.damp(cp.y, target.y, 12.0, dt)
	cam_root.global_position = cp
	cam_root.rotation.y = yaw
	cam_pitch.rotation.x = pitch
	var want_dist := 2.5 if aiming else 3.2
	cam_dist = G.damp(cam_dist, want_dist, 10.0, dt)
	spring.spring_length = cam_dist
	spring.position = Vector3(0.62 if weapon else 0.35, 0.0, 0.0)
	cam.fov = G.damp(cam.fov, 62.0 if aiming else 72.0, 10.0, dt)
	# shake
	trauma = max(0.0, trauma - dt * 1.6)
	shake_t += dt * 30.0
	var sh := trauma * trauma
	cam.h_offset = sin(shake_t * 1.3) * 0.18 * sh
	cam.v_offset = sin(shake_t * 1.7 + 2.0) * 0.14 * sh
	cam.rotation.z = sin(shake_t * 0.9) * 0.04 * sh
	# interact prompt
	interact_scan -= dt
	if interact_scan <= 0.0:
		interact_scan = 0.1
		_scan_interact()

func shake(amount: float) -> void:
	trauma = clamp(trauma + amount, 0.0, 1.0)

func _scan_interact() -> void:
	var best: Node3D = null
	var bd := 2.4
	if not input_locked and not dead:
		var fwd := -cam_root.global_basis.z
		for n in get_tree().get_nodes_in_group("interact"):
			if not n.get("enabled"): continue
			var d: float = n.global_position.distance_to(global_position + Vector3(0, 1.0, 0))
			var r: float = n.get("radius") if n.get("radius") else 2.4
			if d > r: continue
			var to: Vector3 = n.global_position - global_position; to.y = 0
			var facing := fwd.dot(to.normalized()) if to.length() > 0.3 else 1.0
			var score := d - facing * 0.8
			if score < bd: bd = score; best = n
	interact_target = best
	if G.ui: G.ui.set_prompt(best.prompt if best else "")

func do_interact() -> void:
	if interact_target and is_instance_valid(interact_target) and not input_locked:
		interact_target.interact(self)

# ------------------------------------------------------------------ physics
func _physics_process(dt: float) -> void:
	if G.paused: return
	since_fire += dt; since_hurt += dt; invuln -= dt; pulse_cd = max(0.0, pulse_cd - dt); fire_cd -= dt; hurt_bark_t -= dt
	# heat
	if overheated > 0.0:
		overheated -= dt
		heat = max(0.0, heat - COOL_RATE * 0.9 * dt)
		if overheated <= 0.0: heat = 0.0; Audio.sfx("vent_done", -6)
	elif since_fire > 0.25:
		heat = max(0.0, heat - COOL_RATE * dt)
	# regen (partial)
	if since_hurt > 4.0 and hp < 60.0 and not dead:
		hp = min(60.0, hp + 7.0 * dt)
	if zipping: return
	var mv := Vector2.ZERO if (input_locked or dead) else move_input()
	var fwd := -cam_root.global_basis.z; fwd.y = 0; fwd = fwd.normalized()
	var right := cam_root.global_basis.x; right.y = 0; right = right.normalized()
	var wish := (right * mv.x - fwd * mv.y)
	if auto_move != Vector3.ZERO: wish = auto_move
	aiming = weapon and not input_locked and not dead and (Input.is_action_pressed("aim") or Input.is_action_pressed("fire") or touch_fire or touch_aim or since_fire < 0.7)
	var spd := AIM_SPEED if aiming else SPEED
	if Input.is_action_pressed("walk"): spd = 2.6
	var on_floor := is_on_floor()
	if on_floor:
		coyote = 0.12
		if air_time > 0.35:
			Audio.sfx("land", -10)
			if fall_start_y - global_position.y > 2.5: shake(0.15)
		air_time = 0.0; fall_start_y = global_position.y
	else:
		coyote -= dt; air_time += dt
		fall_start_y = max(fall_start_y, global_position.y)
	# fell too far (off the spire, into a pit) -> respawn instead of a long fall
	if not dead and (fall_start_y - global_position.y > 14.0 or global_position.y < -40.0):
		fall_start_y = global_position.y
		if G.level and G.level.has_method("on_fall"): G.level.on_fall()
		return
	jump_buf -= dt
	if not input_locked and not dead and Input.is_action_just_pressed("jump"): jump_buf = 0.13
	if not input_locked and not dead and Input.is_action_just_pressed("roll"): try_roll(wish)
	# roll
	if roll_t > 0.0:
		roll_t -= dt
		velocity.x = roll_dir.x * ROLL_SPEED * (0.55 + 0.45 * roll_t / ROLL_TIME)
		velocity.z = roll_dir.z * ROLL_SPEED * (0.55 + 0.45 * roll_t / ROLL_TIME)
		if roll_t <= 0.0:
			if _ceiling_blocked(): roll_t = 0.12   # keep crouched under low gaps (portcullis)
			else: _set_crouch(false)
	else:
		var acc := 16.0 if on_floor else 5.0
		var tv := wish * spd
		velocity.x = move_toward(velocity.x, tv.x, acc * spd * dt)
		velocity.z = move_toward(velocity.z, tv.z, acc * spd * dt)
	if not on_floor: velocity.y -= GRAV * dt
	if jump_buf > 0.0 and coyote > 0.0 and roll_t <= 0.0:
		velocity.y = JUMP; jump_buf = 0.0; coyote = 0.0
		Audio.sfx("jump", -8, randf_range(0.95, 1.05))
	if velocity.y > 0 and not Input.is_action_pressed("jump") and not G.ui.touch_jump_held and air_time > 0.08:
		velocity.y -= GRAV * dt * 1.2   # variable jump height
	if on_floor and velocity.y <= 0.01: _step_up(dt)
	move_and_slide()
	# push physics props
	for i in get_slide_collision_count():
		var c := get_slide_collision(i)
		var o := c.get_collider()
		if o is RigidBody3D:
			o.apply_central_impulse(-c.get_normal() * 0.6 * Vector3(1, 0, 1).length() + Vector3(velocity.x, 0, velocity.z) * 0.05)
		elif o is Enemy and c.get_normal().y > 0.5:
			# never stand on an enemy's head (they can't hit you, you can't shoot them: an endless stalemate) - slide off
			var away := global_position - (o as Node3D).global_position; away.y = 0
			if away.length() < 0.05: away = Vector3(sin(yaw), 0, cos(yaw))
			var push := away.normalized() * 4.5
			velocity.x = push.x; velocity.z = push.z; velocity.y = maxf(velocity.y, 1.5)
	# facing
	var hv := Vector3(velocity.x, 0, velocity.z)
	if aiming and roll_t <= 0.0:
		face_yaw = G.damp_angle(face_yaw, yaw, 18.0, dt)
	elif hv.length() > 0.5:
		face_yaw = G.damp_angle(face_yaw, atan2(-hv.x, -hv.z), 12.0, dt)
	actor.rotation.y = face_yaw
	_animate(hv, on_floor, mv)
	# footsteps
	if on_floor and hv.length() > 1.0 and roll_t <= 0.0:
		step_t -= dt * hv.length() / 2.6
		if step_t <= 0.0:
			step_t = 0.55
			var surf: String = G.level.surface_at(global_position) if G.level and G.level.has_method("surface_at") else "stone"
			Audio.sfx("step_" + surf, -14.0, randf_range(0.9, 1.1))
	# combat
	if weapon and not input_locked and not dead:
		fire_buf = maxf(0.0, fire_buf - get_physics_process_delta_time())
		if Input.is_action_pressed("fire") or touch_fire: try_fire()
		elif fire_buf > 0.0 and fire_cd <= 0.0: fire_buf = 0.0; try_fire()
		if Input.is_action_just_pressed("pulse"): try_pulse()
	if not input_locked and Input.is_action_just_pressed("interact"): do_interact()

func _animate(hv: Vector3, on_floor: bool, mv: Vector2) -> void:
	var sp := hv.length()
	if roll_t > 0.0: actor.play("roll", 0.05, 1.3); return
	if dead: return
	if not on_floor and air_time > 0.08:
		actor.play("jump" if velocity.y > 0 else "fall", 0.15); return
	if input_locked and actor.cur in ["phone", "type", "talk", "wave", "nod", "shrug", "point", "think", "pickup", "cheer", "sit", "handsup", "kneel", "crouch", "lookaround", "sad", "excited"]:
		return
	if aiming:
		if sp < 0.4: actor.play("aim", 0.12); return
		var local := hv.rotated(Vector3.UP, -face_yaw)
		var a := atan2(local.x, -local.z)
		if abs(a) < 0.8: actor.play("runaim" if sp > 4.0 else "walkaim", 0.15, sp / 4.6)
		elif abs(a) > 2.3: actor.play("backaim", 0.15, sp / 4.0)
		elif a > 0: actor.play("strafeR", 0.15, sp / 4.0)
		else: actor.play("strafeL", 0.15, sp / 4.0)
		return
	if sp > 3.6: actor.play("run", 0.15, sp / 6.6)
	elif sp > 0.4: actor.play("walk", 0.15, sp / 2.6)
	else: actor.play("hold" if weapon else "idle", 0.2)

func try_roll(wish: Vector3) -> void:
	if roll_t > 0.0 or not is_on_floor(): return
	roll_dir = wish.normalized() if wish.length() > 0.1 else Vector3(-sin(face_yaw), 0, -cos(face_yaw))
	face_yaw = atan2(-roll_dir.x, -roll_dir.z)
	roll_t = ROLL_TIME
	invuln = ROLL_TIME + 0.05
	_set_crouch(true)
	Audio.sfx("roll", -6)

func _set_crouch(on: bool) -> void:
	capsule.height = 0.8 if on else 1.75
	capsule.radius = 0.35
	col.position.y = capsule.height * 0.5

func _ceiling_blocked() -> bool:
	var q := PhysicsShapeQueryParameters3D.new()
	var s := CapsuleShape3D.new(); s.radius = 0.33; s.height = 1.7
	q.shape = s
	q.transform = Transform3D(Basis(), global_position + Vector3(0, 0.9, 0))
	q.collision_mask = L_WORLD
	q.exclude = [get_rid()]
	return get_world_3d().direct_space_state.intersect_shape(q, 1).size() > 0

# ------------------------------------------------------------------ shooting
func muzzle_pos() -> Vector3:
	return muzzle.global_position if muzzle else global_position + Vector3(0, 1.3, 0)

func try_fire() -> void:
	if fire_cd > 0.0 or roll_t > 0.0: return
	if overheated > 0.0:
		return
	fire_cd = 1.0 / FIRE_RATE
	since_fire = 0.0
	shot_count += 1
	var space := get_world_3d().direct_space_state
	var origin := cam.global_position
	var dir := -cam.global_basis.z
	# start the ray at the player's depth so walls behind the player don't block it
	var start: Vector3 = origin + dir * maxf(0.0, (global_position + Vector3(0, 1.3, 0) - origin).dot(dir) - 0.3)
	if G.is_touch: dir = _aim_assist(origin, dir)
	var q := PhysicsRayQueryParameters3D.create(start, start + dir * 140.0, L_WORLD | L_ENEMY | L_PROP | L_SHOOT, [get_rid()])
	q.collide_with_areas = true
	var hit := space.intersect_ray(q)
	var target: Vector3 = hit.position if hit else start + dir * 140.0
	var mz := muzzle_pos()
	# make sure nothing blocks between the muzzle and the target point
	var q2 := PhysicsRayQueryParameters3D.create(mz, target + (target - mz).normalized() * 0.05, L_WORLD | L_ENEMY | L_PROP | L_SHOOT, [get_rid()])
	q2.collide_with_areas = true
	var hit2 := space.intersect_ray(q2)
	if hit2 and hit2.position.distance_to(target) > 0.4: hit = hit2; target = hit2.position
	FX.beam(mz, target)
	FX.particles(mz, 4, Color(0.5, 1.0, 0.9), 0.12, 2.0, 0.12, 0.0)
	Audio.sfx(["laser", "laser2", "laser3"][shot_count % 3], -7.0, randf_range(0.96, 1.05))
	shake(0.06)
	pitch = min(0.95, pitch + 0.006)
	heat += HEAT_PER_SHOT
	if heat >= 100.0:
		heat = 100.0; overheated = 1.6
		Audio.sfx("overheat", -2)
		FX.smoke(mz, 6, Color(0.9, 0.9, 0.9, 0.5), 0.4)
		if randf() < 0.6: G.level.bark("bk_heat%d" % (randi() % 2))
	if hit:
		var c: Object = hit.collider
		var n: Vector3 = hit.normal
		if c and c.has_method("laser_hit"):
			var r = c.laser_hit(10.0, target, dir, n)
			if G.ui: G.ui.hitmark(r if r is String else "hit")
		else:
			FX.sparks(target, n, Color(0.5, 1.0, 0.9), 8)
			if c is RigidBody3D:
				c.apply_impulse(dir * 2.5, target - c.global_position)
				if c.has_method("laser_hit"): pass

func _aim_assist(origin: Vector3, dir: Vector3) -> Vector3:
	var best := dir
	var best_a := 0.12
	for e in get_tree().get_nodes_in_group("enemies"):
		if not e.is_hostile(): continue
		var p: Vector3 = e.global_position + Vector3(0, 1.1, 0)
		var to := p - origin
		if to.length() > 45.0: continue
		var a := dir.angle_to(to.normalized())
		if a < best_a: best_a = a; best = to.normalized()
	return best

func try_pulse() -> void:
	if pulse_cd > 0.0: return
	pulse_cd = PULSE_CD
	Audio.sfx("pulse", -2)
	shake(0.4)
	var p := global_position + Vector3(0, 1.0, 0)
	FX.particles(p, 40, Color(0.4, 1.0, 0.9), 0.45, 12.0, 0.25, 0.0, 180.0)
	FX.light_pulse(p, Color(0.4, 1.0, 0.9), 5.0, 0.4, 9.0)
	var ring := MeshInstance3D.new()
	var tm := TorusMesh.new(); tm.inner_radius = 0.9; tm.outer_radius = 1.0
	ring.mesh = tm; ring.material_override = FX.add_mat(Color(0.4, 1.0, 0.9), false)
	get_parent().add_child(ring); ring.global_position = global_position + Vector3(0, 0.3, 0)
	var tw := ring.create_tween()
	tw.tween_property(ring, "scale", Vector3.ONE * PULSE_R, 0.35)
	tw.parallel().tween_property(ring, "transparency", 1.0, 0.35)
	tw.tween_callback(ring.queue_free)
	if randf() < 0.5: G.level.bark("bk_pulse%d" % (randi() % 2))
	for e in get_tree().get_nodes_in_group("enemies"):
		if e.global_position.distance_to(global_position) < PULSE_R and e.has_method("pulse_hit"): e.pulse_hit(global_position)
	for b in get_tree().get_nodes_in_group("physprops"):
		var d: Vector3 = b.global_position - global_position
		if d.length() < PULSE_R: b.apply_central_impulse((d.normalized() + Vector3(0, 0.6, 0)) * 6.0 * b.mass)
	for a in get_tree().get_nodes_in_group("animals"):
		if a.global_position.distance_to(global_position) < PULSE_R * 1.5: a.scare(global_position)

# ------------------------------------------------------------------ health
func damage(amount: float, from := Vector3.ZERO) -> void:
	if dead or invuln > 0.0 or input_locked: return
	if G.trace: G.tlog("hurt %d hp=%d from %s at %s" % [amount, hp, str(from.snapped(Vector3.ONE * 0.1)), str(global_position.snapped(Vector3.ONE * 0.1))])
	hp -= amount
	since_hurt = 0.0
	invuln = 0.25
	shake(0.35)
	actor.flash(Color(1, 0.2, 0.2), 0.6)
	Audio.sfx("hurt", -4, randf_range(0.95, 1.05))
	if G.ui: G.ui.hurt(from)
	if hurt_bark_t <= 0.0 and randf() < 0.35:
		hurt_bark_t = 8.0; G.level.bark("bk_hurt%d" % (randi() % 4))
	if hp <= 0.0: die()

func heal(amount: float) -> void:
	hp = min(max_hp, hp + amount)

func die() -> void:
	if dead: return
	dead = true
	hp = 0
	G.save["deaths"] += 1
	actor.play("down", 0.1)
	Audio.sfx("death")
	Engine.time_scale = 0.45
	await get_tree().create_timer(0.6, true, false, true).timeout
	Engine.time_scale = 1.0
	died.emit()

func revive() -> void:
	dead = false; hp = max_hp; heat = 0; overheated = 0; roll_t = 0; _set_crouch(false)
	invuln = 2.5; velocity = Vector3.ZERO
	actor.play("idle", 0.0)

# ------------------------------------------------------------------ zipline
func zip(a: Vector3, b: Vector3) -> void:
	zipping = true
	input_locked = true
	velocity = Vector3.ZERO
	global_position = a - Vector3(0, 1.9, 0)
	actor.play("climb", 0.1, 0.0)
	face_yaw = atan2(-(b - a).x, -(b - a).z); actor.rotation.y = face_yaw
	yaw = face_yaw
	Audio.sfx("zipline")
	var tw := create_tween()
	var t := a.distance_to(b) / 15.0
	tw.tween_method(func(v: float):
		var p := a.lerp(b, v)
		p.y -= sin(v * PI) * 2.0
		global_position = p - Vector3(0, 1.9, 0), 0.0, 1.0, t).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	await G.wait_for(tw.finished, t + 2.0)
	if tw.is_valid(): tw.kill()
	global_position = b - Vector3(0, 1.9, 0)
	zipping = false
	input_locked = false
	velocity = (b - a).normalized() * 4.0
	velocity.y = 2.0
	fall_start_y = global_position.y

## climbs small ledges (thresholds, planks, kerbs) up to STEP_H high instead of stopping dead
const STEP_H := 0.42
func _step_up(dt: float) -> void:
	var hv := Vector3(velocity.x, 0, velocity.z)
	if hv.length() < 0.5: return
	var ahead := hv.normalized() * maxf(hv.length() * dt, 0.12)
	var t := global_transform
	var col := KinematicCollision3D.new()
	if not test_move(t, ahead, col): return            # nothing in the way
	if col.get_normal().y > 0.7: return                  # it's a slope we can already walk
	if test_move(t, Vector3(0, STEP_H, 0)): return       # no headroom
	t.origin.y += STEP_H
	if test_move(t, ahead): return                       # too tall: a real wall
	t.origin += ahead
	var down := KinematicCollision3D.new()
	if test_move(t, Vector3(0, -STEP_H - 0.05, 0), down) and down.get_normal().y > 0.7:
		var rise := t.origin.y + down.get_travel().y - global_position.y
		if rise > 0.02:
			global_position = t.origin + down.get_travel() - ahead * 0.5
