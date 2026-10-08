extends Node
## Automated playthrough bot (test only; enabled with the user arg --bot).
## Plays the story like a player would: walks with the move vector, aims by turning the camera, holds real
## input actions (fire / jump / roll / interact / pulse), taps the screen during cutscenes to advance dialogue,
## and leaves every enemy active. A monitor prints STALL when the story state hasn't changed for 20 s.
## Options: --bot-taps (tap through dialogue), --bot-skip (sometimes tap SKIP), --bot-pause (pause inside
## cutscenes), --bot-die (die during dialogue / sequences), --bot-god (no damage; to test the story only).

const TX := 27.0
const TZ := -60.0
const RM := 6.75
const GAPS := [14, 15, 30, 31, 50, 51, 66, 67, 86, 87, 100, 101, 116, 117, 129, 130]
const WANT_IT := ["PhoneInteract", "IT_grate", "IT_dungeongate", "IT_cellgate", "IT_zip"]

var opt := {}
var t := 0.0
var nav_map := RID()
var nav_region := RID()
var nav_key := ""
var path := PackedVector3Array()
var path_i := 0
var repath_t := 0.0
var path_goal := Vector3.INF
var stuck_t := 0.0
var last_pos := Vector3.ZERO
var prog_key := ""
var prog_t := 0.0
var stall_n := 0
var fire_on := false
var act_cd := {}
var cs_last := ""
var cs_tap_t := 0.0
var cs_paused := false
var cs_pause_done := {}
var died_in := {}
var seg := -1            # spiral ledge progress
var clock_phase := 0
var status_t := 0.0
var started := false
var done := false

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--bot"): opt[a.substr(2)] = true
	G.trace = true
	G.bench = true
	print("BOT start ", opt.keys())

func _log(s: String) -> void:
	print("BOT %7.1f %s" % [t, s])

# ------------------------------------------------------------------ main loop
func _physics_process(dt: float) -> void:
	t += dt
	var lv = G.level
	if lv == null or G.main.loading: return
	if lv.get("title_mode"):
		if G.save["flags"].get("finished", false) and started:
			if not done: done = true; _log("DONE - back on the title screen after the credits. deaths=%d kos=%d" % [G.save["deaths"], G.save["kos"]])
			return
		if not started:
			started = true; _log("title -> New Game"); G.main.new_game()
		return
	var p: Player = G.player
	if p == null: return
	if opt.has("bot-god"): p.invuln = 1.0
	_monitor(lv, p, dt)
	if G.paused:
		if cs_paused and t > cs_tap_t:
			cs_paused = false; _log("unpause"); _tap_pause_action()
		return
	if lv.in_cs or p.input_locked or p.dead:
		_release()
		if lv.in_cs: _cutscene(lv, p)
		return
	cs_last = ""
	_play(lv, p, dt)

func _release() -> void:
	G.player.auto_move = Vector3.ZERO
	if fire_on: Input.action_release("fire"); fire_on = false

func _press(a: String, hold := 0.12) -> void:
	if act_cd.get(a, 0.0) > t: return
	act_cd[a] = t + hold + 0.1
	Input.action_press(a)
	get_tree().create_timer(hold, true, true, true).timeout.connect(func(): Input.action_release(a))

func _touch(pos: Vector2) -> void:
	var e := InputEventScreenTouch.new(); e.index = 3; e.position = pos; e.pressed = true
	Input.parse_input_event(e)
	var r := InputEventScreenTouch.new(); r.index = 3; r.position = pos; r.pressed = false
	get_tree().create_timer(0.08, true, false, true).timeout.connect(func(): Input.parse_input_event(r))

func _tap_pause_action() -> void:
	var e := InputEventAction.new(); e.action = "pause"; e.pressed = true; Input.parse_input_event(e)
	var r := InputEventAction.new(); r.action = "pause"; r.pressed = false; Input.parse_input_event(r)

# ------------------------------------------------------------------ cutscenes: tap to advance / skip / pause
func _cutscene(lv, p: Player) -> void:
	var nm: String = lv.get("cs_name") if lv.get("cs_name") != null else "?"
	if nm != cs_last:
		cs_last = nm; cs_tap_t = t + randf_range(1.5, 4.0)
	var vs := get_viewport().get_visible_rect().size
	if opt.has("bot-die") and not died_in.has("cs_" + nm) and randf() < 0.002:
		died_in["cs_" + nm] = true
		_log("forcing a death inside cutscene '%s' (should be ignored while locked)" % nm)
		p.invuln = 0.0; p.damage(999)
	if opt.has("bot-pause") and not cs_pause_done.has(nm) and t > cs_tap_t and G.ui.touch.visible:
		cs_pause_done[nm] = true
		_log("tap PAUSE inside cutscene '%s'" % nm)
		_touch(G.ui.touch.buttons["pause"]["pos"]); cs_paused = true; cs_tap_t = t + 2.0
		return
	if t > cs_tap_t:
		if opt.has("bot-skip") and randf() < 0.12 and G.ui.touch.visible:
			_log("tap SKIP in '%s'" % nm); _touch(G.ui.touch.buttons["skip"]["pos"])
		elif opt.has("bot-taps"):
			_touch(vs * Vector2(0.5, 0.45))
		cs_tap_t = t + randf_range(1.2, 3.5)

# ------------------------------------------------------------------ monitor
func _monitor(lv, p: Player, dt: float) -> void:
	var key := "%s|%s|%s|%s|%s|%d|%d" % [_lvname(lv), str(lv.get("stage")), str(lv.get("cp_id")), G.ui.obj_lbl.text, str(lv.in_cs), G.save["flags"].size(), G.save["kos"]]
	if lv.in_cs: key += "|" + str(lv.get("cs_name")) + "|" + G.ui.sub_lbl.text.left(30)
	if lv.get("boss") and lv.boss: key += "|%d" % int(lv.boss.hp)
	if lv.get("chains_left") != null: key += "|%d" % lv.chains_left
	if key != prog_key:
		prog_key = key; prog_t = 0.0; stall_n = 0
	elif not G.paused:
		prog_t += dt
		if prog_t > 20.0 * (stall_n + 1):
			stall_n += 1
			_log("STALL %.0fs: stage=%s cp=%s obj='%s' in_cs=%s cs=%s locked=%s dead=%s fade=%.2f ts=%.2f pos=%s goal=%s" % [prog_t, str(lv.get("stage")), str(lv.get("cp_id")), G.ui.obj_lbl.text, str(lv.in_cs), str(lv.get("cs_name")), str(p.input_locked), str(p.dead), G.ui.fade_rect.color.a, Engine.time_scale, str(p.global_position.snapped(Vector3.ONE * 0.1)), str(path_goal.snapped(Vector3.ONE * 0.1)) if path_goal != Vector3.INF else "-"])
	status_t -= dt
	if status_t <= 0.0:
		status_t = 15.0
		_log("status hp=%d pos=%s obj='%s' fps=%d" % [p.hp, str(p.global_position.snapped(Vector3.ONE * 0.1)), G.ui.obj_lbl.text, Engine.get_frames_per_second()])

# ------------------------------------------------------------------ gameplay
func _play(lv, p: Player, dt: float) -> void:
	var stage: int = lv.get("stage") if lv.get("stage") != null else 0
	var pos := p.global_position
	# 1. interact with story objects in reach
	if p.interact_target and is_instance_valid(p.interact_target) and String(p.interact_target.name) in WANT_IT:
		if act_cd.get("interact", 0.0) <= t: _log("interact " + String(p.interact_target.name))
		_press("interact", 0.12)
	else:
		# a story object close by but not selected: turn to face it (the prompt prefers what you look at)
		for n in get_tree().get_nodes_in_group("interact"):
			if n.get("enabled") and String(n.name) in WANT_IT and n.global_position.distance_to(pos + Vector3(0, 1, 0)) < 2.6:
				var d: Vector3 = n.global_position - pos
				p.yaw = atan2(-d.x, -d.z)
				if int(t * 2) % 10 == 0 and act_cd.get("dbg", 0.0) < t:
					act_cd["dbg"] = t + 5.0
					_log("near %s but prompt is %s" % [n.name, str(p.interact_target.name) if p.interact_target else "none"])
				break
	# 2. pick a target to shoot
	var shoot = null
	var close := 0
	var boss = lv.get("boss")
	if boss and is_instance_valid(boss) and boss.active and boss.state != "down":
		shoot = _boss_aim(lv, boss, p)
	elif stage == 3 and lv.group_cleared("green") and lv.chains_left > 0:
		for c in lv.chain_targets:   # the objective first: the drawbridge chains
			if c.collision_layer != 0 and c.global_position.distance_to(pos) < 30.0: shoot = c.global_position + Vector3(0, 0.5, 0); break
	else:
		var best := 22.0
		for e in get_tree().get_nodes_in_group("enemies"):
			if not is_instance_valid(e) or not e.is_hostile(): continue
			var d: float = e.global_position.distance_to(pos)
			if d < 4.0: close += 1
			if d < best and _los(p, e.global_position + Vector3(0, 1.1, 0)): best = d; shoot = e.global_position + Vector3(0, 1.1, 0)
	if close >= 2 and p.pulse_cd <= 0.0: _press("pulse")
	if shoot != null:
		_aim(p, shoot)
		if prog_t > 12.0 and act_cd.get("raydbg", 0.0) < t:
			act_cd["raydbg"] = t + 10.0
			var q := PhysicsRayQueryParameters3D.create(p.cam.global_position, shoot + (shoot - p.cam.global_position).normalized() * 0.5, 0xFFFFFFFF, [p.get_rid()])
			q.collide_with_areas = true
			var h := p.get_world_3d().direct_space_state.intersect_ray(q)
			_log("aiming at %s: camera ray hits %s at %s" % [str(shoot.snapped(Vector3.ONE * 0.1)), str(h.collider.name) + "/" + str(h.collider.get_parent().name) if h else "nothing", str(h.position.snapped(Vector3.ONE * 0.1)) if h else "-"])
		if not fire_on: Input.action_press("fire"); fire_on = true
	elif fire_on: Input.action_release("fire"); fire_on = false
	# 3. movement
	if stage >= 5 and stage <= 6 and _lvname(lv) == "world" and _spiral(lv, p): return
	var goal = _goal(lv, p, stage)
	if goal == null: p.auto_move = Vector3.ZERO; return
	_go(lv, p, goal, dt, stage)

func _goal(lv, p: Player, stage: int):
	var boss = lv.get("boss")
	if boss and is_instance_valid(boss) and boss.active and boss.state != "down":
		# circle the terrace, keep away from his sword
		var c := Vector3(TX, p.global_position.y, TZ)
		var off := p.global_position - c; off.y = 0
		if off.length() < 0.5: off = Vector3(1, 0, 0)
		var ang := atan2(off.z, off.x) + 0.6
		return c + Vector3(cos(ang), 0, sin(ang)) * 4.6
	if stage == 3 and lv.group_cleared("green") and lv.chains_left > 0: return Vector3(0, 0, 9.5)
	var wp = G.ui.wp_pos
	if wp != null: return wp
	# no waypoint: hunt the nearest hostile enemy of the area
	var best := 60.0; var bp = null
	for e in get_tree().get_nodes_in_group("enemies"):
		if is_instance_valid(e) and e.is_hostile():
			var d: float = e.global_position.distance_to(p.global_position)
			if d < best: best = d; bp = e.global_position
	return bp

func _go(lv, p: Player, goal: Vector3, dt: float, stage: int) -> void:
	_ensure_nav(lv, stage)
	repath_t -= dt
	if repath_t <= 0.0 or goal.distance_to(path_goal) > 1.0:
		repath_t = 0.6
		path_goal = goal
		if nav_map.is_valid():
			var a := NavigationServer3D.map_get_closest_point(nav_map, p.global_position)
			var b := NavigationServer3D.map_get_closest_point(nav_map, goal)
			path = NavigationServer3D.map_get_path(nav_map, a, b, true)
			path_i = 1 if path.size() > 1 else 0
		if path.is_empty(): path = PackedVector3Array([goal]); path_i = 0
	while path_i < path.size() - 1 and _flat(path[path_i]).distance_to(_flat(p.global_position)) < 0.7: path_i += 1
	var tgt: Vector3 = path[min(path_i, path.size() - 1)]
	var to := tgt - p.global_position; to.y = 0
	var dist_goal := _flat(goal).distance_to(_flat(p.global_position))
	if dist_goal < 0.8 and abs(goal.y - p.global_position.y) < 2.0:
		p.auto_move = Vector3.ZERO
		return
	p.auto_move = to.normalized() if to.length() > 0.05 else Vector3.ZERO
	# escape: roll under the dropped portcullis
	if stage == 10 and lv.portcullis_dropped and abs(p.global_position.x) < 3.5 and p.global_position.z > -14.0 and p.global_position.z < -3.0 and p.is_on_floor():
		_press("roll", 0.05)
	# unstick: jump, then roll, then sidestep
	if p.global_position.distance_to(last_pos) < 0.04 * 60.0 * dt * 0.25:
		stuck_t += dt
	else: stuck_t = max(0.0, stuck_t - dt * 2.0)
	last_pos = p.global_position
	if stuck_t > 1.2 and p.is_on_floor(): _press("jump", 0.35)
	if stuck_t > 3.0:
		p.auto_move = p.auto_move.rotated(Vector3.UP, PI / 2 * (1 if int(t) % 2 == 0 else -1))
	if stuck_t > 6.0:
		_log("stuck at %s going to %s - rebaking nav" % [str(p.global_position.snapped(Vector3.ONE * 0.1)), str(goal.snapped(Vector3.ONE * 0.1))])
		nav_key = ""; stuck_t = 0.0

func _flat(v: Vector3) -> Vector3: return Vector3(v.x, 0, v.z)

func _lvname(lv) -> String: return lv.get_script().resource_path.get_file().get_basename()

func _los(p: Player, to: Vector3) -> bool:
	var from := p.global_position + Vector3(0, 1.4, 0)
	var q := PhysicsRayQueryParameters3D.create(from, to, 1, [p.get_rid()])
	return p.get_world_3d().direct_space_state.intersect_ray(q).is_empty()

func _aim(p: Player, at: Vector3) -> void:
	var c := p.cam.global_position
	var d := at - c
	p.yaw = atan2(-d.x, -d.z)
	p.pitch = clamp(atan2(d.y, Vector2(d.x, d.z).length()), -1.2, 0.9)

func _boss_aim(lv, boss, p: Player):
	var off: Vector3 = boss.global_position - Vector3(TX, boss.global_position.y, TZ); off.y = 0
	if off.length() < 5.0 and lv.bell_cd <= 0.0 and lv.movers.has("X-bell"):
		return lv.movers["X-bell"].global_position + Vector3(0, 1.4, 0)
	return boss.global_position + Vector3(0, 1.3, 0)

# ------------------------------------------------------------------ navmesh from the live level
func _ensure_nav(lv, stage: int) -> void:
	var key := "%s|%d|%s" % [_lvname(lv), stage, str(lv.get("chains_left"))]
	var mv = lv.get("movers")
	if mv is Dictionary:   # doors / gates / portcullis that opened or closed since the last bake
		for k in mv:
			if ("gate" in k or "door" in k or "portcullis" in k or "bridge" in k) and is_instance_valid(mv[k]):
				key += "|%s" % str((mv[k] as Node3D).position.snapped(Vector3.ONE))
	if key == nav_key: return
	nav_key = key
	var t0 := Time.get_ticks_msec()
	var nm := NavigationMesh.new()
	nm.agent_radius = 0.4; nm.agent_height = 1.75; nm.agent_max_climb = 0.45; nm.agent_max_slope = 50
	nm.cell_size = 0.25; nm.cell_height = 0.1
	nm.geometry_parsed_geometry_type = NavigationMesh.PARSED_GEOMETRY_STATIC_COLLIDERS
	var src := NavigationMeshSourceGeometryData3D.new()
	NavigationServer3D.parse_source_geometry_data(nm, src, lv)
	NavigationServer3D.bake_from_source_geometry_data(nm, src)
	if not nav_map.is_valid():
		nav_map = NavigationServer3D.map_create()
		NavigationServer3D.map_set_cell_size(nav_map, 0.25); NavigationServer3D.map_set_cell_height(nav_map, 0.1)
		NavigationServer3D.map_set_active(nav_map, true)
		nav_region = NavigationServer3D.region_create()
		NavigationServer3D.region_set_map(nav_region, nav_map)
	NavigationServer3D.region_set_navigation_mesh(nav_region, nm)
	NavigationServer3D.map_force_update(nav_map)
	_log("navmesh baked for %s in %d ms (%d polys)" % [key, Time.get_ticks_msec() - t0, nm.get_polygon_count()])

# ------------------------------------------------------------------ spire ledge + clock hand
func _seg_pos(i: int) -> Vector3:
	var a0 := -PI / 2 + TAU * (i + 0.5) / 36.0
	return Vector3(TX + cos(a0) * RM, 0.6 + i * 40.0 / 144.0, -(-TZ + sin(a0) * RM))

func _spiral(lv, p: Player) -> bool:
	var pos := p.global_position
	var r := Vector2(pos.x - TX, pos.z - TZ).length()
	if seg < 0:
		# not on the ledge yet: walk to the foot of the stairs, then onto segment 0
		if pos.y < 0.4 and _flat(pos).distance_to(_flat(_seg_pos(0))) > 1.2: return false
		seg = 0
		if pos.y > 1.5:   # respawned on a ledge checkpoint: pick the segment we're standing on
			var best := 1e9
			for i in 146:
				var d := _seg_pos(i).distance_to(pos)
				if d < best and not (i in GAPS): best = d; seg = i
		_log("spiral: on the ledge at segment %d" % seg)
	# where are we? nearest segment at our height
	if pos.y < _seg_pos(seg).y - 2.5:
		_log("spiral: fell (y=%.1f), starting over" % pos.y); seg = -1; clock_phase = 0; return false
	var tgt_i := seg + 1
	while tgt_i in GAPS: tgt_i += 1
	if act_cd.get("spdbg", 0.0) < t:
		act_cd["spdbg"] = t + 8.0
		_log("spiral seg=%d phase=%d ct=%.1f pos=%s" % [seg, clock_phase, fmod(lv.clock_t, 19.0), str(pos.snapped(Vector3.ONE * 0.1))])
	if seg + 1 >= 38 and seg < 47:
		return _clock(lv, p)
	if tgt_i > 145:
		seg = 999; _log("spiral: top reached"); return false
	var tgt := _seg_pos(tgt_i)
	var to := tgt - pos; to.y = 0
	p.auto_move = to.normalized()
	if (seg + 1) in GAPS and to.length() < 3.2 and p.is_on_floor():
		_press("jump", 0.35)
	if to.length() < 0.55 and abs(tgt.y - pos.y) < 1.2: seg = tgt_i
	return true

func _clock(lv, p: Player) -> bool:
	var h: Node3D = lv.movers["X-clockhand"]
	var ct := fmod(lv.clock_t, 19.0)
	var pos := p.global_position
	match clock_phase:
		0:   # wait at segment 37 for the hand to sit at our end
			var s37 := _seg_pos(37)
			var to := s37 - pos; to.y = 0
			p.auto_move = to.normalized() if to.length() > 0.4 else Vector3.ZERO
			if to.length() < 1.7 and ct > 0.2 and ct < 1.9:
				clock_phase = 1; _log("clock: boarding the minute hand")
		1:   # hop onto the hand
			var spot := h.global_transform * Vector3(0, 0.6, -4.5)
			var to := spot - pos; to.y = 0
			p.auto_move = to.normalized() if to.length() > 0.4 else Vector3.ZERO
			if to.length() < 2.6 and p.is_on_floor() and spot.y > pos.y + 0.3: _press("jump", 0.35)
			if to.length() < 0.6 and abs(spot.y - pos.y) < 0.8: clock_phase = 2; _log("clock: riding")
			if ct > 2.6 and clock_phase == 1: clock_phase = 0; _log("clock: missed the hand, waiting for the next one")
		2:   # ride: stay on the hand's tip spot
			var spot := h.global_transform * Vector3(0, 0.6, -4.5)
			var to := spot - pos; to.y = 0
			p.auto_move = to.normalized() * 0.6 if to.length() > 0.3 else Vector3.ZERO
			if ct > 9.7 and ct < 11.8: clock_phase = 3; _log("clock: jumping off at segment 47")
		3:
			var s47 := _seg_pos(47)
			var to := s47 - pos; to.y = 0
			p.auto_move = to.normalized()
			if p.is_on_floor() and to.length() < 3.0 and s47.y > pos.y - 0.2: _press("jump", 0.35)
			if to.length() < 0.6 and abs(s47.y - pos.y) < 1.0:
				seg = 47; clock_phase = 0; _log("clock: across")
			if ct > 12.5: clock_phase = 2
	if pos.y < _seg_pos(36).y - 3.0:
		_log("clock: fell"); clock_phase = 0; seg = -1
	return true
