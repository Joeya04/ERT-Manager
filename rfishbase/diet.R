library(dplyr)
library(rfishbase)

################################################################################
# Pulls diet data from fishbase, creates a summary, then exports it to excel
rfishbase_diet <- function(df, server = "fishbase"){

    diet_df <- diet(df$Sci_name, server = server)

    diet_summary <- diet_df %>%
    transmute(
        Sci_name = Species,
        speccode = SpecCode,
        dietcode = DietCode,
        stockcode = StockCode,
        dietref = DietRefNo,
        samplesize = SampleSize,
        trophiclvl = Troph,
        trophicse = seTroph,
        sizemin = SizeMin,
        sizemax = SizeMax,
        fishlength = FishLength,
        observations = n()
    )


    diet_combined <- diet_summary %>%
    group_by(Sci_name) %>%
    summarise(
        dietcode = paste(dietcode, collapse = "; "),
        stockcode = paste(stockcode, collapse = "; "),
        dietref = paste(dietref, collapse = "; "),
        samplesize = paste(samplesize, collapse = "; "),
        trophiclvl = mean(trophiclvl),
        trophicse = mean(trophicse),
        sizemin = paste(sizemin, collapse = "; "),
        sizemax = paste(sizemax, collapse = "; "),
        fishlength = paste(fishlength, collapse = "; ")
    )

    return(diet_combined)
}

    # diet_final <- diet_final %>%
    # mutate(
    #     trophic_class = casewhen(
    #     between(trophiclvl, 2, 2.49) ~ "Low_primary",
    #     between(trophiclvl, 2.5, 2.99) ~  "high_primary",
    #     between(trophiclvl, 3, 3.49) ~  "low_secondary",
    #     between(trophiclvl, 3.5, 4)  ~ "high_secondary",
    #     between(trophiclvl, 4, 4.49) ~  "tertiary"
    #     )
    # )
