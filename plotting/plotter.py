#Plotter for kaplan meier plots

def create_plot(df, x, y):

    # create one figure

    return figure



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
