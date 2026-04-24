
from pathlib import Path
import csv
import pandas as pd

input_docs = Path("input_docs")
approved_docs = Path("approved_docs")
output_docs = Path("output_docs")

#doc validate + clean -> approved_docs

#helpers
REQUIRED_COLUMNS = [
    "Table Name", 
    "No of Records Before", 
    "No of Records After", 
    "Expected Records Deleted", 
    "Actual Records Deleted"]

#file validation
def validate_file(file_name, header, rows):
    if not header: 
        return False, "Missing header row."
    
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in header]
    if missing_columns:
        valid, result = clean_header(header, missing_columns)
        if not valid:
            return valid, result
        header = result

    invalid_rows = []
    for row in rows:
        try:
            before = int(row["No of Records Before"])
            after = int(row["No of Records After"])
            expected_deleted = int(row["Expected Records Deleted"])
            actual_deleted = int(row["Actual Records Deleted"])

        except ValueError:
            invalid_rows.append(row)

    if invalid_rows:
        valid, message = clean_row(invalid_rows)
        return valid, message
    
    extract_team_and_month(file_name)

    return True, "File is valid."
    
    #add a cleaner method for missing columns(incase user used a different name for the column), invalid data types(incase user spelled out integer), or empty cells.

def extract_team_and_month(file_name):
    parts = file_name.split("_")
    if len(parts) >= 2:
        team = parts[0]
        month = parts[1].split(".")[0]
    else:
        new_team, new_month = clean_file_name(file_name)
        team = new_team
        month = new_month
    return team, month

#cleaners
def clean_header(header, missing_columns):
    print(f"Missing required columns: {', '.join(missing_columns)}")
    if input("Did you use a different name for the column? (yes/no):") != "yes":
        return False, f"File could not be processed. Please update your file to include the required columns: {', '.join(missing_columns)}"

    header_map = {}
    for expected in missing_columns:
        actual = input(f"Enter the file column name for '{expected}': ")
        if actual in header:
            header_map[actual] = expected #key = actual column name, value = expected column name
        else:
            print(f"Column '{actual}' not found in header.")

    cleaned_header = [header_map.get(col, col) for col in header]
    return True, cleaned_header
    
def clean_row(invalid_rows):
    print(f"Integer expected. Invalid value for row: {invalid_rows}")
    if input("Would you like to correct the invalid data? (yes/no):").lower() != "yes":
        return False, f"File could not be processed due to invalid data types. Please correct the data and try again."

    for row in invalid_rows:
        for col in ["No of Records Before", "No of Records After", "Expected Records Deleted", "Actual Records Deleted"]:
            user_input = input(f"Please enter a valid integer for '{col}' in row {row}: ")
            try:
                int_value = int(user_input)
                row[col] = int_value
            except ValueError:
                print(f"Invalid input. '{user_input}' is not an integer. Please try again.")
                return False, f"File could not be processed due to invalid data types. Please correct the data and try again."
        return True, "Data cleaned successfully."

def clean_file_name(file_name):
    print(f"File {file_name} name does not match expected format:'TeamName_Month.ext'.")
    if input("Would you like to rename the file? (yes/no):").lower() != "yes":
        return "Unknown Team", "Unknown Month"
    new_file_name = input("Please enter the new file name (format: 'TeamName_Month.ext'): ")
    return extract_team_and_month(new_file_name)

def process_file(): 
    for file_path in input_docs.glob("*"):
        if file_path.suffix.lower() in [".csv", ".txt"]:
            df = pd.read_csv(file_path, sep=None, engine="python")
        elif file_path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        else:
            print(f"{file_path.name}: Unsupported file format.")
            continue

        header = df.columns.tolist()
        rows = df.to_dict("records")
        valid, message = validate_file(file_path.name, header, rows)
        print(f"{file_path.name}: {message}")
