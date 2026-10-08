"""Castle TIME: synthesize every sound effect from scratch with NumPy (no samples). DSP helpers adapted from Steve The PC Repair Man.
Writes OGG files to game/assets/audio/sfx/."""
import numpy as np, subprocess, os, sys, json
from scipy import signal
SR = 44100
OUT = os.path.join(os.path.dirname(__file__), '..', 'game', 'assets', 'audio', 'sfx'); os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)
def t_(d): return np.arange(int(SR * d)) / SR
def env(n, a=0.005, d=0.1, s=0.0, r=0.05, hold=0.0):
    a_, d_, h_, r_ = int(a * SR), int(d * SR), int(hold * SR), int(r * SR)
    e = np.concatenate([np.linspace(0, 1, max(a_, 1)), np.full(h_, 1.0), np.linspace(1, s, max(d_, 1))])
    if s > 0: e = np.concatenate([e, np.full(max(0, n - len(e) - r_), s), np.linspace(s, 0, max(r_, 1))])
    e = e[:n]; return np.pad(e, (0, n - len(e)))
def expd(n, k): return np.exp(-np.arange(n) / SR * k)
def noise(d): return rng.uniform(-1, 1, int(SR * d))
def bp(x, lo, hi, o=2): b, a = signal.butter(o, [lo / (SR / 2), min(hi / (SR / 2), 0.99)], 'band'); return signal.lfilter(b, a, x)
def lp(x, f, o=2): b, a = signal.butter(o, min(f / (SR / 2), 0.99)); return signal.lfilter(b, a, x)
def hp(x, f, o=2): b, a = signal.butter(o, f / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def fit(f, n):
    if not np.ndim(f): return np.full(n, float(f))
    f = np.asarray(f, float); return f[:n] if len(f) >= n else np.pad(f, (0, n - len(f)), mode='edge')
def sine(f, d, ph=0):
    t = t_(d); f = fit(f, len(t)); return np.sin(2 * np.pi * np.cumsum(f) / SR + ph)
def sq(f, d, duty=0.5):
    t = t_(d); f = fit(f, len(t)); ph = np.cumsum(f) / SR % 1; return np.where(ph < duty, 1.0, -1.0)
def saw(f, d):
    t = t_(d); f = fit(f, len(t)); ph = np.cumsum(f) / SR % 1; return 2 * ph - 1
def tri(f, d): return 2 * np.abs(saw(f, d)) - 1
def glide(f0, f1, d, curve=1.0): k = np.linspace(0, 1, int(SR * d)) ** curve; return f0 + (f1 - f0) * k
def mix(*parts):
    n = max(len(p[1]) + int(p[0] * SR) for p in parts); o = np.zeros(n)
    for off, x in parts: i = int(off * SR); o[i:i + len(x)] += x
    return o
def cat(*xs): return np.concatenate(xs)
def sil(d): return np.zeros(int(SR * d))
def norm(x, peak=0.89): m = np.max(np.abs(x)) or 1; return x / m * peak
def reverb(x, size=0.4, wet=0.25, decay=3.0):
    n = int(SR * size); ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * decay * 3 / size); ir = lp(ir, 6000)
    w = signal.fftconvolve(x, ir); w = np.pad(w, (0, max(0, len(x) + n - len(w))))[:len(x) + n]; w = w / (np.max(np.abs(w)) or 1) * np.max(np.abs(x))
    return np.pad(x, (0, n)) * (1 - wet) + w * wet
def pluck(f, d, damp=0.996):
    N = int(SR / f); buf = rng.uniform(-1, 1, N); out = np.zeros(int(SR * d))
    for i in range(len(out)):
        out[i] = buf[i % N]; buf[i % N] = damp * 0.5 * (buf[i % N] + buf[(i + 1) % N])
    return out
def fm(fc, fmod, idx, d, e=None):
    t = t_(d); m = idx * (e if e is not None else 1) * np.sin(2 * np.pi * fmod * t); return np.sin(2 * np.pi * fc * t + m)
def bell_tone(f, d, k=3.0):
    t = t_(d); x = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * k * r ** 0.6) for r, a in [(1, 1), (2.01, 0.5), (2.76, 0.35), (4.07, 0.2), (5.4, 0.1)]); return x
def click(d=0.01, f=3000): n = noise(d) * expd(int(SR * d), 600); return bp(n, f * 0.5, f * 2)

S = {}
def reg(name, x, peak=0.89): S[name] = norm(np.asarray(x, dtype=float), peak)
def n_(d): return int(SR * d)
def E(d, k): return expd(n_(d), k)
# ------------------------------------------------------------- UI
reg('ui_click', mix((0, click(0.02, 2500)), (0, sine(1200, 0.04) * E(.04, 120) * 0.5)), 0.6)
reg('ui_hover', sine(1500, 0.03) * E(.03, 150), 0.25)
reg('ui_back', sine(glide(900, 600, 0.08), 0.08) * env(n_(.08), 0.002, 0.07), 0.4)
reg('objective', reverb(mix((0, bell_tone(587, 0.8, 4)), (0.1, bell_tone(880, 1.0, 3.5)), (0.2, bell_tone(1175, 1.2, 3))), 0.6, 0.3), 0.6)
reg('secret', reverb(mix(*[(i * 0.07, sine(f, 0.4) * E(.4, 8)) for i, f in enumerate([1175, 1397, 1760, 2349])]), 0.5, 0.3), 0.6)
reg('collect', reverb(mix(*[(i * 0.06, sq(f, 0.12, 0.25) * E(.12, 25) * 0.5) for i, f in enumerate([523, 659, 784, 1046, 1318])], *[(i * 0.06, sine(f, 0.3) * E(.3, 10)) for i, f in enumerate([523, 659, 784, 1046, 1318])]), 0.5, 0.25), 0.6)
reg('checkpoint', reverb(mix((0, sine(glide(400, 800, 0.3), 0.3) * env(n_(.3), 0.01, 0.28)), (0.15, bell_tone(1568, 0.6, 6) * 0.4)), 0.5, 0.3), 0.5)
reg('chapter', reverb(mix((0, sine(73, 3.0) * env(n_(3), 0.01, 2.9) * 0.9), (0, saw(146, 3.0) * env(n_(3), 0.3, 2.6) * 0.12), (0, lp(noise(3.0), 300) * E(3, 2) * 0.7), (0.0, bell_tone(293, 3.0, 1.2) * 0.4)), 1.2, 0.45), 0.8)
reg('death', reverb(mix((0, saw(glide(220, 110, 1.4), 1.4) * env(n_(1.4), 0.02, 1.3) * 0.4), (0, sine(glide(440, 220, 1.4), 1.4) * env(n_(1.4), 0.02, 1.3) * 0.5)), 0.8, 0.3), 0.7)
# ------------------------------------------------------------- player / blaster
def laser(f0, f1, d=0.22):
    x = sq(glide(f0, f1, d, 0.5), d, 0.3) * 0.35 + sine(glide(f0 * 2, f1 * 2, d, 0.5), d) * 0.5 + saw(glide(f0 * 0.5, f1 * 0.5, d), d) * 0.2
    return mix((0, lp(x, 7000) * env(n_(d), 0.002, d * 0.95)), (0, hp(noise(0.03), 3000) * E(.03, 120) * 0.3))
reg('laser', laser(2200, 380), 0.55); reg('laser2', laser(2500, 420, 0.2), 0.55); reg('laser3', laser(1900, 330, 0.24), 0.55)
reg('overheat', mix((0, hp(noise(1.2), 2500) * env(n_(1.2), 0.01, 0.2, 0.7, 0.5) * 0.6), (0, sq(1200, 0.1, 0.5) * env(n_(.1), 0.002, 0.09)), (0.15, sq(1200, 0.1, 0.5) * env(n_(.1), 0.002, 0.09))), 0.55)
reg('vent_done', mix((0, sine(glide(600, 1200, 0.15), 0.15) * env(n_(.15), 0.005, 0.14)), (0.12, sine(1500, 0.1) * E(.1, 30))), 0.4)
reg('hitmark', mix((0, sine(2600, 0.05) * E(.05, 70)), (0, click(0.01, 4000))), 0.4)
reg('hit_enemy', mix((0, lp(noise(0.12), 2500) * E(.12, 35)), (0, sine(glide(300, 120, 0.1), 0.1) * E(.1, 30) * 0.8), (0, hp(noise(0.05), 4000) * E(.05, 80) * 0.4)), 0.7)
reg('ko', reverb(mix((0, sine(glide(900, 300, 0.5), 0.5) * E(.5, 5) * 0.5), *[(0.08 * i, bell_tone(1600 + (i % 3) * 300, 0.3, 14) * 0.25) for i in range(6)]), 0.4, 0.25), 0.6)
reg('pulse', reverb(mix((0, sine(glide(160, 40, 0.8), 0.8) * E(.8, 4)), (0, lp(noise(0.6), 1200) * E(.6, 6) * 0.8), (0, sine(glide(1800, 200, 0.5), 0.5) * E(.5, 6) * 0.3)), 0.8, 0.3), 0.85)
reg('pulse_ready', mix((0, sine(880, 0.08) * E(.08, 30)), (0.07, sine(1320, 0.12) * E(.12, 25))), 0.35)
reg('jump', mix((0, lp(noise(0.12), 1800) * env(n_(.12), 0.01, 0.1) * 0.5), (0, sine(glide(220, 340, 0.1), 0.1) * E(.1, 30) * 0.3)), 0.4)
reg('land', mix((0, lp(noise(0.16), 600) * E(.16, 30)), (0, sine(glide(110, 55, 0.14), 0.14) * E(.14, 25))), 0.55)
reg('roll', mix((0, bp(noise(0.4), 300, 2200) * np.sin(np.linspace(0, np.pi, n_(.4))) ** 2), (0.25, lp(noise(0.12), 500) * E(.12, 30) * 0.6)), 0.55)
reg('hurt', mix((0, lp(noise(0.15), 1500) * E(.15, 25)), (0, sine(glide(250, 90, 0.2), 0.2) * E(.2, 15) * 0.8)), 0.7)
for i, (lo, hi, g) in enumerate([(200, 3500, 0.3)]): pass
def step(lo, hi, d=0.1, grit=0.0, thump=0.6):
    x = bp(noise(d), lo, hi) * E(d, 45) + lp(noise(d), 160) * E(d, 55) * thump
    if grit: x = x + hp(noise(d), 4500) * E(d, 30) * grit
    return x
reg('step_grass', mix((0, bp(noise(0.16), 1200, 6000) * env(n_(.16), 0.02, 0.13) * (0.5 + 0.5 * (rng.uniform(0, 1, n_(.16)) > 0.5))), (0, lp(noise(0.1), 200) * E(.1, 40) * 0.4)), 0.35)
reg('step_stone', step(400, 4000, 0.09, 0.4), 0.4)
reg('step_wood', mix((0, step(150, 1500, 0.12)), (0, sine(130, 0.08) * E(.08, 50) * 0.5)), 0.45)
reg('step_dirt', step(200, 2500, 0.12, 0.2, 0.8), 0.38)
reg('step_metal', mix((0, step(400, 6000, 0.1)), (0, bell_tone(380, 0.3, 14) * 0.3), (0, bell_tone(910, 0.25, 18) * 0.2)), 0.45)
reg('eat', mix(*[(0.12 * i, bp(noise(0.08), 600, 3500) * E(.08, 40)) for i in range(3)], (0.4, sine(glide(500, 900, 0.15), 0.15) * E(.15, 15) * 0.4)), 0.5)
reg('pickup', mix((0, lp(noise(0.05), 3000) * E(.05, 60)), (0.02, sine(glide(600, 1100, 0.1), 0.1) * E(.1, 30) * 0.5)), 0.45)
reg('key', reverb(mix(*[(0.05 * i, bell_tone(1318 * (1.26 ** i), 0.6, 6) * 0.4) for i in range(4)]), 0.6, 0.3), 0.6)
reg('teleport', reverb(mix((0, sine(glide(80, 2400, 2.0, 2.0), 2.0) * env(n_(2), 0.5, 1.4) * 0.5), (0, hp(noise(2.0), 1500) * env(n_(2), 1.2, 0.8) * 0.4),
                            (1.6, lp(noise(1.0), 3000) * E(1, 4) * 0.9), (1.6, sine(glide(400, 40, 0.8), 0.8) * E(.8, 4))), 1.0, 0.3), 0.85)
reg('phone_key', sine(1400, 0.07) * env(n_(.07), 0.002, 0.06), 0.4)
reg('phone_open', mix((0, click(0.02, 2000)), (0.03, sine(1300, 0.06) * E(.06, 60)), (0.09, sine(1750, 0.08) * E(.08, 50))), 0.45)
reg('phone_ok', mix((0, sine(1046, 0.1) * env(n_(.1), 0.002, 0.09)), (0.1, sine(1568, 0.25) * env(n_(.25), 0.002, 0.24))), 0.5)
# ------------------------------------------------------------- enemies & combat
reg('alert', mix((0, saw(glide(500, 1100, 0.12), 0.12) * env(n_(.12), 0.002, 0.11)), (0.1, sine(1400, 0.15) * E(.15, 20))), 0.5)
reg('ting', mix((0, bell_tone(2200, 0.5, 9)), (0, bell_tone(3300, 0.4, 12) * 0.5), (0, click(0.01, 6000))), 0.55)
reg('bow', mix((0, sine(glide(220, 180, 0.3), 0.3) * E(.3, 12) * 0.6), (0, click(0.02, 1500)), (0.02, bp(noise(0.25), 1500, 6000) * env(n_(.25), 0.01, 0.2) * 0.4)), 0.5)
reg('arrow_hit', mix((0, click(0.02, 1200)), (0, lp(noise(0.1), 1500) * E(.1, 40)), (0, sine(glide(400, 250, 0.15), 0.15) * E(.15, 25) * 0.5)), 0.6)
reg('swing', bp(noise(0.3), 400, 3000) * np.sin(np.linspace(0, np.pi, n_(.3))) ** 3, 0.5)
reg('throw', bp(noise(0.25), 300, 2000) * np.sin(np.linspace(0, np.pi, n_(.25))) ** 2, 0.4)
reg('splat', mix((0, lp(noise(0.25), 1200) * E(.25, 18)), (0, bp(noise(0.2), 1500, 5000) * E(.2, 30) * 0.5)), 0.6)
reg('slam', reverb(mix((0, lp(noise(0.6), 400) * E(.6, 6)), (0, sine(glide(90, 35, 0.5), 0.5) * E(.5, 5)), (0, bell_tone(300, 0.6, 8) * 0.3)), 0.6, 0.25), 0.9)
reg('bell', reverb(mix((0, bell_tone(98, 5.0, 0.7)), (0, bell_tone(196.5, 4.0, 1.0) * 0.5), (0, bell_tone(235, 4.0, 1.2) * 0.4), (0, click(0.03, 800))), 1.5, 0.35), 0.9)
reg('clank', mix((0, bell_tone(700, 0.25, 15) * 0.4), (0, bell_tone(1450, 0.2, 18) * 0.3), (0, lp(noise(0.08), 3000) * E(.08, 50))), 0.45)
reg('oink', lp(sq(glide(300, 220, 0.25) + 30 * np.sin(2 * np.pi * 35 * t_(0.25)), 0.25, 0.3), 1500) * env(n_(.25), 0.01, 0.22), 0.5)
reg('baa', lp(saw(220 + 25 * np.sin(2 * np.pi * 9 * t_(0.6)), 0.6), 2200) * env(n_(.6), 0.04, 0.5), 0.45)
reg('cluck', mix(*[(0.11 * i, bp(sq(glide(800, 600, 0.06), 0.06), 500, 3000) * E(.06, 40)) for i in range(4)]), 0.5)
reg('moo', lp(saw(glide(140, 110, 1.2) + 4 * np.sin(2 * np.pi * 5 * t_(1.2)), 1.2), 900) * env(n_(1.2), 0.15, 1.0), 0.55)
reg('neigh', lp(saw(glide(900, 500, 0.9) * (1 + 0.06 * np.sin(2 * np.pi * 22 * t_(0.9))), 0.9), 3000) * env(n_(.9), 0.03, 0.85), 0.45)
reg('squeak', sine(glide(2500, 3300, 0.12) + 200 * np.sin(2 * np.pi * 40 * t_(0.12)), 0.12) * env(n_(.12), 0.01, 0.1), 0.35)
reg('meow', lp(saw(glide(500, 700, 0.5, 0.5) * (1 + 0.1 * np.sin(np.linspace(0, np.pi, n_(.5)))), 0.5), 2500) * env(n_(.5), 0.03, 0.45), 0.45)
reg('purr', lp(noise(1.5), 250) * (0.5 + 0.5 * np.sin(2 * np.pi * 24 * t_(1.5))) * env(n_(1.5), 0.2, 0.3, 0.8, 0.4), 0.5)
# ------------------------------------------------------------- world
reg('chain_snap', mix((0, bell_tone(1800, 0.4, 10)), (0, click(0.02, 3000)), *[(0.04 * i, bell_tone(900 + 300 * i, 0.15, 25) * 0.3) for i in range(5)]), 0.6)
reg('crash', reverb(mix((0, lp(noise(1.2), 900) * E(1.2, 4)), (0, sine(glide(70, 30, 0.8), 0.8) * E(.8, 4)), *[(0.05 * i, bp(noise(0.15), 300, 2500) * E(.15, 25) * 0.5) for i in range(8)]), 0.8, 0.3), 0.9)
reg('creak', lp(saw(glide(140, 180, 1.0) + 20 * np.sin(2 * np.pi * 13 * t_(1.0)), 1.0) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * t_(1.0))), 1200) * env(n_(1), 0.1, 0.2, 0.8, 0.3), 0.4)
reg('portcullis', mix((0, mix(*[(0.05 * i, bell_tone(500 + 60 * (i % 4), 0.2, 20) * 0.3) for i in range(16)], *[(0.05 * i, click(0.02, 1500) * 0.4) for i in range(16)])), (0.85, lp(noise(0.6), 700) * E(.6, 7)), (0.85, bell_tone(260, 0.8, 5) * 0.5)), 0.8)
reg('door', mix((0, lp(noise(0.6), 900) * env(n_(.6), 0.05, 0.5) * 0.5), (0, saw(glide(110, 150, 0.6), 0.6) * env(n_(.6), 0.05, 0.5) * 0.15), (0.5, lp(noise(0.25), 500) * E(.25, 15))), 0.6)
reg('unlock', mix(*[(0.09 * i, click(0.02, 2500 if i % 2 else 1400) * 0.7) for i in range(6)], (0.6, lp(noise(0.2), 900) * E(.2, 20)), (0.62, bell_tone(660, 0.6, 7) * 0.4)), 0.6)
reg('gear', mix(*[(0.25 * i, click(0.03, 1200) * 0.6) for i in range(4)], *[(0.25 * i, bell_tone(420, 0.1, 30) * 0.2) for i in range(4)]), 0.4)
reg('zipline', mix((0, bp(noise(2.5), 800, 5000) * env(n_(2.5), 0.2, 0.2, 0.8, 0.5) * 0.6), (0, sine(glide(600, 1100, 2.5), 2.5) * env(n_(2.5), 0.3, 0.2, 0.5, 0.5) * 0.15)), 0.5)
reg('fire_loop', lp(noise(4.0), 1400) * (0.6 + 0.4 * (rng.uniform(0, 1, n_(4)) > 0.995)) + hp(noise(4.0), 3000) * (rng.uniform(0, 1, n_(4)) > 0.997) * 0.8, 0.5)
reg('whoosh_fire', mix((0, lp(noise(0.8), 1500) * np.sin(np.linspace(0, np.pi, n_(.8))) ** 2), (0, sine(glide(80, 50, 0.8), 0.8) * E(.8, 3) * 0.5)), 0.7)
reg('explosion', reverb(mix((0, lp(noise(2.0), 700) * E(2, 2.5)), (0, sine(glide(60, 25, 1.2), 1.2) * E(1.2, 3)), (0, hp(noise(0.3), 2000) * E(.3, 12) * 0.6)), 1.2, 0.35), 0.95)
reg('crate_break', mix((0, bp(noise(0.35), 200, 2500) * E(.35, 12)), *[(0.03 * i, click(0.03, 900 + 200 * i) * 0.5) for i in range(6)]), 0.65)
reg('barrel_hit', mix((0, sine(glide(130, 90, 0.3), 0.3) * E(.3, 10)), (0, lp(noise(0.2), 800) * E(.2, 25) * 0.6)), 0.6)
reg('pot_smash', mix((0, hp(noise(0.4), 1500) * E(.4, 10)), *[(0.02 * i, bell_tone(2000 + 500 * i, 0.15, 30) * 0.2) for i in range(6)]), 0.6)
reg('splash', mix((0, bp(noise(0.8), 400, 4000) * E(.8, 5)), (0, sine(glide(300, 80, 0.3), 0.3) * E(.3, 12) * 0.5)), 0.7)
reg('coin', mix((0, bell_tone(2600, 0.4, 10) * 0.5), (0.35, bp(noise(0.25), 500, 3000) * E(.25, 15) * 0.6)), 0.5)
reg('anvil', mix((0, bell_tone(1100, 1.2, 3)), (0, bell_tone(2700, 0.8, 5) * 0.5)), 0.6)
reg('bubbles', mix(*[(0.13 * i + rng.uniform(0, 0.05), sine(glide(300 + 100 * (i % 3), 600, 0.06), 0.06) * E(.06, 40)) for i in range(10)]), 0.4)
reg('trebuchet', mix((0, lp(saw(glide(60, 90, 1.0), 1.0), 400) * env(n_(1), 0.05, 0.9) * 0.6), (0.6, bp(noise(1.0), 200, 1500) * np.sin(np.linspace(0, np.pi, n_(1))) ** 2), (0.8, lp(noise(0.3), 500) * E(.3, 12))), 0.8)
reg('clockbell', reverb(mix((0, bell_tone(523, 2.0, 1.5)), (0.6, bell_tone(392, 2.0, 1.5))), 1.0, 0.35), 0.6)
reg('swoosh', bp(noise(0.5), 500, 3500) * np.sin(np.linspace(0, np.pi, n_(.5))) ** 2, 0.45)
reg('stinger', reverb(mix((0, saw(73, 1.5) * E(1.5, 2) * 0.4), (0, saw(110, 1.5) * E(1.5, 2) * 0.3), (0, saw(155.6, 1.5) * E(1.5, 2) * 0.3), (0, lp(noise(0.2), 600) * E(.2, 10))), 0.8, 0.3), 0.7)
# ambience loops
amb = lp(noise(6.0), 500) * 0.3
amb = mix((0, amb), *[(rng.uniform(0, 5.8), sine(glide(3000 + 800 * (i % 4), 4200, 0.12), 0.12) * E(.12, 20) * 0.3) for i in range(14)])[:len(amb)]
reg('amb_country', amb, 0.3)
reg('amb_lab', lp(saw(60, 6.0) * 0.2 + saw(120.3, 6.0) * 0.1 + noise(6.0) * 0.05, 600) + sine(7800, 6.0) * 0.004, 0.25)
reg('amb_dungeon', mix((0, lp(noise(6.0), 250) * 0.4), *[(rng.uniform(0, 5.6), bell_tone(1800 + rng.uniform(0, 600), 0.3, 18) * 0.3) for _ in range(5)]), 0.35)
reg('amb_crowd', bp(noise(6.0), 250, 1500) * (0.6 + 0.4 * lp(rng.uniform(0, 1, n_(6)), 3)), 0.3)

def write(name, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()
    p = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-', '-c:a', 'libvorbis', '-q:a', '2', '-ar', '32000', os.path.join(OUT, name + '.ogg')], input=pcm)
    assert p.returncode == 0
for k, v in S.items(): write(k, v)
print(len(S), 'sfx')
