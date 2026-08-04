# ERT-Manager

**Enclosure Residence Time Calculator** — A Shiny for Python application that converts color-coded life tables into individual records of approximate residence time or lifespan. Matches species names with their respective entries in FishBase/SeaLifeBase and returns ecology and diet characteristics. Generates Kaplan-Meier survival curves with summary statistics.

## Architecture

The app is built in **Shiny for Python** and orchestrates **R scripts** for data processing and visualization via `subprocess` calls.

### Project Structure

```
ERT-Manager/
├── app.py                          # Main Shiny app (UI + server)
├── README.md                       # This file
├── requirements.txt                # Python dependencies
├── ERT_App_Script_7-20-26.R        # Original R Shiny app (reference)
├── ERT_Translated.xlsx             # Sample output data
├── controller/                     # Python controllers (orchestrate R scripts)
│   ├── __init__.py
│   ├── workflow_controller.py      # Workbook loading & workflow orchestration
│   ├── fishbase_controller.py      # FishBase/SeaLifeBase lookup
│   ├── plotting_controller.py      # Kaplan-Meier & dumbbell plot generation
│   └── export_controller.py        # Export to Excel/CSV
├── models/                         # Data models
│   ├── __init__.py
│   └── workflow_state.py           # WorkflowState dataclass
├── formatter/                      # Data parsing
│   ├── __init__.py
│   └── ERT_date_puller_shiny.py    # ERT workbook parser (color-coded Excel)
├── export/                         # Export utilities
│   ├── __init__.py
│   ├── excel_exporter.py           # Excel workbook builder
│   └── plot_exporter.py            # Plot file exporter
├── rfishbase/                      # R scripts for FishBase workflow
│   ├── fishbase_workflow.R         # Master FishBase lookup workflow
│   ├── fishbase_lookup.R           # Species matching functions
│   ├── ecology.R                   # Ecology data lookup
│   ├── diet.R                      # Diet data lookup
│   ├── fooditems.R                 # Food items lookup
│   ├── plotting_workflow.R         # Master plotting workflow (inlined functions)
│   └── requirements.R              # R package dependencies
├── examples/                       # Example/demo scripts
│   └── plotter.py                  # Demo: using the plotting controller
├── demo_assets/                    # Demo data files
│   └── Demo_data.xlsx
└── .venv/                          # Python virtual environment
```

### Data Flow

1. **Workbook Upload** (Step 1): User uploads an ERT Workbook Table and Sheet Index Table. The `workflow_controller.load_workbook()` function calls `formatter.ERT_date_puller_shiny.parse_ert_workbook()` to parse color-coded Excel sheets into individual residence time records.

2. **FishBase Lookup** (Fishbase tab): User selects a data source and scientific name column, then clicks "Run Lookup". The `fishbase_controller.run_fishbase()` function invokes `rfishbase/fishbase_workflow.R` via `Rscript` to query FishBase/SeaLifeBase for taxonomy, ecology, diet, and food items data.

3. **Visualization** (Visualization tab): User selects a data source, grouping variable, time column, and status column, then clicks "Generate". The `plotting_controller.run_plot()` function invokes `rfishbase/plotting_workflow.R` via `Rscript` to generate Kaplan-Meier survival curves and/or median dumbbell plots.

4. **Export**: User can export plots to a folder (`export_controller.run_export_plots()`) or export data tables to Excel (`export_controller.run_export_data()`).

### State Management

The app uses two state management patterns:

- **Module-level `reactive.Value()` objects** (in `app.py`): Used for cross-tab UI state sharing. These include `residence_chart_data`, `fishbase_lookup_data`, `plot_manifest_state`, `shared_output_dir`, and various status values. Reactive values provide automatic reactivity for UI updates.

- **`WorkflowState` dataclass** (in `models/workflow_state.py`): Used as a return type from `load_workbook()`. Provides a structured data container for the workbook parsing pipeline. Not used for cross-tab state sharing.

## Dependencies

### Python
Install with: `pip install -r requirements.txt`

- `shiny` — Web framework
- `pandas` — Data manipulation
- `openpyxl` — Excel file reading

### R
Install with: `install.packages(c("jsonlite", "dplyr", "rfishbase", "survival", "ggsurvfit", "ggplot2", "readxl"))`

- `jsonlite` — JSON manifest reading/writing
- `dplyr` — Data manipulation
- `rfishbase` — FishBase/SeaLifeBase API access
- `survival` — Survival analysis (Kaplan-Meier)
- `ggsurvfit` — Survival curve plotting
- `ggplot2` — General plotting
- `readxl` — Excel file reading

## Running the App

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install R packages (in R)
install.packages(c("jsonlite", "dplyr", "rfishbase", "survival", "ggsurvfit", "ggplot2", "readxl"))

# Run the app
python app.py
```

## Workflow Steps

1. **Generating Species Residence Tables**: Upload your ERT Workbook Table and Sheet Index Table, then click "Load Workbook". The parser reads color-coded cells (green = entry, red = departure, blue = still alive) and generates a table of individual residence times.

2. **Fishbase Lookup Tool**: Select a data source (Translated Residence Charts, Uploaded data, or None), choose a scientific name column, and click "Run Lookup". The tool queries FishBase or SeaLifeBase for taxonomy, ecology, diet, and food items data.

3. **Visualization**: Select a data source, choose grouping/time/status columns, configure plot options, and click "Generate". The tool creates Kaplan-Meier survival curves and/or median dumbbell plots.

4. **Export**: Export plots to a folder or export data tables to Excel.

## Disclaimer

We do not warrant that the service provided by the Enclosure Residence Time Calculator will be uninterrupted, error-free, or secure. Your data when using this calculator is stored and backed up on local and/or cloud storage. We have no liability for any loss or misappropriation of your data under any circumstances.
