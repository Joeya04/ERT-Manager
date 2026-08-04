library(dplyr)
library(rfishbase)

################################################################################
# Pulls food items data from fishbase, creates a summary
rfishbase_fooditems <- function(df, server = "fishbase"){

    fooditems_df <- fooditems(df$Sci_name, server = server)

    fooditems_summary <- fooditems_df %>%
      transmute(
        Sci_name = Species,
        speccode = SpecCode,
        foodsref = FoodsRefNo,
        Food1 = FoodI,
        Food2 = FoodII,
        Food3 = FoodIII,
        foodgroup = Foodgroup,
        foodname = Foodname,
        predstage = PredatorStage
      )


    fooditems_combined <- fooditems_summary %>%
      group_by(Sci_name) %>%
      summarise(
        foodsref = paste(foodsref, collapse = "; "),
        Food1 = paste(Food1, collapse = "; "),
        Food2 = paste(Food2, collapse = "; "),
        Food3 = paste(Food3, collapse = "; "),
        foodgroup = paste(foodgroup, collapse = "; "),
        foodname = paste(foodname, collapse = "; "),
        predstage = paste(predstage, collapse = "; ")
      )

    return(fooditems_combined)

}
