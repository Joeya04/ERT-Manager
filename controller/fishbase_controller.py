#controller to pull R scripts

import json
import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd

from controller.rscript_utils import run_r_script


# ----------------------------------------------------
# File Locations
# ----------------------------------------------------

# Resolve paths relative to this file so the controller
# works regardless of the current working directory.
_BASE_DIR = Path(__file__).resolve().parents[1]

R_SCRIPT = _BASE_DIR / "rfishbase" / "fishbase_workflow.R"


# ----------------------------------------------------
# Main Controller
# ----------------------------------------------------

def run_fishbase(df, species_col=None, lookup_source="FishBase"):
    """
    Runs the FishBase workflow in R.

    Parameters
    ----------
    df : pandas.DataFrame
        The input dataframe containing species information.
        Must have a column with scientific names to look up.
    species_col : str, optional
        The name of the column containing scientific names.
        If not provided, the R script will auto-detect by looking
        for "Species", "Sci_name", "scientificName", or "Scientific Name".
    lookup_source : str, optional
        The database to query: "FishBase" or "SeaLifeBase".
        Defaults to "FishBase".

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
    # Create a unique temp directory for this run
    #
    temp_dir = tempfile.mkdtemp(prefix="ert_fishbase_")
    input_file = os.path.join(temp_dir, "fishbase_input.csv")
    manifest_file = os.path.join(temp_dir, "fishbase_manifest.json")

    try:
        #
        # Save dataframe for R
        #
        df.to_csv(input_file, index=False)

        #
        # Run R workflow
        #
        result = run_r_script(
            [
                str(R_SCRIPT),
                input_file,
                manifest_file,
                str(species_col) if species_col else "",
                str(lookup_source),
            ],
            cwd=str(_BASE_DIR),
        )

        #
        # Read manifest
        #
        with open(manifest_file, "r") as f:
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
    finally:
        #
        # Clean up temp directory
        #
        shutil.rmtree(temp_dir, ignore_errors=True)
