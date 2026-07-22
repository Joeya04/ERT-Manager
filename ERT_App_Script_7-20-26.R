#
# This is a Shiny web application. You can run the application by clicking
# the 'Run App' button above.
#
# Find out more about building applications with Shiny here:
#
#    https://shiny.posit.co/

library(shiny)
library(readxl)
library(survival)
library(ggsurvfit)
library(ggplot2)
library(patchwork)
library(dplyr)
library(ggalt)
library(DT)

ui <- fluidPage(
  titlePanel("Enclosure Residence Time Calculator"),
  
  sidebarLayout(
    sidebarPanel(
      helpText("Step 1: Start by uploading your data to the calculator below: (acceptable formats: .csv, .xlsx, .xls) "),
      fileInput("file", "Upload Spreadsheet", accept = c(".csv", ".xlsx", ".xls")),
      hr(),
      helpText("Step 2: Select the column in your datasheet that represents the time variable for your enclosure residence data (typically in years): "),
      uiOutput("time_var_ui"),
      hr(),
      helpText("Step 3: For Kaplan-Meier Plots, select the column in your datasheet that indicates the censorship status. This column must be coded as:"),
      helpText("0 = censored (animal is still in enclosure)"),
      helpText("1 = uncensored (animal is no longer in enclosure)"),
      uiOutput("status_var_ui"),
      hr(),
      helpText("Step 4: Explore the tabs on the right for additional visualizations and summary tables."),
      hr(),
      helpText(span("Disclaimer: We do not warrant that the service provided by the Enclosure Residence Time Calculator
               will be uninterrupted, error-free, or secure. Your data when using this calculator is
               stored and backed up on local and/or cloud storage. We have no liabiliity for any loss
               or misappropriation of your data under any circumstances.", style = "font-size: 12px; font-style: italic;")),
    ),
    
    mainPanel(
      tabsetPanel(
        id = "main_tabs",
        type = "tabs",
        
        # ---------------------------
        # NEW: Data Summary Tab
        # ---------------------------
        tabPanel("Data Preparation",
                 h4("How to Organize your Data:"),
                 helpText("Enclosure residence time analysis requires data on study organisms to be structured so that each individual
                          creature is assigned an enclosure entrance date and exit date.  These dates may be exact or estimated based on 
                          available records and associated data quality.  In the absence of comprehensive records and/or in the case of
                          group-managed organisms, adopting certain assumptions uniformly to generate estimated entrance and exit dates
                          is recommended."),
                 helpText("Organizational tools, such as the enclosure residence diagram below can help investigators reconstruct
                          actual and/or estimated enclosure entrance and exit dates at the individual organism level when population records
                          are spread across multiple repositories or complicated by inconsistent data management practices."),
                 img(src = "FIGURE2.jpg", height = 400, width = 750),
                 helpText("In the diagram above, each column represents an individual organism, while each row is a year with corresponding annual census values.
                          Entrance dates are assigned in chronological order, and estimated or actual exit dates are matched up with individual organisms
                          based on a first-in, first-out assumption, unless individually tracked animals already have confirmed entrance and exit dates.  
                          Estimated entrance or exit dates can then be cross-referenced with annual census values to ensure population numbers match."),
                 hr(),
                 h4("Preparing Data for Upload and Analysis:"),               
                 helpText("Once enclosure residence time for each organism is determined and entrance and exit dates are assigned to each individual,
                          the data should be organized as shown in the example below for uploading to the Enclosure Residence Time Calculator"),
                 img(src = "ERT_Example_Dataframe.jpg", height = 337, width = 574),
                 helpText("Once your input data is structured as outlined above, it can be uploaded via the side panel (starting with Step 1).
                          After uploading your data file, follow the subsequent steps to instruct the calculator which data column in your file represents
                          the residence time for each organism (Step 2), and the censorship status (Step 3). Once steps 1-3 are completed, a summary of the
                          uploaded data will appear below to verify the calculator in interpreting the file correctly. If everything appears correct, explore your data
                          using the tabs on the right."),
                 helpText(""),
                 hr(),
                 h4("Dataset Overview"),
                 verbatimTextOutput("dataDimensions"),
                 hr(),
                 h4("Variable Summary"),
                 DTOutput("dataPreview"),
                 hr(),
                 h4("Data Structure"),
                 verbatimTextOutput("dataStructure"),
                 hr(),
                 h4("Missing Data Analysis"),
                 DTOutput("missingDataTable"),
                 plotOutput("missingDataPlot", height = "400px")
        ),
        
        # ---------------------------
        # Kaplan-Meier Tab
        # ---------------------------
        tabPanel("Kaplan-Meier Plots",
                 h4("Grouping Options"),
                 uiOutput("group_vars_ui"),
                 
                 # --- Subsetting Controls ---
                 h4("Subset Options"),
                 uiOutput("subset_var_ui"),
                 uiOutput("subset_value_ui"),
                 actionButton("reset_filters", "Reset Filters", icon = icon("refresh")),
                 hr(),
                 
                 uiOutput("median_checkbox_ui"),
                 numericInput("ncol", "Plots per row:", value = 1, min = 1, max = 4),
                 hr(),
                 
                 # KM plot displayed first
                 uiOutput("dynamicPlotUI"),
                 hr(),
                 
                 # Controls moved BELOW the plot
                 h4("Download Options"),
                 numericInput("plot_width", "Plot width (inches):", value = 8, min = 4, max = 20),
                 numericInput("plot_height", "Plot height (inches):", value = 6, min = 4, max = 20),
                 numericInput("plot_dpi", "JPEG quality (DPI):", value = 300, min = 72, max = 600),
                 downloadButton("downloadPlot", "Download KM Plots (JPEG - Plot Only)"),
                 br(), br(),
                 downloadButton("downloadRiskTables", "Download Risk Tables (CSV)")
        ),
        
        # ---------------------------
        # Dumbbell Plot Tab
        # ---------------------------
        tabPanel("Median Dumbbell Plot",
                 uiOutput("median_group_ui"),
                 plotOutput("medianDumbbellPlot", height = "500px")
        ),
        
        # ---------------------------
        # Summary Statistics Tab
        # ---------------------------
        tabPanel("Summary Statistics",
                 uiOutput("summary_group_ui"),
                 checkboxInput("include_overall", "Include Overall Summary (No Grouping)", value = TRUE),
                 downloadButton("downloadSummary", "Download CSV"),
                 br(), br(),
                 DTOutput("summaryStatsTable")
        )
      )
    )
  )
)

server <- function(input, output, session) {
  
  # Reactive file input
  dataInput <- reactive({
    req(input$file)
    ext <- tools::file_ext(input$file$name)
    if (ext == "csv") {
      read.csv(input$file$datapath)
    } else if (ext %in% c("xlsx", "xls")) {
      read_excel(input$file$datapath)
    } else {
      validate("Please upload a CSV or Excel file")
    }
  })
  
  # --- Dynamic UI ---
  output$time_var_ui <- renderUI({
    req(dataInput())
    selectInput("time_var", "Time Variable (x-axis)", choices = names(dataInput()))
  })
  
  output$status_var_ui <- renderUI({
    req(dataInput())
    selectInput("status_var", "Status Variable (censored vs. uncensored)", choices = names(dataInput()))
  })
  
  output$group_vars_ui <- renderUI({
    req(dataInput())
    selectInput("group_vars", "Grouping Variables for KM Plots (choose one or more)", 
                choices = names(dataInput()), multiple = TRUE)
  })
  
  # --- Subsetting Variable UI ---
  output$subset_var_ui <- renderUI({
    req(dataInput())
    selectInput("subset_var", "Subset Variable (optional)", 
                choices = c("None", names(dataInput())), selected = "None")
  })
  
  # --- Subsetting Value UI ---
  output$subset_value_ui <- renderUI({
    req(input$subset_var, dataInput())
    if (input$subset_var != "None") {
      vals <- unique(dataInput()[[input$subset_var]])
      selectInput("subset_value", paste("Select Value from", input$subset_var), choices = vals)
    }
  })
  
  # --- Subset data based on user selection ---
  filteredData <- reactive({
    df <- dataInput()
    if (!is.null(input$subset_var) && input$subset_var != "None" && !is.null(input$subset_value)) {
      df <- df[df[[input$subset_var]] == input$subset_value, ]
    }
    df
  })
  
  observeEvent(input$reset_filters, {
    updateSelectInput(session, "subset_var", selected = "None")
    updateSelectInput(session, "subset_value", selected = "")
  })
  
  output$median_checkbox_ui <- renderUI({
    req(dataInput())
    if (is.null(input$group_vars) || length(input$group_vars) == 0) {
      checkboxInput("median_overall", "Show Median Residence Line for Overall", value = TRUE)
    } else {
      tagList(
        lapply(input$group_vars, function(var) {
          checkboxInput(paste0("median_", var), paste("Show Residence Line for", var), value = TRUE)
        })
      )
    }
  })
  
  output$median_group_ui <- renderUI({
    req(dataInput())
    selectInput("median_group_var", "Select Variable for Median Dumbbell Plot", 
                choices = names(dataInput()), selected = names(dataInput())[1])
  })
  
  output$summary_group_ui <- renderUI({
    req(dataInput())
    selectInput("summary_group_var", "Select Grouping Variable for Summary Statistics", 
                choices = names(dataInput()), selected = names(dataInput())[1])
  })
  
  # ===========================================
  # DATA SUMMARY TAB OUTPUTS
  # ===========================================
  
  # Dataset dimensions
  output$dataDimensions <- renderPrint({
    req(dataInput())
    df <- dataInput()
    cat("Number of rows:", nrow(df), "\n")
    cat("Number of columns:", ncol(df), "\n")
    cat("Column names:", paste(names(df), collapse = ", "), "\n")
  })
  
  # Data preview with summary statistics
  output$dataPreview <- renderDT({
    req(dataInput())
    df <- dataInput()
    
    # Create summary for each column
    summary_df <- data.frame(
      Variable = names(df),
      Type = sapply(df, function(x) class(x)[1]),
      Missing = sapply(df, function(x) sum(is.na(x))),
      Unique = sapply(df, function(x) length(unique(x))),
      Sample_Values = sapply(df, function(x) {
        vals <- unique(x)[1:min(3, length(unique(x)))]
        paste(vals, collapse = ", ")
      })
    )
    
    datatable(summary_df, 
              options = list(pageLength = 20, autoWidth = TRUE),
              rownames = FALSE)
  })
  
  # Data structure
  output$dataStructure <- renderPrint({
    req(dataInput())
    str(dataInput())
  })
  
  # Missing data table
  output$missingDataTable <- renderDT({
    req(dataInput())
    df <- dataInput()
    
    missing_df <- data.frame(
      Variable = names(df),
      Missing_Count = sapply(df, function(x) sum(is.na(x))),
      Missing_Percent = sapply(df, function(x) round(100 * sum(is.na(x)) / length(x), 2))
    )
    
    missing_df <- missing_df[order(missing_df$Missing_Count, decreasing = TRUE), ]
    
    datatable(missing_df,
              options = list(pageLength = 20, autoWidth = TRUE),
              rownames = FALSE) %>%
      formatStyle('Missing_Percent',
                  backgroundColor = styleInterval(c(0, 5, 10), 
                                                  c('lightgreen', 'yellow', 'orange', 'red')))
  })
  
  # Missing data visualization
  output$missingDataPlot <- renderPlot({
    req(dataInput())
    df <- dataInput()
    
    missing_df <- data.frame(
      Variable = names(df),
      Missing_Percent = sapply(df, function(x) 100 * sum(is.na(x)) / length(x))
    )
    
    missing_df <- missing_df[order(missing_df$Missing_Percent, decreasing = TRUE), ]
    missing_df$Variable <- factor(missing_df$Variable, levels = missing_df$Variable)
    
    ggplot(missing_df, aes(x = Variable, y = Missing_Percent)) +
      geom_bar(stat = "identity", fill = "steelblue") +
      coord_flip() +
      labs(title = "Missing Data by Variable",
           x = "Variable",
           y = "Percent Missing (%)") +
      theme_minimal() +
      theme(axis.text.y = element_text(size = 10))
  })
  
  # ===========================================
  # KAPLAN-MEIER PLOTS
  # ===========================================
  
  # Helper to build KM plots
  build_plot <- function(fit, title, show_median = TRUE, include_risktable = TRUE) {
    # Increased base font sizes for better readability
    base_size <- 18  # Increased from 12
    title_size <- 22  # Increased for titles
    axis_title_size <- 20  # Increased for axis labels
    axis_text_size <- 16  # Increased for axis tick labels
    legend_size <- 16  # Increased for legend
    
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
    p
  }
  
  # KM plot rendering
  output$dynamicPlotUI <- renderUI({
    req(input$plot_height, input$plot_width)
    plotOutput("combinedPlot", 
               height = paste0(input$plot_height * 96, "px"),
               width = paste0(input$plot_width * 96, "px"))
  })
  
  output$combinedPlot <- renderPlot({
    req(input$time_var, input$status_var)
    df <- filteredData()
    
    # Validate non-empty after filtering
    validate(need(nrow(df) > 0, "No data available after filtering — adjust subset selection."))
    df$SurvObj <- Surv(df[[input$time_var]], df[[input$status_var]])
    
    # Subset title text
    subset_text <- if (!is.null(input$subset_var) && input$subset_var != "None" && !is.null(input$subset_value)) {
      paste("Subset:", input$subset_var, "=", input$subset_value)
    } else {
      "All Data"
    }
    
    if (is.null(input$group_vars) || length(input$group_vars) == 0) {
      fit <- survfit(SurvObj ~ 1, data = df)
      show_median <- isTRUE(input$median_overall)
      return(build_plot(fit, paste("Enclosure Residence Time —", subset_text), show_median, include_risktable = TRUE))
    }
    
    plot_list <- lapply(input$group_vars, function(var) {
      fit <- survfit(as.formula(paste("SurvObj ~", var)), data = df)
      show_median <- isTRUE(input[[paste0("median_", var)]])
      build_plot(fit, paste("ERT by", var, "—", subset_text), show_median, include_risktable = TRUE)
    })
    wrap_plots(plotlist = plot_list, ncol = input$ncol)
  })
  
  # Download KM Plot (JPEG, no risk tables)
  output$downloadPlot <- downloadHandler(
    filename = function() { paste0("ERT_plots_", Sys.Date(), ".jpg") },
    content = function(file) {
      df <- filteredData()
      df$SurvObj <- Surv(df[[input$time_var]], df[[input$status_var]])
      subset_text <- if (!is.null(input$subset_var) && input$subset_var != "None" && !is.null(input$subset_value)) {
        paste("Subset:", input$subset_var, "=", input$subset_value)
      } else {
        "All Data"
      }
      
      if (is.null(input$group_vars) || length(input$group_vars) == 0) {
        fit <- survfit(SurvObj ~ 1, data = df)
        show_median <- isTRUE(input$median_overall)
        p <- build_plot(fit, paste("Enclosure Residence Time —", subset_text), show_median, include_risktable = FALSE)
      } else {
        plot_list <- lapply(input$group_vars, function(var) {
          fit <- survfit(as.formula(paste("SurvObj ~", var)), data = df)
          show_median <- isTRUE(input[[paste0("median_", var)]])
          build_plot(fit, paste("ERT by", var, "—", subset_text), show_median, include_risktable = FALSE)
        })
        p <- wrap_plots(plotlist = plot_list, ncol = input$ncol)
      }
      
      ggsave(file, plot = p, device = "jpeg", width = input$plot_width, height = input$plot_height, dpi = input$plot_dpi, quality = 95)
    }
  )
  
  # Download Risk Tables (CSV)
  output$downloadRiskTables <- downloadHandler(
    filename = function() { paste0("risk_tables_", Sys.Date(), ".csv") },
    content = function(file) {
      req(input$time_var, input$status_var)
      df <- filteredData()
      df$SurvObj <- Surv(df[[input$time_var]], df[[input$status_var]])
      
      # Create comprehensive risk table data
      all_risk_data <- data.frame()
      
      if (is.null(input$group_vars) || length(input$group_vars) == 0) {
        # Overall risk table
        fit <- survfit(SurvObj ~ 1, data = df)
        risk_summary <- summary(fit, times = seq(0, max(fit$time), by = 1))
        
        risk_df <- data.frame(
          Group = "Overall",
          Time = risk_summary$time,
          N_Risk = risk_summary$n.risk,
          N_Event = risk_summary$n.event,
          N_Censored = risk_summary$n.censor,
          Survival = round(risk_summary$surv, 4),
          Std_Error = round(risk_summary$std.err, 4)
        )
        all_risk_data <- risk_df
      } else {
        # Risk tables for each grouping variable
        for (var in input$group_vars) {
          fit <- survfit(as.formula(paste("SurvObj ~", var)), data = df)
          
          # Extract risk table for each stratum
          for (i in seq_along(fit$strata)) {
            strata_name <- names(fit$strata)[i]
            group_name <- sub("^.*=", "", strata_name)
            
            # Get indices for this stratum
            if (i == 1) {
              idx <- 1:fit$strata[i]
            } else {
              idx <- (sum(fit$strata[1:(i-1)]) + 1):sum(fit$strata[1:i])
            }
            
            risk_summary <- summary(fit, times = seq(0, max(fit$time[idx]), by = 1))
            
            # Filter to this stratum's data
            strata_times <- fit$time[idx]
            strata_indices <- which(risk_summary$time %in% strata_times)
            
            if (length(strata_indices) > 0) {
              risk_df <- data.frame(
                Variable = var,
                Group = group_name,
                Time = risk_summary$time[strata_indices],
                N_Risk = risk_summary$n.risk[strata_indices],
                N_Event = risk_summary$n.event[strata_indices],
                N_Censored = risk_summary$n.censor[strata_indices],
                Survival = round(risk_summary$surv[strata_indices], 4),
                Std_Error = round(risk_summary$std.err[strata_indices], 4)
              )
              all_risk_data <- rbind(all_risk_data, risk_df)
            }
          }
        }
      }
      
      write.csv(all_risk_data, file, row.names = FALSE)
    }
  )
  
  # ===========================================
  # DUMBBELL PLOT
  # ===========================================
  
  output$medianDumbbellPlot <- renderPlot({
    req(input$median_group_var, input$time_var, input$status_var)
    df <- dataInput()
    df$SurvObj <- Surv(df[[input$time_var]], df[[input$status_var]])
    group_var <- input$median_group_var
    
    fit <- survfit(as.formula(paste("SurvObj ~", group_var)), data = df)
    medians <- summary(fit)$table
    median_df <- data.frame(
      group = rownames(medians),
      median_time = medians[, "median"]
    )
    
    median_df$group <- factor(median_df$group, 
                              levels = median_df$group[order(median_df$median_time, decreasing = TRUE)])
    
    ggplot(median_df, aes(x = 0, xend = median_time, y = group)) +
      geom_segment(aes(x = 0, xend = median_time, y = group, yend = group), color = "grey80", size = 2) +
      geom_point(aes(x = median_time, y = group), color = "dodgerblue", size = 4) +
      labs(x = "Median Residence Time", y = group_var, title = paste("Median Residence by", group_var)) +
      theme_minimal()
  })
  
  # ===========================================
  # SUMMARY STATISTICS
  # ===========================================
  
  summary_stats <- reactive({
    req(input$summary_group_var, input$time_var, input$status_var)
    df <- dataInput()
    time_var <- input$time_var
    status_var <- input$status_var
    group_var <- input$summary_group_var
    
    df$SurvObj <- Surv(df[[time_var]], df[[status_var]])
    
    results <- data.frame(
      Group = character(),
      Total = numeric(),
      MedianERT = numeric(),
      PercentRemainingAt1Year = numeric(),
      ERTWhen10PercentRemains = numeric(),
      MaxERT = numeric(),
      MinERT = numeric(),
      stringsAsFactors = FALSE
    )
    
    # Add overall summary if checkbox is selected
    if (isTRUE(input$include_overall)) {
      fit_overall <- survfit(SurvObj ~ 1, data = df)
      surv_data_overall <- data.frame(time = fit_overall$time, surv = fit_overall$surv)
      
      median_val <- summary(fit_overall)$table["median"]
      
      # Calculate y01_time (time when 10% remain, i.e., survival = 0.1)
      if (nrow(surv_data_overall) > 0 && min(surv_data_overall$surv) <= 0.1) {
        y01_time <- surv_data_overall$time[which.min(abs(surv_data_overall$surv - 0.1))]
      } else {
        y01_time <- NA
      }
      
      # Calculate x1_surv (survival at time = 1)
      if (nrow(surv_data_overall) > 0 && max(surv_data_overall$time) >= 1) {
        x1_surv <- surv_data_overall$surv[which.min(abs(surv_data_overall$time - 1))]
      } else if (nrow(surv_data_overall) > 0) {
        x1_surv <- surv_data_overall$surv[nrow(surv_data_overall)]
      } else {
        x1_surv <- NA
      }
      
      results <- rbind(results, data.frame(
        Group = "Overall (All Data)",
        Total = nrow(df),
        MedianERT = round(as.numeric(median_val), 3),
        PercentRemainingAt1Year = round(100 * as.numeric(x1_surv), 1),
        ERTWhen10PercentRemains = round(as.numeric(y01_time), 3),
        MaxERT = round(max(df[[time_var]], na.rm = TRUE), 3),
        MinERT = round(min(df[[time_var]], na.rm = TRUE), 3)
      ))
    }
    
    # Add grouped summaries
    fit <- survfit(as.formula(paste("SurvObj ~", group_var)), data = df)
    
    # Get unique groups from the data
    unique_groups <- unique(df[[group_var]])
    
    for (grp_name in unique_groups) {
      grp_data <- df[df[[group_var]] == grp_name, ]
      
      # Skip if no data in this group
      if (nrow(grp_data) == 0) next
      
      fit_grp <- survfit(SurvObj ~ 1, data = grp_data)
      surv_data <- data.frame(time = fit_grp$time, surv = fit_grp$surv)
      
      # Handle edge cases for survival data
      median_val <- ifelse(length(summary(fit_grp)$table) > 0, 
                           summary(fit_grp)$table["median"], 
                           NA)
      
      # Calculate y01_time (time when 10% remain, i.e., survival = 0.1)
      if (nrow(surv_data) > 0 && min(surv_data$surv) <= 0.1) {
        y01_time <- surv_data$time[which.min(abs(surv_data$surv - 0.1))]
      } else {
        y01_time <- NA
      }
      
      # Calculate x1_surv (survival at time = 1)
      if (nrow(surv_data) > 0 && max(surv_data$time) >= 1) {
        x1_surv <- surv_data$surv[which.min(abs(surv_data$time - 1))]
      } else if (nrow(surv_data) > 0) {
        # If max time < 1, use the last available survival value
        x1_surv <- surv_data$surv[nrow(surv_data)]
      } else {
        x1_surv <- NA
      }
      
      results <- rbind(results, data.frame(
        Group = as.character(grp_name),
        Total = nrow(grp_data),
        MedianERT = round(as.numeric(median_val), 3),
        PercentRemainingAt1Year = round(100 * as.numeric(x1_surv), 1),
        ERTWhen10PercentRemains = round(as.numeric(y01_time), 3),
        MaxERT = round(max(grp_data[[time_var]], na.rm = TRUE), 3),
        MinERT = round(min(grp_data[[time_var]], na.rm = TRUE), 3)
      ))
    }
    
    results
  })
  
  output$summaryStatsTable <- renderDT({
    datatable(summary_stats(), options = list(pageLength = 10, autoWidth = TRUE), rownames = FALSE)
  })
  
  output$downloadSummary <- downloadHandler(
    filename = function() { paste0("summary_statistics_", Sys.Date(), ".csv") },
    content = function(file) {
      write.csv(summary_stats(), file, row.names = FALSE)
    }
  )
}

shinyApp(ui, server)