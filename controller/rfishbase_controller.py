#fishbase controller to pull R scripts

import json
import subprocess
from pathlib import Path

import pandas as pd


# ----------------------------------------------------
# File Locations
# ----------------------------------------------------

TEMP_DIR = Path("temp")

INPUT_FILE = TEMP_DIR / "fishbase_input.csv"

MANIFEST_FILE = TEMP_DIR / "fishbase_manifest.json"

R_SCRIPT = Path("r") / "fishbase_workflow.R"


# ----------------------------------------------------
# Main Controller
# ----------------------------------------------------

def run_fishbase(df):

    """
    Runs the FishBase workflow in R.

    Parameters
    ----------
    df : pandas.DataFrame

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

    df.to_csv(

        INPUT_FILE,

        index=False

    )

    #
    # Run R workflow
    #

    subprocess.run(

        [

            "Rscript",

            str(R_SCRIPT),

            str(INPUT_FILE),

            str(MANIFEST_FILE)

        ],

        check=True

    )

    #
    # Read manifest
    #

    with open(MANIFEST_FILE, "r") as f:

        manifest = json.load(f)

    #
    # Read returned dataframe
    #

    output_df = pd.read_csv(

        manifest["output_dataframe"]

    )

    #
    # Return all workflow outputs
    #

    return {

        "dataframe": output_df,

        "report": manifest.get("report"),

        "log": manifest.get("log"),

        "metadata": manifest.get("metadata", {})

    }


