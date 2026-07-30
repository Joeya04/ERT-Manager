library(dplyr)
library(ggsurvfit)
library(survival)
library(ggplot2)

create_kmplot <- function(fit, title, show_median = TRUE, include_risktable = TRUE, output_file = NULL) {

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

    ggsave(output_file, plot = p, width = 8, height = 6, dpi = 300)

    invisible(output_file)
}

generate_median_dumbbell_plot <- function(
    data,
    group_var,
    time_var,
    status_var,
    output_file = NULL
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
        ggsave(output_file, plot = p, width = 8, height = 6, dpi = 300)
    }

    return(p)

}

build_kmplots <- function(dataframe, mapping, title, output_directory, output_file = NULL, show_median = TRUE, include_risktable = TRUE) {

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
        output_file = output_file
    )

    return(output_file)
}

build_median_dumbbell_plots <- function(dataframe, mapping, title, output_directory, output_file = NULL) {

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
        output_file = output_file
    )

    if (!is.null(title)) {
        p <- p + labs(title = title)
        ggsave(output_file, plot = p, width = 8, height = 6, dpi = 300)
    }

    return(output_file)
}
