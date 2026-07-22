#Controls workflow of all modules needed for the app
from formatter.ERT_date_puller_shiny import parse_ert_workbook #MODULES FROM DATE PULLER

from formatter.statistics import run_statistics

from rfishbase.fishbase_lookup import run_fishbase

from plotting.plots import create_plot_set


df = parse_ert_workbook(ert_input, index_input)



def run_analysis(filepath):

    # Step 1
    df = parse_ert_workbook(filepath)


    # Step 2
    df = run_fishbase(df)


    # Step 3
    stats = run_statistics(df)


    return {
        "data": df,
        "statistics": stats
    }

