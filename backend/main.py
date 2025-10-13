# backend/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from reports.report_router import router as report_router
from reports.report_generator import generate_logs_report

load_dotenv()
app = FastAPI(title="CyberFluxAI Report API")
origins = [
    "http://localhost:3000",            # local dev frontend
    "https://your-frontend.vercel.app", # Vercel frontend (set your actual URL)
    # "http://127.0.0.1:3000"           # optionally
]
# CORS (allow frontend during dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # in production, restrict to your frontend URL(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register modular router (already provides /report/generate and /report/download)
app.include_router(report_router, prefix="/report", tags=["Reports"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/report_direct", response_class=FileResponse)
def report_direct(
    csv_filename: str = Query("logs.csv", description="CSV file name inside backend/data/"),
    nrows: int | None = Query(None, ge=1, description="Optional: read only first n rows (dev)"),
):
    """
    Convenience endpoint for development:
    - Calls generate_logs_report(csv_filename=..., nrows=...)
    - Returns the PDF as a FileResponse for download.
    NOTE: For production, use /report/generate (modular router).
    """
    try:
        result = generate_logs_report(csv_filename=csv_filename, nrows=nrows)
        pdf_path = result.get("pdf_path")
        if not pdf_path or not os.path.isfile(pdf_path):
            raise HTTPException(status_code=500, detail="Report generation failed or file missing.")
        filename = os.path.basename(pdf_path)
        return FileResponse(pdf_path, media_type="application/pdf", filename=filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # return a JSON with error info for debugging
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
