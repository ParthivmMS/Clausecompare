import os
import json
from typing import Dict
from groq import Groq

SYSTEM_PROMPT = """You are an assistant that explains contract clause differences in plain English to non-lawyers. For each diff, produce:
1) A 1-3 sentence explanation of why the change matters.
2) Two suggested negotiation lines the user can propose (short).
3) A short confidence estimate as a percentage.
Return JSON object: {"explanation":"...", "suggestions":["...","..."], "confidence":90}"""


def get_llm_explanation(old_text: str, new_text: str, severity: str, summary: str = "") -> Dict:
    """
    Get LLM-powered explanation for a contract clause difference using Groq API.
    Falls back to template-based explanation if LLM unavailable.
    """
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        return get_template_explanation(old_text, new_text, severity, summary)
    
    try:
        client = Groq(api_key=api_key)
        
        user_prompt = f"""Old clause:
{old_text[:1000]}

New clause:
{new_text[:1000]}

Change detected: {summary}
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
        return get_template_explanation(old_text, new_text, severity, summary)


def get_template_explanation(old_text: str, new_text: str, severity: str, summary: str = "") -> Dict:
    """
    Generate template-based explanation with improved context awareness.
    """
    old_lower = old_text.lower()
    new_lower = new_text.lower()
    summary_lower = summary.lower()
    
    # Confidentiality period changes
    if 'confidentiality period' in summary_lower and 'reduced' in summary_lower:
        return {
            "explanation": "Significantly reducing the confidentiality period weakens long-term protection of trade secrets and proprietary information. This change could allow the receiving party to disclose sensitive information much sooner, potentially to competitors or in future business dealings.",
            "suggestions": [
                "Request restoration of the original 5-year confidentiality period with justification for any reduction",
                "At minimum, negotiate a 3-year period with enhanced protections for core trade secrets"
            ],
            "confidence": 95
        }
    
    # Termination notice changes
    if 'termination' in summary_lower and 'reduced' in summary_lower:
        return {
            "explanation": "Shortening the termination notice period reduces your flexibility to exit the agreement and may force rushed transitions. This could lead to business disruption, penalty payments, or difficulty finding alternative arrangements in time.",
            "suggestions": [
                "Restore the original 60-day notice period to allow adequate transition time",
                "If shorter notice is accepted, negotiate penalty-free early termination rights"
            ],
            "confidence": 92
        }
    
    # Payment increases
    if 'payment' in summary_lower and 'increased' in summary_lower:
        return {
            "explanation": "The payment amount has been significantly increased, directly impacting your budget. Combined with a shorter payment deadline, this creates cash flow pressure and financial risk. The addition of late payment penalties further compounds the financial exposure.",
            "suggestions": [
                "Request the original payment amount and timeline, or phase payments based on deliverables",
                "If increase is accepted, negotiate removal of late payment penalties and extend deadline to 30 days"
            ],
            "confidence": 95
        }
    
    # Liability cap removal
    if 'liability' in summary_lower and ('unlimited' in summary_lower or 'removed' in summary_lower):
        return {
            "explanation": "Removing the liability cap or introducing unlimited liability for certain breaches exposes your company to potentially catastrophic financial risk. A breach claim could exceed your insurance coverage and threaten business viability. Industry standard is to cap liability at 1-2x the contract value.",
            "suggestions": [
                "Reinstate a liability cap at 1-2x total fees paid under the agreement",
                "If unlimited liability is required, limit it strictly to fraud, willful misconduct, and gross negligence only"
            ],
            "confidence": 98
        }
    
    # Non-compete addition
    if 'non-compete' in summary_lower:
        return {
            "explanation": "A new non-compete restriction severely limits your business operations and market opportunities. This could prevent you from serving existing clients, hiring talent, or pursuing legitimate business activities in your core market. Non-competes are often unenforceable depending on jurisdiction.",
            "suggestions": [
                "Request complete removal of the non-compete clause as overly restrictive",
                "If required, limit scope to specific products/services directly competitive with disclosed confidential information, and reduce duration to 6-12 months"
            ],
            "confidence": 96
        }
    
    # Governing law changes
    if 'governing law' in summary_lower:
        return {
            "explanation": "Changing the governing law jurisdiction affects which state's laws will interpret the contract. Different states have varying standards for contract enforcement, non-compete validity, and liability limits. This change may make certain clauses more or less favorable.",
            "suggestions": [
                "Maintain original jurisdiction if you have established legal counsel there",
                "If change is accepted, ensure your legal team reviews all provisions under the new state's laws"
            ],
            "confidence": 88
        }
    
    # Dispute resolution changes
    if 'dispute' in summary_lower or 'arbitration' in summary_lower or 'litigation' in summary_lower:
        return {
            "explanation": "Changing from arbitration to court litigation typically increases costs, extends timelines, and makes proceedings public record. However, litigation does preserve appeal rights. The jurisdiction change may also affect convenience and costs of dispute resolution.",
            "suggestions": [
                "Maintain arbitration for cost efficiency and confidentiality",
                "If litigation is accepted, ensure jurisdiction is mutually convenient and specify venue clearly"
            ],
            "confidence": 85
        }
    
    # Attorney fees changes
    if 'attorney' in summary_lower or 'fee' in summary_lower:
        return {
            "explanation": "Removing the prevailing party fee recovery clause means you'll bear your own legal costs even if you win a dispute. This can discourage enforcement of your rights and makes defending frivolous claims more expensive.",
            "suggestions": [
                "Restore prevailing party fee recovery to deter frivolous claims",
                "Alternatively, negotiate a loser-pays provision for bad faith claims only"
            ],
            "confidence": 82
        }
    
    # Agreement term extension
    if 'agreement term' in summary_lower and 'extended' in summary_lower:
        return {
            "explanation": "Extending the agreement term increases your commitment period. Combined with shorter termination notice, this reduces your flexibility to exit if circumstances change or better opportunities arise.",
            "suggestions": [
                "Maintain the original 2-year term with option to renew",
                "If extension is accepted, ensure termination for convenience rights with reasonable notice"
            ],
            "confidence": 80
        }
    
    # Generic confidentiality
    if 'confidential' in old_lower or 'confidential' in new_lower:
        return {
            "explanation": "Changes to confidentiality terms affect how long you must protect sensitive information and what obligations apply. Ensure changes are balanced and protect your own confidential information equally.",
            "suggestions": [
                "Verify confidentiality obligations are mutual and reciprocal",
                "Ensure adequate protection period for your most sensitive trade secrets"
            ],
            "confidence": 80
        }
    
    # Generic payment
    if 'payment' in old_lower or 'fee' in old_lower:
        return {
            "explanation": "Payment term changes directly impact your financial obligations and cash flow. Review total cost, payment schedule, and any penalties carefully against the value received.",
            "suggestions": [
                "Request milestone-based payments tied to deliverables",
                "Negotiate payment terms that align with your budget cycles"
            ],
            "confidence": 85
        }
    
    # Generic liability
    if 'liabilit' in old_lower or 'indemnif' in old_lower:
        return {
            "explanation": "Liability and indemnification clauses determine your financial exposure if something goes wrong. Changes here can significantly increase risk. Ensure liability is capped and mutual where appropriate.",
            "suggestions": [
                "Propose mutual liability caps equal to fees paid",
                "Ensure liability is limited to direct damages, excluding consequential damages"
            ],
            "confidence": 88
        }
    
    # Generic termination
    if 'terminat' in old_lower:
        return {
            "explanation": "Termination clauses affect your ability to exit the agreement. Ensure you have adequate notice periods and termination rights that protect your flexibility.",
            "suggestions": [
                "Request mutual termination rights with equal notice periods",
                "Ensure termination for convenience is available, not just for cause"
            ],
            "confidence": 82
        }
    
    # Generic high severity
    if severity == "High":
        return {
            "explanation": "This is a significant change to an important contract term. The modified language could materially affect your rights, obligations, or risk exposure. Thorough legal review and negotiation is strongly recommended before proceeding.",
            "suggestions": [
                "Request detailed business justification for this material change",
                "Consider reverting to original language or proposing compromise alternatives"
            ],
            "confidence": 75
        }
    
    # Generic medium severity
    if severity == "Medium":
        return {
            "explanation": "This change modifies terms in a way that could affect your obligations or rights. While not critical, review is needed to ensure the new language aligns with your business needs and doesn't create unintended consequences.",
            "suggestions": [
                "Request examples of how this clause would apply in practical scenarios",
                "Propose clarifying language that addresses concerns of both parties"
            ],
            "confidence": 70
        }
    
    # Generic low severity
    return {
        "explanation": "This appears to be a minor wording clarification that likely doesn't materially affect the substance of the agreement. However, review to confirm your interpretation matches the other party's intent.",
        "suggestions": [
            "Accept if the meaning remains substantially the same after careful review",
            "Request clarification for any ambiguous language to prevent future disputes"
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
        summary = diff.get("summary", "")
        
        if use_llm:
            explanation_data = get_llm_explanation(old_text, new_text, severity, summary)
        else:
            explanation_data = get_template_explanation(old_text, new_text, severity, summary)
        
        # Merge explanation data into diff
        diff["explanation"] = explanation_data["explanation"]
        if "suggestions" in explanation_data:
            diff["suggestions"] = explanation_data["suggestions"]
        
        # Update confidence if provided and reasonable
        if "confidence" in explanation_data and explanation_data["confidence"]:
            # Keep original confidence if it's higher (from similarity calculation)
            if explanation_data["confidence"] > diff.get("confidence", 0):
                diff["confidence"] = explanation_data["confidence"]
    
    return diffs
