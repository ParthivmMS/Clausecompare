import re
import difflib
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class Change:
    type: str  # 'addition', 'deletion', 'modification'
    severity: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'time_period', 'liability', 'obligation', etc.
    old_text: str
    new_text: str
    context: str
    risk_score: int  # 0-100
    explanation: str

class EnhancedDiffEngine:
    """
    Advanced contract comparison with legal pattern recognition.
    Detects: time periods, monetary values, obligations, liability shifts.
    """
    
    # Critical legal patterns that change risk
    CRITICAL_PATTERNS = {
        'liability_caps': [
            r'sole\s+(?:and\s+)?exclusive\s+remedy',
            r'limited\s+to\s+(?:the\s+)?(?:amount|sum)',
            r'shall\s+not\s+(?:be\s+)?liable\s+for\s+(?:any\s+)?consequential',
            r'no\s+(?:liability|responsibility)\s+for\s+indirect',
            r'caps?\s+(?:at|to)\s+\$?\d+',
        ],
        'time_periods': [
            r'(\d+)\s*(?:day|week|month|year)s?',
            r'within\s+(\d+)\s*(?:day|week|month|year)s?',
            r'(?:survive|survival)\s+(?:for\s+)?(\d+)\s*(?:day|week|month|year)s?',
            r'(?:term|period)\s+of\s+(\d+)\s*(?:day|week|month|year)s?',
        ],
        'monetary_values': [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|thousand|k|m)?',
            r'(?:damages|liability|compensation)\s+(?:of\s+)?\$\s*(\d+)',
        ],
        'obligations': [
            r'(?:shall|must|will|agrees?\s+to)\s+([^.]{10,100})',
            r'(?:required|obligated|bound)\s+to\s+([^.]{10,100})',
            r'in\s+writing\s+within',
            r'written\s+(?:notice|confirmation|consent)',
        ],
        'termination': [
            r'terminate\s+(?:this\s+)?(?:agreement|contract)',
            r'(?:immediate|without)\s+(?:notice|warning)',
            r'for\s+(?:any|no)\s+reason',
            r'at\s+(?:will|any\s+time)',
        ],
        'confidentiality': [
            r'confidential\s+information',
            r'oral\s+(?:information|disclosure)',
            r'written\s+confirmation',
            r'return\s+(?:all|any)\s+confidential',
        ],
        'indemnification': [
            r'indemnif(?:y|ies|ication)',
            r'hold\s+harmless',
            r'defend\s+against',
        ]
    }
    
    def __init__(self):
        self.changes: List[Change] = []
    
    def compare(self, text_a: str, text_b: str) -> Dict:
        """
        Main comparison function with enhanced detection.
        Returns structured diff with risk scoring.
        """
        self.changes = []
        
        # Step 1: Normalize texts
        text_a_clean = self._normalize(text_a)
        text_b_clean = self._normalize(text_b)
        
        # Step 2: Break into sections
        sections_a = self._chunk_by_sections(text_a_clean)
        sections_b = self._chunk_by_sections(text_b_clean)
        
        # Step 3: Compare sections
        self._compare_sections(sections_a, sections_b)
        
        # Step 4: Line-by-line diff for remaining changes
        self._line_diff(text_a_clean, text_b_clean)
        
        # Step 5: Pattern matching for critical legal terms
        self._detect_critical_patterns(text_a_clean, text_b_clean)
        
        # Step 6: Calculate overall risk score
        risk_score = self._calculate_risk_score()
        
        return {
            'changes': [self._change_to_dict(c) for c in self.changes],
            'total_changes': len(self.changes),
            'critical_changes': len([c for c in self.changes if c.severity == 'critical']),
            'high_changes': len([c for c in self.changes if c.severity == 'high']),
            'risk_score': risk_score,
            'summary': self._generate_summary(),
        }
    
    def _normalize(self, text: str) -> str:
        """Normalize text while preserving legal structure."""
        text = re.sub(r'\s+', ' ', text)  # Collapse whitespace
        text = re.sub(r'\.{2,}', '.', text)  # Remove multiple periods
        return text.strip()
    
    def _chunk_by_sections(self, text: str) -> List[Dict]:
        """
        Break contract into logical sections.
        Looks for: numbered clauses, headings, definitions.
        """
        sections = []
        
        # Pattern 1: Numbered sections (1., 2., 3.)
        numbered = re.split(r'\n\s*(\d+\.)', text)
        if len(numbered) > 3:
            for i in range(1, len(numbered), 2):
                if i+1 < len(numbered):
                    sections.append({
                        'number': numbered[i].strip(),
                        'content': numbered[i+1].strip()
                    })
        
        # Pattern 2: Headings (ALL CAPS or bold)
        if not sections:
            headings = re.split(r'\n\s*([A-Z][A-Z\s]{10,})\n', text)
            if len(headings) > 2:
                for i in range(1, len(headings), 2):
                    if i+1 < len(headings):
                        sections.append({
                            'heading': headings[i].strip(),
                            'content': headings[i+1].strip()
                        })
        
        # Fallback: Split by paragraphs
        if not sections:
            paragraphs = text.split('\n\n')
            sections = [{'content': p.strip()} for p in paragraphs if p.strip()]
        
        return sections
    
    def _compare_sections(self, sections_a: List[Dict], sections_b: List[Dict]):
        """Compare sections to detect moved/deleted/added clauses."""
        # Build content maps
        content_a = {s.get('content', '')[:100]: s for s in sections_a}
        content_b = {s.get('content', '')[:100]: s for s in sections_b}
        
        # Check for deleted sections
        for key, section in content_a.items():
            if key not in content_b and key:
                self.changes.append(Change(
                    type='deletion',
                    severity='high',
                    category='section_removal',
                    old_text=section.get('content', '')[:200],
                    new_text='',
                    context='Entire section removed',
                    risk_score=75,
                    explanation='A complete contract section was deleted'
                ))
        
        # Check for added sections
        for key, section in content_b.items():
            if key not in content_a and key:
                self.changes.append(Change(
                    type='addition',
                    severity='high',
                    category='section_addition',
                    old_text='',
                    new_text=section.get('content', '')[:200],
                    context='New section added',
                    risk_score=70,
                    explanation='A new contract section was added'
                ))
    
    def _line_diff(self, text_a: str, text_b: str):
        """Line-by-line comparison with context."""
        lines_a = text_a.split('. ')
        lines_b = text_b.split('. ')
        
        diff = difflib.unified_diff(lines_a, lines_b, lineterm='')
        
        for line in diff:
            if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
                continue
            
            if line.startswith('-'):
                # Deletion
                old_text = line[1:].strip()
                if len(old_text) > 20:  # Ignore trivial changes
                    self.changes.append(Change(
                        type='deletion',
                        severity='medium',
                        category='text_removal',
                        old_text=old_text,
                        new_text='',
                        context='Text removed',
                        risk_score=50,
                        explanation='Contract text was deleted'
                    ))
            
            elif line.startswith('+'):
                # Addition
                new_text = line[1:].strip()
                if len(new_text) > 20:
                    self.changes.append(Change(
                        type='addition',
                        severity='medium',
                        category='text_addition',
                        old_text='',
                        new_text=new_text,
                        context='Text added',
                        risk_score=50,
                        explanation='New contract text was added'
                    ))
    
    def _detect_critical_patterns(self, text_a: str, text_b: str):
        """
        Pattern matching for critical legal terms.
        THIS IS THE KEY UPGRADE - detects what you missed.
        """
        
        # 1. TIME PERIOD CHANGES
        times_a = self._extract_time_periods(text_a)
        times_b = self._extract_time_periods(text_b)
        
        for period_type, value_a in times_a.items():
            value_b = times_b.get(period_type)
            if value_b and value_a != value_b:
                severity = 'critical' if abs(value_a - value_b) > 180 else 'high'
                self.changes.append(Change(
                    type='modification',
                    severity=severity,
                    category='time_period_change',
                    old_text=f'{period_type}: {value_a} days',
                    new_text=f'{period_type}: {value_b} days',
                    context='Time obligation changed',
                    risk_score=85 if severity == 'critical' else 70,
                    explanation=f'The {period_type} was changed from {value_a} to {value_b} days'
                ))
        
        # 2. LIABILITY CAP ADDITIONS
        liability_a = self._has_liability_cap(text_a)
        liability_b = self._has_liability_cap(text_b)
        
        if not liability_a and liability_b:
            self.changes.append(Change(
                type='addition',
                severity='critical',
                category='liability_cap_added',
                old_text='Full liability',
                new_text='Liability capped/limited',
                context='New liability limitation added',
                risk_score=95,
                explanation='A liability cap or "sole remedy" clause was added, limiting your legal recourse'
            ))
        
        # 3. CONSEQUENTIAL DAMAGES REMOVAL
        conseq_a = self._has_consequential_damages_protection(text_a)
        conseq_b = self._has_consequential_damages_protection(text_b)
        
        if conseq_a and not conseq_b:
            self.changes.append(Change(
                type='deletion',
                severity='critical',
                category='damages_protection_removed',
                old_text='Protected from consequential/punitive damages',
                new_text='No protection',
                context='Damages protection removed',
                risk_score=90,
                explanation='Protection from consequential and punitive damages was removed'
            ))
        
        # 4. WRITTEN CONFIRMATION REQUIREMENTS
        written_a = self._requires_written_confirmation(text_a)
        written_b = self._requires_written_confirmation(text_b)
        
        if written_a and not written_b:
            self.changes.append(Change(
                type='deletion',
                severity='high',
                category='written_requirement_removed',
                old_text='Written confirmation required',
                new_text='No written requirement',
                context='Written documentation requirement removed',
                risk_score=75,
                explanation='Requirement for written confirmation was removed, allowing oral agreements'
            ))
        
        # 5. MONETARY VALUE CHANGES
        money_a = self._extract_monetary_values(text_a)
        money_b = self._extract_monetary_values(text_b)
        
        for context, value_a in money_a.items():
            value_b = money_b.get(context)
            if value_b and value_a != value_b:
                change_pct = abs(value_a - value_b) / value_a * 100
                severity = 'critical' if change_pct > 50 else 'high'
                self.changes.append(Change(
                    type='modification',
                    severity=severity,
                    category='monetary_change',
                    old_text=f'${value_a:,.2f}',
                    new_text=f'${value_b:,.2f}',
                    context=context,
                    risk_score=80 if severity == 'critical' else 65,
                    explanation=f'Monetary value changed by {change_pct:.0f}%'
                ))
    
    def _extract_time_periods(self, text: str) -> Dict[str, int]:
        """Extract time periods and convert to days."""
        periods = {}
        
        patterns = {
            'survival': r'surviv(?:e|al)\s+(?:for\s+)?(\d+)\s*(day|week|month|year)s?',
            'notice': r'(?:notice|notification)\s+(?:of\s+)?(\d+)\s*(day|week|month|year)s?',
            'term': r'(?:term|period)\s+of\s+(\d+)\s*(day|week|month|year)s?',
            'written_confirmation': r'written\s+(?:confirmation|notice)\s+within\s+(\d+)\s*(day|week|month|year)s?',
        }
        
        for name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                unit = match.group(2).lower()
                
                # Convert to days
                multiplier = {'day': 1, 'week': 7, 'month': 30, 'year': 365}
                periods[name] = value * multiplier.get(unit, 1)
        
        return periods
    
    def _has_liability_cap(self, text: str) -> bool:
        """Check if text contains liability limitation language."""
        patterns = [
            r'sole\s+(?:and\s+)?exclusive\s+remedy',
            r'limited\s+to\s+(?:the\s+)?(?:amount|sum)',
            r'liability\s+(?:is\s+)?capped',
            r'maximum\s+liability',
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
    
    def _has_consequential_damages_protection(self, text: str) -> bool:
        """Check if text protects against consequential/punitive damages."""
        patterns = [
            r'no\s+(?:liability|responsibility)\s+for\s+(?:any\s+)?(?:consequential|indirect|punitive)',
            r'not\s+liable\s+for\s+(?:any\s+)?(?:consequential|indirect|punitive)',
            r'excluding\s+(?:consequential|indirect|punitive)',
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
    
    def _requires_written_confirmation(self, text: str) -> bool:
        """Check if text requires written confirmation."""
        patterns = [
            r'in\s+writing\s+within',
            r'written\s+(?:confirmation|notice|consent)\s+(?:within|required)',
            r'must\s+be\s+(?:confirmed|documented)\s+in\s+writing',
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
    
    def _extract_monetary_values(self, text: str) -> Dict[str, float]:
        """Extract monetary values with context."""
        values = {}
        
        pattern = r'(\w+\s+)?(?:damages|liability|compensation|limit)\s+(?:of\s+)?\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|thousand|k|m)?'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context = match.group(1) or 'general'
            amount = float(match.group(2).replace(',', ''))
            
            # Handle multipliers
            if re.search(r'million|m', match.group(0), re.IGNORECASE):
                amount *= 1_000_000
            elif re.search(r'thousand|k', match.group(0), re.IGNORECASE):
                amount *= 1_000
            
            values[context.strip()] = amount
        
        return values
    
    def _calculate_risk_score(self) -> int:
        """Calculate overall risk score (0-100)."""
        if not self.changes:
            return 0
        
        # Weight by severity
        weights = {'critical': 1.0, 'high': 0.7, 'medium': 0.4, 'low': 0.2}
        
        total_weighted_risk = sum(
            change.risk_score * weights.get(change.severity, 0.5)
            for change in self.changes
        )
        
        # Normalize to 0-100
        max_possible = len(self.changes) * 100
        normalized = min(100, int((total_weighted_risk / max_possible) * 100)) if max_possible > 0 else 0
        
        # Boost if multiple critical changes
        critical_count = len([c for c in self.changes if c.severity == 'critical'])
        if critical_count >= 3:
            normalized = min(100, normalized + 15)
        elif critical_count >= 2:
            normalized = min(100, normalized + 10)
        
        return normalized
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary."""
        critical = [c for c in self.changes if c.severity == 'critical']
        high = [c for c in self.changes if c.severity == 'high']
        
        if not self.changes:
            return "No significant changes detected."
        
        summary_parts = [
            f"Found {len(self.changes)} total changes.",
        ]
        
        if critical:
            summary_parts.append(f"{len(critical)} critical changes that significantly increase risk.")
        
        if high:
            summary_parts.append(f"{len(high)} high-priority changes requiring review.")
        
        # Highlight top 3 critical changes
        if critical:
            summary_parts.append("\nMost critical changes:")
            for i, change in enumerate(critical[:3], 1):
                summary_parts.append(f"{i}. {change.explanation}")
        
        return " ".join(summary_parts)
    
    def _change_to_dict(self, change: Change) -> Dict:
        """Convert Change object to dictionary."""
        return {
            'type': change.type,
            'severity': change.severity,
            'category': change.category,
            'old_text': change.old_text,
            'new_text': change.new_text,
            'context': change.context,
            'risk_score': change.risk_score,
            'explanation': change.explanation,
        }

# Standalone function for backward compatibility
def compare_contracts(text_a: str, text_b: str) -> Dict:
    """
    Main entry point for contract comparison.
    Uses enhanced diff engine with legal pattern recognition.
    """
    engine = EnhancedDiffEngine()
    return engine.compare(text_a, text_b)
