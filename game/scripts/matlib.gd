class_name MatLib
## Converts the plain glTF materials exported from Blender into the game's textured materials,
## based on material naming conventions:  T_<tex>[#variant] = triplanar texture, D_<img> = UV decal, W_water = water.

const SCALE := {"stone": 0.32, "cobble": 0.45, "flag": 0.4, "dirt": 0.22, "grass": 0.2, "plaster": 0.35, "wood": 0.55,
	"timber": 0.6, "thatch": 0.35, "rooftile": 0.45, "chainmail": 3.0, "hay": 0.5, "rug": 0.5, "labfloor": 0.5, "panel": 0.5,
	"cloth": 1.2, "bark": 0.5, "leaves": 0.6, "crest": 1.0, "logo_2026": 2.0, "chainmail_guard": 3.0}
static var cache := {}
static var tex_cache := {}
static var water_mat: ShaderMaterial

static func tex(name: String) -> Texture2D:
	if tex_cache.has(name): return tex_cache[name]
	var p := "res://assets/tex/%s.png" % name
	var t: Texture2D = load(p) if ResourceLoader.exists(p) else null
	tex_cache[name] = t
	return t

## world = use world-space triplanar (static level geometry); otherwise object-space (characters, movers)
static func apply(root: Node, world := true) -> void:
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		if mi.mesh == null: continue
		var is_world := world and not String(mi.name).begins_with("X-")
		for i in mi.mesh.get_surface_count():
			var m := mi.mesh.surface_get_material(i)
			if m == null: continue
			var nm := m.resource_name
			var key := nm + ("|w" if is_world else "|l")
			if not cache.has(key): cache[key] = convert_mat(m, is_world)
			var out = cache[key]
			if out != m: mi.set_surface_override_material(i, out)

static func convert_mat(m: Material, world: bool) -> Material:
	var nm := m.resource_name
	var base := m as StandardMaterial3D
	if base == null: return m
	if nm.begins_with("W_"):
		return water()
	if nm.begins_with("T_"):
		var t := nm.substr(2).split("#")[0]
		var tx := tex(t)
		if tx == null and t.begins_with("chainmail"): tx = tex("chainmail")
		if tx == null:
			if OS.is_debug_build(): print("MATLIB missing decal ", nm)
			return m
		var s := StandardMaterial3D.new()
		s.resource_name = nm
		s.albedo_texture = tx
		s.albedo_color = base.albedo_color
		s.roughness = clamp(base.roughness, 0.55, 1.0)
		s.metallic = base.metallic * 0.6
		s.uv1_triplanar = true
		s.uv1_world_triplanar = world
		var sc: float = SCALE.get(t, 0.5)
		if t.begins_with("chainmail"): sc = 3.0
		s.uv1_scale = Vector3(sc, sc, sc)
		s.uv1_triplanar_sharpness = 4.0
		s.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
		var nt := tex(t + "_n")
		if nt and G.settings["quality"] >= 1:
			s.normal_enabled = true; s.normal_texture = nt; s.normal_scale = 0.8
		if t == "leaves" or t == "thatch" or t == "hay":
			s.albedo_color = s.albedo_color * Color(1.05, 1.05, 1.0)
		return s
	if nm.begins_with("D_"):
		var tx := tex(nm.substr(2))
		if tx == null:
			if OS.is_debug_build(): print("MATLIB missing decal ", nm)
			return m
		var s := StandardMaterial3D.new()
		s.resource_name = nm
		s.albedo_texture = tx
		s.roughness = 0.85
		s.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
		if base.emission_enabled:
			s.emission_enabled = true; s.emission_texture = tx; s.emission = Color.BLACK; s.emission_operator = BaseMaterial3D.EMISSION_OP_ADD; s.emission_energy_multiplier = 1.4   # (ADD: colour + texture, so the colour must be black)
			s.albedo_color = Color(0.2, 0.2, 0.2)
		return s
	if nm == "fire" or nm == "fireball":
		var s := StandardMaterial3D.new()
		s.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		s.albedo_color = Color(1.0, 0.55, 0.15)
		return s
	if base.emission_enabled:
		base.emission_energy_multiplier = max(base.emission_energy_multiplier, 1.8)
	return m

static func water() -> ShaderMaterial:
	if water_mat: return water_mat
	var sh := Shader.new()
	sh.code = """
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, specular_schlick_ggx;
uniform sampler2D nmap : hint_normal, filter_linear_mipmap, repeat_enable;
uniform vec4 deep : source_color = vec4(0.10, 0.20, 0.17, 1.0);
uniform vec4 shallow : source_color = vec4(0.25, 0.38, 0.30, 1.0);
varying vec3 wp;
void vertex() { wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	vec2 uv = wp.xz * 0.12;
	vec3 n1 = texture(nmap, uv + TIME * vec2(0.012, 0.02)).rgb;
	vec3 n2 = texture(nmap, uv * 1.7 - TIME * vec2(0.02, 0.008)).rgb;
	NORMAL_MAP = normalize(mix(n1, n2, 0.5));
	NORMAL_MAP_DEPTH = 0.6;
	float f = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	ALBEDO = mix(deep.rgb, shallow.rgb, f);
	ROUGHNESS = 0.08;
	METALLIC = 0.0;
	SPECULAR = 0.6;
	ALPHA = 0.88;
}
"""
	water_mat = ShaderMaterial.new()
	water_mat.shader = sh
	water_mat.set_shader_parameter("nmap", tex("water_n"))
	return water_mat
