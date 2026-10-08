extends Node
## Global game state (autoload "G"): settings, save data, dialogue table, level switching, helpers.

signal settings_changed
signal secret_found(id: String)

const SAVE_PATH := "user://castle_time_save.cfg"
var settings := {"master": 0.9, "music": 0.6, "sfx": 0.9, "voice": 1.0, "subs": true, "quality": 1, "sens": 1.0, "invert": false, "touch_ui": -1}
var save := {"checkpoint": "", "stage": 0, "secrets": [], "collect": [], "flags": {}, "time": 0.0, "kos": 0, "deaths": 0}
var dialogue := {}
var names := {}
var colors := {}
var vo_len := {}
var is_touch := false
var is_web := false
var ui = null          # ui.gd CanvasLayer
var main = null        # main.gd
var level = null       # current level (lab.gd / world.gd)
var player: Player = null
var paused := false
var big_head := false
var bench := false           # automated test mode (no saving, extra logging)
var trace := false           # --trace: print story/cutscene events (used by the automated playthrough)

var secret_total := 45   # recomputed from the dialogue table at startup
const COLLECT_IDS := ["cmos", "earbud", "sunglasses", "tamagotchi", "vr", "phonecase", "gameboy", "fidget"]

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	is_web = OS.has_feature("web")
	is_touch = DisplayServer.is_touchscreen_available() or OS.has_feature("web_android") or OS.has_feature("web_ios") or OS.has_feature("mobile")
	var f := FileAccess.open("res://data/dialogue.json", FileAccess.READ)
	if f:
		var d = JSON.parse_string(f.get_as_text())
		dialogue = d["lines"]; names = d["names"]; colors = d["colors"]
		secret_total = COLLECT_IDS.size() + 2   # + big-head code + archery
		for k in dialogue:
			if String(k).begins_with("i_"): secret_total += 1
	var f2 := FileAccess.open("res://data/vo.json", FileAccess.READ)
	if f2: vo_len = JSON.parse_string(f2.get_as_text())
	load_all()
	if is_touch and settings["quality"] == 1 and not save["flags"].has("q_set"): settings["quality"] = 0
	for a in OS.get_cmdline_user_args():
		if a == "--bench": bench = true
		if a == "--trace": trace = true

func tlog(s: String) -> void:
	if trace: print("TRACE %7.1f %s" % [Time.get_ticks_msec() / 1000.0, s])

class _Waiter extends RefCounted:
	signal done
	var fired := false
	func fire(_a = null, _b = null, _c = null) -> void:
		if fired: return
		fired = true
		done.emit()

## Fail-safe await: resumes when `sig` fires OR after `timeout` real seconds (also if the emitter is freed,
## or a tween gets killed and never emits `finished`). Returns immediately-ish in every case.
func wait_for(sig: Signal, timeout: float) -> void:
	var w := _Waiter.new()
	if not sig.is_null() and is_instance_valid(sig.get_object()):
		sig.connect(w.fire, CONNECT_ONE_SHOT)
	get_tree().create_timer(maxf(timeout, 0.05), false, false, true).timeout.connect(w.fire)   # paused game = paused fallback
	if not w.fired: await w.done

func line_dur(id: String) -> float:
	return float(vo_len.get(id, 2.5))

func load_all() -> void:
	var c := ConfigFile.new()
	if c.load(SAVE_PATH) != OK: return
	for k in settings.keys(): settings[k] = c.get_value("settings", k, settings[k])
	for k in save.keys(): save[k] = c.get_value("save", k, save[k])

func save_all() -> void:
	if bench: return
	var c := ConfigFile.new()
	for k in settings.keys(): c.set_value("settings", k, settings[k])
	for k in save.keys(): c.set_value("save", k, save[k])
	c.save(SAVE_PATH)

func set_setting(k: String, v) -> void:
	settings[k] = v
	if k == "quality": save["flags"]["q_set"] = true
	save_all(); settings_changed.emit()

func flag(k: String, def = false): return save["flags"].get(k, def)
func set_flag(k: String, v = true) -> void: save["flags"][k] = v

func has_save() -> bool: return save["stage"] > 0 and save["checkpoint"] != ""

func new_game() -> void:
	save = {"checkpoint": "", "stage": 0, "secrets": [], "collect": [], "flags": {"q_set": save["flags"].get("q_set", false)}, "time": 0.0, "kos": 0, "deaths": 0}
	save_all()

func checkpoint(id: String, stage: int) -> void:
	save["checkpoint"] = id; save["stage"] = max(save["stage"], stage); save_all()

func add_secret(id: String) -> bool:
	if id in save["secrets"]: return false
	save["secrets"].append(id); save_all(); secret_found.emit(id); return true

func add_collect(id: String) -> bool:
	if id in save["collect"]: return false
	save["collect"].append(id); save_all(); return true

func goto(level_name: String, args := {}) -> void:
	main.load_level(level_name, args)

# ------------------------------------------------------------ helpers
static func find_markers(root: Node, prefix: String) -> Array:
	var out := []
	_collect(root, prefix, out)
	return out

static func _collect(n: Node, prefix: String, out: Array) -> void:
	if n.name.begins_with(prefix): out.append(n)
	for c in n.get_children(): _collect(c, prefix, out)

static func damp(a, b, rate: float, dt: float):
	return lerp(a, b, 1.0 - exp(-rate * dt))

static func damp_angle(a: float, b: float, rate: float, dt: float) -> float:
	return lerp_angle(a, b, 1.0 - exp(-rate * dt))
