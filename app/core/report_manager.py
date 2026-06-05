from datetime import datetime
from pathlib import Path
import app.config as cfg
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.file_manager import extract_team_month_year
from xhtml2pdf import pisa  #for PDF generation

scheduler = BackgroundScheduler()
reports = Path("reports")
mismatch_reports = reports / Path("mismatch_reports")

def generate_scheduled_reports():
    print("[TRACE] generate_scheduled_reports called")
    year = datetime.now().year
    month = datetime.now().month
    groupBy = 'Month'
    print(f"[TRACE] Scheduling jobs | year={year} month={month} groupBy={groupBy}")
    scheduler.add_job(
        save_mismatch_report,
        'cron', month = '1', day = '1', hour = '0', minute = '0',
        args=[year, None, None],
        id = "annual_mismatch_report",
        replace_existing=True
        )

    scheduler.add_job(
        save_mismatch_report,
        'cron', year = year, month = month, day = '1', hour = '0', minute = '0',
        args=[year, None, groupBy],
        id = "monthly_mismatch_report",
        replace_existing=True
    )
    print("[TRACE] Scheduler jobs added")
    #add test schdule job
    # scheduler.add_job(lambda: print("[TRACE] Test scheduled job executed"), 'interval', seconds=30)
    # print("[TRACE] Test scheduled job added to run every 30 seconds")


#save either mismatch or summary report, the report type will come from
#seperate save methods bc they take seperate arguments for saving
#only used for scheduled reports
def save_mismatch_report(year = None, groupValue = None, groupBy = None):
    mismatch_reports.mkdir(parents=True, exist_ok=True)
    print(f"[TRACE] save_mismatch_report called | year={year} groupBy={groupBy} groupValue={groupValue}")
    df = gen_mismatch_df(year, groupBy, groupValue)
    print(f"[TRACE] Mismatch dataframe generated | rows={len(df)}")
    df.to_csv(mismatch_reports / f"mismatch_report_{groupBy}_{groupValue}_{year}.csv", index=False)
    print(f"[TRACE] Mismatch report written to disk | path={mismatch_reports / f'mismatch_report_{groupBy}_{groupValue}_{year}.csv'}")


def gen_mismatch_df(year = None, groupBy = None, groupValue = None):
    print(f"[TRACE] gen_mismatch_df called | year={year} groupBy={groupBy} groupValue={groupValue}")
    report_type = "mismatch"
    df = load_files(year)
    print(f"[TRACE] Source dataframe loaded | rows={len(df)}")

    if df.empty:
        print("[TRACE] No source records found for mismatch report")
        return pd.DataFrame()

    mismatches = calculate_delta(df)
    print(f"[TRACE] Delta calculation complete | mismatch_rows={len(mismatches)}")

    # if year:
    #     report = mismatch_reports / f"mismatch_report_{year}.csv"

    if groupBy and groupValue:
        print(f"[TRACE] Applying mismatch filter | groupBy={groupBy} groupValue={groupValue}")
        return mismatches[mismatches[groupBy] == groupValue]

    print("[TRACE] Returning all mismatches")
    return mismatches, report_type


def load_files(year = None):
    print(f"[TRACE] load_files called | year={year}")
    if year:
        files = list((cfg.approved_docs/str(year)).glob("*.csv"))
    else:
        files = list(cfg.approved_docs.glob("**/*.csv"))
    print(f"[TRACE] CSV files discovered | count={len(files)}")
    if not files:
        print("[TRACE] No files found in approved_docs")
        return pd.DataFrame()
    dfs = []
    for file in files:
        print(f"[TRACE] Reading approved file: {file}")
        team, month, file_year = extract_team_month_year(file.name)
        df = pd.read_csv(file)
        df['Team'] = team
        df['Month'] = month
        df['Year'] = file_year
        dfs.append(df)
    print(f"[TRACE] Concatenating dataframes | parts={len(dfs)}")
    return pd.concat(dfs, ignore_index=True)


def calculate_delta(df):
    print("[TRACE] calculate_delta called")
    df['Delta'] = df['Expected Records Deleted'] - df['Actual Records Deleted']
    mismatches = df[df['Delta'] != 0]
    print(f"[TRACE] calculate_delta complete | mismatch_rows={len(mismatches)}")
    return mismatches

# helper method for saving as file ext based on file extention
def mismatch_buffer_file(df, file_ext, buffer):
    print(f"[TRACE] mismatch_buffer_file called | file_ext={file_ext} df_rows={len(df)}")
    try:
        if file_ext == "csv":
            print("[TRACE] Writing CSV format to buffer")
            df.to_csv(buffer, index=False)
            print("[TRACE] CSV write successful")
            return "text/csv"
        if file_ext == "xlsx":
            print("[TRACE] Writing XLSX format to buffer")
            df.to_excel(buffer, index=False, engine='openpyxl')
            print("[TRACE] XLSX write successful")
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if file_ext == "pdf":
            print("[TRACE] Converting dataframe to HTML for PDF conversion")
            html = df.to_html(index=False)
            print("[TRACE] Writing PDF format to buffer")
            pisa.CreatePDF(html, dest=buffer)
            print("[TRACE] PDF write successful")
            return "application/pdf"
        print(f"[ERROR] Unsupported file format: {file_ext}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to write {file_ext} to buffer: {str(e)}")
        raise