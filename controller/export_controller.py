############################################################
# export_controller.py
#
# Coordinates export of workflow results to various formats
# (Excel, CSV, plots).
#
# Called from:
#     workflow_controller.py
#     app.py (Visualization tab)
#
############################################################

import json
import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd


def run_export(workflow_state, export_options):
    """
    Export workflow results to the requested formats.

    Parameters
    ----------
    workflow_state : WorkflowState
        The current workflow state containing all dataframes and manifests.
    export_options : dict
        Options specifying what to export. Supported keys:
        - "formats": list of formats to export (e.g. ["excel", "csv"])
        - "output_directory": directory to write exports to
        - "include_plots": bool, whether to include plot files

    Returns
    -------
    dict
        A manifest describing what was exported:
        {
            "exports": [list of exported file paths],
            "report": "...",
            "metadata": {...}
        }
    """

    output_dir = export_options.get(
        "output_directory",
        os.path.join(tempfile.gettempdir(), "ert_exports"),
    )
    os.makedirs(output_dir, exist_ok=True)

    formats = export_options.get("formats", ["csv"])
    include_plots = export_options.get("include_plots", False)

    exported_files = []

    # Export raw dataframe
    if workflow_state.raw_df is not None:
        for fmt in formats:
            if fmt == "csv":
                path = os.path.join(output_dir, "raw_data.csv")
                workflow_state.raw_df.to_csv(path, index=False)
                exported_files.append(path)
            elif fmt == "excel":
                path = os.path.join(output_dir, "raw_data.xlsx")
                workflow_state.raw_df.to_excel(path, index=False)
                exported_files.append(path)

    # Export fishbase dataframe
    if workflow_state.fishbase_df is not None:
        for fmt in formats:
            if fmt == "csv":
                path = os.path.join(output_dir, "fishbase_data.csv")
                workflow_state.fishbase_df.to_csv(path, index=False)
                exported_files.append(path)
            elif fmt == "excel":
                path = os.path.join(output_dir, "fishbase_data.xlsx")
                workflow_state.fishbase_df.to_excel(path, index=False)
                exported_files.append(path)

    # Export plot manifest
    if workflow_state.plot_manifest is not None and include_plots:
        manifest_path = os.path.join(output_dir, "plot_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(workflow_state.plot_manifest, f, indent=2)
        exported_files.append(manifest_path)

    report = f"Exported {len(exported_files)} file(s) to {output_dir}."

    return {
        "exports": exported_files,
        "report": report,
        "metadata": {
            "output_directory": output_dir,
            "formats": formats,
            "include_plots": include_plots,
        },
    }


def run_export_plots(plot_manifest, target_dir, create_subdir=False, subdir_name="ERT_Plots"):
    """
    Export generated plot files to a user-specified directory.

    Parameters
    ----------
    plot_manifest : dict
        The manifest returned by run_plot, containing a "plots" key
        with a list of plot file paths.
    target_dir : str
        The base directory to export to.
    create_subdir : bool
        If True, create a subdirectory within target_dir.
    subdir_name : str
        Name of the subdirectory to create.

    Returns
    -------
    dict
        {
            "exports": [list of exported file paths],
            "report": "...",
            "metadata": {...}
        }
    """

    if not plot_manifest or "error" in plot_manifest:
        return {
            "exports": [],
            "report": "No plots to export.",
            "metadata": {"target_dir": target_dir},
        }

    plot_files = plot_manifest.get("plots", [])
    if not plot_files:
        return {
            "exports": [],
            "report": "No plots to export.",
            "metadata": {"target_dir": target_dir},
        }

    # Create subdirectory if requested
    if create_subdir and subdir_name:
        target_dir = os.path.join(target_dir, subdir_name)

    os.makedirs(target_dir, exist_ok=True)

    exported_files = []
    for plot_file in plot_files:
        if os.path.exists(plot_file):
            dest = os.path.join(target_dir, os.path.basename(plot_file))
            shutil.copy2(plot_file, dest)
            exported_files.append(dest)

    # Also export the manifest
    manifest_dest = os.path.join(target_dir, "plot_manifest.json")
    with open(manifest_dest, "w", encoding="utf-8") as f:
        json.dump(plot_manifest, f, indent=2)
    exported_files.append(manifest_dest)

    report = f"Exported {len(exported_files)} file(s) to {target_dir}."

    return {
        "exports": exported_files,
        "report": report,
        "metadata": {
            "target_dir": target_dir,
            "create_subdir": create_subdir,
            "subdir_name": subdir_name,
        },
    }


def run_export_data(dataframes, target_dir, formats=None):
    """
    Export one or more dataframes to the target directory.

    Parameters
    ----------
    dataframes : dict
        A mapping of name -> DataFrame to export.
    target_dir : str
        The directory to write exports to.
    formats : list
        List of formats to export (e.g. ["csv", "excel"]).

    Returns
    -------
    dict
        {
            "exports": [list of exported file paths],
            "report": "...",
            "metadata": {...}
        }
    """

    if formats is None:
        formats = ["csv"]

    os.makedirs(target_dir, exist_ok=True)

    exported_files = []

    for name, df in dataframes.items():
        if df is None:
            continue
        for fmt in formats:
            if fmt == "csv":
                path = os.path.join(target_dir, f"{name}.csv")
                df.to_csv(path, index=False)
                exported_files.append(path)
            elif fmt == "excel":
                path = os.path.join(target_dir, f"{name}.xlsx")
                df.to_excel(path, index=False)
                exported_files.append(path)

    report = f"Exported {len(exported_files)} file(s) to {target_dir}."

    return {
        "exports": exported_files,
        "report": report,
        "metadata": {
            "target_dir": target_dir,
            "formats": formats,
        },
    }
