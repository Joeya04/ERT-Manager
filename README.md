# ERT-Manager

**Enclosure Residence Time Calculator** — A Shiny for Python application that converts color-coded life tables into individual records of approximate residence time or lifespan. Matches species names with their respective entries in FishBase/SeaLifeBase and returns ecology and diet characteristics. Generates Kaplan-Meier survival curves and median dumbbell plots with summary statistics.

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
│   ├── rscript_utils.py            # Rscript resolution, path normalization, package management
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
├── rfishbase/                      # R scripts for FishBase & plotting workflows
│   ├── fishbase_workflow.R         # Master FishBase lookup workflow
│   ├── fishbase_lookup.R           # Species matching functions
│   ├── ecology.R                   # Ecology data lookup
│   ├── diet.R                      # Diet data lookup
│   ├── fooditems.R                 # Food items lookup
│   ├── plotting_workflow.R         # Master plotting workflow (inlined functions)
│   └── requirements.R              # R package dependencies
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

## Inputs and Outputs

### Inputs

The app accepts the following inputs across its tabs:

#### Species Residence Tables Tab
| Input | Type | Description |
|-------|------|-------------|
| ERT Workbook Table | File upload (.csv, .xlsx, .xls) | Color-coded Excel workbook with residence charts. Green cells = entry, red cells = departure, blue cells = still alive. |
| Sheet Index Table | File upload (.csv, .xlsx, .xls) | Excel/CSV file mapping species sheet names to their start rows. Must contain `Species` and `Start Row` columns. |

#### Fishbase Lookup Tool Tab
| Input | Type | Description |
|-------|------|-------------|
| Data Source | Dropdown | `Translated Residence Charts`, `Uploaded data`, or `None` |
| Upload Data | File upload (.csv, .xlsx, .xls) | Optional: upload a separate data file for lookup |
| Database | Dropdown | `FishBase` or `SeaLifeBase` |
| Scientific Name Column | Dropdown | Auto-populated from the selected data source |
| Export Directory | Text input | Full path to directory for Excel exports |

#### Visualization Tab
| Input | Type | Description |
|-------|------|-------------|
| Data Source | Dropdown | `Translated Residence Charts`, `Fishbase lookup`, `Uploaded data`, or `None` |
| Upload Data | File upload (.csv, .xlsx, .xls) | Optional: upload a separate data file for plotting |
| Group By | Multi-select | One or more columns to group plots by |
| Time column | Select | Column representing residence time (e.g., `yearfrac`) |
| Status column | Select | Column representing censorship status (0 = censored, 1 = uncensored) |
| Plot Type | Radio buttons | `Kaplan-Meier Survival` or `Median Dumbbell` |
| Output | Radio buttons | `Single Plot`, `Grouped Plots`, or `Both` |
| Subset Variable | Select | Optional column to subset data by |
| Subset Value | Select | Value to filter on (populated based on Subset Variable) |
| Subset Mode | Radio buttons | `Single Value` (filter to selected) or `Each Unique Value` (new plot per value) |
| Plot title | Text | Title for the plot(s) |
| Plot Width / Height | Numeric | Dimensions in inches (4–20) |
| DPI | Numeric | Resolution (72–600) |
| Show Median Line | Checkbox | Show median reference line (KM plots only) |
| Include Risk Table | Checkbox | Include risk table (KM plots only) |
| Export Directory | Text input | Full path to directory for plot exports |
| Create new subdirectory | Checkbox | Create a subdirectory within the export directory |
| Subdirectory name | Text | Name for the subdirectory |

### Outputs

The app produces the following outputs:

#### Parsed Data (Species Residence Tables Tab)
- A `WorkflowState` object containing a `raw_df` DataFrame with columns: `Species`, `Individual`, `Intro_date`, `Exit_date`, `duration_days`, `yearfrac`, `status`, `red_census`, `green_census`.

#### FishBase Lookup Results (Fishbase Lookup Tool Tab)
- A joined DataFrame with original data + FishBase/SeaLifeBase columns: `Family`, `Order`, `Class`, `Genus`, ecology data, diet data, and food items data.
- Exportable as Excel (summary table: 1 record per unique scientific name; or full joined table).

#### Plots (Visualization Tab)
- **Kaplan-Meier Survival plots**: PNG files showing survival curves with confidence intervals, optional median reference lines, and optional risk tables.
- **Median Dumbbell plots**: PNG files showing median residence time per group as horizontal segments with points.
- A `plot_manifest.json` file containing metadata about generated plots (plot type, output mode, group_by, subset info, number of plots, file paths, and settings).
- Plots are displayed inline in the app via data URIs.

#### Exported Files
- **Plot exports**: PNG files copied to the user-specified directory (optionally in a subdirectory), along with a copy of the `plot_manifest.json`.
- **Data exports**: Excel files (`.xlsx`) containing raw data, formatted data, FishBase data, and/or statistics, depending on what has been generated.

### Plot Manifest Format

The `plot_manifest.json` file has the following structure:

```json
{
  "workflow": "plot_generation",
  "plot_type": "survival" | "dumbbell",
  "output_mode": "single" | "grouped" | "both",
  "group_by": ["column_name"] | null,
  "subset_var": "column_name" | null,
  "subset_value": "value" | null,
  "subset_mode": "single" | "each",
  "number_of_plots": 3,
  "plots": ["path/to/plot1.png", "path/to/plot2.png"],
  "output_directory": "/path/to/output",
  "settings": {
    "show_median": true,
    "include_risktable": true,
    "width": 8,
    "height": 6,
    "dpi": 300
  }
}
```

## Workflow Steps

1. **Generating Species Residence Tables**: Upload your ERT Workbook Table and Sheet Index Table, then click "Load Workbook". The parser reads color-coded cells (green = entry, red = departure, blue = still alive) and generates a table of individual residence times.

2. **Fishbase Lookup Tool**: Select a data source (Translated Residence Charts, Uploaded data, or None), choose a scientific name column, and click "Run Lookup". The tool queries FishBase or SeaLifeBase for taxonomy, ecology, diet, and food items data.

3. **Visualization**: Select a data source, choose grouping/time/status columns, configure plot options, and click "Generate". The tool creates Kaplan-Meier survival curves and/or median dumbbell plots.

4. **Export**: Export plots to a folder or export data tables to Excel.

## Known Issues & Fixes

### Dumbbell Plot Generation in Grouped Mode (Fixed)

**Problem**: When generating median dumbbell plots with `output_mode = "grouped"`, the app failed with:
```
Error in medians[, "median"] : incorrect number of dimensions
```

**Root Cause**: In grouped mode, `generate_grouped_plots()` filters the data to a single group value before calling the plot function. This produces a `survfit` object with only one stratum, causing `summary(fit)$table` to return a named numeric vector instead of a matrix. The code then attempted 2D matrix indexing (`medians[, "median"]`) on a 1D vector.

**Fix**: In `rfishbase/plotting_workflow.R`, `generate_median_dumbbell_plot()` now detects when `summary(fit)$table` is a vector (via `is.null(dim(medians))`) and converts it to a 1-row matrix with a proper group name before indexing. A guard was also added for the edge case where all medians are NA (survival never crosses 50%), which returns a placeholder plot instead of crashing.

## Disclaimer

We do not warrant that the service provided by the Enclosure Residence Time Calculator will be uninterrupted, error-free, or secure. Your data when using this calculator is stored and backed up on local and/or cloud storage. We have no liability for any loss or misappropriation of your data under any circumstances.
