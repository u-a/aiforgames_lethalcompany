import requests
import os
import time
import datetime
from dotenv import load_dotenv
from pydub import AudioSegment
import pathlib
import shutil # Standard library for folder operations

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
API_BASE_URL = "https://api.fish.audio"
API_ENDPOINT = f"{API_BASE_URL}/model"
API_TOKEN = os.getenv("FISH_AUDIO_API_KEY")

# --- Script Specific Configuration ---
MONITOR_FOLDER = "../Dissonance_Diagnostics"  # Folder to watch for new WAV files
TEMP_FOLDER = "temp_stitch_processing" # Temporary folder for stitched files
# Optional: Move processed files here instead of just tracking them
# PROCESSED_ARCHIVE_FOLDER = "processed_audio_archive"
TARGET_TOTAL_DURATION_SECONDS = 50  # Threshold to trigger stitching (in seconds)
POLLING_INTERVAL_SECONDS = 5        # How often to check the folder (in seconds)
TARGET_SAMPLE_RATE = 16000          # Target sample rate in Hz for the API
TARGET_CHANNELS = 1                  # Target channels (1 for mono) for the API

# --- FALSE FOR TESTING, SET TO TRUE ---
ENABLE_API_UPLOAD = True # Set to False to disable API calls for testing

# --- Global State ---
# Dictionary to store {filepath: duration_ms} for files found but not yet processed
tracked_files = {}
# Set to store filepaths that have been successfully processed and uploaded in a batch
processed_files = set()

# --- Helper Function to Get Audio Duration ---
def get_audio_duration_ms(filepath):
    """Loads a WAV file and returns its duration in milliseconds."""
    try:
        audio = AudioSegment.from_file(filepath, format="wav")
        return len(audio)
    except Exception as e:
        print(f"Error getting duration for {filepath}: {e}")
        return None # Indicate error

# --- Helper Function to Process and Export Stitched Audio ---
def process_and_export_stitched(audio_segment, output_filepath):
    """
    Ensures the stitched audio segment is mono 16kHz and exports it.
    Returns the output path or None if an error occurs.
    """
    try:
        processed_audio = audio_segment
        processed = False

        # Convert to target sample rate and channels if needed
        if processed_audio.frame_rate != TARGET_SAMPLE_RATE or processed_audio.channels != TARGET_CHANNELS:
            print(f"Converting stitched audio to {TARGET_CHANNELS} channel(s) at {TARGET_SAMPLE_RATE} Hz.")
            processed_audio = processed_audio.set_frame_rate(TARGET_SAMPLE_RATE).set_channels(TARGET_CHANNELS)
            processed = True
        else:
             print("Stitched audio already meets target format (16kHz mono).")


        # Export the processed audio
        print(f"Exporting stitched WAV to: {output_filepath}")
        # Ensure the temporary output directory exists
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        processed_audio.export(output_filepath, format="wav")

        if os.path.exists(output_filepath):
            print(f"Successfully exported stitched audio to {output_filepath}")
            return output_filepath
        else:
            print(f"Error: Export command seemed to succeed but output file {output_filepath} was not found.")
            return None

    except Exception as e:
        print(f"Error processing/exporting stitched audio: {e}")
        return None

# --- Helper Function to Upload to Fish Audio API ---
def upload_to_fish_audio(api_token, audio_filepath, model_title):
    """Uploads the given audio file to the Fish Audio API."""

    if not ENABLE_API_UPLOAD:
        print(f"--- API UPLOAD DISABLED --- Skipping upload for model '{model_title}'.")
        print(f"    Audio file intended for upload: {audio_filepath}")
        return "upload_disabled" # Return a specific indicator


    if not api_token:
        print("Error: API Token is missing.")
        return None

    headers = {"Authorization": f"Bearer {api_token}"}
    response = None # Initialize for error reporting

    try:
        with open(audio_filepath, "rb") as audio_file:
            # Use the generated model title or a generic name for the file part
            files = {
                "voices": (f"{model_title}.wav", audio_file, 'audio/wav')
            }
            data = {
                "visibility": "private",
                "type": "tts",
                "title": model_title,
                "train_mode": "fast",
                "enhance_audio_quality": "true" # Adjust as needed
            }

            print(f"Uploading {os.path.basename(audio_filepath)} to create model '{model_title}'...")
            response = requests.post(API_ENDPOINT, headers=headers, files=files, data=data)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        response_json = response.json()
        model_id = response_json.get("_id")
        if model_id:
            print(f"Voice model '{model_title}' creation successful. Model ID: {model_id}")
            return model_id
        else:
            print(f"Warning: Voice model '{model_title}' creation request submitted, but no '_id' found in response: {response_json}")
            # Consider this a success for processing purposes if the API accepted it (status 2xx)
            return "submitted_no_id"

    except requests.exceptions.RequestException as e:
        print(f"Error during API request for '{model_title}': {e}")
        if response is not None:
            print(f"Response status code: {response.status_code}")
            try:
                print(f"Response body: {response.json()}")
            except requests.exceptions.JSONDecodeError:
                print(f"Response body (non-JSON): {response.text}")
        return None # Indicate API error
    except FileNotFoundError:
        print(f"Error: Stitched audio file not found at {audio_filepath} before upload.")
        return None # Indicate file error
    except Exception as e:
        print(f"An unexpected error occurred during API upload for '{model_title}': {e}")
        return None # Indicate other error


# --- Main Monitoring and Processing Loop ---
if __name__ == "__main__":
    print("--- Starting Audio Monitor and Batch Processor ---")

    if not API_TOKEN:
        print("Error: FISH_AUDIO_API_KEY not found in .env file or environment variables.")
        exit(1)

    # Ensure the input monitor folder exists
    if not os.path.isdir(MONITOR_FOLDER):
        try:
            print(f"Monitor folder '{MONITOR_FOLDER}' not found. Creating it.")
            os.makedirs(MONITOR_FOLDER)
        except OSError as e:
            print(f"Error: Could not create monitor folder '{MONITOR_FOLDER}': {e}")
            exit(1)

    # Optional: Ensure archive folder exists if using move functionality
    # if PROCESSED_ARCHIVE_FOLDER and not os.path.isdir(PROCESSED_ARCHIVE_FOLDER):
    #     try:
    #         os.makedirs(PROCESSED_ARCHIVE_FOLDER)
    #     except OSError as e:
    #         print(f"Warning: Could not create archive folder '{PROCESSED_ARCHIVE_FOLDER}': {e}")
            # Decide if this is critical or just a warning

    # --- Cleanup Temporary Folder on Start ---
    if os.path.exists(TEMP_FOLDER):
         try:
             shutil.rmtree(TEMP_FOLDER)
             print(f"Cleared existing temp folder: {TEMP_FOLDER}")
         except OSError as e:
             print(f"Warning: Could not clear temp folder {TEMP_FOLDER}: {e}. Check permissions.")
    try:
        os.makedirs(TEMP_FOLDER, exist_ok=True)
    except OSError as e:
        print(f"Error creating temp folder {TEMP_FOLDER}: {e}")
        exit(1)


    print(f"Monitoring folder: '{MONITOR_FOLDER}'")
    print(f"Duration threshold: {TARGET_TOTAL_DURATION_SECONDS} seconds")
    print(f"Polling interval: {POLLING_INTERVAL_SECONDS} seconds")
    print("--------------------------------------------------")

    try:
        while True:
            # --- 1. Scan Monitor Folder for New WAV Files ---
            new_files_found_this_cycle = 0
            try:
                current_files = os.listdir(MONITOR_FOLDER)
            except OSError as e:
                print(f"Error listing directory {MONITOR_FOLDER}: {e}. Retrying next cycle.")
                time.sleep(POLLING_INTERVAL_SECONDS)
                continue # Skip rest of the loop iteration

            for filename in current_files:
                if filename.lower().endswith(".wav"):
                    filepath = os.path.join(MONITOR_FOLDER, filename)
                    # Check if it's a file and not already tracked or processed
                    if os.path.isfile(filepath) and filepath not in tracked_files and filepath not in processed_files:
                        print(f"Found new file: {filename}")
                        duration_ms = get_audio_duration_ms(filepath)
                        if duration_ms is not None:
                            tracked_files[filepath] = duration_ms
                            new_files_found_this_cycle += 1
                        else:
                            print(f"Could not get duration for {filename}. Skipping.")
                            # Optionally, add to processed_files to avoid retrying problematic files
                            # processed_files.add(filepath)


            if new_files_found_this_cycle > 0:
                print(f"Added {new_files_found_this_cycle} new WAV file(s) to tracking.")

            # --- 2. Check Total Duration and Trigger Processing ---
            total_tracked_duration_ms = sum(tracked_files.values())
            total_tracked_duration_sec = total_tracked_duration_ms / 1000.0

            print(f"Current tracked files: {len(tracked_files)}. Total duration: {total_tracked_duration_sec:.2f} seconds.")

            if total_tracked_duration_sec >= TARGET_TOTAL_DURATION_SECONDS and len(tracked_files) > 0:
                print(f"\nThreshold ({TARGET_TOTAL_DURATION_SECONDS}s) reached. Processing batch...")

                # Create a list of files for this batch
                batch_files = list(tracked_files.keys()) # Get paths
                batch_files_info = {fp: tracked_files[fp] for fp in batch_files} # Keep info for logging

                # --- 3. Stitch Audio Files ---
                combined_audio = None
                print("Stitching audio files...")
                try:
                    # Initialize with the first file's segment
                    first_file_path = batch_files[0]
                    combined_audio = AudioSegment.from_file(first_file_path, format="wav")

                    # Append the rest
                    for filepath in batch_files[1:]:
                        segment = AudioSegment.from_file(filepath, format="wav")
                        combined_audio += segment

                    print(f"Successfully stitched {len(batch_files)} files. New duration: {len(combined_audio)/1000.0:.2f}s")

                except Exception as e:
                    print(f"Error during audio stitching: {e}")
                    # Decide how to handle: maybe skip this batch and retry later?
                    # For now, we'll just log and continue the loop.
                    # Consider removing problematic files from tracked_files if identifiable.
                    combined_audio = None # Ensure it's None if stitching failed

                # --- 4. Process and Export Stitched Audio ---
                processed_stitch_path = None
                if combined_audio:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    stitched_filename = f"stitched_batch_{timestamp}.wav"
                    stitched_filepath = os.path.join(TEMP_FOLDER, stitched_filename)
                    model_title = f"Batch_{timestamp}" # Generate a unique model title

                    processed_stitch_path = process_and_export_stitched(combined_audio, stitched_filepath)

                # --- 5. Upload to Fish Audio API ---
                upload_successful = False
                upload_disabled_this_batch = False # Flag for disabled upload
                if processed_stitch_path:
                    model_id = upload_to_fish_audio(API_TOKEN, processed_stitch_path, model_title)

                    # --- ADD THIS CHECK ---
                    if model_id == "upload_disabled":
                        upload_successful = True # Treat as success for state update
                        upload_disabled_this_batch = True # Mark that upload was skipped
                    # ----------------------
                    elif model_id: # Includes "submitted_no_id" as success for processing
                        upload_successful = True
                    else:
                        print(f"API upload failed for batch {model_title}.")
                        # Keep files in tracked_files to retry next time threshold is met
                else:
                    print("Skipping API upload due to stitching or processing failure.")

                # --- 6. Update State and Cleanup ---
                if upload_successful:
                    print(f"Successfully processed batch. Updating state for {len(batch_files)} files.")
                    # ...(state update logic remains the same)...
                    # for filepath in batch_files:
                    #    processed_files.add(filepath)
                    #    if filepath in tracked_files: del tracked_files[filepath]
                    #    # Optional move logic...

                # --- MODIFY CLEANUP ---
                # Clean up the temporary stitched file ONLY if upload was NOT disabled
                if not upload_disabled_this_batch and processed_stitch_path and os.path.exists(processed_stitch_path):
                    try:
                        os.remove(processed_stitch_path)
                        print(f"Cleaned up temporary file: {processed_stitch_path}")
                    except OSError as e:
                        print(f"Warning: Could not remove temporary file {processed_stitch_path}: {e}")
                elif upload_disabled_this_batch:
                    print(f"--- API UPLOAD DISABLED --- Stitched file kept for inspection:")
                    print(f"    {processed_stitch_path}")
                    print(f"    (Note: This file will be deleted when the script stops or if the temp folder is cleaned up on next run)")
                # -----------------------

                print("--------------------------------------------------") # Separator after processing a batch
            # --- 7. Clear all files in Dissonance_Diagnostics folder ---
            try:
                for filename in os.listdir(MONITOR_FOLDER):
                    file_path = os.path.join(MONITOR_FOLDER, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                print(f"Cleared all files in monitor folder: {MONITOR_FOLDER}")
            except Exception as e:
                print(f"Warning: Failed to clear files in monitor folder {MONITOR_FOLDER}: {e}")

            # --- 8. Wait for the next polling interval ---
            # print(f"Waiting for {POLLING_INTERVAL_SECONDS} seconds...") # Optional: Verbose logging
            time.sleep(POLLING_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n--- Script interrupted by user. Exiting. ---")
    finally:
        # --- Final Cleanup ---
        if os.path.exists(TEMP_FOLDER):
            try:
                shutil.rmtree(TEMP_FOLDER)
                print(f"Cleaned up temporary folder: {TEMP_FOLDER}")
            except OSError as e:
                print(f"Warning: Could not remove temporary folder {TEMP_FOLDER} on exit: {e}")
        print("--- Monitor stopped. ---")