import matplotlib.pyplot as plt
import matplotlib.animation as animation
from typing import Any
import datetime as dt
from matplotlib.ticker import FuncFormatter
from matplotlib.lines import Line2D
import math
from matplotlib import cm
from matplotlib.colors import Normalize
from pathlib import Path
from typing import Callable
from stravalib.model import Activity, ActivityType
from stravalib.unithelper import Quantity


def plot(activities: list[Activity], output_directory: Path) -> None:
    # Sort activities by start date.
    activities.sort(key=lambda activity: activity.start_date)

    runs = [
        activity
        for activity in activities
        if activity.type == "Run" and activity.average_heartrate is not None
    ]

    rides = [
        activity
        for activity in activities
        if activity.type == "Ride" and activity.average_heartrate is not None
    ]
    generate_plots("Runs", runs, output_directory)
    generate_plots("Rides", rides, output_directory)


def generate_plots(
    activity_type: ActivityType,
    activities: list[Activity],
    output_directory: Path,
):
    speed_conversion_function = get_speed_conversion_function(activity_type)
    y_axis_label = get_y_axis_label(activity_type)

    # Set up animation
    fig, ax = plt.subplots()
    plt.figure(figsize=(8, 5))

    ax.scatter(
        [],
        [],
    )

    cmap = plt.cm.get_cmap("plasma")

    # init the figure
    fig, ax = plt.subplots(figsize=(8, 7))

    average_heartrates = [activity.average_heartrate for activity in activities]
    average_paces = [
        speed_conversion_function(activity.average_speed) for activity in activities
    ]
    start_times = [activity.start_date.timestamp() for activity in activities]
    distances = [activity.distance / 1000 for activity in activities]

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
            min(activity.average_heartrate for activity in activities) - 10,
            max(activity.average_heartrate for activity in activities) + 10,
        )

        y_min, y_max = (
            min(
                speed_conversion_function(activity.average_speed)
                for activity in activities
            )
            * 0.9,
            max(
                speed_conversion_function(activity.average_speed)
                for activity in activities
            )
            * 1.1,
        )

        plt.grid(linestyle="--")

        # Set labels
        ax.set_xlabel("Average Heartrate (BPM)")
        ax.set_ylabel(y_axis_label)
        ax.set_title(f"{activity_type} Improvement Visualiser")

        # Set graph limits
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

        # Set legend
        legend_elements = get_legend_elements(activity_type, distances)
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

        y_axis_formatter = get_y_axis_formatter(activity_type)
        plt.gca().yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

        ax.scatter(x, y, s=s, c=c)
        return []

    update(len(activities) - 1)
    plt.savefig(
        output_directory
        / f"{activity_type.lower()}_average_heartrate_by_average_speed.png"
    )

    ani = animation.FuncAnimation(
        fig, update, frames=len(activities), blit=True, interval=50
    )

    # Save animation as video
    ani.save(
        output_directory
        / f"{activity_type.lower()}_average_heartrate_by_average_speed.gif"
    )


def meters_per_second_to_seconds_per_kilometer(speed: float) -> dt.timedelta:
    return 1000 / speed


def meters_per_second_to_kilometers_per_hour(speed: float) -> dt.timedelta:
    return speed / 1000 * 3600


def get_speed_conversion_function(
    activity_type: ActivityType,
) -> Callable[[float], float]:
    if activity_type == "Run":
        return meters_per_second_to_seconds_per_kilometer
    else:
        return meters_per_second_to_kilometers_per_hour


def get_y_axis_label(activity_type: ActivityType) -> str:
    if activity_type == "Run":
        return "Average Pace (mins/km)"
    else:
        return "Average Speed (kmph)"


def get_legend_elements(
    activity_type: ActivityType, distances: list[Quantity]
) -> list[Line2D]:
    distances = [float(distance) for distance in distances]
    if activity_type == "Run":
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
    else:
        return [
            Line2D(
                [0],
                [0],
                marker="o",
                color="k",
                label="20km",
                markerfacecolor="k",
                markersize=math.sqrt(
                    (20.0000 - min(distances)) / (max(distances) - min(distances)) * 200
                ),
                linestyle="",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="k",
                label="40km",
                markerfacecolor="k",
                markersize=math.sqrt(
                    (40.0000 - min(distances)) / (max(distances) - min(distances)) * 200
                ),
                linestyle="",
            ),
        ]


def get_y_axis_formatter(activity_type: ActivityType) -> Callable:
    if activity_type == "Run":

        def format_time(x, pos):
            mins = int(x / 60)
            secs = int(x) % 60
            return f"{mins:02d}:{secs:02d}"

        return format_time
    else:

        def format_speed(x, pos):
            return x

        return format_speed


# For testing
if __name__ == "__main__":
    import os
    from pathlib import Path
    import pickle

    dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    p = dir_path / ".." / "activity_cache.obj"

    with open(p, "rb") as json_file:
        json_data = pickle.load(json_file)

    plot(activities=json_data, output_directory=dir_path)
