from typing import Any
from pathlib import Path
import datetime as dt
import itertools
import matplotlib.pyplot as plt
import matplotlib
from typing import Optional


def plot(activities: list[dict[str, Any]], output_directory: Path) -> None:
    # Get set of all the different types of activities this person has logged.
    activity_types = set(activity["type"] for activity in activities)

    for activity_type in activity_types:
        plot_graph(
            list(
                filter(lambda activity: activity["type"] == activity_type, activities)
            ),
            output_directory,
            activity_type,
        )

    plot_graph(activities, output_directory)


def plot_graph(
    activities: list[dict[str, Any]],
    output_directory: Path,
    activity_type: Optional[str] = None,
) -> None:
    format = "%Y-%m-%dT%H:%M:%SZ"
    graph_data = {}
    for activity in activities:
        activity_datetime = dt.datetime.strptime(activity["start_date_local"], format)
        year = activity_datetime.year
        year_data = graph_data.get(year, [0] * 366)
        year_data[activity_datetime.timetuple().tm_yday] += activity["elapsed_time"]
        graph_data[year] = year_data

    for year, year_data in graph_data.items():
        graph_data[year] = list(itertools.accumulate(year_data))

    # Remove additional zeros from end of data is if year is the current year
    current_year = dt.datetime.now().year
    if current_year in graph_data:
        graph_data[current_year] = graph_data[current_year][
            0 : graph_data[current_year].index(max(graph_data[current_year]))
        ]

    # Convert seconds to hours
    for year, year_data in graph_data.items():
        graph_data[year] = list(map(lambda x: x / 3600, year_data))

    # Plot graph and save it.
    plt.clf()

    for year, year_data in graph_data.items():
        plt.plot(list(range(1, len(year_data) + 1)), year_data, label=year)

    # Label the plot
    plt.ylabel("Activity Duration (Hours)")
    plt.xlabel("Days")
    plt.title(get_title_for_activity_type(activity_type))

    # Add a legend
    plt.legend()

    plt.savefig(output_directory / f"cumulative_time_spent_{activity_type}.png")


def get_title_for_activity_type(activity_type: Optional[str]) -> str:
    if activity_type:
        return f"Cumulative Time Spent on {activity_type} Activities"
    else:
        return "Time Logged on Strava by Year"


# For testing
if __name__ == "__main__":
    import os
    from pathlib import Path
    import json

    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    p = dir_path / ".." / "activity_cache.json"

    with open(p, "r") as json_file:
        json_data = json.load(json_file)

    plot(activities=json_data, output_directory=dir_path)
