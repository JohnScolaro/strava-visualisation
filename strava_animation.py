import requests
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from typing import Any
import os.path
import datetime as dt
from matplotlib.ticker import FuncFormatter
from dateutil import parser
from matplotlib.lines import Line2D
import math
from keys import CLIENT_SECRET, CLIENT_ID
from matplotlib import cm
from matplotlib.colors import Normalize


def get_strava_activity_data() -> list[dict[str, Any]]:
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

    # Get all running activities with average heartrate
    params = {"per_page": 200, "page": 1}
    activities = []
    while True:
        response = requests.get(activities_url, headers=headers, params=params)
        if not response.ok:
            raise Exception(
                f"Request failed with status code {response.status_code}: {response.text}"
            )
        new_activities = [activity for activity in response.json()]
        filtered_activities = [
            activity
            for activity in new_activities
            if activity["type"] == "Run" and "average_heartrate" in activity
        ]
        activities += filtered_activities
        if len(new_activities) < params["per_page"]:
            break
        params["page"] += 1

    # Sort activities by date
    activities.sort(key=lambda activity: activity["start_date"])
    return activities


def strava_data_already_exists() -> bool:
    cache_path = get_json_cache_file_path()

    # Check if the JSON file exists
    return os.path.isfile(cache_path)


def save_strava_activity_data(activities: list[dict[str, Any]]) -> None:
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


def plot_data(activities: list[dict[str, Any]]) -> None:
    # Set up animation
    fig, ax = plt.subplots()
    plt.figure(figsize=(8, 5))

    scatter = ax.scatter(
        [],
        [],
    )

    cmap = plt.cm.get_cmap("plasma")

    # init the figure
    fig, ax = plt.subplots(figsize=(8, 7))

    average_heartrates = [activity["average_heartrate"] for activity in activities]
    average_paces = [
        meters_per_second_to_seconds_per_kilometer(activity["average_speed"])
        for activity in activities
    ]
    start_times = [
        parser.parse(activity["start_date"]).timestamp() for activity in activities
    ]
    distances = [activity["distance"] / 1000 for activity in activities]

    normalized_start_times = [
        (t - min(start_times)) / (max(start_times) - min(start_times))
        for t in start_times
    ]
    normalized_distances = [
        (d - min(distances)) / (max(distances) - min(distances)) for d in distances
    ]
    colours = [
        cmap(normalized_start_time) for normalized_start_time in normalized_start_times
    ]
    sizes = [s * 200 for s in normalized_distances]

    # Gradient legend
    ticks = [0.001, 0.25, 0.5, 0.75, 1.0]
    plt.set_cmap(cmap)
    cbar = fig.colorbar(
        cm.ScalarMappable(norm=Normalize(vmin=0, vmax=1), cmap=cmap),
        ax=ax,
        location="bottom",
    )

    labels = [
        dt.datetime.fromtimestamp(
            tick * (max(start_times) - min(start_times)) + min(start_times)
        ).strftime("%d/%m/%y")
        for tick in ticks
    ]
    cbar.ax.set_xticks(ticks)
    cbar.ax.set_xticklabels(labels)

    def set_pretty_things() -> None:
        x_min, x_max = (
            min(activity["average_heartrate"] for activity in activities) - 10,
            max(activity["average_heartrate"] for activity in activities) + 10,
        )

        y_min, y_max = (
            min(
                meters_per_second_to_seconds_per_kilometer(activity["average_speed"])
                for activity in activities
            )
            * 0.9,
            max(
                meters_per_second_to_seconds_per_kilometer(activity["average_speed"])
                for activity in activities
            )
            * 1.1,
        )

        plt.grid(linestyle="--")

        # Set labels
        ax.set_xlabel("Average Heartrate (BPM)")
        ax.set_ylabel("Average Pace (mins/km)")
        ax.set_title("Running Improvement Visualiser")

        # Set graph limits
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

        # Set legend
        legend_elements = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="k",
                label="5km",
                markerfacecolor="k",
                markersize=math.sqrt(
                    (5.0000 - min(distances)) / (max(distances) - min(distances)) * 200
                ),
                linestyle="",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="k",
                label="10km",
                markerfacecolor="k",
                markersize=math.sqrt(
                    (10.0000 - min(distances)) / (max(distances) - min(distances)) * 200
                ),
                linestyle="",
            ),
        ]
        ax.legend(handles=legend_elements, loc="upper right")

    set_pretty_things()

    def update(frame):
        print(f"Generating frame {frame}/{len(activities)}")
        ax.clear()
        set_pretty_things()

        x = average_heartrates[: frame + 1]
        y = average_paces[: frame + 1]
        s = sizes[: frame + 1]
        c = colours[: frame + 1]

        # format the y-axis labels with time in minutes and seconds
        def format_time(x, pos):
            mins = int(x / 60)
            secs = int(x) % 60
            return f"{mins:02d}:{secs:02d}"

        plt.gca().yaxis.set_major_formatter(FuncFormatter(format_time))

        scatter = ax.scatter(x, y, s=s, c=c)
        return []

    ani = animation.FuncAnimation(
        fig, update, frames=len(activities), blit=True, interval=50
    )

    # Save animation as video
    ani.save("strava_activities.gif")


def meters_per_second_to_seconds_per_kilometer(speed: float) -> dt.timedelta:
    return 1000 / speed


if __name__ == "__main__":
    if not strava_data_already_exists():
        activities = get_strava_activity_data()
        save_strava_activity_data(activities)
    else:
        activities = load_cached_strava_activities()

    plot_data(activities)
