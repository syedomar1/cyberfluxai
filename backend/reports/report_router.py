# backend/reports/report_router.py
"""
FastAPI router to generate and download CyberFluxAI PDF reports.

Endpoints:
 - GET /report/generate?csv_filename=logs.csv&nrows=500&include_ai=false
     -> returns JSON metadata and download url
 - GET /report/download?path=<filename>
     -> returns FileResponse for previously generated PDF (from tmp_reports)
 - GET /report/direct?csv=logs.csv&nrows=500&include_ai=false
     -> returns the generated PDF file directly (one-shot)
 - GET /report/direct_debug?csv=logs.csv&include_ai=true
     -> returns the PDF or detailed JSON with traceback (for development)
"""
import os
import traceback
from dotenv import load_dotenv
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from reports.report_generator import generate_logs_report

load_dotenv()
router = APIRouter()

# tmp folder where generator writes output
TMP_DIR = os.path.join(os.path.dirname(__file__), "..", "tmp_reports")
TMP_DIR = os.path.abspath(TMP_DIR)
os.makedirs(TMP_DIR, exist_ok=True)


@router.get("/generate")
def generate_report(
    nrows: Optional[int] = Query(None, description="Optional: limit rows (dev)"),
    csv_filename: str = Query("logs.csv", description="Filename in backend/data or a full path"),
    include_ai: bool = Query(False, description="If true, call LLM summary (requires OPENAI_API_KEY)")
):
    """
    Generate a report and return JSON metadata including a download path.
    The generated PDF is stored in backend/tmp_reports.
    """
    try:
        res = generate_logs_report(csv_filename=csv_filename, nrows=nrows, include_ai=include_ai)
        pdf_path = res.get("pdf_path")
        if not pdf_path or not os.path.isfile(pdf_path):
            raise HTTPException(status_code=500, detail="PDF generation failed (no file).")

        filename = os.path.basename(pdf_path)
        download_url = f"/report/download?path={filename}"

        # Return metadata (do not expose sensitive absolute paths in normal responses)
        return JSONResponse({
            "status": "ok",
            "pdf_path": filename,
            "filename": filename,
            "num_records": res.get("num_records"),
            "suspicious_records": res.get("suspicious_records"),
            "figures": res.get("figures", []),
            "llm_trust": res.get("llm_trust", {}),
            "download": download_url
        })
    except FileNotFoundError as e:
        # clear message when CSV not found
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        # re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        # generic server error
        tb = traceback.format_exc()
        # Optionally print or log tb for dev
        print("=== Exception in /report/generate ===")
        print(tb)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download")
def download_report(path: str = Query(..., description="File name created by generate endpoint (in tmp_reports)")):
    """
    Download the generated PDF. 'path' should be the file name inside backend/tmp_reports.
    We validate that the requested file resolves inside TMP_DIR to prevent path traversal.
    """
    try:
        # Ensure path is a basename (no directories)
        filename = os.path.basename(path)
        if filename != path:
            raise HTTPException(status_code=400, detail="Invalid file path.")

        full = os.path.join(TMP_DIR, filename)
        full = os.path.abspath(full)

        # Security: confirm file sits under TMP_DIR
        if not full.startswith(TMP_DIR + os.sep):
            raise HTTPException(status_code=400, detail="Invalid download path.")

        if not os.path.isfile(full):
            raise HTTPException(status_code=404, detail=f"Report file not found: {filename}")

        return FileResponse(full, media_type="application/pdf", filename=filename)
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print("=== Exception in /report/download ===")
        print(tb)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/direct")
def get_report_direct(
    csv: str = Query("logs.csv", description="CSV filename in backend/data or absolute path"),
    include_ai: bool = Query(False, description="Include LLM-based summary (requires OPENAI_API_KEY)"),
    nrows: Optional[int] = Query(None, description="Limit rows for dev/testing")
):
    """
    Generate and immediately return the PDF as a FileResponse (no JSON metadata).
    Use this for quick single-call downloads.
    """
    try:
        meta = generate_logs_report(csv_filename=csv, nrows=nrows, include_ai=include_ai)
        pdf_path = meta.get("pdf_path")
        if not pdf_path or not os.path.isfile(pdf_path):
            raise HTTPException(status_code=500, detail="PDF not produced.")
        return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print("=== Exception in /report/direct ===")
        print(tb)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/direct_debug")
def get_report_direct_debug(
    csv: str = Query("logs.csv", description="CSV filename in backend/data or absolute path"),
    include_ai: bool = Query(False, description="Include LLM-based summary"),
    nrows: Optional[int] = Query(None, description="Limit rows for dev/testing")
):
    """
    Debug route: generates PDF, but if anything fails return full traceback in JSON.
    Use this to see the exact error without checking server console.
    """
    try:
        meta = generate_logs_report(csv_filename=csv, nrows=nrows, include_ai=include_ai)
        return FileResponse(meta["pdf_path"], media_type="application/pdf", filename=os.path.basename(meta["pdf_path"]))
    except FileNotFoundError as e:
        # For file-not-found errors, expose explicit message
        tb = traceback.format_exc()
        return JSONResponse({"error": str(e), "traceback": tb}, status_code=404)
    except Exception as e:
        tb = traceback.format_exc()
        # print to console for developer
        print("=== Exception in /report/direct_debug ===")
        print(tb)
        # Return both the message and the full traceback in the JSON for debugging
        return JSONResponse({"error": str(e), "traceback": tb}, status_code=500)
