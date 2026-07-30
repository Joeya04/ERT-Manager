############################################################
# plot_exporter.py
############################################################

import shutil
from pathlib import Path


def copy_selected_plots(

        manifest,

        output_directory

):

    exported = []

    plots_folder = Path(

        output_directory

    ) / "Plots"

    plots_folder.mkdir(

        exist_ok=True

    )

    for plot in manifest["plots"]:

        source = Path(

            plot["file"]

        )

        destination = plots_folder / source.name

        shutil.copy2(

            source,

            destination

        )

        exported.append(

            str(destination)

        )

    return exported