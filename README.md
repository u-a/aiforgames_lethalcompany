# LCMimicry Suite

This suite contains Python scripts for in-game LLM-driven TTS and voice model processing using Fish Audio.

## Prerequisites

*   **Python 3.7+**: Ensure Python is installed and added to your system's PATH. You can download it from [python.org](https://www.python.org/downloads/).
*   **API Keys**: You will need API keys from OpenAI and Fish Audio.

## Setup Instructions

1.  **Extract Files**: Extract all files from the provided archive into a folder on your computer (e.g., `C:\LCMimicrySuite`). All scripts and essential files should be in this main folder.
2.  **Configure API Keys**:
    *   Locate the `.env.example` file in the main package directory.
    *   **Rename** this file to `.env` (in the same main directory).
    *   Open the new `.env` file with a text editor.
    *   Replace `"YOUR_OPENAI_API_KEY_HERE"` and `"YOUR_FISH_AUDIO_API_KEY_HERE"` with your actual API keys. Save the file.
3.  **Run the Setup and Launch Script**:
    *   Double-click the `run_suite.bat` file located in the main package directory.
    *   This script will:
        *   Check for Python.
        *   Create a virtual environment (`.venv` folder) in the main directory.
        *   Install all necessary Python packages from `requirements.txt`.
        *   Launch the `voice_model2.py` and `ingame_llm_tts.py` scripts in separate command prompt windows.

## Usage

*   Once `run_suite.bat` has completed its setup, two new command prompt windows will appear:
    *   One for "Voice Model Processor" (`voice_model2.py`).
    *   One for "In-Game LLM TTS" (`ingame_llm_tts.py`).
*   These windows will show the output and logs for each script.
*   **`voice_model2.py`**:
    *   Monitors the `Dissonance_Diagnostics/` folder (expected at the top level) for new `.wav` files.
    *   When enough audio is collected, it stitches them and uploads them to Fish Audio to create/train a voice model.
*   **`ingame_llm_tts.py`**:
    *   Monitors the `watch_folder/` (this folder will be created at the top level by the script if it doesn't exist) for `.json` context files.
    *   When a new context file appears, it uses OpenAI to generate personalized voice lines and then uses Fish Audio TTS to generate audio, saving it to `test/` (also created at the top level).

## Stopping the Scripts

To stop the scripts, simply close their respective command prompt windows.

## Folder Structure (after running `run_suite.bat` once)

Your main package directory will look something like this:

LCMimicryPackage/
├── run_suite.bat
├── requirements.txt
├── .env.example
├── .env                       <-- Your API keys (you create this from .env.example)
├── ingame_llm_tts.py
├── voice_model2.py
├── cloned_tts.py
├── models_list.py
├── emotion_phrases.json
├── Dissonance_Diagnostics/    <-- Input for voice_model2.py (created externally or by other means at this level)
├── .venv/                     <-- Virtual environment (created by script)
├── watch_folder/              <-- Input for ingame_llm_tts.py (created by script)
├── test/                      <-- Output for ingame_llm_tts.py (created by script)
└── temp_stitch_processing/    <-- Temporary files for voice_model2.py (created by script)
└── README.md
