from fastapi import FastAPI, UploadFile, File, Form #for handling file uploads and form data
from fastapi.middleware.cors import CORSMiddleware #cross origin resource sharing
import json
import shutil
from pathlib import Path
import pandas as pd
from .core.dataManager import validate_file, input_docs, approved_docs, output_docs, process_file, migrate_approved_files

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], #allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],

)

@app.post("/validate")
async def validate_endpoint(
    file: UploadFile = File(...), 
    mappings: str = Form(None), 
    row_correction: str = Form(None),
    new_file_name: str = Form(None)
):
    # 1. Parse the stringified JSON from React back into Python dictionaries
    parsed_mappings = json.loads(mappings) if mappings else None
    parsed_corrections = json.loads(row_correction) if row_correction else None
    parse_new_file_name = json.loads(new_file_name) if new_file_name else None

    # 2. Save the uploaded file temporarily so pandas can read it
    input_docs.mkdir(parents=True, exist_ok=True)
    file_path = input_docs / file.filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Read the file using Pandas to get headers and rows
    try:
        header, rows = process_file(file_path)
    except Exception as e:
        return {"status": "error", "error": f"Failed to read file: {str(e)}"}

    # 4. Call your decoupled validation logic
    result_dict = validate_file(file.filename, header, rows, parsed_mappings, parsed_corrections)

    # 5. If successful, migrate the file directly from the router!
    if result_dict.get("status") == "success":
        approved_docs.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file_path), str(approved_docs / file.filename))

    # 6. Return the dictionary back to React (whether it requires mapping, fixes, or success)
    return result_dict
