from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime
from typing import Optional

from services.ocr_handler import extract_text_from_file
from services.diff_engine import generate_diff_report
from services.llm_explainer import enhance_diffs_with_explanations


app = FastAPI(
    title="ClauseCompare API",
    description="Contract comparison API for ClauseCompare",
    version="1.0.0"
)

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ClauseCompare API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "llm_available": bool(os.getenv("OPENAI_API_KEY"))
    }


@app.post("/compare")
async def compare_contracts(
    fileA: UploadFile = File(..., description="First contract file (PDF, DOCX, or TXT)"),
    fileB: UploadFile = File(..., description="Second contract file (PDF, DOCX, or TXT)"),
    use_llm: Optional[str] = Form("false", description="Whether to use LLM explanations")
):
    """
    Compare two contract files and return structured diff report.
    
    Args:
        fileA: First contract file
        fileB: Second contract file
        use_llm: "true" or "false" to enable LLM-powered explanations
    
    Returns:
        JSON report with diffs, risk score, and explanations
    """
    try:
        # Validate file formats
        allowed_extensions = ['pdf', 'docx', 'doc', 'txt']
        
        fileA_ext = fileA.filename.lower().split('.')[-1]
        fileB_ext = fileB.filename.lower().split('.')[-1]
        
        if fileA_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format for fileA: {fileA_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        if fileB_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format for fileB: {fileB_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file contents
        fileA_bytes = await fileA.read()
        fileB_bytes = await fileB.read()
        
        # Check file sizes (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(fileA_bytes) > max_size:
            raise HTTPException(status_code=413, detail=f"fileA too large (max 10MB)")
        if len(fileB_bytes) > max_size:
            raise HTTPException(status_code=413, detail=f"fileB too large (max 10MB)")
        
        # Extract text from files
        try:
            text_a = extract_text_from_file(fileA_bytes, fileA.filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing fileA: {str(e)}")
        
        try:
            text_b = extract_text_from_file(fileB_bytes, fileB.filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing fileB: {str(e)}")
        
        # Validate extracted text
        if not text_a.strip():
            raise HTTPException(status_code=400, detail="fileA appears to be empty or unreadable")
        if not text_b.strip():
            raise HTTPException(status_code=400, detail="fileB appears to be empty or unreadable")
        
        # Generate diff report
        report = generate_diff_report(text_a, text_b)
        
        # Enhance with explanations
        use_llm_bool = use_llm.lower() == "true"
        report["diffs"] = enhance_diffs_with_explanations(report["diffs"], use_llm=use_llm_bool)
        
        # Add metadata
        timestamp = datetime.utcnow().isoformat() + "Z"
        report_id = f"rpt-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        response = {
            "reportId": report_id,
            "riskScore": report["riskScore"],
            "diffs": report["diffs"],
            "createdAt": timestamp,
            "fileA": fileA.filename,
            "fileB": fileB.filename,
            "llmUsed": use_llm_bool
        }
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in /compare: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
