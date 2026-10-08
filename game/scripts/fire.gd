extends Node3D
## Flickering fire: additive flame particles + embers + smoke + optional light.

var light: OmniLight3D
var base_energy := 1.5
var t := 0.0
var flames: CPUParticles3D

func setup(s: float, with_light: bool) -> void:
	add_to_group("fires")
	flames = CPUParticles3D.new()
	add_child(flames)
	flames.amount = int(clamp(10 * s, 6, 26))
	flames.lifetime = 0.7
	flames.mesh = FX.quad(0.55 * s)
	flames.material_override = FX.add_mat(Color(1.0, 0.55, 0.15), true, true)
	flames.direction = Vector3.UP; flames.spread = 12
	flames.initial_velocity_min = 0.6 * s; flames.initial_velocity_max = 1.6 * s
	flames.gravity = Vector3(0, 1.5, 0)
	flames.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	flames.emission_sphere_radius = 0.15 * s
	flames.scale_amount_min = 0.5; flames.scale_amount_max = 1.2
	var g := Gradient.new()
	g.set_color(0, Color(1.0, 0.85, 0.4, 1.0)); g.set_color(1, Color(0.8, 0.15, 0.02, 0.0))
	g.add_point(0.4, Color(1.0, 0.45, 0.08, 0.8))
	flames.color_ramp = g
	var sc := Curve.new(); sc.add_point(Vector2(0, 0.6)); sc.add_point(Vector2(0.3, 1.0)); sc.add_point(Vector2(1, 0.1))
	flames.scale_amount_curve = sc
	if s > 1.4:
		var sm := CPUParticles3D.new()
		add_child(sm)
		sm.amount = 6; sm.lifetime = 2.5; sm.mesh = FX.quad(1.2 * s)
		sm.material_override = FX.smoke_mat()
		sm.position.y = 1.0 * s
		sm.direction = Vector3.UP; sm.spread = 15; sm.initial_velocity_min = 1.0; sm.initial_velocity_max = 2.0
		sm.gravity = Vector3(0.3, 0.6, 0)
		var g2 := Gradient.new(); g2.set_color(0, Color(0.15, 0.13, 0.12, 0.45)); g2.set_color(1, Color(0.2, 0.2, 0.2, 0.0))
		sm.color_ramp = g2
	if with_light:
		light = OmniLight3D.new()
		add_child(light)
		light.position.y = 0.4 * s
		light.light_color = Color(1.0, 0.62, 0.3)
		base_energy = 1.2 + 0.4 * s
		light.light_energy = base_energy
		light.omni_range = 5.0 + 3.0 * s
		light.shadow_enabled = false
		light.add_to_group("dyn_lights")

func _process(dt: float) -> void:
	if light and light.visible:
		t += dt
		light.light_energy = base_energy * (0.85 + 0.15 * sin(t * 13.0) * sin(t * 7.3 + 1.0))
