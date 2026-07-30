#controller to pull R scripts

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


# ----------------------------------------------------
# File Locations
# ----------------------------------------------------

# Resolve paths relative to this file so the controller
# works regardless of the current working directory.
_BASE_DIR = Path(__file__).resolve().parents[1]

TEMP_DIR = _BASE_DIR / "temp"

INPUT_FILE = TEMP_DIR / "fishbase_input.csv"

MANIFEST_FILE = TEMP_DIR / "fishbase_manifest.json"

R_SCRIPT = _BASE_DIR / "rfishbase" / "fishbase_workflow.R"


# ----------------------------------------------------
# Main Controller
# ----------------------------------------------------

def run_fishbase(df):
    """
    Runs the FishBase workflow in R.

    Parameters
    ----------
    df : pandas.DataFrame
        The input dataframe containing species information.
        Must have a column named 'Species' (or 'Sci_name') with
        scientific names to look up.

    Returns
    -------
    dict
        {
            "dataframe": pandas.DataFrame,
            "report": "...",
            "log": "...",
            "metadata": {...}
        }
    """

    #
    # Ensure temp directory exists
    #
    TEMP_DIR.mkdir(exist_ok=True)

    #
    # Save dataframe for R
    #
    df.to_csv(INPUT_FILE, index=False)

    #
    # Run R workflow
    #
    result = subprocess.run(
        [
            "Rscript",
            str(R_SCRIPT),
            str(INPUT_FILE),
            str(MANIFEST_FILE),
        ],
        check=True,
        cwd=str(_BASE_DIR),
        capture_output=True,
        text=True,
    )

    #
    # Read manifest
    #
    with open(MANIFEST_FILE, "r") as f:
        manifest = json.load(f)

    #
    # Read returned dataframe
    #
    output_df = pd.read_csv(manifest["output_dataframe"])

    #
    # Return all workflow outputs
    #
    return {
        "dataframe": output_df,
        "report": manifest.get("report"),
        "log": result.stdout,
        "metadata": manifest.get("metadata", {}),
    }
