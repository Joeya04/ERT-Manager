############################################################
# grouped_plots.R
#
# Generic grouped plotting functions
#
# Called by:
#     plot_workflow.R
#
# Depends on:
#     basic_plots.R
#
############################################################

library(dplyr)

############################################################
# Generate one plot for each group
############################################################

generate_grouped_plots <- function(
    dataframe,
    group_by,
    plot_function,
    mapping,
    title,
    output_directory
) {

    if (!dir.exists(output_directory)) {
        dir.create(output_directory, recursive = TRUE, showWarnings = FALSE)
    }

    groups <- sort(unique(dataframe[[group_by]]))
    groups <- groups[!is.na(groups)]

    output_files <- character()

    for (group in groups) {
        subset_df <- dataframe %>%
            filter(.data[[group_by]] == group)

        safe_group <- gsub("[^A-Za-z0-9_-]", "_", as.character(group))

        output_file <- file.path(
            output_directory,
            paste0(safe_group, ".png")
        )

        group_title <- paste(title, "-", group)

        plot_function(
            dataframe = subset_df,
            mapping = mapping,
            title = group_title,
            output_directory = output_directory,
            output_file = output_file
        )

        output_files <- c(output_files, output_file)
    }

    return(output_files)
}