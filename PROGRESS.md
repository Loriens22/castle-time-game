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
