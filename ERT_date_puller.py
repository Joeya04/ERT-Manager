from openpyxl import load_workbook
import pandas as pd
from datetime import datetime

file_path = "your_file.xlsx"
wb = load_workbook(file_path)

START_ROW = 5

BLUE = "FF0000FF"
GREEN = "FF00FF00"


def normalize_color(rgb):
    if rgb is None:
        return None
    return rgb[-8:]


def parse_date(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    try:
        return datetime.strptime(str(value), "%m/%d/%Y")
    except ValueError:
        return None


records = []

# ---- LOOP THROUGH ALL SHEETS ----
for ws in wb.worksheets:

    sheet_name = ws.title

    # ---- LOOP THROUGH COLUMNS ----
    for col in ws.iter_cols():

        col_id = col[0].column_letter

        state = "idle"
        start_date = None

        # ---- SCAN ROWS ----
        for cell in col[START_ROW - 1:]:

            fill = cell.fill
            if not fill or fill.fill_type != "solid":
                continue

            color = normalize_color(fill.start_color.rgb)
            date = parse_date(cell.value)

            if not date:
                continue

            # ---- START EVENT ----
            if color == BLUE:
                start_date = date
                state = "started"

            # ---- STOP EVENT ----
            elif color == GREEN and state == "started":
                stop_date = date

                records.append({
                    "sheet": sheet_name,
                    "entity": col_id,
                    "start_date": start_date,
                    "stop_date": stop_date,
                    "duration_days": (stop_date - start_date).days
                })

                state = "idle"
                start_date = None


# ---- BUILD DATAFRAME ----
df = pd.DataFrame(records)

print(df)

from openpyxl import load_workbook
from datetime import datetime
import pandas as pd
import re

# =====================================================
# USER SETTINGS
# =====================================================

FILE_PATH = r"C:\YourFolder\your_workbook.xlsx"

START_ROW = 5

# Update these to match your workbook colors.
# Print cell.fill.start_color.rgb once if you're unsure.
BLUE = "FF0000FF"
GREEN = "FF00FF00"

OUTPUT_FILE = "Event_Durations.xlsx"

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def normalize_color(rgb):
    """
    Converts Excel ARGB colors into a consistent format.
    """

    if rgb is None:
        return None

    return rgb[-8:]


def parse_date(value):
    """
    Converts an Excel cell into a datetime object.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    try:
        return datetime.strptime(str(value), "%m/%d/%Y")
    except ValueError:
        return None


def sheet_prefix(sheet_name):
    """
    Examples

    Site A          -> SA
    North Pond      -> NP
    Upper River     -> UR
    Study Site 2    -> SS2
    """

    words = re.findall(r"[A-Za-z0-9]+", sheet_name)

    return "".join(word[0].upper() for word in words)


# =====================================================
# LOAD WORKBOOK
# =====================================================

wb = load_workbook(FILE_PATH)

records = []

# =====================================================
# PROCESS EVERY WORKSHEET
# =====================================================

for ws in wb.worksheets:

    sheet_name = ws.title
    prefix = sheet_prefix(sheet_name)

    print(f"Processing {sheet_name}")

    # --------------------------------------------
    # Each column is one individual
    # --------------------------------------------

    for person_num, col in enumerate(ws.iter_cols(), start=1):

        entity_id = f"{prefix}{person_num}"

        state = "idle"
        start_date = None

        # ----------------------------------------
        # Scan downward beginning at START_ROW
        # ----------------------------------------

        for cell in col[START_ROW - 1:]:

            fill = cell.fill

            if fill is None:
                continue

            if fill.fill_type != "solid":
                continue

            color = normalize_color(fill.start_color.rgb)

            date = parse_date(cell.value)

            if date is None:
                continue

            # ------------------------------------
            # BLUE = START EVENT
            # ------------------------------------

            if color == BLUE:

                start_date = date
                state = "started"

            # ------------------------------------
            # GREEN = STOP EVENT
            # ------------------------------------

            elif color == GREEN and state == "started":

                stop_date = date

                duration_days = (stop_date - start_date).days

                yearfrac = duration_days / 365.25

                records.append({

                    "sheet": sheet_name,

                    "entity_id": entity_id,

                    "start_date": start_date,

                    "stop_date": stop_date,

                    "duration_days": duration_days,

                    "yearfrac": yearfrac

                })

                # Ready for another interval

                state = "idle"
                start_date = None


# =====================================================
# CREATE DATAFRAME
# =====================================================

df = pd.DataFrame(records)

# Optional: sort output

df = df.sort_values(
    by=["sheet", "entity_id", "start_date"]
).reset_index(drop=True)

print(df)

# =====================================================
# SAVE OUTPUT
# =====================================================

df.to_excel(OUTPUT_FILE, index=False)

print(f"\nFinished! Output saved to {OUTPUT_FILE}")