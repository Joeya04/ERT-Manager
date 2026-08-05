library(jsonlite)
library(dplyr)
library(ggsurvfit)
library(survival)
library(ggplot2)

############################################################
# Plotting Functions (inlined from plotting/basic_plots.R and plotting/plot_grouping.R)
############################################################

create_kmplot <- function(fit, title, show_median = TRUE, include_risktable = TRUE, output_file = NULL, width = 8, height = 6, dpi = 300) {

    if (is.null(output_file)) {
        output_file <- file.path(output_directory, "kmplot.png")
    }

    base_size <- 18
    title_size <- 22
    axis_title_size <- 20
    axis_text_size <- 16
    legend_size <- 16

    p <- ggsurvfit(fit) +
        labs(title = title, x = "Time", y = "ERT Probability") +
        add_confidence_interval() +
        scale_x_continuous(breaks = seq(0, 50, by = 2)) +
        theme_bw(base_size = base_size) +
        theme(
            legend.position = "bottom",
            plot.title = element_text(size = title_size, face = "bold"),
            axis.title = element_text(size = axis_title_size, face = "bold"),
            axis.text = element_text(size = axis_text_size),
            axis.text.x = element_text(size = axis_text_size),
            axis.text.y = element_text(size = axis_text_size),
            legend.text = element_text(size = legend_size),
            legend.title = element_text(size = legend_size, face = "bold")
        )

    if (isTRUE(include_risktable)) {
        p <- p + add_risktable(size = 5, y.text = TRUE, y.text.col = TRUE)
    }

    if (isTRUE(show_median)) {
        p <- p + add_quantile(y_value = 0.5, linetype = "dotted", color = "grey30", linewidth = 0.8)
    }

    if (!dir.exists(dirname(output_file))) {
        dir.create(dirname(output_file), recursive = TRUE, showWarnings = FALSE)
    }

    ggsave(output_file, plot = p, width = width, height = height, dpi = dpi)

    invisible(output_file)
}

generate_median_dumbbell_plot <- function(
    data,
    group_var,
    time_var,
    status_var,
    output_file = NULL,
    width = 8,
    height = 6,
    dpi = 300
) {

    data$SurvObj <- survival::Surv(
        data[[time_var]],
        data[[status_var]]
    )

    # Handle NULL group_var by using a constant grouping
    if (is.null(group_var)) {
        data$.dummy_group <- "All"
        group_var <- ".dummy_group"
    }

    fit <- survival::survfit(
        as.formula(paste("SurvObj ~", group_var)),
        data = data
    )

    medians <- summary(fit)$table

    median_df <- data.frame(
        group = rownames(medians),
        median_time = medians[, "median"],
        stringsAsFactors = FALSE
    )

    median_df <- median_df[!is.na(median_df$median_time), ]

    median_df$group <- factor(
        median_df$group,
        levels = median_df$group[
            order(median_df$median_time, decreasing = TRUE)
        ]
    )

    p <- ggplot(
        median_df,
        aes(
            x = 0,
            xend = median_time,
            y = group
        )
    ) +
        geom_segment(
            aes(
                yend = group
            ),
            color = "grey80",
            linewidth = 2
        ) +
        geom_point(
            aes(
                x = median_time
            ),
            color = "dodgerblue",
            size = 4
        ) +
        labs(
            x = "Median Residence Time",
            y = if (is.null(group_var) || group_var == ".dummy_group") "Group" else group_var,
            title = if (is.null(group_var) || group_var == ".dummy_group") "Median Residence Time" else paste("Median Residence by", group_var)
        ) +
        theme_minimal()

    if (!is.null(output_file)) {
        if (!dir.exists(dirname(output_file))) {
            dir.create(dirname(output_file), recursive = TRUE, showWarnings = FALSE)
        }
        ggsave(output_file, plot = p, width = width, height = height, dpi = dpi)
    }

    return(p)

}

build_kmplots <- function(dataframe, mapping, title, output_directory, output_file = NULL, show_median = TRUE, include_risktable = TRUE, width = 8, height = 6, dpi = 300) {

    if (!dir.exists(output_directory)) {
        dir.create(output_directory, recursive = TRUE, showWarnings = FALSE)
    }

    if (is.null(output_file)) {
        output_file <- file.path(output_directory, "kmplot.png")
    }

    group_var <- mapping[["group_var"]]
    time_var <- mapping[["time_var"]]
    status_var <- mapping[["status_var"]]

    if (is.null(time_var) || is.null(status_var)) {
        stop("A valid mapping with time_var and status_var is required for survival plots.")
    }

    dataframe$SurvObj <- survival::Surv(
        dataframe[[time_var]],
        dataframe[[status_var]]
    )

    # Handle NULL group_var by using ~ 1 (no grouping)
    if (is.null(group_var)) {
        fit <- survival::survfit(SurvObj ~ 1, data = dataframe)
    } else {
        fit <- survival::survfit(
            as.formula(paste("SurvObj ~", group_var)),
            data = dataframe
        )
    }

    create_kmplot(
        fit = fit,
        title = title,
        show_median = show_median,
        include_risktable = include_risktable,
        output_file = output_file,
        width = width,
        height = height,
        dpi = dpi
    )

    return(output_file)
}

build_median_dumbbell_plots <- function(dataframe, mapping, title, output_directory, output_file = NULL, show_median = TRUE, include_risktable = TRUE, width = 8, height = 6, dpi = 300) {

    if (!dir.exists(output_directory)) {
        dir.create(output_directory, recursive = TRUE, showWarnings = FALSE)
    }

    if (is.null(output_file)) {
        output_file <- file.path(output_directory, "median_dumbbell.png")
    }

    group_var <- mapping[["group_var"]]
    time_var <- mapping[["time_var"]]
    status_var <- mapping[["status_var"]]

    if (is.null(time_var) || is.null(status_var)) {
        stop("A valid mapping with time_var and status_var is required for dumbbell plots.")
    }

    p <- generate_median_dumbbell_plot(
        data = dataframe,
        group_var = group_var,
        time_var = time_var,
        status_var = status_var,
        output_file = output_file,
        width = width,
        height = height,
        dpi = dpi
    )

    if (!is.null(title)) {
        p <- p + labs(title = title)
        ggsave(output_file, plot = p, width = width, height = height, dpi = dpi)
    }

    return(output_file)
}

generate_grouped_plots <- function(
    dataframe,
    group_by,
    plot_function,
    mapping,
    title,
    output_directory,
    show_median = TRUE,
    include_risktable = TRUE,
    width = 8,
    height = 6,
    dpi = 300
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
            output_file = output_file,
            show_median = show_median,
            include_risktable = include_risktable,
            width = width,
            height = height,
            dpi = dpi
        )

        output_files <- c(output_files, output_file)
    }

    return(output_files)
}


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

# Normalize to forward slashes to prevent R from interpreting
# backslash escape sequences (e.g. \U in \Users) as Unicode escapes
output_directory <- gsub("\\\\", "/", output_directory)

# Extract optional formatting parameters
show_median <- if (!is.null(options$show_median)) options$show_median else TRUE
include_risktable <- if (!is.null(options$include_risktable)) options$include_risktable else TRUE
plot_width <- if (!is.null(options$width)) options$width else 8
plot_height <- if (!is.null(options$height)) options$height else 6
plot_dpi <- if (!is.null(options$dpi)) options$dpi else 300

# Extract subset options
subset_var <- options$subset_var
subset_value <- options$subset_value
subset_mode <- if (!is.null(options$subset_mode)) options$subset_mode else "single"

# Extract group_by (can be a list from multi-select or a single string)
group_by <- options$group_by
if (is.list(group_by)) {
    group_by <- unlist(group_by)
}
has_grouping <- !is.null(group_by) && length(group_by) > 0 && all(group_by != "None" && group_by != "")

# Helper: create a single plot (with strata if group_var is set)
create_single_plot <- function(dataframe, group_vars, plot_function, mapping, title,
                               output_directory, show_median, include_risktable,
                               width, height, dpi, subset_label = "") {
    full_title <- if (nzchar(subset_label)) paste(title, "-", subset_label) else title
    plot_files <- character()

    if (has_grouping && length(group_vars) > 0) {
        for (gb in group_vars) {
            gb_mapping <- mapping
            gb_mapping$group_var <- gb
            gb_title <- if (length(group_vars) == 1) full_title else paste(full_title, "-", gb)
            gb_output_file <- file.path(output_directory, paste0(gsub("[^A-Za-z0-9_-]", "_", gb), ".png"))
            p_file <- plot_function(
                dataframe = dataframe,
                mapping = gb_mapping,
                title = gb_title,
                output_directory = output_directory,
                output_file = gb_output_file,
                show_median = show_median,
                include_risktable = include_risktable,
                width = width,
                height = height,
                dpi = dpi
            )
            plot_files <- c(plot_files, p_file)
        }
    } else {
        gb_mapping <- mapping
        gb_mapping$group_var <- NULL
        p_file <- plot_function(
            dataframe = dataframe,
            mapping = gb_mapping,
            title = full_title,
            output_directory = output_directory,
            output_file = NULL,
            show_median = show_median,
            include_risktable = include_risktable,
            width = width,
            height = height,
            dpi = dpi
        )
        plot_files <- c(plot_files, p_file)
    }

    return(plot_files)
}

# Helper: create grouped plots (one per unique value of each group_var)
create_grouped_plots <- function(dataframe, group_vars, plot_function, mapping, title,
                                 output_directory, show_median, include_risktable,
                                 width, height, dpi, subset_label = "") {
    full_title <- if (nzchar(subset_label)) paste(title, "-", subset_label) else title
    plot_files <- character()

    if (has_grouping && length(group_vars) > 0) {
        for (gb in group_vars) {
            gb_mapping <- mapping
            gb_mapping$group_var <- gb
            grouped_files <- generate_grouped_plots(
                dataframe = dataframe,
                group_by = gb,
                plot_function = plot_function,
                mapping = gb_mapping,
                title = full_title,
                output_directory = output_directory,
                show_median = show_median,
                include_risktable = include_risktable,
                width = width,
                height = height,
                dpi = dpi
            )
            plot_files <- c(plot_files, grouped_files)
        }
    } else {
        gb_mapping <- mapping
        gb_mapping$group_var <- NULL
        p_file <- plot_function(
            dataframe = dataframe,
            mapping = gb_mapping,
            title = full_title,
            output_directory = output_directory,
            output_file = NULL,
            show_median = show_median,
            include_risktable = include_risktable,
            width = width,
            height = height,
            dpi = dpi
        )
        plot_files <- c(plot_files, p_file)
    }

    return(plot_files)
}

# Determine subset values to iterate over
if (is.null(subset_var) || subset_var == "None" || subset_var == "") {
    # No subsetting — use all data
    subset_configs <- list(list(value = NULL, label = "All Data"))
} else if (subset_mode == "single") {
    # Single value — filter to selected value
    if (is.null(subset_value) || subset_value == "None" || subset_value == "") {
        # No value selected — use all data
        subset_configs <- list(list(value = NULL, label = "All Data"))
    } else {
        subset_configs <- list(list(value = subset_value, label = paste("Subset:", subset_var, "=", subset_value)))
    }
} else {
    # Each unique value — create a plot for each
    unique_vals <- sort(unique(df[[subset_var]]))
    unique_vals <- unique_vals[!is.na(unique_vals)]
    subset_configs <- lapply(unique_vals, function(v) {
        list(value = v, label = paste("Subset:", subset_var, "=", v))
    })
}

# Generate plots for each subset configuration
plot_files <- character()

for (sc in subset_configs) {
    # Filter data for this subset
    if (is.null(sc$value)) {
        subset_df <- df
    } else {
        subset_df <- df[df[[subset_var]] == sc$value, ]
    }

    # Skip if no data after filtering
    if (nrow(subset_df) == 0) next

    subset_label <- sc$label

    if (options$output_mode == "single") {
        plot_files <- c(plot_files, create_single_plot(
            dataframe = subset_df,
            group_vars = group_by,
            plot_function = plot_function,
            mapping = options$mapping,
            title = options$title,
            output_directory = output_directory,
            show_median = show_median,
            include_risktable = include_risktable,
            width = plot_width,
            height = plot_height,
            dpi = plot_dpi,
            subset_label = subset_label
        ))
    } else if (options$output_mode == "grouped") {
        plot_files <- c(plot_files, create_grouped_plots(
            dataframe = subset_df,
            group_vars = group_by,
            plot_function = plot_function,
            mapping = options$mapping,
            title = options$title,
            output_directory = output_directory,
            show_median = show_median,
            include_risktable = include_risktable,
            width = plot_width,
            height = plot_height,
            dpi = plot_dpi,
            subset_label = subset_label
        ))
    } else if (options$output_mode == "both") {
        plot_files <- c(plot_files, create_single_plot(
            dataframe = subset_df,
            group_vars = group_by,
            plot_function = plot_function,
            mapping = options$mapping,
            title = options$title,
            output_directory = output_directory,
            show_median = show_median,
            include_risktable = include_risktable,
            width = plot_width,
            height = plot_height,
            dpi = plot_dpi,
            subset_label = subset_label
        ))
        plot_files <- c(plot_files, create_grouped_plots(
            dataframe = subset_df,
            group_vars = group_by,
            plot_function = plot_function,
            mapping = options$mapping,
            title = options$title,
            output_directory = output_directory,
            show_median = show_median,
            include_risktable = include_risktable,
            width = plot_width,
            height = plot_height,
            dpi = plot_dpi,
            subset_label = subset_label
        ))
    } else {
        stop("Unknown output mode.")
    }
}

manifest <- list(
    workflow = "plot_generation",
    plot_type = options$plot_type,
    output_mode = options$output_mode,
    group_by = if (has_grouping) as.list(group_by) else NA,
    subset_var = if (!is.null(subset_var) && subset_var != "None") subset_var else NA,
    subset_value = if (!is.null(subset_value) && subset_value != "None") subset_value else NA,
    subset_mode = subset_mode,
    number_of_plots = length(plot_files),
    plots = plot_files,
    output_directory = output_directory,
    settings = list(
        show_median = show_median,
        include_risktable = include_risktable,
        width = plot_width,
        height = plot_height,
        dpi = plot_dpi
    )
)

write_json(manifest, manifest_file, pretty = TRUE, auto_unbox = TRUE)
