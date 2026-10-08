class_name Boss
extends Enemy
## Ser Bruno, the Iron Bell. Mirror-polished breastplate reflects lasers: hit him in the back,
## after a ground slam, or ring the great bell above him to daze him.

signal defeated_boss
var max_hp := 420.0
var daze := 0.0
var reflect_lines := 0
var phase2 := false
var center := Vector3.ZERO
var mode := "walk"
var mode_t := 0.0
var active := false

func _ready() -> void:
	kind = "bruno"
	st = {"model": "bruno", "hp": 420, "speed": 3.0, "dmg": 20, "range": 2.8, "atk": "swing", "tele": 0.6, "cd": 1.4, "aggro": 40, "bark": "knight"}
	hp = max_hp
	add_to_group("enemies")
	collision_layer = 4
	collision_mask = 1 | 2
	var cs := CollisionShape3D.new(); var cap := CapsuleShape3D.new(); cap.radius = 0.6; cap.height = 2.3
	cs.shape = cap; cs.position.y = 1.15; add_child(cs)
	actor = Actor.make("bruno"); add_child(actor)
	actor.scale = Vector3.ONE * 1.15
	actor.attach("P-sword", "hand_R", Enemy.GRIP["P-sword"][0], Enemy.GRIP["P-sword"][1], 1.5)
	actor.attach("P-shield", "forearm_L", Vector3(0.08, 0.15, 0.0), Vector3(0, 90, 0), 1.3)
	global_position = home
	face = home_yaw
	actor.play("eidle")

func is_hostile() -> bool:
	return active and state != "down"

func _physics_process(dt: float) -> void:
	if G.paused: return
	player = G.player
	if state == "down" or not active or scripted:
		velocity = Vector3(0, -5, 0); move_and_slide(); actor.rotation.y = face; return
	mode_t += dt; daze -= dt
	var to := player.global_position - global_position; to.y = 0
	var dist := to.length()
	var mv := Vector3.ZERO
	if daze > 0.0:
		actor.play("dizzy", 0.2)
	else:
		match mode:
			"walk":
				face = G.damp_angle(face, atan2(-to.x, -to.z), 4.0 if not phase2 else 6.0, dt)
				mv = to.normalized() * (st["speed"] * (1.3 if phase2 else 1.0))
				actor.play("ewalk", 0.2, 0.8)
				if dist < 2.8 and mode_t > 0.4: _mode("swing")
				elif dist < 4.5 and mode_t > 3.0: _mode("slam")
				elif dist > 7.0 and mode_t > (2.5 if phase2 else 4.0): _mode("charge_tele")
			"swing":
				face = G.damp_angle(face, atan2(-to.x, -to.z), 6.0 if mode_t < 0.5 else 0.5, dt)
				if mode_t < 0.02:
					actor.play("swing", 0.1, 0.8, true); actor.flash(Color(1, 0.5, 0.1), 0.4); Audio.sfx3("swing", global_position)
				if mode_t > 0.65 and not hit_done:
					hit_done = true
					var fwd := -actor.global_basis.z.normalized()
					if dist < 3.3 and fwd.dot(to.normalized()) > 0.2: player.damage(20, global_position)
				if mode_t > 1.3: _mode("walk")
			"slam":
				if mode_t < 0.02:
					actor.play("slam", 0.1, 0.7, true); actor.flash(Color(1, 0.4, 0.1), 0.5); Audio.sfx3("swing", global_position, 0, 0.7)
				if mode_t > 0.85 and not hit_done:
					hit_done = true
					Audio.sfx3("slam", global_position, 2); Audio.sfx3("bell", global_position, -8, 0.6)
					FX.particles(global_position, 30, Color(0.8, 0.7, 0.5), 0.7, 8.0, 0.4, -8.0, 80.0, Vector3.UP, true)
					player.shake(0.6)
					_ring_wave()
					if dist < 5.5 and player.is_on_floor(): player.damage(18, global_position)
				if mode_t > 0.9: actor.play("dizzy", 0.2)
				if mode_t > 3.2: _mode("walk")
			"charge_tele":
				face = G.damp_angle(face, atan2(-to.x, -to.z), 8.0, dt)
				actor.play("taunt", 0.15)
				if mode_t < 0.02: actor.flash(Color(1, 0.3, 0.1), 0.6); Audio.sfx3("alert", global_position)
				if mode_t > 0.9:
					charge_dir = to.normalized(); _mode("charge")
			"charge":
				actor.play("echarge", 0.1, 1.5)
				mv = charge_dir * 12.0
				face = atan2(-charge_dir.x, -charge_dir.z)
				if dist < 2.0 and not hit_done:
					hit_done = true; player.damage(25, global_position); player.velocity += charge_dir * 10 + Vector3(0, 5, 0)
				var flat := global_position - center; flat.y = 0
				if mode_t > 1.3 or flat.length() > 8.6:
					if flat.length() > 8.6:
						Audio.sfx3("clank", global_position, 2); Audio.sfx3("bell", global_position, -6, 0.8); player.shake(0.4)
						daze = 2.5
					_mode("walk")
	velocity.x = mv.x + knock.x; velocity.z = mv.z + knock.z
	knock = knock.move_toward(Vector3.ZERO, 30 * dt)
	velocity.y = -2.0 if is_on_floor() else velocity.y - 22 * dt
	move_and_slide()
	# stay on the terrace
	var off := global_position - center; off.y = 0
	if off.length() > 8.8: global_position -= off.normalized() * (off.length() - 8.8)
	# keep out of the opening where the ledge arrives (south-west arc of the terrace)
	off = global_position - center; off.y = 0
	var ang := rad_to_deg(atan2(-off.z, off.x))
	if ang < 0.0: ang += 360.0
	if ang > 150.0 and ang < 300.0 and off.length() > 4.6 and off.length() < 8.9:
		global_position = center + off.normalized() * 4.6 + Vector3(0, global_position.y - center.y, 0)
	actor.rotation.y = face

func _mode(m: String) -> void:
	mode = m; mode_t = 0.0; hit_done = false

func _ring_wave() -> void:
	var ring := MeshInstance3D.new(); var tm := TorusMesh.new(); tm.inner_radius = 0.9; tm.outer_radius = 1.0
	ring.mesh = tm; ring.material_override = FX.add_mat(Color(1.0, 0.7, 0.3), false)
	get_parent().add_child(ring); ring.global_position = global_position + Vector3(0, 0.2, 0)
	var tw := ring.create_tween(); tw.tween_property(ring, "scale", Vector3(5.5, 1, 5.5), 0.35); tw.tween_callback(ring.queue_free)

func dazed() -> bool:
	return daze > 0.0 or (mode == "slam" and mode_t > 0.85)

func bell_hit() -> void:
	daze = 4.5
	_mode("walk")
	var s := FX.stars(self, 2.9)
	get_tree().create_timer(4.5).timeout.connect(s.queue_free)
	G.level.bark("bk_bell")

func laser_hit(dmg: float, pos: Vector3, dir: Vector3, n: Vector3) -> String:
	if state == "down" or not active: return "none"
	var fwd := -actor.global_basis.z.normalized()   # the actor is scaled
	var front := fwd.dot(-dir) > 0.15
	if front and not dazed():
		# reflect!
		var refl := dir.bounce(fwd).normalized() if fwd.length() > 0 else -dir
		refl = (refl + Vector3(randf_range(-0.3, 0.3), randf_range(0.0, 0.4), randf_range(-0.3, 0.3))).normalized()
		FX.beam(pos, pos + refl * 12.0, Color(1.0, 0.8, 0.3), 0.03)
		FX.sparks(pos, -dir, Color(1.0, 0.85, 0.4), 8)
		Audio.sfx3("ting", pos, -4, randf_range(0.9, 1.2))
		reflect_lines += 1
		if reflect_lines == 4 or reflect_lines == 25: G.level.bark("bk_reflect")
		return "block"
	var mult := 1.6 if dazed() else 1.0
	hp -= dmg * mult
	actor.flash()
	FX.sparks(pos, -dir, Color(0.6, 1.0, 0.95), 12)
	Audio.sfx3("hit_enemy", pos, -2, 0.8)
	G.ui.boss(true, hp / max_hp)
	if not phase2 and hp < max_hp * 0.5:
		phase2 = true
		G.level.bark("c12")
	if not front and reflect_lines > 0 and randf() < 0.05: G.level.bark("bk_back")
	if hp <= 0.0:
		hp = 0; state = "down"; active = false
		actor.play("down", 0.1)
		defeated_boss.emit()
		return "ko"
	return "hit"

func pulse_hit(from: Vector3) -> void:
	var d := global_position - from; d.y = 0
	knock += d.normalized() * 3.0
	if not active or state == "down": return
	hp = max(1.0, hp - 10)
	G.ui.boss(true, hp / max_hp)
