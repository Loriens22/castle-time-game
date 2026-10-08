class_name Level
extends Node3D
## Shared level functionality: markers, player, cutscene helpers, barks, lights, checkpoints.

var markers := {}
var player: Player
var cs_cam: Camera3D
var in_cs := false
var env: WorldEnvironment
var sun: DirectionalLight3D
var light_t := 0.0
var bark_t := 0.0
var cp_id := ""
var cp_pos := Vector3.ZERO
var cp_yaw := 0.0
var talkers := {}     # speaker id -> Actor (lip flap)
var objective_text := ""
# ---- fail-safes: a cutscene that makes no progress for CS_WATCHDOG seconds is force-ended (and its
# essential story effects applied via its recover callable); stuck input locks / black screens / slow-mo
# are released too. Every wait in a cutscene ticks cs_idle, so only a dead or stuck coroutine trips it.
const CS_WATCHDOG := 10.0
var cs_name := ""
var cs_idle := 0.0
var cs_abort := false
var cs_recover := Callable()
var _wd_lock := 0.0
var _wd_fade := 0.0
var _wd_slow := 0.0
var wd_off := false

func collect_markers(root: Node) -> void:
	for c in root.get_children():
		if String(c.name).begins_with("M-"):
			markers[String(c.name)] = c
		if c.get_child_count() > 0 and not (c is MeshInstance3D): collect_markers(c)

func mpos(name: String) -> Vector3:
	return markers[name].global_position if markers.has(name) else Vector3.ZERO

func myaw(name: String) -> float:
	return markers[name].global_rotation.y if markers.has(name) else 0.0

func spawn_player(pos: Vector3, yaw: float, weapon := true) -> void:
	player = Player.new()
	player.weapon = weapon
	add_child(player)
	player.teleport(pos, yaw)
	player.invuln = 3.0   # grace period at checkpoints
	player.died.connect(_on_player_died)
	cs_cam = Camera3D.new(); cs_cam.fov = 50; cs_cam.near = 0.05; cs_cam.far = 600
	add_child(cs_cam)

func setup_env(sky_top: Color, sky_hor: Color, ground: Color, sun_col: Color, sun_energy: float, sun_rot: Vector3, fog_col: Color, fog_density: float, ambient := 0.5) -> void:
	env = WorldEnvironment.new()
	var e := Environment.new()
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = sky_top; sm.sky_horizon_color = sky_hor
	sm.ground_bottom_color = ground; sm.ground_horizon_color = sky_hor
	sm.sun_angle_max = 20.0; sm.sky_curve = 0.12
	sky.sky_material = sm
	e.background_mode = Environment.BG_SKY
	e.sky = sky
	e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	e.ambient_light_energy = ambient
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	e.tonemap_exposure = 1.0
	e.fog_enabled = fog_density > 0.0
	e.fog_light_color = fog_col
	e.fog_density = fog_density
	e.fog_sky_affect = 0.25
	e.glow_enabled = G.settings["quality"] >= 1
	e.glow_intensity = 0.6
	e.glow_bloom = 0.05
	e.glow_hdr_threshold = 1.1
	env.environment = e
	add_child(env)
	sun = DirectionalLight3D.new()
	sun.light_color = sun_col; sun.light_energy = sun_energy
	sun.rotation_degrees = sun_rot
	add_child(sun)
	apply_quality()
	if not G.settings_changed.is_connected(apply_quality): G.settings_changed.connect(apply_quality)

func apply_quality() -> void:
	var q: int = G.settings["quality"]
	if sun:
		sun.shadow_enabled = q >= 1
		sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL if q == 1 else DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
		sun.directional_shadow_max_distance = 45.0 if q == 1 else 80.0
		sun.shadow_blur = 1.5
	var vp := get_viewport()
	vp.scaling_3d_scale = [0.7, 0.85 if G.is_web else 1.0, 1.0][q]
	vp.msaa_3d = Viewport.MSAA_DISABLED if q < 2 else Viewport.MSAA_2X
	if env: env.environment.glow_enabled = q >= 1

func max_lights() -> int:
	return [3, 6, 10][G.settings["quality"]]

func _process(dt: float) -> void:
	_watchdog()
	Enemy.bark_cool -= dt
	bark_t -= dt
	light_t -= dt
	if light_t <= 0.0:
		light_t = 0.35
		_manage_lights()
	for k in talkers.keys():
		var a = talkers[k]   # untyped on purpose: a talker can be freed (assigning a freed object to a typed var is an error)
		if is_instance_valid(a): a.talking = false
		else: talkers.erase(k)
	if Audio.vo_player.playing and cur_speaker != "" and talkers.has(cur_speaker) and is_instance_valid(talkers[cur_speaker]):
		talkers[cur_speaker].talking = true

func _watchdog() -> void:
	var rdt := clampf(get_process_delta_time() / maxf(Engine.time_scale, 0.05), 0.0, 0.25)   # unscaled game time
	if wd_off or G.paused or player == null or (G.main and G.main.loading): return
	if in_cs:
		cs_idle += rdt
		if cs_idle > CS_WATCHDOG: _cs_watchdog_fire()
	# input lock left on outside a cutscene (fall, zip, a crashed sequence)
	if player.input_locked and not in_cs and not player.zipping and not player.dead:
		_wd_lock += rdt
		if _wd_lock > 6.0:
			_wd_report("input lock released")
			player.input_locked = false
	else: _wd_lock = 0.0
	# screen left black outside a cutscene
	if G.ui.fade_rect.color.a > 0.9 and not in_cs and not player.dead:
		_wd_fade += rdt
		if _wd_fade > 5.0:
			_wd_report("black screen cleared"); _wd_fade = 0.0
			G.ui.fade(0.0, 0.4)
	else: _wd_fade = 0.0
	# slow motion left on
	if Engine.time_scale < 0.99 and not player.dead:
		_wd_slow += rdt
		if _wd_slow > 2.0: _wd_report("time scale reset"); Engine.time_scale = 1.0
	else: _wd_slow = 0.0

func _wd_report(what: String) -> void:
	G.tlog("WATCHDOG " + what)
	push_warning("Castle TIME watchdog: " + what)

func _cs_watchdog_fire() -> void:
	var nm := cs_name; var rec := cs_recover
	_wd_report("cutscene '%s' made no progress for %.0fs - forcing it to end" % [nm, CS_WATCHDOG])
	cs_abort = true          # a zombie coroutine that wakes up later races through (skip mode)
	Engine.time_scale = 1.0
	if G.ui.fade_rect.color.a > 0.0: G.ui.fade(0.0, 0.4)
	cs_end()
	if rec.is_valid(): rec.call()

func cs_tick() -> void:
	cs_idle = 0.0

func _manage_lights() -> void:
	var cam := get_viewport().get_camera_3d()
	if cam == null: return
	var cp := cam.global_position
	var ls := get_tree().get_nodes_in_group("dyn_lights")
	ls.sort_custom(func(a, b): return a.global_position.distance_squared_to(cp) < b.global_position.distance_squared_to(cp))
	var n := max_lights()
	for i in ls.size():
		ls[i].visible = i < n and ls[i].global_position.distance_to(cp) < 45.0

# ------------------------------------------------------------------ dialogue
var cur_speaker := ""
func say_line(id: String) -> float:
	if not G.dialogue.has(id): return 0.0
	var d: Dictionary = G.dialogue[id]
	var dur := maxf(Audio.vo(id), 0.8)
	cs_tick()
	cur_speaker = d["who"]
	G.tlog("say %s (%.1fs) %s: %s" % [id, dur, d["who"], String(d["text"]).left(50)])
	G.ui.subtitle(d["who"], d["text"], dur)
	return dur

func bark(id: String, _src: Node = null) -> void:
	if Audio.vo_player.playing or in_cs or bark_t > 0.0: return
	bark_t = 2.5
	say_line(id)

## plays a line during gameplay and waits for it (non-blocking for the player)
func line(id: String, gap := 0.25) -> void:
	var d := say_line(id)
	await wait_real(d + gap)

func wait_real(t: float) -> void:
	var e := 0.0
	while e < t:
		await get_tree().process_frame
		if not is_inside_tree(): return
		if in_cs: cs_tick()
		if not G.paused: e += get_process_delta_time()

# ------------------------------------------------------------------ cutscenes
func skipping() -> bool:
	return G.ui.skip_req or cs_abort

func cs_begin(name := "", recover := Callable()) -> void:
	G.tlog("cs_begin %s" % name)
	if in_cs: G.tlog("  (replacing running cutscene '%s')" % cs_name)
	cs_name = name; cs_recover = recover; cs_idle = 0.0; cs_abort = false
	in_cs = true
	G.ui.skip_req = false
	G.ui.advance_req = false
	Engine.time_scale = 1.0
	player.input_locked = true
	player.velocity = Vector3.ZERO
	player.touch_fire = false
	G.ui.letterbox(true)
	G.ui.set_waypoint(null)
	cs_cam.global_transform = player.cam.global_transform
	cs_cam.fov = player.cam.fov
	cs_cam.current = true

func cs_end(restore_cam := true) -> void:
	G.tlog("cs_end %s" % cs_name)
	cs_name = ""; cs_recover = Callable(); cs_idle = 0.0
	in_cs = false
	Engine.time_scale = 1.0
	if shot_tw: shot_tw.kill()
	G.ui.letterbox(false)
	Audio.stop_vo()
	G.ui.clear_sub()
	if restore_cam: player.cam.current = true
	player.input_locked = false
	player.velocity = Vector3.ZERO
	G.ui.skip_req = false
	G.ui.advance_req = false
	refresh_objective()

func refresh_objective() -> void:
	pass

var shot_tw: Tween
## camera shot: place cs_cam at pos looking at look; optionally dolly to pos2/look2 over dur
func shot(pos: Vector3, look: Vector3, dur := 0.0, pos2 = null, look2 = null, fov := 50.0) -> void:
	if shot_tw: shot_tw.kill()
	cs_tick()
	cs_cam.fov = fov
	cs_cam.global_position = pos
	_look(cs_cam, look)
	if dur > 0.0 and pos2 != null:
		var l2: Vector3 = look2 if look2 != null else look
		shot_tw = create_tween()
		shot_tw.tween_method(func(v: float):
			cs_cam.global_position = pos.lerp(pos2, v)
			_look(cs_cam, look.lerp(l2, v)), 0.0, 1.0, dur).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)

func _look(c: Node3D, at: Vector3) -> void:
	if c.global_position.distance_to(at) < 0.01: return
	var up := Vector3.UP
	if abs((at - c.global_position).normalized().dot(up)) > 0.99: up = Vector3.FORWARD
	c.look_at(at, up)

## say a line in a cutscene (skippable); actor lip-flaps if registered in talkers
## (tap / click / Space / Enter / gamepad A advances to the next line; SKIP ends the whole cutscene)
func say(id: String, extra := 0.25) -> void:
	if skipping(): return
	G.ui.advance_req = false
	var d := say_line(id)
	await cs_wait(d + extra, true)

## waits t seconds of (unpaused) cutscene time. Never waits on audio/animation signals, so it always returns.
func cs_wait(t: float, is_line := false) -> void:
	var e := 0.0
	while e < t and not skipping():
		await get_tree().process_frame
		if not is_inside_tree(): return
		cs_tick()
		if not G.paused: e += get_process_delta_time()
		if G.ui.advance_req and not G.paused:
			G.ui.advance_req = false
			if e > 0.25:   # ignore a tap in the very first moment (double taps)
				if is_line: Audio.stop_vo(); G.ui.clear_sub()
				break
	if skipping():
		Audio.stop_vo(); G.ui.clear_sub()

# ------------------------------------------------------------------ checkpoints / death
func set_checkpoint(id: String, pos: Vector3, yaw: float, stage: int, toast := true) -> void:
	if id == cp_id: return
	cp_id = id; cp_pos = pos; cp_yaw = yaw
	G.tlog("checkpoint %s" % id)
	G.checkpoint(id, stage)
	if toast:
		G.ui.toast("CHECKPOINT", Color(0.6, 1.0, 0.9))
		Audio.sfx("checkpoint", -6)

func _on_player_died() -> void:
	G.tlog("player died")
	await G.ui.fade(1.0, 0.8)
	respawn_now()
	await get_tree().create_timer(0.3).timeout
	await G.ui.fade(0.0, 0.6)
	if randf() < 0.5: bark("bk_respawn")

func respawn() -> void:
	await G.ui.fade(1.0, 0.5)
	respawn_now()
	await G.ui.fade(0.0, 0.5)

func respawn_now() -> void:
	player.revive()
	player.teleport(cp_pos, cp_yaw)
	player.cam.current = true

func on_fall() -> void:
	player.input_locked = true
	await G.ui.fade(1.0, 0.35)
	player.teleport(cp_pos, cp_yaw)
	player.damage(0)
	player.input_locked = false
	await G.ui.fade(0.0, 0.4)

func surface_at(_p: Vector3) -> String:
	return "stone"

func spawn_pickup(kind: String, pos: Vector3) -> void:
	var p := Pickup.new()
	p.setup(kind, pos)
	add_child(p)
