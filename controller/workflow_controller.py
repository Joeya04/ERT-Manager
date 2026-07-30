############################################################
# workflow_controller.py
#
# Master workflow controller
#
# Coordinates all application modules
#
############################################################

from pathlib import Path
import pandas as pd

from models.workflow_state import WorkflowState

from formatter.ERT_date_puller_shiny import parse_ert_workbook
from controller.fishbase_controller import run_fishbase
from controller.plotting_controller import run_plot
from controller.export_controller import run_export


############################################################
# Load workbook
############################################################

def load_workbook(filepath, sheet_index_path=None):
    """
    Read the uploaded workbook into the workflow state.

    Parameters
    ----------
    filepath : str
        Path to the ERT workbook (Excel file with color-coded residence charts).
    sheet_index_path : str, optional
        Path to the sheet index workbook that maps species sheet names
        to their start rows. Required for the parser to know where
        each species table begins.
    """

    workflow = WorkflowState()

    workflow.workbook_path = filepath

    try:
        if sheet_index_path is None:
            raise ValueError(
                "sheet_index_path is required for the ERT parser. "
                "Please upload both the ERT Workbook Table and the Sheet Index Table."
            )

        workflow.raw_df = parse_ert_workbook(filepath, sheet_index_path)

        workflow.metadata["load_status"] = "parsed"
        workflow.metadata["parser"] = "ERT_date_puller_shiny"
        workflow.status["workbook_loaded"] = True

    except Exception as exc:
        if filepath.lower().endswith(".csv"):
            workflow.raw_df = pd.read_csv(filepath)
        else:
            workflow.raw_df = pd.DataFrame()

        workflow.metadata["load_status"] = "fallback"
        workflow.metadata["error"] = str(exc)

    return workflow


############################################################
# Formatting
############################################################

def run_formatting_step(workflow):
    """
    Run the formatting step on the raw dataframe.
    Currently a pass-through; the parser already produces
    a formatted dataframe.
    """
    workflow.formatted_df = workflow.raw_df
    workflow.status["formatting_complete"] = True
    return workflow


############################################################
# FishBase
############################################################

def run_fishbase_step(workflow):
    """
    Run the FishBase lookup step.

    run_fishbase returns a dict with a 'dataframe' key;
    we extract the DataFrame and store it on the workflow.
    """
    result = run_fishbase(workflow.raw_df)

    if isinstance(result, dict):
        workflow.fishbase_df = result.get("dataframe")
        workflow.metadata["fishbase_report"] = result.get("report", "")
        workflow.metadata["fishbase_log"] = result.get("log", "")
        workflow.metadata["fishbase_metadata"] = result.get("metadata", {})
    else:
        workflow.fishbase_df = result

    workflow.status["fishbase_complete"] = True
    return workflow


############################################################
# Statistics
############################################################

def run_statistics_step(workflow):
    """
    Run the statistics step.

    Currently a pass-through; the fishbase dataframe
    is used directly for plotting.
    """
    workflow.statistics_df = workflow.fishbase_df
    workflow.status["statistics_complete"] = True
    return workflow


############################################################
# Plotting
############################################################

def run_plot_step(workflow, plot_options):
    """
    Run the plotting step.

    Calls run_plot with the statistics dataframe (or raw_df
    as fallback) and the user-supplied plot options.
    """
    data_df = workflow.statistics_df
    if data_df is None:
        data_df = workflow.raw_df

    if data_df is None:
        raise ValueError("No data available for plotting. Please load a workbook first.")

    csv_path = _write_dataframe_to_csv(data_df)

    workflow.plot_manifest = run_plot(
        input_csv=csv_path,
        options=plot_options,
    )

    workflow.status["plots_generated"] = True
    return workflow


def _write_dataframe_to_csv(df):
    """Write a DataFrame to a temporary CSV file and return the path."""
    import os
    import tempfile

    temp_dir = tempfile.mkdtemp(prefix="ert_workflow_", dir=tempfile.gettempdir())
    csv_path = os.path.join(temp_dir, "plot_input.csv")
    df.to_csv(csv_path, index=False)
    return csv_path


############################################################
# Export
############################################################

def run_export_step(workflow, export_options):
    """
    Run the export step.
    """
    workflow.export_manifest = run_export(
        workflow_state=workflow,
        export_options=export_options,
    )
    workflow.status["export_complete"] = True
    return workflow


############################################################
# Complete workflow
############################################################

def run_complete_workflow(filepath, sheet_index_path, plot_options, export_options):
    """
    Run the entire workflow from beginning to end.
    """
    workflow = load_workbook(filepath, sheet_index_path)

    workflow = run_formatting_step(workflow)

    workflow = run_fishbase_step(workflow)

    workflow = run_statistics_step(workflow)

    workflow = run_plot_step(workflow, plot_options)

    workflow = run_export_step(workflow, export_options)

    return workflow
