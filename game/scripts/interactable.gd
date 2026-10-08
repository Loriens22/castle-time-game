class_name Interactable
extends Node3D
## Something the player can examine / use. Calls `action` (Callable taking this node) or plays the dialogue line `line`.

var prompt := "Look"
var line := ""
var enabled := true
var radius := 2.4
var action: Callable
var once := false
var secret := true

func _ready() -> void:
	add_to_group("interact")

func interact(_p: Node) -> void:
	if action.is_valid():
		action.call(self)
	elif line != "":
		G.level.say_line(line)
	if secret and line != "":
		if G.add_secret(line): G.ui.toast("Discovery %d / %d" % [G.save["secrets"].size(), G.secret_total], Color(0.6, 1.0, 0.9))
	if once: enabled = false
