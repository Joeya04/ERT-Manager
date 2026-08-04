############################################################
# workflow_state.py
#
# Master application state
#
# Purpose:
#     Stores all datasets, manifests, metadata, and workflow
#     status for the current Shiny session.
#
# Used by:
#     workflow_controller.py
#     formatting_controller.py
#     rfishbase_controller.py
#     statistics_controller.py
#     plotting_controller.py
#     export_controller.py
#
############################################################

from dataclasses import dataclass, field
from typing import Optional
import pandas as pd


@dataclass
class WorkflowState:
    """
    Represents the state of the ERT analysis workflow.

    Architecture Note:
    The Shiny app (app.py) uses module-level reactive.Value() objects
    for cross-tab UI state management (e.g., residence_chart_data,
    fishbase_lookup_data, plot_manifest_state). WorkflowState is used
    as a return type from load_workbook() and is not used for cross-tab
    state sharing. This is a deliberate design choice: reactive values
    provide automatic reactivity for UI updates, while WorkflowState
    provides a structured data container for the workbook parsing pipeline.
    """

    ########################################################
    # Session Information
    ########################################################

    session_name: str = "Untitled Session"

    workbook_path: Optional[str] = None

    species_col: Optional[str] = None

    lookup_source: str = "FishBase"

    ########################################################
    # Uploaded Data
    ########################################################

    raw_df: Optional[pd.DataFrame] = None

    ########################################################
    # Workflow Outputs
    ########################################################

    formatted_df: Optional[pd.DataFrame] = None

    fishbase_df: Optional[pd.DataFrame] = None

    statistics_df: Optional[pd.DataFrame] = None

    ########################################################
    # Current Working Dataset
    #
    # Updated by controllers when appropriate.
    # Allows downstream pages to choose
    # "Current Data" as a source.
    ########################################################

    current_df: Optional[pd.DataFrame] = None

    ########################################################
    # Plotting
    ########################################################

    plot_manifest: Optional[dict] = None

    ########################################################
    # Export
    ########################################################

    export_manifest: Optional[dict] = None

    ########################################################
    # Metadata
    ########################################################

    metadata: dict = field(default_factory=dict)

    ########################################################
    # Workflow Status
    #
    # Used by the UI to determine whether
    # individual workflow steps have been run.
    ########################################################

    status: dict = field(
        default_factory=lambda: {

            "workbook_loaded": False,

            "formatting_complete": False,

            "fishbase_complete": False,

            "statistics_complete": False,

            "plots_generated": False,

            "export_complete": False

        }
    )

    ########################################################
    # User Selections
    #
    # Stores the most recent options selected
    # in the Shiny interface.
    ########################################################

    selections: dict = field(default_factory=dict)

    ########################################################
    # Messages
    #
    # Controllers may append informational,
    # warning, or error messages here.
    ########################################################

    messages: list = field(default_factory=list)

    ########################################################
    # Convenience Methods
    ########################################################

    def reset_outputs(self):
        """
        Clear all workflow outputs while
        preserving the uploaded workbook.
        """

        self.formatted_df = None
        self.fishbase_df = None
        self.statistics_df = None
        self.current_df = None

        self.plot_manifest = None
        self.export_manifest = None

        self.status.update({

            "formatting_complete": False,

            "fishbase_complete": False,

            "statistics_complete": False,

            "plots_generated": False,

            "export_complete": False

        })

    def set_current_data(self, dataframe):
        """
        Update the current working dataframe.
        """

        self.current_df = dataframe

    def add_message(self, message):
        """
        Store a workflow message.
        """

        self.messages.append(message)