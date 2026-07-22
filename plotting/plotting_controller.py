#Controller for Kaplan Meier plots, dumbbell plots, and some summary statistics?

from plotting.plotter import create_plot
from plotting.plotter import create_plot_set

from plotting.summaries import summarize_data


def run_plot(
        df,
        group_by,
        x,
        y,
        output_mode
):

    summary = summarize_data(
        df,
        group_by,
        y
    )


    if output_mode == "single":

        plots = create_plot(
            df,
            x,
            y
        )


    elif output_mode == "multiple":

        plots = create_plot_set(
            df,
            group_by,
            x,
            y
        )


    elif output_mode == "both":

        plots = {
            "combined": create_plot(df, x, y),
            "groups": create_plot_set(
                df,
                group_by,
                x,
                y
            )
        }


    return {
        "summary": summary,
        "plots": plots
    }
  
