from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from services.ocr_handler import extract_text_from_file
from services.diff_engine import generate_diff_report
from services.ai_comparator import compare_contracts_with_ai

# NEW: Import database services
from services.database import UserService, ReportService

# ============================================
# AUTH SETUP (NEW)
# ============================================
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production-VERY-IMPORTANT")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and verify JWT token, return user_id"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Pydantic models for auth
class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# ============================================
# ORIGINAL APP SETUP (UNCHANGED)
# ============================================
app = FastAPI(
    title="ClauseCompare API",
    description="AI-powered contract comparison with semantic understanding",
    version="2.0.0"
)

# Keep in-memory tracking as fallback (but will use DB now)
usage_tracker = defaultdict(lambda: {"count": 0, "month": datetime.utcnow().strftime("%Y-%m")})
MONTHLY_LIMIT = 10  # Free tier limit

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# NEW: AUTH ENDPOINTS
# ============================================
@app.post("/auth/signup")
async def signup(data: SignupRequest):
    """Create new user account"""
    try:
        # Check if user exists
        existing = await UserService.get_user_by_email(data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        password_hash = hash_password(data.password)
        user = await UserService.create_user(data.email, password_hash)
        
        # Generate token
        token = create_access_token({"sub": user["id"], "email": user["email"]})
        
        return {
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "plan": user["plan"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create account")

@app.post("/auth/login")
async def login(data: LoginRequest):
    """Login existing user"""
    try:
        user = await UserService.get_user_by_email(data.email)
        
        if not user or not verify_password(data.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = create_access_token({"sub": user["id"], "email": user["email"]})
        
        return {
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "plan": user["plan"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Failed to login")

@app.get("/auth/me")
async def get_me(user_id: str = Depends(get_current_user)):
    """Get current user info"""
    try:
        user = await UserService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user["id"],
            "email": user["email"],
            "plan": user["plan"],
            "comparisons_used": user["comparisons_used"],
            "comparisons_limit": user["comparisons_limit"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")

# ============================================
# NEW: REPORTS ENDPOINTS
# ============================================
@app.get("/reports")
async def get_reports(user_id: str = Depends(get_current_user)):
    """Get user's comparison history"""
    try:
        reports = await ReportService.get_user_reports(user_id, limit=50)
        return reports
    except Exception as e:
        print(f"Get reports error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reports")

@app.get("/reports/{report_id}")
async def get_report(report_id: str, user_id: str = Depends(get_current_user)):
    """Get specific report by ID"""
    try:
        report = await ReportService.get_report_by_id(report_id, user_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get report error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch report")

# ============================================
# ORIGINAL ENDPOINTS (KEPT AS-IS)
# ============================================
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ClauseCompare API",
        "version": "2.0.0",
        "features": ["semantic_analysis", "ai_powered", "clause_comparison"]
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_available": bool(os.getenv("GROQ_API_KEY")),
        "ai_model": "llama-3.3-70b-versatile",
        "comparison_methods": {
            "rule_based": True,
            "ai_enhanced": bool(os.getenv("GROQ_API_KEY")),
            "ai_semantic": bool(os.getenv("GROQ_API_KEY"))
        }
    }

# ============================================
# MODIFIED: /compare endpoint with AUTH
# ============================================
@app.post("/compare")
async def compare_contracts(
    fileA: UploadFile = File(..., description="First contract file (PDF, DOCX, or TXT)"),
    fileB: UploadFile = File(..., description="Second contract file (PDF, DOCX, or TXT)"),
    use_llm: Optional[str] = Form("false", description="Enhance rule-based diffs with AI explanations"),
    use_ai_full: Optional[str] = Form("true", description="Use full AI-powered semantic comparison (RECOMMENDED - default)"),
    user_id: str = Depends(get_current_user)  # CHANGED: Now requires auth token
):
    """
    Compare two contract files with semantic understanding.
    
    **AUTHENTICATION REQUIRED** - Send JWT token in Authorization header
    
    FREE TIER LIMIT: 10 comparisons per month per user.
    PRO TIER: Unlimited comparisons
    
    This endpoint performs intelligent, lawyer-grade contract comparison that focuses
    on legal meaning changes, not just text differences.
    """
    try:
        # CHANGED: Get usage from database instead of in-memory
        usage = await UserService.get_usage(user_id)
        
        # Check if user has reached limit
        if usage["used"] >= usage["limit"]:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Monthly comparison limit reached",
                    "message": f"You have used all {usage['limit']} comparisons for this month. Upgrade to Pro for unlimited comparisons.",
                    "usage": usage
                }
            )
        
        print(f"User: {user_id}, Usage: {usage['used']}/{usage['limit']}")
        
        # Validate file formats (UNCHANGED)
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
        
        # Read file contents (UNCHANGED)
        print(f"Reading files: {fileA.filename} and {fileB.filename}")
        fileA_bytes = await fileA.read()
        fileB_bytes = await fileB.read()
        
        # Check file sizes (10MB limit) (UNCHANGED)
        max_size = 10 * 1024 * 1024
        if len(fileA_bytes) > max_size:
            raise HTTPException(
                status_code=413, 
                detail=f"fileA too large: {len(fileA_bytes) / 1024 / 1024:.1f}MB (max 10MB)"
            )
        if len(fileB_bytes) > max_size:
            raise HTTPException(
                status_code=413, 
                detail=f"fileB too large: {len(fileB_bytes) / 1024 / 1024:.1f}MB (max 10MB)"
            )
        
        print(f"File sizes: A={len(fileA_bytes)} bytes, B={len(fileB_bytes)} bytes")
        
        # Extract text from files (UNCHANGED)
        print("Extracting text from fileA...")
        try:
            text_a = extract_text_from_file(fileA_bytes, fileA.filename)
            print(f"Extracted {len(text_a)} characters from fileA")
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Error processing fileA: {str(e)}"
            )
        
        print("Extracting text from fileB...")
        try:
            text_b = extract_text_from_file(fileB_bytes, fileB.filename)
            print(f"Extracted {len(text_b)} characters from fileB")
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Error processing fileB: {str(e)}"
            )
        
        # Validate extracted text (UNCHANGED)
        if not text_a.strip():
            raise HTTPException(
                status_code=400, 
                detail="fileA appears to be empty or unreadable. Please check the file."
            )
        if not text_b.strip():
            raise HTTPException(
                status_code=400, 
                detail="fileB appears to be empty or unreadable. Please check the file."
            )
        
        # Choose comparison method (UNCHANGED)
        use_ai_full_bool = use_ai_full.lower() == "true"
        use_llm_bool = use_llm.lower() == "true"
        
        report = None
        comparison_method = "Rule-Based"
        
        # PRIMARY METHOD: AI Semantic Analysis (UNCHANGED)
        if use_ai_full_bool:
            print("=" * 60)
            print("Using AI-powered semantic comparison (RECOMMENDED method)")
            print("=" * 60)
            
            try:
                report = compare_contracts_with_ai(text_a, text_b)
                comparison_method = "AI-Powered Semantic Analysis"
                
                diff_count = len(report.get('diffs', []))
                print(f"✓ AI semantic comparison successful!")
                print(f"✓ Found {diff_count} meaningful differences")
                print(f"✓ Risk Score: {report.get('riskScore', 0)}/100")
                
            except Exception as e:
                print(f"✗ AI comparison failed: {str(e)}")
                print("→ Falling back to rule-based comparison...")
                
                report = generate_diff_report(text_a, text_b)
                comparison_method = "Rule-Based (AI Fallback)"
                use_llm_bool = False
                
                print(f"✓ Rule-based comparison completed")
                print(f"✓ Found {len(report.get('diffs', []))} differences")
        
        # ALTERNATIVE METHOD: Rule-Based Comparison (UNCHANGED)
        else:
            print("=" * 60)
            print("Using rule-based comparison")
            print("=" * 60)
            
            report = generate_diff_report(text_a, text_b)
            comparison_method = "Rule-Based"
            
            print(f"✓ Rule-based comparison completed")
            print(f"✓ Found {len(report.get('diffs', []))} differences")
            
            if use_llm_bool:
                print("→ Enhancing with AI explanations...")
                try:
                    from services.llm_explainer import enhance_diffs_with_explanations
                    report["diffs"] = enhance_diffs_with_explanations(report["diffs"], use_llm=True)
                    comparison_method = "Rule-Based + AI Explanations"
                    print("✓ AI explanations added successfully")
                except Exception as e:
                    print(f"✗ AI enhancement failed: {str(e)}")
                    print("→ Continuing with template explanations")
        
        # Add metadata (UNCHANGED)
        timestamp = datetime.utcnow().isoformat() + "Z"
        report_id = f"rpt-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        diffs = report.get("diffs", [])
        type_counts = {
            "Added": sum(1 for d in diffs if d.get('type') == 'Added'),
            "Removed": sum(1 for d in diffs if d.get('type') == 'Removed'),
            "Modified": sum(1 for d in diffs if d.get('type') == 'Modified'),
            "Reworded": sum(1 for d in diffs if d.get('type') == 'Reworded')
        }
        
        severity_counts = {
            "High": sum(1 for d in diffs if d.get('severity') == 'High'),
            "Medium": sum(1 for d in diffs if d.get('severity') == 'Medium'),
            "Low": sum(1 for d in diffs if d.get('severity') == 'Low')
        }
        
        # Build response (UNCHANGED structure)
        response = {
            "reportId": report_id,
            "riskScore": report.get("riskScore", 0),
            "summary": report.get("summary", ""),
            "riskReport": report.get("riskReport", ""),
            "verdict": report.get("verdict", ""),
            "diffs": diffs,
            "usage": usage,  # CHANGED: Now from database
            "metadata": {
                "createdAt": timestamp,
                "fileA": fileA.filename,
                "fileB": fileB.filename,
                "comparisonMethod": comparison_method,
                "llmUsed": use_llm_bool or use_ai_full_bool,
                "diffCount": len(diffs),
                "typeBreakdown": type_counts,
                "severityBreakdown": severity_counts
            }
        }
        
        # NEW: Save report to database
        try:
            await ReportService.save_report(user_id, response)
            print(f"✓ Report saved to database: {report_id}")
        except Exception as e:
            print(f"⚠ Warning: Failed to save report to database: {e}")
            # Don't fail the request if database save fails
        
        # NEW: Increment usage counter in database
        try:
            updated_usage = await UserService.increment_usage(user_id)
            response["usage"] = updated_usage
            print(f"✓ Usage incremented: {updated_usage['used']}/{updated_usage['limit']}")
        except Exception as e:
            print(f"⚠ Warning: Failed to increment usage: {e}")
        
        print("=" * 60)
        print(f"✓ Report generated successfully: {report_id}")
        print(f"✓ Total differences: {len(diffs)}")
        print(f"✓ High risk: {severity_counts['High']}, Medium: {severity_counts['Medium']}, Low: {severity_counts['Low']}")
        print("=" * 60)
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Unexpected error in /compare: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# ============================================
# ORIGINAL ENDPOINTS (UNCHANGED)
# ============================================
@app.get("/methods")
async def comparison_methods():
    """Get available comparison methods and their descriptions"""
    ai_available = bool(os.getenv("GROQ_API_KEY"))
    
    methods = {
        "ai-semantic": {
            "name": "AI Semantic Analysis",
            "description": "Understands legal meaning, not just words. Detects substantive vs cosmetic changes. RECOMMENDED for accurate results.",
            "available": ai_available,
            "requires_api_key": True,
            "speed": "Medium (5-15 seconds)",
            "accuracy": "Excellent (95%+)",
            "features": [
                "Semantic understanding",
                "Rewording detection",
                "Specific measurements",
                "Legal meaning focus",
                "Clause matching by similarity"
            ]
        },
        "rule-based-enhanced": {
            "name": "Rule-Based + AI Explanations",
            "description": "Fast pattern matching enhanced with AI-generated explanations",
            "available": ai_available,
            "requires_api_key": True,
            "speed": "Fast (2-5 seconds)",
            "accuracy": "Very Good (90%)",
            "features": [
                "Fast pattern matching",
                "AI explanations",
                "Negotiation suggestions"
            ]
        },
        "rule-based": {
            "name": "Rule-Based Only",
            "description": "Fast, deterministic comparison using predefined rules and patterns",
            "available": True,
            "requires_api_key": False,
            "speed": "Very Fast (1-2 seconds)",
            "accuracy": "Good (85%)",
            "features": [
                "No API key required",
                "Fast processing",
                "Template explanations"
            ]
        }
    }
    
    return {
        "methods": methods,
        "recommended": "ai-semantic" if ai_available else "rule-based",
        "ai_provider": "Groq (LLaMA 3.3 70B)" if ai_available else None,
        "default_method": "ai-semantic"
    }

@app.get("/stats")
async def get_stats():
    """Get API statistics and capabilities"""
    return {
        "api_version": "2.0.0",
        "supported_formats": ["PDF", "DOCX", "DOC", "TXT"],
        "max_file_size_mb": 10,
        "max_files_per_request": 2,
        "ai_enabled": bool(os.getenv("GROQ_API_KEY")),
        "ai_model": "llama-3.3-70b-versatile",
        "features": {
            "semantic_analysis": bool(os.getenv("GROQ_API_KEY")),
            "clause_comparison": True,
            "risk_scoring": True,
            "ai_explanations": bool(os.getenv("GROQ_API_KEY")),
            "negotiation_suggestions": True,
            "summary_generation": True,
            "verdict_generation": True,
            "rewording_detection": bool(os.getenv("GROQ_API_KEY")),
            "legal_meaning_focus": bool(os.getenv("GROQ_API_KEY"))
        },
        "change_types_detected": ["Added", "Removed", "Modified", "Reworded"],
        "risk_levels": ["High", "Medium", "Low"]
    }

@app.get("/ping")
async def ping():
    """Simple ping endpoint for uptime monitoring"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
