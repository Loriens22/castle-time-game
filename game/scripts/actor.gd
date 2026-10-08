class_name Actor
extends Node3D
## A skinned character built from the Blender exports: model + shared animation library + held items.

const LOOP := ["idle", "hold", "aim", "walk", "run", "runaim", "walkaim", "backaim", "strafeL", "strafeR", "fall", "climb", "talk",
	"type", "sit", "sitsleep", "stunned", "cheer", "think", "lookaround", "crouch", "eidle", "ewalk", "echarge", "block", "flee",
	"cower", "write", "excited", "kneel", "hammerhold", "hammerwalk", "dizzy", "phone", "handsup", "sad"]
static var lib: AnimationLibrary
static var scenes := {}
static var props_root: Node3D

var kind := ""
var model: Node3D
var skel: Skeleton3D
var ap: AnimationPlayer
var cur := ""
var eyes: Array[Node3D] = []
var mouth: Node3D
var talking := false
var blink_t := 2.0
var held := {}
var overlay: StandardMaterial3D
var meshes: Array[MeshInstance3D] = []
var head_bone := -1
var big_head := false

static func load_lib() -> void:
	if lib: return
	var a: Node = load("res://assets/models/anims.glb").instantiate()
	var src: AnimationPlayer = a.get_node("AnimationPlayer")
	lib = AnimationLibrary.new()
	for n in src.get_animation_list():
		var an: Animation = src.get_animation(n).duplicate()
		an.loop_mode = Animation.LOOP_LINEAR if n in LOOP else Animation.LOOP_NONE
		for t in an.get_track_count():
			var tp := String(an.track_get_path(t))
			if tp.ends_with(":head"): an.track_set_path(t, NodePath(tp + "_2"))
		lib.add_animation(n, an)
	a.free()

static func prop(name: String) -> Node3D:
	if props_root == null:
		props_root = load("res://assets/models/props.glb").instantiate()
		MatLib.apply(props_root, false)
	var src := props_root.get_node_or_null(name)
	if src == null:
		push_warning("missing prop " + name); return Node3D.new()
	var d: Node3D = src.duplicate()
	d.transform = Transform3D.IDENTITY
	return d

static func prop_xform(name: String) -> Transform3D:
	prop("P-blaster")
	var src: Node3D = props_root.get_node_or_null(name)
	return src.transform if src else Transform3D.IDENTITY

static func make(k: String) -> Actor:
	var a := Actor.new()
	a.setup(k)
	return a

func setup(k: String) -> void:
	kind = k
	load_lib()
	var file := k
	if not scenes.has(file):
		scenes[file] = load("res://assets/models/%s.glb" % file)
	model = scenes[file].instantiate()
	model.rotation.y = PI    # Blender characters face -Y -> make them face Godot -Z
	add_child(model)
	MatLib.apply(model, false)
	skel = model.find_child("Skeleton3D", true, false)
	if skel:
		head_bone = skel.find_bone("head_2")
	if k == "cat":
		ap = model.get_node("AnimationPlayer")
		for n in ap.get_animation_list():
			ap.get_animation(n).loop_mode = Animation.LOOP_LINEAR
	else:
		ap = AnimationPlayer.new()
		model.add_child(ap)
		ap.root_node = NodePath("..")
		ap.add_animation_library("", lib)
	for n in model.find_children("*", "MeshInstance3D", true, false):
		meshes.append(n)
		if n.name.begins_with("eye_"): eyes.append(n)
		if n.name == "mouth": mouth = n
	overlay = StandardMaterial3D.new()
	overlay.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	overlay.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	overlay.albedo_color = Color(1, 1, 1, 0)
	overlay.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	play("idle" if k != "cat" else "idle", 0.0)
	if G.big_head: set_big_head(true)

func play(n: String, blend := 0.18, speed := 1.0, restart := false) -> void:
	if not ap.has_animation(n):
		n = "idle" if ap.has_animation("idle") else n
	if n == cur and not restart and ap.is_playing():
		ap.speed_scale = speed; return
	cur = n
	ap.play(n, blend)
	ap.speed_scale = speed
	if restart: ap.seek(0.0, true)

func anim_len(n: String) -> float:
	return ap.get_animation(n).length if ap.has_animation(n) else 0.5

func is_done() -> bool:
	return not ap.is_playing() or (ap.current_animation_position >= ap.current_animation_length - 0.02 and ap.get_animation(cur).loop_mode == Animation.LOOP_NONE)

## attach a props.glb item to a bone. rot in degrees (bone space), off in metres.
func attach(prop_name: String, bone := "hand_R", off := Vector3.ZERO, rot := Vector3.ZERO, scl := 1.0) -> Node3D:
	if skel == null: return null
	var ba := BoneAttachment3D.new()
	ba.bone_name = bone
	skel.add_child(ba)
	var p := prop(prop_name)
	p.position = off
	p.rotation_degrees = rot
	p.scale = Vector3.ONE * scl
	ba.add_child(p)
	held[prop_name] = p
	for n in p.find_children("*", "MeshInstance3D", true, false): meshes.append(n)
	if p is MeshInstance3D: meshes.append(p)
	return p

func detach(prop_name: String) -> void:
	if held.has(prop_name):
		var p: Node3D = held[prop_name]
		held.erase(prop_name)
		meshes.erase(p)
		p.get_parent().queue_free()

func flash(col := Color(1, 1, 1), strength := 0.8) -> void:
	overlay.albedo_color = Color(col.r, col.g, col.b, strength)
	for m in meshes:
		if is_instance_valid(m): m.material_overlay = overlay
	var tw := create_tween()
	tw.tween_property(overlay, "albedo_color:a", 0.0, 0.14)
	tw.tween_callback(func():
		for m in meshes:
			if is_instance_valid(m): m.material_overlay = null)

func set_big_head(on: bool) -> void:
	big_head = on
	if skel and head_bone >= 0:
		skel.set_bone_pose_scale(head_bone, Vector3.ONE * (2.2 if on else 1.0))

func _process(dt: float) -> void:
	# blinking + simple lip flap
	blink_t -= dt
	if eyes.size() > 0:
		var closed := blink_t < 0.12
		for e in eyes: e.scale.y = 0.15 if closed else 1.0
		if blink_t < 0: blink_t = randf_range(2.0, 5.0)
	if mouth:
		mouth.scale.y = (1.0 + abs(sin(Time.get_ticks_msec() * 0.018)) * 2.2) if talking else 1.0
	if big_head and skel and head_bone >= 0:
		skel.set_bone_pose_scale(head_bone, Vector3.ONE * 2.2)
