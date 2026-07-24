#App interface for the shiiny app (in Python)

from shiny import App, ui, reactive, render, req

from controller.plotting_controller import run_plot

from controller.workflow_controller import run_analysis


app.ui = ui.page_navbar(

    ui.nav.panel(
        "ERT Project Overview",
        ui.h2("Generating a Species Table")

        ui.p("Species residence tables are an important step toward determining the overall residency time for an individual in a given tank or enclosure."
        " They are created by using census counts for the target tank/enclosure over the study duration with addition and mortality records to determine the total number of unique individuals and their approximate residence times in that enclosure")

        ui.h3("How to Organize your data")

        ui.p("Enclosure residence time analysis requires data on study organisms to be structured so that each individual"
                          "creature is assigned an enclosure entrance date and exit date.  These dates may be exact or estimated based on"
                          "available records and associated data quality.  In the absence of comprehensive records and/or in the case of "
                          "group-managed organisms, adopting certain assumptions uniformly to generate estimated entrance and exit dates"
                          "is recommended.")
    

        ui.p("Organizational tools, such as the enclosure residence diagram below can help investigators reconstruct
                          "actual and/or estimated enclosure entrance and exit dates at the individual organism level when population records"
                          "are spread across multiple repositories or complicated by inconsistent data management practices.")),

#input nav panel for ERT workbook and sheet index upload
    ui.nav.panel(
        "Generating Species Residence Tables",
        ui.h2("Overview"),

        ui.input_file("ert_input", "Upload ERT Workbook Table"),

        ui.input_file("index_input", "Upload Sheet Index Table"),

        ui.input_action_button(
            "load_workbook",
            "Load Workbook"
        ),

        ui.output_text_verbatim("load_status")
    ),

#fishbase lookup panel
    ui.nav_panel(

        "Fishbase Lookup",

        ui.h2("Using fishbase data"),

        ui.input_select(

            "lookup_source",

            "Database",

            [

                "FishBase",

                "SeaLifeBase"

            ]

        ),

        ui.input_action_button(

            "run_species",

            "Run Lookup"

        ),

        ui.output_text_verbatim("species_status")

    ),

#plotting navpanel 

    ui.nav_panel(

        "Visualization",

        ui.h2("Visualization"),

        ui.input_select(

            "group_by",

            "Group By",

            [

                "None",

                "Site",

                "Species",

                "Year"

            ]

        ),

        ui.input_select(

            "x",

            "X",

            ["Placeholder"]

        ),

        ui.input_select(

            "y",

            "Y",

            ["Placeholder"]

        ),

        ui.input_select(

            "plot_type",

            "Plot Type",

            [

                "Scatter",

                "Boxplot",

                "Histogram"

            ]

        ),

        ui.input_radio_buttons(

            "output_mode",

            "Output",

            [

                "Single",

                "Multiple",

                "Both"

            ]

        ),

        ui.input_action_button(

            "generate_plots",

            "Generate"

        ),

        ui.output_plot("preview_plot")

    ),
)

def server(input, output, session):

    #loads workbook and sets reactive values for the raw dataframe and the workbook path
    @reactive.effect
    @reactive.effect(input.load_workbook)

    def _():

        path = input.input_file()[0]["datapath"]

        workbook_path.set(path)

        raw_df.set(

            load_workbook(path)

        )

#Checks to see if workbook is loaded
    @output
    @render.text

    def load_status():

        if raw_df() is None:

            return "Workbook not loaded."

        return "Workbook loaded."

#Runs ERT parser to created a validated table
    @reactive.effect
    @reactive.event(input.run_analysis)

    def _():

        df, report = run_analysis(

            raw_df()

        )

        formatted_df.set(df)

        validation_report.set(report)

    @reactive.effect
    @reactive.event(input.run_species)

    def _():

        matched_df.set(

            #DUMMY FISHBASE MODULE(

                formatted_df(),

                source=input.lookup_source()

            )



        )
##############################################################
# Reactive storage
#
# Every page has access to these.
##############################################################

workbook_path = reactive.Value(None)

raw_df = reactive.Value(None)

formatted_df = reactive.Value(None)

matched_df = reactive.Value(None)

statistics = reactive.Value(None)

summary_tables = reactive.Value(None)

plots = reactive.Value(None)

validation_report = reactive.Value(None)

##############################################################
# Server
##############################################################

def server(input, output, session):

    ###########################################################
    # Load Workbook
    ###########################################################

    @reactive.effect
    @reactive.event(input.load_workbook)

    def _():

        path = input.input_file()[0]["datapath"]

        workbook_path.set(path)

        raw_df.set(

            load_workbook(path)

        )

    ###########################################################
    # Status
    ###########################################################

    @output
    @render.text

    def load_status():

        if raw_df() is None:

            return "Workbook not loaded."

        return "Workbook loaded."

    ###########################################################
    # Validation
    ###########################################################

    @reactive.effect
    @reactive.event(input.run_validation)

    def _():

        df, report = format_workbook(

            raw_df()

        )

        formatted_df.set(df)

        validation_report.set(report)

    ###########################################################
    # Species Lookup
    ###########################################################

    @reactive.effect
    @reactive.event(input.run_species)

    def _():

        matched_df.set(

            run_species_lookup(

                formatted_df(),

                source=input.lookup_source()

            )

        )

    ###########################################################
    # Statistics
    ###########################################################

    @reactive.effect
    @reactive.event(input.run_statistics)

    def _():

        statistics.set(

            run_statistics(

                matched_df(),

                response=input.response(),

                factor=input.factor(),

                test=input.test()

            )

        )

    ###########################################################
    # Summaries
    ###########################################################

    @reactive.effect
    @reactive.event(input.generate_plots)

    def _():

        summary_tables.set(

            generate_summary(

                matched_df(),

                group_by=input.group_by()

            )

        )

    ###########################################################
    # Plots
    ###########################################################

    @reactive.effect
    @reactive.event(input.generate_plots)

    def _():

        plots.set(

            generate_plots(

                df=matched_df(),

                group_by=input.group_by(),

                x=input.x(),

                y=input.y(),

                plot_type=input.plot_type(),

                output_mode=input.output_mode()

            )

        )

    ###########################################################
    # Preview
    ###########################################################

    @output
    @render.plot

    def preview_plot():

        if plots() is None:

            return None

        #
        # If multiple plots exist
        #
        # Show first plot only
        #

        if isinstance(plots(), dict):

            return list(plots().values())[0]

        return plots()

    ###########################################################
    # Export
    ###########################################################

    @reactive.effect
    @reactive.event(input.export)

    def _():

        export_excel(

            matched_df(),

            statistics(),

            summary_tables(),

            plots()

        )

##############################################################
# Create App
##############################################################

app = App(app_ui, server)
