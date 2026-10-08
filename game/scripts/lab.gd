extends Level
## 2026: Juno's hacker-lab bedroom. Intro (with free exploration + easter eggs) and the epilogue.

var args := {}
var lab: Node3D
var holo: Node3D
var phone_prop: Node3D
var cat: Actor
var vacuum: Node3D
var vac_t := 0.0
var juno_npc: Actor
var screen_ui: Control
var chicken: Animal

func _ready() -> void:
	G.level = self
	lab = load("res://assets/models/lab.glb").instantiate()
	add_child(lab)
	MatLib.apply(lab, true)
	collect_markers(lab)
	for b in lab.find_children("*", "StaticBody3D", true, false): b.collision_layer = 1
	setup_env(Color(0.02, 0.02, 0.05), Color(0.08, 0.06, 0.14), Color(0.02, 0.02, 0.03), Color(0.5, 0.6, 1.0), 0.15, Vector3(-40, 30, 0), Color(0.05, 0.05, 0.1), 0.0, 0.35)
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color(0.01, 0.01, 0.02)
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.32, 0.3, 0.45)
	env.environment.ambient_light_energy = 0.6
	sun.shadow_enabled = false
	_lights()
	_props()
	_interactables()
	if args.get("ending", false):
		spawn_player(mpos("M-start"), PI * 0.1, false)
		ending()
	else:
		spawn_player(mpos("M-start"), myaw("M-start"), false)
		intro()

func _lights() -> void:
	var spec := {"M-light-desk": [Color(0.55, 0.85, 1.0), 2.2, 5.0], "M-light-bed": [Color(1.0, 0.55, 0.3), 1.6, 4.0],
		"M-light-main": [Color(0.75, 0.55, 1.0), 1.4, 9.0], "M-light-rack": [Color(0.3, 1.0, 0.6), 1.2, 3.5]}
	for k in spec:
		if not markers.has(k): continue
		var l := OmniLight3D.new()
		add_child(l); l.global_position = mpos(k)
		l.light_color = spec[k][0]; l.light_energy = spec[k][1]; l.omni_range = spec[k][2]
		l.shadow_enabled = k == "M-light-main" and G.settings["quality"] >= 1
	# neon strip glow + window moonlight
	var wl := SpotLight3D.new(); add_child(wl)
	wl.global_position = Vector3(4.6, 2.6, 0.0); wl.light_color = Color(0.5, 0.6, 1.0); wl.light_energy = 2.0; wl.spot_range = 9; wl.spot_angle = 50
	wl.look_at_from_position(wl.global_position, Vector3(0, 0, 0))

func _props() -> void:
	# SIBYL hologram
	holo = Node3D.new(); add_child(holo); holo.global_position = mpos("M-sibyl")
	var core := MeshInstance3D.new(); var sm := SphereMesh.new(); sm.radius = 0.16; sm.height = 0.32; sm.radial_segments = 16; sm.rings = 8
	core.mesh = sm; core.material_override = FX.add_mat(Color(0.75, 0.55, 1.0), false); holo.add_child(core)
	for i in 3:
		var r := MeshInstance3D.new(); var tm := TorusMesh.new(); tm.inner_radius = 0.26 + i * 0.07; tm.outer_radius = 0.28 + i * 0.07
		r.mesh = tm; r.material_override = FX.add_mat(Color(0.5, 0.8, 1.0, 0.7), false); r.name = "ring%d" % i
		r.rotation = Vector3(randf() * PI, randf() * PI, 0); holo.add_child(r)
	var hl := OmniLight3D.new(); hl.light_color = Color(0.7, 0.5, 1.0); hl.light_energy = 1.4; hl.omni_range = 3.5; holo.add_child(hl)
	talkers["sibyl"] = null
	# phone on its dock
	phone_prop = Actor.prop("P-phone"); add_child(phone_prop)
	phone_prop.global_position = mpos("M-phone"); phone_prop.rotation.y = myaw("M-phone")
	phone_prop.scale = Vector3.ONE * 1.4
	# Pixel the cat, asleep on the cat tree
	cat = Actor.make("cat"); add_child(cat)
	cat.global_position = mpos("M-an-cat-lab"); cat.rotation.y = myaw("M-an-cat-lab") + PI
	cat.play("sleep")
	# robot vacuum
	if lab.find_child("X-vacuum", true, false):
		vacuum = lab.find_child("X-vacuum", true, false)

func _interactables() -> void:
	var prompts := {"monitor0": "Read code", "monitor1": "Check map", "monitor2": "Look at SIBYL's screen", "mug": "Inspect mug", "server": "Touch server",
		"printer": "Check 3D printer", "scope": "Read oscilloscope", "bed": "Sleep?", "poster": "Read poster", "steve": "Read business card",
		"cat": "Pet Pixel", "door": "Open door", "whiteboard": "Read whiteboard", "fridge": "Open fridge", "books": "Browse books",
		"ring": "Inspect prototype", "plant": "Talk to plant", "vacuum": "Inspect robot vacuum", "sibyl": "Talk to SIBYL"}
	for k in markers.keys():
		if not k.begins_with("M-it-"): continue
		var id: String = k.substr(5)
		var it := Interactable.new()
		add_child(it); it.global_position = mpos(k)
		if id == "phone":
			it.prompt = "Take T-PORT phone"; it.secret = false
			it.action = func(_n): phone_cutscene()
			it.radius = 2.6
			it.name = "PhoneInteract"
			continue
		it.prompt = prompts.get(id, "Look")
		it.line = "i_" + id
		if id == "cat":
			it.action = func(_n): cat.play("purr"); Audio.sfx3("purr", cat.global_position); say_line("i_cat"); _after(3.0, func(): cat.play("sleep"))
		elif id == "vacuum":
			it.action = func(_n): vac_t += 3.0; say_line("i_vacuum")
		elif id == "printer":
			it.action = func(_n): Audio.sfx3("gear", it.global_position, -6); say_line("i_printer")
		elif id == "server":
			it.action = func(_n): Audio.sfx3("hitmark", it.global_position, -6); say_line("i_server")

func _after(t: float, cb: Callable) -> void:
	await get_tree().create_timer(t).timeout
	cb.call()

func _process(dt: float) -> void:
	super._process(dt)
	if holo:
		holo.position.y = mpos("M-sibyl").y + sin(Time.get_ticks_msec() * 0.002) * 0.05
		for i in 3:
			var r := holo.get_node_or_null("ring%d" % i)
			if r: r.rotate_object_local(Vector3(0, 1, 0).rotated(Vector3.RIGHT, i), dt * (0.8 + i * 0.5))
	if vacuum:
		vac_t += dt * 0.4
		vacuum.position = Vector3(1.6 + sin(vac_t) * 1.2, vacuum.position.y, 0.6 + sin(vac_t * 2.0) * 0.8)
		vacuum.rotation.y = -vac_t

# ------------------------------------------------------------------ intro
func intro() -> void:
	G.ui.show_hud(true)
	Audio.music("lab")
	Audio.ambience("amb_lab")
	player.global_position = Vector3(0.0, 0.0, -2.0)
	player.set_view(0.0)
	player.actor.play("type")
	cs_begin()
	G.ui.fade_rect.color.a = 1.0
	shot(mpos("M-cam-wide"), Vector3(0, 1.0, -1.5), 14.0, mpos("M-cam-wide") + Vector3(1.6, -0.6, -0.8), Vector3(0, 1.2, -2.5), 55)
	G.ui.fade(0.0, 1.5)
	G.ui.card("CASTLE TIME", "The Lab  -  17 October 2026, 23:51", 3.0)
	await cs_wait(2.5)
	await say("p01")
	shot(Vector3(1.2, 1.5, -0.6), Vector3(0, 1.3, -2.2), 6.0, Vector3(0.9, 1.45, -0.9), Vector3(0, 1.4, -2.2), 45)
	await say("p02")
	shot(holo.global_position + Vector3(1.2, 0.2, 1.4), holo.global_position, 10.0, holo.global_position + Vector3(-0.9, 0.3, 1.5), holo.global_position, 45)
	await say("p03")
	shot(Vector3(0.3, 1.4, -1.6), Vector3(0, 1.25, -3.0), 8.0, Vector3(-0.2, 1.35, -1.9), Vector3(0, 1.2, -3.0), 45)
	await say("p04")
	player.actor.play("excited")
	shot(Vector3(-1.0, 1.6, -0.4), player.global_position + Vector3(0, 1.4, 0), 0.0, null, null, 45)
	await say("p05")
	shot(holo.global_position + Vector3(0.0, 0.4, 2.0), holo.global_position, 6.0, holo.global_position + Vector3(0.6, 0.2, 1.6), holo.global_position, 45)
	await say("p06")
	player.actor.play("lookaround")
	shot(Vector3(-1.4, 1.5, 0.4), player.global_position + Vector3(0, 1.3, 0), 0.0, null, null, 45)
	await say("p07")
	await say("p08")
	player.actor.play("shrug")
	await say("p09")
	player.teleport(mpos("M-start") + Vector3(0, 0, -1.6), PI * 0.05)
	cs_end()
	G.ui.objective("Grab your T-PORT phone from the desk", "THE LAB  -  2026")
	G.ui.set_waypoint(mpos("M-phone") + Vector3(0, 0.3, 0))
	G.checkpoint("lab", 0)
	await wait_real(4.0)
	if not in_cs: G.ui.toast("Tip: examine things in the lab with " + ("USE" if G.is_touch else "[E]"), Color(1, 1, 1))

func phone_cutscene() -> void:
	if in_cs: return
	var it := get_node_or_null("PhoneInteract")
	if it: it.enabled = false
	cs_begin()
	G.ui.set_waypoint(null)
	player.teleport(mpos("M-phone") + Vector3(-0.6, -0.85, 0.8), 0.6)
	player.global_position.y = 0.0
	player.actor.play("pickup")
	shot(mpos("M-cam-phone"), mpos("M-phone"), 1.5, mpos("M-cam-phone") + Vector3(0.1, -0.1, -0.2), mpos("M-phone"), 40)
	await cs_wait(0.8)
	phone_prop.visible = false
	player.actor.attach("P-phone", "hand_L", Vector3(0, 0.08, 0.04), Vector3(-90, 0, 0), 1.4)
	player.actor.play("phone")
	Audio.sfx("phone_open")
	shot(player.global_position + Vector3(0.8, 1.6, -0.9), player.global_position + Vector3(0, 1.3, 0), 0.0, null, null, 45)
	await cs_wait(0.6)
	await _phone_screen()
	shot(holo.global_position + Vector3(1.0, 0.1, 1.2), holo.global_position, 0.0, null, null, 45)
	await say("p11")
	shot(player.global_position + Vector3(1.2, 1.5, 1.4), player.global_position + Vector3(0, 1.2, 0), 4.0, player.global_position + Vector3(1.6, 1.6, 2.0), player.global_position + Vector3(0, 1.2, 0), 45)
	player.equip(true)
	player.actor.play("hold")
	await say("p12")
	player.actor.play("nod")
	await say("p13")
	# teleport!
	Audio.sfx("teleport")
	player.actor.play("phone")
	var tw := create_tween()
	for i in 6:
		tw.tween_callback(func(): FX.light_pulse(player.global_position + Vector3(0, 1, 0), Color(0.4, 1.0, 0.9), 6.0, 0.25, 6.0))
		tw.tween_interval(0.15)
	if not skipping():
		for i in 3:
			FX.particles(player.global_position + Vector3(0, 1, 0), 30, Color(0.4, 1.0, 0.9), 0.8, 4.0, 0.12, 0.0)
			await cs_wait(0.35)
	player.shake(1.0)
	G.ui.flash(Color(0.8, 1.0, 1.0), 1.5)
	G.ui.fade_rect.color = Color(1, 1, 1, 0)
	await G.ui.fade(1.0, 0.25)
	G.ui.fade_rect.color = Color(1, 1, 1, 1)
	in_cs = false
	G.checkpoint("farm", 1)
	G.goto("world", {"arrive": true})

func _phone_screen() -> void:
	screen_ui = PanelContainer.new()
	var sb := StyleBoxFlat.new(); sb.bg_color = Color(0.02, 0.08, 0.07, 0.95); sb.border_color = Color(0.36, 1.0, 0.85); sb.set_border_width_all(3)
	sb.set_corner_radius_all(14); sb.set_content_margin_all(26)
	screen_ui.add_theme_stylebox_override("panel", sb)
	G.ui.root.add_child(screen_ui)
	var v := VBoxContainer.new(); screen_ui.add_child(v)
	var l: Label = G.ui.lbl("", 30, Color(0.36, 1.0, 0.85), true)
	v.add_child(l)
	screen_ui.position = Vector2(G.ui.root.size.x / 2 - 230, G.ui.root.size.y * 0.18)
	screen_ui.custom_minimum_size = Vector2(460, 300)
	var lines := ["T-PORT v2   ////   BATT 97%", "", "DATE:  17.10.1283", "TIME:  18:42", "LAT:   43.4512 N", "LON:   11.0157 E", "", "> TARGET LOCKED", "> [ ENGAGE ]"]
	var txt := ""
	Audio.vo("p10"); cur_speaker = "juno"
	G.ui.subtitle("juno", G.dialogue["p10"]["text"], G.line_dur("p10"))
	for ln in lines:
		for ch in ln:
			if skipping(): break
			txt += ch; l.text = txt
			if ch != " ": Audio.sfx("phone_key", -10, randf_range(0.9, 1.2))
			await get_tree().create_timer(0.035).timeout
		txt += "\n"; l.text = txt
		if skipping(): break
	Audio.sfx("phone_ok", -4)
	await cs_wait(max(0.6, G.line_dur("p10") - 3.6))
	screen_ui.queue_free()

# ------------------------------------------------------------------ ending
func ending() -> void:
	G.ui.show_hud(true)
	Audio.music("")
	Audio.ambience("amb_lab")
	player.equip(true)
	cs_begin()
	G.ui.fade_rect.color = Color(1, 1, 1, 1)
	player.teleport(Vector3(-0.6, 0, 0.6), PI * 0.8)
	player.actor.play("kneel")
	player.actor.attach("P-scroll", "hand_L", Vector3(0, 0.1, 0), Vector3(0, 0, 90), 1.2)
	shot(mpos("M-cam-wide"), player.global_position + Vector3(0, 1, 0), 0.0, null, null, 55)
	Audio.sfx("teleport")
	FX.particles(player.global_position + Vector3(0, 1, 0), 40, Color(0.4, 1.0, 0.9), 0.9, 5.0, 0.15, 0.0)
	G.ui.fade(0.0, 1.2)
	await cs_wait(1.6)
	G.ui.fade_rect.color = Color(0, 0, 0, 0)
	Audio.music("ending")
	player.actor.play("idle")
	shot(holo.global_position + Vector3(1.4, 0.2, 1.0), holo.global_position, 0.0, null, null, 45)
	await say("f01")
	shot(player.global_position + Vector3(0.9, 1.5, 1.4), player.global_position + Vector3(0, 1.3, 0), 5.0, player.global_position + Vector3(0.6, 1.5, 1.0), player.global_position + Vector3(0, 1.3, 0), 45)
	player.actor.play("cheer")
	await say("f02")
	player.actor.play("idle")
	shot(Vector3(0.3, 1.4, -1.6), Vector3(0, 1.25, -3.0), 0.0, null, null, 45)
	await say("f03")
	shot(player.global_position + Vector3(-1.0, 1.5, 1.2), player.global_position + Vector3(0, 1.3, 0), 0.0, null, null, 45)
	player.actor.play("think")
	await say("f04")
	shot(holo.global_position + Vector3(0, 0.3, 1.8), holo.global_position, 6.0, holo.global_position + Vector3(0.5, 0.2, 1.3), holo.global_position, 45)
	await say("f05")
	player.actor.play("excited")
	shot(player.global_position + Vector3(0.8, 1.4, 1.1), player.global_position + Vector3(0, 1.4, 0), 0.0, null, null, 40)
	await say("f06")
	await say("f07")
	player.actor.play("sit")
	shot(mpos("M-cam-wide"), player.global_position + Vector3(0, 0.8, 0), 6.0, mpos("M-cam-wide") + Vector3(0.6, 0.2, -0.6), player.global_position + Vector3(0, 0.8, 0), 50)
	await say("f08")
	await say("f09")
	await cs_wait(1.0)
	await G.ui.fade(1.0, 1.5)
	G.ui.show_hud(false)
	G.ui.clear_sub()
	G.save["flags"]["finished"] = true
	G.save_all()
	G.ui.skip_req = false
	G.ui.letterbox(false, 0.01)
	G.ui.cutscene_on = false
	G.ui.show_credits(func(): post_credits(), true)
	G.ui.fade(0.0, 0.5)

func post_credits() -> void:
	G.ui.show_hud(true)
	G.ui.fade_rect.color.a = 1.0
	cs_begin()
	chicken = Animal.new(); chicken.setup("chicken", Vector3(0.5, 0.75, -2.6), 0.0); add_child(chicken)
	chicken.set_physics_process(false)
	chicken.global_position = Vector3(0.6, 0.78, -2.75)
	player.teleport(Vector3(-0.8, 0, 0.2), PI * 0.9)
	player.actor.play("idle")
	shot(Vector3(1.4, 1.3, -1.2), Vector3(0.6, 0.9, -2.75), 6.0, Vector3(1.2, 1.2, -1.5), Vector3(0.6, 0.9, -2.75), 45)
	G.ui.fade(0.0, 0.8)
	Audio.music("")
	await cs_wait(1.0)
	await say("f10")
	player.actor.play("excited")
	shot(player.global_position + Vector3(0.8, 1.5, 1.2), player.global_position + Vector3(0, 1.4, 0), 0.0, null, null, 45)
	await say("f11")
	shot(Vector3(1.0, 1.1, -1.9), Vector3(0.6, 0.9, -2.75), 0.0, null, null, 35)
	await say("f12")
	Audio.sfx("cluck")
	await say("f13", 1.2)
	G.ui.card("THE END", "...or is it? Thanks for playing CASTLE TIME", 4.0)
	await cs_wait(5.5)
	cs_end()
	G.main.to_title()

func dbg_mats() -> void:
	for n in find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		if mi.mesh == null: continue
		for i in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(i)
			if m and m.resource_name.begins_with("D_"):
				var o := mi.get_surface_override_material(i)
				print("MAT ", mi.name, " ", m.resource_name, " -> ", o.resource_name if o else "NONE", " tex=", (o as StandardMaterial3D).albedo_texture.resource_path if o and (o as StandardMaterial3D).albedo_texture else "-")
