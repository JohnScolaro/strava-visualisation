import matplotlib.pyplot as plt
import matplotlib.animation as animation
from typing import Any
import datetime as dt
from matplotlib.ticker import FuncFormatter
from dateutil import parser
from matplotlib.lines import Line2D
import math
from matplotlib import cm
from matplotlib.colors import Normalize


def plot(activities: list[dict[str, Any]]) -> None:
    # Keep only runs with an average heartrate
    activities = [
        activity
        for activity in activities
        if activity["type"] == "Run" and "average_heartrate" in activity
    ]

    # Sort activities by start date.
    activities.sort(key=lambda activity: activity["start_date"])

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
