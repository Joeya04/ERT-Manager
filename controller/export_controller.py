############################################################
# export_controller.py
#
# Coordinates export of workflow results to various formats
# (Excel, CSV, plots).
#
# Called from:
#     workflow_controller.py
#
############################################################

import os
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
        import json
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
