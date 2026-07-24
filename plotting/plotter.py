#Plotter for kaplan meier plots
from rfishbase.kmplots import build_plot

def create_plot(df, x, y):

    # Create the Kaplan-Meier plot using the build_plot function
    km_plot = build_plot(
        fit=df,
        title=f"Kaplan-Meier Plot: {y} vs {x}",
        show_median=True,
        include_risktable=True
    )

    return km_plot




def create_plot_set(df, group_by, x, y):

    plots = {}

    groups = df[group_by].unique()


    for group in groups:

        subset = df[df[group_by] == group]

        plots[group] = create_plot(
            subset,
            x,
            y
        )

    return plots

