library(jsonlite)

source("plotting/basic_plots.R")
source("plotting/plot_grouping.R")

############################################################
# plot_workflow.R
#
# Master R Plot Workflow
#
# Called from:
#     plotting_controller.py
#
# Arguments:
#     args[1] = input CSV file path
#     args[2] = options JSON file path
#     args[3] = manifest JSON output path
############################################################

args <- commandArgs(trailingOnly = TRUE)

input_file <- args[1]
options_file <- args[2]
manifest_file <- args[3]

if (length(args) < 3) {
    stop("Expected input_file, options_file, and manifest_file as arguments.")
}

if (!file.exists(input_file)) {
    stop(paste("Input file not found:", input_file))
}

if (!file.exists(options_file)) {
    stop(paste("Options file not found:", options_file))
}

# Read dataframe
if (grepl("\\.csv$", input_file, ignore.case = TRUE)) {
    df <- read.csv(input_file, stringsAsFactors = FALSE)
} else {
    stop("Only CSV input is supported for the current plotting workflow.")
}

# Read plotting options
options <- fromJSON(options_file)

plot_registry <- list(
    survival = build_kmplots,
    dumbbell = build_median_dumbbell_plots
)

if (!(options$plot_type %in% names(plot_registry))) {
    stop("Unknown plot type.")
}

plot_function <- plot_registry[[options$plot_type]]

output_directory <- if (!is.null(options$output_directory)) options$output_directory else "output/plots"

# Extract optional formatting parameters
show_median <- if (!is.null(options$show_median)) options$show_median else TRUE
include_risktable <- if (!is.null(options$include_risktable)) options$include_risktable else TRUE
plot_width <- if (!is.null(options$width)) options$width else 8
plot_height <- if (!is.null(options$height)) options$height else 6
plot_dpi <- if (!is.null(options$dpi)) options$dpi else 300

# Determine whether grouping is requested
group_by <- options$group_by
has_grouping <- !is.null(group_by) && group_by != "None" && group_by != ""

if (options$output_mode == "single") {
    plot_files <- plot_function(
        dataframe = df,
        mapping = options$mapping,
        title = options$title,
        output_directory = output_directory,
        output_file = if (!is.null(options$output_file)) options$output_file else NULL,
        show_median = show_median,
        include_risktable = include_risktable,
        width = plot_width,
        height = plot_height,
        dpi = plot_dpi
    )
} else if (options$output_mode == "grouped") {
    if (has_grouping) {
        plot_files <- generate_grouped_plots(
            dataframe = df,
            group_by = group_by,
            plot_function = plot_function,
            mapping = options$mapping,
            title = options$title,
            output_directory = output_directory,
            show_median = show_median,
            include_risktable = include_risktable,
            width = plot_width,
            height = plot_height,
            dpi = plot_dpi
        )
    } else {
        # No group_by specified — fall back to single plot
        plot_files <- plot_function(
            dataframe = df,
            mapping = options$mapping,
            title = options$title,
            output_directory = output_directory,
            output_file = if (!is.null(options$output_file)) options$output_file else NULL,
            show_median = show_median,
            include_risktable = include_risktable,
            width = plot_width,
            height = plot_height,
            dpi = plot_dpi
        )
    }
} else if (options$output_mode == "both") {
    single_plot <- plot_function(
        dataframe = df,
        mapping = options$mapping,
        title = options$title,
        output_directory = output_directory,
        output_file = if (!is.null(options$output_file)) options$output_file else NULL,
        show_median = show_median,
        include_risktable = include_risktable,
        width = plot_width,
        height = plot_height,
        dpi = plot_dpi
    )

    if (has_grouping) {
        grouped_plots <- generate_grouped_plots(
            dataframe = df,
            group_by = group_by,
            plot_function = plot_function,
            mapping = options$mapping,
            title = options$title,
            output_directory = output_directory,
            show_median = show_median,
            include_risktable = include_risktable,
            width = plot_width,
            height = plot_height,
            dpi = plot_dpi
        )
    } else {
        grouped_plots <- character(0)
    }

    plot_files <- c(single_plot, grouped_plots)
} else {
    stop("Unknown output mode.")
}

manifest <- list(
    workflow = "plot_generation",
    plot_type = options$plot_type,
    output_mode = options$output_mode,
    group_by = if (!is.null(group_by) && group_by != "None") group_by else NA,
    number_of_plots = length(plot_files),
    plots = plot_files,
    settings = list(
        show_median = show_median,
        include_risktable = include_risktable,
        width = plot_width,
        height = plot_height,
        dpi = plot_dpi
    )
)

write_json(manifest, manifest_file, pretty = TRUE, auto_unbox = TRUE)
