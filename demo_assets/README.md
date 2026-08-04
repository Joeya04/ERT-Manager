# Demo Assets

This directory contains archival scripts, demo data, and reference materials for the ERT-Manager application.

## Contents

- **`ERT_date_puller.py`** — Original standalone Python script for parsing color-coded ERT workbooks. This was the predecessor to `formatter/ERT_date_puller_shiny.py` and is kept here for reference. It has hardcoded file paths and is not used by the Shiny app.

- **`plotting/`** — Original R plotting scripts (`basic_plots.R`, `plot_grouping.R`). These functions were inlined into `rfishbase/plotting_workflow.R` and are kept here for reference.

- **`plotter.py`** — Demo script showing how to use the `plotting_controller.run_plot()` function programmatically (outside of the Shiny app).

- **`Demo_data.xlsx`** — Sample ERT workbook data for testing the parser.

## Purpose

These files are archival/reference materials. They are not imported or used by the main Shiny application (`app.py`). They can be copied elsewhere and ultimately removed from the repository once the team has reviewed and archived them.
