"""Procedural texture generator for Castle TIME (NumPy + Pillow only, no source images).
Writes tileable greyscale-ish detail maps (tinted in-engine by each material's colour), normal maps
and decal images to game/assets/tex/.  run: venv/bin/python gen/textures.py"""
import numpy as np, os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT = os.path.join(os.path.dirname(__file__), '..', 'game', 'assets', 'tex'); os.makedirs(OUT, exist_ok=True)
N = 512
rng = np.random.default_rng(1283)

def fnoise(n=N, beta=2.0, seed=None):
    """tileable 1/f^beta noise via FFT"""
    r = np.random.default_rng(seed) if seed is not None else rng
    w = r.standard_normal((n, n)); F = np.fft.fft2(w)
    fx = np.fft.fftfreq(n)[:, None]; fy = np.fft.fftfreq(n)[None, :]; f = np.sqrt(fx ** 2 + fy ** 2); f[0, 0] = 1
    x = np.real(np.fft.ifft2(F / f ** (beta / 2))); x -= x.min(); return x / x.max()

def voronoi(pts, n=N, jitter=None):
    """tileable voronoi: returns (F1, F2, id) using wrapped distances. pts in [0,1)^2"""
    yy, xx = np.mgrid[0:n, 0:n] / n
    F1 = np.full((n, n), 9.0); F2 = np.full((n, n), 9.0); ID = np.zeros((n, n), int)
    for i, (px, py) in enumerate(pts):
        dx = np.abs(xx - px); dx = np.minimum(dx, 1 - dx); dy = np.abs(yy - py); dy = np.minimum(dy, 1 - dy)
        d = np.sqrt(dx * dx + dy * dy)
        m = d < F1; F2 = np.where(m, F1, np.minimum(F2, d)); ID = np.where(m, i, ID); F1 = np.where(m, d, F1)
    return F1, F2, ID

def save(name, a, mode='L'):
    a = np.clip(a, 0, 1)
    if a.ndim == 2: im = Image.fromarray((a * 255).astype(np.uint8), 'L').convert('RGB')
    else: im = Image.fromarray((a * 255).astype(np.uint8), 'RGB')
    im.save(os.path.join(OUT, name + '.png'))

def normal_from_height(h, strength=4.0):
    gy, gx = np.gradient(np.pad(h, 1, mode='wrap'))
    gx = gx[1:-1, 1:-1] * strength * N / 256; gy = gy[1:-1, 1:-1] * strength * N / 256
    nz = np.ones_like(h); l = np.sqrt(gx ** 2 + gy ** 2 + 1)
    return np.stack([(-gx / l) * 0.5 + 0.5, (gy / l) * 0.5 + 0.5, nz / l * 0.5 + 0.5], -1)

def tint(g, c0, c1):
    c0 = np.array(c0) / 255; c1 = np.array(c1) / 255; return c0 + (c1 - c0) * g[..., None]

def blocks(rows, cols, mortar=0.035, jitter=0.15, seed=0, stagger=True):
    """running-bond block pattern. returns (height, per-block random value)"""
    yy, xx = np.mgrid[0:N, 0:N] / N; r = np.random.default_rng(seed)
    row = np.floor(yy * rows).astype(int); off = (row % 2) * 0.5 / cols if stagger else 0
    # variable block widths per row
    u = (xx + off) % 1 * cols; col = np.floor(u).astype(int); fu = u - col; fv = yy * rows - row
    val = r.random((rows, cols + 1))[row, col % cols]
    edge = np.minimum(np.minimum(fu, 1 - fu) / cols * N / (N / cols), np.minimum(fv, 1 - fv) * cols / rows)
    ex = np.minimum(fu, 1 - fu) / cols; ey = np.minimum(fv, 1 - fv) / rows; e = np.minimum(ex, ey)
    h = np.clip(e / mortar * 3, 0, 1) ** 0.5
    return h, val

def T_stone():  # castle ashlar
    h, v = blocks(8, 4, 0.012, seed=1); n = fnoise(beta=2.2); n2 = fnoise(beta=1.2)
    hh = h * (0.75 + 0.25 * n) - (1 - h) * 0.1
    g = 0.55 + 0.25 * (v - 0.5) + 0.25 * (n - 0.5) + 0.15 * (n2 - 0.5); g = g * (0.35 + 0.65 * h)
    save('stone', tint(g, (60, 56, 52), (235, 228, 214))); save('stone_n', normal_from_height(hh, 3))
def T_cobble():
    pts = rng.random((140, 2)); F1, F2, ID = voronoi(pts); e = np.clip((F2 - F1) * 40, 0, 1)
    v = rng.random(140)[ID]; n = fnoise(beta=2.0); dome = np.clip(1 - F1 * 18, 0, 1) ** 0.5
    hh = e ** 0.5 * (0.6 + 0.4 * dome); g = (0.45 + 0.35 * v + 0.2 * (n - 0.5)) * (0.25 + 0.75 * e ** 0.6)
    save('cobble', tint(g, (50, 46, 42), (215, 205, 190))); save('cobble_n', normal_from_height(hh, 4))
def T_flag():  # big interior flagstones
    pts = rng.random((26, 2)); F1, F2, ID = voronoi(pts); e = np.clip((F2 - F1) * 60, 0, 1)
    v = rng.random(26)[ID]; n = fnoise(beta=2.3)
    g = (0.5 + 0.25 * v + 0.3 * (n - 0.5)) * (0.3 + 0.7 * e ** 0.4)
    save('flag', tint(g, (55, 50, 46), (205, 196, 182))); save('flag_n', normal_from_height(e ** 0.4 * 0.8 + n * 0.2, 3))
def T_dirt():
    n = fnoise(beta=2.4); n2 = fnoise(beta=1.0); peb = (fnoise(beta=0.5) > 0.78) * 0.25
    g = 0.5 + 0.35 * (n - 0.5) + 0.2 * (n2 - 0.5) + peb
    save('dirt', tint(g, (70, 52, 36), (190, 160, 120)))
def T_grass():
    n = fnoise(beta=2.6); n2 = fnoise(beta=0.9); blades = fnoise(beta=0.3)
    g = 0.45 + 0.3 * (n - 0.5) + 0.25 * (n2 - 0.5) + 0.2 * (blades - 0.5)
    c = tint(g, (40, 62, 24), (150, 175, 80)) * (1 + 0.15 * (n[..., None] - 0.5) * np.array([1.6, 0.4, -0.5]))
    save('grass', c)
def T_plaster():
    n = fnoise(beta=2.5); n2 = fnoise(beta=1.1); stain = np.clip((fnoise(beta=3.0) - 0.55) * 3, 0, 1)
    g = 0.82 + 0.1 * (n - 0.5) + 0.08 * (n2 - 0.5) - 0.25 * stain
    save('plaster', tint(g, (90, 80, 66), (250, 245, 232)))
def T_wood():  # planks running along U
    yy, xx = np.mgrid[0:N, 0:N] / N; plank = np.floor(yy * 6); fv = yy * 6 - plank
    r = np.random.default_rng(3); pv = r.random(7)[plank.astype(int)]; off = r.random(7)[plank.astype(int)]
    grain = np.sin((yy * 90 + np.sin((xx + off) * 2 * np.pi * 2) * 0.6 + fnoise(beta=2.0) * 3) * 2 * np.pi) * 0.5 + 0.5
    gap = np.clip(np.minimum(fv, 1 - fv) * 40, 0, 1)
    end = np.clip(np.abs(((xx + off * 3) % 0.5) - 0.25) * 200 - 48, 0, 1)
    g = (0.55 + 0.2 * (pv - 0.5) + 0.18 * grain) * gap * (0.6 + 0.4 * end)
    save('wood', tint(g, (45, 30, 18), (205, 160, 110))); save('wood_n', normal_from_height(gap * 0.9 + grain * 0.05, 3))
def T_timber():  # rough hewn beams
    yy, xx = np.mgrid[0:N, 0:N] / N
    grain = np.sin((yy * 40 + fnoise(beta=2.2) * 6) * 2 * np.pi) * 0.5 + 0.5; n = fnoise(beta=1.5)
    g = 0.5 + 0.2 * grain + 0.25 * (n - 0.5)
    save('timber', tint(g, (30, 20, 14), (140, 100, 70)))
def T_thatch():
    yy, xx = np.mgrid[0:N, 0:N] / N; n = fnoise(beta=1.8)
    s = np.zeros((N, N)); r = np.random.default_rng(5)
    for i in range(1400):  # straws
        x = r.integers(0, N); y = r.integers(0, N); L = r.integers(30, 90); b = r.random()
        ys = (y + np.arange(L)) % N; xs = (x + (np.arange(L) * r.uniform(-0.15, 0.15)).astype(int)) % N
        s[ys, xs] = np.maximum(s[ys, xs], 0.4 + 0.6 * b)
    s = np.array(Image.fromarray((s * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))) / 255
    rows = (np.sin(yy * 2 * np.pi * 8) * 0.5 + 0.5) ** 3
    g = 0.35 + 0.45 * s + 0.15 * (n - 0.5) - 0.2 * rows
    save('thatch', tint(g, (60, 45, 25), (225, 195, 120))); save('thatch_n', normal_from_height(s * 0.6 - rows * 0.4, 3))
def T_rooftile():
    yy, xx = np.mgrid[0:N, 0:N] / N; rows = 10; cols = 8
    row = np.floor(yy * rows); fv = yy * rows - row; u = (xx + (row % 2) * 0.5 / cols) * cols; fu = u - np.floor(u)
    curve = np.sin(fu * np.pi); over = np.clip(fv * 1.3, 0, 1)
    r = np.random.default_rng(7); v = r.random((rows, cols + 1))[row.astype(int), np.floor(u).astype(int) % cols]
    hh = curve * 0.6 + over * 0.4; n = fnoise(beta=2.0)
    g = (0.5 + 0.25 * v + 0.2 * (n - 0.5)) * (0.45 + 0.55 * curve) * (0.5 + 0.5 * over)
    save('rooftile', tint(g, (70, 28, 16), (230, 120, 80))); save('rooftile_n', normal_from_height(hh, 3))
def T_chainmail():
    yy, xx = np.mgrid[0:N, 0:N] / N; k = 48
    u = xx * k; v = yy * k; row = np.floor(v); u2 = u + (row % 2) * 0.5
    d = np.sqrt((u2 - np.floor(u2) - 0.5) ** 2 + (v - row - 0.5) ** 2); ring = np.exp(-((d - 0.36) / 0.08) ** 2)
    g = 0.25 + 0.75 * ring * (0.8 + 0.2 * fnoise(beta=1.5))
    save('chainmail', tint(g, (40, 42, 45), (230, 232, 236)))
def T_hay():
    T_thatch_like = fnoise(beta=0.8); n = fnoise(beta=2)
    g = 0.5 + 0.3 * (T_thatch_like - 0.5) + 0.2 * (n - 0.5)
    save('hay', tint(g, (150, 115, 50), (245, 215, 130)))
def T_rug():
    yy, xx = np.mgrid[0:N, 0:N] / N
    pat = (np.sin(xx * 2 * np.pi * 8) * np.sin(yy * 2 * np.pi * 8) > 0.3) * 1.0
    border = ((np.abs(xx - 0.5) > 0.42) | (np.abs(yy - 0.5) > 0.42)) * 1.0
    diamond = (np.abs(xx - 0.5) + np.abs(yy - 0.5) < 0.25) * 1.0; n = fnoise(beta=1.0)
    c = np.zeros((N, N, 3)) + np.array([0.55, 0.08, 0.08])
    c = np.where(pat[..., None] > 0, np.array([0.75, 0.55, 0.15]), c); c = np.where(diamond[..., None] > 0, np.array([0.1, 0.15, 0.4]), c)
    c = np.where(border[..., None] > 0, np.array([0.12, 0.1, 0.25]), c)
    save('rug', c * (0.85 + 0.15 * n[..., None]))
def T_parchment():
    n = fnoise(beta=2.2); n2 = fnoise(beta=1.0); yy, xx = np.mgrid[0:N, 0:N] / N
    vig = 1 - 0.0 * ((xx - 0.5) ** 2 + (yy - 0.5) ** 2)
    g = 0.8 + 0.12 * (n - 0.5) + 0.06 * (n2 - 0.5)
    save('parchment', tint(g * vig, (150, 110, 60), (250, 232, 190)))
def T_metal():
    n = fnoise(beta=2.0); yy, xx = np.mgrid[0:N, 0:N] / N
    scr = np.zeros((N, N)); r = np.random.default_rng(9)
    for i in range(300):
        x0, y0 = r.integers(0, N, 2); a = r.uniform(0, np.pi); L = r.integers(10, 80)
        t = np.arange(L); xs = ((x0 + t * np.cos(a)).astype(int)) % N; ys = ((y0 + t * np.sin(a)).astype(int)) % N; scr[ys, xs] = 1
    g = 0.7 + 0.2 * (n - 0.5) + 0.15 * scr
    save('metal', tint(g, (90, 90, 95), (255, 255, 255)))
def T_labfloor():
    yy, xx = np.mgrid[0:N, 0:N] / N; k = 4; fu = (xx * k) % 1; fv = (yy * k) % 1
    seam = np.clip(np.minimum(np.minimum(fu, 1 - fu), np.minimum(fv, 1 - fv)) * 120, 0, 1); n = fnoise(beta=1.5)
    g = (0.6 + 0.1 * (n - 0.5)) * (0.5 + 0.5 * seam)
    save('labfloor', tint(g, (20, 22, 28), (120, 125, 140)))
def T_panel():
    yy, xx = np.mgrid[0:N, 0:N] / N; fu = (xx * 2) % 1; fv = (yy * 1) % 1
    seam = np.clip(np.minimum(np.minimum(fu, 1 - fu), np.minimum(fv, 1 - fv)) * 150, 0, 1); n = fnoise(beta=2)
    holes = ((np.sin(xx * 2 * np.pi * 32) > 0.9) & (np.sin(yy * 2 * np.pi * 32) > 0.9)) * 1.0
    g = (0.7 + 0.08 * (n - 0.5)) * (0.4 + 0.6 * seam) * (1 - 0.5 * holes)
    save('panel', tint(g, (30, 32, 38), (210, 215, 225)))
def T_cloth():
    yy, xx = np.mgrid[0:N, 0:N] / N; w = (np.sin(xx * 2 * np.pi * 128) * np.sin(yy * 2 * np.pi * 128)) * 0.5 + 0.5; n = fnoise(beta=1.8)
    save('cloth', tint(0.7 + 0.15 * w + 0.15 * (n - 0.5), (60, 60, 60), (255, 255, 255)))
def T_bark():
    yy, xx = np.mgrid[0:N, 0:N] / N; n = fnoise(beta=1.6)
    ridges = np.abs(np.sin((xx * 14 + fnoise(beta=2.5) * 2.5) * np.pi)) ** 0.6
    g = 0.3 + 0.5 * ridges * (0.7 + 0.3 * n)
    save('bark', tint(g, (35, 25, 18), (150, 120, 90))); save('bark_n', normal_from_height(ridges, 4))
def T_leaves():
    pts = rng.random((400, 2)); F1, F2, ID = voronoi(pts); v = rng.random(400)[ID]; e = np.clip((F2 - F1) * 60, 0, 1)
    g = (0.4 + 0.5 * v) * (0.5 + 0.5 * e)
    save('leaves', tint(g, (20, 45, 15), (120, 165, 60)))
def T_water():
    n = fnoise(beta=2.4); save('water_n', normal_from_height(n, 6))
def T_noise():  # generic
    save('noise', fnoise(beta=1.6))

# ---------------------------------------------------------------- decals (drawn with PIL)
def font(sz, bold=False):
    for f in ['/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else ''), '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf']:
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()
def serif(sz):
    for f in ['/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf']:
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return font(sz)
def mono(sz):
    for f in ['/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf']:
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return font(sz)

def parchment_img(w, h):
    a = np.array(Image.open(os.path.join(OUT, 'parchment.png')).resize((w, h)))
    yy, xx = np.mgrid[0:h, 0:w]; d = np.maximum(np.abs(xx / w - 0.5), np.abs(yy / h - 0.5)) * 2
    a = (a * (1 - 0.45 * np.clip(d - 0.75, 0, 1) * 4)[..., None]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(a)

INK = (58, 36, 22)
def sketch(name, draw_fn, caption):
    im = parchment_img(512, 512); d = ImageDraw.Draw(im); draw_fn(d)
    d.text((256, 470), caption, fill=INK, font=serif(22), anchor='mm'); im.save(os.path.join(OUT, name + '.png'))

def sk_heli(d):
    d.line([(256, 130), (256, 330)], INK, 4)
    for k in range(18):
        a = k / 18 * 2 * math.pi; r = 150 - k * 3; y = 200 - k * 5
        d.arc([256 - r, y - r * 0.25, 256 + r, y + r * 0.25], 0, 360, INK, 2)
    d.rectangle([200, 330, 312, 360], outline=INK, width=3)
    for x in (210, 300): d.line([(x, 360), (x - 20, 420)], INK, 3)
    d.text((40, 40), 'vite aerea', fill=INK, font=serif(26))
def sk_phone(d):
    d.rounded_rectangle([190, 90, 320, 420], 18, outline=INK, width=5); d.rectangle([205, 110, 305, 230], outline=INK, width=3)
    for r in range(4):
        for c in range(3): d.ellipse([212 + c * 32, 250 + r * 38, 236 + c * 32, 274 + r * 38], outline=INK, width=2)
    d.line([(320, 120), (360, 60)], INK, 4); d.text((40, 40), 'la scatola parlante?', fill=INK, font=serif(24))
    d.text((340, 200), '"Moto-\nrola"', fill=INK, font=serif(20))
def sk_traveller(d):
    d.ellipse([220, 80, 292, 160], outline=INK, width=4); d.rectangle([228, 108, 284, 122], fill=INK)  # visor
    d.polygon([(200, 165), (312, 165), (330, 330), (182, 330)], outline=INK, width=4)
    d.line([(220, 170), (256, 205), (292, 170)], INK, 3)  # hood
    d.line([(200, 180), (140, 260)], INK, 4); d.line([(312, 180), (400, 210)], INK, 4)
    d.rectangle([380, 195, 440, 222], outline=INK, width=3); d.line([(440, 208), (500, 208)], (200, 40, 40), 3)
    d.line([(225, 330), (215, 430)], INK, 4); d.line([(287, 330), (297, 430)], INK, 4)
    d.text((30, 30), 'la viaggiatrice', fill=INK, font=serif(26)); d.text((30, 64), 'XVII ottobre MCCLXXXIII', fill=INK, font=serif(18))
def sk_laser(d):
    d.ellipse([60, 200, 160, 300], outline=INK, width=4); d.line([(110, 250), (460, 250)], INK, 2)
    for i in range(6): d.line([(160 + i * 50, 240), (180 + i * 50, 260)], INK, 2)
    d.polygon([(380, 200), (460, 250), (380, 300)], outline=INK, width=3)
    d.text((40, 40), 'specchio di luce', fill=INK, font=serif(26)); d.text((40, 360), 'luce che morde ma non uccide', fill=INK, font=serif(20))
def sk_trebuchet(d):
    d.polygon([(120, 420), (256, 180), (392, 420)], outline=INK, width=4); d.line([(80, 140), (420, 300)], INK, 5)
    d.rectangle([380, 290, 450, 350], outline=INK, width=3); d.line([(80, 140), (60, 260)], INK, 2); d.ellipse([45, 255, 75, 285], outline=INK, width=3)
    d.text((40, 40), 'NON col fuoco!!', fill=(150, 20, 20), font=serif(30)); d.line([(30, 90), (300, 90)], (150, 20, 20), 3)
def sk_clock(d):
    for r in (150, 110, 60):
        d.ellipse([256 - r, 240 - r, 256 + r, 240 + r], outline=INK, width=3)
        for k in range(int(r / 6)):
            a = k / (r / 6) * 2 * math.pi; d.line([(256 + math.cos(a) * r, 240 + math.sin(a) * r), (256 + math.cos(a) * (r + 10), 240 + math.sin(a) * (r + 10))], INK, 2)
    d.line([(256, 240), (256, 130)], INK, 4); d.line([(256, 240), (320, 260)], INK, 4); d.text((40, 30), "l'orologio del conte", fill=INK, font=serif(26))

def decals():
    sketch('sketch_heli', sk_heli, 'Lorenzo V. - anno 1281'); sketch('sketch_phone', sk_phone, 'Lorenzo V. - anno 1282')
    sketch('sketch_traveller', sk_traveller, 'Lorenzo V. - anno 1283'); sketch('sketch_laser', sk_laser, 'Lorenzo V. - anno 1283')
    sketch('sketch_trebuchet', sk_trebuchet, 'Lorenzo V. - anno 1283'); sketch('sketch_clock', sk_clock, 'Lorenzo V. - anno 1280')
    # scroll (the McGuffin) face
    im = parchment_img(512, 256); d = ImageDraw.Draw(im)
    d.text((256, 40), 'SCIENTIA TEMPORIS', fill=INK, font=serif(30), anchor='mm')
    for i in range(7): d.line([(40, 80 + i * 22), (470 - (i % 3) * 40, 80 + i * 22)], INK, 2)
    d.ellipse([400, 150, 480, 230], outline=(150, 20, 20), width=4); im.save(os.path.join(OUT, 'scroll.png'))
    # crest of Valtorre: golden tower + clock on red
    im = Image.new('RGB', (256, 256), (163, 38, 42)); d = ImageDraw.Draw(im)
    d.rectangle([100, 60, 156, 220], fill=(224, 178, 58)); d.polygon([(92, 60), (164, 60), (128, 18)], fill=(224, 178, 58))
    d.ellipse([110, 90, 146, 126], fill=(163, 38, 42)); d.line([(128, 108), (128, 94)], (224, 178, 58), 3); d.line([(128, 108), (138, 112)], (224, 178, 58), 3)
    for x in range(100, 160, 14): d.rectangle([x, 220, x + 8, 236], fill=(224, 178, 58))
    im.save(os.path.join(OUT, 'crest.png'))
    # 2026 hoodie logo
    im = Image.new('RGB', (256, 256), (43, 47, 58)); d = ImageDraw.Draw(im)
    d.ellipse([28, 28, 228, 228], outline=(57, 255, 208), width=10); d.text((128, 128), '2026', fill=(57, 255, 208), font=font(64, True), anchor='mm')
    im.save(os.path.join(OUT, 'logo_2026.png'))
    # tavern sign
    im = Image.new('RGB', (512, 256), (90, 60, 35)); d = ImageDraw.Draw(im)
    d.rectangle([10, 10, 502, 246], outline=(40, 25, 15), width=8); d.text((256, 80), 'IL DRAGO', fill=(230, 190, 90), font=serif(56), anchor='mm')
    d.text((256, 160), 'UBRIACO', fill=(230, 190, 90), font=serif(56), anchor='mm'); d.text((256, 220), 'birra - letti - niente streghe', fill=(220, 210, 180), font=serif(20), anchor='mm')
    im.save(os.path.join(OUT, 'tavern_sign.png'))
    # medieval wanted poster of Juno
    im = parchment_img(384, 512); d = ImageDraw.Draw(im)
    d.text((192, 50), 'STREGA!', fill=INK, font=serif(60), anchor='mm'); d.text((192, 105), '(forse)', fill=INK, font=serif(26), anchor='mm')
    sk_traveller.__call__  # reuse simple doodle
    d.ellipse([150, 150, 234, 240], outline=INK, width=4); d.rectangle([155, 180, 229, 198], fill=(60, 200, 190)); d.polygon([(120, 250), (264, 250), (290, 400), (94, 400)], outline=INK, width=4)
    d.text((192, 440), 'Vesti strane. Luce rossa.', fill=INK, font=serif(22), anchor='mm'); d.text((192, 474), 'Ricompensa: 3 galline', fill=INK, font=serif(22), anchor='mm')
    im.save(os.path.join(OUT, 'wanted.png'))
    # lab: monitors
    im = Image.new('RGB', (512, 320), (6, 10, 18)); d = ImageDraw.Draw(im); f = mono(15); r = np.random.default_rng(4)
    for i in range(18):
        ind = int(r.integers(0, 4)) * 16; col = [(120, 220, 255), (255, 120, 200), (140, 255, 170), (230, 230, 230)][int(r.integers(0, 4))]
        words = ['def', 'jump(t):', 'flux', '=', 'chrono.lock(', '1283,', '10,', '17)', 'if', 'paradox:', 'return', 'cat.feed()', '# TODO', 'sibyl.ask()']
        d.text((14 + ind, 10 + i * 17), ' '.join(r.choice(words, int(r.integers(2, 6)))), fill=col, font=f)
    im.save(os.path.join(OUT, 'screen_code.png'))
    im = Image.new('RGB', (512, 320), (4, 14, 20)); d = ImageDraw.Draw(im)
    for i in range(0, 512, 32): d.line([(i, 0), (i, 320)], (14, 50, 60), 1)
    for i in range(0, 320, 32): d.line([(0, i), (512, i)], (14, 50, 60), 1)
    d.polygon([(250, 40), (300, 80), (330, 200), (290, 300), (230, 260), (210, 140)], outline=(57, 255, 208), width=3)  # italy-ish
    d.ellipse([255, 150, 271, 166], outline=(255, 80, 120), width=3); d.text((280, 140), '43.4512 N\n11.0157 E', fill=(255, 120, 160), font=mono(20))
    d.text((14, 10), 'TARGET: ROCCA DI VALTORRE', fill=(57, 255, 208), font=mono(20)); d.text((14, 290), 'T-MINUS: 743 YEARS', fill=(255, 210, 90), font=mono(18))
    im.save(os.path.join(OUT, 'screen_map.png'))
    im = Image.new('RGB', (512, 320), (10, 4, 16)); d = ImageDraw.Draw(im)
    for k in range(160):
        a = k / 160 * 2 * np.pi; rr = 90 + 30 * np.sin(a * 6)
        d.line([(256, 160), (256 + rr * np.cos(a), 160 + rr * np.sin(a))], (int(120 + 100 * np.sin(a)), 60, 255), 1)
    d.text((256, 290), 'SIBYL v9.3  //  ONLINE', fill=(200, 160, 255), font=mono(20), anchor='mm'); im.save(os.path.join(OUT, 'screen_sibyl.png'))
    # lab posters
    im = Image.new('RGB', (384, 512), (18, 16, 30)); d = ImageDraw.Draw(im)
    for i in range(30): d.line([(0, 300 + i * 8), (384, 300 + i * 8)], (255, 60 + i * 5, 160), 2)
    d.ellipse([92, 120, 292, 320], fill=(255, 140, 60)); d.rectangle([0, 300, 384, 512], fill=(18, 16, 30))
    for i in range(12): d.line([(192, 300), (-200 + i * 70, 512)], (57, 255, 208), 1)
    d.text((192, 50), 'TIME', fill=(255, 255, 255), font=font(64, True), anchor='mm'); d.text((192, 400), 'WAITS FOR', fill=(57, 255, 208), font=font(36, True), anchor='mm')
    d.text((192, 450), 'NO ONE', fill=(57, 255, 208), font=font(36, True), anchor='mm'); im.save(os.path.join(OUT, 'poster_time.png'))
    im = Image.new('RGB', (384, 256), (240, 240, 235)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 384, 70], fill=(63, 127, 198)); d.text((192, 36), "STEVE'S PC REPAIR", fill=(255, 255, 255), font=font(30, True), anchor='mm')
    d.text((192, 110), 'Fair prices for seniors.', fill=(40, 40, 40), font=font(24), anchor='mm')
    d.text((192, 150), 'CMOS batteries replaced', fill=(40, 40, 40), font=font(22), anchor='mm')
    d.text((192, 190), 'Other jobs: 100% up-front.', fill=(150, 30, 30), font=font(20, True), anchor='mm'); d.text((192, 228), '(no questions)', fill=(90, 90, 90), font=font(16), anchor='mm')
    im.save(os.path.join(OUT, 'card_steve.png'))
    im = Image.new('RGB', (512, 320), (235, 238, 240)); d = ImageDraw.Draw(im); f = font(22)
    lines = ['dt = h / (m c^2)  ?', 'E = mc^2 + (cat)', 'Oct 17 1283 -> FIRE', 'scroll = ???', 'DONT FORGET: change clothes!!', 'feed Pixel']
    for i, l in enumerate(lines): d.text((20, 20 + i * 46), l, fill=[(30, 60, 160), (180, 30, 40), (20, 120, 60)][i % 3], font=f)
    d.ellipse([360, 180, 470, 290], outline=(180, 30, 40), width=4); im.save(os.path.join(OUT, 'whiteboard.png'))
    # night city window
    im = Image.new('RGB', (512, 320), (8, 10, 28)); d = ImageDraw.Draw(im); r = np.random.default_rng(11)
    for i in range(26):
        x = int(r.integers(0, 500)); w = int(r.integers(20, 60)); h = int(r.integers(60, 280)); c = int(r.integers(14, 30))
        d.rectangle([x, 320 - h, x + w, 320], fill=(c, c, c + 12))
        for k in range(int(h / 14)):
            for j in range(int(w / 10)):
                if r.random() < 0.35: d.rectangle([x + 3 + j * 10, 320 - h + 6 + k * 14, x + 7 + j * 10, 320 - h + 11 + k * 14], fill=(255, int(r.integers(180, 240)), 120))
    d.ellipse([420, 30, 470, 80], fill=(240, 240, 220)); im.save(os.path.join(OUT, 'window_city.png'))
    # phone screen (keypad UI) + motorola-ish badge
    im = Image.new('RGB', (256, 384), (6, 20, 14)); d = ImageDraw.Draw(im)
    d.text((128, 30), 'T-PORT v2', fill=(120, 255, 160), font=mono(24), anchor='mm'); d.text((128, 120), '17.10.1283', fill=(120, 255, 160), font=mono(34), anchor='mm')
    d.text((128, 190), '43.4512N', fill=(120, 255, 160), font=mono(30), anchor='mm'); d.text((128, 235), '11.0157E', fill=(120, 255, 160), font=mono(30), anchor='mm')
    d.text((128, 330), '[ JUMP ]', fill=(255, 220, 120), font=mono(28), anchor='mm'); im.save(os.path.join(OUT, 'phone_screen.png'))

if __name__ == '__main__':
    for f in [T_stone, T_cobble, T_flag, T_dirt, T_grass, T_plaster, T_wood, T_timber, T_thatch, T_rooftile, T_chainmail, T_hay, T_rug,
              T_parchment, T_metal, T_labfloor, T_panel, T_cloth, T_bark, T_leaves, T_water, T_noise]:
        f(); print(f.__name__)
    decals(); print('decals')
