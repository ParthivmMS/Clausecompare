from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime
from typing import Optional

from services.ocr_handler import extract_text_from_file
from services.diff_engine import generate_diff_report
from services.ai_comparator import compare_contracts_with_ai


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
        "ai_available": bool(os.getenv("GROQ_API_KEY")),
        "comparison_methods": ["rule-based", "ai-enhanced", "ai-full"]
    }


@app.post("/compare")
async def compare_contracts(
    fileA: UploadFile = File(..., description="First contract file (PDF, DOCX, or TXT)"),
    fileB: UploadFile = File(..., description="Second contract file (PDF, DOCX, or TXT)"),
    use_llm: Optional[str] = Form("false", description="Enhance rule-based diffs with AI explanations"),
    use_ai_full: Optional[str] = Form("false", description="Use full AI-powered comparison (recommended)")
):
    """
    Compare two contract files and return structured diff report.
    
    Args:
        fileA: First contract file
        fileB: Second contract file
        use_llm: "true" to enhance rule-based diffs with AI explanations
        use_ai_full: "true" to use full AI-powered comparison (most accurate)
    
    Returns:
        JSON report with diffs, risk score, summary, verdict, and explanations
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
        
        # Choose comparison method
        use_ai_full_bool = use_ai_full.lower() == "true"
        use_llm_bool = use_llm.lower() == "true"
        
        # Initialize report variable
        report = None
        comparison_method = "Rule-Based"
        
        if use_ai_full_bool:
            # Use full AI-powered comparison
            print("Using full AI-powered comparison...")
            try:
                report = compare_contracts_with_ai(text_a, text_b)
                comparison_method = "AI-Powered (Full)"
                print(f"AI comparison successful. Found {len(report.get('diffs', []))} differences")
            except Exception as e:
                print(f"AI comparison failed: {str(e)}")
                print("Falling back to rule-based comparison...")
                # Fallback to rule-based
                report = generate_diff_report(text_a, text_b)
                comparison_method = "Rule-Based (AI Fallback)"
                use_llm_bool = False
        else:
            # Use rule-based comparison
            print("Using rule-based comparison...")
            report = generate_diff_report(text_a, text_b)
            comparison_method = "Rule-Based"
            
            # Optionally enhance with AI explanations
            if use_llm_bool:
                print("Enhancing with AI explanations...")
                try:
                    from services.llm_explainer import enhance_diffs_with_explanations
                    report["diffs"] = enhance_diffs_with_explanations(report["diffs"], use_llm=True)
                    comparison_method = "Rule-Based + AI Explanations"
                except Exception as e:
                    print(f"AI enhancement failed: {str(e)}")
                    # Continue with rule-based results
        
        # Add metadata
        timestamp = datetime.utcnow().isoformat() + "Z"
        report_id = f"rpt-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Build response
        response = {
            "reportId": report_id,
            "riskScore": report.get("riskScore", 0),
            "summary": report.get("summary", ""),
            "riskReport": report.get("riskReport", ""),
            "verdict": report.get("verdict", ""),
            "diffs": report.get("diffs", []),
            "createdAt": timestamp,
            "fileA": fileA.filename,
            "fileB": fileB.filename,
            "comparisonMethod": comparison_method,
            "llmUsed": use_llm_bool or use_ai_full_bool,
            "diffCount": len(report.get("diffs", []))
        }
        
        print(f"Successfully generated report {report_id} with {response['diffCount']} differences")
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in /compare: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/methods")
async def comparison_methods():
    """
    Get available comparison methods and their descriptions
    """
    ai_available = bool(os.getenv("GROQ_API_KEY"))
    
    methods = {
        "rule-based": {
            "name": "Rule-Based Comparison",
            "description": "Fast, deterministic comparison using predefined rules and patterns",
            "available": True,
            "requires_api_key": False,
            "speed": "Fast",
            "accuracy": "Good"
        },
        "ai-enhanced": {
            "name": "Rule-Based + AI Explanations",
            "description": "Rule-based comparison enhanced with AI-generated explanations",
            "available": ai_available,
            "requires_api_key": True,
            "speed": "Medium",
            "accuracy": "Very Good"
        },
        "ai-full": {
            "name": "Full AI-Powered Comparison",
            "description": "Complete AI analysis with clause-by-clause comparison and risk assessment",
            "available": ai_available,
            "requires_api_key": True,
            "speed": "Slower",
            "accuracy": "Excellent"
        }
    }
    
    return {
        "methods": methods,
        "recommended": "ai-full" if ai_available else "rule-based",
        "ai_provider": "Groq (LLaMA 3.3)" if ai_available else None
    }


@app.get("/stats")
async def get_stats():
    """
    Get API statistics and capabilities
    """
    return {
        "api_version": "1.0.0",
        "supported_formats": ["PDF", "DOCX", "DOC", "TXT"],
        "max_file_size_mb": 10,
        "max_files_per_request": 2,
        "ai_enabled": bool(os.getenv("GROQ_API_KEY")),
        "ai_model": "llama-3.3-70b-versatile",
        "features": {
            "clause_comparison": True,
            "risk_scoring": True,
            "ai_explanations": bool(os.getenv("GROQ_API_KEY")),
            "negotiation_suggestions": True,
            "summary_generation": True,
            "verdict_generation": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
