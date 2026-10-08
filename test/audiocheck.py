"""Headless audio check for the web build.
Hooks Web Audio (AudioContext state, started sources, RMS of everything routed to the destination)
and prints a timeline.  usage: python3 test/audiocheck.py URL [--gesture] [--mobile] [--wait 60] [--clicks x,y@t;...] [--keys KEY@t;...]
--gesture: do NOT pass --autoplay-policy=no-user-gesture-required (real-browser behaviour: audio needs a tap/click)."""
import sys, time, argparse, json
from playwright.sync_api import sync_playwright

HOOK = r"""
(() => {
  const W = window; W.__au = {ctxs: [], started: 0, startedBuf: 0, media: 0, rmsMax: 0, rms: 0, analysers: [], log: []};
  const Orig = W.AudioContext || W.webkitAudioContext;
  function attach(ctx) {
    try { const an = ctx.createAnalyser(); an.fftSize = 2048; an.__isProbe = true; W.__au.analysers.push(an); ctx.__probe = an; }
    catch (e) { W.__au.log.push('analyser fail ' + e); }
  }
  class Hooked extends Orig {
    constructor(...a) { super(...a); W.__au.ctxs.push(this); W.__au.log.push('ctx created sr=' + this.sampleRate + ' state=' + this.state);
      this.addEventListener('statechange', () => W.__au.log.push('ctx state -> ' + this.state)); attach(this); }
  }
  W.AudioContext = Hooked; if (W.webkitAudioContext) W.webkitAudioContext = Hooked;
  const oc = AudioNode.prototype.connect;
  AudioNode.prototype.connect = function (dst, ...r) {
    const res = oc.call(this, dst, ...r);
    try { if (dst instanceof AudioDestinationNode && !this.__isProbe && this.context.__probe) oc.call(this, this.context.__probe); } catch (e) {}
    return res;
  };
  const os = AudioScheduledSourceNode.prototype.start;
  AudioScheduledSourceNode.prototype.start = function (...a) { W.__au.started++; if (this instanceof AudioBufferSourceNode) W.__au.startedBuf++; return os.apply(this, a); };
  const ob = AudioBufferSourceNode.prototype.start;
  AudioBufferSourceNode.prototype.start = function (...a) { W.__au.started++; W.__au.startedBuf++; W.__au.log.push('src start buffer=' + (this.buffer ? this.buffer.duration.toFixed(2) + 's' : '?') + ' at ctx t=' + this.context.currentTime.toFixed(1)); return ob.apply(this, a); };
  const op = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function () { W.__au.media++; return op.call(this); };
  const buf = new Float32Array(2048);
  setInterval(() => {
    let m = 0;
    for (const an of W.__au.analysers) { an.getFloatTimeDomainData(buf); let s = 0; for (let i = 0; i < buf.length; i++) s += buf[i] * buf[i]; m = Math.max(m, Math.sqrt(s / buf.length)); }
    W.__au.rms = m; W.__au.rmsMax = Math.max(W.__au.rmsMax, m);
  }, 50);
})();
"""

ap = argparse.ArgumentParser()
ap.add_argument('url'); ap.add_argument('--gesture', action='store_true'); ap.add_argument('--wait', type=float, default=60)
ap.add_argument('--clicks', default=''); ap.add_argument('--keys', default=''); ap.add_argument('--mobile', action='store_true')
ap.add_argument('--all', action='store_true'); ap.add_argument('--shots', default='', help='t,t,... -> /tmp/au_<t>.png')
a = ap.parse_args()
ev = []
for c in filter(None, a.clicks.split(';')):
    xy, t = c.split('@'); ev.append((float(t), 'click', tuple(map(float, xy.split(',')))))
for k in filter(None, a.keys.split(';')):
    key, t = k.split('@'); ev.append((float(t), 'key', key))
for s in filter(None, a.shots.split(',')): ev.append((float(s), 'shot', None))
step = 2.0; t = step
while t <= a.wait: ev.append((t, 'probe', None)); t += step
ev.sort(key=lambda e: e[0])
args = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
if not a.gesture: args.append('--autoplay-policy=no-user-gesture-required')
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=args)
    if a.mobile:
        ctx = b.new_context(viewport={'width': 844, 'height': 390}, device_scale_factor=2, is_mobile=True, has_touch=True,
                            user_agent='Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36')
    else:
        ctx = b.new_context(viewport={'width': 1280, 'height': 720})
    ctx.add_init_script(HOOK)
    pg = ctx.new_page(); logs = []; bad = []
    pg.on('console', lambda m: logs.append((m.type, m.text)))
    pg.on('pageerror', lambda e: logs.append(('pageerror', str(e))))
    pg.on('response', lambda r: bad.append((r.status, r.url)) if r.status >= 400 else None)
    t0 = time.time(); pg.goto(a.url, wait_until='load', timeout=120000)
    for t, kind, arg in ev:
        dt = t - (time.time() - t0)
        if dt > 0: time.sleep(dt)
        if kind == 'click':
            (pg.touchscreen.tap(*arg) if a.mobile else pg.mouse.click(*arg)); print('%5.1f tap %s' % (t, arg), flush=True)
        elif kind == 'key':
            k, _, hold = arg.partition('~'); pg.keyboard.down(k); time.sleep(float(hold or 0.15)); pg.keyboard.up(k); print('%5.1f key %s' % (t, arg), flush=True)
        elif kind == 'shot':
            pg.screenshot(path='/tmp/au_%03d.png' % int(t)); print('%5.1f shot' % t, flush=True)
        else:
            st = pg.evaluate("() => ({states: __au.ctxs.map(c => c.state), started: __au.started, buf: __au.startedBuf, media: __au.media, rms: __au.rms, rmsMax: __au.rmsMax, log: __au.log.splice(0)})")
            for l in st['log']: print('      ', l)
            print('%5.1f ctx=%s started=%d buf=%d media=%d rms=%.4f max=%.4f' % (t, st['states'], st['started'], st['buf'], st['media'], st['rms'], st['rmsMax']), flush=True)
    b.close()
for typ, txt in logs:
    if a.all or typ in ('error', 'warning', 'pageerror') or 'ERROR' in txt or 'udio' in txt: print('CONSOLE', typ, txt[:300])
for s, u in bad: print('HTTP', s, u)
print('console lines:', len(logs))
