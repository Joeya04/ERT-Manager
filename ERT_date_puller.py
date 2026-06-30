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
