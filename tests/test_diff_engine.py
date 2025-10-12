import pytest
from services.diff_engine import (
    extract_years, extract_days, extract_amounts, extract_state,
    detect_risk_patterns, segment_clauses, generate_diff_report
)


def test_extract_years():
    """Test year extraction from text"""
    assert extract_years("confidentiality for 5 years") == 5
    assert extract_years("term of two (2) years") == 2
    assert extract_years("no years mentioned") == 999


def test_extract_days():
    """Test day extraction from text"""
    assert extract_days("notice of 60 days") == 60
    assert extract_days("within thirty (30) days") == 30
    assert extract_days("no days mentioned") == 999


def test_extract_amounts():
    """Test amount extraction from text"""
    amounts = extract_amounts("fee of $10,000")
    assert 10000.0 in amounts
    
    amounts = extract_amounts("Fifteen Thousand Dollars ($15,000)")
    assert 15000.0 in amounts


def test_extract_state():
    """Test state name extraction"""
    assert extract_state("laws of Delaware") == "Delaware"
    assert extract_state("California jurisdiction") == "California"
    assert extract_state("no state mentioned") == ""


def test_confidentiality_period_reduction():
    """Test detection of confidentiality period reduction"""
    old = "confidentiality obligations for a period of five (5) years"
    new = "confidentiality obligations for a period of one (1) year"
    
    severity, risk_type = detect_risk_patterns(old, new, "Confidentiality Period")
    
    assert severity == "High"
    assert "reduced" in risk_type.lower()
    assert "5" in risk_type
    assert "1" in risk_type


def test_termination_notice_reduction():
    """Test detection of termination notice reduction"""
    old = "terminate with sixty (60) days written notice"
    new = "terminate with thirty (30) days written notice"
    
    severity, risk_type = detect_risk_patterns(old, new, "Termination")
    
    assert severity == "High"
    assert "reduced" in risk_type.lower()


def test_payment_increase():
    """Test detection of payment increase"""
    old = "fee of Ten Thousand Dollars ($10,000) within 30 days"
    new = "fee of Fifteen Thousand Dollars ($15,000) within 15 days"
    
    severity, risk_type = detect_risk_patterns(old, new, "Payment Terms")
    
    assert severity == "High"
    assert "increased" in risk_type.lower()


def test_liability_cap_removal():
    """Test detection of liability cap removal"""
    old = "liability of One Hundred Thousand Dollars ($100,000)"
    new = "unlimited liability for willful misconduct"
    
    severity, risk_type = detect_risk_patterns(old, new, "Indemnification")
    
    assert severity == "High"
    assert "unlimited" in risk_type.lower() or "removed" in risk_type.lower()


def test_non_compete_addition():
    """Test detection of non-compete clause"""
    old = ""
    new = "During the term and for two (2) years thereafter, the Receiving Party agrees not to compete"
    
    severity, risk_type = detect_risk_patterns(old, new, "Non-Compete Clause")
    
    assert severity == "High"
    assert "non-compete" in risk_type.lower()


def test_governing_law_change():
    """Test detection of governing law change"""
    old = "governed by the laws of Delaware"
    new = "governed by the laws of California"
    
    severity, risk_type = detect_risk_patterns(old, new, "Governing Law")
    
    assert severity == "Medium"
    assert "Delaware" in risk_type
    assert "California" in risk_type


def test_clause_segmentation():
    """Test clause segmentation"""
    text = """
1. CONFIDENTIALITY
This is the confidentiality clause.

2. PAYMENT TERMS
This is the payment clause.

3. TERMINATION
This is the termination clause.
    """
    
    clauses = segment_clauses(text)
    
    assert len(clauses) >= 3
    titles = [c["title"] for c in clauses]
    assert any("CONFIDENTIALITY" in t for t in titles)
    assert any("PAYMENT" in t for t in titles)


def test_full_report_generation():
    """Test full diff report generation"""
    contract_a = """
1. CONFIDENTIALITY
Confidential information shall be protected for 5 years.

2. PAYMENT
Fee of $10,000 within 30 days.
    """
    
    contract_b = """
1. CONFIDENTIALITY
Confidential information shall be protected for 1 year.

2. PAYMENT
Fee of $15,000 within 15 days.
    """
    
    report = generate_diff_report(contract_a, contract_b)
    
    assert "riskScore" in report
    assert "diffs" in report
    assert "summary" in report
    assert "verdict" in report
    
    # Should detect both high-risk changes
    assert report["riskScore"] > 50
    assert len(report["diffs"]) >= 2
    
    # Check for high-risk diffs
    high_risk_diffs = [d for d in report["diffs"] if d["severity"] == "High"]
    assert len(high_risk_diffs) >= 2


def test_risk_score_calculation():
    """Test that risk scores are reasonable"""
    # Identical contracts
    text = "This is a simple contract."
    report = generate_diff_report(text, text)
    assert report["riskScore"] == 0
    
    # Minor change
    text_a = "Payment of $1000"
    text_b = "Payment of $1001"
    report = generate_diff_report(text_a, text_b)
    assert report["riskScore"] < 30
    
    # Major changes
    text_a = "Confidentiality for 5 years, liability cap $100,000"
    text_b = "Confidentiality for 1 year, unlimited liability"
    report = generate_diff_report(text_a, text_b)
    assert report["riskScore"] > 60
