
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
def validate_file(header, row):
    if not header: 
        return False, "Missing header row."
    
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in header]
    if missing_columns:
        valid, result = clean_header(header, missing_columns)
        if not valid:
            return valid, result
        header = result

    try:
        before = int(row["No of Records Before"])
        after = int(row["No of Records After"])
        expected_deleted = int(row["Expected Records Deleted"])
        actual_deleted = int(row["Actual Records Deleted"])

    except ValueError:
        invalid_rows = [row for row in row if not all(isinstance(row[col], int) for col in ["No of Records Before", "No of Records After", "Expected Records Deleted", "Actual Records Deleted"])]
        valid, message = clean_row(invalid_rows)
        return valid, message
    return True, "File is valid."
    
    #add a cleaner method for missing columns(incase user used a different name for the column), invalid data types(incase user spelled out integer), or empty cells.

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
    user_input = input("Would you like to correct the invalid data? (yes/no):")
    if user_input.lower() == "yes":
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
    else: 
        return False, f"File could not be processed due to invalid data types. Please correct the data and try again."

#mismatch creator
