#Loads modules
from openpyxl import load_workbook
from datetime import datetime
import pandas as pd
import re


#Inputs
FILE_PATH = r"C:\Users\jgasink\Desktop\ERT Project\Working Copies\Species_ERT_Workbook_7-1-26.xlsx"

START_ROW = 26

GREEN = "#FFE2EFDA"
RED = "#FFFFCCCC"

OUTPUT_FILE = r"C:\Users\jgasink\Desktop\ERT Project\Python\ERT_Translated.xlsx"

#Optional allowlist of sheet names to process. Leave empty to process all sheets.
SHEETS_TO_PROCESS = ["Jolthead Porgy", "Saucereye Porgy", "Sheepshead Porgy"]


#Helper functions 
#Normalizes color to 8 digit ARGB hex code (e.g. #AARRGGBB)
def normalize_color(rgb):

    if rgb is None:
        return None

    if isinstance(rgb, str):
        value = rgb.strip().upper()
        return value if value.startswith("#") else f"#{value}"

    if hasattr(rgb, "rgb") and rgb.rgb:
        value = str(rgb.rgb).strip().upper()
        return value if value.startswith("#") else f"#{value}"

    if hasattr(rgb, "type") and getattr(rgb, "type") == "rgb":
        value = str(getattr(rgb, "value", "")).strip().upper()
        return value if value.startswith("#") else f"#{value}"

    return str(rgb).upper()

#Converts an Excel cell into a datetime object
def parse_date(value):

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    try:
        return datetime.strptime(str(value), "%m/%d/%Y")
    except ValueError:
        return None

#Resolves a cell date, including Census year handling for green and red cells.
def get_cell_date(value, color, start_date=None):

    census_match = re.search(r"census\s*(\d{4})", str(value or ""), flags=re.I)

    if census_match:
        year = int(census_match.group(1))

        if color == GREEN:
            return datetime.strptime(f"12/31/{year}", "%m/%d/%Y")

        if color == RED:
            if start_date is not None and start_date.year == year:
                year_end = datetime.strptime(f"12/31/{year}", "%m/%d/%Y")
                return start_date + (year_end - start_date) / 2

            return datetime.strptime(f"12/31/{year}", "%m/%d/%Y")

    return parse_date(value)

#Pulls the first letter of each word in a sheet name and returns it as a string (Collects Species Name)
def sheet_prefix(sheet_name):


    words = re.findall(r"[A-Za-z0-9]+", sheet_name)

    return "".join(word[0].upper() for word in words)


wb = load_workbook(FILE_PATH)

records = []

#Loads the workbook and iterates through each worksheet, processing each column to extract start and stop dates based on cell fill colors. 
#It collects the data into a list of records, which is then converted into a DataFrame and saved to an Excel file.
allowed_sheets = {name.strip().casefold() for name in SHEETS_TO_PROCESS if name and name.strip()}

for ws in wb.worksheets:

    sheet_name = ws.title

    if allowed_sheets and sheet_name.strip().casefold() not in allowed_sheets:
        print(f"Skipping {sheet_name}")
        continue

    prefix = sheet_prefix(sheet_name)

    print(f"Processing {sheet_name}")



    active_person_num = 0

    for col in ws.iter_cols():

        state = "idle"
        start_date = None
        column_record = None
        had_activity = False
        entity_id = f"{prefix}{active_person_num + 1}"

        #Scans the fill color of each cell in the column starting from START_ROW. If a cell is filled with GREEN, it marks the start date. 
        #If a cell is filled with RED and a start date has been recorded, it marks the stop date and calculates the duration in days and year fraction. 
        #The results are stored as one record per column/individual.
        for cell in col[START_ROW - 1:]:

            fill = cell.fill

            if fill is None:
                continue

            if fill.fill_type != "solid":
                continue

            color = normalize_color(getattr(fill.fgColor, "rgb", None))
            if color is None:
                color = normalize_color(getattr(fill.start_color, "rgb", None))

            date = get_cell_date(cell.value, color, start_date if state == "started" else None)

            if date is None:
                continue

            had_activity = True

            #Green indicates the addition of a fish/individual to the GOT (start_date)
            if color == GREEN:

                start_date = date
                state = "started"

            #If green was found ("started") and red is found, it indicated the death/disappearance/removal of that individual from the GOT
            elif color == RED and state == "started":

                stop_date = date

                duration_days = (stop_date - start_date).days

                yearfrac = duration_days / 365.25

                column_record = {

                    "sheet": sheet_name,

                    "entity_id": entity_id,

                    "start_date": start_date,

                    "stop_date": stop_date,

                    "duration_days": duration_days,

                    "yearfrac": yearfrac,

                    "status": "completed"

                }

                # Ready for another interval

                state = "idle"
                start_date = None

        if not had_activity:
            continue

        active_person_num += 1

        if column_record is not None:
            column_record["entity_id"] = entity_id
            records.append(column_record)
        elif state == "started" and start_date is not None:
            records.append({

                "sheet": sheet_name,

                "entity_id": entity_id,

                "start_date": start_date,

                "stop_date": None,

                "duration_days": None,

                "yearfrac": None,

                "status": "still alive"

            })


expected_columns = ["sheet", "entity_id", "start_date", "stop_date", "duration_days", "yearfrac", "status"]

df = pd.DataFrame(records, columns=expected_columns)

if not df.empty:
    df = df.sort_values(
        by=["sheet", "entity_id", "start_date"]
    ).reset_index(drop=True)
else:
    df = df.reset_index(drop=True)

print(df)


df.to_excel(OUTPUT_FILE, index=False)

print(f"\nFinished! Output saved to {OUTPUT_FILE}")