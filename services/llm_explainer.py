import os
import json
from typing import Dict
from groq import Groq

SYSTEM_PROMPT = """You are an assistant that explains contract clause differences in plain English to non-lawyers. For each diff, produce:
1) A 1-3 sentence explanation of why the change matters.
2) Two suggested negotiation lines the user can propose (short).
3) A short confidence estimate as a percentage.
Return JSON object: {"explanation":"...", "suggestions":["...","..."], "confidence":90}"""


def get_llm_explanation(old_text: str, new_text: str, severity: str) -> Dict:
    """
    Get LLM-powered explanation for a contract clause difference using Groq API.
    Falls back to template-based explanation if LLM unavailable.
    """
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        return get_template_explanation(old_text, new_text, severity)
    
    try:
        client = Groq(api_key=api_key)
        
        user_prompt = f"""Old clause:
{old_text[:1000]}

New clause:
{new_text[:1000]}

Severity: {severity}

Provide explanation/suggestions JSON."""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to parse JSON from response
        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        result = json.loads(content)
        
        return {
            "explanation": result.get("explanation", ""),
            "suggestions": result.get("suggestions", []),
            "confidence": result.get("confidence", 85)
        }
        
    except Exception as e:
        print(f"LLM explanation failed: {str(e)}")
        return get_template_explanation(old_text, new_text, severity)


def get_template_explanation(old_text: str, new_text: str, severity: str) -> Dict:
    """
    Generate template-based explanation when LLM is unavailable.
    Uses rule-based logic to provide useful explanations.
    """
    old_lower = old_text.lower()
    new_lower = new_text.lower()
    
    # Confidentiality changes
    if 'confidential' in old_lower or 'confidential' in new_lower:
        return {
            "explanation": "Changes to confidentiality terms can affect how long you must protect sensitive information. Shorter periods may reduce your obligations but could expose your own confidential data. Review if mutual protections are maintained.",
            "suggestions": [
                "Propose matching confidentiality periods for both parties",
                "Request carve-outs for information already publicly available"
            ],
            "confidence": 80
        }
    
    # Payment changes
    if 'payment' in old_lower or 'fee' in old_lower or '$' in old_text:
        return {
            "explanation": "Payment terms directly impact your financial obligations. Ensure any increases are justified and aligned with the value received. Consider payment schedules and late payment penalties.",
            "suggestions": [
                "Request phase-based payments tied to deliverables",
                "Negotiate a cap on annual payment increases"
            ],
            "confidence": 85
        }
    
    # Liability changes
    if 'liabilit' in old_lower or 'indemnif' in old_lower:
        return {
            "explanation": "Liability clauses determine your financial exposure if something goes wrong. Unlimited liability can put your business at significant risk. Standard practice is to cap liability at contract value.",
            "suggestions": [
                "Propose mutual liability caps equal to fees paid",
                "Request carve-outs only for gross negligence and willful misconduct"
            ],
            "confidence": 90
        }
    
    # Termination changes
    if 'terminat' in old_lower:
        return {
            "explanation": "Termination clauses affect your ability to exit the agreement. Shorter notice periods reduce flexibility. Ensure you have adequate time to transition to alternatives if needed.",
            "suggestions": [
                "Request mutual termination rights with equal notice periods",
                "Propose termination for convenience with reasonable notice"
            ],
            "confidence": 85
        }
    
    # IP changes
    if 'intellectual property' in old_lower or 'copyright' in old_lower or 'patent' in old_lower:
        return {
            "explanation": "Intellectual property terms determine ownership of created work and innovations. Changes here can significantly impact your business assets and future product development.",
            "suggestions": [
                "Clarify that you retain IP for pre-existing materials",
                "Request license-back rights for jointly developed IP"
            ],
            "confidence": 88
        }
    
    # Generic high severity
    if severity == "High":
        return {
            "explanation": "This is a significant change to an important contract term. The modified language could materially affect your rights, obligations, or risk exposure. Careful review and potential legal counsel is recommended.",
            "suggestions": [
                "Request clarification on the business reason for this change",
                "Propose reverting to original language with minor modifications"
            ],
            "confidence": 75
        }
    
    # Generic medium severity
    if severity == "Medium":
        return {
            "explanation": "This change modifies the terms in a way that could affect your obligations or rights. Review to ensure the new language aligns with your expectations and business needs.",
            "suggestions": [
                "Request examples of how this clause would apply in practice",
                "Propose compromise language that addresses both parties' concerns"
            ],
            "confidence": 70
        }
    
    # Generic low severity
    return {
        "explanation": "This appears to be a minor clarification or wording change that likely doesn't materially affect the substance of the agreement. However, review to confirm it aligns with your understanding.",
        "suggestions": [
            "Accept the change if the meaning remains substantially the same",
            "Request clarification if any ambiguity exists"
        ],
        "confidence": 65
    }


def enhance_diffs_with_explanations(diffs: list, use_llm: bool = False) -> list:
    """
    Enhance a list of diffs with LLM or template explanations.
    Modifies diffs in place and returns the enhanced list.
    """
    for diff in diffs:
        old_text = diff.get("oldText", "")
        new_text = diff.get("newText", "")
        severity = diff.get("severity", "Low")
        
        if use_llm:
            explanation_data = get_llm_explanation(old_text, new_text, severity)
        else:
            explanation_data = get_template_explanation(old_text, new_text, severity)
        
        # Merge explanation data into diff
        diff["explanation"] = explanation_data["explanation"]
        if "suggestions" in explanation_data:
            diff["suggestions"] = explanation_data["suggestions"]
        
        # Update confidence if LLM provides one
        if "confidence" in explanation_data and explanation_data["confidence"]:
            diff["confidence"] = explanation_data["confidence"]
    
    return diffs
