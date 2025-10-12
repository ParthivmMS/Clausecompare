import difflib
import re
from typing import List, Dict, Tuple


def segment_clauses(text: str) -> List[Dict[str, str]]:
    """
    Segment contract text into clauses with improved detection.
    Handles numbered sections, headings, and subsections better.
    """
    clauses = []
    lines = text.split('\n')
    current_clause = {"title": "", "content": "", "number": ""}
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
        
        # Detect numbered headings (1., 2., etc. or 1. HEADING)
        numbered_heading = re.match(r'^(\d+)\.\s*([A-Z][A-Z\s]+)$', stripped)
        if numbered_heading:
            if current_clause["content"]:
                clauses.append(current_clause.copy())
            current_clause = {
                "title": stripped,
                "content": "",
                "number": numbered_heading.group(1)
            }
            continue
        
        # Detect all-caps headings
        if stripped.isupper() and len(stripped) > 3 and len(stripped) < 100:
            if current_clause["content"]:
                clauses.append(current_clause.copy())
            current_clause = {"title": stripped, "content": "", "number": ""}
            continue
        
        # Detect headings ending with colon
        if stripped.endswith(':') and len(stripped) < 100:
            if current_clause["content"]:
                clauses.append(current_clause.copy())
            current_clause = {"title": stripped, "content": "", "number": ""}
            continue
        
        # Add to current clause content
        current_clause["content"] += stripped + " "
    
    # Add last clause
    if current_clause["content"]:
        clauses.append(current_clause)
    
    # If no clauses detected, treat whole text as one clause
    if not clauses:
        clauses = [{"title": "Document", "content": text, "number": ""}]
    
    return clauses


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts using difflib"""
    if not text1 or not text2:
        return 0.0
    return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def match_clauses(clauses_a: List[Dict], clauses_b: List[Dict]) -> List[Tuple]:
    """
    Match clauses between two contracts with improved matching.
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
            
            # Match by number first (if available)
            if clause_a.get("number") and clause_b.get("number"):
                if clause_a["number"] == clause_b["number"]:
                    best_match = j
                    best_similarity = 0.9  # High similarity for number match
                    break
            
            # Match by title similarity
            title_sim = calculate_similarity(clause_a["title"], clause_b["title"])
            content_sim = calculate_similarity(clause_a["content"], clause_b["content"])
            
            # Weighted similarity (title more important for matching)
            similarity = title_sim * 0.5 + content_sim * 0.5
            
            if similarity > best_similarity and similarity > 0.2:
                best_similarity = similarity
                best_match = j
        
        if best_match is not None:
            # Recalculate content similarity for matched clauses
            content_similarity = calculate_similarity(
                clauses_a[i]["content"], 
                clauses_b[best_match]["content"]
            )
            matches.append((i, best_match, content_similarity))
            used_b.add(best_match)
    
    return matches


def extract_numbers(text: str, pattern: str) -> List[int]:
    """Extract numbers matching a pattern from text"""
    matches = re.findall(pattern, text.lower())
    return [int(m) for m in matches if m.isdigit()]


def extract_years(text: str) -> int:
    """Extract number of years from text"""
    # Match patterns like "5 years", "five (5) years", etc.
    matches = re.findall(r'(\d+)\s*year', text.lower())
    if matches:
        return int(matches[0])
    return 999  # Default high value if not found


def extract_days(text: str) -> int:
    """Extract number of days from text"""
    matches = re.findall(r'(\d+)\s*day', text.lower())
    if matches:
        return int(matches[0])
    return 999


def extract_months(text: str) -> int:
    """Extract number of months from text"""
    matches = re.findall(r'(\d+)\s*month', text.lower())
    if matches:
        return int(matches[0])
    return 999


def extract_amounts(text: str) -> List[float]:
    """Extract dollar amounts from text"""
    # Match $10,000 or $10000 or Ten Thousand Dollars
    matches = re.findall(r'\$\s*([\d,]+(?:\.\d{2})?)', text)
    amounts = [float(m.replace(',', '')) for m in matches]
    
    # Also match written numbers
    text_amounts = {
        'thousand': 1000,
        'million': 1000000,
        'hundred thousand': 100000
    }
    
    text_lower = text.lower()
    for word, value in text_amounts.items():
        if word in text_lower:
            number_match = re.search(rf'(\w+)\s+{word}', text_lower)
            if number_match:
                word_to_num = {
                    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                    'fifteen': 15, 'twenty': 20, 'fifty': 50, 'hundred': 100
                }
                word_num = word_to_num.get(number_match.group(1), 1)
                amounts.append(word_num * value)
    
    return amounts


def extract_state(text: str) -> str:
    """Extract US state name from text"""
    states = [
        'alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado',
        'connecticut', 'delaware', 'florida', 'georgia', 'hawaii', 'idaho',
        'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana',
        'maine', 'maryland', 'massachusetts', 'michigan', 'minnesota',
        'mississippi', 'missouri', 'montana', 'nebraska', 'nevada',
        'new hampshire', 'new jersey', 'new mexico', 'new york',
        'north carolina', 'north dakota', 'ohio', 'oklahoma', 'oregon',
        'pennsylvania', 'rhode island', 'south carolina', 'south dakota',
        'tennessee', 'texas', 'utah', 'vermont', 'virginia', 'washington',
        'west virginia', 'wisconsin', 'wyoming'
    ]
    
    text_lower = text.lower()
    for state in states:
        if state in text_lower:
            return state.title()
    return ""


def detect_risk_patterns(old_text: str, new_text: str, clause_title: str) -> Tuple[str, str]:
    """
    Enhanced risk pattern detection with specific checks for common contract changes.
    Returns (severity, risk_type)
    """
    old_lower = old_text.lower()
    new_lower = new_text.lower()
    title_lower = clause_title.lower()
    
    # === CRITICAL CHECKS ===
    
    # 1. Confidentiality Period Changes
    if 'confidential' in title_lower or 'confidential' in old_lower:
        old_years = extract_years(old_text)
        new_years = extract_years(new_text)
        old_months = extract_months(old_text)
        new_months = extract_months(new_text)
        
        # Check year changes
        if old_years != 999 and new_years != 999:
            if new_years < old_years:
                reduction_pct = ((old_years - new_years) / old_years) * 100
                if reduction_pct >= 50:
                    return ("High", f"Confidentiality period significantly reduced from {old_years} to {new_years} years")
                else:
                    return ("Medium", f"Confidentiality period reduced from {old_years} to {new_years} years")
        
        # Check month changes
        if old_months != 999 and new_months != 999 and new_months < old_months:
            return ("Medium", f"Confidentiality period reduced from {old_months} to {new_months} months")
    
    # 2. Termination Notice Period Changes
    if 'terminat' in title_lower or 'terminat' in old_lower:
        old_days = extract_days(old_text)
        new_days = extract_days(new_text)
        
        if old_days != 999 and new_days != 999 and new_days < old_days:
            reduction_pct = ((old_days - new_days) / old_days) * 100
            if reduction_pct >= 40:
                return ("High", f"Termination notice significantly reduced from {old_days} to {new_days} days")
            elif reduction_pct >= 20:
                return ("Medium", f"Termination notice reduced from {old_days} to {new_days} days")
    
    # 3. Payment Amount Changes
    if 'payment' in title_lower or 'fee' in old_lower or 'consideration' in old_lower:
        old_amounts = extract_amounts(old_text)
        new_amounts = extract_amounts(new_text)
        
        if old_amounts and new_amounts:
            if new_amounts[0] > old_amounts[0]:
                increase_pct = ((new_amounts[0] - old_amounts[0]) / old_amounts[0]) * 100
                if increase_pct >= 25:
                    return ("High", f"Payment increased from ${old_amounts[0]:,.0f} to ${new_amounts[0]:,.0f}")
                else:
                    return ("Medium", f"Payment increased from ${old_amounts[0]:,.0f} to ${new_amounts[0]:,.0f}")
            elif new_amounts[0] < old_amounts[0]:
                return ("Low", "Payment amount decreased")
        
        # Check payment deadline changes
        old_days = extract_days(old_text)
        new_days = extract_days(new_text)
        if old_days != 999 and new_days != 999 and new_days < old_days:
            if abs(old_days - new_days) >= 15:
                return ("High", f"Payment deadline shortened from {old_days} to {new_days} days")
    
    # 4. Liability Cap Changes
    if 'liabilit' in title_lower or 'indemnif' in title_lower:
        if 'unlimited' in new_lower and 'unlimited' not in old_lower:
            return ("High", "Liability cap removed - unlimited liability introduced")
        
        if 'cap' in old_lower and 'cap' not in new_lower:
            return ("High", "Liability cap removed")
        
        old_amounts = extract_amounts(old_text)
        new_amounts = extract_amounts(new_text)
        if old_amounts and not new_amounts:
            return ("High", "Liability cap removed")
        if old_amounts and new_amounts and new_amounts[0] > old_amounts[0]:
            return ("Medium", "Liability cap increased")
    
    # 5. Non-Compete Clause Detection
    if 'non-compete' in title_lower or 'non compete' in title_lower or 'noncompete' in title_lower:
        if 'compete' in new_lower and 'compete' not in old_lower:
            years = extract_years(new_text)
            if years != 999:
                return ("High", f"New non-compete restriction added ({years} years)")
            return ("High", "New non-compete restriction added")
    
    # 6. Governing Law Changes
    if 'governing law' in title_lower or 'governed by' in old_lower:
        old_state = extract_state(old_text)
        new_state = extract_state(new_text)
        if old_state and new_state and old_state != new_state:
            return ("Medium", f"Governing law changed from {old_state} to {new_state}")
    
    # 7. Dispute Resolution Changes
    if 'dispute' in title_lower or 'arbitrat' in old_lower:
        if 'arbitration' in old_lower and 'court' in new_lower:
            return ("Medium", "Dispute resolution changed from arbitration to litigation")
        if 'court' in old_lower and 'arbitration' in new_lower:
            return ("Medium", "Dispute resolution changed from litigation to arbitration")
    
    # 8. Attorney Fees Changes
    if 'attorney' in old_lower or 'legal fee' in old_lower:
        if 'prevailing party' in old_lower and 'prevailing party' not in new_lower:
            return ("Medium", "Fee recovery changed - no longer favorable to prevailing party")
    
    # 9. Agreement Term Changes
    if 'term' in title_lower and 'terminat' not in title_lower:
        old_years = extract_years(old_text)
        new_years = extract_years(new_text)
        if old_years != 999 and new_years != 999 and new_years > old_years:
            return ("Medium", f"Agreement term extended from {old_years} to {new_years} years")
    
    # === GENERAL SIMILARITY CHECKS ===
    
    # High-risk clause types
    high_risk_keywords = [
        'confidentiality', 'indemnity', 'liability', 'intellectual property',
        'termination', 'non-compete', 'arbitration', 'warranty', 'payment'
    ]
    
    is_high_risk_clause = any(keyword in title_lower for keyword in high_risk_keywords)
    
    # Calculate similarity
    similarity = calculate_similarity(old_text, new_text)
    
    # Determine severity based on similarity and clause type
    if similarity < 0.4 and is_high_risk_clause:
        return ("High", "Significant change to critical clause")
    elif similarity < 0.6 and is_high_risk_clause:
        return ("Medium", "Moderate change to critical clause")
    elif similarity < 0.5:
        return ("Medium", "Significant change")
    elif similarity < 0.8:
        return ("Low", "Minor change")
    else:
        return ("Low", "Minimal change")


def generate_diff_report(text_a: str, text_b: str) -> Dict:
    """
    Generate comprehensive diff report with improved accuracy.
    Returns structured report with diffs, risk scores, summary, and metadata.
    """
    # Segment both contracts into clauses
    clauses_a = segment_clauses(text_a)
    clauses_b = segment_clauses(text_b)
    
    # Match clauses between contracts
    matches = match_clauses(clauses_a, clauses_b)
    
    diffs = []
    risk_counters = {"High": 0, "Medium": 0, "Low": 0}
    
    # Process matched clauses (modified)
    for idx_a, idx_b, similarity in matches:
        clause_a = clauses_a[idx_a]
        clause_b = clauses_b[idx_b]
        
        # Report if there's meaningful difference
        if similarity < 0.98:
            severity, risk_type = detect_risk_patterns(
                clause_a["content"],
                clause_b["content"],
                clause_a["title"] or clause_b["title"]
            )
            
            risk_counters[severity] += 1
            
            diff_entry = {
                "clause": clause_a["title"] or clause_b["title"] or f"Clause {idx_a + 1}",
                "type": "Modified",
                "summary": risk_type,
                "oldText": clause_a["content"][:800].strip(),
                "newText": clause_b["content"][:800].strip(),
                "severity": severity,
                "explanation": "",  # Will be filled by LLM or template
                "confidence": round(similarity * 100, 1)
            }
            
            diffs.append(diff_entry)
    
    # Process removed clauses (in A but not in B)
    matched_a = {idx_a for idx_a, _, _ in matches}
    for i, clause in enumerate(clauses_a):
        if i not in matched_a and clause["content"].strip():
            severity = determine_removal_severity(clause["title"], clause["content"])
            risk_counters[severity] += 1
            
            diffs.append({
                "clause": clause["title"] or f"Clause {i + 1}",
                "type": "Removed",
                "summary": "This clause was removed from the new version",
                "oldText": clause["content"][:800].strip(),
                "newText": "",
                "severity": severity,
                "explanation": "",
                "confidence": 100.0
            })
    
    # Process added clauses (in B but not in A)
    matched_b = {idx_b for _, idx_b, _ in matches}
    for i, clause in enumerate(clauses_b):
        if i not in matched_b and clause["content"].strip():
            severity = determine_addition_severity(clause["title"], clause["content"])
            risk_counters[severity] += 1
            
            diffs.append({
                "clause": clause["title"] or f"New Clause {i + 1}",
                "type": "Added",
                "summary": "This is a new clause added in the new version",
                "oldText": "",
                "newText": clause["content"][:800].strip(),
                "severity": severity,
                "explanation": "",
                "confidence": 100.0
            })
    
    # Calculate overall risk score with refined algorithm
    risk_score = calculate_refined_risk_score(risk_counters, diffs)
    
    # Generate summary and verdict
    summary, verdict = generate_summary_and_verdict(diffs, risk_counters, risk_score)
    
    return {
        "riskScore": risk_score,
        "summary": summary,
        "verdict": verdict,
        "riskReport": generate_risk_report(risk_counters, diffs),
        "diffs": diffs
    }


def determine_removal_severity(title: str, content: str) -> str:
    """Determine severity of a removed clause"""
    title_lower = title.lower()
    content_lower = content.lower()
    
    critical_keywords = ['confidential', 'liability', 'indemnif', 'intellectual property', 'warranty']
    if any(kw in title_lower or kw in content_lower for kw in critical_keywords):
        return "High"
    
    important_keywords = ['termination', 'payment', 'dispute', 'governing law']
    if any(kw in title_lower or kw in content_lower for kw in important_keywords):
        return "Medium"
    
    return "Low"


def determine_addition_severity(title: str, content: str) -> str:
    """Determine severity of an added clause"""
    title_lower = title.lower()
    content_lower = content.lower()
    
    # Non-compete is always high risk
    if 'non-compete' in title_lower or 'non compete' in content_lower:
        return "High"
    
    critical_keywords = ['liability', 'indemnif', 'penalty', 'liquidated damages']
    if any(kw in title_lower or kw in content_lower for kw in critical_keywords):
        return "High"
    
    important_keywords = ['confidential', 'termination', 'obligation', 'restriction']
    if any(kw in title_lower or kw in content_lower for kw in important_keywords):
        return "Medium"
    
    return "Low"


def calculate_refined_risk_score(risk_counters: Dict, diffs: List[Dict]) -> int:
    """Calculate risk score with refined algorithm (0-100 scale)"""
    
    # Base points per severity
    base_points = {
        "High": 18,
        "Medium": 10,
        "Low": 3
    }
    
    total_risk = 0
    
    # Add base risk
    for severity, count in risk_counters.items():
        total_risk += base_points[severity] * count
    
    # Add multipliers for specific critical changes
    for diff in diffs:
        summary_lower = diff.get("summary", "").lower()
        
        # Critical multipliers
        if "confidentiality period" in summary_lower and "reduced" in summary_lower:
            total_risk += 15
        
        if "unlimited liability" in summary_lower:
            total_risk += 12
        
        if "non-compete" in summary_lower:
            total_risk += 12
        
        if "termination" in summary_lower and "reduced" in summary_lower:
            total_risk += 10
    
    # Cap at 100
    return min(100, total_risk)


def generate_summary_and_verdict(diffs: List[Dict], risk_counters: Dict, risk_score: int) -> tuple:
    """Generate overall summary and verdict"""
    
    total_diffs = len(diffs)
    high_risk = risk_counters["High"]
    medium_risk = risk_counters["Medium"]
    low_risk = risk_counters["Low"]
    
    # Count types
    added = sum(1 for d in diffs if d.get('type') == 'Added')
    removed = sum(1 for d in diffs if d.get('type') == 'Removed')
    modified = sum(1 for d in diffs if d.get('type') == 'Modified')
    
    # Build summary
    parts = []
    if added > 0:
        parts.append(f"{added} clause{'s' if added != 1 else ''} added")
    if removed > 0:
        parts.append(f"{removed} clause{'s' if removed != 1 else ''} removed")
    if modified > 0:
        parts.append(f"{modified} clause{'s' if modified != 1 else ''} modified")
    
    summary = f"Found {total_diffs} difference{'s' if total_diffs != 1 else ''}: {', '.join(parts)}. "
    
    if high_risk > 0:
        summary += f"{high_risk} high-risk change{'s' if high_risk != 1 else ''} detected requiring immediate attention. "
    if medium_risk > 0:
        summary += f"{medium_risk} medium-risk change{'s' if medium_risk != 1 else ''} should be reviewed. "
    
    # Highlight specific critical changes
    critical_changes = []
    for diff in diffs:
        if diff['severity'] == 'High':
            critical_changes.append(diff['summary'])
    
    if critical_changes:
        summary += f"Critical concerns: {'; '.join(critical_changes[:3])}."
    
    # Generate verdict
    if risk_score >= 75:
        verdict = "Contract B poses significantly higher risk compared to Contract A. Multiple critical changes detected. Recommend thorough legal review and substantial negotiation before signing."
    elif risk_score >= 50:
        verdict = "Contract B contains moderate to high risks compared to Contract A. Several important clauses have been modified unfavorably. Key terms should be renegotiated."
    elif risk_score >= 30:
        verdict = "Contract B has notable differences from Contract A with moderate overall risk. Review and negotiation of specific clauses recommended."
    elif risk_score >= 15:
        verdict = "Contract B has minor to moderate differences from Contract A. Most changes are low-risk, but review is still recommended for business alignment."
    else:
        verdict = "Contract B is substantially similar to Contract A with minimal risk differences. Changes appear to be minor clarifications or formatting updates."
    
    return summary, verdict


def generate_risk_report(risk_counters: Dict, diffs: List[Dict]) -> str:
    """Generate detailed risk report"""
    
    high_risk = risk_counters["High"]
    medium_risk = risk_counters["Medium"]
    
    if high_risk == 0 and medium_risk == 0:
        return "No significant risks identified. All changes are low-impact."
    
    report_parts = []
    
    if high_risk > 0:
        high_risk_items = [d['clause'] for d in diffs if d['severity'] == 'High']
        report_parts.append(f"{high_risk} high-risk change{'s' if high_risk != 1 else ''} found. "
                           f"Critical review required for: {', '.join(high_risk_items[:3])}.")
    
    if medium_risk > 0:
        report_parts.append(f"{medium_risk} medium-risk change{'s' if medium_risk != 1 else ''} identified. "
                           "These should be reviewed to ensure alignment with business objectives.")
    
    report_parts.append("Recommended action: Engage legal counsel to review all high and medium risk changes before signing.")
    
    return " ".join(report_parts)
