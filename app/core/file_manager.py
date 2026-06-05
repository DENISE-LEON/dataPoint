import datetime
from pathlib import Path
import pandas as pd
from app.models.valid_file import file_model, df_to_pydantic, mappings_to_pydantic_header, validate_pydantic_model, required_aliases
from datetime import datetime
import openpyxl
from openpyxl.reader.excel import load_workbook

input_docs = Path("input_docs")

def validate_file(file_name, df, mappings=None, row_correction=None, new_file_name=None):
    print(f"[TRACE] validate_file started | file_name={file_name} | new_file_name={new_file_name}")
    if new_file_name:
        file_name = new_file_name
        print(f"[TRACE] Using renamed file_name={file_name}")

    team, month, year = extract_team_month_year(file_name)
    print(f"[TRACE] Extracted filename parts | team={team} month={month} year={year}")
    if not team or not month or not year:
        print("[ERROR] Filename format invalid: expected team_month_year.ext")
        return {
            "status": "requires valid _team_month_year",
            "error": "Filename must be in the format team_month_year.ext (e.g., sales_january_2024.csv)."
        }
    #add format validation
    try:
        valid_month = datetime.strptime(month, "%B").month
        print(f"[TRACE] Valid month parsed | month={valid_month}")
    except (ValueError, TypeError, OverflowError):
        valid_month = None
        print(f"[ERROR] Invalid month value: {month}")
        return {
            "status": "requires valid month",
            "error": f"Month '{month}' is not valid. Please provide a valid month name (e.g., January)."
        }

    try:
        valid_year = datetime.strptime(year, "%Y").year
        print(f"[TRACE] Valid year parsed | year={valid_year}")
    except (ValueError, TypeError, OverflowError):
        valid_year = None
        print(f"[ERROR] Invalid year value: {year}")
        return {
            "status": "requires valid year",
            "error": f"Year '{year}' is not valid. Please provide a valid year (e.g., 2024)."
        }

    if valid_year < 2000 or valid_year > datetime.now().year + 1:
        print(f"[ERROR] Year out of acceptable range: {valid_year}")
        return {
            "status": "requires valid year range",
            "error": f"Year '{valid_year}' is out of acceptable range. Please provide a year between 2000 and {datetime.now().year + 1}."
        }

    header, rows = df_to_pydantic(df)
    print(f"[TRACE] Converted dataframe to rows | header_count={len(header)} row_count={len(rows)}")
    actual_header = header
    if mappings:
        actual_header = [mappings[col] if col in mappings else col for col in header]
        rows = mappings_to_pydantic_header(mappings, rows)
        print(f"[TRACE] Applied mappings | mapped_header_count={len(actual_header)}")

    if not header:
        print("[ERROR] Missing header row in uploaded file")
        return {
            "status": "error",
            "error": "Missing header row."
        }

    missing = [f for f in required_aliases if f not in actual_header]
    if missing:
        print(f"[TRACE] Missing required fields detected | missing={missing}")
        return {
            "status": "requires_mappings",
            "missing_fields": missing,
            "actual_fields": actual_header
        }

    corrections = row_correction.get("corrections", {}) if row_correction else {}
    for index, row in enumerate(rows):
        if row_correction and index == row_correction.get("index"):
            print(f"[TRACE] Applying row corrections at index={index} | keys={list(corrections.keys())}")
            for col, new_val in corrections.items():
                row[col] = new_val

    invalid_rows = validate_pydantic_model(rows)
    print(f"[TRACE] Pydantic validation complete | invalid_row_count={len(invalid_rows)}")

    if invalid_rows:
        print("[TRACE] Returning row fix requirements")
        return {
            "status": "requires_row_fixes",
            "invalid_rows": invalid_rows
        }

    print("[TRACE] validate_file success")
    return {
        "status": "success",
        "message": "File is valid and has been moved to approved documents.",
        "file_name": file_name,
        "file_month": valid_month,
        "file_year": valid_year,
        "header": actual_header,
        "rows": rows
    }

def extract_team_month_year(file_name):
    print(f"[TRACE] extract_team_month_year called | file_name={file_name}")
    parts = file_name.split("_")
    if len(parts) >= 3:
        team = parts[0].strip()
        month = parts[1].strip()
        year = parts[2].strip().split(".")[0]
        print(f"[TRACE] Filename parts extracted | team={team} month={month} year={year}")
    else:
        team = None
        month = None
        year = None
        print("[ERROR] Filename does not contain expected parts separated by underscores")

    return team, month, year

#used in the file validation endpoint to read the file into a dataframe
def process_file(file_path):
    print(f"[TRACE] process_file called | file_path={file_path}")
    path_obj = Path(file_path)
    if path_obj.suffix.lower() in [".csv", ".txt"]:
        df = pd.read_csv(path_obj, sep=None, engine="python")
        print(f"[TRACE] Delimited file read successfully | rows={len(df)} columns={len(df.columns)}")
    elif path_obj.suffix.lower() in [".xlsx", ".xls"]:
        try:
            df = pd.read_excel(path_obj, engine="openpyxl")
            print(f"[TRACE] Excel file read successfully | rows={len(df)} columns={len(df.columns)}")
        except Exception as e:
            print(f"[ERROR] Failed reading Excel file {path_obj.name}: {str(e)}")
            raise ValueError(f"Error reading Excel file {path_obj.name}: {e}")
    else:
        print(f"[ERROR] Unsupported file format: {path_obj.suffix}")
        raise ValueError(f"Unsupported file format for file {path_obj.name}.")

    print("[TRACE] process_file returning dataframe")
    return df