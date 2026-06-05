from fastapi import APIRouter, UploadFile, File, Form, HTTPException  #for handling file uploads and form data
from fastapi.middleware.cors import CORSMiddleware  #cross origin resource sharing
import json
import shutil
import pandas as pd
from app.core.file_manager import validate_file, input_docs, process_file
from app.models.valid_file import file_model
import app.config as cfg

router = APIRouter()

@router.get("/")
async def root():
    print("[TRACE] GET /files/ called")
    return {"message": "Welcome to the File Validation API!"}  #what is returned to the user

@router.post("/validate")
async def validate_endpoint(
    input_file: UploadFile = File(...),
    mappings: str = Form(None),
    row_correction: str = Form(None),
    new_file_name: str = Form(None)
):
    print(f"[TRACE] POST /files/validate called | filename={input_file.filename} | new_file_name={new_file_name}")
    # Parse optional JSON form fields and fail as a client error, not an internal server error.
    try:
        parsed_mappings = json.loads(mappings) if mappings else None
        parsed_corrections = json.loads(row_correction) if row_correction else None
        print("[TRACE] JSON form fields parsed successfully")
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in form fields: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON in form fields: {str(e)}")

    file_name = new_file_name if new_file_name else input_file.filename

    input_docs.mkdir(parents=True, exist_ok=True)
    old_file_path = input_docs / input_file.filename
    file_path = input_docs / file_name
    print(f"[TRACE] Input directory ready | target_path={file_path}")

    #create a copy of the uploaded file with the new name if provided, otherwise use the original name
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(input_file.file, buffer)
    print(f"[TRACE] Uploaded file saved to disk: {file_path}")

    #read file and convert to data frame to be used for pydantic validation
    try:
        df = process_file(file_path)
        print(f"[TRACE] File processed to dataframe | rows={len(df)} | columns={len(df.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to read uploaded file: {str(e)}")
        return {"status": "error", "error": f"Failed to read file: {str(e)}"}

    #file components extraction and validation
    try:
        result_dict = validate_file(file_name, df, parsed_mappings, parsed_corrections, new_file_name)
        print(f"[TRACE] File validation completed | status={result_dict.get('status')}")
    except (AttributeError, TypeError, KeyError) as e:
        print(f"[ERROR] Invalid mappings/row correction payload: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid mappings or row_correction structure: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Unexpected validation failure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected validation failure: {str(e)}")

    # If validation is successful, move the file to the approved_docs directory and clean up the input_docs directory.
    if result_dict.get("status") == "success":
        cfg.approved_docs.mkdir(parents=True, exist_ok=True)
        final_file_name = result_dict.get("file_name", file_name)
        print(f"[TRACE] Validation success | writing approved file={final_file_name}")
        try:
            cleaned_df = pd.DataFrame(result_dict["rows"], columns=result_dict["header"])
            years = result_dict.get("file_year")
            approved_years_dir = cfg.approved_docs / str(years)
            approved_years_dir.mkdir(parents=True, exist_ok=True)
            cleaned_df.to_csv(approved_years_dir / final_file_name, index=False)
            print(f"[TRACE] Approved file written: {approved_years_dir / final_file_name}")
        except Exception as e:
            print(f"[ERROR] Failed while writing approved file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed while writing approved file: {str(e)}")

        try:
            file_path.unlink(missing_ok=True)
            old_file_path.unlink(missing_ok=True)
            print("[TRACE] Input temp files cleaned up")
        except PermissionError as e:
            print(f"[ERROR] Failed to delete input file because it is in use: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete input file because it is in use: {str(e)}")
        except Exception as e:
            print(f"[ERROR] Failed to delete input file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete input file: {str(e)}")

    print(f"[TRACE] Returning validation response | status={result_dict.get('status')}")
    return result_dict

#add function to view prev submitted files in the approved_docs directory, with optional filtering by year, team, month, etc.