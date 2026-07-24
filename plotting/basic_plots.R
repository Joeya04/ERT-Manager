

create_kmplot <- function(fit, title, show_median = TRUE, include_risktable = TRUE, output_file){

    base_size <- 18  # Increased from 12
    title_size <- 22  # Increased for titles
    axis_title_size <- 20  # Increased for axis labels
    axis_text_size <- 16  # Increased for axis tick labels
    legend_size <- 16  # Increased for legend
    
    #GGsurvfit
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
        
        # Add risk table only if requested
        if (include_risktable) {
        p <- p + add_risktable(size = 5, y.text = TRUE, y.text.col = TRUE)
        }
        
        if (isTRUE(show_median)) {
        p <- p + add_quantile(y_value = 0.5, linetype = "dotted", color = "grey30", linewidth = 0.8)
        }
    
    ggsave(

        output_file,

        plot = p

    )

}