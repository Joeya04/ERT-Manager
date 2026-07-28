# App interface for the Shiny app (in Python)

import json
import os
import tempfile

from shiny import App, reactive, render, ui

from controller.plotting_controller import run_plot
from controller.workflow_controller import run_analysis


app_ui = ui.page_navbar(
    ui.panel_title("Enclosure Residence Time Calculator"),
    ui.nav_panel(
        "Enclosure Residence Time Calculator Overview",
        ui.h2("Generating a Species Table"),
        ui.p(
            "Species residence tables are an important step toward determining the overall residency time for a given tank or enclosure."
            " They are created by using census counts for the target tank/enclosure over the study duration with addition and mortality records to determine the total number of unique individuals and their approximate residence times in that enclosure"
        ),
        ui.p("Enclosure residence time analysis requires data on study organisms to be structured so that each individual"
                          "creature is assigned an enclosure entrance date and exit date.  These dates may be exact or estimated based on "
                          "available records and associated data quality.  In the absence of comprehensive records and/or in the case of "
                          "group-managed organisms, adopting certain assumptions uniformly to generate estimated entrance and exit dates "
                          "is recommended."
                          "Organizational tools, such as the enclosure residence diagram below can help investigators reconstruct "
                          "actual and/or estimated enclosure entrance and exit dates at the individual organism level when population records "
                          "are spread across multiple repositories or complicated by inconsistent data management practices."
                 #Needs python translated Figure caption
                 # img(src = "FIGURE2.jpg", height = 400, width = 750),
                 "In the diagram above, each column represents an individual organism, while each row is a year with corresponding annual census values. "
                          "Entrance dates are assigned in chronological order, and estimated or actual exit dates are matched up with individual organisms "
                          "based on a first-in, first-out assumption, unless individually tracked animals already have confirmed entrance and exit dates. "
                          "Estimated entrance or exit dates can then be cross-referenced with annual census values to ensure population numbers match."
        ),
#blank spacer here before next heading
        ui.h4("Preparing Data for Upload and Analysis:"),               
                 ui.p("Once enclosure residence time for each organism is determined and entrance and exit dates are assigned to each individual, "
                          "the data should be organized as shown in the example below for uploading to the Enclosure Residence Time Calculator "
                 ),
                 #img(src = "ERT_Example_Dataframe.jpg", height = 337, width = 574), insert second image from mike's script
                 ui.p("Once your input data is structured as outlined above, it can be uploaded via the side panel (starting with Step 1). "
                        "After uploading your data file, follow the subsequent steps to instruct the calculator which data column in your file represents "
                          "the residence time for each organism (Step 2), and the censorship status (Step 3). Once steps 1-3 are completed, a summary of the "
                          "uploaded data will appear below to verify the calculator in interpreting the file correctly. If everything appears correct, explore your data "
                          "using the tabs on the right. "
                 ),

        ui.p("Disclaimer: We do not warrant that the service provided by the Enclosure Residence Time Calculator "
               "will be uninterrupted, error-free, or secure. Your data when using this calculator is "
               "stored and backed up on local and/or cloud storage. We have no liabiliity for any loss "
               "or misappropriation of your data under any circumstances."),
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
        )
        ),

        ui.h2("Overview"),
        ui.p("The number of unique individuals in a given tank or enclosure is determined by using census counts for the target tank/enclosure over the study duration in tandem with addition and mortality records. "
        " Creating residence charts can be first step toward visualizing complex datasets containing multiple record sources. Each table represents a single species, with each column representing a unique individual. "
        " Formatted charts can be translated inside of this tool by following the formatting rules below. " 
        ),


        ui.h2("Steps to Generate Species Residence Tables"),
        ui.p("Introduction dates are delineated with a green (hex code here?) cell with the corresponding date. "
        "Each departure dates delineated with red colored cells (Hex Code Here?) containing the departure or death date. "
        "Each row represents a timestep, such as years, and surivival of an individual to the next timestep is indicated by a green cell. "
        ),

    ),
    ui.nav_panel(
        "Fishbase Lookup",
        ui.h2("Using fishbase data"),
        ui.input_select("lookup_source", "Database", ["FishBase", "SeaLifeBase"]),
        ui.input_action_button("run_species", "Run Lookup"),
        ui.output_text_verbatim("species_status"),
    ),
    ui.nav_panel(
        "Visualization",
        ui.h2("Visualization"),
        ui.input_select("group_by", "Group By", ["Order", "Family", "trophic_classs",]),
        ui.input_text("time_var", "Time column", value="time"),
        ui.input_text("status_var", "Status column", value="status"),
        ui.input_select("plot_type", "Plot Type", ["survival", "dumbbell"]),
        ui.input_radio_buttons("output_mode", "Output", ["single", "grouped", "both"]),
        ui.input_text("plot_title", "Plot title", value="ERT Plot"),
        ui.input_action_button("generate_plots", "Generate"),
        ui.output_text_verbatim("plot_status"),
        ui.output_text_verbatim("plot_manifest"),
    )
)


def server(input, output, session):
    def _write_dataframe_to_csv(df):
        temp_dir = tempfile.mkdtemp(prefix="ert_app_", dir=tempfile.gettempdir())
        csv_path = os.path.join(temp_dir, "plot_input.csv")

        if hasattr(df, "to_csv"):
            df.to_csv(csv_path, index=False)
        else:
            with open(csv_path, "w", encoding="utf-8") as handle:
                handle.write(str(df))

        return csv_path

    @reactive.effect
    @reactive.event(input.load_workbook)
    def _load_workbook():
        uploaded_files = input.ert_input()
        if not uploaded_files:
            return

        path = uploaded_files[0]["datapath"]
        workbook_path.set(path)

        try:
            analysis = run_analysis(path)
            formatted_df.set(analysis.get("data"))
            statistics.set(analysis.get("statistics", {}))
        except Exception as exc:
            formatted_df.set(None)
            statistics.set({"error": str(exc)})

    @output
    @render.text
    def load_status():
        if formatted_df() is None:
            return "Workbook not loaded."
        return "Workbook loaded and ready for plotting."

    @reactive.effect
    @reactive.event(input.run_species)
    def _run_species():
        data = formatted_df() if formatted_df() is not None else raw_df()
        if data is None:
            return
        matched_df.set(data)

    @reactive.effect
    @reactive.event(input.generate_plots)
    def _generate_plots():
        data = formatted_df() if formatted_df() is not None else raw_df()
        if data is None:
            plot_manifest.set({"error": "No data loaded for plotting."})
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
            plot_manifest.set(manifest)
        except Exception as exc:
            plot_manifest.set({"error": str(exc)})

    @output
    @render.text
    def plot_status():
        manifest = plot_manifest()
        if not manifest:
            return "No plot generated yet."
        if "error" in manifest:
            return manifest["error"]
        return f"Generated {manifest.get('number_of_plots', 0)} plot(s)."

    @output
    @render.text
    def plot_manifest():
        manifest = plot_manifest()
        if not manifest:
            return ""
        return json.dumps(manifest, indent=2)


# Reactive storage
workbook_path = reactive.Value(None)
raw_df = reactive.Value(None)
formatted_df = reactive.Value(None)
matched_df = reactive.Value(None)
statistics = reactive.Value(None)
plot_manifest = reactive.Value({})

summary_tables = reactive.Value(None)

plots = reactive.Value(None)

validation_report = reactive.Value(None)

app = App(app_ui, server)