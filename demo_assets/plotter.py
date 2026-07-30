# Plotter for kaplan meier plots
#
# This demo script shows how to use the plotting controller
# to generate Kaplan-Meier survival plots from a dataframe.
#
# The actual plotting is performed by R scripts via the
# plotting_controller.run_plot function.

import os
import tempfile

from controller.plotting_controller import run_plot


def create_plot(df, x, y, title="Kaplan-Meier Plot"):
    """
    Create a single Kaplan-Meier survival plot.

    Parameters
    ----------
    df : pandas.DataFrame
        The input data containing time and status columns.
    x : str
        Name of the time variable column.
    y : str
        Name of the status variable column.
    title : str
        Plot title.

    Returns
    -------
    dict
        The plot manifest returned by run_plot.
    """
    temp_dir = tempfile.mkdtemp(prefix="ert_demo_", dir=tempfile.gettempdir())
    csv_path = os.path.join(temp_dir, "plot_input.csv")
    df.to_csv(csv_path, index=False)

    output_dir = os.path.join(temp_dir, "plots")

    options = {
        "plot_type": "survival",
        "output_mode": "single",
        "group_by": None,
        "mapping": {
            "group_var": None,
            "time_var": x,
            "status_var": y,
        },
        "title": title,
        "output_directory": output_dir,
    }

    manifest_path = os.path.join(output_dir, "manifest.json")
    manifest = run_plot(csv_path, options, manifest_path=manifest_path)

    return manifest


def create_plot_set(df, group_by, x, y, title="ERT Plot"):
    """
    Create a set of Kaplan-Meier plots, one per group.

    Parameters
    ----------
    df : pandas.DataFrame
        The input data.
    group_by : str
        Column name to group by.
    x : str
        Name of the time variable column.
    y : str
        Name of the status variable column.
    title : str
        Base plot title.

    Returns
    -------
    dict
        The plot manifest returned by run_plot.
    """
    temp_dir = tempfile.mkdtemp(prefix="ert_demo_", dir=tempfile.gettempdir())
    csv_path = os.path.join(temp_dir, "plot_input.csv")
    df.to_csv(csv_path, index=False)

    output_dir = os.path.join(temp_dir, "plots")

    options = {
        "plot_type": "survival",
        "output_mode": "grouped",
        "group_by": group_by,
        "mapping": {
            "group_var": group_by,
            "time_var": x,
            "status_var": y,
        },
        "title": title,
        "output_directory": output_dir,
    }

    manifest_path = os.path.join(output_dir, "manifest.json")
    manifest = run_plot(csv_path, options, manifest_path=manifest_path)

    return manifest
