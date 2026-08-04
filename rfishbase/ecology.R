library(dplyr)
library(rfishbase)

################################################################################
# Pulls ecology data from fishbase, creates a summary
rfishbase_ecology <- function(df, server = "fishbase"){

    ecology_df <- ecology(df$Sci_name, server = server)

    ecology_summary <- ecology_df %>%
      transmute(
        Sci_name = Species,
        SpecCode = SpecCode,
        ecoref = EcologyRefNo,
        herbivory = HerbivoryRef,
        feedtype = FeedingType,
        feedtyperef = FeedingTypeRef,
        diettroph = DietTroph,
        diettrophse = DietSeTroph,
        dietref = DietRef,
        dietcomment = DietRemark,
        foodref = FoodRef,
        addrems = AddRems,
        associationref = AssociationRef,
        solitarystatus = Solitary,
        schoolingstatus = Schooling,
        schoolingfrequency = SchoolingFrequency,
        schoolinglifestage = SchoolingLifestage,
        schoolingref = SchoolShoalRef,
        associationswith = AssociationsWith,
        associationcomments = AssociationsRemarks,
        habitatsref = HabitatsRef
      )

    return(ecology_summary)
}

# ecology_final <- ecology_final %>%
#   mutate(
#     trophic_class = case_when(
#       between(diettroph, 2, 2.49) ~ "Low_primary",
#       between(diettroph, 2.5, 2.99) ~  "high_primary",
#       between(diettroph, 3, 3.49) ~  "low_secondary",
#       between(diettroph, 3.5, 4)  ~ "high_secondary",
#       between(diettroph, 4, 4.49) ~  "tertiary"
#     )
