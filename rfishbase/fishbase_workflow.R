library(jsonlite)

ource("plotting/basic_plots.R")

source("plotting/grouped_plots.R")


############################################################
# plot_workflow.R
#
# Master R Plot Workflow
#
# Called from:
#     plotting_controller.py
#
############################################################




############################################################
# Read command line arguments
############################################################

args <- commandArgs(trailingOnly = TRUE)

input_file    <- args[1]
options_file  <- args[2]
manifest_file <- args[3]

############################################################
# Read dataframe
############################################################

df <- read.csv(
    input_file,
    stringsAsFactors = FALSE
)

############################################################
# Read plotting options
############################################################

options <- fromJSON(options_file)

############################################################
# Available plot types
############################################################

plot_registry <- list(

    survival     = build_kmplots

)

############################################################
# Validate plot type
############################################################

if(!(options$plot_type %in% names(plot_registry))){

    stop("Unknown plot type.")

}

############################################################
# Retrieve plotting function
############################################################

plot_function <- plot_registry[[options$plot_type]]

############################################################
# Generate plots
############################################################

if(options$output_mode == "single"){

    plot_files <- plot_function(

        dataframe = df,

        mapping = options$mapping,

        title = options$title,

        output_directory = options$output_directory

    )

}else if(options$output_mode == "grouped"){

    plot_files <- generate_grouped_plots(

        dataframe = df,

        group_by = options$group_by,

        plot_function = plot_function,

        mapping = options$mapping,

        title = options$title,

        output_directory = options$output_directory

    )

}else if(options$output_mode == "both"){

    single_plot <- plot_function(

        dataframe = df,

        mapping = options$mapping,

        title = options$title,

        output_directory = options$output_directory

    )

    grouped_plots <- generate_grouped_plots(

        dataframe = df,

        group_by = options$group_by,

        plot_function = plot_function,

        mapping = options$mapping,

        title = options$title,

        output_directory = options$output_directory

    )

    plot_files <- c(single_plot, grouped_plots)

}else{

    stop("Unknown output mode.")

}

############################################################
# Build manifest
############################################################

manifest <- list(

    workflow = "plot_generation",

    plot_type = options$plot_type,

    output_mode = options$output_mode,

    group_by = options$group_by,

    number_of_plots = length(plot_files),

    plots = plot_files

)

############################################################
# Save manifest
############################################################

write_json(

    manifest,

    manifest_file,

    pretty = TRUE,

    auto_unbox = TRUE

)