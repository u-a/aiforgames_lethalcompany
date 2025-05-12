import openai
from openai import OpenAI

import os
import time
import json
import random
from dotenv import load_dotenv
from cloned_tts import find_and_generate_with_model_name
from models_list import list_my_voice_models, MODELS_PER_PAGE # Import the function and constant

from pydub import AudioSegment

# --- Configuration ---
load_dotenv()

# Set up OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

lethal_company_moon_loot = {
    "Experimentation": ["Gold Bar", "Cash Register", "Laser Pointer", "Wedding Ring", "Air Horn", "V-type Engine", "Metal Sheet", "Large Axle", "Big Bolt", "Steering Wheel"],
    "Assurance": ["Cash Register", "Hairdryer", "Robot Toy", "Laser Pointer", "Brass Bell", "Big Bolt", "Bottles", "Cookie Mold Pan", "V-type Engine", "Stop Sign"],
    "Vow": ["Cash Register", "Robot Toy", "Laser Pointer", "Brass Bell", "Air Horn", "Clown Horn", "Egg Beater", "Cookie Mold Pan", "Chemical Jug", "Hair Brush"],
    "Offense": ["Robot Toy", "Teeth", "Laser Pointer", "Air Horn", "Clown Horn", "Metal Sheet", "Large Axle", "Big Bolt", "V-type Engine", "Bottles"],
    "March": ["Gold Bar", "Cash Register", "Robot Toy", "Laser Pointer", "Clown Horn", "Large Axle", "Big Bolt", "Metal Sheet", "V-type Engine", "Bottles"],
    "Adamance": ["Cash Register", "Robot Toy", "Laser Pointer", "Brass Bell", "Air Horn", "Clown Horn", "Egg Beater", "Cookie Mold Pan", "Chemical Jug", "Hair Brush"],
    "Rend": ["Cash Register", "Fancy Lamp", "Painting", "Hairdryer", "Perfume Bottle", "Brass Bell", "Robot Toy", "Bottles"],
    "Dine": ["Cash Register", "Fancy Lamp", "Painting", "Hairdryer", "Perfume Bottle"],
    "Titan": ["Fancy Lamp", "Painting", "Hairdryer", "Perfume Bottle", "Robot Toy"],
    "Artifice": ["Gold Bar", "Cash Register", "Fancy Lamp", "Painting", "Hairdryer", "Perfume Bottle", "Robot Toy"],
    "Embrion": ["Cash Register", "Hairdryer", "Robot Toy", "Laser Pointer", "Brass Bell", "Big Bolt", "Bottles", "Cookie Mold Pan", "V-type Engine", "Stop Sign"],
    "Liquidation": ["Gold Bar", "Cash Register", "Fancy Lamp", "Painting", "Hairdryer", "Perfume Bottle", "Robot Toy"]
}

# Dictionary of all known monsters in Lethal Company and a short description for each
lethal_company_monsters = {
    "BaboonHawk": "Large, hunchbacked primates with wings and horned beaks; timid alone, aggressive in packs.",
    "Barber": "Unpredictable entity associated with surreal behavior and dreamlike lore.",
    "Bracken": "Intelligent, elusive humanoid with leaf-like protrusions; becomes hostile when watched.",
    "BunkerSpider": "Large spider that ambushes prey with silk traps; best avoided unless necessary.",
    "Butler": "Rotting humanoids that sweep mansions; occasionally hostile, especially when provoked.",
    "Coil-Head": "Mannequin with a spring head; stops when looked at, resets with light or noise.",
    "CircuitBees": "Red bees with electrostatic charge; attack aggressively when disturbed or provoked.",
    "EarthLeviathan": "Massive burrowing predator; attracted to vibration, advised to move constantly.",
    "EyelessDog": "Social hunters that rely on sound; attack in large, roaring packs.",
    "ForestKeeper": "Giant, childlike creatures with tough skin; curious and potentially dangerous.",
    "GhostGirl": "Unlogged entity; assumed to be paranormal and extremely dangerous.",
    "HoardingBug": "Territorial insects that collect and defend objects; mostly harmless unless disturbed.",
    "Hygrodere": "Gelatinous, heat-seeking blobs that multiply fast; avoid contact and climb to escape.",
    "Jester": "Unpredictable jack-in-the-box monster; lethal when active, reset by leaving building.",
    "KidnapperFox": "Elusive predator with sticky tongue; often partners with Vain Shrouds.",
    "Maneater": "Gigantic, metamorphic cockroach; terrifyingly fast and aggressive post-transformation.",
    "Manticoil": "Four-winged birds; intelligent and harmless but may carry disease.",
    "Masked": "Undocumented entity; presumed hostile based on name and presence.",
    "MaskHornets": "Unlogged stinging insects; can be scanned but no Bestiary info available.",
    "Nutcracker": "Mechanical guards that detect motion; track targets continuously once noticed.",
    "OldBird": "Autonomous war machine with spotlights and rocket legs; dormant but powerful.",
    "RoamingLocusts": "Light-attracted flying grasshoppers; scatter when approached.",
    "SnareFlea": "Silk-propelled centipede that suffocates prey; fragile but deadly in ambush.",
    "SporeLizard": "Large, timid herbivores that release fungal spores when threatened.",
    "Thumper": "Legless, aggressive predator with poor hearing; runs fast in straight lines.",
    "TulipSnake": "Flying, brightly colored lizards; engage in bizarre mating displays with objects.",
    "VainShrouds": "Massive, invasive red ferns that obscure vision and partner with Kidnapper Foxes."
}


def load_and_select_phrases(file_path, preferred_emotion, num_per_category=15):
    with open(file_path, "r", encoding="utf-8") as f:
        all_phrases = json.load(f)

    if preferred_emotion not in all_phrases:
        raise ValueError(f"Emotion category '{preferred_emotion}' not found in phrase file.")

    return random.sample(all_phrases[preferred_emotion], 
                         min(num_per_category, len(all_phrases[preferred_emotion])))



def build_prompt(phrases, context, moon_loot, monster_description):
    return f"""
You are helping develop a horror mod for the game *Lethal Company*. In this game, an enemy NPC mimics real players by speaking voice lines over voice chat. These lines are played using a **low-quality text-to-speech model**, so it’s absolutely critical that the phrasing sounds:

- **Short**
- **Natural**
- **Emotionally expressive**
- And most importantly: **like something a real player would say in voice chat.**

You are given:
- A list of candidate voice lines from the current emotional category (`{context["preferred_emotion"]}`)
- The current game context (player names, monster, moon loot, etc.)

---

### GAME CONTEXT

- Players in this session: {", ".join(context["player_names"])}
- Current moon: {context["current_moon"]}
- Enemy nearby: {context["enemy_name"]}
- Enemy behavior: {monster_description}
- Distance to target player: {context["distance_to_player"]}
- Loot found on this moon: {", ".join(moon_loot)}

---

### FORMAT RULES

- Keep each phrase **under 8 words**
- Use **casual spoken English** — contractions, slang, filler words
- Use **ALL CAPS** for yelling and **extra vowels** for drama (e.g., “ruuuuun!”, “nooo way!”)

---

### YOUR TASK

1. Select and rewrite voice lines from the list provided.
2. Make the lines **feel like real player speech** — panicked, curious, mocking, or urgent — depending on the situation.
3. Inject contextual hints using:
   - **Player names** from the session — like calling someone out or pretending to help.
   - **Monster behavior** — fake warnings like “DON’T RUN! It tracks sound!” or “It’s the spider, stay above ground!”
   - **Loot items** — suggest lures like “Gold bar over here!”, “Who left a clown horn?”, “Air horn, grab it!”

4. The NPC is trying to **trick, bait, or mislead** real players. Keep this in mind.
5. Voice lines must be **short, casual, emotionally expressive**, and optimized for **low-quality TTS** (like voice chat).

---

### FORMAT

Return your output as a flat list of voice lines, like this:

[
  "line 1",
  "line 2",
  "line 3",
  ...
]

---

### CANDIDATE PHRASES TO PERSONALIZE

{json.dumps(phrases, indent=2)}
"""



def personalize_phrases(phrases, context):
    moon_name = context["current_moon"]
    enemy_name = context["enemy_name"]

    moon_loot = lethal_company_moon_loot.get(moon_name, [])
    monster_description = lethal_company_monsters.get(enemy_name, "Unknown creature.")

    prompt_text = build_prompt(phrases, context, moon_loot, monster_description)

    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {"role": "system", "content": "You are a helpful assistant optimizing horror game dialogue."},
            {"role": "user", "content": prompt_text}
        ],
    )

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        print("Failed to parse JSON from response.")
        print(response.choices[0].message.content)
        return {}



if __name__ == "__main__":
    # --------------------------------------------
    # MODIFY THIS PART FOR YOUR USE CASE
    WATCH_DIR = "VoiceContexts"
    OUTPUT_DIR = "ReceivedAudio"
    # --------------------------------------------

    os.makedirs(WATCH_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    seen_files = set()

    fish_api_key = os.getenv("FISH_AUDIO_API_KEY")
    if not fish_api_key:
        print("Missing FISH_AUDIO_API_KEY in .env.")
        exit(1)

    print(f"Monitoring folder: '{WATCH_DIR}' for in-game context files...\n")

    while True:
        for fname in os.listdir(WATCH_DIR):
            if not fname.endswith(".json") or fname in seen_files:
                continue

            path = os.path.join(WATCH_DIR, fname)
            try:
                print(f"\n--- Detected new context file: {fname} ---")

                # STEP 1: Load and parse input JSON
                with open(path, "r", encoding="utf-8") as f:
                    context_json = json.load(f)

                moon_raw = context_json.get("moonName", "")
                moon_clean = moon_raw.split(" ", 1)[-1] if " " in moon_raw else moon_raw

                enemy_raw = context_json.get("enemyName", "")
                enemy_clean = enemy_raw.split(" (")[0] if " (" in enemy_raw else enemy_raw

                emotion = context_json.get("preferredEmotion", "interest")
                distance_to_player = context_json.get("distanceToPlayer", "unknown")

                personalization_context = {
                    "player_names": ["Allan", "Matthew", "Matt", "Andy", "Ushan"],
                    "current_moon": moon_clean,
                    "enemy_name": enemy_clean,
                    "preferred_emotion": emotion,
                    "distance_to_player": distance_to_player
                }

                print(f"\nStep 1: Parsed context:")
                print(f"  - Moon:        {moon_clean}")
                print(f"  - Enemy:       {enemy_clean}")
                print(f"  - Emotion:     {emotion}")
                print(f"  - Distance:    {distance_to_player}")

                # STEP 2: Load and sample phrases
                selected_phrases = load_and_select_phrases("emotion_phrases.json", preferred_emotion=emotion)
                print(f"\nStep 2: Sampled {len(selected_phrases)} raw phrases:")
                for i, phrase in enumerate(selected_phrases, 1):
                    print(f"  {i}. {phrase}")

                # STEP 3: Personalize phrases
                personalized_lines = personalize_phrases(selected_phrases, personalization_context)
                print(f"\nStep 3: Personalized phrases:")
                for i, phrase in enumerate(personalized_lines, 1):
                    print(f"  {i}. {phrase}")

                # STEP 4: Select voice line and TTS model
                text = random.choice(personalized_lines)

                # Fetch available voice model titles
                print("Fetching available voice model titles from Fish Audio...")
                available_model_titles = list_my_voice_models(fish_api_key, page_size=MODELS_PER_PAGE)

                if not available_model_titles:
                    print("Error: No voice models found or failed to retrieve model list. Please ensure models are available on your Fish Audio account.")
                    exit(1)
                print(f"Successfully retrieved {len(available_model_titles)} model titles: {', '.join(available_model_titles)}")
                
                model = random.choice(available_model_titles)
                out_path = os.path.join(OUTPUT_DIR, fname.replace(".json", ".wav"))

                print(f"\nStep 4: Generating TTS output")
                print(f"  - Voice model:  {model}")
                print(f"  - Output file:  {out_path}")
                print(f"  - Selected line: \"{text}\"")

                success = find_and_generate_with_model_name(
                    api_key=fish_api_key,
                    model_name_to_find=model,
                    text=text,
                    output_file=out_path,
                    emotion=emotion
                )

                # Final status
                if success:
                    print(f"\nStep 5: TTS generation complete. mp3 saved to: {out_path}")
                else:
                    print(f"\nStep 5: TTS generation failed for: {fname}")

            except Exception as e:
                print(f"\nError processing file '{fname}': {e}")
            finally:
                seen_files.add(fname)

            print("\n--- Processing complete ---\n")

        time.sleep(1)
