# Castle TIME – progress log

Repo: https://github.com/Loriens22/castle-time-game (the older `Loriens22/castle-time` repo belongs to a different project and has not been touched)
Live: https://loriens22.github.io/castle-time-game/ (gh-pages branch, deployed by `./deploy.sh`)

## Done
- All assets generated: Blender scripts in `blender/` (world, lab, characters, props); textures, SFX, music and Kokoro voices from `gen/`
- Godot 4.7.2 project in `game/` (Compatibility renderer); Web export without threads, about 57 MB uncompressed
- Soft-lock check `game/tools/reach.gd`: navmesh chain over 30 objectives, plus spiral-ledge clearance. **0 fails**
- Physical walk tests with the `--walk=` debug helper: spire base → full spiral including gap jumps → terrace; escape route from the cell → hall → courtyard → roll under the dropped portcullis → drawbridge
- Fixes this session:
  - movers (AnimatableBody sync_to_physics bug: every door, gate, clock hand and gear was sitting at the origin)
  - stairwell hole in the ground collider
  - keep east wall clashing with the spire ledge
  - spire entry stairs and the guard rail
  - roof pillars and the terrace hole / inner disc
  - steps up to the throne dais
  - player step-up
  - subtitles were off-screen
  - touch UI layout
  - emissive decals rendering white
  - decal UVs
- Web build verified on a local server: desktop and mobile emulation (touch UI)

## Left / in progress
- DONE: story beats verified (lab→phone→teleport→arrival, peasants cutscene+combat, boss_defeated→zip, keepdoor, dungeon gate, Beppe, cell_scene→trebuchet→escape timer, escape route+roll, finale→ending→credits)
- DONE: live URL checked in headless Chrome. Desktop: title → New Game → lab. Mobile 844x390 with touch: title → lab, touch UI showing. No console errors.
- DONE: screenshots in `screenshots/` (01–08)
- DONE: HUD centring, combat balance (at most 2 melee attackers at once), spire checkpoints face up the ledge
- DONE: discovery counter now shows N / total (56, worked out from the dialogue table); deployed and live-checked 05:21 Sofia
- Optional later: terrain colour/fog tuning, full real-device playtest

## How to resume
- Test helpers (user args after `--`):
  - `--level=lab|world|ending`, `--cp=<id>`
  - `--do=[player:|ui:|main:]method@sec`, `--shot=path@sec`
  - `--walk=x,z[,j|r|w];...`, `--hold=action@t0-t1`
  - `--noenemies`, `--touch`, `--movers`
- `tools/` (Godot/Blender binaries) is git-ignored

## Audio fix (8 Oct, 16:30 Sofia)
- Root cause of "no sound" on the web: `audio.gd` created the Music/SFX/Voice buses at runtime with `AudioServer.add_bus()`, which uses position -1. Godot's web "Sample" playback copies the buses into Web Audio, and `Bus.addAt(-1)` → `move(id, -1)` → `splice(-2)` puts each new bus *in front of* Master. Master is then sent into it, so the graph loops and nothing reaches `ctx.destination`. All audio went silent on every browser.
- Fix: a static `game/default_bus_layout.tres` (Master/Music/SFX/Voice), and the fallback `add_bus(explicit index)`; iOS `navigator.audioSession.type="playback"`; quick fire clicks are buffered.
- Check: `python3 test/audiocheck.py URL [--gesture] [--mobile] [--gargs "--level=world --cp=farm"]` (hooks AudioContext, buffer-source starts, RMS at the destination)

## "Mostly on Tuesdays" freeze + fail-safe cutscenes (8 Oct, 17:20–18:15 Sofia)
- Root cause: a moat guard KO'd while the player was >25 m away (e.g. one who chased her into town) was `queue_free`d 30 s later. When the green/moat cutscene reached a14 ("Mostly on Tuesdays"), `for e in gs: e.scripted = false` hit the freed guard. That is a SCRIPT ERROR, which aborts the coroutine, so `cs_end()` never ran. Letterbox, input lock and the cutscene camera then stayed on forever. Repro: `--level=world --cp=town --trace --do=dbg_repro_tuesdays@70`.
- Fixes:
  - KO'd enemies are never freed; they are hidden and put to sleep instead.
  - Story code uses `_alive()`/`_unscript()` validity checks.
  - The talker loop is untyped, which was causing 41,800 errors per run.
- Fail-safe layer (level.gd):
  - A cutscene watchdog (10 s with no line/shot/wait progress) force-ends the cutscene, calls a per-cutscene `recover` callable that applies the story outcome, and restores the camera, input and time_scale.
  - Input lock is released after 6 s outside a cutscene; a black screen clears after 5 s; slow-mo resets after 2 s.
  - `G.wait_for(signal, timeout)` replaces every bare `await tween.finished` (fades, zip line, trebuchet, beams).
  - Dialogue is timed by line length, never by the voice `finished` signal.
- Input:
  - Tap, click, Space, Enter or pad A plays the next line.
  - The touch SKIP button, Esc, Tab, Backspace or pad Back skips the cutscene.
- Other bugs found by the playthrough bot (`--bot [--bot-taps --bot-skip --bot-pause --bot-die --touch]`, scripts/test/bot.gd):
  - The right drawbridge chain was unhittable from the moat bank, because its hit box sat inside the gatehouse wall. The hit box now follows the whole visible chain.
  - An enemy knocked into the moat trench stayed hostile forever and blocked "Fight through the castle guard". It now counts as KO'd.
  - The player could stand on an enemy's head, a stalemate where neither side could hit. The player now slides off.
  - The boss mirror check used an unnormalized basis, which caused a reflect() error every shot.
  - Overlapping level loads are now serialized.
  - Respawning mid-cutscene no longer steals the cutscene camera.
  - Wall archers were softened slightly (dmg 10→7, cd 2.6→3.2).
- Native full runs (headless, fixed 60 fps, touch on, enemies active), all reaching credits and then the title with 0 SCRIPT ERRORs and 0 watchdog fires:
  - taps only;
  - taps + pause in every cutscene + forced deaths in every cutscene and once per stage;
  - taps + SKIP.
- Deployed 18:11 Sofia (gh-pages f5bd880).

### Left
- Full web playthrough in headless Chrome (Android UA, touch, audio): `python3 test/webplay.py URL --minutes 70`.
