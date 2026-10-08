extends Level
## 1283: farm -> Valtorre town -> moat -> courtyard -> clock spire -> keep -> dungeon -> burning escape.

const GROUP_STAGE := {"farm": 1, "market": 2, "green": 3, "yard": 4, "spire": 6, "hall": 8, "kitchen": 8, "dungeon": 9}
const CPS := {"farm": ["M-cp-farm", 1], "town": ["M-cp-town", 2], "green": ["M-cp-green", 3], "yard": ["M-cp-yard", 4],
	"spire": ["M-cp-spire", 5], "sp0": ["M-cp-sp0", 6], "sp1": ["M-cp-sp1", 6], "sp2": ["M-cp-sp2", 6], "spiretop": ["M-cp-spiretop", 7],
	"hall": ["M-cp-hall", 8], "dungeon": ["M-cp-dungeon", 9], "escape": ["", 10], "escape2": ["", 10]}
const ESCAPE_TIME := 180.0
const TOWER := Vector3(27, 0, -60)

var args := {}
var world: Node3D
var stage := 1
var title_mode := false
var groups := {}          # group -> Array[Enemy]
var movers := {}          # name -> Node3D (AnimatableBody3D or mesh)
var triggers := {}        # id -> AABB
var fired := {}
var chains_left := 2
var chain_targets := []
var bullseyes := {}
var boss: Boss
var boss_started := false
var escape_t := -1.0
var escape_cp_t := ESCAPE_TIME
var escape_lines := {}
var music_zone := ""
var zone_t := 0.0
var clock_t := 0.0
var gear_t := 0.0
var beams_done := {}
var maestro: Actor
var beppe: Actor
var scroll_prop: Node3D
var title_t := 0.0
var fire_nodes := []
var dormant_t := 0.0
var pig_friend: Animal
var portcullis_dropped := false
var finale_started := false

func _ready() -> void:
	G.level = self
	title_mode = args.get("title", false)
	world = load("res://assets/models/world.glb").instantiate()
	add_child(world)
	MatLib.apply(world, true)
	collect_markers(world)
	for b in world.find_children("*", "StaticBody3D", true, false): b.collision_layer = 1; b.collision_mask = 0
	setup_env(Color(0.16, 0.22, 0.42), Color(0.98, 0.62, 0.38), Color(0.15, 0.13, 0.12), Color(1.0, 0.78, 0.55), 1.35, Vector3(-18, -62, 0), Color(0.72, 0.55, 0.5), 0.0045, 0.65)
	_movers()
	if title_mode:
		_spawn_static()
		_title_cam()
		return
	var cp: String = args.get("cp", G.save["checkpoint"])
	if not CPS.has(cp): cp = "farm"
	stage = CPS[cp][1]
	_spawn_static()
	_spawn_enemies()
	_restore_state()
	var spos := _cp_pos(cp)
	spawn_player(spos[0], spos[1], true)
	cp_id = cp; cp_pos = spos[0]; cp_yaw = spos[1]
	G.ui.show_hud(true)
	if args.get("arrive", false): arrival()
	else:
		G.ui.fade(0.0, 0.8)
		if stage >= 10: start_escape(true)
		refresh_objective()
	_update_music(true)

func _cp_pos(cp: String) -> Array:
	match cp:
		"escape": return [Vector3(8, -6, -60.5), PI]
		"escape2": return [Vector3(-11, 0, -46.5), PI]
		"sp0", "sp1", "sp2": return [mpos(CPS[cp][0]) + Vector3(0, 0.3, 0), PI * 0.5]
	return [mpos(CPS[cp][0]) + Vector3(0, 0.1, 0), myaw(CPS[cp][0])]

# ------------------------------------------------------------------ construction
func _movers() -> void:
	var shapes := {
		"X-drawbridge": [[Vector3(6.2, 0.4, 6.6), Vector3(0, 0, 3.3)]],
		"X-portcullis": [[Vector3(6.2, 6.0, 0.3), Vector3(0, 3.0, 0)]],
		"X-keepdoor": [[Vector3(3.8, 4.6, 0.3), Vector3(0, 2.3, 0)]],
		"X-dungeongate": [[Vector3(3.0, 3.0, 0.3), Vector3(0, 1.5, 0)]],
		"X-cellgate": [[Vector3(3.0, 3.0, 0.3), Vector3(0, 1.5, 0)]],
		"X-clockhand": [[Vector3(0.9, 0.35, 7.6), Vector3(0, 0, -3.2)], [Vector3(1.4, 0.35, 1.4), Vector3.ZERO]],
		"X-gear0": [[Vector3(3.2, 0.35, 3.2), Vector3.ZERO]], "X-gear1": [[Vector3(3.2, 0.35, 3.2), Vector3.ZERO]], "X-gear2": [[Vector3(3.2, 0.35, 3.2), Vector3.ZERO]],
	}
	for n in world.get_children():
		var nm := String(n.name)
		if not nm.begins_with("X-"): continue
		if shapes.has(nm):
			var body := AnimatableBody3D.new()
			body.name = nm + "_body"
			body.collision_layer = 1; body.collision_mask = 0
			body.sync_to_physics = false   # (true makes Godot revert direct transform writes until a physics sync)
			var gt: Transform3D = n.global_transform
			add_child(body)
			body.global_transform = gt
			n.reparent(body, false)
			n.transform = Transform3D.IDENTITY
			for s in shapes[nm]:
				var cs := CollisionShape3D.new(); var b := BoxShape3D.new(); b.size = s[0]; cs.shape = b; cs.position = s[1]
				body.add_child(cs)
			movers[nm] = body
		else:
			movers[nm] = n
	if movers.has("X-clockhand"): movers["X-clockhand"].global_position.y = 12.35
	if "--movers" in OS.get_cmdline_user_args():
		get_tree().create_timer(2.0).timeout.connect(func():
			for k in movers: print("MOVER ", k, " ", movers[k].global_position.snapped(Vector3.ONE * 0.1), " rot ", movers[k].rotation.snapped(Vector3.ONE * 0.01)))

func _spawn_static() -> void:
	# fx
	for k in markers.keys():
		var p := mpos(k)
		if k.begins_with("M-fx-fire"): fire_nodes.append(FX.fire(self, p, 1.0, true))
		elif k.begins_with("M-fx-torch"): FX.fire(self, p, 0.45, true)
		elif k.begins_with("M-fx-candle"): FX.fire(self, p, 0.15, true)
		elif k.begins_with("M-fx-chandelier"):
			var ch := Actor.prop("P-chandelier"); add_child(ch); ch.global_position = p
			for i in 4: FX.fire(ch, p + Vector3(cos(i * PI / 2) * 0.9, 0.2, sin(i * PI / 2) * 0.9), 0.15, i == 0)
	# animals
	for k in markers.keys():
		if k.begins_with("M-an-"):
			var parts: PackedStringArray = k.split("-")
			var a := Animal.new(); a.setup(parts[2], mpos(k), myaw(k)); add_child(a)
			if parts[2] == "pig" and parts[3] == "0": pig_friend = a
	if title_mode: return
	# physics props
	for k in markers.keys():
		if k.begins_with("M-pr-"):
			var pp := PhysProp.new(); pp.setup(k.split("-")[2]); add_child(pp)
			pp.global_position = mpos(k) + Vector3(0, 0.05, 0)
		elif k.begins_with("M-pk-"):
			spawn_pickup(k.split("-")[2], mpos(k))
		elif k.begins_with("M-col-"):
			var id: String = k.split("-")[2]
			if not id in G.save["collect"]: spawn_pickup("col_" + id, mpos(k) + Vector3(0, 0.1, 0))
	if not markers.has("M-col-fidget-library") and not "fidget" in G.save["collect"]: spawn_pickup("col_fidget", Vector3(16.0, 0.3, -60.0))
	# triggers
	for k in markers.keys():
		if k.begins_with("M-tr-"):
			var m: Node3D = markers[k]
			var he: Vector3 = m.scale.abs()
			triggers[k.substr(5)] = AABB(m.global_position - he, he * 2.0)
	_interactables()
	_targets()
	# NPCs
	maestro = Actor.make("maestro"); add_child(maestro)
	maestro.global_position = mpos("M-npc-maestro"); maestro.rotation.y = myaw("M-npc-maestro"); maestro.play("write")
	talkers["maestro"] = maestro
	beppe = Actor.make("peasant"); add_child(beppe)
	beppe.global_position = mpos("M-npc-beppe"); beppe.rotation.y = myaw("M-npc-beppe"); beppe.play("sad")
	talkers["beppe"] = beppe
	scroll_prop = Actor.prop("P-scroll"); add_child(scroll_prop)
	scroll_prop.global_position = mpos("M-scroll") + Vector3(0, 0.05, 0); scroll_prop.scale = Vector3.ONE * 1.4
	var cl := OmniLight3D.new(); scroll_prop.add_child(cl); cl.light_color = Color(1.0, 0.8, 0.4); cl.light_energy = 0.8; cl.omni_range = 2.0; cl.position.y = 0.4
	# light under the Maestro's grate
	var gl := OmniLight3D.new(); add_child(gl); gl.global_position = mpos("M-it-grate") + Vector3(0, -1.2, 0); gl.light_color = Color(1.0, 0.7, 0.35); gl.light_energy = 1.5; gl.omni_range = 4
	# zipline rope
	var a := mpos("M-zip-top"); var b := mpos("M-zip-bottom") + Vector3(0, 2.4, 0)
	var rope := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 0.03; cm.bottom_radius = 0.03; cm.height = a.distance_to(b); cm.radial_segments = 5
	rope.mesh = cm; var rm := StandardMaterial3D.new(); rm.albedo_color = Color(0.45, 0.35, 0.22); rope.material_override = rm
	add_child(rope); rope.global_position = (a + b) / 2; rope.look_at(b, Vector3.UP); rope.rotate_object_local(Vector3.RIGHT, PI / 2)
	var post := MeshInstance3D.new(); var pm := CylinderMesh.new(); pm.top_radius = 0.15; pm.bottom_radius = 0.18; pm.height = 2.6
	post.mesh = pm; post.material_override = rm; add_child(post); post.global_position = mpos("M-zip-bottom") + Vector3(0, 1.3, 0)

func _interactables() -> void:
	var prompts := {"scarecrow": "Look at scarecrow", "milkstool": "Inspect stool", "tavern": "Read tavern sign", "wanted": "Read poster",
		"churchbell": "Ring the bell", "well": "Look into well", "stocks": "Inspect stocks", "anvil": "Look at the forge", "cat_town": "Pet the cat",
		"armory": "Browse weapons", "horse": "Pat the horse", "well2": "Look into well", "throne": "Look at throne", "globe": "Spin globe",
		"cauldron": "Sniff cauldron", "cat_kitchen": "Pet the cat", "dice": "Pick up dice", "skeleton": "Say hello", "flyer": "Inspect model",
		"sketch_heli": "Study sketch", "sketch_phone": "Study sketch", "sketch_clock": "Study sketch", "sketch_laser": "Study sketch",
		"sketch_traveller": "Study sketch", "sketch_trebuchet": "Study sketch", "beppe": "Talk to prisoner", "grate": "Talk to the voice",
		"dungeongate": "Use the clock key", "cellgate": "Open the Maestro's cell"}
	for k in markers.keys():
		if not k.begins_with("M-it-"): continue
		var id: String = k.substr(5)
		if id.begins_with("chain"): continue
		var it := Interactable.new(); add_child(it); it.global_position = mpos(k)
		it.name = "IT_" + id
		if id.begins_with("armour"): id = "armour"; it.prompt = "Inspect armour"
		else: it.prompt = prompts.get(id, "Look")
		it.line = "i_" + id
		match id:
			"churchbell":
				it.action = func(_n): Audio.sfx3("bell", it.global_position, 2); say_line("i_churchbell"); _alert_near(it.global_position, 25.0)
			"beppe":
				it.secret = false; it.line = ""; it.action = func(_n): _beppe_talk(); it.once = true
			"grate":
				it.secret = false; it.line = ""; it.action = func(_n): grate_talk()
			"dungeongate":
				it.secret = false; it.line = ""; it.action = func(_n): open_dungeon()
			"cellgate":
				it.secret = false; it.line = ""; it.action = func(_n): cell_scene()
			"horse":
				it.action = func(_n): Audio.sfx3("neigh", it.global_position); say_line("i_horse")
			"cat_town", "cat_kitchen":
				var lid := "i_" + id
				it.action = func(_n): Audio.sfx3("purr", it.global_position); say_line(lid)
			"well", "well2":
				var lid2 := "i_" + id
				it.action = func(_n): Audio.sfx3("splash", it.global_position, -6); say_line(lid2)
			"anvil":
				it.action = func(_n): Audio.sfx3("anvil", it.global_position); FX.sparks(it.global_position, Vector3.UP, Color(1, 0.6, 0.2), 16); say_line("i_anvil")
	# the zipline handle
	var z := Interactable.new(); add_child(z); z.global_position = mpos("M-zip-top") + Vector3(0, -1.2, 0); z.name = "IT_zip"
	z.prompt = "Ride the rope line"; z.secret = false; z.radius = 3.0; z.enabled = false
	z.action = func(_n): ride_zip()

func _alert_near(p: Vector3, r: float) -> void:
	for e in get_tree().get_nodes_in_group("enemies"):
		if e.global_position.distance_to(p) < r: e.alert(false)

func _targets() -> void:
	# drawbridge chains
	for i in 2:
		var k := "M-it-chain%d" % i
		var t := ShootTarget.make(self, mpos(k), Vector3(0.6, 3.5, 0.6), _chain_hit, "chain%d" % i)
		t.hp = 4
		chain_targets.append(t)
		var cm := MeshInstance3D.new(); var cy := CylinderMesh.new(); cy.top_radius = 0.07; cy.bottom_radius = 0.07; cy.height = 6.0; cy.radial_segments = 6
		cm.mesh = cy; var im := StandardMaterial3D.new(); im.albedo_color = Color(0.3, 0.28, 0.26); im.metallic = 0.8; im.roughness = 0.5; cm.material_override = im
		t.add_child(cm); cm.name = "Chain"
		cm.global_position = mpos(k) + Vector3(0, -0.2, 2.0)
		cm.rotation.x = -0.6
	# archery targets
	for k in markers.keys():
		if k.begins_with("M-tg-archery"):
			var t2 := ShootTarget.make(self, mpos(k), Vector3(1.2, 1.2, 0.3), _archery_hit, k)
		elif k.begins_with("M-tg-dummy"):
			ShootTarget.make(self, mpos(k), Vector3(0.7, 1.6, 0.5), _dummy_hit, k)
	# the great bell
	if movers.has("X-bell"):
		var bpos: Vector3 = movers["X-bell"].global_position + Vector3(0, 1.4, 0)
		ShootTarget.make(self, bpos, Vector3(3.2, 2.8, 3.2), _bell_hit, "bell")

func _chain_hit(t: ShootTarget, pos: Vector3) -> String:
	if t.hp <= 0: return "none"
	t.hp -= 1
	Audio.sfx3("clank", pos, 0, randf_range(0.9, 1.1))
	if t.hp <= 0:
		chains_left -= 1
		Audio.sfx3("chain_snap", pos, 2)
		FX.sparks(pos, Vector3.UP, Color(1, 0.8, 0.4), 24)
		t.get_node("Chain").visible = false
		t.collision_layer = 0
		if chains_left <= 0: drawbridge_scene()
		else: G.ui.toast("One chain down!", Color(1, 0.9, 0.6))
		return "ko"
	return "hit"

func _archery_hit(t: ShootTarget, pos: Vector3) -> String:
	var c := t.global_position
	var d := Vector2(pos.x - c.x, pos.y - c.y).length()
	Audio.sfx3("arrow_hit", pos, -4)
	if d < 0.22:
		FX.text3d(pos + Vector3(0, 0.4, 0), "BULLSEYE!", Color(1, 0.9, 0.3))
		Audio.sfx("ting", -4)
		bullseyes[t.tag] = true
		if bullseyes.size() == 3 and G.add_secret("bullseye"):
			say_line("bk_bullseye"); G.ui.toast("SECRET: Robin Hood", Color(1, 0.85, 0.3))
			spawn_pickup("roast", t.global_position + Vector3(0, -0.8, 2.0))
		return "ko"
	return "hit"

func _dummy_hit(t: ShootTarget, pos: Vector3) -> String:
	Audio.sfx3("hit_enemy", pos, -8, 1.3)
	var tw := create_tween()
	tw.tween_property(t, "rotation:z", 0.25, 0.08); tw.tween_property(t, "rotation:z", -0.15, 0.12); tw.tween_property(t, "rotation:z", 0.0, 0.15)
	return "hit"

var bell_cd := 0.0
func _bell_hit(_t: ShootTarget, pos: Vector3) -> String:
	if bell_cd > 0.0: return "block"
	bell_cd = 2.0
	Audio.sfx3("clockbell", pos, 4)
	player.shake(0.3)
	var b: Node3D = movers["X-bell"]
	var tw := create_tween(); tw.tween_property(b, "rotation:x", 0.25, 0.15); tw.tween_property(b, "rotation:x", -0.18, 0.3); tw.tween_property(b, "rotation:x", 0.0, 0.4)
	if boss and boss.active:
		var off := boss.global_position - Vector3(TOWER.x, boss.global_position.y, TOWER.z)
		if off.length() < 5.5:
			boss.bell_hit(); bell_cd = 7.0
			if not fired.has("c13"): fired["c13"] = true; bark("c13")
			return "ko"
		else:
			G.ui.toast("Lure him under the bell!", Color(1, 0.9, 0.6))
	return "hit"

func _spawn_enemies() -> void:
	for k in markers.keys():
		if not k.begins_with("M-en-"): continue
		var parts: PackedStringArray = k.split("-")
		var kind := parts[2]; var grp := parts[3]
		if GROUP_STAGE.get(grp, 99) < stage: continue
		var e := Enemy.new()
		e.setup(kind, grp, mpos(k), myaw(k))
		add_child(e)
		if not groups.has(grp): groups[grp] = []
		groups[grp].append(e)
		e.knocked_out.connect(_on_ko)

func _on_ko(e: Enemy) -> void:
	var grp := e.group
	if group_cleared(grp):
		match grp:
			"farm": farm_cleared()
			"green": green_cleared()
			"yard": yard_progress()
	elif grp == "yard":
		yard_progress()

func group_cleared(grp: String) -> bool:
	for e in groups.get(grp, []):
		if is_instance_valid(e) and not e.defeated: return false
	return true

func group_left(grp: String) -> int:
	var n := 0
	for e in groups.get(grp, []):
		if is_instance_valid(e) and not e.defeated: n += 1
	return n

func _restore_state() -> void:
	if stage >= 4:
		_bridge_down(true)
		for t in chain_targets: t.get_node("Chain").visible = false; t.collision_layer = 0
		chains_left = 0
	if stage >= 8:
		_open_keepdoor(true)
		get_node("IT_zip").enabled = false
		G.set_flag("key")
	if stage == 7:
		_spawn_boss()
	if stage >= 9: _open_gate("X-dungeongate", true); get_node("IT_dungeongate").enabled = false
	if stage >= 10:
		_open_gate("X-cellgate", true); get_node("IT_cellgate").enabled = false
		scroll_prop.visible = false
	if stage >= 5 and G.flag("grate_done"): get_node("IT_grate").enabled = false

# ------------------------------------------------------------------ per-frame logic
func _process(dt: float) -> void:
	super._process(dt)
	if title_mode: _title_update(dt); return
	if player == null: return
	bell_cd -= dt
	_animate_movers(dt)
	_check_triggers()
	zone_t -= dt
	if zone_t <= 0.0:
		zone_t = 0.5
		_update_music()
		_dormancy()
		_spire_checks()
	if escape_t >= 0.0 and not in_cs and not player.dead:
		escape_t -= dt
		G.ui.show_timer(escape_t)
		if escape_t < 90.0 and not escape_lines.has("e03"): escape_lines["e03"] = true; bark("e03")
		if escape_t < 30.0 and not escape_lines.has("e04"): escape_lines["e04"] = true; bark("e04")
		if escape_t <= 0.0:
			escape_t = 0.01
			G.ui.toast("The castle collapsed!", Color(1, 0.4, 0.3))
			FX.explosion(player.global_position + Vector3(0, 3, -2), 1.5)
			player.hp = 1; player.invuln = 0; player.damage(999)
		_escape_events()

func _animate_movers(dt: float) -> void:
	clock_t += dt
	if movers.has("X-clockhand"):
		var cyc := 19.0
		var t := fmod(clock_t, cyc)
		var phi := 0.0
		if t < 2.5: phi = 0.0
		elif t < 9.5: phi = smoothstep(0.0, 1.0, (t - 2.5) / 7.0)
		elif t < 12.0: phi = 1.0
		else: phi = 1.0 - smoothstep(0.0, 1.0, (t - 12.0) / 7.0)
		var ext := 0.26
		var ang := -ext + phi * (PI + 2.0 * ext)
		var out := Vector3(0.866, 0, 0.5)
		var dlow := Vector3(-0.5, 0, 0.866)
		var d := dlow * cos(ang) + out * sin(ang)
		movers["X-clockhand"].rotation = Vector3(0, atan2(-d.x, -d.z), 0)
	gear_t += dt
	for i in 3:
		var k := "X-gear%d" % i
		if movers.has(k): movers[k].rotation.y = gear_t * (0.55 if i % 2 == 0 else -0.55)

func _check_triggers() -> void:
	var p := player.global_position + Vector3(0, 0.5, 0)
	for id in triggers:
		if fired.has(id) and id != "moat": continue
		if triggers[id].has_point(p):
			_trigger(id)

func _trigger(id: String) -> void:
	if id != "moat": fired[id] = true
	match id:
		"moat": fall_in_moat()
		"leave_shed": if stage <= 1: peasants_scene()
		"market":
			if stage <= 2:
				set_checkpoint("town", _cp_pos("town")[0], _cp_pos("town")[1], 2); stage = 2
				_market_lines()
		"green": if stage <= 3: green_scene()
		"yard":
			if stage <= 4:
				set_checkpoint("yard", _cp_pos("yard")[0], _cp_pos("yard")[1], 4); stage = 4
				bark("b01"); refresh_objective()
				get_tree().create_timer(50.0).timeout.connect(func(): if stage == 4 and not G.flag("grate_call"): maestro_call())
		"grate": if stage == 4 and G.flag("grate_call") and not G.flag("grate_done"): grate_talk()
		"spire":
			if stage <= 5:
				set_checkpoint("spire", _cp_pos("spire")[0], _cp_pos("spire")[1], 5); stage = 5
				if not G.flag("grate_done"): G.set_flag("grate_done")
				bark("c01"); refresh_objective()
		"spiretop": if stage <= 7 and not boss_started: boss_intro()
		"hall":
			if stage <= 8 and G.flag("key"):
				set_checkpoint("hall", _cp_pos("hall")[0], _cp_pos("hall")[1], 8); stage = 8
				bark("d02"); refresh_objective()
			else: fired.erase("hall")
		"dungeon":
			if stage <= 9 and stage >= 8:
				set_checkpoint("dungeon", _cp_pos("dungeon")[0], _cp_pos("dungeon")[1], 9); stage = 9
				refresh_objective()
				get_tree().create_timer(1.5).timeout.connect(func(): bark("d04"))

func _spire_checks() -> void:
	var p := player.global_position
	if stage >= 5 and stage <= 6:
		for k in ["sp0", "sp1", "sp2"]:
			var m := mpos(CPS[k][0])
			if p.distance_to(m) < 2.6 and cp_id != k and int(k.substr(2)) >= int(cp_id.substr(2) if cp_id.begins_with("sp") else "-1"):
				stage = 6; set_checkpoint(k, _cp_pos(k)[0], _cp_pos(k)[1], 6)
		if not fired.has("c02") and p.distance_to(mpos("M-clock")) < 7.0: fired["c02"] = true; bark("c02")
		if not fired.has("c03") and movers.has("X-gear0") and p.distance_to(movers["X-gear0"].global_position) < 6.0: fired["c03"] = true; bark("c03")

func _dormancy() -> void:
	var p := player.global_position
	for e in get_tree().get_nodes_in_group("enemies"):
		var d: float = e.global_position.distance_to(p)
		var far: bool = d > 70.0 and e != boss
		e.process_mode = Node.PROCESS_MODE_DISABLED if far else Node.PROCESS_MODE_INHERIT
		e.visible = d < 110.0
	for a in get_tree().get_nodes_in_group("animals"):
		var d2: float = a.global_position.distance_to(p)
		a.process_mode = Node.PROCESS_MODE_DISABLED if d2 > 60.0 else Node.PROCESS_MODE_INHERIT
		a.visible = d2 < 90.0

func _update_music(force := false) -> void:
	var p := player.global_position
	var zone := "town"
	var amb := "amb_country"
	if escape_t >= 0.0: zone = "escape"; amb = ""
	elif boss and boss.active: zone = "boss"
	elif p.y < -2.5: zone = "dungeon"; amb = "amb_dungeon"
	elif Vector2(p.x - TOWER.x, p.z - TOWER.z).length() < 12.0 and p.y > 2.0: zone = "spire"
	else:
		var fighting := 0
		for e in get_tree().get_nodes_in_group("enemies"):
			if e.alerted and not e.defeated and e.global_position.distance_to(p) < 30.0: fighting += 1
		if fighting >= 2: zone = "battle"
		elif p.z < 5.0: zone = "spire" if p.y > 5.0 else "town"
		if p.z > 15 and p.z < 76 and abs(p.x) < 20: amb = "amb_crowd"
	if zone != music_zone or force:
		music_zone = zone
		Audio.music(zone)
	Audio.ambience(amb)

func surface_at(p: Vector3) -> String:
	if p.y < -2.5: return "stone"
	if Vector2(p.x - TOWER.x, p.z - TOWER.z).length() < 9.0 and p.y > 1.0: return "wood"
	if p.z < -49.0 and p.z > -75.0 and p.x > -25.0 and p.x < 21.0: return "stone"
	if p.y > 8.0: return "stone"
	if p.z < 6.0: return "dirt" if abs(p.x) > 3.2 else "stone"
	if p.z < 76.0 and abs(p.x) < 5.0: return "stone"
	if p.z < 76.0: return "dirt"
	return "grass"

# ------------------------------------------------------------------ objectives
func refresh_objective() -> void:
	var t := ""; var wp = null; var ch := ""
	match stage:
		1:
			ch = "VALTORRE OUTSKIRTS  -  1283"
			if not group_cleared("farm") and fired.has("leave_shed"): t = "Calm down the angry farmers (stun them!)"
			elif not fired.has("leave_shed"): t = "Sneak out from behind the shed"; wp = mpos("M-tr-leave_shed")
			else: t = "Follow the road north into Valtorre"; wp = mpos("M-tr-market")
		2: ch = "THE TOWN OF VALTORRE"; t = "Get through the market to the castle"; wp = mpos("M-tr-green")
		3:
			ch = "THE CASTLE MOAT"
			if not group_cleared("green"): t = "Get past the moat guards (%d left)" % group_left("green")
			else: t = "Shoot both drawbridge chains (%d left)" % chains_left; wp = mpos("M-it-chain0").lerp(mpos("M-it-chain1"), 0.5)
		4:
			ch = "CASTLE COURTYARD"
			if G.flag("grate_done"): t = "Climb the clock spire"; wp = mpos("M-tr-spire")
			elif G.flag("grate_call"): t = "Find the voice by the grate near the keep"; wp = mpos("M-it-grate")
			else: t = "Fight through the castle guard"
		5, 6: ch = "THE CLOCK SPIRE"; t = "Climb to the top of the spire"; wp = mpos("M-cp-spiretop")
		7:
			ch = "THE CLOCK SPIRE"
			if boss and boss.active: t = "Defeat Ser Bruno - hit his back, or ring the bell above him"
			elif G.flag("key"): t = "Ride the rope line down to the courtyard"; wp = mpos("M-zip-top")
			else: t = "Reach the top of the spire"; wp = mpos("M-cp-spiretop")
		8:
			ch = "THE KEEP"
			if cp_id == "hall": t = "Find the golden clock lock to the dungeon"; wp = mpos("M-it-dungeongate")
			else: t = "Get into the keep"; wp = mpos("M-tr-hall")
		9: ch = "THE DUNGEON"; t = "Find the Maestro's cell"; wp = mpos("M-it-cellgate")
		10:
			ch = "ESCAPE!"
			var p := player.global_position
			if p.y < -2.0: t = "Get out! Up the stairs to the great hall"; wp = Vector3(-21.5, 0.5, -60)
			elif p.z < -48.5 and p.x < 20: t = "Get out of the keep!"; wp = mpos("M-keepdoor")
			else: t = "Out through the gate and over the drawbridge!"; wp = Vector3(0, 1, 10)
	G.ui.objective(t, ch)
	G.ui.set_waypoint(wp)

# ------------------------------------------------------------------ story beats
func arrival() -> void:
	Audio.music("")
	Audio.ambience("amb_country")
	cs_begin()
	player.actor.play("crouch")
	G.ui.fade_rect.color = Color(1, 1, 1, 1)
	shot(mpos("M-cam-shed1"), player.global_position + Vector3(0, 1, 0), 6.0, mpos("M-cam-shed1") + Vector3(1.0, 0.6, 1.0), player.global_position + Vector3(0, 1.2, 0), 55)
	Audio.sfx("teleport", -2, 0.8)
	FX.particles(player.global_position + Vector3(0, 1, 0), 40, Color(0.4, 1.0, 0.9), 0.9, 5.0, 0.15, 0.0)
	FX.light_pulse(player.global_position + Vector3(0, 1, 0), Color(0.5, 1, 0.9), 8, 1.0, 10)
	var chick := get_tree().get_nodes_in_group("animals").filter(func(a): return a.kind == "chicken")
	for c in chick:
		if c.global_position.distance_to(player.global_position) < 6: c.scare(player.global_position)
	await G.ui.fade(0.0, 1.2)
	G.ui.fade_rect.color = Color(0, 0, 0, 0)
	G.ui.card("VALTORRE, TUSCANY", "17 October 1283  -  suppertime", 3.0)
	await cs_wait(1.5)
	player.actor.play("lookaround")
	await say("a01")
	Audio.music("town")
	await say("a02")
	cs_end()
	G.checkpoint("farm", 1)
	refresh_objective()

func peasants_scene() -> void:
	cs_begin()
	var farm: Array = groups.get("farm", [])
	for e in farm: e.scripted = true
	if farm.size() > 1:
		farm[0].global_position = player.global_position + Vector3(2.0, 0, -6.0)
		farm[1].global_position = player.global_position + Vector3(-2.0, 0, -6.5)
		for e in [farm[0], farm[1]]:
			var to: Vector3 = player.global_position - e.global_position
			e.face = atan2(-to.x, -to.z); e.actor.rotation.y = e.face
		talkers["peasant"] = farm[0].actor; talkers["peasantf"] = farm[1].actor
	player.set_view(PI * 0.0)
	var mid := player.global_position + Vector3(0, 1.4, -3.0)
	shot(mpos("M-cam-shed2"), farm[0].global_position + Vector3(0, 1.5, 0) if farm.size() else mid, 0.0, null, null, 45)
	if farm.size(): farm[0].actor.play("point")
	await say("a03")
	if farm.size() > 1: farm[1].actor.play("excited")
	await say("a04")
	shot(player.global_position + Vector3(-1.2, 1.6, -2.4), player.global_position + Vector3(0, 1.4, 0), 0.0, null, null, 45)
	player.actor.play("wave")
	await say("a05")
	shot(mpos("M-cam-shed2"), farm[0].global_position + Vector3(0, 1.5, 0) if farm.size() else mid, 0.0, null, null, 40)
	if farm.size(): farm[0].actor.play("taunt")
	await say("a06")
	player.actor.play("shrug")
	shot(player.global_position + Vector3(1.4, 1.7, 2.2), player.global_position + Vector3(0, 1.3, -2), 0.0, null, null, 50)
	await say("a07")
	player.actor.play("hold")
	await say("a08")
	for e in farm: e.scripted = false; e.alert(false)
	cs_end()
	refresh_objective()

func farm_cleared() -> void:
	await wait_real(1.0)
	await line("a09")
	refresh_objective()

func _market_lines() -> void:
	refresh_objective()
	await wait_real(1.0)
	await line("a10")
	await line("a11")

func green_scene() -> void:
	set_checkpoint("green", _cp_pos("green")[0], _cp_pos("green")[1], 3); stage = 3
	cs_begin()
	var gs: Array = groups.get("green", [])
	for e in gs: e.scripted = true
	if gs.size() > 4: talkers["guard"] = gs[4].actor; talkers["guard2"] = gs[0].actor
	shot(mpos("M-cam-green1"), Vector3(0, 1.5, 6), 6.0, mpos("M-cam-green1") + Vector3(0, -1.0, -3.0), Vector3(0, 1.5, 6), 50)
	if gs.size() > 4: gs[4].actor.play("point")
	await say("a12")
	shot(player.global_position + Vector3(-1.2, 1.6, 2.0), player.global_position + Vector3(0, 1.4, 0), 0.0, null, null, 45)
	player.actor.play("shrug")
	await say("a13")
	if gs.size() > 0:
		shot(gs[0].global_position + Vector3(1.5, 1.7, -2.5), gs[0].global_position + Vector3(0, 1.5, 0), 0.0, null, null, 40)
		gs[0].actor.play("nod")
	await say("a14")
	for e in gs: e.scripted = false; e.alert(false)
	cs_end()
	refresh_objective()

func green_cleared() -> void:
	refresh_objective()
	await wait_real(0.8)
	if chains_left > 0:
		shot_hint_chains()

func shot_hint_chains() -> void:
	await line("a15")
	refresh_objective()

func drawbridge_scene() -> void:
	cs_begin()
	stage = max(stage, 3)
	shot(mpos("M-cam-bridge"), Vector3(0, 2.0, 0), 4.0, mpos("M-cam-bridge") + Vector3(-3, -2, -2), Vector3(0, 1.0, 1), 50)
	Audio.sfx("creak"); Audio.sfx("chain_snap", -2)
	_bridge_down(false)
	await cs_wait(2.6)
	shot(mpos("M-cam-gate2"), Vector3(0, 1.6, -6), 0.0, null, null, 55)
	await cs_wait(0.4)
	await say("a16")
	for e in groups.get("green", []):
		if is_instance_valid(e) and not e.defeated: e.alert(false)
	cs_end()
	stage = 4 if stage < 4 else stage
	G.checkpoint("yard", 4)
	fired.erase("yard")
	refresh_objective()
	G.ui.objective("Storm the castle!", "CASTLE COURTYARD")
	G.ui.set_waypoint(mpos("M-tr-yard"))

func _bridge_down(instant: bool) -> void:
	var b: Node3D = movers["X-drawbridge"]
	if instant: b.rotation.x = 0.0; return
	var tw := create_tween()
	tw.tween_property(b, "rotation:x", 0.0, 2.2).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	tw.tween_callback(func(): Audio.sfx3("slam", b.global_position, 4); player.shake(0.5); FX.smoke(b.global_position + Vector3(0, 0, 5), 10))

func yard_progress() -> void:
	if stage != 4 or G.flag("grate_call"): return
	var total: int = groups.get("yard", []).size()
	if total == 0 or float(group_left("yard")) / total <= 0.35: maestro_call()

func maestro_call() -> void:
	if G.flag("grate_call") or stage != 4: return
	G.set_flag("grate_call")
	await line("b02")
	refresh_objective()

func grate_talk() -> void:
	if G.flag("grate_done") or in_cs: return
	G.set_flag("grate_call")
	cs_begin()
	get_node("IT_grate").enabled = false
	player.teleport(mpos("M-it-grate") + Vector3(0, -0.3, 2.2), 0.0)
	player.actor.play("crouch")
	shot(mpos("M-cam-grate"), mpos("M-it-grate"), 0.0, null, null, 45)
	await say("b03")
	shot(mpos("M-it-grate") + Vector3(0.6, 1.6, 1.2), mpos("M-it-grate") + Vector3(0, -0.8, 0), 6.0, mpos("M-it-grate") + Vector3(-0.4, 1.3, 1.0), mpos("M-it-grate") + Vector3(0, -0.8, 0), 45)
	await say("b04")
	shot(player.global_position + Vector3(1.4, 1.2, 1.4), player.global_position + Vector3(0, 0.9, 0), 0.0, null, null, 45)
	await say("b05")
	shot(mpos("M-it-grate") + Vector3(0.6, 1.6, 1.2), mpos("M-it-grate") + Vector3(0, -0.8, 0), 0.0, null, null, 45)
	await say("b06")
	await say("b07")
	shot(Vector3(20, 2.0, -40), Vector3(27, 30, -60), 4.0, Vector3(19, 1.6, -39), Vector3(27, 42, -60), 55)
	await say("b08")
	await say("b09")
	G.set_flag("grate_done")
	G.save_all()
	player.actor.play("idle")
	cs_end()
	refresh_objective()

# ------------------------------------------------------------------ boss
func _spawn_boss() -> void:
	boss = Boss.new()
	boss.setup("bruno", "boss", mpos("M-boss"), 0.0)
	boss.center = Vector3(TOWER.x, mpos("M-boss").y, TOWER.z)
	add_child(boss)
	boss.defeated_boss.connect(boss_defeated)
	talkers["bruno"] = boss.actor

func boss_intro() -> void:
	boss_started = true
	stage = 7
	set_checkpoint("spiretop", _cp_pos("spiretop")[0], _cp_pos("spiretop")[1], 7)
	if boss == null: _spawn_boss()
	cs_begin()
	Audio.music("boss")
	var bp := boss.global_position
	boss.face = atan2(-(player.global_position - bp).x, -(player.global_position - bp).z); boss.actor.rotation.y = boss.face
	shot(mpos("M-cam-boss1"), bp + Vector3(0, 2, 0), 5.0, mpos("M-cam-boss1") + Vector3(-2, -1, 1), bp + Vector3(0, 2, 0), 50)
	boss.actor.play("taunt")
	await say("c04")
	shot(player.global_position + Vector3(1.2, 1.6, 1.6), player.global_position + Vector3(0, 1.3, -1), 0.0, null, null, 45)
	player.actor.play("wave")
	await say("c05")
	shot(bp + (player.global_position - bp).normalized() * 3.0 + Vector3(0.5, 1.6, 0), bp + Vector3(0, 2.1, 0), 0.0, null, null, 45)
	boss.actor.play("cheer")
	await say("c06")
	player.actor.play("hold")
	shot(player.global_position + Vector3(-1.0, 1.6, 1.4), player.global_position + Vector3(0, 1.4, -1), 0.0, null, null, 45)
	await say("c07")
	shot(mpos("M-cam-boss2"), bp + Vector3(0, 1.5, 0), 0.0, null, null, 55)
	await say("c08")
	cs_end()
	boss.active = true
	G.ui.boss(true, boss.hp / boss.max_hp)
	refresh_objective()

func boss_defeated() -> void:
	G.ui.boss(false)
	await wait_real(0.8)
	cs_begin()
	shot(boss.global_position + Vector3(2.5, 1.5, 2.5), boss.global_position + Vector3(0, 0.6, 0), 4.0, boss.global_position + Vector3(1.8, 1.0, 1.8), boss.global_position + Vector3(0, 0.6, 0), 45)
	FX.stars(boss, 0.9)
	await say("c09")
	# the key drops
	var key := Actor.prop("P-key"); add_child(key); key.global_position = boss.global_position + Vector3(0, 0.3, 1.0); key.scale = Vector3.ONE * 2.0
	var kl := OmniLight3D.new(); key.add_child(kl); kl.light_color = Color(1, 0.85, 0.4); kl.light_energy = 1.5; kl.omni_range = 2.5
	Audio.sfx("key")
	player.teleport(boss.global_position + Vector3(0, 0.1, 2.4), 0.0)
	player.actor.play("pickup")
	shot(player.global_position + Vector3(1.6, 1.4, 1.5), player.global_position + Vector3(0, 0.8, -0.6), 0.0, null, null, 45)
	await cs_wait(0.9)
	key.queue_free()
	G.set_flag("key")
	G.ui.toast("CLOCK KEY acquired", Color(1, 0.85, 0.4))
	player.actor.play("cheer")
	await say("c10")
	shot(mpos("M-zip-top") + Vector3(3, 1, 3), mpos("M-zip-bottom"), 3.0, mpos("M-zip-top") + Vector3(2, 0.5, 2), mpos("M-zip-bottom"), 50)
	await say("c11")
	cs_end()
	get_node("IT_zip").enabled = true
	G.checkpoint("spiretop", 7)
	refresh_objective()
	_update_music(true)

func ride_zip() -> void:
	get_node("IT_zip").enabled = false
	G.ui.set_waypoint(null)
	bark("bk_zip")
	await player.zip(mpos("M-zip-top") + Vector3(0, 0.6, 0), mpos("M-zip-bottom") + Vector3(0, 2.4, 0))
	stage = 8
	G.checkpoint("hall", 8)
	cp_pos = _cp_pos("hall")[0]; cp_yaw = 0.0; cp_id = "hall_out"
	_keepdoor_scene()

func _keepdoor_scene() -> void:
	cs_begin()
	shot(mpos("M-cam-keepdoor"), mpos("M-keepdoor") + Vector3(0, 2, 0), 3.0, mpos("M-cam-keepdoor") + Vector3(-1, -0.5, -1), mpos("M-keepdoor") + Vector3(0, 2, 0), 50)
	_open_keepdoor(false)
	var ks := groups.get("hall", [])
	if ks.size() > 0: talkers["knight"] = ks[0].actor
	await cs_wait(1.0)
	await say("d01")
	cs_end()
	refresh_objective()
	for e in ks:
		if is_instance_valid(e) and e.kind == "knight": e.alert(false)

func _open_keepdoor(instant: bool) -> void:
	var d: Node3D = movers["X-keepdoor"]
	var target := d.position + Vector3(0, -4.7, 0)
	if instant: d.position = target; return
	Audio.sfx3("door", d.global_position, 2); Audio.sfx3("creak", d.global_position)
	FX.smoke(d.global_position + Vector3(0, 0.5, 1.0), 12, Color(0.5, 0.45, 0.4, 0.6), 1.5)
	var tw := create_tween(); tw.tween_property(d, "position", target, 2.5).set_trans(Tween.TRANS_SINE)

func _open_gate(name: String, instant: bool) -> void:
	var d: Node3D = movers[name]
	var target := d.position + Vector3(0, 3.1, 0)
	if instant: d.position = target; return
	Audio.sfx3("unlock", d.global_position, 0); Audio.sfx3("portcullis", d.global_position, -2)
	var tw := create_tween(); tw.tween_property(d, "position", target, 1.6).set_trans(Tween.TRANS_SINE)

func open_dungeon() -> void:
	if not G.flag("key"):
		bark("i_dungeongate"); return
	get_node("IT_dungeongate").enabled = false
	G.add_secret("i_dungeongate")
	_open_gate("X-dungeongate", false)
	say_line("d03")
	stage = max(stage, 8)
	G.ui.set_waypoint(mpos("M-cp-dungeon"))
	G.ui.objective("Head down into the dungeon", "THE KEEP")

func _beppe_talk() -> void:
	beppe.play("talk")
	await line("d05")
	await line("d06")
	beppe.play("sad")
	await line("d07")
	beppe.play("sad")
	G.add_secret("i_beppe")

# ------------------------------------------------------------------ the Maestro + trebuchet
func cell_scene() -> void:
	if not G.flag("key"): bark("bk_locked"); return
	get_node("IT_cellgate").enabled = false
	_open_gate("X-cellgate", false)
	await wait_real(1.2)
	cs_begin()
	player.teleport(Vector3(8, -6, -59.5), PI * 0.9)
	maestro.global_position = mpos("M-npc-maestro")
	maestro.look_at(player.global_position * Vector3(1, 0, 1) + Vector3(0, maestro.global_position.y, 0), Vector3.UP); maestro.rotation.y += PI
	maestro.play("excited")
	shot(mpos("M-cam-cell1"), maestro.global_position + Vector3(0, 1.5, 0), 6.0, mpos("M-cam-cell1") + Vector3(1.5, 0, 0.5), maestro.global_position + Vector3(0, 1.5, 0), 45)
	await say("d08")
	shot(player.global_position + Vector3(-1.0, 1.6, -1.2), player.global_position + Vector3(0, 1.4, 0), 0.0, null, null, 45)
	await say("d09")
	maestro.play("talk")
	shot(maestro.global_position + Vector3(-1.4, 1.6, 1.2), maestro.global_position + Vector3(0, 1.5, 0), 0.0, null, null, 40)
	await say("d10")
	shot(Vector3(3.6, -4.2, -55.5), Vector3(3.0, -3.4, -54.0), 4.0, Vector3(4.2, -4.0, -55.5), Vector3(3.0, -3.4, -55.5), 45)
	await say("d11")
	await say("d12")
	maestro.play("point")
	shot(mpos("M-cam-cell2"), mpos("M-scroll"), 4.0, mpos("M-cam-cell2") + Vector3(-0.3, -0.2, -0.4), mpos("M-scroll"), 45)
	await say("d13")
	scroll_prop.visible = false
	player.actor.attach("P-scroll", "hand_L", Vector3(0, 0.1, 0), Vector3(0, 0, 90), 1.2)
	player.actor.play("pickup")
	Audio.sfx("collect")
	shot(player.global_position + Vector3(1.4, 1.5, 1.6), player.global_position + Vector3(0, 1.3, 0), 0.0, null, null, 45)
	await say("d14")
	maestro.play("shrug")
	shot(maestro.global_position + Vector3(1.3, 1.6, 1.4), maestro.global_position + Vector3(0, 1.5, 0), 0.0, null, null, 40)
	await say("d15")
	await trebuchet_scene()

func trebuchet_scene() -> void:
	var tp := mpos("M-treb")
	var count := Actor.make("count"); add_child(count); count.global_position = tp + Vector3(4.5, 0, 6.0); count.rotation.y = PI * 0.75
	var eng := Actor.make("peasant"); add_child(eng); eng.global_position = tp + Vector3(2.5, 0, 4.0); eng.rotation.y = PI * 0.8
	talkers["count"] = count; talkers["engineer"] = eng
	count.play("point")
	G.ui.fade_rect.color.a = 0.0
	shot(mpos("M-cam-treb"), tp + Vector3(0, 4, 0), 6.0, mpos("M-cam-treb") + Vector3(-1, 0.5, -1), tp + Vector3(0, 5, 0), 50)
	Audio.music("")
	await say("d16")
	eng.play("shrug")
	shot(eng.global_position + Vector3(1.4, 1.6, 1.8), eng.global_position + Vector3(0, 1.5, 0), 0.0, null, null, 40)
	await say("d17")
	count.play("taunt")
	shot(count.global_position + Vector3(-1.2, 1.6, 2.0), count.global_position + Vector3(0, 1.6, 0), 0.0, null, null, 40)
	await say("d18")
	# FIRE!
	shot(mpos("M-cam-treb2"), tp + Vector3(0, 5, 0), 0.0, null, null, 55)
	var arm: Node3D = movers["X-trebuchet_arm"]
	Audio.sfx3("trebuchet", arm.global_position, 4)
	var tw := create_tween()
	tw.tween_property(arm, "rotation:x", deg_to_rad(120), 0.7).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	await cs_wait(0.6)
	var fb := Projectile.new(); add_child(fb)
	var start := arm.global_position + Vector3(0, 6, 4)
	fb.launch("fireball", start, start, 0, null)
	fb.set_physics_process(false)
	var keep_hit := Vector3(-10, 14, -60)
	var ft := create_tween()
	ft.tween_method(func(v: float):
		var p := start.lerp(keep_hit, v); p.y += sin(v * PI) * 14.0
		fb.global_position = p
		cs_cam.look_at(p, Vector3.UP), 0.0, 1.0, 1.6)
	if not skipping(): await ft.finished
	if is_instance_valid(fb): fb.queue_free()
	FX.explosion(keep_hit, 2.5)
	ignite()
	eng.play("cower")
	shot(count.global_position + Vector3(-1.2, 1.6, 2.0), count.global_position + Vector3(0, 1.6, 0), 0.0, null, null, 40)
	await say("d19")
	count.play("shrug")
	await say("d20")
	# back to the cell
	shot(mpos("M-cam-cell1"), maestro.global_position + Vector3(0, 1.5, 0), 0.0, null, null, 45)
	player.shake(0.8)
	maestro.play("point")
	await say("d21")
	await say("d22")
	count.queue_free(); eng.queue_free()
	tw.kill()
	arm.rotation.x = deg_to_rad(120)
	cs_end()
	start_escape(false)

func ignite() -> void:
	if not get_tree().get_nodes_in_group("escape_fire").is_empty(): return
	var spots := [Vector3(-10, 0.2, -56), Vector3(-17, 0.2, -66), Vector3(-3, 0.2, -70), Vector3(-6, 0.2, -52), Vector3(-20, 0.2, -53),
		Vector3(-21, 0.2, -70), Vector3(0, 0.2, -60), Vector3(-14, 0.2, -59),
		Vector3(-10, 15.5, -60), Vector3(5, 15.5, -66), Vector3(-20, 15.5, -55),
		Vector3(31, 4.4, -20), Vector3(31, 4.4, -26), Vector3(-30, 3.0, -24), Vector3(-20, 1.0, -30), Vector3(-26, 0.3, -12), Vector3(24, 0.3, -36),
		Vector3(-3, 9.5, -3), Vector3(3, 9.5, -3), Vector3(-20, 10.5, -6), Vector3(20, 10.5, -6), Vector3(12, 0.3, -18), Vector3(-12, 0.3, -42)]
	for p in spots:
		var f := FX.fire(self, p, 2.2 if p.y > 5 else 1.6, true)
		f.add_to_group("escape_fire")

func start_escape(from_cp: bool) -> void:
	stage = 10
	ignite()
	escape_t = escape_cp_t if not from_cp else (G.flag("escape_t", ESCAPE_TIME))
	if escape_t < 60.0: escape_t = 60.0
	if not from_cp:
		cp_id = ""
		set_checkpoint("escape", _cp_pos("escape")[0], _cp_pos("escape")[1], 10)
		G.set_flag("escape_t", escape_t)
	scroll_prop.visible = false
	if not player.actor.held.has("P-scroll"): player.actor.attach("P-scroll", "hips", Vector3(0.2, 0.0, 0.15), Vector3(0, 0, 0), 1.0)
	else:
		player.actor.detach("P-scroll"); player.actor.attach("P-scroll", "hips", Vector3(0.2, 0.0, 0.15), Vector3(0, 0, 0), 1.0)
	# hellish sky
	var sm: ProceduralSkyMaterial = env.environment.sky.sky_material
	sm.sky_top_color = Color(0.12, 0.05, 0.06); sm.sky_horizon_color = Color(0.95, 0.35, 0.12)
	env.environment.fog_light_color = Color(0.55, 0.25, 0.15); env.environment.fog_density = 0.012
	sun.light_color = Color(1.0, 0.5, 0.3)
	Audio.music("escape"); music_zone = "escape"
	# the castle panics: remaining guards flee, two knights still want a fight
	for e in get_tree().get_nodes_in_group("enemies"):
		if not e.defeated and e.kind in ["guard", "peasant", "cook", "archer"] and e.global_position.y > -3: e.go("flee"); e.defeated_soft()
	if not from_cp or true:
		for pos in [Vector3(-6, 0, -30), Vector3(6, 0, -22)]:
			var k := Enemy.new(); k.setup("knight", "escape", pos, PI); add_child(k)
	refresh_objective()
	if not from_cp: G.ui.toast("ESCAPE BEFORE THE CASTLE COLLAPSES", Color(1, 0.5, 0.3))

func _escape_events() -> void:
	var p := player.global_position
	# objective refresh as she moves through areas
	if int(escape_t * 2) % 2 == 0: refresh_objective()
	# escape checkpoint at the keep door
	if cp_id == "escape" and p.z > -48.0 and p.y > -1.0:
		escape_cp_t = max(escape_t, 75.0)
		G.set_flag("escape_t", escape_cp_t)
		set_checkpoint("escape2", _cp_pos("escape2")[0], _cp_pos("escape2")[1], 10)
	# falling burning beams (telegraphed, no permanent obstacles)
	for spot in [Vector3(-14, 0, -56), Vector3(-11, 0, -44), Vector3(-5, 0, -30), Vector3(-1, 0, -16)]:
		var key := str(spot)
		if beams_done.has(key): continue
		if Vector2(p.x - spot.x, p.z - spot.z).length() < 7.0:
			beams_done[key] = true
			_drop_beam(spot)
	# portcullis drops as she approaches the gate
	if not portcullis_dropped and p.z > -24.0 and p.z < 0.0 and p.y > -1.0:
		portcullis_dropped = true
		_drop_portcullis()
	# out over the drawbridge -> finale
	if not finale_started and p.z > 8.0 and p.y > -1.0:
		finale_started = true
		finale()

func _drop_beam(spot: Vector3) -> void:
	var target := spot + Vector3(randf_range(-1, 1), 0, randf_range(-1, 1))
	var ring := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 1.6; cm.bottom_radius = 1.6; cm.height = 0.05
	ring.mesh = cm; ring.material_override = FX.add_mat(Color(1.0, 0.3, 0.1, 0.5), false)
	add_child(ring); ring.global_position = target + Vector3(0, 0.1, 0)
	Audio.sfx3("creak", target + Vector3(0, 6, 0), 2)
	FX.particles(target + Vector3(0, 7, 0), 16, Color(0.5, 0.45, 0.4), 1.0, 2.0, 0.3, -6.0, 40, Vector3.DOWN, true)
	await get_tree().create_timer(1.1).timeout
	var beam := Actor.prop("P-debris"); add_child(beam)
	beam.global_position = target + Vector3(0, 9, 0); beam.scale = Vector3.ONE * 1.8
	var f := FX.fire(beam, beam.global_position, 0.8, false)
	var tw := create_tween(); tw.tween_property(beam, "global_position", target + Vector3(0, 0.2, 0), 0.45).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUAD)
	await tw.finished
	ring.queue_free()
	FX.explosion(target, 0.6)
	if player.global_position.distance_to(target) < 2.0: player.damage(22, target)
	await get_tree().create_timer(6.0).timeout
	if is_instance_valid(beam): beam.queue_free()

func _drop_portcullis() -> void:
	bark("e01")
	var pc: Node3D = movers["X-portcullis"]
	Audio.sfx3("portcullis", pc.global_position, 4)
	var tw := create_tween()
	tw.tween_property(pc, "position:y", 0.95, 4.0).set_trans(Tween.TRANS_SINE)
	await get_tree().create_timer(2.5).timeout
	if not G.is_touch: G.ui.toast("ROLL under the portcullis!  [Shift]", Color(1, 0.8, 0.4))
	else: G.ui.toast("ROLL under the portcullis!", Color(1, 0.8, 0.4))

func finale() -> void:
	escape_t = -1.0
	G.ui.show_timer(-1)
	G.checkpoint("finale", 11)
	cs_begin()
	await cs_wait(0.2)
	player.teleport(Vector3(0, 0.1, 14), PI)
	player.actor.play("idle")
	if pig_friend:
		pig_friend.global_position = Vector3(1.5, 0.1, 16); pig_friend.follow = false; pig_friend.target = pig_friend.global_position
	# the flying machine
	var fly := _make_flyer()
	add_child(fly)
	fly.global_position = Vector3(-30, 30, -50)
	shot(Vector3(4, 1.4, 20), Vector3(0, 4, -4), 0.0, null, null, 55)
	await say("e02")
	var ftw := create_tween()
	ftw.tween_property(fly, "global_position", Vector3(25, 14, 40), 9.0)
	player.actor.play("point")
	shot(player.global_position + Vector3(1.0, 1.0, 1.6), Vector3(-10, 25, -30), 4.0, player.global_position + Vector3(1.0, 1.0, 1.6), Vector3(5, 18, 0), 50)
	await say("e05")
	shot(Vector3(10, 10, 20), fly.global_position, 0.0, null, null, 45)
	var follow := create_tween().set_loops(40)
	follow.tween_callback(func(): if is_instance_valid(fly) and in_cs: _look(cs_cam, fly.global_position)).set_delay(0.05)
	await say("e06")
	await say("e07")
	follow.kill()
	player.actor.play("phone")
	player.actor.attach("P-phone", "hand_L", Vector3(0, 0.08, 0.04), Vector3(-90, 0, 0), 1.4)
	shot(player.global_position + Vector3(1.6, 1.5, 1.4), player.global_position + Vector3(0, 1.2, 0), 0.0, null, null, 45)
	await say("e08")
	await say("e09")
	if pig_friend:
		shot(player.global_position + Vector3(3.0, 0.8, 2.0), pig_friend.global_position + Vector3(0, 0.4, 0), 0.0, null, null, 45)
	player.actor.play("wave")
	await say("e10")
	Audio.sfx("teleport")
	FX.particles(player.global_position + Vector3(0, 1, 0), 40, Color(0.4, 1.0, 0.9), 0.8, 5.0, 0.15, 0.0)
	G.ui.fade_rect.color = Color(1, 1, 1, 0)
	await G.ui.fade(1.0, 0.4)
	in_cs = false
	G.goto("lab", {"ending": true})

func _make_flyer() -> Node3D:
	var n := Node3D.new()
	var wood := StandardMaterial3D.new(); wood.albedo_color = Color(0.45, 0.3, 0.18)
	var cloth := StandardMaterial3D.new(); cloth.albedo_color = Color(0.92, 0.86, 0.72); cloth.cull_mode = BaseMaterial3D.CULL_DISABLED
	cloth.albedo_texture = MatLib.tex("cloth")
	var spar := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = Vector3(9, 0.12, 0.12); spar.mesh = bm; spar.material_override = wood; n.add_child(spar)
	var keel := MeshInstance3D.new(); var km := BoxMesh.new(); km.size = Vector3(0.12, 0.12, 4); keel.mesh = km; keel.material_override = wood; n.add_child(keel)
	for s in [-1, 1]:
		var w := MeshInstance3D.new(); var pm := PrismMesh.new(); pm.size = Vector3(4.5, 2.6, 0.03); pm.left_to_right = 0.0 if s > 0 else 1.0
		w.mesh = pm; w.material_override = cloth; w.rotation.x = -PI / 2; w.position = Vector3(s * 2.25, 0.05, 0.3)
		n.add_child(w)
	var m := Actor.make("maestro"); n.add_child(m); m.position = Vector3(0, -1.9, 0.2); m.play("climb")
	m.rotation.y = 0
	n.rotation.y = -PI * 0.75
	return n

# ------------------------------------------------------------------ misc
func fall_in_moat() -> void:
	if player.input_locked: return
	player.input_locked = true
	Audio.sfx("splash")
	FX.particles(player.global_position + Vector3(0, 0.5, 0), 20, Color(0.6, 0.8, 0.9), 0.6, 5.0, 0.15, -10.0)
	bark("bk_moat")
	await G.ui.fade(1.0, 0.4)
	var pos := Vector3(0, 0.2, 12.0) if player.global_position.z > 0.75 or stage < 4 else Vector3(0, 0.2, -9.0)
	if escape_t >= 0: pos = Vector3(0, 0.2, 12.0)
	player.teleport(pos, PI if pos.z > 0 else 0.0)
	player.input_locked = false
	player.damage(5)
	await G.ui.fade(0.0, 0.4)

func respawn_now() -> void:
	super.respawn_now()
	# reset unfinished fights in the current area
	for e in get_tree().get_nodes_in_group("enemies"):
		if e is Boss: continue
		if not e.defeated and e.state != "down":
			e.global_position = e.home; e.hp = e.st["hp"]; e.alerted = false; e.go("idle"); e.velocity = Vector3.ZERO
	if boss and boss.active:
		boss.hp = max(boss.hp, boss.max_hp * 0.5)
		boss.global_position = mpos("M-boss"); boss.daze = 0; boss._mode("walk")
		G.ui.boss(true, boss.hp / boss.max_hp)
	if stage >= 10:
		escape_t = G.flag("escape_t", ESCAPE_TIME)
		escape_lines.clear()
		portcullis_dropped = false
		if movers.has("X-portcullis"): movers["X-portcullis"].position.y = 5.6
		beams_done.clear()
		if cp_id == "escape2": pass

func on_fall() -> void:
	if stage >= 5 and stage <= 7 and randf() < 0.4: bark("bk_respawn")
	super.on_fall()

# ------------------------------------------------------------------ title backdrop
func _title_cam() -> void:
	cs_cam = Camera3D.new(); cs_cam.fov = 55; cs_cam.far = 700; add_child(cs_cam); cs_cam.current = true

func _title_update(dt: float) -> void:
	title_t += dt * 0.035
	var c := Vector3(0, 12, -35)
	var p := c + Vector3(sin(title_t) * 70.0, 22.0 + sin(title_t * 0.7) * 6.0, cos(title_t) * 70.0)
	cs_cam.global_position = p
	cs_cam.look_at(c + Vector3(8, 8, -10), Vector3.UP)

## debug: ride the clock hand from its start position and report where the player ends up
func dbg_ride() -> void:
	var h: Node3D = movers["X-clockhand"]
	while fmod(clock_t, 19.0) > 0.6 or fmod(clock_t, 19.0) < 0.3: await get_tree().physics_frame
	var spot := h.global_transform * Vector3(0, 0.6, -4.5)
	player.teleport(spot, player.yaw)
	for k in 10:
		await get_tree().create_timer(1.0).timeout
		print("RIDE t=%.1f pos=%s floor=%s" % [fmod(clock_t, 19.0), str(player.global_position.snapped(Vector3.ONE * 0.1)), player.is_on_floor()])
