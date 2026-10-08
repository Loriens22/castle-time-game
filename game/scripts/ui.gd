extends CanvasLayer
## All 2D UI: HUD, subtitles, letterbox, fades, menus, touch controls.

const CYAN := Color(0.36, 1.0, 0.85)
const GOLD := Color(1.0, 0.82, 0.42)
const RED := Color(1.0, 0.35, 0.3)

var root: Control
var hud: Control
var hp_bar: ProgressBar
var heat_bar: ProgressBar
var pulse_lbl: Label
var obj_panel: PanelContainer
var obj_lbl: Label
var chapter_lbl: Label
var waypoint: Control
var wp_pos = null
var wp_lbl: Label
var cross: Control
var hit_t := 0.0
var hit_col := Color.WHITE
var prompt_lbl: Label
var sub_panel: PanelContainer
var sub_lbl: RichTextLabel
var sub_t := 0.0
var lb_top: ColorRect
var lb_bot: ColorRect
var fade_rect: ColorRect
var flash_rect: ColorRect
var vignette: ColorRect
var vig_amount := 0.0
var boss_box: VBoxContainer
var boss_bar: ProgressBar
var boss_lbl: Label
var timer_lbl: Label
var toast_box: VBoxContainer
var card_lbl: Label
var skip_lbl: Label
var touch: TouchPad
var menu_layer: Control
var title_box: Control
var pause_box: Control
var settings_box: Control
var credits_box: Control
var loading_box: Control
var loading_bar: ProgressBar
var loading_lbl: Label
var rotate_hint: Label
var theme_main: Theme
var settings_back: Callable
var touch_jump_held := false
var font_bold: FontVariation
var cutscene_on := false
var skip_req := false
var konami := []

func _ready() -> void:
	layer = 10
	process_mode = Node.PROCESS_MODE_ALWAYS
	G.ui = self
	_make_theme()
	root = Control.new(); root.set_anchors_preset(Control.PRESET_FULL_RECT); root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = theme_main
	add_child(root)
	_build_hud()
	_build_overlays()
	_build_menus()
	G.settings_changed.connect(_apply_settings)
	_apply_settings()

func _make_theme() -> void:
	theme_main = Theme.new()
	font_bold = FontVariation.new()
	font_bold.base_font = ThemeDB.fallback_font
	font_bold.variation_embolden = 0.9
	font_bold.spacing_glyph = 1
	theme_main.default_font = ThemeDB.fallback_font
	theme_main.default_font_size = 22
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.04, 0.05, 0.08, 0.72); sb.set_corner_radius_all(8); sb.set_content_margin_all(12)
	sb.border_color = Color(CYAN, 0.35); sb.set_border_width_all(1)
	theme_main.set_stylebox("panel", "PanelContainer", sb)
	var bn := StyleBoxFlat.new(); bn.bg_color = Color(0.06, 0.08, 0.12, 0.85); bn.set_corner_radius_all(6)
	bn.border_color = Color(CYAN, 0.45); bn.set_border_width_all(2); bn.content_margin_left = 24; bn.content_margin_right = 24; bn.content_margin_top = 10; bn.content_margin_bottom = 10
	var bh := bn.duplicate(); bh.bg_color = Color(0.1, 0.28, 0.26, 0.95); bh.border_color = CYAN
	var bp := bn.duplicate(); bp.bg_color = Color(0.2, 0.5, 0.45, 1.0)
	theme_main.set_stylebox("normal", "Button", bn)
	theme_main.set_stylebox("hover", "Button", bh)
	theme_main.set_stylebox("focus", "Button", bh)
	theme_main.set_stylebox("pressed", "Button", bp)
	theme_main.set_font("font", "Button", font_bold)
	theme_main.set_font_size("font_size", "Button", 26)
	theme_main.set_color("font_color", "Button", Color(0.9, 0.97, 1.0))
	theme_main.set_color("font_hover_color", "Button", Color.WHITE)
	theme_main.set_color("font_focus_color", "Button", Color.WHITE)
	var bg := StyleBoxFlat.new(); bg.bg_color = Color(0, 0, 0, 0.55); bg.set_corner_radius_all(4)
	var fg := StyleBoxFlat.new(); fg.bg_color = Color(0.3, 1.0, 0.6); fg.set_corner_radius_all(4)
	theme_main.set_stylebox("background", "ProgressBar", bg)
	theme_main.set_stylebox("fill", "ProgressBar", fg)
	theme_main.set_constant("outline_size", "Label", 6)
	theme_main.set_color("font_outline_color", "Label", Color(0, 0, 0, 0.85))
	var sl := StyleBoxFlat.new(); sl.bg_color = Color(0.2, 0.25, 0.3); sl.content_margin_top = 4; sl.content_margin_bottom = 4; sl.set_corner_radius_all(3)
	theme_main.set_stylebox("slider", "HSlider", sl)
	var ga := StyleBoxFlat.new(); ga.bg_color = Color(CYAN, 0.8); ga.content_margin_top = 4; ga.content_margin_bottom = 4; ga.set_corner_radius_all(3)
	theme_main.set_stylebox("grabber_area", "HSlider", ga)
	theme_main.set_stylebox("grabber_area_highlight", "HSlider", ga)

func lbl(text: String, size := 22, col := Color.WHITE, bold := false) -> Label:
	var l := Label.new(); l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	if bold: l.add_theme_font_override("font", font_bold)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l

func bar(col: Color, w: float, h: float) -> ProgressBar:
	var b := ProgressBar.new(); b.show_percentage = false; b.custom_minimum_size = Vector2(w, h); b.max_value = 100
	var fg := StyleBoxFlat.new(); fg.bg_color = col; fg.set_corner_radius_all(4)
	b.add_theme_stylebox_override("fill", fg)
	b.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return b

# ------------------------------------------------------------------ HUD
func _build_hud() -> void:
	hud = Control.new(); hud.set_anchors_preset(Control.PRESET_FULL_RECT); hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(hud)
	var tl := VBoxContainer.new(); tl.position = Vector2(24, 20); tl.add_theme_constant_override("separation", 6)
	hud.add_child(tl)
	var r1 := HBoxContainer.new(); tl.add_child(r1)
	r1.add_child(lbl("HP ", 18, Color(0.7, 1.0, 0.8), true))
	hp_bar = bar(Color(0.35, 1.0, 0.55), 240, 16); r1.add_child(hp_bar)
	var r2 := HBoxContainer.new(); tl.add_child(r2)
	r2.add_child(lbl("HEAT ", 14, Color(0.6, 0.9, 1.0), true))
	heat_bar = bar(CYAN, 200, 10); r2.add_child(heat_bar)
	pulse_lbl = lbl("PULSE READY [Q]", 14, GOLD, true); tl.add_child(pulse_lbl)
	# objective
	obj_panel = PanelContainer.new(); obj_panel.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	obj_panel.position = Vector2(-470, 16); obj_panel.custom_minimum_size = Vector2(450, 0); obj_panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	hud.add_child(obj_panel)
	var ov := VBoxContainer.new(); obj_panel.add_child(ov)
	chapter_lbl = lbl("", 14, GOLD, true); chapter_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; ov.add_child(chapter_lbl)
	obj_lbl = lbl("", 21, Color.WHITE); obj_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; obj_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART; ov.add_child(obj_lbl)
	obj_panel.visible = false
	# boss
	boss_box = VBoxContainer.new(); boss_box.set_anchors_preset(Control.PRESET_CENTER_TOP); boss_box.position = Vector2(-300, 120)
	boss_box.custom_minimum_size = Vector2(600, 0); boss_box.grow_horizontal = Control.GROW_DIRECTION_BOTH
	boss_lbl = lbl("SER BRUNO, THE IRON BELL", 20, GOLD, true); boss_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	boss_box.add_child(boss_lbl); boss_bar = bar(Color(1.0, 0.7, 0.2), 600, 18); boss_box.add_child(boss_bar)
	boss_box.visible = false; hud.add_child(boss_box)
	# timer
	timer_lbl = lbl("3:00", 52, RED, true); timer_lbl.set_anchors_preset(Control.PRESET_CENTER_TOP); timer_lbl.position = Vector2(-60, 84)
	timer_lbl.visible = false; hud.add_child(timer_lbl)
	# crosshair
	cross = Control.new(); cross.set_anchors_preset(Control.PRESET_CENTER); cross.mouse_filter = Control.MOUSE_FILTER_IGNORE
	cross.draw.connect(_draw_cross); hud.add_child(cross)
	# waypoint
	waypoint = Control.new(); waypoint.mouse_filter = Control.MOUSE_FILTER_IGNORE; waypoint.draw.connect(_draw_wp); hud.add_child(waypoint)
	wp_lbl = lbl("", 16, GOLD, true); waypoint.add_child(wp_lbl)
	# prompt
	prompt_lbl = lbl("", 24, Color.WHITE, true); prompt_lbl.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	prompt_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; prompt_lbl.position = Vector2(-300, -210); prompt_lbl.custom_minimum_size = Vector2(600, 30)
	prompt_lbl.grow_horizontal = Control.GROW_DIRECTION_BOTH
	hud.add_child(prompt_lbl)
	# toasts
	toast_box = VBoxContainer.new(); toast_box.position = Vector2(24, 130)
	toast_box.custom_minimum_size = Vector2(400, 0)
	root.add_child(toast_box)
	touch = TouchPad.new(); root.add_child(touch); touch.visible = false
	hud.visible = false

func _build_overlays() -> void:
	vignette = ColorRect.new(); vignette.set_anchors_preset(Control.PRESET_FULL_RECT); vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = "shader_type canvas_item; uniform float amount = 0.0; uniform vec4 col : source_color = vec4(0.8,0.05,0.05,1.0);\nvoid fragment(){ float d = distance(UV, vec2(0.5)); COLOR = vec4(col.rgb, smoothstep(0.35, 0.85, d) * amount); }"
	var sm := ShaderMaterial.new(); sm.shader = sh; vignette.material = sm
	root.add_child(vignette); root.move_child(vignette, 0)
	lb_top = ColorRect.new(); lb_top.color = Color.BLACK; lb_top.set_anchors_preset(Control.PRESET_TOP_WIDE); lb_top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	lb_bot = ColorRect.new(); lb_bot.color = Color.BLACK; lb_bot.set_anchors_preset(Control.PRESET_BOTTOM_WIDE); lb_bot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	lb_bot.grow_vertical = Control.GROW_DIRECTION_BEGIN
	root.add_child(lb_top); root.add_child(lb_bot)
	lb_top.custom_minimum_size.y = 0; lb_bot.custom_minimum_size.y = 0; lb_top.size.y = 0; lb_bot.size.y = 0
	# subtitles
	sub_panel = PanelContainer.new(); sub_panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	sub_panel.custom_minimum_size = Vector2(900, 0); sub_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH; sub_panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	sub_panel.position = Vector2(-450, -40)
	var ssb := StyleBoxFlat.new(); ssb.bg_color = Color(0, 0, 0, 0.62); ssb.set_corner_radius_all(6); ssb.set_content_margin_all(14)
	sub_panel.add_theme_stylebox_override("panel", ssb)
	sub_lbl = RichTextLabel.new(); sub_lbl.bbcode_enabled = true; sub_lbl.fit_content = true; sub_lbl.scroll_active = false
	sub_lbl.custom_minimum_size = Vector2(870, 0); sub_lbl.add_theme_font_size_override("normal_font_size", 26)
	sub_lbl.add_theme_font_override("bold_font", font_bold); sub_lbl.add_theme_font_size_override("bold_font_size", 26)
	sub_lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sub_panel.add_child(sub_lbl); sub_panel.visible = false; sub_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(sub_panel)
	card_lbl = lbl("", 54, Color.WHITE, true); card_lbl.set_anchors_preset(Control.PRESET_CENTER)
	card_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; card_lbl.custom_minimum_size = Vector2(1100, 0); card_lbl.position = Vector2(-550, -120)
	card_lbl.grow_horizontal = Control.GROW_DIRECTION_BOTH
	card_lbl.modulate.a = 0; root.add_child(card_lbl)
	skip_lbl = lbl("Hold [Enter] / tap to skip", 16, Color(1, 1, 1, 0.6)); skip_lbl.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	skip_lbl.position = Vector2(-300, -36); skip_lbl.visible = false; root.add_child(skip_lbl)
	flash_rect = ColorRect.new(); flash_rect.set_anchors_preset(Control.PRESET_FULL_RECT); flash_rect.color = Color(1, 1, 1, 0); flash_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(flash_rect)
	fade_rect = ColorRect.new(); fade_rect.set_anchors_preset(Control.PRESET_FULL_RECT); fade_rect.color = Color(0, 0, 0, 1); fade_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(fade_rect)
	rotate_hint = lbl("Tip: rotate your phone to landscape for the best experience", 26, GOLD, true)
	rotate_hint.set_anchors_preset(Control.PRESET_CENTER_TOP); rotate_hint.position = Vector2(-330, 200); rotate_hint.custom_minimum_size = Vector2(660, 0)
	rotate_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART; rotate_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; rotate_hint.visible = false
	root.add_child(rotate_hint)

func _process(dt: float) -> void:
	var p: Player = G.player
	if p and hud.visible:
		hp_bar.value = p.hp
		var hs := hp_bar.get_theme_stylebox("fill") as StyleBoxFlat
		hs.bg_color = Color(1.0, 0.3, 0.3) if p.hp < 30 else Color(0.35, 1.0, 0.55)
		heat_bar.value = p.heat
		var fs := heat_bar.get_theme_stylebox("fill") as StyleBoxFlat
		fs.bg_color = Color(1.0, 0.35, 0.2) if p.overheated > 0.0 else CYAN.lerp(Color(1.0, 0.6, 0.2), p.heat / 100.0)
		heat_bar.visible = p.weapon; pulse_lbl.visible = p.weapon
		if p.pulse_cd > 0.0: pulse_lbl.text = "PULSE  %.0f" % ceil(p.pulse_cd); pulse_lbl.modulate = Color(1, 1, 1, 0.5)
		else: pulse_lbl.text = "PULSE READY" + ("" if G.is_touch else " [Q]"); pulse_lbl.modulate = Color(1, 1, 1, 1)
		if p.overheated > 0.0: pulse_lbl.text = "OVERHEATED - VENTING"; pulse_lbl.modulate = RED
		vig_amount = max(vig_amount - dt * 1.5, (1.0 - p.hp / 45.0) * 0.6 if p.hp < 45 else 0.0)
		cross.visible = p.weapon and not cutscene_on
		touch.use_visible = p.interact_target != null
	(vignette.material as ShaderMaterial).set_shader_parameter("amount", vig_amount)
	hit_t -= dt
	cross.queue_redraw()
	waypoint.queue_redraw()
	if sub_t > 0.0:
		sub_t -= dt
		if sub_t <= 0.0: sub_panel.visible = false
	touch.visible = _touch_enabled() and hud.visible and not G.paused
	touch.cutscene = cutscene_on
	# subtitle size follows the screen
	var vs := root.size
	sub_panel.custom_minimum_size.x = min(vs.x - 40, 980)
	sub_lbl.custom_minimum_size.x = sub_panel.custom_minimum_size.x - 30
	sub_panel.size.x = sub_panel.custom_minimum_size.x
	# (absolute coordinates: 'position' ignores anchors)
	var sub_y := vs.y - sub_panel.size.y - (lb_bot.size.y * 0.55 if cutscene_on else (150.0 if touch.visible else 40.0))
	sub_panel.position = Vector2((vs.x - sub_panel.size.x) * 0.5, sub_y)
	rotate_hint.visible = G.is_touch and vs.y > vs.x and title_box.visible

func _touch_enabled() -> bool:
	var t: int = G.settings["touch_ui"]
	if t == 1: return true
	if t == 0: return false
	return G.is_touch

func _draw_cross() -> void:
	var c := Color(1, 1, 1, 0.85)
	var p: Player = G.player
	var spread := 8.0 + (p.heat * 0.06 if p else 0.0) + (6.0 if p and p.since_fire < 0.1 else 0.0)
	for d in [Vector2.RIGHT, Vector2.LEFT, Vector2.UP, Vector2.DOWN]:
		cross.draw_line(d * spread, d * (spread + 9), Color(0, 0, 0, 0.5), 4)
		cross.draw_line(d * spread, d * (spread + 9), c, 2)
	cross.draw_circle(Vector2.ZERO, 2.2, CYAN)
	if hit_t > 0.0:
		var a: float = clamp(hit_t / 0.2, 0.0, 1.0)
		for d in [Vector2(1, 1), Vector2(-1, 1), Vector2(1, -1), Vector2(-1, -1)]:
			cross.draw_line(d * 7, d * 16, Color(hit_col, a), 3)

func _draw_wp() -> void:
	wp_lbl.visible = false
	if wp_pos == null or G.player == null or cutscene_on: return
	var cam := get_viewport().get_camera_3d()
	if cam == null: return
	var p: Vector3 = wp_pos
	var vs := root.size
	var behind := cam.is_position_behind(p)
	var sp := cam.unproject_position(p)
	if behind: sp = vs - sp
	var m := 50.0
	var clamped := Vector2(clamp(sp.x, m, vs.x - m), clamp(sp.y, m + 90, vs.y - m - 60))
	if behind: clamped.y = vs.y - m - 60
	var d := G.player.global_position.distance_to(p)
	var col := Color(GOLD, 0.9)
	var pts := PackedVector2Array([clamped + Vector2(0, -12), clamped + Vector2(10, 0), clamped + Vector2(0, 12), clamped + Vector2(-10, 0)])
	waypoint.draw_colored_polygon(pts, col)
	waypoint.draw_polyline(pts + PackedVector2Array([pts[0]]), Color(0, 0, 0, 0.7), 2)
	wp_lbl.visible = true
	wp_lbl.text = "%dm" % int(d)
	wp_lbl.position = clamped + Vector2(-20, 14)

func hitmark(kind: String) -> void:
	if kind == "none": return
	hit_t = 0.2
	hit_col = {"hit": Color.WHITE, "ko": RED, "block": Color(0.6, 0.6, 0.6)}.get(kind, Color.WHITE)
	if kind == "ko": Audio.sfx("hitmark", -2, 0.8)
	elif kind == "hit": Audio.sfx("hitmark", -12)

func hurt(_from: Vector3) -> void:
	vig_amount = 0.85

func set_prompt(t: String) -> void:
	if t == "": prompt_lbl.text = ""; return
	prompt_lbl.text = ("" if G.is_touch else "[E]  ") + t

func objective(t: String, chapter := "") -> void:
	if chapter != "": chapter_lbl.text = chapter
	if t == "": obj_panel.visible = false; return
	if obj_lbl.text != t:
		obj_lbl.text = t
		obj_panel.visible = true
		obj_panel.modulate = Color(1, 1, 1, 0)
		var tw := create_tween(); tw.tween_property(obj_panel, "modulate:a", 1.0, 0.4)
		Audio.sfx("objective", -6)

func set_waypoint(p) -> void:
	wp_pos = p

func toast(t: String, col := Color.WHITE) -> void:
	var pc := PanelContainer.new()
	var l := lbl(t, 20, col, true); pc.add_child(l)
	toast_box.add_child(pc)
	pc.modulate.a = 0
	var tw := pc.create_tween()
	tw.tween_property(pc, "modulate:a", 1.0, 0.25)
	tw.tween_interval(2.8)
	tw.tween_property(pc, "modulate:a", 0.0, 0.5)
	tw.tween_callback(pc.queue_free)

func subtitle(who: String, text: String, dur: float) -> void:
	if not G.settings["subs"]: return
	var name: String = G.names.get(who, who.to_upper())
	var col: String = G.colors.get(who, "#ffffff")
	sub_lbl.text = "[b][color=%s]%s[/color][/b]  %s" % [col, name, text]
	var fs := 26
	if G.is_touch: fs = 30
	sub_lbl.add_theme_font_size_override("normal_font_size", fs); sub_lbl.add_theme_font_size_override("bold_font_size", fs)
	sub_panel.visible = true
	sub_t = dur + 0.35

func clear_sub() -> void:
	sub_panel.visible = false; sub_t = 0.0

func letterbox(on: bool, t := 0.6) -> void:
	cutscene_on = on
	skip_lbl.visible = on
	skip_lbl.text = "Tap to skip" if G.is_touch else "[Enter] Skip"
	var h := root.size.y * 0.11 if on else 0.0
	var tw := create_tween().set_parallel(true)
	tw.tween_property(lb_top, "size:y", h, t)
	tw.tween_property(lb_bot, "size:y", h, t)
	tw.tween_property(lb_bot, "position:y", root.size.y - h, t)
	for n in [obj_panel, prompt_lbl, hp_bar.get_parent().get_parent(), toast_box]:
		tw.tween_property(n, "modulate:a", 0.0 if on else 1.0, t * 0.6)
	if on: touch.release_all(); set_prompt("")

func fade(to: float, t := 0.6) -> void:
	var tw := create_tween()
	tw.tween_property(fade_rect, "color:a", to, t)
	await tw.finished

func flash(col := Color.WHITE, t := 0.6) -> void:
	flash_rect.color = col
	var tw := create_tween()
	tw.tween_property(flash_rect, "color:a", 0.0, t)

func card(text: String, sub := "", t := 3.0) -> void:
	card_lbl.text = text + ("\n[size=-]" if false else ("\n" + sub if sub != "" else ""))
	var tw := create_tween()
	tw.tween_property(card_lbl, "modulate:a", 1.0, 0.6)
	tw.tween_interval(t)
	tw.tween_property(card_lbl, "modulate:a", 0.0, 0.8)
	Audio.sfx("chapter", -4)

func boss(on: bool, frac := 1.0) -> void:
	boss_box.visible = on
	boss_bar.value = frac * 100.0

func show_timer(sec: float) -> void:
	timer_lbl.visible = sec >= 0.0
	if sec >= 0.0:
		timer_lbl.text = "%d:%02d" % [int(sec) / 60, int(sec) % 60]
		timer_lbl.modulate = Color(1, 1, 1, 1) if sec > 30 or int(sec * 4) % 2 == 0 else Color(1, 1, 1, 0.5)

func request_skip() -> void:
	skip_req = true

func show_hud(on: bool) -> void:
	hud.visible = on

func _unhandled_input(e: InputEvent) -> void:
	if cutscene_on and (e.is_action_pressed("skip") or (e is InputEventMouseButton and e.pressed and e.device != -1 and not G.is_touch)):
		skip_req = true
	if e is InputEventKey and e.pressed and not e.echo:
		konami.append(e.keycode)
		if konami.size() > 10: konami.pop_front()
		if konami == [KEY_UP, KEY_UP, KEY_DOWN, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_LEFT, KEY_RIGHT, KEY_B, KEY_A]:
			G.big_head = not G.big_head
			for a in get_tree().get_nodes_in_group("actors_all"): pass
			for n in get_tree().root.find_children("*", "Node3D", true, false):
				if n is Actor: n.set_big_head(G.big_head)
			if G.add_secret("bighead"): toast("SECRET: Big Head Mode", GOLD)
			if G.level: G.level.say_line("bk_bighead")
	if e is InputEventMouseMotion and e.device != -1 and G.settings["touch_ui"] == -1 and e.relative.length() > 0 and not DisplayServer.is_touchscreen_available():
		G.is_touch = false

# ------------------------------------------------------------------ menus
func _build_menus() -> void:
	menu_layer = Control.new(); menu_layer.set_anchors_preset(Control.PRESET_FULL_RECT); menu_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(menu_layer)
	root.move_child(menu_layer, fade_rect.get_index())
	title_box = _build_title(); menu_layer.add_child(title_box)
	pause_box = _build_pause(); menu_layer.add_child(pause_box)
	settings_box = _build_settings(); menu_layer.add_child(settings_box)
	credits_box = _build_credits(); menu_layer.add_child(credits_box)
	loading_box = _build_loading(); root.add_child(loading_box)
	for b in [title_box, pause_box, settings_box, credits_box, loading_box]: b.visible = false

func _btn(parent: Node, text: String, cb: Callable) -> Button:
	var b := Button.new(); b.text = text; b.pressed.connect(func(): Audio.sfx("ui_click", -4); cb.call())
	b.mouse_entered.connect(func(): Audio.sfx("ui_hover", -14))
	b.focus_entered.connect(func(): Audio.sfx("ui_hover", -14))
	b.custom_minimum_size = Vector2(320, 54)
	parent.add_child(b)
	return b

func _full_panel() -> Control:
	var c := Control.new(); c.set_anchors_preset(Control.PRESET_FULL_RECT)
	return c

func _build_title() -> Control:
	var c := _full_panel()
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var grad := TextureRect.new(); grad.set_anchors_preset(Control.PRESET_FULL_RECT); grad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var g := Gradient.new(); g.set_color(0, Color(0.02, 0.02, 0.05, 0.85)); g.set_color(1, Color(0.02, 0.02, 0.05, 0.0))
	var gt := GradientTexture2D.new(); gt.gradient = g; gt.fill_from = Vector2(0, 0); gt.fill_to = Vector2(0.75, 0)
	grad.texture = gt; grad.stretch_mode = TextureRect.STRETCH_SCALE
	c.add_child(grad)
	var v := VBoxContainer.new(); v.position = Vector2(80, 70); v.add_theme_constant_override("separation", 10)
	v.name = "Box"
	c.add_child(v)
	var t1 := lbl("CASTLE", 92, Color(0.95, 0.88, 0.7), true); v.add_child(t1)
	var t2 := lbl("TIME", 120, CYAN, true); v.add_child(t2)
	t2.add_theme_constant_override("outline_size", 14); t2.add_theme_color_override("font_outline_color", Color(0.0, 0.25, 0.2))
	t1.add_theme_constant_override("outline_size", 12)
	v.add_child(lbl("Rocca di Valtorre  -  17 October 1283", 22, GOLD))
	var sp := Control.new(); sp.custom_minimum_size.y = 18; v.add_child(sp)
	var bc := _btn(v, "CONTINUE", func(): G.main.continue_game())
	bc.name = "Continue"
	_btn(v, "NEW GAME", func(): G.main.new_game())
	_btn(v, "SETTINGS", func(): show_settings(func(): show_title()))
	_btn(v, "CREDITS", func(): show_credits())
	var ver := lbl("Made with Blender + Godot. Every model, texture, sound and voice generated for this game.", 15, Color(1, 1, 1, 0.55))
	ver.set_anchors_preset(Control.PRESET_BOTTOM_LEFT); ver.position = Vector2(24, -34)
	c.add_child(ver)
	return c

func show_title() -> void:
	_hide_menus()
	title_box.visible = true
	var box := title_box.get_node("Box")
	box.get_node("Continue").visible = G.has_save()
	var fb: Button = box.get_node("Continue") if G.has_save() else box.get_child(5)
	fb.grab_focus.call_deferred()
	var sc: float = clamp(root.size.y / 720.0, 0.6, 1.0) if root.size.x > root.size.y else clamp(root.size.x / 1000.0, 0.55, 1.0)
	box.scale = Vector2(sc, sc)

func _hide_menus() -> void:
	for b in [title_box, pause_box, settings_box, credits_box]: b.visible = false

func _build_pause() -> Control:
	var c := _full_panel()
	var bg := ColorRect.new(); bg.color = Color(0, 0, 0, 0.55); bg.set_anchors_preset(Control.PRESET_FULL_RECT); c.add_child(bg)
	var pc := PanelContainer.new(); pc.set_anchors_preset(Control.PRESET_CENTER); pc.grow_horizontal = Control.GROW_DIRECTION_BOTH; pc.grow_vertical = Control.GROW_DIRECTION_BOTH
	c.add_child(pc)
	var v := VBoxContainer.new(); v.add_theme_constant_override("separation", 10); pc.add_child(v)
	v.add_child(lbl("PAUSED", 40, CYAN, true))
	var stats := lbl("", 18, Color(0.85, 0.9, 1.0)); stats.name = "Stats"; v.add_child(stats)
	_btn(v, "RESUME", func(): G.main.toggle_pause()).name = "Resume"
	_btn(v, "SETTINGS", func(): show_settings(func(): show_pause()))
	_btn(v, "RESTART CHECKPOINT", func(): G.main.toggle_pause(); G.level.respawn())
	_btn(v, "QUIT TO TITLE", func(): G.main.toggle_pause(); G.main.to_title())
	var help := lbl("", 15, Color(1, 1, 1, 0.6)); help.name = "Help"; v.add_child(help)
	return c

func show_pause() -> void:
	_hide_menus()
	pause_box.visible = true
	var pc := pause_box.get_child(1)
	pc.position = root.size / 2 - pc.size / 2
	var v := pc.get_child(0)
	v.get_node("Stats").text = "Discoveries: %d    Anachronisms: %d / %d    Knock-outs: %d" % [G.save["secrets"].size(), G.save["collect"].size(), G.COLLECT_IDS.size(), G.save["kos"]]
	v.get_node("Help").text = "Touch: left = move, right = look, FIRE / JUMP / ROLL / PULSE / USE buttons" if G.is_touch else "WASD move | Mouse aim | LMB fire | RMB aim | Space jump | Shift roll | Q pulse | E use | Esc pause"
	v.get_node("Resume").grab_focus.call_deferred()

func _build_settings() -> Control:
	var c := _full_panel()
	var bg := ColorRect.new(); bg.color = Color(0, 0, 0, 0.6); bg.set_anchors_preset(Control.PRESET_FULL_RECT); c.add_child(bg)
	var pc := PanelContainer.new(); c.add_child(pc)
	var sc := ScrollContainer.new(); sc.custom_minimum_size = Vector2(620, 560); sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	pc.add_child(sc)
	var v := VBoxContainer.new(); v.add_theme_constant_override("separation", 8); v.custom_minimum_size.x = 590; sc.add_child(v)
	v.add_child(lbl("SETTINGS", 36, CYAN, true))
	for k in [["master", "Master volume"], ["music", "Music"], ["sfx", "Sound effects"], ["voice", "Voices"], ["sens", "Look sensitivity"]]:
		var h := HBoxContainer.new(); v.add_child(h)
		var l := lbl(k[1], 20); l.custom_minimum_size.x = 230; h.add_child(l)
		var s := HSlider.new(); s.min_value = 0.0 if k[0] != "sens" else 0.3; s.max_value = 1.0 if k[0] != "sens" else 2.5; s.step = 0.05
		s.custom_minimum_size = Vector2(320, 36); s.value = G.settings[k[0]]; s.name = k[0]
		var key: String = k[0]
		s.value_changed.connect(func(val): G.set_setting(key, val))
		h.add_child(s)
	for k in [["subs", "Subtitles"], ["invert", "Invert look Y"]]:
		var cb := CheckButton.new(); cb.text = k[1]; cb.button_pressed = G.settings[k[0]]; cb.name = k[0]
		var key2: String = k[0]
		cb.toggled.connect(func(on): G.set_setting(key2, on))
		cb.add_theme_font_size_override("font_size", 20)
		v.add_child(cb)
	var hq := HBoxContainer.new(); v.add_child(hq)
	var lq := lbl("Graphics quality", 20); lq.custom_minimum_size.x = 230; hq.add_child(lq)
	var q := OptionButton.new(); q.name = "quality"
	for o in ["Low (fast)", "Medium", "High"]: q.add_item(o)
	q.selected = G.settings["quality"]; q.item_selected.connect(func(i): G.set_setting("quality", i)); hq.add_child(q)
	var ht := HBoxContainer.new(); v.add_child(ht)
	var lt := lbl("Touch controls", 20); lt.custom_minimum_size.x = 230; ht.add_child(lt)
	var t := OptionButton.new(); t.name = "touch"
	for o in ["Auto", "Off", "On"]: t.add_item(o)
	t.selected = {-1: 0, 0: 1, 1: 2}[int(G.settings["touch_ui"])]
	t.item_selected.connect(func(i): G.set_setting("touch_ui", [-1, 0, 1][i])); ht.add_child(t)
	var bk := _btn(v, "BACK", func(): settings_back.call())
	bk.name = "Back"
	return c

func show_settings(back: Callable) -> void:
	_hide_menus()
	settings_back = back
	settings_box.visible = true
	var pc: Control = settings_box.get_child(1)
	var sc: ScrollContainer = pc.get_child(0)
	sc.custom_minimum_size = Vector2(min(620.0, root.size.x - 40), min(560.0, root.size.y - 40))
	pc.reset_size()
	pc.position = root.size / 2 - pc.get_combined_minimum_size() / 2
	(sc.get_child(0).get_node("Back") as Button).grab_focus.call_deferred()

func _build_credits() -> Control:
	var c := _full_panel()
	var bg := ColorRect.new(); bg.color = Color(0.01, 0.01, 0.03, 0.96); bg.set_anchors_preset(Control.PRESET_FULL_RECT); c.add_child(bg)
	var l := RichTextLabel.new(); l.bbcode_enabled = true; l.fit_content = true; l.name = "Roll"
	l.custom_minimum_size = Vector2(900, 0); l.add_theme_font_size_override("normal_font_size", 24)
	l.add_theme_font_override("bold_font", font_bold); l.add_theme_font_size_override("bold_font_size", 30)
	l.scroll_active = false
	l.text = """[center][b][color=#5ff5d8]CASTLE TIME[/color][/b]
a time-travel laser adventure


[b][color=#ffcf6b]STARRING[/color][/b]
Juno  -  time traveller, hoodie enthusiast
SIBYL  -  an AI with opinions
Maestro Lorenzo Vinciguerra  -  inventor, two centuries early
Ser Bruno, the Iron Bell  -  very shiny
Count Ottone  -  terrible at trebuchets
Grimaldo the jailer, Beppe the prisoner, Bartolo and the good people of Valtorre
Pixel the cat, and a chicken with a credit card


[b][color=#ffcf6b]MADE WITH[/color][/b]
Godot Engine 4 (MIT)  -  game engine
Blender  -  every 3D model, character, rig and animation, built by script
Kokoro TTS (Apache 2.0)  -  every voice, generated locally
Procedural Python synthesis  -  every sound effect and music track
Procedural Python  -  every texture, sketch and poster


[b][color=#ffcf6b]NO HARM DONE[/color][/b]
Nobody was hurt in 1283. The blaster only stuns.
Animals were startled, never harmed.
The castle had excellent insurance.


[b][color=#ffcf6b]SPECIAL THANKS[/color][/b]
Steve's PC Repair (other jobs: 100% up-front)
Gerald the plant
You, for playing


[b][color=#5ff5d8]Thanks for playing![/color][/b]

[/center]"""
	c.add_child(l)
	var b := Button.new(); b.text = "BACK"; b.name = "Back"; b.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT); b.position = Vector2(-200, -80)
	b.pressed.connect(func(): credits_done())
	c.add_child(b)
	return c

var credits_tw: Tween
var credits_cb: Callable
func show_credits(cb := Callable(), auto := false) -> void:
	_hide_menus()
	credits_cb = cb
	credits_box.visible = true
	var l: RichTextLabel = credits_box.get_node("Roll")
	l.custom_minimum_size.x = min(900.0, root.size.x - 40)
	l.position = Vector2(root.size.x / 2 - l.custom_minimum_size.x / 2, root.size.y)
	if credits_tw: credits_tw.kill()
	credits_tw = create_tween()
	credits_tw.tween_property(l, "position:y", -1300.0, 38.0)
	if auto: credits_tw.tween_callback(credits_done)
	(credits_box.get_node("Back") as Button).grab_focus.call_deferred()

func credits_done() -> void:
	if credits_tw: credits_tw.kill()
	credits_box.visible = false
	if credits_cb.is_valid():
		var cb := credits_cb; credits_cb = Callable(); cb.call()
	else: show_title()

func _build_loading() -> Control:
	var c := _full_panel()
	var bg := ColorRect.new(); bg.color = Color(0.02, 0.02, 0.04); bg.set_anchors_preset(Control.PRESET_FULL_RECT); c.add_child(bg)
	var v := VBoxContainer.new(); v.set_anchors_preset(Control.PRESET_CENTER); v.position = Vector2(-260, -40); v.custom_minimum_size = Vector2(520, 0)
	v.grow_horizontal = Control.GROW_DIRECTION_BOTH
	c.add_child(v)
	loading_lbl = lbl("Calibrating chrono-resonator...", 22, CYAN, true); loading_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(loading_lbl)
	loading_bar = bar(CYAN, 520, 14); v.add_child(loading_bar)
	var tip := lbl("", 18, Color(1, 1, 1, 0.65)); tip.name = "Tip"; tip.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART; tip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(tip)
	return c

const TIPS := ["Guards block lasers with their shields. Flank them, or use the stun PULSE to knock the shields down.",
	"Your blaster overheats. Short bursts keep it cool.",
	"Roll (Shift / ROLL) makes you briefly untouchable - and fits under low gaps.",
	"Cabbages can be shot out of the air.",
	"Look for glowing anachronisms - eight bits of the future got lost in 1283.",
	"Press E / USE near objects to examine them. Juno has opinions about everything.",
	"Food heals. Medieval food heals slightly less than you'd hope."]

func show_loading(on: bool, p := 0.0, text := "") -> void:
	loading_box.visible = on
	loading_bar.value = p * 100.0
	if text != "": loading_lbl.text = text
	if on and p == 0.0:
		(loading_box.get_child(1).get_node("Tip") as Label).text = TIPS[randi() % TIPS.size()]

func _apply_settings() -> void:
	pass
