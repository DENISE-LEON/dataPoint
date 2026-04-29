from pathlib import Path
import csv
import pandas as pd
import shutil
import os

input_docs = Path("input_docs")
approved_docs = Path("approved_docs")
output_docs = Path("output_docs")
mismatch_reports = output_docs / Path("mismatch_reports")

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
    
    extract_team_month_year(file_name)

    return True, "File is valid."
    
    #add a cleaner method for missing columns(incase user used a different name for the column), invalid data types(incase user spelled out integer), or empty cells.

def extract_team_month_year(file_name):
    parts = file_name.split("_")
    if len(parts) >= 3:
        team = parts[0]
        month = parts[1]
        year = parts[2].split(".")[0]
    else:
        new_team, new_month, new_year = clean_file_name(file_name)
        team = new_team
        month = new_month
        year = new_year
    return team, month, year

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
        return "Unknown Team", "Unknown Month", "Unknown Year"
    new_file_name = input("Please enter the new file name (format: 'TeamName_Month.ext'): ")
    return extract_team_month_year(new_file_name)

#process + migrate
def process_file(): 
    results = {}
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
        results[file_path.name] = (valid, message)
        print(f"{file_path.name}: {message}")
    return results

def migrate_approved_files():
    results = process_file()
    approved_docs.mkdir(parents=True, exist_ok=True)
    for source_file in input_docs.glob("*"):
        if source_file.is_file() and results[source_file.name][0]: #check if file was processed and is valid
            shutil.move(str(source_file), str(approved_docs))    
            print(f"{source_file.name} moved to {approved_docs}.")
        else:
            print(f"{source_file.name} not moved due to validation failure or processing error.")
    
#add helper method to load the data for reporting and analysis
def load_data():
    files = list(approved_docs.glob("*"))
    if not files:
        print("No approved files found. Please validate and clean your files first.")
        return pd.DataFrame() #return empty dataframe if no approved files
    return pd.concat([pd.read_csv(file) if file.suffix.lower() in [".csv", ".txt"] else pd.read_excel(file) for file in files], ignore_index=True)


#writer functions
def gen_mismatch_report(groupBy):
    mismatch_reports.mkdir(parents=True, exist_ok=True)
    
    df = load_data()
    if df.empty:
        print("No data available to generate mismatch report.")
        return

    df['delta'] = df['Expected Records Deleted'] - df['Actual Records Deleted']
    mismatches = df[df['delta']!=0]

    for group_value, group in mismatches.groupby(groupBy):
        output_file = mismatch_reports/ f"mismatch_report_{group_value}.csv"
        group.to_csv(output_file, index = False)
    
#notes
    