from pathlib import Path
import re


def generate_grouped_plots(
        df,
        group_by,
        plot_function,
        output_directory,
        plot_name,
        **kwargs
):

    """
    Generate one plot per group.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe

    group_by : str
        Column used for grouping

    plot_function : function
        Plotting function to execute

    output_directory : str
        Folder where plots are saved

    plot_name : str
        Base name for output files

    kwargs :
        Additional plotting arguments

    Returns
    -------
    list of dictionaries
        Plot metadata for manifest
    """

    output_directory = Path(output_directory)

    output_directory.mkdir(
        exist_ok=True,
        parents=True
    )


    plot_outputs = []


    #
    # Determine groups
    #

    groups = sorted(
        df[group_by]
        .dropna()
        .unique()
    )


    #
    # Generate each plot
    #

    for group in groups:


        #
        # Filter dataframe
        #

        subset = df[
            df[group_by] == group
        ]


        #
        # Make safe filename
        #

        safe_group = re.sub(
            r"[^a-zA-Z0-9_-]",
            "_",
            str(group)
        )


        output_file = (
            output_directory /
            f"{plot_name}_{safe_group}.png"
        )


        #
        # Generate plot
        #

        plot_function(

            dataframe=subset,

            output_file=str(output_file),

            title=f"{plot_name}: {group}",

            **kwargs

        )


        #
        # Record output
        #

        plot_outputs.append(

            {

                "group": str(group),

                "file": str(output_file),

                "rows_used": len(subset)

            }

        )


    return plot_outputs