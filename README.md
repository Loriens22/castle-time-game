# Castle TIME

A 3D third-person action-comedy game that runs in your browser. Every model, texture, sound, song and voice in it was generated from code.

## ▶ Play: https://loriens22.github.io/castle-time-game/

Works in desktop browsers (Chrome, Edge, Firefox) and on phones and tablets with touch controls. Landscape works best on a phone. The download is about 40 MB, so the first load takes a moment.

---

## Story

**2026.** Juno is a sleep-deprived time-tech hacker. She is in her neon lab-bedroom when her AI, **SIBYL**, finds the coordinates of the lost **Valtorre Scroll**. It is the notebook of Maestro Lorenzo Vinciguerra, a da Vinci-style inventor born about two centuries too early. The scroll burns on the night of **17 October 1283**.

Juno punches the date and coordinates into her **T-PORT**, a modded Motorola-style flip phone. She lands behind a livestock shed on the edge of the Tuscan town of Valtorre, still wearing her hoodie and sneakers. The locals take one look at her and grab their pitchforks.

Armed with a **stun-only LASER blaster**, Juno has to:

1. **Get out of the farm** without hurting anybody. Stunned peasants get stars, not wounds.
2. **Get through the market town and the village green.** There are cabbage throwers, torch bearers and a lot of opinions about witchcraft.
3. **Shoot the drawbridge chains** to get into the castle courtyard, which is full of guards, archers and knights.
4. **Climb the clock spire.** You ride the giant minute hand, hop across spinning gears and dodge archers on a ledge that spirals around the tower.
5. **Beat Ser Bruno**, the bell-helmeted champion, at the top. Ring the great bell to daze him, take the **clock key**, then **zipline** down to the keep.
6. **Get through the Great Hall, kitchens and dungeon**, use the key on the Maestro's lock and take the scroll.
7. **Escape the burning castle.** A misfired flaming trebuchet has set it on fire, so you race a 3-minute timer past falling beams to a dodge-roll under the closing portcullis.

Then it's back to 2026 for a **time-loop twist**, followed by the credits and a **post-credits gag**.

## Features

- Third-person shooter feel: recoil, hit markers, sparks, heat and overheating, a stun **PULSE** shockwave, dodge-roll, screen shake and KO stars. There is no gore.
- **9 enemy types**, each with its own AI:
  - pitchfork peasants
  - fleeing peasant women
  - torch bearers
  - cabbage throwers
  - shield guards that block shots from the front
  - archers who keep their distance
  - armoured knights
  - pot-throwing cooks
  - jailers
  - **Ser Bruno**, the boss: his front reflects lasers, he charges, and he slams the ground
- Spire platforming with moving platforms (the clock hand and the gears), plus checkpoints, health pickups (food) and a save/continue system.
- A timed fire escape with burning debris and collapsing beams.
- Cinematic cutscenes with letterboxing and subtitles, and **199 voiced lines** from 13 distinct voices.
- **45 discoveries** to find:
  - 8 **anachronism collectibles** (a CMOS battery, an earbud, sunglasses, a Tamagotchi, a VR headset, a phone case, a Game Boy, a fidget spinner)
  - the Maestro's **inventor sketches**
  - **cats**: one in the lab, one in town, one in the kitchen
  - a hidden **Steve The PC Repair Man** business card
  - two wishing wells
  - an archery challenge
  - a skeleton called Ser Rattlebones
  - …and typing the Konami code (↑↑↓↓←→←→BA) at any time turns on **Big Head Mode**.
- Menus: title, pause (with your stats and the controls), settings (master/music/SFX/voice volume, subtitles, quality, sensitivity, invert Y), a loading screen with tips, an ending and scrolling credits.

## Controls

| Action | Keyboard & mouse | Gamepad | Touch |
|---|---|---|---|
| Move | WASD / arrows | Left stick | Left half: floating joystick |
| Look | Mouse | Right stick | Drag on the right half |
| Fire LASER | Left mouse | RT | FIRE button (hold; drag it to aim) |
| Aim | Right mouse | LT | Auto aim-assist while firing |
| Jump | Space | A | JUMP |
| Dodge-roll | Shift / C / Ctrl | B | ROLL |
| Stun pulse | Q | Y / LB | PULSE |
| Interact | E / F | X | USE (shows up next to things) |
| Walk | Alt | – | – |
| Pause | Esc / P | Start | ❚❚ (top right) |
| Skip cutscene | Enter / Esc | A | Tap |

## How it was made

- **Engine:** [Godot 4.7.2](https://godotengine.org) (official build) with the GL Compatibility renderer. It is exported to **Web without threads**, so it runs on GitHub Pages with no special headers.
- **3D models:** all built in **Blender 4.5**, running headless from Python scripts in [`blender/`](blender/), and exported to GLB. That covers the world, the lab, the characters with their skeletons and 51 animations, the props and the animals.
- **Textures:** generated procedurally with NumPy ([`gen/textures.py`](gen/textures.py)).
- **Sound effects and music:** synthesised from scratch with NumPy/SciPy ([`gen/sfx.py`](gen/sfx.py), [`gen/music.py`](gen/music.py)).
- **Voices:** generated locally with the open-source **Kokoro TTS** (kokoro-onnx, Apache-2.0 model weights), with per-character effects and compressed to OGG Vorbis ([`gen/voice.py`](gen/voice.py), [`gen/dialogue.py`](gen/dialogue.py)).
  - Voice cast: Juno – `af_heart`, SIBYL – `bf_isabella`, Maestro – `bm_george`, Ser Bruno – `am_fenrir`, plus nine more.
- No cloud AI APIs, stock assets or third-party art.

### Rebuilding

```bash
# 1. assets (Blender 4.5 headless)
blender -b --factory-startup -noaudio --python blender/chars.py
blender -b --factory-startup -noaudio --python blender/props.py
blender -b --factory-startup -noaudio --python blender/lab.py
blender -b --factory-startup -noaudio --python blender/world.py
python3 gen/textures.py && python3 gen/sfx.py && python3 gen/music.py
<venv-with-kokoro-onnx>/bin/python gen/voice.py
# 2. web export (Godot 4.7.2 + export templates)
cd game && godot --headless --export-release "Web" ../build/web/index.html
```

`game/tools/reach.gd` is a soft-lock checker. It bakes a navmesh from the real collision and checks that every objective in the chain can be reached on foot:

```bash
godot --headless -s tools/reach.gd
```

## Credits

Design, code, 3D models, textures, music, sound and voice direction were all generated for this project.
Engine: Godot Engine (MIT). Voices: Kokoro TTS (Apache-2.0). Modelling: Blender (GPL; the generated output is ours).

Made for Betsi.
