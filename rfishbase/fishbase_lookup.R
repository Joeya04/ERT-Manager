library(dplyr)
library(rfishbase)


############################################################
# match_species
#
# Reads a species index from an Excel sheet and returns
# taxonomic information (Order, Family) from FishBase.
#
# Parameters:
#   index_df   - path to the Excel file containing the species index
#   index_sheet - name of the sheet within the Excel file
#
# Returns:
#   A dataframe with Species, Family, and Order columns
############################################################
match_species <- function(index_df, index_sheet) {
    fish_df <- read.xlsx(index_df, sheet = index_sheet)

    taxa_data <- load_taxa()

    fish_taxonomy <- taxa_data %>%
        filter(Species %in% fish_df$Sci_name) %>%
        select(Species, Family, Order)

    return(fish_taxonomy)
}


############################################################
# match_species_joined
#
# Takes the records from the input df, renames columns to
# standard names, and joins FishBase taxonomy information.
#
# Parameters:
#   df - input dataframe with a 'Species' column containing
#        scientific names
#
# Returns:
#   A dataframe with original columns plus Family and Order
############################################################
match_species_joined <- function(df) {
    df_names <- df %>% rename(
        common_name = Species,
        entity_id = Individual,
        intro = Intro_date,
        exit = Exit_date,
        days = duration_days,
        years = yearfrac,
        censored = status,
        red_census = red_census
    )

    # Adds respective dates to all of the records
    df_names$intro <- as.Date(df_names$intro, origin = "1899-12-30")
    df_names$exit <- as.Date(df_names$exit, origin = "1899-12-30")

    # Look up taxonomy from FishBase
    species_list <- unique(df$Species)
    species_list <- species_list[!is.na(species_list)]

    taxa_data <- load_taxa()

    matched <- taxa_data %>%
        filter(Species %in% species_list) %>%
        select(Species, Family, Order)

    matched_df <- matched %>%
        left_join(df_names, by = c("Species" = "common_name"))

    return(matched_df)
}
