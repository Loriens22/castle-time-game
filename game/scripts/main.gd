extends Node
## Root: owns the UI and the current level, handles title / pause / level switching.

var ui: CanvasLayer
var level_holder: Node
var level: Node
var loading := false

func _ready() -> void:
	G.main = self
	process_mode = Node.PROCESS_MODE_ALWAYS
	_setup_input()
	ui = preload("res://scripts/ui.gd").new()
	add_child(ui)
	level_holder = Node.new(); level_holder.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(level_holder)
	get_tree().root.size_changed.connect(_on_resize)
	_on_resize()
	var a := {}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--level="): a["level"] = arg.substr(8)
		elif arg.begins_with("--cp="): a["cp"] = arg.substr(5)
	_debug_args()
	if "--bot" in OS.get_cmdline_user_args():
		var b: Node = load("res://scripts/test/bot.gd").new(); b.name = "Bot"; add_child(b)
	if a.has("level"):
		var args := {}
		if a.has("cp"): args["cp"] = a["cp"]; G.save["stage"] = 1
		if a["level"] == "ending": load_level("lab", {"ending": true})
		elif a["level"] == "arrive": load_level("world", {"arrive": true, "cp": "farm"})
		else: load_level(a["level"], args)
	else:
		to_title()

## debug / test helpers: --shot=/path.png@seconds  --tp=x,y,z,yaw  --do=method@seconds
func _debug_args() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--shot="):
			var parts := arg.substr(7).split("@")
			_shot_later(parts[0], float(parts[1]) if parts.size() > 1 else 3.0)
		elif arg.begins_with("--tp="):
			var v := arg.substr(5).split(",")
			_tp_later(Vector3(float(v[0]), float(v[1]), float(v[2])), float(v[3]) if v.size() > 3 else 0.0, float(v[4]) if v.size() > 4 else 1.5)
		elif arg.begins_with("--do="):
			var p2 := arg.substr(5).split("@")
			_do_later(p2[0], float(p2[1]) if p2.size() > 1 else 2.0)
		elif arg == "--touch":
			G.is_touch = true
		elif arg.begins_with("--hold="):   # --hold=action@start-end
			var hp := arg.substr(7).split("@"); var tt := hp[1].split("-")
			_hold_later(hp[0], float(tt[0]), float(tt[1]))
		elif arg.begins_with("--walk="):
			_walk_later(arg.substr(7))

## --walk=x,z;x,z;...  (optional 3rd value 'j' = jump at that waypoint). Starts 3 s after load,
## steers the player along the waypoints and reports STUCK / WALK DONE (headless soft-lock check).
func _walk_later(spec: String) -> void:
	await get_tree().create_timer(3.5, true, false, true).timeout
	var pts := []
	for w in spec.split(";"):
		var v := w.split(",")
		pts.append([Vector2(float(v[0]), float(v[1])), v[2] if v.size() > 2 else ""])
	if "--noenemies" in OS.get_cmdline_user_args():
		for e in get_tree().get_nodes_in_group("enemies"): e.queue_free()
	var idx := 0; var best := INF; var t_best := 0.0; var t := 0.0
	while idx < pts.size():
		await get_tree().physics_frame
		t += 1.0 / 60.0
		var p: Player = G.player
		if p == null: continue
		p.invuln = 1.0
		var tgt: Vector2 = pts[idx][0]
		var d := Vector2(p.global_position.x, p.global_position.z).distance_to(tgt)
		if d < best - 0.05: best = d; t_best = t
		if pts[idx][1] == "j" and d < 1.6 and p.is_on_floor(): Input.action_press("jump"); get_tree().create_timer(0.35).timeout.connect(func(): Input.action_release("jump"))
		if pts[idx][1] == "r" and d < 3.2 and p.is_on_floor() and p.roll_t <= 0.0: Input.action_press("roll"); await get_tree().physics_frame; Input.action_release("roll")
		if d < 0.7:
			if pts[idx][1] == "w":
				p.auto_move = Vector3.ZERO
				await get_tree().create_timer(5.0).timeout
				t += 5.0
			if "--walkv" in OS.get_cmdline_user_args(): print("  wp ", idx, " reached at ", p.global_position.snapped(Vector3.ONE * 0.1))
			idx += 1; best = INF; t_best = t
			continue
		var dir := Vector3(tgt.x - p.global_position.x, 0, tgt.y - p.global_position.z).normalized()
		p.auto_move = dir
		if t - t_best > 4.0:
			print("WALK STUCK at ", p.global_position.snapped(Vector3.ONE * 0.1), " heading to wp ", idx, " ", tgt, " floor=", p.is_on_floor())
			p.auto_move = Vector3.ZERO
			return
	G.player.auto_move = Vector3.ZERO
	print("WALK DONE at ", G.player.global_position.snapped(Vector3.ONE * 0.1), " t=", snappedf(t, 0.1))

func _shot_later(path: String, t: float) -> void:
	await get_tree().create_timer(t, true, false, true).timeout
	var img := get_viewport().get_texture().get_image()
	img.save_png(path)
	print("SHOT ", path)

func _tp_later(p: Vector3, yaw: float, t: float) -> void:
	await get_tree().create_timer(t, true, false, true).timeout
	if G.player: G.player.teleport(p, yaw)
	if G.level: G.level.cp_pos = p; G.level.cp_yaw = yaw

func _do_later(m: String, t: float) -> void:
	await get_tree().create_timer(t, true, false, true).timeout
	var parts := m.split(":")
	var target: Object = G.level
	if parts[0] == "player": target = G.player; parts.remove_at(0)
	elif parts[0] == "main": target = self; parts.remove_at(0)
	elif parts[0] == "ui": target = G.ui; parts.remove_at(0)
	if target and target.has_method(parts[0]):
		if parts.size() > 1: target.callv(parts[0], parts.slice(1))
		else: target.call(parts[0])
	print("DO ", m)

func _on_resize() -> void:
	var s := get_viewport().get_visible_rect().size
	var win := DisplayServer.window_get_size()
	if win.y > win.x:
		get_tree().root.content_scale_size = Vector2i(720, 1280)
	else:
		get_tree().root.content_scale_size = Vector2i(1280, 720)

func _setup_input() -> void:
	var map := {
		"move_fwd": [KEY_W, KEY_UP], "move_back": [KEY_S, KEY_DOWN], "move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT],
		"jump": [KEY_SPACE], "roll": [KEY_SHIFT, KEY_C, KEY_CTRL], "pulse": [KEY_Q], "interact": [KEY_E, KEY_F], "walk": [KEY_ALT],
		"pause": [KEY_ESCAPE, KEY_P], "skip": [KEY_TAB, KEY_BACKSPACE], "advance": [KEY_SPACE, KEY_ENTER, KEY_KP_ENTER],
	}
	for a in map:
		if not InputMap.has_action(a): InputMap.add_action(a, 0.25)
		for k in map[a]:
			var e := InputEventKey.new(); e.physical_keycode = k; InputMap.action_add_event(a, e)
	for a in ["fire", "aim", "look_left", "look_right", "look_up", "look_down"]:
		if not InputMap.has_action(a): InputMap.add_action(a, 0.15)
	var mb := InputEventMouseButton.new(); mb.button_index = MOUSE_BUTTON_LEFT; InputMap.action_add_event("fire", mb)
	var mb2 := InputEventMouseButton.new(); mb2.button_index = MOUSE_BUTTON_RIGHT; InputMap.action_add_event("aim", mb2)
	# gamepad
	var pads := {"jump": JOY_BUTTON_A, "roll": JOY_BUTTON_B, "interact": JOY_BUTTON_X, "pulse": JOY_BUTTON_Y, "pause": JOY_BUTTON_START, "skip": JOY_BUTTON_BACK, "advance": JOY_BUTTON_A}
	for a in pads:
		var j := InputEventJoypadButton.new(); j.button_index = pads[a]; InputMap.action_add_event(a, j)
	var lb := InputEventJoypadButton.new(); lb.button_index = JOY_BUTTON_LEFT_SHOULDER; InputMap.action_add_event("pulse", lb)
	var axes := {"move_left": [JOY_AXIS_LEFT_X, -1.0], "move_right": [JOY_AXIS_LEFT_X, 1.0], "move_fwd": [JOY_AXIS_LEFT_Y, -1.0], "move_back": [JOY_AXIS_LEFT_Y, 1.0],
		"look_left": [JOY_AXIS_RIGHT_X, -1.0], "look_right": [JOY_AXIS_RIGHT_X, 1.0], "look_up": [JOY_AXIS_RIGHT_Y, -1.0], "look_down": [JOY_AXIS_RIGHT_Y, 1.0],
		"fire": [JOY_AXIS_TRIGGER_RIGHT, 1.0], "aim": [JOY_AXIS_TRIGGER_LEFT, 1.0]}
	for a in axes:
		var j2 := InputEventJoypadMotion.new(); j2.axis = axes[a][0]; j2.axis_value = axes[a][1]; InputMap.action_add_event(a, j2)

func _unhandled_input(e: InputEvent) -> void:
	if e.is_action_pressed("pause") and level and level.get("player") and not loading:
		if level.in_cs and not G.paused:
			G.ui.request_skip()
			return
		toggle_pause()

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and level and level.get("player") and not G.paused and not loading and not G.bench:
		if not level.in_cs: toggle_pause()

func toggle_pause() -> void:
	if level == null or level.get("player") == null: return
	G.paused = not G.paused
	get_tree().paused = G.paused
	if G.paused:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		G.ui.touch.release_all()
		G.ui.show_pause()
		Audio.vo_player.stream_paused = true
	else:
		G.ui._hide_menus()
		Audio.vo_player.stream_paused = false
		if not G.is_touch: Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func to_title() -> void:
	G.paused = false; get_tree().paused = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	await load_level("world", {"title": true})
	G.ui.show_hud(false)
	G.ui.show_title()
	Audio.music("title")
	Audio.ambience("")
	G.ui.fade(0.0, 1.0)

func new_game() -> void:
	G.new_game()
	G.ui._hide_menus()
	if not G.is_touch: Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	load_level("lab", {})

func continue_game() -> void:
	G.ui._hide_menus()
	if not G.is_touch: Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	var cp: String = G.save["checkpoint"]
	if cp == "lab" or cp == "": load_level("lab", {})
	elif cp == "finale": load_level("lab", {"ending": true})
	else: load_level("world", {"cp": cp})

func load_level(name: String, args := {}) -> void:
	while loading: await get_tree().process_frame   # serialize overlapping loads (e.g. a fail-safe recover firing mid-transition)
	loading = true
	G.ui.skip_req = false
	G.ui.letterbox(false, 0.01)
	G.ui.cutscene_on = false
	G.ui.clear_sub()
	G.ui.objective("")
	G.ui.set_waypoint(null)
	G.ui.boss(false)
	G.ui.show_timer(-1)
	Audio.stop_vo()
	if G.ui.fade_rect.color.a < 0.99:
		await G.ui.fade(1.0, 0.4)
	G.ui.show_loading(true, 0.0, "Loading the twenty-first century..." if name == "lab" else ("Loading 1283..." if not args.get("title", false) else "Warming up the time machine..."))
	await get_tree().process_frame
	if level:
		level.queue_free(); level = null; G.level = null; G.player = null
		await get_tree().process_frame
	var path := "res://assets/models/%s.glb" % ("lab" if name == "lab" else "world")
	ResourceLoader.load_threaded_request(path)
	while true:
		var prog := []
		var st := ResourceLoader.load_threaded_get_status(path, prog)
		G.ui.show_loading(true, prog[0] if prog.size() else 0.5)
		if st == ResourceLoader.THREAD_LOAD_LOADED or st == ResourceLoader.THREAD_LOAD_FAILED or st == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE: break
		await get_tree().process_frame
	ResourceLoader.load_threaded_get(path)
	G.ui.show_loading(true, 1.0)
	await get_tree().process_frame
	var lv: Node3D = Node3D.new()
	lv.set_script(load("res://scripts/%s.gd" % ("lab" if name == "lab" else "world")))
	lv.set("args", args)
	level = lv
	level_holder.add_child(lv)
	G.ui.show_loading(false)
	loading = false

func _hold_later(action: String, t0: float, t1: float) -> void:
	await get_tree().create_timer(t0, true, false, true).timeout
	Input.action_press(action)
	await get_tree().create_timer(t1 - t0, true, false, true).timeout
	Input.action_release(action)
