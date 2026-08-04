library(jsonlite)
library(dplyr)
library(rfishbase)

############################################################
# fishbase_workflow.R
#
# Master R FishBase Workflow
#
# Called from:
#     controller/fishbase_controller.py
#
# Arguments:
#     args[1] = input CSV file path
#     args[2] = manifest JSON output path
#     args[3] = species column name (optional, auto-detected if not provided)
#     args[4] = database source: "FishBase" or "SeaLifeBase" (optional, defaults to "FishBase")
#
# Produces:
#     A manifest JSON with:
#       - output_dataframe: path to the output CSV
#       - report: summary text
#       - metadata: workflow metadata
############################################################

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
    stop("Expected input_file and manifest_file as arguments.")
}

input_file <- args[1]
manifest_file <- args[2]
species_col_arg <- if (length(args) >= 3) args[3] else NULL
db_source <- if (length(args) >= 4) args[4] else "FishBase"

if (!file.exists(input_file)) {
    stop(paste("Input file not found:", input_file))
}

# Read input dataframe
df <- read.csv(input_file, stringsAsFactors = FALSE)

# Source helper functions
source("rfishbase/ecology.R")
source("rfishbase/diet.R")
source("rfishbase/fooditems.R")

# Determine the species column name
# Priority: explicit argument > known column names > first column
# Recognizes: "Species", "Sci_name", "scientificName", "Scientific Name"
if (!is.null(species_col_arg) && species_col_arg %in% names(df)) {
    species_col <- species_col_arg
} else {
    species_col <- if ("Species" %in% names(df)) "Species" else
                   if ("Sci_name" %in% names(df)) "Sci_name" else
                   if ("scientificName" %in% names(df)) "scientificName" else
                   if ("Scientific Name" %in% names(df)) "Scientific Name" else
                   names(df)[1]
}

# Set the rfishbase server based on the database source
if (db_source == "SeaLifeBase") {
    # SeaLifeBase uses a different server; rfishbase supports this via
    # the 'server' argument in load_taxa() and other functions
    fb_server <- "sealifebase"
} else {
    fb_server <- "fishbase"
}

# Get unique species names
species_list <- unique(df[[species_col]])
species_list <- species_list[!is.na(species_list)]

report_lines <- c()

# Look up taxonomy for each species
taxa_data <- tryCatch({
    load_taxa(server = fb_server)
}, error = function(e) {
    report_lines <- c(report_lines, paste("Warning: load_taxa failed:", e$message))
    NULL
})

if (!is.null(taxa_data)) {
    fish_taxonomy <- taxa_data %>%
        filter(Species %in% species_list) %>%
        select(Species, Family, Order, Class, Genus)
} else {
    fish_taxonomy <- data.frame(
        Species = species_list,
        Family = NA,
        Order = NA,
        Class = NA,
        Genus = NA
    )
}

# Look up ecology data
ecology_summary <- tryCatch({
    rfishbase_ecology(df = data.frame(Sci_name = species_list), server = fb_server)
}, error = function(e) {
    report_lines <- c(report_lines, paste("Warning: ecology lookup failed:", e$message))
    NULL
})

# Look up diet data
diet_combined <- tryCatch({
    rfishbase_diet(df = data.frame(Sci_name = species_list), server = fb_server)
}, error = function(e) {
    report_lines <- c(report_lines, paste("Warning: diet lookup failed:", e$message))
    NULL
})

# Look up food items data
fooditems_combined <- tryCatch({
    rfishbase_fooditems(df = data.frame(Sci_name = species_list), server = fb_server)
}, error = function(e) {
    report_lines <- c(report_lines, paste("Warning: fooditems lookup failed:", e$message))
    NULL
})

# Join all data together
result_df <- df

# Join taxonomy
if (nrow(fish_taxonomy) > 0) {
    result_df <- result_df %>%
        left_join(fish_taxonomy, by = c(species_col = "Species"))
}

# Join ecology
if (!is.null(ecology_summary) && nrow(ecology_summary) > 0) {
    result_df <- result_df %>%
        left_join(ecology_summary, by = c(species_col = "Sci_name"))
}

# Join diet
if (!is.null(diet_combined) && nrow(diet_combined) > 0) {
    result_df <- result_df %>%
        left_join(diet_combined, by = c(species_col = "Sci_name"))
}

# Join fooditems
if (!is.null(fooditems_combined) && nrow(fooditems_combined) > 0) {
    result_df <- result_df %>%
        left_join(fooditems_combined, by = c(species_col = "Sci_name"))
}

# Write output dataframe
output_dir <- file.path(dirname(manifest_file), "fishbase_output")
if (!dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
}

output_csv <- file.path(output_dir, "fishbase_output.csv")
write.csv(result_df, output_csv, row.names = FALSE)

# Build report
report <- paste(
    paste0("FishBase lookup complete for ", nrow(result_df), " records."),
    paste0("Species looked up: ", length(species_list)),
    paste(report_lines, collapse = "\n"),
    sep = "\n"
)

# Write manifest
manifest <- list(
    workflow = "fishbase_lookup",
    input_file = input_file,
    output_dataframe = output_csv,
    report = report,
    metadata = list(
        species_count = length(species_list),
        record_count = nrow(result_df),
        columns = names(result_df),
        database_source = db_source,
        species_column = species_col
    )
)

write_json(manifest, manifest_file, pretty = TRUE, auto_unbox = TRUE)

cat("FishBase workflow complete.\n")
cat("Output written to:", output_csv, "\n")
