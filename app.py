# App interface for the Shiny app (in Python)

import json
import os
import tempfile

import pandas as pd
from shiny import App, reactive, render, ui

from controller.plotting_controller import run_plot
from controller.workflow_controller import load_workbook
from controller.fishbase_controller import run_fishbase


app_ui = ui.page_fluid(
    ui.h1("Enclosure Residence Time Calculator"),
    ui.navset_tab(
        ui.nav_panel(
            "Enclosure Residence Time Calculator Overview",
            ui.h2("Generating a Species Table"),
            ui.p(
                "Species residence tables are an important step toward determining the overall residency time for a given tank or enclosure."
                " They are created by using census counts for the target tank/enclosure over the study duration with addition and mortality records to determine the total number of unique individuals and their approximate residence times in that enclosure"
            ),
            ui.h3("How to Organize your data"),
            ui.p(
                "Enclosure residence time analysis requires data on study organisms to be structured so that each individual"
                "creature is assigned an enclosure entrance date and exit date.  These dates may be exact or estimated based on"
                "available records and associated data quality.  In the absence of comprehensive records and/or in the case of "
                "group-managed organisms, adopting certain assumptions uniformly to generate estimated entrance and exit dates"
                "is recommended."
            ),
            ui.p(
                "Organizational tools, such as the enclosure residence diagram below can help investigators reconstruct"
                "actual and/or estimated enclosure entrance and exit dates at the individual organism level when population records"
                "are spread across multiple repositories or complicated by inconsistent data management practices."
            ),
            ui.h4("Preparing Data for Upload and Analysis:"),
            ui.p(
                "Once enclosure residence time for each organism is determined and entrance and exit dates are assigned to each individual, "
                "the data should be organized as shown in the example below for uploading to the Enclosure Residence Time Calculator "
            ),
            ui.p(
                "Once your input data is structured as outlined above, it can be uploaded via the side panel (starting with Step 1). "
                "After uploading your data file, follow the subsequent steps to instruct the calculator which data column in your file represents "
                "the residence time for each organism (Step 2), and the censorship status (Step 3). Once steps 1-3 are completed, a summary of the "
                "uploaded data will appear below to verify the calculator in interpreting the file correctly. If everything appears correct, explore your data "
                "using the tabs on the right. "
            ),
            ui.p(
                "Disclaimer: We do not warrant that the service provided by the Enclosure Residence Time Calculator "
                "will be uninterrupted, error-free, or secure. Your data when using this calculator is "
                "stored and backed up on local and/or cloud storage. We have no liabiliity for any loss "
                "or misappropriation of your data under any circumstances."
            ),
        ),

        ui.nav_panel(
            "Generating Species Residence Tables",
            ui.page_sidebar(
                sidebar=ui.sidebar(
                    ui.p(
                        "Upload your ERT Workbook Table and Sheet Index Table  using the file upload buttons below. "
                        "The ERT Workbook Table should contain the data for your study organisms, while the Sheet Index Table should provide information about the structure of your workbook."
                    ),
                    ui.input_file("ert_input", "Upload ERT Workbook Table"),
                    ui.input_file("index_input", "Upload Sheet Index Table"),
                    ui.input_action_button("load_workbook", "Load Workbook"),
                    ui.output_text_verbatim("load_status"),
                    ui.output_text_verbatim("generated_status"),
                )
            ),
            ui.h2("Overview"),
            ui.p(
                "The number of unique individuals in a given tank or enclosure is determined by using census counts for the target tank/enclosure over the study duration in tandem with addition and mortality records. "
                " Creating residence charts can be first step toward visualizing complex datasets containing multiple record sources. Each table represents a single species, with each column representing a unique individual. "
                " Formatted charts can be translated inside of this tool by following the formatting rules below. "
            ),
            ui.h2("Steps to Generate Species Residence Tables"),
            ui.p(
                "Introduction dates are delineated with a green (hex code here?) cell with the corresponding date. "
                "Each departure dates delineated with red colored cells (Hex Code Here?) containing the departure or death date. "
                "Each row represents a timestep, such as years, and surivival of an individual to the next timestep is indicated by a green cell. "
            ),
        ),
        ui.nav_panel(
            "Fishbase Lookup Tool",
            ui.h2("Gathering Species Information from Fishbase"),
            ui.p("This tool matches the scientific names of your organisms with fishbase records. Diet, Ecology, and information on specific food items are available"
                 " Fishbase reference numbers are available, but full text citation translation will be integrated later"),
            ui.input_file("fishbase_input", "Upload Data"),
            ui.input_select("fishbase_data_source", "Use data from", ["Translated Residence Charts", "Uploaded data", "None"]),
            #Mapping for each type of analysis
            ui.input_select("lookup_source", "Database", ["FishBase", "SeaLifeBase"]),
            #ui.input_select("analysis type", "list", ["Ecology", "Fooditems", "Diet"]),
            ui.input_action_button("run_species", "Run Lookup"),
            ui.output_text_verbatim("species_status"),
        ),
        ui.nav_panel(
            "Visualization",
            ui.h2("Visualization"),
            ui.input_select("plot_data_source", "Use data from", ["Translated Residence Charts", "Fishbase lookup", "Uploaded data", "None"]),
            ui.input_file("visualization_input", "Upload Data"),
            ui.input_selectize("group_by", "Group By", choices=[], selected=None),
            ui.input_selectize("time_var", "Time column", choices=[], selected=None),
            ui.input_selectize("status_var", "Status column", choices=[], selected=None),
            ui.input_select("plot_type", "Plot Type", ["survival", "dumbbell"]),
            ui.input_radio_buttons("output_mode", "Output", ["single", "grouped", "both"]),
            ui.input_text("plot_title", "Plot title", value="ERT Plot"),
            ui.input_action_button("generate_plots", "Generate"),
            ui.output_text_verbatim("plot_status"),
            ui.output_text_verbatim("plot_manifest"),
        )
    )
)


def server(input, output, session):
    def _read_dataframe_from_path(path):
        if path.lower().endswith(".csv"):
            return pd.read_csv(path)
        if path.lower().endswith(".xlsx"):
            return pd.read_excel(path)
        if path.lower().endswith(".json"):
            return pd.read_json(path)
        raise ValueError("Unsupported file format. Please upload a CSV, Excel, or JSON file.")

    def _write_dataframe_to_csv(df):
        temp_dir = tempfile.mkdtemp(prefix="ert_app_", dir=tempfile.gettempdir())
        csv_path = os.path.join(temp_dir, "plot_input.csv")
        if hasattr(df, "to_csv"):
            df.to_csv(csv_path, index=False)
        else:
            with open(csv_path, "w", encoding="utf-8") as handle:
                handle.write(str(df))
        return csv_path

    def _resolve_fishbase_data():
        source_name = input.fishbase_data_source()
        if source_name == "Translated Residence Charts" and residence_chart_data() is not None:
            return residence_chart_data()

        uploaded_files = input.fishbase_input()
        if uploaded_files:
            return _read_dataframe_from_path(uploaded_files[0]["datapath"])

        return None

    def _resolve_visualization_data():
        source_name = input.plot_data_source()
        if source_name == "Fishbase lookup" and fishbase_lookup_data() is not None:
            return fishbase_lookup_data()
        if source_name == "Translated Residence Charts" and residence_chart_data() is not None:
            return residence_chart_data()

        uploaded_files = input.visualization_input()
        if uploaded_files:
            return _read_dataframe_from_path(uploaded_files[0]["datapath"])

        if source_name != "None":
            if fishbase_lookup_data() is not None:
                return fishbase_lookup_data()
            if residence_chart_data() is not None:
                return residence_chart_data()

        return None

    # Reactive value that holds the currently resolved visualization dataframe.
    # Used to dynamically populate the group_by, time_var, and status_var
    # selectize inputs with the columns of whatever data is available.
    viz_data = reactive.Value(None)

    @reactive.effect
    def _update_column_choices():
        """Update group_by, time_var, and status_var choices based on
        the currently resolved visualization data."""
        data = _resolve_visualization_data()
        viz_data.set(data)

        if data is None or not hasattr(data, "columns"):
            ui.update_selectize(
                session, "group_by", choices=[], selected=None,
                server=False,
            )
            ui.update_selectize(
                session, "time_var", choices=[], selected=None,
                server=False,
            )
            ui.update_selectize(
                session, "status_var", choices=[], selected=None,
                server=False,
            )
            return

        columns = list(data.columns)

        # Pick sensible defaults for time_var and status_var
        time_default = "yearfrac" if "yearfrac" in columns else (
            "time" if "time" in columns else columns[0]
        )
        status_default = "status" if "status" in columns else (
            columns[1] if len(columns) > 1 else columns[0]
        )

        ui.update_selectize(
            session, "group_by", choices=columns, selected=None,
            server=False,
        )
        ui.update_selectize(
            session, "time_var", choices=columns, selected=time_default,
            server=False,
        )
        ui.update_selectize(
            session, "status_var", choices=columns, selected=status_default,
            server=False,
        )

    @reactive.effect
    @reactive.event(input.load_workbook)
    def _load_workbook():
        uploaded_files = input.ert_input()
        if not uploaded_files:
            residence_chart_data.set(None)
            generated_status_state.set("No workbook was uploaded.")
            return

        path = uploaded_files[0]["datapath"]

        # Also get the sheet index file if uploaded
        index_files = input.index_input()
        index_path = index_files[0]["datapath"] if index_files else None

        try:
            analysis = load_workbook(path, sheet_index_path=index_path)
            residence_chart_data.set(analysis.raw_df)
            generated_status_state.set("Workbook loaded and prepared for downstream analysis.")
        except Exception as exc:
            residence_chart_data.set(None)
            generated_status_state.set(f"Workbook load failed: {exc}")

    @output
    @render.text
    def load_status():
        return generated_status_state() if generated_status_state() is not None else "Workbook not loaded."

    @reactive.effect
    @reactive.event(input.run_species)
    def _run_species():
        data = _resolve_fishbase_data()
        if data is None:
            fishbase_lookup_data.set(None)
            fishbase_status_state.set("No data available for fishbase lookup.")
            return

        try:
            result = run_fishbase(data)

            # run_fishbase returns a dict with a 'dataframe' key
            if isinstance(result, dict):
                output_df = result.get("dataframe")
                fishbase_lookup_data.set(output_df)
                fishbase_status_state.set(
                    f"Fishbase lookup complete. {len(output_df) if output_df is not None else 0} rows returned."
                )
            else:
                fishbase_lookup_data.set(result)
                fishbase_status_state.set(
                    f"Fishbase lookup complete. {len(result)} rows returned."
                )
        except Exception as exc:
            fishbase_lookup_data.set(None)
            fishbase_status_state.set(f"Fishbase lookup failed: {exc}")

    @output
    @render.text
    def species_status():
        return fishbase_status_state() if fishbase_status_state() is not None else ""

    @reactive.effect
    @reactive.event(input.generate_plots)
    def _generate_plots():
        data = _resolve_visualization_data()
        if data is None:
            plot_manifest_state.set({"error": "No data available for plotting."})
            return

        csv_path = _write_dataframe_to_csv(data)
        output_dir = os.path.join(tempfile.gettempdir(), "ert_plots")
        options = {
            "plot_type": input.plot_type(),
            "output_mode": input.output_mode(),
            "group_by": None if input.group_by() == "None" else input.group_by(),
            "mapping": {
                "group_var": None if input.group_by() == "None" else input.group_by(),
                "time_var": input.time_var(),
                "status_var": input.status_var(),
            },
            "title": input.plot_title(),
            "output_directory": output_dir,
        }

        try:
            manifest = run_plot(csv_path, options, manifest_path=os.path.join(output_dir, "manifest.json"))
            plot_manifest_state.set(manifest)
        except Exception as exc:
            plot_manifest_state.set({"error": str(exc)})

    @output
    @render.text
    def plot_status():
        manifest = plot_manifest_state()
        if not manifest:
            return "No plot generated yet."
        if "error" in manifest:
            return manifest["error"]
        return f"Generated {manifest.get('number_of_plots', 0)} plot(s)."

    @output
    @render.text
    def plot_manifest():
        manifest = plot_manifest_state()
        if not manifest:
            return ""
        return json.dumps(manifest, indent=2)


# Reactive storage
residence_chart_data = reactive.Value(None)
generated_status_state = reactive.Value(None)
fishbase_lookup_data = reactive.Value(None)
fishbase_status_state = reactive.Value(None)
plot_manifest_state = reactive.Value({})

app = App(app_ui, server)
