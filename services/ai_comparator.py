import os
import json
from typing import Dict, List
from groq import Groq


def compare_contracts_with_ai(text_a: str, text_b: str) -> Dict:
    """
    Use AI (Groq LLaMA 3.3) to perform full clause-by-clause comparison.
    Returns structured comparison with summary, differences, risk report, and verdict.
    """
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        raise Exception("GROQ_API_KEY not set. AI comparison requires API key.")
    
    try:
        client = Groq(api_key=api_key)
        
        prompt = build_comparison_prompt(text_a, text_b)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent output
            max_tokens=4000
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


def get_system_prompt() -> str:
    """System prompt that defines AI behavior"""
    return """You are a legal AI assistant specializing in contract analysis.

Your task is to compare two contracts (A and B) clause by clause and identify all differences.

For each difference, you must:
1. Identify the clause name/title
2. Determine the type: "Added", "Removed", or "Modified"
3. Describe the exact difference concisely
4. Explain the business/legal impact
5. Assign a risk level: "High", "Medium", or "Low"

You must also provide:
- An overall summary of all changes
- A risk report highlighting critical issues
- A verdict on which contract is riskier

Always return your response as valid JSON with this exact structure:
{
  "summary": "string",
  "differences": [
    {
      "clause": "string",
      "type": "Added|Removed|Modified",
      "difference": "string",
      "impact": "string",
      "risk_level": "High|Medium|Low"
    }
  ],
  "risk_report": "string",
  "verdict": "string"
}

Be thorough, objective, and focus on material changes that affect legal rights or obligations."""


def build_comparison_prompt(contract_a: str, contract_b: str) -> str:
    """Build the user prompt with both contracts"""
    
    # Truncate if too long (LLaMA 3.3 has 128K context but we want to be safe)
    max_length = 15000  # characters per contract
    contract_a_truncated = contract_a[:max_length]
    contract_b_truncated = contract_b[:max_length]
    
    if len(contract_a) > max_length:
        contract_a_truncated += "\n[... truncated for length ...]"
    if len(contract_b) > max_length:
        contract_b_truncated += "\n[... truncated for length ...]"
    
    prompt = f"""Compare the following two contracts clause by clause:

CONTRACT A:
{contract_a_truncated}

CONTRACT B:
{contract_b_truncated}

Analyze all differences and return a structured JSON comparison report."""
    
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
        print(f"Content: {json_str[:500]}")
        raise Exception(f"AI returned invalid JSON: {str(e)}")


def format_ai_response(ai_result: Dict) -> Dict:
    """
    Format AI response to match our internal structure.
    Converts AI format to our backend format.
    """
    
    # Calculate risk score based on differences
    differences = ai_result.get("differences", [])
    risk_score = calculate_risk_score(differences)
    
    # Convert differences to our internal format
    formatted_diffs = []
    for diff in differences:
        formatted_diff = {
            "clause": diff.get("clause", "Unknown Clause"),
            "type": diff.get("type", "Modified"),
            "summary": diff.get("difference", ""),
            "oldText": "",  # AI doesn't provide exact text quotes
            "newText": "",
            "severity": diff.get("risk_level", "Medium"),
            "explanation": diff.get("impact", ""),
            "confidence": 95.0,  # AI-generated, high confidence
            "suggestions": generate_suggestions_for_diff(diff)
        }
        formatted_diffs.append(formatted_diff)
    
    return {
        "riskScore": risk_score,
        "summary": ai_result.get("summary", ""),
        "riskReport": ai_result.get("risk_report", ""),
        "verdict": ai_result.get("verdict", ""),
        "diffs": formatted_diffs
    }


def calculate_risk_score(differences: List[Dict]) -> int:
    """Calculate overall risk score (0-100) based on differences"""
    
    if not differences:
        return 0
    
    risk_points = {
        "High": 30,
        "Medium": 15,
        "Low": 5
    }
    
    total_risk = 0
    for diff in differences:
        risk_level = diff.get("risk_level", "Low")
        total_risk += risk_points.get(risk_level, 5)
    
    # Cap at 100
    return min(100, total_risk)


def generate_suggestions_for_diff(diff: Dict) -> List[str]:
    """Generate negotiation suggestions based on diff type and risk"""
    
    risk_level = diff.get("risk_level", "Medium")
    diff_type = diff.get("type", "Modified")
    
    if risk_level == "High":
        if diff_type == "Added":
            return [
                "Request removal or significant modification of this new clause",
                "Negotiate reciprocal terms if clause must remain"
            ]
        elif diff_type == "Removed":
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
