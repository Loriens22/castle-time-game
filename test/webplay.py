"""Full web playthrough in headless Chrome as an Android phone (touch, Android UA, audio needs a real tap).
The in-game bot (--bot) plays; THIS script does the real browser taps: one on the title (unlocks audio),
then taps the screen to advance dialogue whenever the game reports a cutscene. Console is streamed to stdout.
usage: python3 test/webplay.py URL [--gargs "--level=world --cp=green"] [--minutes 60] [--shots 120]"""
import sys, time, argparse, json, re
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('url'); ap.add_argument('--gargs', default=''); ap.add_argument('--minutes', type=float, default=60)
ap.add_argument('--shots', type=float, default=0, help='screenshot every N s to /tmp/wp_<t>.png')
a = ap.parse_args()
HOOK = open(__file__.rsplit('/', 1)[0] + '/audiocheck.py').read().split('HOOK = r"""')[1].split('"""')[0]
gargs = ['--', '--bot', '--trace'] + a.gargs.split()
args = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--autoplay-policy=user-gesture-required']
state = {'in_cs': False, 'done': False, 'errors': 0, 'stalls': 0, 'wd': 0, 'last': time.time()}
def on_console(m):
    txt = m.text
    for line in txt.splitlines():
        print('%7.1f %s %s' % (time.time() - T0, m.type[:4], line[:240]), flush=True)
        if 'cs_begin' in line: state['in_cs'] = True
        if 'cs_end' in line or 'objective [' in line and 'cs_begin' not in line: pass
        if 'cs_end' in line: state['in_cs'] = False
        if 'SCRIPT ERROR' in line or m.type == 'error' and 'favicon' not in line: state['errors'] += 1
        if ' STALL ' in line: state['stalls'] += 1
        if 'WATCHDOG' in line: state['wd'] += 1
        if 'DONE - back on the title' in line: state['done'] = True
T0 = time.time()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=args)
    ctx = b.new_context(viewport={'width': 844, 'height': 390}, device_scale_factor=2, is_mobile=True, has_touch=True,
                        user_agent='Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36')
    ctx.add_init_script(HOOK)
    def _rw(route):
        r = route.fetch(); body = r.text().replace('"args":[]', '"args":' + json.dumps(gargs))
        route.fulfill(response=r, body=body)
    ctx.route('**/index.html', _rw); ctx.route(a.url.rstrip('/') + '/', _rw)
    pg = ctx.new_page()
    pg.on('console', on_console)
    pg.on('pageerror', lambda e: (print('PAGEERROR', e, flush=True), state.__setitem__('errors', state['errors'] + 1)))
    pg.goto(a.url, wait_until='load', timeout=120000)
    time.sleep(12)
    pg.touchscreen.tap(422, 300); print('%7.1f TAP title (audio unlock)' % (time.time() - T0), flush=True)
    next_tap = 0; next_probe = 0; next_shot = a.shots or 1e9; ntaps = 0
    while time.time() - T0 < a.minutes * 60 and not state['done']:
        now = time.time() - T0
        if state['in_cs'] and now > next_tap:
            pg.touchscreen.tap(422, 170); ntaps += 1; next_tap = now + 2.5   # real tap: next line
        if now > next_probe:
            next_probe = now + 30
            st = pg.evaluate("() => ({states: __au.ctxs.map(c => c.state), started: __au.started, rms: __au.rms, rmsMax: __au.rmsMax})")
            print('%7.1f AUDIO ctx=%s sources_started=%d rms=%.4f max=%.4f taps=%d' % (now, st['states'], st['started'], st['rms'], st['rmsMax'], ntaps), flush=True)
        if now > next_shot:
            pg.screenshot(path='/tmp/wp_%04d.png' % int(now)); next_shot = now + a.shots
        pg.wait_for_timeout(250)
    time.sleep(2)
    b.close()
print('RESULT done=%s script_errors=%d stalls=%d watchdog=%d minutes=%.1f' % (state['done'], state['errors'], state['stalls'], state['wd'], (time.time() - T0) / 60))
