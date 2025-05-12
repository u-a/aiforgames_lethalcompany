import os
from dotenv import load_dotenv
from fish_audio_sdk import Session, TTSRequest
from fish_audio_sdk.schemas import PaginatedResponse, ModelEntity, Prosody # Import relevant schemas
import logging
import sys # To exit gracefully
from thefuzz import process # Import for fuzzy matching
import random

from pydub import AudioSegment
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Set the desired voice model name to find
VOICE_MODEL_NAME = "Andy_Ng" # <--- Name to search for

# Text to speak
# TEXT_TO_SPEAK = "HI!!"
# TEXT_TO_SPEAK = "Hello world, this is a test using a cloned voice model. Is it good? I HOPE SO!!"
TEXT_TO_SPEAK = "Oh nice! Where did you find it??"

# Output filename
OUTPUT_FILENAME = "cloned_voice.mp3"

# How many models to fetch per page when searching (increase if you have many models)
MODELS_PER_PAGE_SEARCH = 50
OUTPUT_DIR = "data" # Define output directory

# --- Function Definition (Keep find_and_generate_with_model_name as is) ---
def find_and_generate_with_model_name(api_key: str, model_name_to_find: str, text: str, output_file: str, emotion):

    if not api_key:
        print("ERROR: API key is missing. Please set the FISH_AUDIO_API_KEY environment variable.")
        return False
    if not model_name_to_find:
        print("ERROR: Voice model name to find cannot be empty.")
        return False
    if not text:
        print("ERROR: Text to speak cannot be empty.")
        return False

    # Ensure output directory exists for the specific file
    output_dir_for_file = os.path.dirname(output_file)
    if output_dir_for_file and not os.path.exists(output_dir_for_file):
        try:
            os.makedirs(output_dir_for_file)
            print(f"INFO: Created directory '{output_dir_for_file}'")
        except OSError as e:
            print(f"ERROR: Could not create directory '{output_dir_for_file}': {e}")
            return False

    if not output_file.endswith(".wav"):
        print(f"WARNING: Output filename '{output_file}' does not end with .wav. Appending .wav")
        output_file += ".wav"

    found_model_id = None

    try:
        print("Initializing Fish Audio session...")
        session = Session(api_key)

        print(f"Fetching own voice models (page size: {MODELS_PER_PAGE_SEARCH}) to find exact match for '{model_name_to_find}'...")
        paginated_response: PaginatedResponse[ModelEntity] = session.list_models(
            self_only=True,
            page_size=MODELS_PER_PAGE_SEARCH
        )

        if paginated_response and hasattr(paginated_response, 'items') and paginated_response.items:
            models_list = paginated_response.items

            model_title_to_id = {
                getattr(m, 'title', ''): getattr(m, 'id', None)
                for m in models_list if hasattr(m, 'title') and hasattr(m, 'id') and getattr(m, 'title', '')
            }

            if not model_title_to_id:
                 print("ERROR: Could not extract any valid model titles and IDs from the fetched list.")
                 return False

            print(f"Found {len(model_title_to_id)} owned models with titles. Searching for exact match '{model_name_to_find}'...")

            if model_name_to_find in model_title_to_id:
                found_model_id = model_title_to_id[model_name_to_find]
                print(f"Exact match found: '{model_name_to_find}' with ID: {found_model_id}")
            else:
                print(f"ERROR: Exact match not found for '{model_name_to_find}'.")
                print("Available model titles:")
                for title in model_title_to_id.keys():
                    print(f"  - {title}")
                # Don't return False here in the loop context, just skip this iteration maybe?
                # Or let the caller handle it. For now, returning False as before.
                return False

        else:
            print("ERROR: No models found for your account or failed to retrieve models.")
            return False

        # MODIFY THIS
        prosody_settings = {
            "panic":     Prosody(pitch=1.7, speed=1.5, volume=1.3),
            "confusion": Prosody(pitch=1.3, speed=0.95, volume=1.0),
            "interest":  Prosody(pitch=1.5, speed=1.1, volume=1.2),
        }
        prosody = prosody_settings.get(emotion, prosody_settings["interest"])


        # 3. Generate audio using the found model ID
        logging.info(f"Preparing TTS request for model ID: {found_model_id}")
        # request = TTSRequest(text=text, reference_id=found_model_id) # Use reference_id for TTS with a specific model
        request = TTSRequest(
            text=text,
            reference_id=found_model_id,
            prosody=prosody
        )

        print(f"Generating audio for text: '{text}'")
        print(f"Saving audio to: {output_file}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
            tmp_mp3_path = tmp_mp3.name
            print(f"Saving temporary MP3 to: {tmp_mp3_path}")
            for chunk in session.tts(request):
                tmp_mp3.write(chunk)
        
        # Convert to WAV using pydub
        print(f"Converting MP3 to WAV and saving to: {output_file}")

        audio = AudioSegment.from_mp3(tmp_mp3_path)

        # INDREASE VOLUME
        boost_db = 12
        louder_audio = audio + boost_db

        # Export louder audio
        louder_audio.export(output_file, format="wav")


        # Clean up temporary MP3
        os.remove(tmp_mp3_path)

        print(f"Successfully generated audio file: {output_file}")
        return True

    except Exception as e:
        print(f"ERROR: An unexpected error occurred during generation for '{output_file}': {e}")
        import traceback
        traceback.print_exc()

        if os.path.exists(output_file):
             try:
                 os.remove(output_file)
                 print(f"INFO: Removed partially written file: {output_file}")
             except OSError as remove_error:
                 print(f"ERROR: Error removing partially written file {output_file}: {remove_error}")
        return False


# --- Main Execution Block (Modified) ---
if __name__ == "__main__":

    load_dotenv()
    fish_api_key = os.getenv("FISH_AUDIO_API_KEY")

    if not fish_api_key:
        print("Error: FISH_AUDIO_API_KEY not found in environment variables or .env file.")
        print("Please create a .env file with FISH_AUDIO_API_KEY=YOUR_API_KEY")
        sys.exit(1)

    # --- Loop for generating multiple files ---
    num_files_to_generate = 20
    print(f"\nStarting generation of {num_files_to_generate} audio files...")

    # Ensure the main output directory exists before starting the loop
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"INFO: Created main output directory '{OUTPUT_DIR}'")
        except OSError as e:
            print(f"ERROR: Could not create main output directory '{OUTPUT_DIR}': {e}")
            sys.exit(1) # Exit if we can't create the main directory

    successful_generations = 0
    failed_generations = 0

    for i in range(num_files_to_generate):
        print(f"\n--- Generating file {i + 1} of {num_files_to_generate} ---")

        # 1. Select random model
        chosen_model = random.choice(available_models)

        # 2. Select random category and text
        chosen_category_name = random.choice(list(text_categories.keys()))
        chosen_text_list = text_categories[chosen_category_name]
        chosen_text = random.choice(chosen_text_list)

        # 3. Construct output filename
        output_filename = os.path.join(OUTPUT_DIR, f"{chosen_model}_{chosen_category_name}_{i + 1}.mp3")

        print(f"Model: {chosen_model}")
        print(f"Category: {chosen_category_name}")
        print(f"Text: \"{chosen_text}\"")
        print(f"Output File: {output_filename}")

        # 4. Call the generation function
        success = find_and_generate_with_model_name(
            api_key=fish_api_key,
            model_name_to_find=chosen_model,
            text=chosen_text,
            output_file=output_filename
        )

        if success:
            print(f"--- Successfully generated file {i + 1} ---")
            successful_generations += 1
        else:
            print(f"--- Failed to generate file {i + 1} ---")
            failed_generations += 1

        # Optional: Add a small delay to avoid overwhelming the API
        # time.sleep(1) # Sleep for 1 second

    print(f"\n--- Generation Complete ---")
    print(f"Successful: {successful_generations}")
    print(f"Failed:     {failed_generations}")
    print(f"Total attempted: {num_files_to_generate}")
    print(f"Generated files are in the '{OUTPUT_DIR}' directory.")

    # --- Original single call (commented out or removed) ---
    # success = find_and_generate_with_model_name(
    #     api_key=fish_api_key,
    #     model_name_to_find=VOICE_MODEL_NAME,
    #     text=TEXT_TO_SPEAK,
    #     output_file=OUTPUT_FILENAME # This would need adjustment if kept
    # )
    #
    # if success:
    #     print(f"\nAudio generation complete. Check '{OUTPUT_FILENAME}'.")
    # else:
    #     print("\nAudio generation failed. Check messages above for details.")
