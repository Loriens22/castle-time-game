extends Node
## Audio autoload: music crossfades, pooled 2D/3D sfx, voice-over with ducking.

var music_a: AudioStreamPlayer
var music_b: AudioStreamPlayer
var cur_music := ""
var vo_player: AudioStreamPlayer
var amb_player: AudioStreamPlayer
var pool2d: Array[AudioStreamPlayer] = []
var pool3d: Array[AudioStreamPlayer3D] = []
var cache := {}
var duck := 1.0
var music_vol := 1.0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for b in ["Music", "SFX", "Voice"]:
		if AudioServer.get_bus_index(b) == -1:
			# Buses normally come from res://default_bus_layout.tres. Fallback: add at an explicit index.
			# add_bus() with the default position -1 breaks Godot's web "Sample" bus mirror (the new bus is
			# inserted before Master in JS, Master gets rerouted into it and nothing reaches the speakers).
			var i := AudioServer.bus_count
			AudioServer.add_bus(i)
			AudioServer.set_bus_name(i, b); AudioServer.set_bus_send(i, "Master")
	music_a = _mk2d("Music"); music_b = _mk2d("Music"); vo_player = _mk2d("Voice"); amb_player = _mk2d("SFX")
	for i in 14: pool2d.append(_mk2d("SFX"))
	for i in 20:
		var p := AudioStreamPlayer3D.new(); p.bus = "SFX"; p.unit_size = 6.0; p.max_distance = 70.0
		p.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE; p.panning_strength = 0.8; add_child(p); pool3d.append(p)
	G.settings_changed.connect(apply_volumes); apply_volumes()

func _mk2d(bus: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new(); p.bus = bus; add_child(p); return p

func apply_volumes() -> void:
	var s = G.settings
	AudioServer.set_bus_volume_db(0, linear_to_db(max(0.0001, s["master"])))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Music"), linear_to_db(max(0.0001, s["music"] * 0.8)))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("SFX"), linear_to_db(max(0.0001, s["sfx"])))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Voice"), linear_to_db(max(0.0001, s["voice"] * 1.25)))

func _stream(path: String) -> AudioStream:
	if cache.has(path): return cache[path]
	if not ResourceLoader.exists(path): cache[path] = null; return null
	var st: AudioStream = load(path); cache[path] = st; return st

func music(name: String, fade := 1.5) -> void:
	if name == cur_music: return
	cur_music = name
	var st: AudioStream = null if name == "" else _stream("res://assets/audio/music/%s.ogg" % name)
	if st is AudioStreamOggVorbis: st.loop = true
	var old := music_a; music_a = music_b; music_b = old
	var tw := create_tween().set_parallel(true)
	if st:
		music_a.stream = st; music_a.volume_db = -40.0; music_a.play()
		tw.tween_property(music_a, "volume_db", 0.0, fade)
	if music_b.playing: tw.tween_property(music_b, "volume_db", -40.0, fade)
	tw.chain().tween_callback(func(): if music_b.volume_db < -35: music_b.stop())

func ambience(name: String) -> void:
	var st: AudioStream = null if name == "" else _stream("res://assets/audio/sfx/%s.ogg" % name)
	if st is AudioStreamOggVorbis: st.loop = true
	if st == amb_player.stream and amb_player.playing: return
	amb_player.stream = st; amb_player.volume_db = -8.0
	if st: amb_player.play()
	else: amb_player.stop()

func sfx(name: String, vol_db := 0.0, pitch := 1.0) -> void:
	var st := _stream("res://assets/audio/sfx/%s.ogg" % name)
	if st == null: return
	for p in pool2d:
		if not p.playing:
			p.stream = st; p.volume_db = vol_db; p.pitch_scale = pitch; p.play(); return
	pool2d[0].stop(); pool2d[0].stream = st; pool2d[0].play()

func sfx3(name: String, pos: Vector3, vol_db := 0.0, pitch := 1.0) -> void:
	var st := _stream("res://assets/audio/sfx/%s.ogg" % name)
	if st == null: return
	var best: AudioStreamPlayer3D = null
	for p in pool3d:
		if not p.playing: best = p; break
	if best == null: best = pool3d[randi() % pool3d.size()]
	best.stream = st; best.global_position = pos; best.volume_db = vol_db; best.pitch_scale = pitch; best.play()

## plays a voice line; returns its duration in seconds
func vo(id: String) -> float:
	var st := _stream("res://assets/audio/vo/%s.ogg" % id)
	var d := G.line_dur(id)
	if st:
		vo_player.stream = st; vo_player.play()
		_duck(d)
	return d

func stop_vo() -> void:
	vo_player.stop(); _duck(0.0)

var _duck_tw: Tween
func _duck(d: float) -> void:
	if _duck_tw: _duck_tw.kill()
	var bus := AudioServer.get_bus_index("Music")
	var base := linear_to_db(max(0.0001, G.settings["music"] * 0.8))
	_duck_tw = create_tween()
	if d > 0:
		_duck_tw.tween_method(func(v): AudioServer.set_bus_volume_db(bus, v), AudioServer.get_bus_volume_db(bus), base - 7.0, 0.2)
		_duck_tw.tween_interval(d)
	_duck_tw.tween_method(func(v): AudioServer.set_bus_volume_db(bus, v), base - (7.0 if d > 0 else 0.0), base, 0.6)
