"""Castle TIME procedural soundtrack: a small NumPy sequencer with synthesized instruments (no samples).
Engine adapted from Steve The PC Repair Man; medieval/synth instruments and all cues written for Castle TIME."""
import numpy as np, subprocess, os, sys
from scipy import signal
SR = 32000
OUT = os.path.join(os.path.dirname(__file__), '..', 'game', 'assets', 'audio', 'music'); os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(3)
def lp(x, f, o=2): b, a = signal.butter(o, min(f / (SR / 2), 0.99)); return signal.lfilter(b, a, x)
def hp(x, f, o=2): b, a = signal.butter(o, f / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def bp(x, lo, hi): b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return signal.lfilter(b, a, x)
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
def n(s):  # 'C4', 'F#3', 'Bb2'
    k = NOTE[s[0]]; i = 1
    if s[i] in '#b': k += 1 if s[i] == '#' else -1; i += 1
    return 12 * (int(s[i:]) + 1) + k
def ad(nn, a, d): a_ = max(1, int(a * SR)); e = np.ones(nn); e[:a_] = np.linspace(0, 1, a_); e *= np.exp(-np.arange(nn) / SR * d); return e
def rel(e, r=0.03): r_ = min(len(e), int(r * SR)); e[-r_:] *= np.linspace(1, 0, r_); return e
# ---------------------------------------------------------------- instruments: f(freq, dur) -> samples
def i_ep(f, d, vel=1):  # FM electric piano
    t = np.arange(int(SR * d)) / SR; e = ad(len(t), 0.003, 2.2); m = 1.8 * np.exp(-t * 6) * np.sin(2 * np.pi * f * 14 * t) * 0.15 + 1.2 * np.exp(-t * 3) * np.sin(2 * np.pi * f * t)
    return rel(e) * np.sin(2 * np.pi * f * t + m) * 0.5 * vel
def i_bass(f, d, vel=1):
    t = np.arange(int(SR * d)) / SR; ph = (f * t) % 1; x = (2 * ph - 1) * 0.6 + np.sin(2 * np.pi * f * t); e = ad(len(t), 0.004, 3.0)
    return lp(rel(e) * x, 300 + 900 * vel) * 0.7 * vel
def i_sub(f, d, vel=1): t = np.arange(int(SR * d)) / SR; return rel(ad(len(t), 0.01, 1.2)) * np.sin(2 * np.pi * f * t) * vel
def i_pad(f, d, vel=1):
    t = np.arange(int(SR * d)) / SR; x = sum(2 * ((f * dt * t + o) % 1) - 1 for dt, o in [(1, 0), (1.004, .3), (0.996, .6), (2.002, .1)]) / 4
    e = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.4 + 0.001); return lp(x * e, 1400) * 0.35 * vel
def i_pluck(f, d, vel=1, damp=0.994, bright=0.5):
    N = max(2, int(SR / f)); L = int(SR * d); x = np.zeros(L); burst = lp(rng.uniform(-1, 1, N * 4), 1500 + 6000 * bright)[-N:]; x[:N] = burst
    a = np.zeros(N + 2); a[0] = 1; a[N] = -damp * 0.5; a[N + 1] = -damp * 0.5
    return rel(signal.lfilter([1.0], a, x)) * 0.6 * vel
def i_trem(f, d, vel=1):  # surf guitar with tremolo
    x = i_pluck(f, d, vel, 0.997, 0.8); t = np.arange(len(x)) / SR; x = np.tanh(x * 2.5) * 0.6; return x * (0.65 + 0.35 * np.sin(2 * np.pi * 7 * t))
def i_lead(f, d, vel=1):
    t = np.arange(int(SR * d)) / SR; vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.3); ph = np.cumsum(f * vib) / SR % 1
    x = np.where(ph < 0.5, 1, -1) * 0.5 + (2 * ph - 1) * 0.5; return lp(x * rel(ad(len(t), 0.01, 0.8)), 2500) * 0.3 * vel
def i_bell(f, d, vel=1):
    t = np.arange(int(SR * d)) / SR; return sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * k) for r, a, k in [(1, 1, 2), (2.0, .4, 3), (3.01, .2, 5), (4.2, .1, 7)]) * 0.35 * vel
def i_str(f, d, vel=1):
    t = np.arange(int(SR * d)) / SR; vib = 1 + 0.004 * np.sin(2 * np.pi * 5 * t); ph = np.cumsum(f * vib) / SR % 1; x = 2 * ph - 1
    e = np.minimum(1, t / 0.15) * np.minimum(1, (d - t) / 0.2 + 0.001); return lp(x * e, 2200) * 0.25 * vel
def i_organ(f, d, vel=1):
    t = np.arange(int(SR * d)) / SR; x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(4 * np.pi * f * t) + 0.3 * np.sin(6 * np.pi * f * t) + 0.2 * np.sin(8 * np.pi * f * t)
    e = np.minimum(1, t / 0.01) * np.minimum(1, (d - t) / 0.03 + 0.001); return x * e * 0.2 * (1 + 0.1 * np.sin(2 * np.pi * 6 * t)) * vel
def i_arp(f, d, vel=1): t = np.arange(int(SR * d)) / SR; ph = f * t % 1; x = np.where(ph < 0.25, 1, -1); return lp(x * rel(ad(len(t), 0.002, 9)), 3500) * 0.22 * vel
# drums
def d_kick(v=1): t = np.arange(int(SR * .35)) / SR; f = 50 + 110 * np.exp(-t * 30); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * v
def d_snare(v=1): t = np.arange(int(SR * .25)) / SR; return (bp(rng.uniform(-1, 1, len(t)), 900, 7000) * np.exp(-t * 18) * 0.8 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.5) * v
def d_hat(v=1, open_=False): t = np.arange(int(SR * (.3 if open_ else .06))) / SR; return hp(rng.uniform(-1, 1, len(t)), 7000) * np.exp(-t * (8 if open_ else 60)) * 0.4 * v
def d_rim(v=1): t = np.arange(int(SR * .05)) / SR; return bp(rng.uniform(-1, 1, len(t)), 1500, 5000) * np.exp(-t * 80) * 0.6 * v + np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 90) * 0.3 * v
def d_brush(v=1): t = np.arange(int(SR * .2)) / SR; return bp(rng.uniform(-1, 1, len(t)), 2000, 9000) * np.exp(-t * 14) * 0.25 * v
def d_ride(v=1): t = np.arange(int(SR * .6)) / SR; return (hp(rng.uniform(-1, 1, len(t)), 5000) * 0.25 + sum(np.sin(2 * np.pi * f * t) for f in [3200, 4370, 5810]) * 0.04) * np.exp(-t * 5) * v
def d_tom(v=1, f=110): t = np.arange(int(SR * .4)) / SR; return np.sin(2 * np.pi * np.cumsum(f * (1 + 0.5 * np.exp(-t * 20))) / SR) * np.exp(-t * 8) * v
def d_timp(v=1, f=73): t = np.arange(int(SR * 1.2)) / SR; return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 1.5 * t)) * np.exp(-t * 3) * v + lp(rng.uniform(-1, 1, len(t)), 300) * np.exp(-t * 20) * 0.5 * v
DR = {'k': d_kick, 's': d_snare, 'h': d_hat, 'o': lambda v=1: d_hat(v, True), 'r': d_rim, 'b': d_brush, 'R': d_ride, 't': d_tom, 'T': d_timp}

class Song:
    def __init__(s, bpm, bars, beats=4): s.bpm = bpm; s.beat = 60 / bpm; s.len = bars * beats * s.beat; s.tracks = {}; s.bars = bars; s.bb = beats
    def tr(s, name, gain=1.0, pan=0):
        if name not in s.tracks: s.tracks[name] = [np.zeros(int(SR * (s.len + 4))), gain]
        return s.tracks[name][0]
    def note(s, track, inst, midi, beat, dur, vel=1.0, gain=1.0):
        buf = s.tr(track, gain); x = inst(mtof(midi), dur * s.beat + 0.05, vel); i = int(beat * s.beat * SR); buf[i:i + len(x)] += x[:len(buf) - i]
    def hit(s, track, key, beat, vel=1.0):
        buf = s.tr(track); x = DR[key](vel); i = int(beat * s.beat * SR); buf[i:i + len(x)] += x[:len(buf) - i]
    def drums(s, pattern, bars, start=0, track='drums', swing=0.0, vel=1.0, steps=16):
        # pattern: dict key -> string of length steps ('x' hit, 'g' ghost, '.' none)
        for b in range(start, start + bars):
            for k, p in pattern.items():
                for i, ch in enumerate(p):
                    if ch in 'xXg':
                        st = i * (s.bb / steps); st += swing * s.beat / 4 if (i % 2 == 1) else 0
                        s.hit(track, k, b * s.bb + st, vel * (0.35 if ch == 'g' else 1.25 if ch == 'X' else 1))
    def render(s, gains, reverb=0.2, master_lp=None, loop=True):
        out = np.zeros(int(SR * (s.len + 4)))
        for name, (buf, g) in s.tracks.items(): out += buf * gains.get(name, 1.0)
        if reverb:
            nn = int(SR * 1.6); ir = rng.normal(0, 1, nn) * np.exp(-np.arange(nn) / SR * 3.5); ir = lp(ir, 5000); ir /= np.sqrt(np.sum(ir ** 2))
            wet = signal.fftconvolve(out, ir)[:len(out)] * 0.6; out = out + wet * reverb
        if master_lp: out = lp(out, master_lp)
        L = int(SR * s.len)
        if loop: tail = out[L:]; out = out[:L].copy(); out[:len(tail)] += tail  # wrap tail -> seamless loop
        else: out = out[:L + int(SR * 2)]
        out = np.tanh(out / (np.max(np.abs(out)) + 1e-9) * 1.3) * 0.9; return out

def chord_notes(root, kind):
    iv = {'maj': [0, 4, 7], 'min': [0, 3, 7], 'maj7': [0, 4, 7, 11], 'm7': [0, 3, 7, 10], '7': [0, 4, 7, 10], 'm6': [0, 3, 7, 9], 'mM7': [0, 3, 7, 11], 'm9': [0, 3, 7, 10, 14], 'sus': [0, 5, 7], 'dim': [0, 3, 6]}[kind]
    return [root + i for i in iv]

def write(name, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()
    p = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-', '-c:a', 'libvorbis', '-q:a', '2', os.path.join(OUT, name + '.ogg')], input=pcm); assert p.returncode == 0


# ---------------------------------------------------------------- Castle TIME instruments
def i_lute(f, d, vel=1):
    x = i_pluck(f, min(d + 0.6, 3.0), vel, 0.991, 0.65); return bp(x, 120, 5000) * 1.3 + lp(x, 400) * 0.3
def i_recorder(f, d, vel=1):
    t = np.arange(int(SR * d)) / SR; vib = 1 + 0.005 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.25)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR; x = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    br = bp(rng.uniform(-1, 1, len(t)), f, min(f * 4, 12000)) * 0.08
    e = np.minimum(1, t / 0.04) * np.minimum(1, (d - t) / 0.06 + 0.001); return (x + br) * e * 0.28 * vel
def i_gurdy(f, d, vel=1):   # hurdy-gurdy drone with buzz
    t = np.arange(int(SR * d)) / SR; ph = (f * t) % 1; x = (2 * ph - 1) * 0.5 + np.sin(2 * np.pi * f * t)
    buzz = (np.sin(2 * np.pi * 6.5 * t) > 0.6) * 0.25 * np.sign(np.sin(2 * np.pi * f * 2 * t))
    e = np.minimum(1, t / 0.2) * np.minimum(1, (d - t) / 0.3 + 0.001); return lp((x + buzz) * e, 1800) * 0.18 * vel
def i_choir(f, d, vel=1):
    t = np.arange(int(SR * d)) / SR; x = np.zeros(len(t))
    for dt in (1.0, 1.003, 0.997): x += 2 * ((f * dt * t) % 1) - 1
    y = bp(x, 500, 1100) * 1.0 + bp(x, 700, 1300) * 0.6 + bp(x, 2300, 2900) * 0.25
    e = np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.5 + 0.001); return y * e * 0.32 * vel * (1 + 0.05 * np.sin(2 * np.pi * 4.8 * t))
def i_saw(f, d, vel=1):  # synth bass pulse
    t = np.arange(int(SR * d)) / SR; ph = (f * t) % 1; ph2 = (f * 1.005 * t) % 1; x = (2 * ph - 1) + (2 * ph2 - 1)
    e = ad(len(t), 0.004, 4.0); return lp(rel(e) * x, 500 + 1200 * vel) * 0.3 * vel
def i_synth(f, d, vel=1):  # bright arpeggio
    t = np.arange(int(SR * d)) / SR; ph = (f * t) % 1; x = np.where(ph < 0.5, 1.0, -1.0) * 0.6 + (2 * ph - 1) * 0.4
    return lp(x * rel(ad(len(t), 0.002, 7)), 4200) * 0.18 * vel
def i_brass(f, d, vel=1):
    t = np.arange(int(SR * d)) / SR; ph = np.cumsum(f * (1 + 0.003 * np.sin(2 * np.pi * 5 * t))) / SR % 1; x = 2 * ph - 1
    env = np.minimum(1, t / 0.06) * np.minimum(1, (d - t) / 0.12 + 0.001); cut = 600 + 2500 * np.minimum(1, t / 0.15)
    return lp(x * env, 2200) * 0.22 * vel
def d_taiko(v=1): t = np.arange(int(SR * .9)) / SR; f = 55 + 60 * np.exp(-t * 25); return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5) + lp(rng.uniform(-1, 1, len(t)), 500) * np.exp(-t * 30) * 0.6) * v
def d_frame(v=1): t = np.arange(int(SR * .3)) / SR; return (np.sin(2 * np.pi * np.cumsum(140 * (1 + 0.4 * np.exp(-t * 30))) / SR) * np.exp(-t * 12) + bp(rng.uniform(-1, 1, len(t)), 800, 4000) * np.exp(-t * 35) * 0.5) * 0.8 * v
def d_tick(v=1): t = np.arange(int(SR * .05)) / SR; return (np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 120) + bp(rng.uniform(-1, 1, len(t)), 2000, 6000) * np.exp(-t * 150) * 0.4) * 0.5 * v
def d_tock(v=1): t = np.arange(int(SR * .06)) / SR; return (np.sin(2 * np.pi * 1300 * t) * np.exp(-t * 90) + bp(rng.uniform(-1, 1, len(t)), 900, 3000) * np.exp(-t * 120) * 0.4) * 0.5 * v
def d_bigbell(v=1):
    t = np.arange(int(SR * 3.0)) / SR; return sum(a * np.sin(2 * np.pi * 98 * r * t) * np.exp(-t * k) for r, a, k in [(1, 1, 0.8), (2.0, .5, 1.2), (2.4, .4, 1.5), (3.0, .3, 2), (4.2, .2, 3), (5.4, .12, 4)]) * 0.5 * v
def d_tamb(v=1): t = np.arange(int(SR * .18)) / SR; return hp(rng.uniform(-1, 1, len(t)), 6000) * np.exp(-t * 22) * 0.35 * v * (1 + 0.5 * np.sin(2 * np.pi * 40 * t))
DR.update({'K': d_taiko, 'f': d_frame, 'c': d_tick, 'C': d_tock, 'B': d_bigbell, 'm': d_tamb})

D = n('D3')
DORIAN = [0, 2, 3, 5, 7, 9, 10]
def deg(root, i): o, k = divmod(i, 7); return root + 12 * o + DORIAN[k]
THEME = [(0, 1), (2, .5), (4, .5), (3, 1), (2, .5), (1, .5), (0, 1.5), (-1, .5), (0, 2)]          # "Castle TIME" motif (scale degrees, beats)
THEME_B = [(4, 1), (5, .5), (6, .5), (7, 1), (6, .5), (4, .5), (5, 1), (3, 1), (4, 2)]
def melody(s, track, inst, root, mel, start, vel=1.0, oct_=0):
    b = start
    for d_, l in mel: s.note(track, inst, deg(root, d_) + 12 * oct_, b, l * 0.95, vel); b += l
    return b

def cue_title():
    s = Song(96, 24)
    chords = [(0, 'min'), (-2, 'maj'), (3, 'maj'), (4, 'min')]   # Dm  C  F  Am-ish (dorian colours)
    for b in range(24):
        r = deg(D, chords[b % 4][0]); sec = b // 8
        for k in range(8): s.note('arp', i_synth, r + [12, 19, 24, 19, 15, 19, 24, 27][k] - (0 if chords[b % 4][1] == 'maj' else 0), b * 4 + k * 0.5, 0.45, 0.6 + 0.2 * (k % 2 == 0))
        s.note('drone', i_gurdy, r, b * 4, 4, 0.8); s.note('drone', i_gurdy, r + 7, b * 4, 4, 0.5)
        if sec >= 1: s.note('choir', i_choir, r + 12, b * 4, 4, 0.7); s.note('choir', i_choir, r + 19, b * 4, 4, 0.5)
        s.note('bass', i_saw, r - 12, b * 4, 1.5, 0.8); s.note('bass', i_saw, r - 12, b * 4 + 2.5, 1, 0.6)
    for rep in range(3):
        st = 32 * rep + (0 if rep == 0 else 0)
        if rep >= 1: melody(s, 'lead', i_recorder, D, THEME, st + 0, 0.9, 1); melody(s, 'lead', i_recorder, D, THEME_B, st + 16, 0.9, 1)
        else: melody(s, 'lute', i_lute, D, THEME, st + 0, 0.9, 1); melody(s, 'lute', i_lute, D, THEME_B, st + 16, 0.9, 1)
    s.drums({'K': 'x.......x...x...', 'f': '....x.......x.x.', 'm': '..x...x...x...x.'}, 16, start=8)
    return s.render({'arp': 0.5, 'drone': 0.7, 'choir': 0.6, 'bass': 0.8, 'lead': 1.0, 'lute': 1.1, 'drums': 0.8}, reverb=0.35)

def cue_lab():
    s = Song(100, 16)
    prog = [(n('A2'), 'm7'), (n('F2'), 'maj7'), (n('C3'), 'maj7'), (n('G2'), '7')]
    for b in range(16):
        r, k = prog[b % 4]; cn = chord_notes(r + 12, k)
        s.note('pad', i_pad, cn[0], b * 4, 4, 0.6); s.note('pad', i_pad, cn[1], b * 4, 4, 0.5); s.note('pad', i_pad, cn[2], b * 4, 4, 0.45)
        for j in range(16): s.note('arp', i_synth, cn[j % len(cn)] + 12 + (12 if j % 8 >= 4 else 0), b * 4 + j * 0.25, 0.22, 0.5)
        s.note('bass', i_saw, r, b * 4, 0.8, 0.8); s.note('bass', i_saw, r, b * 4 + 1.5, 0.4, 0.6); s.note('bass', i_saw, r + 12, b * 4 + 3, 0.5, 0.5)
    s.drums({'k': 'x.......x.......', 's': '....x.......x...', 'h': '..x...x...x...x.'}, 12, start=4, vel=0.7)
    return s.render({'pad': 0.8, 'arp': 0.55, 'bass': 0.7, 'drums': 0.6}, reverb=0.3)

def cue_town():  # medieval saltarello-ish dance
    s = Song(132, 24, beats=3)
    prog = [0, 0, -2, -2, 3, 3, 4, 0]
    for b in range(24):
        r = deg(D, prog[b % 8])
        s.note('drone', i_gurdy, D, b * 3, 3, 0.7); s.note('drone', i_gurdy, D + 7, b * 3, 3, 0.4)
        s.note('lute', i_lute, r, b * 3, 1, 0.9); s.note('lute', i_lute, r + 7, b * 3 + 1, 0.5, 0.6); s.note('lute', i_lute, r + 12, b * 3 + 1.5, 0.5, 0.6); s.note('lute', i_lute, r + 7, b * 3 + 2, 1, 0.6)
    mel = [(7, 1), (6, .5), (5, .5), (4, 1), (2, 1), (3, .5), (4, .5), (2, 1), (0, 2), (4, 1), (5, 1), (6, 1), (7, 1.5), (6, .5), (4, 1), (5, .5), (4, .5), (3, 1), (2, 1), (1, 1), (0, 2), (-1, 1)]
    t = 0
    while t < 24 * 3 - 12:
        t = melody(s, 'lead', i_recorder, D, mel, t, 0.85, 1)
    s.drums({'f': 'x..x.x', 'm': '..x..x'}, 24, track='drums', steps=6)
    return s.render({'drone': 0.6, 'lute': 0.9, 'lead': 0.9, 'drums': 0.8}, reverb=0.3)

def cue_battle():
    s = Song(140, 16)
    prog = [0, 0, -2, -1, 0, 0, 3, 4]
    for b in range(16):
        r = deg(D, prog[b % 8]) - 12
        for k in range(8): s.note('bass', i_saw, r + (12 if k in (3, 6) else 0), b * 4 + k * 0.5, 0.45, 0.9)
        s.note('str', i_str, r + 24, b * 4, 4, 0.7); s.note('str', i_str, r + 31, b * 4, 4, 0.5); s.note('str', i_str, r + 27, b * 4, 4, 0.45)
        if b >= 4: s.note('brass', i_brass, r + 24, b * 4, 1.5, 0.8); s.note('brass', i_brass, r + 22, b * 4 + 1.5, 0.5, 0.7); s.note('brass', i_brass, r + 24 + (3 if b % 2 else 5), b * 4 + 2, 2, 0.8)
    s.drums({'K': 'x..x..x...x..x..', 'f': '....x.......x...', 's': '....x.......x..x', 'h': 'x.x.x.x.x.x.x.x.'}, 16, vel=0.9)
    for b in range(8, 16): melody(s, 'lead', i_synth, D, THEME, b * 4 if b == 8 else 1e9, 1.0, 2) if b == 8 else None
    melody(s, 'lead', i_synth, D, THEME_B, 48, 1.0, 2)
    return s.render({'bass': 0.8, 'str': 0.6, 'brass': 0.7, 'drums': 1.0, 'lead': 0.6}, reverb=0.25)

def cue_spire():
    s = Song(90, 16)
    for b in range(16):
        r = deg(D, [0, -2, 3, 1][b % 4]) 
        s.note('choir', i_choir, r, b * 4, 4, 0.8); s.note('choir', i_choir, r + 7, b * 4, 4, 0.6); s.note('choir', i_choir, r + 15, b * 4, 4, 0.4)
        s.note('bass', i_sub, r - 24, b * 4, 4, 0.8)
        for k in range(8): s.note('arp', i_lute, r + [12, 15, 19, 24, 19, 15, 12, 10][k], b * 4 + k * 0.5, 0.5, 0.55)
    s.drums({'c': 'x...x...x...x...', 'C': '..x...x...x...x.'}, 16, vel=0.8)
    s.drums({'K': 'x.......x.......'}, 8, start=8, vel=0.8)
    melody(s, 'lead', i_recorder, D, THEME, 32, 0.8, 1); melody(s, 'lead', i_recorder, D, THEME_B, 48, 0.8, 1)
    return s.render({'choir': 0.7, 'bass': 0.7, 'arp': 0.5, 'drums': 0.7, 'lead': 0.8}, reverb=0.45)

def cue_boss():
    s = Song(150, 16)
    for b in range(16):
        r = deg(D, [0, 0, -1, -2][b % 4]) - 12
        for k in range(16): s.note('bass', i_saw, r + (0 if k % 4 else 12) + (7 if k in (6, 14) else 0), b * 4 + k * 0.25, 0.22, 0.85)
        s.note('choir', i_choir, r + 24, b * 4, 4, 0.7); s.note('choir', i_choir, r + 27, b * 4, 4, 0.6)
        s.note('brass', i_brass, r + 24, b * 4, 0.75, 0.9); s.note('brass', i_brass, r + 24, b * 4 + 0.75, 0.75, 0.9); s.note('brass', i_brass, r + 27, b * 4 + 1.5, 2.5, 0.9)
    s.drums({'K': 'x..x..x.x..x..x.', 's': '....x.......x...', 'h': 'xxxxxxxxxxxxxxxx'}, 16, vel=0.95)
    for b in range(0, 16, 4): s.hit('drums', 'B', b * 4, 0.9)
    return s.render({'bass': 0.8, 'choir': 0.55, 'brass': 0.7, 'drums': 1.0}, reverb=0.3)

def cue_dungeon():
    s = Song(70, 12)
    for b in range(12):
        r = deg(D, [0, 1, 0, -2][b % 4]) - 12
        s.note('drone', i_gurdy, r, b * 4, 4, 0.6); s.note('drone', i_str, r + 13, b * 4, 4, 0.35)
        s.note('pad', i_choir, r + 24, b * 4, 4, 0.4)
        for k in (0, 2.75): s.note('drip', i_bell, r + 36 + [7, 12, 10, 15][b % 4], b * 4 + k, 1, 0.35)
    s.drums({'K': 'x...............', 'f': '........x.......'}, 12, vel=0.6)
    return s.render({'drone': 0.7, 'pad': 0.6, 'drip': 0.6, 'drums': 0.8}, reverb=0.6)

def cue_escape():
    s = Song(168, 16)
    for b in range(16):
        r = deg(D, [0, -2, -3, -1][b % 4]) - 12
        for k in range(16): s.note('str', i_str, r + 24 + (12 if k % 2 else 0), b * 4 + k * 0.25, 0.24, 0.8)
        for k in range(8): s.note('bass', i_saw, r, b * 4 + k * 0.5, 0.4, 0.9)
        s.note('brass', i_brass, r + 24, b * 4, 2, 0.8); s.note('brass', i_brass, r + 22, b * 4 + 2, 2, 0.8)
        s.note('alarm', i_synth, r + 36 + (12 if b % 2 else 0), b * 4, 0.5, 0.5); s.note('alarm', i_synth, r + 36 + 7, b * 4 + 2, 0.5, 0.5)
    s.drums({'K': 'x.x...x.x.x...x.', 's': '....x.......x...', 'h': 'x.x.x.x.x.x.x.x.', 'f': '..x...x...x...xx'}, 16, vel=1.0)
    return s.render({'str': 0.55, 'bass': 0.8, 'brass': 0.7, 'alarm': 0.4, 'drums': 1.0}, reverb=0.2)

def cue_ending():
    s = Song(84, 16)
    chords = [(0, 'min'), (3, 'maj'), (-2, 'maj'), (4, 'min')]
    for b in range(16):
        r = deg(D, chords[b % 4][0]) + 12
        cn = chord_notes(r, chords[b % 4][1])
        for k in range(6): s.note('lute', i_lute, cn[k % 3] + (12 if k >= 3 else 0), b * 4 + k * 0.66, 0.6, 0.6)
        s.note('pad', i_pad, cn[0], b * 4, 4, 0.5); s.note('pad', i_pad, cn[1], b * 4, 4, 0.4); s.note('pad', i_pad, cn[2], b * 4, 4, 0.35)
        s.note('bass', i_sub, r - 24, b * 4, 4, 0.7)
    melody(s, 'lead', i_recorder, D, THEME, 16, 0.8, 1); melody(s, 'lead', i_recorder, D, THEME_B, 32, 0.8, 1); melody(s, 'lead', i_synth, D, THEME, 48, 0.8, 2)
    return s.render({'lute': 0.9, 'pad': 0.7, 'bass': 0.6, 'lead': 0.9}, reverb=0.4)

if __name__ == '__main__':
    only = sys.argv[1:]
    for nm, fn in [('title', cue_title), ('lab', cue_lab), ('town', cue_town), ('battle', cue_battle), ('spire', cue_spire), ('boss', cue_boss),
                   ('dungeon', cue_dungeon), ('escape', cue_escape), ('ending', cue_ending)]:
        if only and nm not in only: continue
        x = fn(); write(nm, x); print(nm, round(len(x) / SR, 1), 's')
