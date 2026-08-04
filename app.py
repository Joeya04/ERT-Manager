# App interface for the Shiny app (in Python)

import base64
import json
import os
import tempfile

import pandas as pd
from shiny import App, reactive, render, ui

from controller.plotting_controller import run_plot
from controller.workflow_controller import load_workbook
from controller.fishbase_controller import run_fishbase
from controller.export_controller import run_export_plots, run_export_data


# Reactive storage — declared at module level so they are available
# when the server function is called. These are per-session in a
# production deployment; for now they are module-level singletons.
residence_chart_data = reactive.Value(None)
generated_status_state = reactive.Value(None)
fishbase_lookup_data = reactive.Value(None)
fishbase_status_state = reactive.Value(None)
fishbase_export_status_state = reactive.Value(None)
plot_manifest_state = reactive.Value({})
export_status_state = reactive.Value(None)

# Shared output directory — accessible across tabs
shared_output_dir = reactive.Value(None)


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
                    ui.input_file("ert_input", "Upload ERT Workbook Table", accept=[".csv", ".xlsx", ".xls"], multiple=False),
                    ui.input_file("index_input", "Upload Sheet Index Table", accept=[".csv", ".xlsx", ".xls"], multiple=False),
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
            ui.input_file("fishbase_input", "Upload Data", accept=[".csv", ".xlsx", ".xls"], multiple=False),
            ui.input_select("fishbase_data_source", "Use data from", ["Translated Residence Charts", "Uploaded data", "None"]),
            #Mapping for each type of analysis
            ui.input_select("lookup_source", "Database", ["FishBase", "SeaLifeBase"]),
            ui.input_select("species_col", "Scientific Name Column", choices=[], selected=None),
            ui.input_action_button("run_species", "Run Lookup"),
            ui.output_text_verbatim("species_status"),
            ui.input_text("export_dir", "Export Directory", value=""),
            ui.p("Enter the full path to the directory where data will be exported.", style="font-size: 12px; color: gray;"),
            ui.input_action_button("export_fishbase_summary", "Export Summary Table (Excel)"),
            ui.input_action_button("export_fishbase_joined", "Export Joined Table (Excel)"),
            ui.output_text_verbatim("fishbase_export_status"),
            ui.output_text_verbatim("shared_output_info"),
        ),
        ui.nav_panel(
            "Visualization",
            ui.h2("Visualization"),
            # Horizontal layout: Upload items | Plot customization
            ui.row(
                ui.column(
                    6,
                    ui.h4("Data Source & Upload"),
                    ui.input_select("plot_data_source", "Use data from", ["Translated Residence Charts", "Fishbase lookup", "Uploaded data", "None"]),
                    ui.input_file("visualization_input", "Upload Data", accept=[".csv", ".xlsx", ".xls"], multiple=False),
                    ui.input_selectize("group_by", "Group By", choices=[], selected=None),
                    ui.input_selectize("time_var", "Time column", choices=[], selected=None),
                    ui.input_selectize("status_var", "Status column", choices=[], selected=None),
                ),
                ui.column(
                    6,
                    ui.h4("Plot Customization"),
                    ui.input_select("plot_type", "Plot Type", ["survival", "dumbbell"]),
                    ui.input_radio_buttons("output_mode", "Output", ["single", "grouped", "both"]),
                    ui.input_text("plot_title", "Plot title", value="ERT Plot"),
                    ui.input_numeric("plot_width", "Plot Width (inches)", value=8, min=4, max=20, step=0.5),
                    ui.input_numeric("plot_height", "Plot Height (inches)", value=6, min=4, max=20, step=0.5),
                    ui.input_numeric("plot_dpi", "DPI", value=300, min=72, max=600, step=10),
                    ui.input_checkbox("show_median", "Show Median Line", value=True),
                    ui.input_checkbox("include_risktable", "Include Risk Table", value=True),
                    ui.input_action_button("generate_plots", "Generate"),
                ),
            ),
            ui.output_text_verbatim("plot_status"),
            ui.output_text_verbatim("plot_manifest"),
            ui.h3("Plot Preview"),
            ui.output_ui("plot_preview"),
            ui.h3("Export"),
            ui.input_text("export_dir", "Export Directory", value=""),
            ui.p("Enter the full path to the directory where plots and data will be exported.", style="font-size: 12px; color: gray;"),
            ui.input_action_button("browse_dir", "Browse for Directory"),
            ui.input_checkbox("create_subdir", "Create new subdirectory", value=True),
            ui.input_text("subdir_name", "Subdirectory name", value="ERT_Plots"),
            ui.input_action_button("export_plots", "Export Plots to Folder"),
            ui.output_text_verbatim("export_status"),
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
        if source_name == "None":
            return None
        if source_name == "Translated Residence Charts" and residence_chart_data() is not None:
            return residence_chart_data()

        uploaded_files = input.fishbase_input()
        if uploaded_files:
            return _read_dataframe_from_path(uploaded_files[0]["datapath"])

        return None

    def _resolve_visualization_data():
        source_name = input.plot_data_source()
        if source_name == "None":
            return None
        if source_name == "Fishbase lookup" and fishbase_lookup_data() is not None:
            return fishbase_lookup_data()
        if source_name == "Translated Residence Charts" and residence_chart_data() is not None:
            return residence_chart_data()

        uploaded_files = input.visualization_input()
        if uploaded_files:
            return _read_dataframe_from_path(uploaded_files[0]["datapath"])

        return None

    @reactive.effect
    @reactive.event(input.visualization_input, input.plot_data_source, residence_chart_data, fishbase_lookup_data)
    def _update_column_choices():
        """Update group_by, time_var, and status_var choices based on
        the currently resolved visualization data.

        Triggered when a new file is uploaded or the data source selection
        changes, so that the column dropdowns are always in sync with the
        currently available data."""
        data = _resolve_visualization_data()

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
    @reactive.event(input.fishbase_input, input.fishbase_data_source, residence_chart_data)
    def _update_species_col_choices():
        """Update the species column dropdown choices based on
        the currently resolved fishbase data.

        Triggered when a new file is uploaded or the data source
        selection changes, so that the column dropdown is always
        in sync with the available data."""
        data = _resolve_fishbase_data()

        if data is None or not hasattr(data, "columns"):
            ui.update_select(
                session, "species_col", choices=[], selected=None,
            )
            return

        columns = list(data.columns)

        # Pick a sensible default: prefer "Scientific Name", then "Species", etc.
        default_col = None
        for candidate in ["Scientific Name", "Species", "Sci_name", "scientificName"]:
            if candidate in columns:
                default_col = candidate
                break
        if default_col is None:
            default_col = columns[0]

        ui.update_select(
            session, "species_col", choices=columns, selected=default_col,
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

        # Validate file format
        if not path.lower().endswith((".xlsx", ".xls")):
            residence_chart_data.set(None)
            generated_status_state.set("Please upload an Excel file (.xlsx or .xls).")
            return

        # Also get the sheet index file if uploaded
        index_files = input.index_input()
        index_path = index_files[0]["datapath"] if index_files else None

        try:
            analysis = load_workbook(path, sheet_index_path=index_path)
            residence_chart_data.set(analysis.raw_df)
            generated_status_state.set("Workbook loaded and prepared for downstream analysis.")

            # Validate that the loaded data has required columns for downstream analysis
            required_cols = ["yearfrac", "status"]
            missing_cols = [c for c in required_cols if c not in analysis.raw_df.columns]
            if missing_cols:
                generated_status_state.set(
                    f"Warning: Loaded data is missing required columns: {missing_cols}. "
                    f"Plotting and fishbase lookup may not work correctly."
                )
        except Exception as exc:
            residence_chart_data.set(None)
            generated_status_state.set(f"Workbook load failed: {exc}")

    @output
    @render.text
    def load_status():
        return generated_status_state() if generated_status_state() is not None else "Workbook not loaded."

    @output
    @render.text
    def generated_status():
        """Display the generated status (e.g. row count after parsing)."""
        data = residence_chart_data()
        if data is None:
            return ""
        if hasattr(data, "shape"):
            return f"Generated {data.shape[0]} row(s) x {data.shape[1]} column(s)."
        return ""

    @reactive.effect
    @reactive.event(input.run_species)
    def _run_species():
        data = _resolve_fishbase_data()
        if data is None:
            fishbase_lookup_data.set(None)
            fishbase_status_state.set("No data available for fishbase lookup.")
            return

        species_col = input.species_col()
        if species_col is not None and species_col not in data.columns:
            fishbase_status_state.set(f"Species column '{species_col}' not found in data.")
            return

        try:
            result = run_fishbase(
                data,
                species_col=species_col,
                lookup_source=input.lookup_source(),
            )

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
    @reactive.event(input.export_fishbase_summary)
    def _export_fishbase_summary():
        """Export a summary table (1 record per unique scientific name) as Excel."""
        data = fishbase_lookup_data()
        if data is None:
            fishbase_export_status_state.set("No fishbase data available to export.")
            return

        target_dir = input.export_dir()
        if not target_dir or not os.path.isdir(target_dir):
            fishbase_export_status_state.set("Please specify a valid export directory.")
            return

        # Determine the species column for grouping
        species_col = input.species_col()
        if species_col is None or species_col == "" or species_col not in data.columns:
            # Try to find a species column
            for candidate in ["Scientific Name", "Species", "Sci_name", "scientificName"]:
                if candidate in data.columns:
                    species_col = candidate
                    break
            if species_col is None:
                fishbase_export_status_state.set("Could not determine the species column for summary.")
                return

        # Create summary: 1 record per unique scientific name
        summary_df = data.groupby(species_col, dropna=False).first().reset_index()

        result = run_export_data(
            dataframes={"fishbase_summary": summary_df},
            target_dir=target_dir,
            formats=["excel"],
        )

        fishbase_export_status_state.set(result["report"])

    @reactive.effect
    @reactive.event(input.export_fishbase_joined)
    def _export_fishbase_joined():
        """Export the full joined table (user data + fishbase data) as Excel."""
        data = fishbase_lookup_data()
        if data is None:
            fishbase_export_status_state.set("No fishbase data available to export.")
            return

        target_dir = input.export_dir()
        if not target_dir or not os.path.isdir(target_dir):
            fishbase_export_status_state.set("Please specify a valid export directory.")
            return

        result = run_export_data(
            dataframes={"fishbase_joined": data},
            target_dir=target_dir,
            formats=["excel"],
        )

        fishbase_export_status_state.set(result["report"])

    @reactive.effect
    @reactive.event(input.generate_plots)
    def _generate_plots():
        data = _resolve_visualization_data()
        if data is None:
            plot_manifest_state.set({"error": "No data available for plotting."})
            return

        # Validate required columns for survival analysis
        required_cols = ["yearfrac", "status"]
        missing_cols = [c for c in required_cols if c not in data.columns]
        if missing_cols:
            plot_manifest_state.set({"error": f"Data is missing required columns: {missing_cols}. Please ensure your data has 'yearfrac' and 'status' columns."})
            return

        csv_path = _write_dataframe_to_csv(data)
        output_dir = tempfile.mkdtemp(prefix="ert_plots_")
        options = {
            "plot_type": input.plot_type(),
            "output_mode": input.output_mode(),
            "group_by": input.group_by(),
            "mapping": {
                "group_var": input.group_by(),
                "time_var": input.time_var(),
                "status_var": input.status_var(),
            },
            "title": input.plot_title(),
            "output_directory": output_dir,
            "show_median": input.show_median(),
            "include_risktable": input.include_risktable(),
            "width": input.plot_width(),
            "height": input.plot_height(),
            "dpi": input.plot_dpi(),
            "output_file": None,
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

    @output
    @render.ui
    def plot_preview():
        """Display generated plots as images in the app using data URIs."""
        manifest = plot_manifest_state()
        if not manifest or "error" in manifest:
            return ui.p("No plots to display.")

        plot_files = manifest.get("plots", [])
        if not plot_files:
            return ui.p("No plots to display.")

        # Build image tags for each plot file using data URIs
        image_tags = []
        for plot_file in plot_files:
            if os.path.exists(plot_file):
                filename = os.path.basename(plot_file)
                try:
                    with open(plot_file, "rb") as img_file:
                        encoded = base64.b64encode(img_file.read()).decode("utf-8")
                    ext = os.path.splitext(plot_file)[1].lower()
                    mime_type = "image/png" if ext == ".png" else "image/jpeg" if ext in (".jpg", ".jpeg") else "application/octet-stream"
                    data_uri = f"data:{mime_type};base64,{encoded}"
                    image_tags.append(
                        ui.tags.div(
                            ui.tags.h4(filename),
                            ui.tags.img(src=data_uri, style="max-width: 100%; height: auto;"),
                            ui.tags.hr(),
                        )
                    )
                except Exception:
                    image_tags.append(
                        ui.tags.div(
                            ui.tags.h4(filename),
                            ui.tags.p("Unable to load image."),
                            ui.tags.hr(),
                        )
                    )

        if not image_tags:
            return ui.p("Plot files not found on disk.")

        return ui.tags.div(*image_tags)

    @reactive.effect
    @reactive.event(input.browse_dir)
    def _browse_directory():
        """Handle the 'Browse for Directory' button.

        Since we are using only Python and R (no JavaScript), we show
        a notification to the user explaining how to specify a directory
        path. The user enters the path manually in the text input above.
        """
        ui.notification_show(
            "Please enter the full path to your export directory in the text box above. "
            "On Windows, use backslashes (e.g., C:\\Users\\name\\Documents). "
            "On Mac/Linux, use forward slashes (e.g., /Users/name/Documents).",
            duration=10,
            type="message",
        )

    @reactive.effect
    @reactive.event(input.export_plots)
    def _export_plots():
        """Export generated plots to the user-selected directory."""
        manifest = plot_manifest_state()
        if not manifest or "error" in manifest:
            export_status_state.set("No plots to export.")
            return

        target_dir = input.export_dir()
        if not target_dir or not os.path.isdir(target_dir):
            export_status_state.set("Please specify a valid export directory.")
            return

        # Use the export controller to handle the export
        result = run_export_plots(
            plot_manifest=manifest,
            target_dir=target_dir,
            create_subdir=input.create_subdir(),
            subdir_name=input.subdir_name(),
        )

        # Update shared output directory so other tabs can use it
        shared_output_dir.set(result["metadata"]["target_dir"])

        export_status_state.set(result["report"])

    @output
    @render.text
    def export_status():
        return export_status_state() if export_status_state() is not None else ""

    @output
    @render.text
    def fishbase_export_status():
        return fishbase_export_status_state() if fishbase_export_status_state() is not None else ""

    @output
    @render.text
    def shared_output_info():
        """Display the shared output directory from plot exports."""
        dir_path = shared_output_dir()
        if dir_path:
            return f"Plots exported to: {dir_path}"
        return ""


app = App(app_ui, server)
