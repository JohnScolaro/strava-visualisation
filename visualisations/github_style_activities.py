from typing import Any
from pathlib import Path
import matplotlib.pyplot as plt
import datetime as dt
import pandas as pd
import seaborn
from collections import Counter
from matplotlib.patches import Patch
import matplotlib
from stravalib.model import Activity

CMAP = "YlGn"


def plot(activities: list[Activity], output_directory: Path) -> None:
    activity_dates = [activity.start_date_local for activity in activities]

    earliest_activity = min(activity_dates)
    latest_activity = max(activity_dates)

    activity_counter = Counter(
        dt.datetime(activity_date.year, activity_date.month, activity_date.day)
        for activity_date in activity_dates
    )

    earliest_day = dt.datetime(earliest_activity.year, 1, 1)
    latest_day = dt.datetime(latest_activity.year, 12, 31)

    data = []
    day = earliest_day
    while day <= latest_day:
        data.append(
            {
                "year": day.year,
                "week": get_week_of_year_from_datetime(day),
                "day_of_week": day.weekday(),
                "num_activities": activity_counter[day],
            }
        )
        day += dt.timedelta(days=1)

    df = pd.DataFrame(data)

    year = earliest_activity.year
    while year <= latest_activity.year:
        generate_graph_for_year(df, year, output_directory)
        year += 1


def generate_graph_for_year(
    df: pd.DataFrame, year: int, output_directory: Path
) -> None:
    plt.clf()

    year_df = df[df["year"] == year]

    year_df = modify_activity_count(year_df)

    year_df = year_df.pivot(
        values=["num_activities"], index=["day_of_week"], columns=["week"]
    ).fillna(0)

    # Change row names to weeks
    days_of_week = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday",
    }
    year_df.index = year_df.index.map(days_of_week)

    # Change col names to week num only
    year_df.columns = year_df.columns.get_level_values(1)

    fig = plt.figure(figsize=(16, 2.5))
    plt.title(f"Activity Frequency for Calendar Year {year}")
    ax = seaborn.heatmap(
        year_df, linewidths=5, cmap=CMAP, linecolor="white", square=True, cbar=False
    )

    # Change x ticks to months
    plt.xticks(
        [
            get_week_of_year_from_datetime(dt.datetime(year, month, 1))
            for month in range(1, 13)
        ],
        [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
    )

    # Remove x and y labels
    ax.set(xlabel=None)
    ax.set(ylabel=None)

    # Add legend
    cmap = matplotlib.colormaps[CMAP]
    no_activities_colour = cmap(0.0)
    one_activity_colour = cmap(0.5)
    multi_activities_colour = cmap(1.0)

    legend_elements = [
        Patch(facecolor=no_activities_colour, label="No Activities"),
        Patch(facecolor=one_activity_colour, label="One Activity"),
        Patch(facecolor=multi_activities_colour, label="Multiple Activities"),
    ]
    fig.legend(loc="center right", handles=legend_elements)

    # Shift plot over a little to the left so that the spacing with the legend looks aesthetic.
    bbox = fig.axes[0].get_position()
    fig.axes[0].set_position([bbox.x0 / 1.7, bbox.y0, bbox.width, bbox.height])

    plt.savefig(output_directory / f"github_style_activity_counter_{year}.png")


def get_week_of_year_from_datetime(datetime: dt.datetime) -> int:
    return int(datetime.strftime("%U"))


def modify_activity_count(df: pd.DataFrame) -> pd.DataFrame:
    """
    It's not uncommon for users to have many activities in one day. When
    scaled on a normal colour map, this makes regular days look terrible,
    and only one day look a dark green colour. It makes more sense to crush
    all days with more than 1 activity into a "multiple activities" day which
    allows us to control the colours of the plot more effectivly. This function
    does that modification to the df.
    """
    df = df.copy()

    def scale_numbers(a: pd.Series) -> pd.Series:
        if a["num_activities"] >= 2:
            a["num_activities"] = 2

    df.apply(scale_numbers, axis=1)
    return df


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
