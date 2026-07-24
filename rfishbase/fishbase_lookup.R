library(dplyr)
library(rfishbase)


#Matches species with their target index and returns a dataframe with taxonomic information (Order, Family)
match_species <- function(index_df, index_sheet){


    #reads scientific name index and assigns taxonomic information (Order, Family)
    fish_df <- read.xlsx(index_df, sheet = index_sheet)


    #Loads taxonomy information from fishbase
    taxa_data <- load_taxa()

    fish_taxonomy <- taxa_data %>% 
    filter(Species == Sci_name) %>%
    select(Species, Family, Order)

    return(fish_taxonomy)
}

#Takes the records from the input df and joins the index data to it after some formatting and renaming
match_species_joined <- function(df){

df_names <- df %>% rename(common_name = `Species`, 
                          entity_id = `Individual`,
                          intro = `Intro_date`, 
                          exit = `Exit_date`,
                          days = `duration_days`,
                          years = `yearfrac`,
                          censored = `status`,
                          red_census = `red_census`
) 

    #Adds respective dates to all of the records
    df_names$intro <- as.Date(df_names$intro, origin = "1899-12-30")
    df_names$exit <- as.Date(df_names$exit, origin = "1899-12-30")

    matched <- matched_species(df) %>%
    matched_df <- matched %>%
        left_join(df_names, by = "Species")

    return(matched_df)

}