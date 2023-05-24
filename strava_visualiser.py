"""
Parent program that orchestrates the generation of visualisations.

This parent programs job is to:
    1: Pull down all Strava data
    2: Call all visualisation generating modules, passing them the data they
        require to run, and supplying them with locations to output their
        visualistations to.
"""

import requests
import json
import os.path
from keys import CLIENT_SECRET, CLIENT_ID
from typing import Any
import os
import importlib.util


def get_strava_activity_data_from_web() -> list[dict[str, Any]]:
    # Set up API credentials
    redirect_uri = "http://localhost:8000/"
    authorization_url = f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope=profile:read_all,activity:read_all"

    # Print authorization URL and prompt user to visit it
    print(
        f"Please visit the following URL to authorize your Strava account:\n{authorization_url}"
    )
    authorization_code = input("Enter the authorization code: ")

    # Exchange authorization code for access token
    access_token_url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": authorization_code,
        "grant_type": "authorization_code",
        "scope": "activity:read",
    }
    response = requests.post(access_token_url, data=data)
    if not response.ok:
        raise Exception(
            f"Request failed with status code {response.status_code}: {response.text}"
        )
    access_token = response.json()["access_token"]

    # Set up API endpoints
    base_url = "https://www.strava.com/api/v3"
    activities_url = f"{base_url}/athlete/activities"

    # Set up headers
    headers = {"authorization": f"Bearer {access_token}", "accept": "application/json"}

    # Get all activities
    params = {"per_page": 200, "page": 1}
    activities = []
    while True:
        response = requests.get(activities_url, headers=headers, params=params)
        if not response.ok:
            raise Exception(
                f"Request failed with status code {response.status_code}: {response.text}"
            )
        new_activities = [activity for activity in response.json()]
        activities += new_activities
        if len(new_activities) < params["per_page"]:
            break
        params["page"] += 1

    return activities


def strava_data_cache_already_exists() -> bool:
    cache_path = get_json_cache_file_path()

    # Check if the JSON file exists
    return os.path.isfile(cache_path)


def save_strava_activity_data_to_cache(activities: list[dict[str, Any]]) -> None:
    cache_path = get_json_cache_file_path()

    # Wipe the JSON file if it exists, then dump the list of dictionaries to it
    with open(cache_path, "w") as f:
        json.dump(activities, f)
        print("Successfully dumped to activity_cache.json")


def load_cached_strava_activities() -> list[dict[str, Any]]:
    cache_path = get_json_cache_file_path()

    # Wipe the JSON file if it exists, then dump the list of dictionaries to it
    with open(cache_path, "r") as f:
        activities = json.load(f)
        print("Successfully loaded from activity_cache.json")

    return activities


def get_json_cache_file_path() -> str:
    # Get the path of the currently executing file
    current_file_path = os.path.abspath(__file__)

    # Get the directory containing the currently executing file
    current_directory = os.path.dirname(current_file_path)

    # Construct the path to the JSON file
    json_file_path = os.path.join(current_directory, "activity_cache.json")
    return json_file_path


def get_strava_activities():
    if not strava_data_cache_already_exists():
        activities = get_strava_activity_data_from_web()
        save_strava_activity_data_to_cache(activities)
    else:
        activities = load_cached_strava_activities()
    return activities


def traverse_modules_and_call_function(activities: list[dict[str, Any]]):
    folder_path = "visualisations"
    function_name = "plot"

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                module_name = os.path.splitext(file)[0]
                module_path = os.path.join(root, file)

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, function_name) and callable(
                    getattr(module, function_name)
                ):
                    function = getattr(module, function_name)
                    function(activities)  # Call the function


if __name__ == "__main__":
    activities = get_strava_activities()
    traverse_modules_and_call_function(activities)
