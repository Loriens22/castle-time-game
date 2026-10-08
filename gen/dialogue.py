"""Castle TIME - full voiced script. line(id, who, subtitle, say=pronunciation override)
python3 gen/dialogue.py -> game/data/dialogue.json"""
import json, os
L = []
def line(i, who, text, say=None): L.append(dict(id=i, who=who, text=text, say=say or text))

# ---------------------------------------------------------------- PROLOGUE: the lab, 2026
line('p01', 'sibyl', "Juno. Wake up. Correction: you are awake. You have been awake for thirty-one hours. That is a different problem.")
line('p02', 'juno', "I'm calibrating a chrono-resonator, SIBYL. Being awake is the job.", say="I'm calibrating a chrono resonator, Sibyl. Being awake is the job.")
line('p03', 'sibyl', "I found it. The Valtorre Scroll. Lorenzo Vinciguerra's notebook. Every idea of his that history never got to read.", say="I found it. The Valtorre Scroll. Lorenzo Vinchi gwerra's notebook. Every idea of his that history never got to read.")
line('p04', 'sibyl', "It burns tonight. Rocca di Valtorre, Tuscany. The seventeenth of October, twelve eighty-three.", say="It burns tonight. Rocca dee Valtorre, Tuscany. The seventeenth of October, twelve eighty three.")
line('p05', 'juno', "Tonight tonight? As in, seven hundred and forty-three years ago tonight?")
line('p06', 'sibyl', "The temporal window closes in nine minutes. After that the night is sealed, and the scroll is ash. Forever.")
line('p07', 'juno', "Then we go now. Where's my phone?")
line('p08', 'sibyl', "Charging on the desk. And Juno? You might want to change out of the hoodie.")
line('p09', 'juno', "No time! It's a castle, not a dress code.")
line('p10', 'juno', "Seventeen, ten, twelve eighty-three. Forty-three point four five one two north. Eleven point oh one five seven east.")
line('p11', 'sibyl', "Coordinates locked. Arrival point: behind a livestock shed. I'm told it's very authentic.")
line('p12', 'sibyl', "Reminder: your blaster is set to stun. History gets cranky when you delete people from it.")
line('p13', 'juno', "Stun only. Got it. See you in the thirteenth century.")
# ---------------------------------------------------------------- ACT 1: the farm
line('a01', 'juno', "Okay. Smells... authentic.")
line('a02', 'sibyl', "Arrival confirmed. October seventeenth, twelve eighty-three. Local time: suppertime. The castle is north, past the village.")
line('a03', 'peasant', "Mother of saints! What is that thing?")
line('a04', 'peasantf', "Its shoes glow! Bartolo, its shoes GLOW!")
line('a05', 'juno', "Hi! Um. Buongiorno? I'm a pilgrim. From... Milan.", say="Hi! Um. Bwon jorno? I'm a pilgrim. From... Milan.")
line('a06', 'peasant', "A witch from Milan! Get the pitchforks!")
line('a07', 'juno', "Okay. The hoodie was a mistake.")
line('a08', 'sibyl', "Noted, logged and laminated. Blaster to stun, please.")
line('a09', 'sibyl', "Farm cleared. Follow the road north. The market will be busy. Busy, and hostile.")
line('a10', 'peasantf', "Cabbages! Fresh cabbages! Perfect for throwing at witches!")
line('a11', 'juno', "Is that a cabbage? Did she just throw a cabbage at me?")
line('a12', 'guard', "Halt! By order of Count Ottone, no witches past the moat!")
line('a13', 'juno', "Do you get a lot of witches?")
line('a14', 'guard2', "Mostly on Tuesdays.")
line('a15', 'sibyl', "The drawbridge is up. Those chains look old. Old, rusty, and very shootable.")
line('a16', 'juno', "Knock knock.")
# ---------------------------------------------------------------- ACT 2: courtyard + grate
line('b01', 'sibyl', "You're inside the walls. Archers on the battlements. Keep moving and use the pulse if they swarm you.")
line('b02', 'maestro', "Psst! Psst! Signorina! Down here! The grate! Yes, you, the glowing lady!", say="Psst! Psst! Seenyorina! Down here! The grate! Yes, you, the glowing lady!")
line('b03', 'juno', "Hello? Are you Lorenzo Vinciguerra?", say="Hello? Are you Lorenzo Vinchi gwerra?")
line('b04', 'maestro', "The one and only, unfortunately. The Count locked me down here for drawing a flying machine. He calls it witchcraft. I call it Tuesday.")
line('b05', 'juno', "I'm here for your scroll. Long story. Time travel. You'd love it.")
line('b06', 'maestro', "Time travel! I knew it! I drew your shoes last week, in a dream!")
line('b07', 'maestro', "The scroll is with me, but my cell has the Count's clock lock. Only the clock key opens it, and the key is at the top of the spire, with Ser Bruno. He is a very large man, in a very large bell.")
line('b08', 'juno', "Top of the spire. Big man. Bell. Got it.")
line('b09', 'maestro', "Hurry! The Count is testing his trebuchet tonight, and his engineers are idiots!")
# ---------------------------------------------------------------- ACT 3: spire + boss
line('c01', 'sibyl', "Fun fact: mechanical clocks are being invented right about now. You are standing on a prototype.")
line('c02', 'sibyl', "The ledge is out. Ride the minute hand. Please do not break time. Literally.")
line('c03', 'juno', "Gears. Giant spinning gears. Sure. Why not.")
line('c04', 'bruno', "WHO DARES CLIMB THE COUNT'S CLOCK?")
line('c05', 'juno', "Hi. I'm here about a key.")
line('c06', 'bruno', "I am Ser Bruno, the Iron Bell! No blade has ever pierced my armour!")
line('c07', 'juno', "Good thing this isn't a blade.")
line('c08', 'sibyl', "His breastplate is polished like a mirror. Shots will bounce off the front. Hit his back after he slams, or ring that bell to daze him.")
line('c09', 'bruno', "The bell... it tolls... for me...")
line('c10', 'juno', "Clock key: acquired. Now, how do I get down?")
line('c11', 'sibyl', "There's a rope line to the courtyard. The Count uses it to deliver fruit. Hold on tight.")
line('c12', 'bruno', "BONG! Hold still, little witch!")
line('c13', 'bruno', "My helmet! It is ringing! Why is it ringing?")
# ---------------------------------------------------------------- ACT 4: keep + dungeon
line('d01', 'knight', "The witch rides the fruit line! To arms!")
line('d02', 'sibyl', "The dungeon entrance is in the great hall. North-west corner. Look for the golden lock.")
line('d03', 'juno', "The clock key fits. Tick tock.")
line('d04', 'jailer', "Nobody gets past old Grimaldo! Nobody! Except at lunch.")
line('d05', 'beppe', "Is it Thursday? They told me I'd be out by Thursday.")
line('d06', 'juno', "Which Thursday?")
line('d07', 'beppe', "Twelve seventy-nine.")
line('d08', 'maestro', "You came! And with the glowing shoes! Exactly as I drew them!")
line('d09', 'juno', "You drew me?")
line('d10', 'maestro', "La viaggiatrice. A woman with a lantern on her eyes and a talking box in her hand. I thought I was finally going mad.", say="La vee-ajja-treechay. A woman with a lantern on her eyes and a talking box in her hand. I thought I was finally going mad.")
line('d11', 'juno', "SIBYL, are you hearing this?", say="Sibyl, are you hearing this?")
line('d12', 'sibyl', "I am. I would like to file a paradox report.")
line('d13', 'maestro', "Here. The Scientia Temporis. Everything I know about light, gears and time. Take it somewhere it will not burn.", say="Here. The Shee-entia Temporis. Everything I know about light, gears and time. Take it somewhere it will not burn.")
line('d14', 'juno', "Come with me! I can get you out of—")
line('d15', 'maestro', "No, no. Someone must stay and invent things badly, so that someone else can invent them well. Now go!")
line('d16', 'count', "Engineers! The witch is in my dungeon! Fire the trebuchet at her!")
line('d17', 'engineer', "My lord, the trebuchet points at the village. The dungeon is behind us.")
line('d18', 'count', "Then fire it BACKWARDS!")
line('d19', 'engineer', "My lord, that is not how... oh no.")
line('d20', 'count', "Write that down in the chronicle as an accident.")
line('d21', 'maestro', "That fool! This whole castle is made of oak and pride. Run, signorina! RUN!", say="That fool! This whole castle is made of oak and pride. Run, seenyorina! Run!")
line('d22', 'sibyl', "Structural collapse in three minutes. I recommend leaving at roughly the speed of panic.")
# ---------------------------------------------------------------- ESCAPE + finale
line('e01', 'sibyl', "The portcullis is dropping! Slide under it! Roll, Juno, roll!")
line('e02', 'juno', "Hot, hot, hot, hot!")
line('e03', 'sibyl', "Ninety seconds. The great hall roof is going.")
line('e04', 'sibyl', "Thirty seconds! Faster!")
line('e05', 'juno', "Look! Up there! The flying machine!")
line('e06', 'juno', "He actually built it.")
line('e07', 'sibyl', "And it actually flies. Don't tell history.")
line('e08', 'juno', "Take me home, SIBYL.", say="Take me home, Sibyl.")
line('e09', 'sibyl', "Recall in three. Two. Say goodbye to the pig.")
line('e10', 'juno', "Bye, pig.")
# ---------------------------------------------------------------- EPILOGUE: 2026
line('f01', 'sibyl', "Welcome back. You smell like smoke and pig.")
line('f02', 'juno', "And I have the Valtorre Scroll.")
line('f03', 'sibyl', "Scanning. Light theory. Gear trains. A clock with no pendulum. And... page forty-two.")
line('f04', 'juno', "What's on page forty-two?")
line('f05', 'sibyl', "A schematic. A flip phone, with a time resonator where the battery should be. Labelled: for la viaggiatrice, so that she can come and find me.", say="A schematic. A flip phone, with a time resonator where the battery should be. Labelled: for la vee-ajja-treechay, so that she can come and find me.")
line('f06', 'juno', "Wait. He designed my phone? But I built my phone from...")
line('f07', 'sibyl', "From an anonymous medieval sketch you found in a museum archive. Yes. Congratulations. You are a closed time loop.")
line('f08', 'juno', "I need to sit down.")
line('f09', 'sibyl', "You need to change out of that hoodie.")
line('f10', 'sibyl', "Juno. There is a chicken in the lab.")
line('f11', 'juno', "There's a WHAT?")
line('f12', 'sibyl', "It followed you through the portal. It has also just ordered forty pizzas. With my card.")
line('f13', 'chicken', "Bawk.")
# ---------------------------------------------------------------- gameplay barks
for k, t in enumerate(["Witch!", "Get the witch!", "Begone, demon!", "It has a glowing stick!", "Burn it! Wait, no, it burns US!", "For Valtorre!", "Witch! Witch! Witch!", "Saints preserve us!"]):
    line('bk_peas%d' % k, ['peasant', 'peasantf', 'peasant', 'peasantf', 'peasant', 'peasant', 'peasantf', 'peasant'][k], t)
for k, t in enumerate(["Ooh... pretty lights...", "I see stars... and a goat...", "Tell my pig I loved him."]): line('bk_ko%d' % k, ['peasant', 'peasant', 'peasant'][k], t)
for k, t in enumerate(["Run! It's the witch!", "Mamma mia! Run!"]): line('bk_flee%d' % k, ['peasantf', 'peasant'][k], t)
for k, t in enumerate(["Hold the line!", "Shields up!", "There she is!", "In the name of the Count!", "Surrender, sorceress!"]): line('bk_guard%d' % k, ['guard', 'guard2', 'guard', 'guard2', 'guard'][k], t)
for k, t in enumerate(["Archers, loose!", "She's on the wall!"]): line('bk_arch%d' % k, 'guard2', t)
for k, t in enumerate(["Face me, witch!", "My armour laughs at your light!"]): line('bk_knight%d' % k, 'knight', t)
for k, t in enumerate(["Fire! Save the wine!", "The witch did this!", "Every man for himself!"]): line('bk_fire%d' % k, ['guard', 'peasant', 'guard2'][k], t)
for k, t in enumerate(["Ow! Medieval healthcare is not an option.", "That's going to bruise.", "Okay, that hurt.", "Rude!"]): line('bk_hurt%d' % k, 'juno', t)
for k, t in enumerate(["Blaster's overheating!", "Too hot, venting!"]): line('bk_heat%d' % k, 'juno', t)
for k, t in enumerate(["Stun pulse!", "Everybody, take a nap!"]): line('bk_pulse%d' % k, 'juno', t)
for k, t in enumerate(["Nap time.", "Sweet dreams.", "Stunned. You're welcome.", "That's a knock-out."]): line('bk_kill%d' % k, 'juno', t)
line('bk_respawn', 'sibyl', "Reloading from the last checkpoint. Let's call that a practice run.")
line('bk_cp', 'sibyl', "Checkpoint saved.")
line('bk_locked', 'juno', "Locked. It needs some kind of fancy key.")
line('bk_closed', 'juno', "Barred from the inside.")
line('bk_food', 'juno', "Mm. Organic. Very organic.")
line('bk_bell', 'sibyl', "Direct hit on the bell! He's dazed!")
line('bk_reflect', 'sibyl', "It's bouncing off his breastplate! Get behind him!")
line('bk_back', 'sibyl', "His back is open! Now!")
line('bk_zip', 'juno', "Wheeeee!")
line('bk_moat', 'juno', "Moat water. That's... going to stay with me.")
line('bk_bullseye', 'juno', "Three bullseyes. Robin Hood's got nothing on me.")
line('bk_bighead', 'sibyl', "Big head mode enabled. Medically inadvisable.")
# ---------------------------------------------------------------- interactables & secrets
for i, w, t, s in [
    ('i_monitor0', 'juno', "Seventeen thousand lines of code, and one comment. It just says: sorry.", None),
    ('i_monitor1', 'sibyl', "Rocca di Valtorre. Destroyed in twelve eighty-three. The records only say: an incident involving a trebuchet.", "Rocca dee Valtorre. Destroyed in twelve eighty three. The records only say: an incident involving a trebuchet."),
    ('i_monitor2', 'sibyl', "That's my good side.", None),
    ('i_mug', 'juno', "World's Okayest Physicist. Accurate.", None),
    ('i_server', 'sibyl', "Please don't touch my brain.", None),
    ('i_printer', 'juno', "It's printing a tiny castle. I don't remember asking it to do that.", None),
    ('i_scope', 'juno', "The oscilloscope says the resonator is stable. The oscilloscope is an optimist.", None),
    ('i_bed', 'juno', "No time to sleep. Sleep is for people with fewer paradoxes.", None),
    ('i_poster', 'juno', "Time waits for no one. Except me, apparently.", None),
    ('i_steve', 'juno', "Steve's PC Repair. He replaced my CMOS battery once. Fair price. Then he stared at the door like someone was about to walk in with a briefcase.", "Steve's P C Repair. He replaced my sea moss battery once. Fair price. Then he stared at the door like someone was about to walk in with a briefcase."),
    ('i_cat', 'juno', "Hey, Pixel. Guard the lab while I'm gone. No chewing the cables.", None),
    ('i_door', 'juno', "Nope. Wrong century.", None),
    ('i_whiteboard', 'juno', "Don't forget: change clothes. Huh.", None),
    ('i_fridge', 'juno', "Volt Cola. Two hundred milligrams of caffeine, and regret.", None),
    ('i_books', 'juno', "Time Travel for Dummies. Third edition. The first two haven't been written yet. Or have been. Ugh, tenses.", None),
    ('i_ring', 'sibyl', "Prototype one. It sent a sandwich to nineteen ninety-seven. We never found it.", None),
    ('i_plant', 'juno', "Gerald. My oldest friend. Mostly because he can't leave.", None),
    ('i_vacuum', 'sibyl', "The robot vacuum has achieved sentience. It is choosing not to use it.", None),
    ('i_sibyl', 'sibyl', "Yes? I'm busy calculating how many ways tonight can go wrong. Currently four hundred and twelve.", None),
    ('i_scarecrow', 'juno', "Straw hat, blue tunic. Honestly? Very twenty twenty-six street style.", None),
    ('i_milkstool', 'juno', "A three-legged milking stool. Peak furniture technology.", None),
    ('i_tavern', 'juno', "The Drunken Dragon. Beer, beds, no witches. Rude.", None),
    ('i_wanted', 'juno', "WITCH, maybe. Reward: three chickens. That's... actually kind of flattering.", None),
    ('i_churchbell', 'sibyl', "Please don't ring the church bell. People here take bells very seriously.", None),
    ('i_well', 'juno', "A wishing well. I wish for indoor plumbing.", None),
    ('i_stocks', 'juno', "The stocks. The medieval comment section.", None),
    ('i_anvil', 'juno', "Hot iron, hammers and sparks. Basically a medieval 3D printer.", "Hot iron, hammers and sparks. Basically a medieval three D printer."),
    ('i_cat_town', 'juno', "Hey, kitty. You look exactly like Pixel. Great, great, great, great grandma?", None),
    ('i_armory', 'juno', "Swords, spears, maces. And not one safety manual.", None),
    ('i_horse', 'juno', "Easy, horse. Sorry about the noise. And the lasers.", None),
    ('i_well2', 'juno', "Another well. Still no plumbing.", None),
    ('i_throne', 'juno', "Sitting on the throne would be a power move. I'm not going to. Probably.", None),
    ('i_armour', 'juno', "An empty suit of armour. Definitely not going to come alive. Definitely.", None),
    ('i_sketch_heli', 'juno', "A helicopter. In twelve eighty-one. He's two centuries ahead of da Vinci.", None),
    ('i_sketch_phone', 'juno', "That's a flip phone. Why is there a flip phone?", None),
    ('i_sketch_clock', 'sibyl', "A mechanical escapement. Decades ahead of schedule.", None),
    ('i_sketch_laser', 'juno', "Light that bites but does not kill. That's my blaster. That is literally my blaster.", None),
    ('i_sketch_traveller', 'juno', "That's me. Hoodie, visor, everything. Dated today.", None),
    ('i_sketch_trebuchet', 'juno', "NOT with fire. Underlined three times. Foreshadowing much?", None),
    ('i_globe', 'juno', "A round globe. So much for the flat earth myth.", None),
    ('i_cauldron', 'juno', "Smells like stew. And slightly like eye of newt.", None),
    ('i_cat_kitchen', 'juno', "Another orange cat. They really do run this place.", None),
    ('i_dice', 'juno', "Loaded dice. Some things never change.", None),
    ('i_skeleton', 'juno', "Hello, Ser Rattlebones. Still waiting on lunch?", None),
    ('i_flyer', 'juno', "A model flying machine. Canvas, wood, and very big dreams.", None),
    ('i_dungeongate', 'juno', "A golden lock shaped like a clock face. That needs the clock key.", None),
    ('col_cmos', 'juno', "A CR2032 coin cell. How did a CMOS battery get to twelve eighty-three? Somewhere, a computer wants to remember the date.", "A C R twenty thirty two coin cell. How did a sea moss battery get to twelve eighty three? Somewhere, a computer wants to remember the date."),
    ('col_earbud', 'juno', "My earbud! I've been looking for that since twenty twenty-four.", None),
    ('col_sunglasses', 'juno', "My sunglasses. The peasants probably think these are demon eyes.", None),
    ('col_tamagotchi', 'juno', "A Tamagotchi. Still alive. Somehow.", None),
    ('col_vr', 'juno', "A VR headset. Imagine showing virtual reality to a medieval monk. Actually, don't.", "A V R headset. Imagine showing virtual reality to a medieval monk. Actually, don't."),
    ('col_phonecase', 'juno', "My glitter phone case! The cook was using it as a spoon rest.", None),
    ('col_gameboy', 'juno', "A handheld console. The jailer's high score is... honestly impressive.", None),
    ('col_fidget', 'juno', "A fidget spinner. Of course it ended up in the past. It always felt like it came from the past.", None),
]:
    line(i, w, t, s)

VOICES = {
    'juno':     dict(voice='af_heart',    lang='en-us', speed=1.04, pitch=1.0,  fx='room'),
    'sibyl':    dict(voice='bf_isabella', lang='en-gb', speed=1.0,  pitch=1.03, fx='ai'),
    'maestro':  dict(voice='bm_george',   lang='en-gb', speed=1.0,  pitch=0.9,  fx='old'),
    'peasant':  dict(voice='am_puck',     lang='en-us', speed=1.08, pitch=0.95, fx='outdoor'),
    'peasantf': dict(voice='bf_lily',     lang='en-gb', speed=1.08, pitch=1.04, fx='outdoor'),
    'guard':    dict(voice='bm_lewis',    lang='en-gb', speed=1.0,  pitch=0.94, fx='outdoor'),
    'guard2':   dict(voice='am_eric',     lang='en-us', speed=0.95, pitch=0.97, fx='outdoor'),
    'knight':   dict(voice='am_onyx',     lang='en-us', speed=0.95, pitch=0.9,  fx='helmet'),
    'bruno':    dict(voice='am_fenrir',   lang='en-us', speed=0.9,  pitch=0.82, fx='bell'),
    'count':    dict(voice='bm_daniel',   lang='en-gb', speed=1.05, pitch=1.06, fx='outdoor'),
    'engineer': dict(voice='bm_fable',    lang='en-gb', speed=1.05, pitch=1.0,  fx='outdoor'),
    'jailer':   dict(voice='am_santa',    lang='en-us', speed=0.95, pitch=0.9,  fx='dungeon'),
    'beppe':    dict(voice='am_echo',     lang='en-us', speed=0.9,  pitch=1.05, fx='dungeon'),
    'chicken':  None,
}
NAMES = {'juno': 'JUNO', 'sibyl': 'SIBYL', 'maestro': 'MAESTRO LORENZO', 'peasant': 'BARTOLO', 'peasantf': 'VILLAGER', 'guard': 'GUARD',
         'guard2': 'GUARD', 'knight': 'KNIGHT', 'bruno': 'SER BRUNO', 'count': 'COUNT OTTONE', 'engineer': 'ENGINEER', 'jailer': 'GRIMALDO',
         'beppe': 'BEPPE', 'chicken': 'CHICKEN'}
COLORS = {'juno': '#5ff5d8', 'sibyl': '#c9a0ff', 'maestro': '#ffcf6b', 'peasant': '#d9b48a', 'peasantf': '#e8c39a', 'guard': '#ff8a7a',
          'guard2': '#ff9e8a', 'knight': '#c8ccd2', 'bruno': '#e0b23a', 'count': '#d58cff', 'engineer': '#b8d0a0', 'jailer': '#c0a080',
          'beppe': '#a0c0e0', 'chicken': '#ffffff'}
if __name__ == '__main__':
    out = os.path.join(os.path.dirname(__file__), '..', 'game', 'data', 'dialogue.json')
    json.dump({'lines': {l['id']: {'who': l['who'], 'text': l['text']} for l in L}, 'names': NAMES, 'colors': COLORS}, open(out, 'w'), indent=0)
    print(len(L), 'lines')
