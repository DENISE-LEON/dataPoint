import io
from fastapi import APIRouter
from fastapi.responses import FileResponse, StreamingResponse
from app.core.report_manager import gen_mismatch_df, mismatch_buffer_file

router = APIRouter()

@router.get("/mismatch_reports")
async def view_mismatch_reports():
    print("[TRACE] GET /reports/mismatch_reports called")
    #this endpoint will list all existing mismatch reports in the reports folder with options to view or download
    #the front end will allow for filtering by year, team, month, etc. based on the naming convention of the reports
    return {}

@router.get("/summary_reports")
async def view_summary_reports():
    print("[TRACE] GET /reports/summary_reports called")
    #this endpoint will list all existing summary reports in the reports folder with options to view or download
    #the front end will allow for filtering by year, team, month, etc. based on the naming convention of the reports
    return {}

@router.get("/generate_mismatch_report")
async def generate_mismatch_report(year: int = None, groupBy: str = None, groupValue: str = None):
    print(f"[TRACE] GET /reports/generate_mismatch_report called | year={year} groupBy={groupBy} groupValue={groupValue}")

    df = gen_mismatch_df(year=year, groupBy=groupBy, groupValue=groupValue)
    print(f"[TRACE] gen_mismatch_df returned type={type(df)}")
    if df.empty:
        print("[TRACE] No mismatch data for provided filters")
        return {
            "status": "error",
            "message": f"No mismatches found for filters: year = {year}, groupBy = {groupBy}, groupValue = {groupValue}"
        }

    print(f"[TRACE] Returning mismatch report rows={len(df)}")
    return {
        "status": "success",
        "report": df.to_dict(orient="records")
    }

@router.get("/download")
async def download_report(
    file_ext: str,
    report_type: str,
    year: int = None,
    groupBy: str = None,
    groupValue: str = None,
    file_name: str = None,
):
    print(f"[TRACE] GET /reports/download called | report_type={report_type} year={year} groupBy={groupBy} groupValue={groupValue}")
    #add an if for ext type
    if file_ext == "xlsx" or file_ext == "pdf":
        buffer = io.BytesIO()
    else:
        buffer = io.StringIO()

    if file_name:
        base_name = file_name.strip()
    else:
        parts = [f"{report_type}_report"]
        if year is not None:
            parts.append(str(year))
        if groupBy:
            parts.append(groupBy)
        if groupValue:
            parts.append(groupValue)
        base_name = "_".join(parts)
    final_file_name = f"{base_name}.{file_ext}"

    if report_type == "mismatch":
        df = gen_mismatch_df(year=year, groupBy=groupBy, groupValue=groupValue)
        print(f"[TRACE] download mismatch df type={type(df)}")
        if df.empty:
            print("[TRACE] No data to download for mismatch report")
            return {
                "status": "error",
                "message": f"No mismatches found for filters: year = {year}, groupBy = {groupBy}, groupValue = {groupValue}"
            }
        #string io buffer to hold the csv data in memory for download without saving to disk,
        # treats the csv data as a file-like object that can be sent in the response
        media_type = mismatch_buffer_file(df, file_ext, buffer)
        #buffer is used to write the csv data in memory, and after writing, the position is at the end of the buffer.
        #buffer is also used to read the data when sending the response,
        # and it needs to be moved back to the beginning so that the entire content can be read and sent in the response.
        buffer.seek(0)  # Move the buffer position to the beginning after writing

    #add if summary report logic

        #the response includes the csv data from the buffer, sets the media type to "text/csv", and includes a content-disposition header to prompt the user to download the file with a specified filename.
        #the header is a part of the HTTP response that provides metadata about the response,
        # such as content type, content disposition, caching directives, etc.
        # In this case, the "Content-Disposition" header is used to indicate that the response should be treated as an attachment (a file to be downloaded) and specifies the filename for the download.
        #it allows you to send a response that is generated on the fly, rather than having to generate the entire response content before sending it.
        print("[TRACE] Returning streaming CSV response for mismatch report")
        return StreamingResponse(buffer, media_type=media_type, headers={"Content-Disposition": f"attachment; filename={final_file_name}"})
    # print(f"[TRACE] Unsupported report_type requested: {report_type}")

#he

@router.post("/generate_summary_report")
async def generate_summary_report(groupBy: str):
    print(f"[TRACE] POST /reports/generate_summary_report called | groupBy={groupBy}")

    #this endpoint will trigger the generation of summary reports based on the groupBy parameter (year, team, month, etc.)
    #the report generation logic will be handled in the report_manager and the generated reports will be saved in the reports folder with a naming convention that includes the groupBy value for
    #if groupBy is provided, generate reports based on that grouping, otherwise generate a general summary report
    #user can generate from curr year or select a year to generate from, same for team, month, etc.
    return {""}

# pseudo code/ plan
# the User clicks on reports
# they have options:
# view existing reports
# download existing reports
#  to generate by year, team, month, file, etc. (groupBy)
# future: reports are autogenerated on a schedule (weekly, monthly, etc.) and stored in a reports folder with the option to download or view in the app
# endpoints should be: