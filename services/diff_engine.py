import difflib
import re
from typing import List, Dict, Tuple


def segment_clauses(text: str) -> List[Dict[str, str]]:
    """
    Segment contract text into clauses based on headings and blank lines.
    Returns list of clause dictionaries with title and content.
    """
    clauses = []
    lines = text.split('\n')
    current_clause = {"title": "", "content": ""}
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines between clauses
        if not stripped:
            if current_clause["content"]:
                clauses.append(current_clause)
                current_clause = {"title": "", "content": ""}
            continue
        
        # Detect headings (all caps, ends with colon, or numbered)
        is_heading = (
            stripped.isupper() and len(stripped) < 100 or
            stripped.endswith(':') or
            re.match(r'^\d+\.?\s+[A-Z]', stripped)
        )
        
        if is_heading and not current_clause["content"]:
            current_clause["title"] = stripped
        else:
            current_clause["content"] += stripped + " "
    
    # Add last clause
    if current_clause["content"]:
        clauses.append(current_clause)
    
    # If no clauses detected, treat whole text as one clause
    if not clauses:
        clauses = [{"title": "Document", "content": text}]
    
    return clauses


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts using difflib"""
    return difflib.SequenceMatcher(None, text1, text2).ratio()


def match_clauses(clauses_a: List[Dict], clauses_b: List[Dict]) -> List[Tuple]:
    """
    Match clauses between two contracts based on similarity.
    Returns list of tuples: (clause_a_idx, clause_b_idx, similarity)
    """
    matches = []
    used_b = set()
    
    for i, clause_a in enumerate(clauses_a):
        best_match = None
        best_similarity = 0.0
        
        for j, clause_b in enumerate(clauses_b):
            if j in used_b:
                continue
            
            # Compare both title and content
            title_sim = calculate_similarity(clause_a["title"], clause_b["title"])
            content_sim = calculate_similarity(clause_a["content"], clause_b["content"])
            
            # Weighted similarity
            similarity = title_sim * 0.3 + content_sim * 0.7
            
            if similarity > best_similarity and similarity > 0.3:
                best_similarity = similarity
                best_match = j
        
        if best_match is not None:
            matches.append((i, best_match, best_similarity))
            used_b.add(best_match)
    
    return matches


def detect_risk_patterns(old_text: str, new_text: str, clause_title: str) -> Tuple[str, str]:
    """
    Detect risk patterns in clause changes using heuristics.
    Returns (severity, risk_type)
    """
    old_lower = old_text.lower()
    new_lower = new_text.lower()
    title_lower = clause_title.lower()
    
    # High-risk patterns
    high_risk_keywords = [
        'confidentiality', 'indemnity', 'liability', 'intellectual property',
        'termination', 'non-compete', 'arbitration', 'warranty'
    ]
    
    # Check if this is a high-risk clause type
    is_high_risk_clause = any(keyword in title_lower for keyword in high_risk_keywords)
    
    # Detect specific changes
    if 'confidentiality' in title_lower or 'confidential' in old_lower:
        if extract_years(new_text) < extract_years(old_text):
            return ("High", "Confidentiality period reduced")
    
    if 'payment' in title_lower or 'fee' in old_lower:
        old_amounts = extract_amounts(old_text)
        new_amounts = extract_amounts(new_text)
        if new_amounts and old_amounts and new_amounts[0] > old_amounts[0]:
            return ("High", "Payment amount increased")
    
    if 'liability' in title_lower or 'indemnif' in old_lower:
        if 'unlimited' in new_lower and 'unlimited' not in old_lower:
            return ("High", "Liability cap removed")
    
    if 'termination' in title_lower:
        old_notice = extract_days(old_text)
        new_notice = extract_days(new_text)
        if new_notice < old_notice:
            return ("Medium", "Termination notice period reduced")
    
    # General severity based on similarity
    similarity = calculate_similarity(old_text, new_text)
    
    if similarity < 0.5 and is_high_risk_clause:
        return ("High", "Significant change to critical clause")
    elif similarity < 0.7 and is_high_risk_clause:
        return ("Medium", "Moderate change to critical clause")
    elif similarity < 0.5:
        return ("Medium", "Significant change")
    else:
        return ("Low", "Minor change")


def extract_years(text: str) -> int:
    """Extract number of years from text (e.g., '5 years' -> 5)"""
    match = re.search(r'(\d+)\s*year', text.lower())
    return int(match.group(1)) if match else 999


def extract_days(text: str) -> int:
    """Extract number of days from text (e.g., '30 days' -> 30)"""
    match = re.search(r'(\d+)\s*day', text.lower())
    return int(match.group(1)) if match else 999


def extract_amounts(text: str) -> List[float]:
    """Extract dollar amounts from text (e.g., '$1,000' -> [1000.0])"""
    matches = re.findall(r'\$\s*([\d,]+(?:\.\d{2})?)', text)
    return [float(m.replace(',', '')) for m in matches]


def generate_diff_report(text_a: str, text_b: str) -> Dict:
    """
    Generate comprehensive diff report between two contract texts.
    Returns structured report with diffs, risk scores, and metadata.
    """
    # Segment both contracts into clauses
    clauses_a = segment_clauses(text_a)
    clauses_b = segment_clauses(text_b)
    
    # Match clauses between contracts
    matches = match_clauses(clauses_a, clauses_b)
    
    diffs = []
    total_risk = 0
    
    # Process matched clauses (modified)
    for idx_a, idx_b, similarity in matches:
        clause_a = clauses_a[idx_a]
        clause_b = clauses_b[idx_b]
        
        # Only report if there's meaningful difference
        if similarity < 0.95:
            severity, risk_type = detect_risk_patterns(
                clause_a["content"],
                clause_b["content"],
                clause_a["title"] or clause_b["title"]
            )
            
            # Calculate risk contribution
            risk_value = {"High": 30, "Medium": 15, "Low": 5}[severity]
            total_risk += risk_value
            
            diff_entry = {
                "clause": clause_a["title"] or clause_b["title"] or "Unnamed Clause",
                "summary": generate_summary(clause_a["content"], clause_b["content"], risk_type),
                "oldText": clause_a["content"][:500],  # Truncate for brevity
                "newText": clause_b["content"][:500],
                "severity": severity,
                "explanation": "",  # Will be filled by LLM or template
                "confidence": round(similarity * 100, 1)
            }
            
            diffs.append(diff_entry)
    
    # Process removed clauses (in A but not in B)
    matched_a = {idx_a for idx_a, _, _ in matches}
    for i, clause in enumerate(clauses_a):
        if i not in matched_a and clause["content"].strip():
            diffs.append({
                "clause": clause["title"] or "Removed Clause",
                "summary": "This clause was removed from the new version.",
                "oldText": clause["content"][:500],
                "newText": "",
                "severity": "Medium",
                "explanation": "",
                "confidence": 100.0
            })
            total_risk += 15
    
    # Process added clauses (in B but not in A)
    matched_b = {idx_b for _, idx_b, _ in matches}
    for i, clause in enumerate(clauses_b):
        if i not in matched_b and clause["content"].strip():
            diffs.append({
                "clause": clause["title"] or "Added Clause",
                "summary": "This is a new clause added in the new version.",
                "oldText": "",
                "newText": clause["content"][:500],
                "severity": "Medium",
                "explanation": "",
                "confidence": 100.0
            })
            total_risk += 15
    
    # Calculate overall risk score (0-100)
    risk_score = min(100, total_risk)
    
    return {
        "riskScore": risk_score,
        "diffs": diffs
    }


def generate_summary(old_text: str, new_text: str, risk_type: str) -> str:
    """Generate human-readable summary of the change"""
    old_words = len(old_text.split())
    new_words = len(new_text.split())
    
    if abs(old_words - new_words) > 20:
        if new_words > old_words:
            return f"{risk_type}. Clause expanded with additional terms."
        else:
            return f"{risk_type}. Clause shortened, some terms removed."
    
    return f"{risk_type}. Wording and terms have been modified."
