class_name TouchPad
extends Control
## On-screen touch controls: floating move stick (left), drag-to-look (right), action buttons.

var stick_id := -1
var stick_origin := Vector2.ZERO
var stick_pos := Vector2.ZERO
var look_id := -1
var look_last := Vector2.ZERO
var fire_id := -1
var fire_last := Vector2.ZERO
var btn_ids := {}
var buttons := {}   # name -> {pos, r, label}
var use_visible := false
var pulse_frac := 1.0
var cutscene := false
var scale_f := 1.0
var font: Font

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	font = ThemeDB.fallback_font
	resized.connect(_layout)
	_layout()

func _layout() -> void:
	var s := size
	scale_f = clamp(min(s.x, s.y) / 720.0, 0.7, 1.6)
	var r := 62.0 * scale_f
	var br := s - Vector2(110, 120) * scale_f
	buttons = {
		"fire": {"pos": br, "r": r * 1.25, "label": "FIRE"},
		"jump": {"pos": br + Vector2(-150, 40) * scale_f, "r": r * 0.85, "label": "JUMP"},
		"roll": {"pos": br + Vector2(-60, -150) * scale_f, "r": r * 0.75, "label": "ROLL"},
		"pulse": {"pos": br + Vector2(-190, -100) * scale_f, "r": r * 0.75, "label": "PULSE"},
		"use": {"pos": br + Vector2(-110, -260) * scale_f, "r": r * 0.8, "label": "USE"},
		"pause": {"pos": Vector2(s.x * 0.5, 44 * scale_f), "r": 34 * scale_f, "label": "II"},
	}
	queue_redraw()

func _hit_button(p: Vector2) -> String:
	for k in buttons:
		if k == "use" and not use_visible: continue
		if cutscene and k != "pause": continue
		if p.distance_to(buttons[k]["pos"]) < buttons[k]["r"] * 1.15: return k
	return ""

func _input(e: InputEvent) -> void:
	if not visible: return
	if e is InputEventScreenTouch:
		G.is_touch = true
		if e.pressed:
			if cutscene:
				if _hit_button(e.position) == "pause": G.main.toggle_pause()
				else: G.ui.request_skip()
				return
			if G.paused: return
			var b := _hit_button(e.position)
			if b != "":
				btn_ids[e.index] = b
				_press(b, true)
				if b == "fire": fire_id = e.index; fire_last = e.position
			elif e.position.x < size.x * 0.42 and stick_id == -1:
				stick_id = e.index; stick_origin = e.position; stick_pos = e.position
			elif look_id == -1:
				look_id = e.index; look_last = e.position
		else:
			if btn_ids.has(e.index):
				_press(btn_ids[e.index], false); btn_ids.erase(e.index)
			if e.index == stick_id:
				stick_id = -1
				if G.player: G.player.touch_move = Vector2.ZERO
			if e.index == look_id: look_id = -1
			if e.index == fire_id: fire_id = -1
		queue_redraw()
		get_viewport().set_input_as_handled()
	elif e is InputEventScreenDrag:
		if cutscene or G.paused: return
		if e.index == stick_id:
			stick_pos = e.position
			var d: Vector2 = (stick_pos - stick_origin)
			var maxr := 70.0 * scale_f
			if d.length() > maxr: stick_origin = stick_pos - d.normalized() * maxr; d = d.normalized() * maxr
			if G.player: G.player.touch_move = d / maxr
			queue_redraw()
		elif e.index == look_id or e.index == fire_id:
			var last := look_last if e.index == look_id else fire_last
			var delta: Vector2 = e.position - last
			if G.player: G.player.touch_look += delta * (1.0 / scale_f)
			if e.index == look_id: look_last = e.position
			else: fire_last = e.position
		get_viewport().set_input_as_handled()

func _press(b: String, on: bool) -> void:
	match b:
		"fire":
			if G.player: G.player.touch_fire = on
		"jump": _act("jump", on)
		"roll": _act("roll", on)
		"pulse": _act("pulse", on)
		"use": _act("interact", on)
		"pause":
			if on: G.main.toggle_pause()

func _act(a: String, on: bool) -> void:
	if on: Input.action_press(a)
	else: Input.action_release(a)

func release_all() -> void:
	for i in btn_ids: _press(btn_ids[i], false)
	btn_ids.clear(); stick_id = -1; look_id = -1; fire_id = -1
	if G.player: G.player.touch_move = Vector2.ZERO; G.player.touch_fire = false

func _process(_dt: float) -> void:
	if G.player:
		var pf: float = 1.0 - G.player.pulse_cd / Player.PULSE_CD
		if abs(pf - pulse_frac) > 0.01: pulse_frac = pf; queue_redraw()

func _draw() -> void:
	var cyan := Color(0.35, 1.0, 0.85)
	for k in buttons:
		if k == "use" and not use_visible: continue
		if cutscene and k != "pause": continue
		var b: Dictionary = buttons[k]
		var pressed: bool = k in btn_ids.values()
		draw_circle(b["pos"], b["r"], Color(0.05, 0.08, 0.1, 0.45 if not pressed else 0.7))
		draw_arc(b["pos"], b["r"], 0, TAU, 40, Color(cyan, 0.75 if not pressed else 1.0), 3.0 * scale_f, true)
		if k == "pulse" and pulse_frac < 1.0:
			draw_arc(b["pos"], b["r"] - 6 * scale_f, -PI / 2, -PI / 2 + TAU * pulse_frac, 40, Color(1, 0.8, 0.3, 0.9), 5 * scale_f, true)
		var fs := int(20 * scale_f) if k != "fire" else int(26 * scale_f)
		var tw := font.get_string_size(b["label"], HORIZONTAL_ALIGNMENT_CENTER, -1, fs)
		draw_string(font, b["pos"] - Vector2(tw.x / 2, -fs * 0.35), b["label"], HORIZONTAL_ALIGNMENT_CENTER, -1, fs, Color(1, 1, 1, 0.9))
	if stick_id != -1:
		draw_circle(stick_origin, 70 * scale_f, Color(0.05, 0.08, 0.1, 0.35))
		draw_arc(stick_origin, 70 * scale_f, 0, TAU, 40, Color(cyan, 0.5), 2.0 * scale_f, true)
		draw_circle(stick_pos, 30 * scale_f, Color(cyan, 0.6))
	elif not cutscene:
		var hint := Vector2(150, size.y - 150) * Vector2(scale_f, 1)
		hint.y = size.y - 150 * scale_f
		draw_arc(hint, 60 * scale_f, 0, TAU, 40, Color(1, 1, 1, 0.15), 2.0, true)
		var fs2 := int(16 * scale_f)
		var t2 := font.get_string_size("MOVE", HORIZONTAL_ALIGNMENT_CENTER, -1, fs2)
		draw_string(font, hint - Vector2(t2.x / 2, -fs2 * 0.35), "MOVE", HORIZONTAL_ALIGNMENT_CENTER, -1, fs2, Color(1, 1, 1, 0.3))
