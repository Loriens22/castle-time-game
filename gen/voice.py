"""Castle TIME: generate every voiced line with Kokoro (local, open-source TTS, kokoro-onnx) + NumPy/SciPy effects -> OGG Vorbis.
usage: <venv with kokoro-onnx>/bin/python gen/voice.py [--force] [ids...]   (model files: KOKORO_DIR, default ../steve-pc-repair-man/tools/kokoro)"""
import os, sys, json, subprocess, numpy as np, soundfile as sf
from scipy import signal
sys.path.insert(0, os.path.dirname(__file__))
from dialogue import L, VOICES
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'game', 'assets', 'audio', 'vo')
DUR = os.path.join(HERE, '..', 'game', 'data', 'vo.json')
KDIR = os.environ.get('KOKORO_DIR', '/workspace/steve-pc-repair-man/tools/kokoro')
os.makedirs(OUT, exist_ok=True)
SR = 24000
rng = np.random.default_rng(7)

def ir(seconds, decay, sr=SR, pre=0.0):
    n = int(seconds * sr); t = np.arange(n) / sr
    x = rng.standard_normal(n) * np.exp(-t / decay)
    b, a = signal.butter(2, 4500 / (sr / 2)); x = signal.lfilter(b, a, x)
    x[0] = 0; return x / np.sqrt(np.sum(x ** 2))

def reverb(x, mix, seconds=0.6, decay=0.12):
    w = signal.fftconvolve(x, ir(seconds, decay))[:len(x) + int(seconds * SR)]
    y = np.concatenate([x, np.zeros(len(w) - len(x))])
    return y * (1 - mix * 0.5) + w * mix

def shelf(x, f, gain_db, kind='low'):
    b, a = signal.butter(2, f / (SR / 2), 'low' if kind == 'low' else 'high')
    band = signal.lfilter(b, a, x)
    return x + band * (10 ** (gain_db / 20) - 1)

def vibrato(x, rate=5.0, depth_ms=0.6):
    n = np.arange(len(x)); d = (depth_ms / 1000 * SR) * (1 + np.sin(2 * np.pi * rate * n / SR)) / 2 + 2
    idx = np.clip(n - d, 0, len(x) - 1); i0 = idx.astype(int); fr = idx - i0
    i1 = np.minimum(i0 + 1, len(x) - 1)
    return x[i0] * (1 - fr) + x[i1] * fr

def fx(x, kind):
    if kind == 'warm':
        x = shelf(x, 200, 2.0); x = reverb(x, 0.10, 0.4, 0.07)
    elif kind == 'old':
        x = vibrato(x, 5.2, 0.5); b, a = signal.butter(2, 6000 / (SR / 2)); x = signal.lfilter(b, a, x)
        x = x * (1 + 0.04 * np.sin(2 * np.pi * 6 * np.arange(len(x)) / SR)); x = reverb(x, 0.10, 0.4, 0.07)
    elif kind == 'deep':
        x = shelf(x, 160, 4.0); x = reverb(x, 0.10, 0.4, 0.07)
    elif kind == 'robot':
        n = np.arange(len(x)); ring = x * np.sin(2 * np.pi * 55 * n / SR)
        d = int(0.009 * SR); comb = x.copy()
        for k in range(1, 5): comb[k * d:] += x[:-k * d] * (0.55 ** k)
        x = 0.62 * comb + 0.38 * ring
        x = np.round(x * 90) / 90 * 0.5 + x * 0.5
        x = reverb(x, 0.35, 1.6, 0.4)
    elif kind == 'radio':
        b, a = signal.butter(3, [350 / (SR / 2), 3200 / (SR / 2)], 'band'); x = signal.lfilter(b, a, x)
        x = np.tanh(x * 2.2) / 1.6 + rng.standard_normal(len(x)) * 0.004
    elif kind == 'outdoor':
        b, a = signal.butter(2, 120 / (SR / 2), 'high'); x = signal.lfilter(b, a, x); x = reverb(x, 0.18, 0.9, 0.18)
    elif kind == 'ai':   # SIBYL: slight chorus + shimmer + airy reverb
        n = np.arange(len(x)); d = (0.004 * SR) * (1 + 0.5 * np.sin(2 * np.pi * 0.7 * n / SR))
        idx = np.clip(n - d, 0, len(x) - 1).astype(int); x = 0.7 * x + 0.3 * x[idx]
        b, a = signal.butter(2, 180 / (SR / 2), 'high'); x = signal.lfilter(b, a, x)
        x = x + 0.12 * x * np.sin(2 * np.pi * 1800 * n / SR); x = reverb(x, 0.22, 0.9, 0.25)
    elif kind == 'helmet':
        d = int(0.006 * SR); y = x.copy(); y[d:] += 0.5 * x[:-d]; b, a = signal.butter(2, [200 / (SR / 2), 3500 / (SR / 2)], 'band'); x = signal.lfilter(b, a, y); x = reverb(x, 0.15, 0.5, 0.1)
    elif kind == 'bell':
        d = int(0.011 * SR); y = x.copy()
        for k in range(1, 6): y[k * d:] += x[:-k * d] * (0.6 ** k)
        x = shelf(y, 150, 5.0); x = reverb(x, 0.3, 1.2, 0.35)
    elif kind == 'dungeon':
        x = reverb(x, 0.3, 1.4, 0.45)
    elif kind == 'room':
        x = reverb(x, 0.14, 0.5, 0.09)
    return x

def norm(x, target_rms=0.085):
    r = np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2) + 1e-9) if np.any(np.abs(x) > 0.01) else 0.1
    x = x * (target_rms / r)
    pk = np.max(np.abs(x)); 
    if pk > 0.95: x = x * 0.95 / pk
    return x

def mrrp():
    t = np.arange(int(0.55 * SR)) / SR
    f = 420 + 260 * np.sin(np.pi * np.clip(t / 0.5, 0, 1)) ** 0.7
    ph = 2 * np.pi * np.cumsum(f) / SR
    trill = 0.6 + 0.4 * np.sin(2 * np.pi * 28 * t) * (t < 0.18)
    env = np.minimum(1, t / 0.03) * np.exp(-((t - 0.25) / 0.22) ** 2)
    x = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)) * env * trill
    b, a = signal.butter(2, [500 / (SR / 2), 3000 / (SR / 2)], 'band')
    return reverb(signal.lfilter(b, a, x), 0.1, 0.4, 0.07)

def bawk():
    t = np.arange(int(0.5 * SR)) / SR; out = np.zeros_like(t)
    for st, f0 in ((0.0, 700), (0.16, 850)):
        m = (t >= st) & (t < st + 0.22); tt = t[m] - st
        f = f0 * (1 + 0.6 * np.exp(-tt * 18)); ph = 2 * np.pi * np.cumsum(f) / SR
        out[m] += (np.sign(np.sin(ph)) * 0.3 + np.sin(ph * 2) * 0.5) * np.exp(-tt * 9) * np.minimum(1, tt / 0.01)
    b, a = signal.butter(2, [400 / (SR / 2), 4000 / (SR / 2)], 'band'); return reverb(signal.lfilter(b, a, out), 0.1, 0.4, 0.07)

def main():
    force = '--force' in sys.argv; only = [a for a in sys.argv[1:] if not a.startswith('--')]
    durs = json.load(open(DUR)) if os.path.exists(DUR) else {}
    k = None
    for l in L:
        if only and l['id'] not in only: continue
        mp3 = os.path.join(OUT, l['id'] + '.ogg')
        if os.path.exists(mp3) and not force and l['id'] in durs: continue
        v = VOICES[l['who']]
        if v is None:
            y = bawk()
        else:
            if k is None:
                from kokoro_onnx import Kokoro
                k = Kokoro(os.path.join(KDIR, 'kokoro-v1.0.onnx'), os.path.join(KDIR, 'voices-v1.0.bin'))
            p = v['pitch']
            s, sr = k.create(l['say'], voice=v['voice'], speed=v['speed'] / p, lang=v['lang'])
            s = np.asarray(s, dtype=np.float64)
            if abs(p - 1) > 1e-3:  # resample: lowers pitch AND slows by p; speed was pre-compensated
                s = signal.resample_poly(s, int(round(1000 / p)), 1000)
            y = fx(s, v['fx'])
        y = np.concatenate([np.zeros(int(0.03 * SR)), norm(y), np.zeros(int(0.08 * SR))])
        wav = '/tmp/_vo.wav'; sf.write(wav, y.astype(np.float32), SR)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-ac', '1', '-ar', '24000', '-c:a', 'libvorbis', '-q:a', '1', mp3], check=True)
        durs[l['id']] = round(len(y) / SR, 3)
        print(l['id'], durs[l['id']])
    json.dump(durs, open(DUR, 'w'), indent=0)
main()
