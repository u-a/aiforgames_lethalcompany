import os
import sys
import logging
from dotenv import load_dotenv
# Note that FishAudioError is not available with the currently available library, do not use it
from typing import List # Import List for type hinting
from fish_audio_sdk import Session
from fish_audio_sdk.schemas import PaginatedResponse, ModelEntity # Import relevant schemas

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Configuration ---
# Set how many models you want to retrieve per API call.
# Adjust if you have a very large number of your own models.
# The API default is 10 if not specified.
MODELS_PER_PAGE = 50 # Adjusted default, can be increased if needed

def list_my_voice_models(api_key: str, page_size: int) -> List[str]:
    """
    Connects to Fish Audio and retrieves a list of voice model titles
    created by the user (using self_only=True) for the current page.

    Args:
        api_key: Your Fish Audio API key.
        page_size: The maximum number of models to request per page.

    Returns:
        A list of model titles. Returns an empty list if an error occurs,
        the API key is invalid, or no models are found on the current page.
    """
    model_titles: List[str] = []

    if not api_key:
        return model_titles # Return empty list if API key is missing

    try:
        session = Session(api_key)

        # Pass self_only=True and page_size to the SDK function
        paginated_response: PaginatedResponse[ModelEntity] = session.list_models(
            self_only=True,
            page_size=page_size
        )

        # Check if the response object exists and has the expected attributes
        if paginated_response and hasattr(paginated_response, 'items'):
            models_list = paginated_response.items

            if isinstance(models_list, list) and models_list:
                for model_entity in models_list:
                    if not isinstance(model_entity, ModelEntity):
                         continue
                    try:
                        title = getattr(model_entity, 'title', None)
                        if title is not None:
                            model_titles.append(title)
                    except AttributeError:
                        # Silently skip if 'title' attribute is missing or other attribute error
                        continue
    except Exception as e:
        # In case of any API error or other exception, return an empty list.
        # The calling script can decide how to handle this (e.g., log, retry).
        # For now, we ensure the function doesn't crash and returns the specified type.
        return [] # Return empty list on any exception

    return model_titles

# Main execution block
if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Retrieve the API key from environment variables
    fish_api_key = os.getenv("FISH_AUDIO_API_KEY")

    if not fish_api_key:
        print("Error: FISH_AUDIO_API_KEY not found in environment variables or .env file.")
        print("Please create a .env file with FISH_AUDIO_API_KEY=YOUR_API_KEY")
        sys.exit(1) # Exit if key is missing

    # Call the function to get model titles
    retrieved_titles = list_my_voice_models(fish_api_key, page_size=MODELS_PER_PAGE)

    if retrieved_titles:
        print("\n--- Your Voice Model Titles (from current page) ---")
        for idx, title in enumerate(retrieved_titles):
            print(f"{idx + 1}. {title}")
        print(f"\nRetrieved {len(retrieved_titles)} model titles.")
        print(f"Note: This list may be paginated. Increase MODELS_PER_PAGE or implement full pagination to see all models if more exist.")
    else:
        print("No voice model titles found for your account on the current page, or an error occurred during retrieval.")
