import pytest
from fastapi.testclient import TestClient
from main import app
import io


client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ClauseCompare API"


def test_compare_with_text_files():
    """Test /compare endpoint with simple text files"""
    # Create sample contract texts
    contract_a = """
CONFIDENTIALITY AGREEMENT

1. CONFIDENTIAL INFORMATION
The receiving party agrees to maintain confidentiality for a period of 5 years.

2. PAYMENT TERMS
Payment of $10,000 shall be made within 30 days.

3. TERMINATION
Either party may terminate with 60 days written notice.
"""
    
    contract_b = """
CONFIDENTIALITY AGREEMENT

1. CONFIDENTIAL INFORMATION
The receiving party agrees to maintain confidentiality for a period of 1 year.

2. PAYMENT TERMS
Payment of $15,000 shall be made within 15 days.

3. TERMINATION
Either party may terminate with 30 days written notice.
"""
    
    # Create file-like objects
    file_a = ("contract_a.txt", io.BytesIO(contract_a.encode()), "text/plain")
    file_b = ("contract_b.txt", io.BytesIO(contract_b.encode()), "text/plain")
    
    response = client.post(
        "/compare",
        files={
            "fileA": file_a,
            "fileB": file_b
        },
        data={"use_llm": "false"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "reportId" in data
    assert "riskScore" in data
    assert "diffs" in data
    assert "createdAt" in data
    assert isinstance(data["diffs"], list)
    assert data["riskScore"] >= 0 and data["riskScore"] <= 100
    
    # Verify diffs have required fields
    if len(data["diffs"]) > 0:
        diff = data["diffs"][0]
        assert "clause" in diff
        assert "summary" in diff
        assert "oldText" in diff
        assert "newText" in diff
        assert "severity" in diff
        assert "explanation" in diff
        assert "confidence" in diff


def test_compare_identical_files():
    """Test comparing identical files returns minimal diffs"""
    contract = "This is a simple contract with standard terms."
    
    file_a = ("contract.txt", io.BytesIO(contract.encode()), "text/plain")
    file_b = ("contract.txt", io.BytesIO(contract.encode()), "text/plain")
    
    response = client.post(
        "/compare",
        files={
            "fileA": file_a,
            "fileB": file_b
        },
        data={"use_llm": "false"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["riskScore"] == 0 or data["riskScore"] < 10


def test_compare_missing_file():
    """Test error handling when file is missing"""
    file_a = ("contract.txt", io.BytesIO(b"test"), "text/plain")
    
    response = client.post(
        "/compare",
        files={"fileA": file_a},
        data={"use_llm": "false"}
    )
    
    assert response.status_code == 422  # FastAPI validation error


def test_compare_invalid_file_format():
    """Test error handling for invalid file formats"""
    file_a = ("contract.exe", io.BytesIO(b"test"), "application/octet-stream")
    file_b = ("contract.txt", io.BytesIO(b"test"), "text/plain")
    
    response = client.post(
        "/compare",
        files={
            "fileA": file_a,
            "fileB": file_b
        },
        data={"use_llm": "false"}
    )
    
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]


def test_compare_empty_file():
    """Test error handling for empty files"""
    file_a = ("empty.txt", io.BytesIO(b""), "text/plain")
    file_b = ("contract.txt", io.BytesIO(b"Some content"), "text/plain")
    
    response = client.post(
        "/compare",
        files={
            "fileA": file_a,
            "fileB": file_b
        },
        data={"use_llm": "false"}
    )
    
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_compare_with_llm_flag():
    """Test that use_llm parameter is respected"""
    contract_a = "Confidentiality: 5 years"
    contract_b = "Confidentiality: 1 year"
    
    file_a = ("a.txt", io.BytesIO(contract_a.encode()), "text/plain")
    file_b = ("b.txt", io.BytesIO(contract_b.encode()), "text/plain")
    
    response = client.post(
        "/compare",
        files={
            "fileA": file_a,
            "fileB": file_b
        },
        data={"use_llm": "true"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "llmUsed" in data
