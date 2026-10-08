class_name Enemy
extends CharacterBody3D
## Medieval opponents. Every enemy is stunned / knocked out by the blaster - nobody gets hurt for real.

signal knocked_out(e)

const STATS := {
	"peasant": {"model": "peasant", "hp": 30, "speed": 4.3, "dmg": 9, "range": 2.0, "atk": "thrust", "tele": 0.45, "cd": 1.3, "weapon": "P-pitchfork", "aggro": 16, "bark": "peas"},
	"peasantf": {"model": "peasant_f", "hp": 25, "speed": 4.5, "dmg": 7, "range": 1.8, "atk": "swing", "tele": 0.4, "cd": 1.2, "weapon": "P-pitchfork", "aggro": 16, "bark": "peas"},
	"torch": {"model": "peasant", "hp": 30, "speed": 4.0, "dmg": 12, "range": 1.9, "atk": "swing", "tele": 0.5, "cd": 1.4, "weapon": "P-torch", "aggro": 16, "bark": "peas"},
	"cabbage": {"model": "peasant_f", "hp": 25, "speed": 3.6, "dmg": 8, "range": 17.0, "atk": "throw", "tele": 0.55, "cd": 2.0, "weapon": "P-cabbage", "aggro": 20, "ranged": "cabbage", "keep": 8.0, "bark": "peas"},
	"guard": {"model": "guard", "hp": 60, "speed": 3.8, "dmg": 12, "range": 2.5, "atk": "thrust", "tele": 0.5, "cd": 1.5, "weapon": "P-spear", "shield": true, "aggro": 22, "bark": "guard"},
	"archer": {"model": "archer", "hp": 35, "speed": 0.0, "dmg": 10, "range": 42.0, "atk": "bow", "tele": 0.9, "cd": 2.6, "weapon": "P-bow", "aggro": 38, "ranged": "arrow", "bark": "arch", "static": true},
	"knight": {"model": "knight", "hp": 140, "speed": 3.4, "dmg": 18, "range": 2.4, "atk": "swing", "tele": 0.55, "cd": 1.6, "weapon": "P-sword", "armor": 0.4, "aggro": 24, "charge": true, "bark": "knight"},
	"cook": {"model": "peasant", "hp": 40, "speed": 4.0, "dmg": 10, "range": 1.9, "atk": "swing", "tele": 0.4, "cd": 1.2, "weapon": "P-cleaver", "aggro": 12, "bark": "peas"},
	"jailer": {"model": "jailer", "hp": 120, "speed": 3.2, "dmg": 20, "range": 2.8, "atk": "slam", "tele": 0.7, "cd": 2.0, "weapon": "P-hammer", "aggro": 14, "slam": true, "bark": "guard"},
}
# weapon grips per weapon (bone-space offset/rotation)
const GRIP := {
	"P-pitchfork": [Vector3(0, 0.08, 0.02), Vector3(0, 0, 90)],
	"P-spear": [Vector3(0, 0.08, 0.02), Vector3(0, 0, 90)],
	"P-torch": [Vector3(0, 0.08, 0.0), Vector3(-90, 0, 0)],
	"P-sword": [Vector3(0, 0.08, 0.0), Vector3(-90, 0, 0)],
	"P-cleaver": [Vector3(0, 0.08, 0.0), Vector3(-90, 0, 0)],
	"P-hammer": [Vector3(0, 0.08, 0.0), Vector3(-90, 0, 0)],
	"P-cabbage": [Vector3(0, 0.1, 0.0), Vector3(0, 0, 0)],
	"P-bow": [Vector3(0, 0.07, 0.0), Vector3(0, 90, 0)],
}

var kind := "peasant"
var group := ""
var st := {}
var actor: Actor
var hp := 30.0
var state := "idle"
var st_t := 0.0
var atk_cd := 0.0
var think_t := 0.0
var alerted := false
var los := false
var home := Vector3.ZERO
var home_yaw := 0.0
var face := 0.0
var side_t := 0.0
var side_dir := 0.0
var last_pos := Vector3.ZERO
var stuck_t := 0.0
var stars: Node3D
var hit_done := false
var scripted := false
var defeated := false
var knock := Vector3.ZERO
var torch_fire: Node3D
var charge_dir := Vector3.ZERO
var player: Player

static var bark_cool := 0.0

func setup(k: String, grp: String, pos: Vector3, yaw: float) -> void:
	kind = k; group = grp
	st = STATS.get(k, STATS["peasant"])
	hp = st["hp"]
	home = pos; home_yaw = yaw; face = yaw

func _ready() -> void:
	add_to_group("enemies")
	collision_layer = 4
	collision_mask = 1 | 2 | 4
	floor_snap_length = 0.4
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new(); cap.radius = 0.38 if kind != "knight" and kind != "jailer" else 0.45; cap.height = 1.8
	cs.shape = cap; cs.position.y = 0.9
	add_child(cs)
	actor = Actor.make(st["model"])
	add_child(actor)
	actor.rotation.y = face
	if st.has("weapon"):
		var g: Array = GRIP.get(st["weapon"], [Vector3.ZERO, Vector3.ZERO])
		var w := actor.attach(st["weapon"], "hand_L" if st["weapon"] == "P-bow" else "hand_R", g[0], g[1])
		if st["weapon"] == "P-torch" and w:
			torch_fire = FX.fire(w, w.global_position, 0.35, false)
			torch_fire.position = Vector3(0, 0.62, 0)
	if st.get("shield", false):
		actor.attach("P-shield", "forearm_L", Vector3(0.08, 0.15, 0.0), Vector3(0, 90, 0))
	if kind == "jailer": actor.attach("P-keyring", "hips", Vector3(0.2, 0.0, 0.1), Vector3.ZERO)
	global_position = home
	last_pos = home
	actor.play("eidle" if not st.get("static", false) else "idle", 0.0)
	actor.ap.seek(randf() * 1.0, true)
	think_t = randf() * 0.3

func is_hostile() -> bool:
	return not defeated and not scripted and state != "down"

# ------------------------------------------------------------------ AI
func _physics_process(dt: float) -> void:
	if G.paused: return
	player = G.player
	st_t += dt; atk_cd -= dt
	if state == "down": 
		if not is_on_floor():
			velocity.y -= 22.0 * dt; velocity.x *= 0.9; velocity.z *= 0.9
			move_and_slide()
		return
	if scripted:
		velocity = Vector3.ZERO
		if not is_on_floor(): velocity.y = -5.0
		move_and_slide()
		return
	think_t -= dt
	if think_t <= 0.0:
		think_t = 0.25
		_perceive()
	var to := Vector3.ZERO
	var dist := 999.0
	if player:
		to = player.global_position - global_position; to.y = 0
		dist = to.length()
	var mv := Vector3.ZERO
	var spd: float = st["speed"]
	match state:
		"idle":
			actor.play("eidle" if not st.get("static", false) else "idle")
			if alerted: go("chase")
		"chase":
			if player == null or player.dead: go("idle"); alerted = false
			elif global_position.distance_to(home) > 45.0 and dist > 8.0: go("return")
			else:
				var ranged := st.has("ranged")
				var want_attack: bool = dist < st["range"] and atk_cd <= 0.0 and (not ranged or los)
				if want_attack and (not ranged or dist > 2.0): go("attack")
				elif st.get("static", false):
					face = G.damp_angle(face, atan2(-to.x, -to.z), 6.0, dt)
					actor.play("idle")
				else:
					var dir := to.normalized()
					if ranged and dist < st.get("keep", 6.0):
						dir = -dir   # back off
					elif ranged and dist < st["range"] * 0.8 and los:
						dir = Vector3.ZERO
					elif not ranged and dist < st["range"] * 0.8:
						dir = Vector3.ZERO
					if st.get("charge", false) and dist > 6.0 and dist < 14.0 and atk_cd <= 0.0 and los and randf() < 0.02:
						charge_dir = to.normalized(); go("charge")
					mv = _steer(dir) * spd
					face = G.damp_angle(face, atan2(-to.x, -to.z), 8.0, dt)
					actor.play("ewalk" if mv.length() > 0.3 else "eidle", 0.2, clamp(mv.length() / 2.5, 0.6, 1.8))
		"return":
			var th := home - global_position; th.y = 0
			if th.length() < 1.0: go("idle"); alerted = false
			else:
				mv = _steer(th.normalized()) * spd
				face = G.damp_angle(face, atan2(-th.x, -th.z), 8.0, dt)
				actor.play("ewalk", 0.2)
			if dist < 10.0 and los: go("chase")
		"attack":
			face = G.damp_angle(face, atan2(-to.x, -to.z), 10.0 if st_t < st["tele"] else 2.0, dt)
			if st_t < 0.02:
				actor.play(st["atk"], 0.1, actor.anim_len(st["atk"]) / (st["tele"] + 0.35), true)
				actor.flash(Color(1.0, 0.5, 0.1), 0.35)
				if st.has("ranged"): Audio.sfx3("bow" if kind == "archer" else "throw", global_position, -6)
				else: Audio.sfx3("swing", global_position, -4)
			if st_t >= st["tele"] and not hit_done:
				hit_done = true
				_strike(dist)
			if st_t >= st["tele"] + 0.45:
				atk_cd = st["cd"] * randf_range(0.8, 1.25)
				go("chase")
		"charge":
			actor.play("echarge", 0.1, 1.4)
			mv = charge_dir * 9.0
			face = atan2(-charge_dir.x, -charge_dir.z)
			if dist < 1.8 and not hit_done:
				hit_done = true
				player.damage(st["dmg"] * 0.8, global_position)
				player.velocity += charge_dir * 8.0 + Vector3(0, 4, 0)
			if st_t > 1.1 or (is_on_wall() and st_t > 0.2):
				if is_on_wall(): Audio.sfx3("clank", global_position); go("stunned"); return
				atk_cd = 2.0; go("chase")
		"hit":
			actor.play("hit", 0.05)
			if st_t > 0.3: go("chase")
		"stunned":
			actor.play("dizzy" if actor.ap.has_animation("dizzy") else "stunned", 0.1)
			if st_t > 3.0:
				if stars: stars.queue_free(); stars = null
				go("chase")
		"flee":
			if player:
				var away := -to.normalized()
				mv = _steer(away) * 5.0
				face = G.damp_angle(face, atan2(-away.x, -away.z), 8.0, dt)
				actor.play("flee", 0.2)
			if st_t > 4.0:
				go("cower")
		"cower":
			actor.play("cower", 0.3)
	# knockback + gravity
	knock = knock.move_toward(Vector3.ZERO, 30.0 * dt)
	velocity.x = mv.x + knock.x
	velocity.z = mv.z + knock.z
	if is_on_floor(): velocity.y = -1.0
	else: velocity.y -= 22.0 * dt
	move_and_slide()
	actor.rotation.y = face
	# stuck detection
	if mv.length() > 1.0:
		if global_position.distance_to(last_pos) < mv.length() * dt * 0.25: stuck_t += dt
		else: stuck_t = max(0.0, stuck_t - dt)
		if stuck_t > 0.6: side_t = 0.8; side_dir = [-1.0, 1.0][randi() % 2]; stuck_t = 0.0
	last_pos = global_position
	side_t -= dt

func go(s: String) -> void:
	state = s; st_t = 0.0; hit_done = false

func _steer(dir: Vector3) -> Vector3:
	if dir == Vector3.ZERO: return dir
	var out := dir
	if side_t > 0.0: out = dir.rotated(Vector3.UP, side_dir * 1.3)
	var space := get_world_3d().direct_space_state
	var p := global_position + Vector3(0, 0.6, 0)
	var q := PhysicsRayQueryParameters3D.create(p, p + out * 1.4, 1, [get_rid()])
	if space.intersect_ray(q):
		for a in [0.7, -0.7, 1.4, -1.4]:
			var d2 := out.rotated(Vector3.UP, a)
			q = PhysicsRayQueryParameters3D.create(p, p + d2 * 1.4, 1, [get_rid()])
			if not space.intersect_ray(q): out = d2; break
	# edge check: don't walk off ledges (spire, walls)
	var ahead := global_position + out * 0.8 + Vector3(0, 0.5, 0)
	var q2 := PhysicsRayQueryParameters3D.create(ahead, ahead - Vector3(0, 2.5, 0), 1, [get_rid()])
	if not space.intersect_ray(q2): return Vector3.ZERO
	# separation
	for e in get_tree().get_nodes_in_group("enemies"):
		if e == self or e.state == "down": continue
		var d: Vector3 = global_position - e.global_position; d.y = 0
		if d.length() < 1.1 and d.length() > 0.01: out += d.normalized() * (1.1 - d.length()) * 1.5
	return out.normalized() if out.length() > 0.01 else Vector3.ZERO

func _perceive() -> void:
	if player == null or player.dead or player.input_locked: los = false; return
	var eye := global_position + Vector3(0, 1.6, 0)
	var tgt := player.global_position + Vector3(0, 1.2, 0)
	var d := eye.distance_to(tgt)
	if d > st["aggro"] * (1.0 if not alerted else 1.8): los = false; return
	var q := PhysicsRayQueryParameters3D.create(eye, tgt, 1, [get_rid()])
	los = get_world_3d().direct_space_state.intersect_ray(q).is_empty()
	if los and not alerted: alert(true)

func alert(spread := false) -> void:
	if alerted or defeated: return
	alerted = true
	if state == "idle": go("chase")
	if bark_cool <= 0.0 and randf() < 0.6:
		bark_cool = 5.0
		var b: String = st["bark"]
		var n := {"peas": 8, "guard": 5, "arch": 2, "knight": 2}.get(b, 1)
		G.level.bark("bk_%s%d" % [b, randi() % n], self)
	if spread:
		Audio.sfx3("alert", global_position, -8)
		for e in get_tree().get_nodes_in_group("enemies"):
			if e != self and e.group == group and e.global_position.distance_to(global_position) < 25.0: e.alert(false)

func _strike(dist: float) -> void:
	if player == null: return
	if st.has("ranged"):
		var from := global_position + Vector3(0, 1.5, 0) + (-actor.global_basis.z) * 0.5
		var aim := player.global_position + Vector3(0, 1.0, 0) + player.velocity * (0.35 if kind == "archer" else 0.6)
		var pj := Projectile.new()
		get_parent().add_child(pj)
		pj.launch(st["ranged"], from, aim, st["dmg"], self)
		return
	if st.get("slam", false):
		FX.particles(global_position + (-actor.global_basis.z) * 1.6, 20, Color(0.7, 0.6, 0.5), 0.6, 5.0, 0.4, -6.0, 60.0, Vector3.UP, true)
		Audio.sfx3("slam", global_position)
		player.shake(0.4)
		if dist < st["range"] + 1.0: player.damage(st["dmg"], global_position)
		return
	var fwd := -actor.global_basis.z
	var to := (player.global_position - global_position); to.y = 0
	if dist < st["range"] + 0.6 and fwd.dot(to.normalized()) > 0.3 and abs(player.global_position.y - global_position.y) < 1.8:
		player.damage(st["dmg"], global_position)
		if kind == "torch": FX.particles(player.global_position + Vector3(0, 1, 0), 10, Color(1, 0.5, 0.1), 0.4, 3.0, 0.15, 2.0)

# ------------------------------------------------------------------ damage
func laser_hit(dmg: float, pos: Vector3, dir: Vector3, n: Vector3) -> String:
	if state == "down": return "none"
	if scripted: return "none"
	if not alerted: alert(true)
	var fwd := -actor.global_basis.z
	if st.get("shield", false) and state != "stunned" and state != "attack" and fwd.dot(-dir) > 0.45:
		FX.sparks(pos, -dir, Color(1.0, 0.7, 0.3), 10)
		Audio.sfx3("clank", pos, -6, randf_range(0.9, 1.1))
		actor.play("block", 0.05)
		return "block"
	dmg *= 1.0 - st.get("armor", 0.0)
	hp -= dmg
	actor.flash()
	FX.sparks(pos, -dir, Color(0.6, 1.0, 0.95), 10)
	Audio.sfx3("hit_enemy", pos, -4, randf_range(0.9, 1.15))
	knock += Vector3(dir.x, 0, dir.z).normalized() * (2.5 if st.get("armor", 0.0) == 0.0 else 0.8)
	if hp <= 0.0:
		ko(); return "ko"
	if kind in ["peasant", "peasantf", "cabbage", "torch", "cook"] and hp < st["hp"] * 0.35 and randf() < 0.3 and state != "flee":
		go("flee"); defeated_soft()
		if bark_cool <= 0.0: bark_cool = 4.0; G.level.bark("bk_flee%d" % (randi() % 2), self)
		return "hit"
	if state in ["idle", "chase"] and st.get("armor", 0.0) == 0.0 and kind != "archer": go("hit")
	return "hit"

func defeated_soft() -> void:
	if defeated: return
	defeated = true
	knocked_out.emit(self)

func pulse_hit(from: Vector3) -> void:
	if state == "down": return
	var d := global_position - from; d.y = 0
	knock += d.normalized() * 9.0
	alert(true)
	if kind == "jailer" or kind == "knight": hp -= 15
	else: hp -= 8
	if hp <= 0: ko(); return
	go("stunned")
	if stars == null: stars = FX.stars(self, 2.2)

func ko() -> void:
	if state == "down": return
	go("down")
	collision_layer = 0
	collision_mask = 1
	actor.play("down", 0.1)
	if stars: stars.queue_free()
	stars = FX.stars(self, 0.6)
	Audio.sfx3("ko", global_position, -2)
	G.save["kos"] += 1
	if torch_fire: torch_fire.queue_free(); torch_fire = null
	if randf() < 0.2 and kind in ["peasant", "peasantf", "cabbage", "torch"]:
		G.level.bark("bk_ko%d" % (randi() % 3), self)
	elif randf() < 0.18:
		G.level.bark("bk_kill%d" % (randi() % 4))
	if randf() < 0.22 and G.level.has_method("spawn_pickup"):
		G.level.spawn_pickup("apple", global_position + Vector3(0, 0.5, 0))
	var was := defeated
	defeated = true
	if not was: knocked_out.emit(self)
	# no body blocking: collision off, stay on the ground as scenery
	await get_tree().create_timer(30.0).timeout
	if is_instance_valid(self) and G.player and G.player.global_position.distance_to(global_position) > 25.0:
		queue_free()
