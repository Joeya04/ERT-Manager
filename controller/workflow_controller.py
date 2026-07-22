#Controls workflow of all modules needed for the app
from formatter.ERT_date_puller_shiny import parse_ert_workbook #MODULES FROM DATE PULLER

from rfishbase.fishbase_lookup import run_fishbase

from plotting.plots import create_plot_set

from shiny import App, ui, reactive, render, req

ert_input = input.sheet_index()[0].datapath
index_input = input.sheet_index()[0].datapath

df = parse_ert_workbook(ert_input, index_input)



ui.page_fluid(
    ui.h2("ERT Workflow App"),
    ui.input_file("ert_workbook", "Upload ERT workbook", accept=[".xlsx"]),
    ui.input_file("sheet_index", "Upload sheet index", accept=[".xlsx"]),
    ui.input_select("species_filter", "Species", choices=["All", "SpeciesA", "SpeciesB"]),
    ui.input_action_button("run_parser", "Run parser"),
    ui.output_table("parsed_results"),
    ui.output_text("workflow_status"),
    ui.download_button("download_excel", "Download parsed data"),
)
