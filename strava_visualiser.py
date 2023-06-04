"""
Parent program that orchestrates the generation of visualisations.

This parent programs job is to:
    1: Pull down all Strava data
    2: Call all visualisation generating modules, passing them the data they
        require to run, and supplying them with locations to output their
        visualistations to.
"""

import os.path
from keys import CLIENT_SECRET, CLIENT_ID
from typing import Any
import os
import importlib.util
from pathlib import Path
from stravalib.client import Client
import pickle


def get_strava_activity_data_from_web() -> list[dict[str, Any]]:
    # Set up API credentials
    redirect_uri = "http://localhost:8000/"

    client = Client()
    authorize_url = client.authorization_url(
        client_id=CLIENT_ID, redirect_uri=redirect_uri
    )

    # Print authorization URL and prompt user to visit it
    print(
        f"Please visit the following URL to authorize your Strava account:\n{authorize_url}"
    )
    authorization_code = input("Enter the authorization code: ")

    token_response = client.exchange_code_for_token(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=authorization_code
    )
    access_token = token_response["access_token"]
    refresh_token = token_response["refresh_token"]
    expires_at = token_response["expires_at"]

    client.access_token = access_token
    client.refresh_token = refresh_token
    client.token_expires_at = expires_at

    activities = client.get_activities()
    return list(activities)


def strava_data_cache_already_exists() -> bool:
    cache_path = get_pickle_cache_file_path()

    # Check if the JSON file exists
    return os.path.isfile(cache_path)


def save_strava_activity_data_to_cache(activities: list[dict[str, Any]]) -> None:
    cache_path = get_pickle_cache_file_path()

    # Wipe the JSON file if it exists, then dump the list of dictionaries to it
    with open(cache_path, "wb") as f:
        pickle.dump(activities, f)
        print("Successfully dumped to cache.")


def load_cached_strava_activities() -> list[dict[str, Any]]:
    cache_path = get_pickle_cache_file_path()

    # Wipe the JSON file if it exists, then dump the list of dictionaries to it
    with open(cache_path, "rb") as f:
        activities = pickle.load(f)
        print("Successfully loaded from cache.")

    return activities


def get_pickle_cache_file_path() -> str:
    # Get the path of the currently executing file
    current_file_path = os.path.abspath(__file__)

    # Get the directory containing the currently executing file
    current_directory = os.path.dirname(current_file_path)

    # Construct the path to the JSON file
    file_path = os.path.join(current_directory, "activity_cache.obj")
    return file_path


def get_strava_activities():
    if not strava_data_cache_already_exists():
        activities = get_strava_activity_data_from_web()
        save_strava_activity_data_to_cache(activities)
    else:
        activities = load_cached_strava_activities()
    return activities


def traverse_modules_and_call_function(activities: list[dict[str, Any]]):
    visualisation_folder_name = "visualisations"
    function_name = "plot"

    # Create output folder
    folder_path = "output"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    output_directory = Path(folder_path)

    for root, dirs, files in os.walk(visualisation_folder_name):
        for file in files:
            if file.endswith(".py"):
                module_name = os.path.splitext(file)[0]
                module_path = os.path.join(root, file)

                # Create a subdirectory for the output if it doesn't exist.
                output_subdir = output_directory / module_name
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, function_name) and callable(
                    getattr(module, function_name)
                ):
                    function = getattr(module, function_name)
                    function(activities, output_subdir)  # Call the function


if __name__ == "__main__":
    activities = get_strava_activities()
    traverse_modules_and_call_function(activities)
