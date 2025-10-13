import os
import json
from typing import Dict, List
from groq import Groq


ENHANCED_SYSTEM_PROMPT = """You are the core intelligence behind ClauseCompare — an AI that compares two legal contracts clause by clause.

Your main goal is NOT to just detect surface-level changes (like numbers or dates) but to understand **semantic and legal meaning changes** between clauses.

Follow these steps strictly every time:

1. **Clause Segmentation:**
   - Split both documents into individual clauses using numbering patterns (like "1.", "2.", "3.") or headings (like "Termination", "Confidentiality", etc.).
   - If no numbering exists, split by paragraphs logically.

2. **Clause Matching:**
   - Match clauses between the two versions based on semantic similarity (not just text position).
   - For example, "Termination" in one document and "End of Employment" in another should be treated as the same clause if meaning matches.

3. **Comparison Logic:**
   For each matched clause pair:
   - If no change → Mark as "No Change".
   - If minor wording changes but same meaning → Mark as "Reworded (No legal impact)".
   - If legal meaning changes → Describe the exact difference in simple terms.
   - If a clause is added or deleted → Flag as "Added Clause" or "Deleted Clause".

4. **Risk Scoring:**
   - Assign risk levels:
     - Low Risk: stylistic or wording change.
     - Medium Risk: change affects terms but not core rights.
     - High Risk: change affects legal obligation, penalty, or duration.
   - Score range: 0–100.

5. **Report Output:**
   Always output in JSON format:
   {
     "overall_risk_score": <0–100>,
     "summary": "Brief overview of all changes",
     "verdict": "Overall assessment of Contract B vs Contract A",
     "risk_report": "Detailed risk analysis",
     "changes": [
        {
           "clause_title": "...",
           "change_type": "Modified/Added/Removed/Reworded",
           "old_text": "...",
           "new_text": "...",
           "difference_summary": "...",
           "legal_impact": "Specific legal/business impact",
           "risk_level": "Low/Medium/High",
           "confidence": "xx%",
           "suggestions": ["negotiation suggestion 1", "negotiation suggestion 2"]
        }
     ]
   }

6. **Language & Tone:**
   - Use simple, professional legal English.
   - Avoid vague terms like "may have changed." Be specific ("Termination notice increased from 7 to 15 days.").

7. **Error Handling:**
   - If structure mismatch occurs (unequal number of clauses), still try to map logically.
   - If uncertain, include a "possible change" tag with low confidence.

GOAL:
Deliver human-level, clause-by-clause legal comparisons that lawyers can trust. Focus on legal meaning — not just words.

CRITICAL: Focus on semantic meaning changes, not just word-level differences. Two clauses with different wording but identical legal meaning should be marked as "Reworded (No legal impact)"."""


def compare_contracts_with_ai(text_a: str, text_b: str) -> Dict:
    """
    Use AI (Groq LLaMA 3.3) to perform semantic clause-by-clause comparison.
    Follows enhanced system instructions for legal meaning analysis.
    Returns structured comparison with summary, differences, risk report, and verdict.
    """
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        raise Exception("GROQ_API_KEY not set. AI comparison requires API key.")
    
    try:
        client = Groq(api_key=api_key)
        
        prompt = build_enhanced_comparison_prompt(text_a, text_b)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": ENHANCED_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # Lower temperature for more consistent, precise analysis
            max_tokens=6000   # Increased for detailed analysis
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON from response
        result = extract_json_from_response(content)
        
        # Validate and format result
        formatted_result = format_ai_response(result)
        
        return formatted_result
        
    except Exception as e:
        print(f"AI comparison failed: {str(e)}")
        raise Exception(f"Failed to compare contracts with AI: {str(e)}")


def build_enhanced_comparison_prompt(contract_a: str, contract_b: str) -> str:
    """Build the enhanced user prompt with both contracts"""
    
    # Intelligent truncation with context preservation
    max_length = 20000  # characters per contract (LLaMA 3.3 has 128K context)
    
    def smart_truncate(text: str, max_len: int) -> str:
        """Truncate while preserving clause structure"""
        if len(text) <= max_len:
            return text
        
        # Try to truncate at clause boundaries
        truncated = text[:max_len]
        
        # Find last complete clause (look for numbered section or double newline)
        last_section = max(
            truncated.rfind('\n\n'),
            truncated.rfind('\n1.'),
            truncated.rfind('\n2.'),
            truncated.rfind('\n3.')
        )
        
        if last_section > max_len * 0.8:  # If we found a good break point
            truncated = truncated[:last_section]
        
        return truncated + "\n\n[... document continues but truncated for length ...]"
    
    contract_a_prepared = smart_truncate(contract_a, max_length)
    contract_b_prepared = smart_truncate(contract_b, max_length)
    
    prompt = f"""Compare the following two contracts clause by clause with semantic understanding:

CONTRACT A (Original Version):
{contract_a_prepared}

==========================================

CONTRACT B (New/Modified Version):
{contract_b_prepared}

==========================================

INSTRUCTIONS:
1. Segment both contracts into logical clauses
2. Match clauses by semantic meaning (not just position or title)
3. For each difference, determine if it's:
   - Substantive legal change (affects rights/obligations)
   - Reworded but same meaning
   - Addition or removal
4. Provide specific, measurable descriptions (e.g., "from 30 to 15 days", not "shortened")
5. Focus on business/legal impact, not cosmetic changes

Return your analysis as a JSON object matching the specified format."""
    
    return prompt


def extract_json_from_response(content: str) -> Dict:
    """Extract JSON from AI response, handling markdown code blocks"""
    
    # Try to extract JSON from markdown code blocks
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        json_str = content.split("```")[1].split("```")[0].strip()
    else:
        json_str = content.strip()
    
    # Remove any leading/trailing whitespace
    json_str = json_str.strip()
    
    # Parse JSON
    try:
        result = json.loads(json_str)
        return result
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Content preview: {json_str[:500]}")
        raise Exception(f"AI returned invalid JSON: {str(e)}")


def format_ai_response(ai_result: Dict) -> Dict:
    """
    Format AI response to match our internal structure.
    Handles both the new enhanced format and maintains backward compatibility.
    """
    
    # Extract risk score (handle both field names)
    risk_score = ai_result.get("overall_risk_score", ai_result.get("riskScore", 0))
    
    # Extract changes/differences
    changes = ai_result.get("changes", ai_result.get("differences", []))
    
    # Convert to our internal diff format
    formatted_diffs = []
    for change in changes:
        # Handle different field names from AI
        clause_title = change.get("clause_title", change.get("clause", "Unknown Clause"))
        change_type = change.get("change_type", change.get("type", "Modified"))
        old_text = change.get("old_text", change.get("oldText", ""))
        new_text = change.get("new_text", change.get("newText", ""))
        difference = change.get("difference_summary", change.get("difference", change.get("summary", "")))
        legal_impact = change.get("legal_impact", change.get("impact", ""))
        risk_level = change.get("risk_level", change.get("severity", "Medium"))
        confidence = change.get("confidence", "90%")
        suggestions = change.get("suggestions", [])
        
        # Normalize change_type
        if change_type in ["Added Clause", "Added"]:
            change_type = "Added"
        elif change_type in ["Deleted Clause", "Removed", "Deleted"]:
            change_type = "Removed"
        elif change_type in ["Reworded (No legal impact)", "Reworded"]:
            change_type = "Reworded"
            risk_level = "Low"  # Rewording is always low risk
        else:
            change_type = "Modified"
        
        # Parse confidence percentage
        if isinstance(confidence, str):
            confidence_val = float(confidence.rstrip('%'))
        else:
            confidence_val = float(confidence)
        
        # Build explanation combining difference and legal impact
        explanation = difference
        if legal_impact and legal_impact != difference:
            explanation = f"{difference} {legal_impact}"
        
        formatted_diff = {
            "clause": clause_title,
            "type": change_type,
            "summary": difference,
            "oldText": old_text[:800] if old_text else "",
            "newText": new_text[:800] if new_text else "",
            "severity": risk_level,
            "explanation": explanation,
            "confidence": confidence_val,
            "suggestions": suggestions if suggestions else generate_default_suggestions(risk_level, change_type)
        }
        
        formatted_diffs.append(formatted_diff)
    
    # Build final response
    return {
        "riskScore": int(risk_score),
        "summary": ai_result.get("summary", ""),
        "riskReport": ai_result.get("risk_report", ""),
        "verdict": ai_result.get("verdict", ""),
        "diffs": formatted_diffs
    }


def generate_default_suggestions(risk_level: str, change_type: str) -> List[str]:
    """Generate default negotiation suggestions based on risk and type"""
    
    if change_type == "Reworded":
        return [
            "Accept if meaning remains substantively the same",
            "Request clarification if any ambiguity exists"
        ]
    
    if risk_level == "High":
        if change_type == "Added":
            return [
                "Request removal or significant modification of this new clause",
                "Negotiate reciprocal terms if clause must remain"
            ]
        elif change_type == "Removed":
            return [
                "Request reinstatement of this critical protection",
                "Seek alternative safeguards if original clause cannot be restored"
            ]
        else:  # Modified
            return [
                "Revert to original language with minor compromises",
                "Request detailed justification for this material change"
            ]
    
    elif risk_level == "Medium":
        return [
            "Clarify the business rationale behind this change",
            "Propose compromise language that addresses both parties' concerns"
        ]
    
    else:  # Low
        return [
            "Accept if meaning remains substantially the same",
            "Request minor clarification if any ambiguity exists"
        ]


def validate_ai_response(ai_result: Dict) -> bool:
    """Validate that AI response has required fields"""
    
    required_fields = ["overall_risk_score", "changes"]
    
    for field in required_fields:
        if field not in ai_result and field.replace("_", "") not in str(ai_result):
            print(f"Warning: Missing required field '{field}' in AI response")
            return False
    
    # Check changes structure
    changes = ai_result.get("changes", ai_result.get("differences", []))
    if not isinstance(changes, list):
        print("Warning: 'changes' is not a list")
        return False
    
    return True


def fallback_comparison(text_a: str, text_b: str) -> Dict:
    """
    Fallback to rule-based comparison if AI fails.
    """
    from services.diff_engine import generate_diff_report
    
    print("Using fallback rule-based comparison due to AI failure")
    return generate_diff_report(text_a, text_b)
