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
        output_file <- "kmplot.png"
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
