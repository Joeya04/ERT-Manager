############################################################
# excel_exporter.py
#
# Build Excel workbook
#
############################################################

from pathlib import Path

import pandas as pd


def export_excel_workbook(

        raw_df,

        formatted_df,

        fishbase_df,

        statistics_df,

        output_directory

):

    """
    Create a multi-sheet workbook.

    Returns
    -------
    str
        Path to workbook
    """

    output_file = Path(

        output_directory

    ) / "Analysis_Summary.xlsx"

    with pd.ExcelWriter(

            output_file,

            engine="openpyxl"

    ) as writer:

        ####################################################
        # Raw data
        ####################################################

        if raw_df is not None:

            raw_df.to_excel(

                writer,

                sheet_name="Raw Data",

                index=False

            )

        ####################################################
        # Formatted data
        ####################################################

        if formatted_df is not None:

            formatted_df.to_excel(

                writer,

                sheet_name="Formatted Data",

                index=False

            )

        ####################################################
        # FishBase
        ####################################################

        if fishbase_df is not None:

            fishbase_df.to_excel(

                writer,

                sheet_name="FishBase",

                index=False

            )

        ####################################################
        # Statistics
        ####################################################

        if statistics_df is not None:

            statistics_df.to_excel(

                writer,

                sheet_name="Statistics",

                index=False

            )

    return str(output_file)