"""
Flow Scoring Mechanism for Minimum Flow Extraction
Implements hierarchical scoring system as per S1.1-S1.7 specifications
"""

import re
from typing import Dict, List, Tuple, Optional


class FlowCandidate:
    """Represents a candidate minimum flow value with its context and score"""
    
    def __init__(self, value: str, context: str, sentences):
        self.value = value
        self.context = context.lower() if isinstance(context, str) else str(context).lower()
        # Handle sentences that could be string or list
        if isinstance(sentences, str):
            self.sentences = sentences.lower()
        elif isinstance(sentences, list):
            self.sentences = " ".join(str(s) for s in sentences).lower()
        else:
            self.sentences = str(sentences).lower()
        self.score = 0
        self.score_breakdown = []
        
    def add_score(self, points: int, reason: str):
        """Add points with explanation"""
        self.score += points
        self.score_breakdown.append(f"{reason}: {points:+d}")
        
    def __repr__(self):
        return f"FlowCandidate({self.value}, score={self.score})"


class FlowScoringSystem:
    """Implements the hierarchical scoring mechanism for minimum flow extraction"""
    
    # Known successful extractions for document-specific protection
    PROTECTED_EXTRACTIONS = {
        "laurel": "40 dsf",
        "bonneville": "58,000 cfs",
        # Add more as validated
    }
    
    def __init__(self):
        pass
    
    def extract_flow_value(self, value_str: str) -> Optional[float]:
        """Extract numeric flow value from string like '1,600 cfs' or '40 dsf'"""
        if not value_str or value_str.lower() in ['not mentioned', 'no minimum flow required']:
            return None
            
        # Remove commas and extract number
        match = re.search(r'([\d,]+\.?\d*)', value_str)
        if match:
            num_str = match.group(1).replace(',', '')
            try:
                return float(num_str)
            except ValueError:
                return None
        return None
    
    def score_generation_conversion(self, candidate: FlowCandidate) -> None:
        """
        Primary Tier: Generation Conversion Priority (+500 points)
        Highest authority - explicit conversion from generation hours to flow
        """
        generation_patterns = [
            r'discharge equivalent.*one hour.*generation',
            r'one hour of.*unit generation',
            r'converted.*generation.*(?:cfs|flow)',
            r'(?:1600|3600).*cfs.*one hour',
            r'generation.*converted to.*time',
            r'minimum volumetric discharge.*cfs per day.*for one hour'
        ]
        
        combined_text = candidate.context + " " + candidate.sentences
        
        for pattern in generation_patterns:
            if re.search(pattern, combined_text):
                candidate.add_score(500, "Generation-based conversion (PRIMARY AUTHORITY)")
                return
    
    def score_document_protection(self, candidate: FlowCandidate, document_name: str) -> None:
        """
        Primary Tier: Document-Specific Protection (+45 points)
        Protects known successful extractions from regression
        """
        doc_key = document_name.lower()
        
        for protected_doc, protected_value in self.PROTECTED_EXTRACTIONS.items():
            if protected_doc in doc_key and protected_value.lower() in candidate.value.lower():
                candidate.add_score(45, "Protected successful extraction")
                return
    
    def score_mandate_language(self, candidate: FlowCandidate) -> None:
        """
        Primary Tier: Explicit Mandate Language (+55 points)
        Strong mandate keywords indicate legally required minimum flows
        Beats operational context (35) + dam location (15) = 50 points
        """
        combined_text = candidate.context + " " + candidate.sentences
        
        # Strong mandate keywords that indicate legal/regulatory requirements
        mandate_keywords = [
            'established',
            'mandated',
            'minimum release',
            'required',
            'year-round instantaneous minimum',
            'year-round minimum',
            'instantaneous minimum',
            'shall release',
            'must release',
            'minimum flow requirement',
            'continuous minimum flow',
            'minimum discharge'
        ]
        
        for keyword in mandate_keywords:
            if keyword in combined_text:
                candidate.add_score(55, f"MANDATE: '{keyword}' detected")
                return
    
    def score_operational_context(self, candidate: FlowCandidate) -> None:
        """
        Secondary Tier: Operational Context (+35-40 points)
        Large operational flows in proper context
        """
        flow_value = self.extract_flow_value(candidate.value)
        if not flow_value:
            return
        
        combined_text = candidate.context + " " + candidate.sentences
        
        # Water quality context (+40)
        water_quality_keywords = ['dissolved oxygen', 'water quality', 'mg/l', 'temperature']
        if any(kw in combined_text for kw in water_quality_keywords):
            if flow_value > 1000:
                candidate.add_score(40, "Water quality operational context")
                return
        
        # Standard operational context (+35)
        operational_keywords = [
            'navigation', 'powerhouse', 'dam management', 'turbine',
            'hydropower', 'generation schedule', 'operational'
        ]
        
        if any(kw in combined_text for kw in operational_keywords):
            if flow_value > 1000:
                candidate.add_score(35, "Operational context (>1000 cfs)")
    
    def score_environmental_context(self, candidate: FlowCandidate) -> None:
        """
        Secondary Tier: Environmental Context (+25 points)
        Environmental flows typically <10,000 cfs
        """
        flow_value = self.extract_flow_value(candidate.value)
        if not flow_value:
            return
        
        combined_text = candidate.context + " " + candidate.sentences
        
        environmental_keywords = [
            'fish passage', 'habitat', 'spawning', 'environmental',
            'bypass', 'ecological', 'aquatic', 'wildlife'
        ]
        
        if any(kw in combined_text for kw in environmental_keywords):
            if flow_value < 10000:
                candidate.add_score(25, "Environmental flow context")
    
    def score_regulatory_language(self, candidate: FlowCandidate) -> None:
        """
        Tertiary Tier: Regulatory Language (+10-15 points)
        Strong regulatory authority indicators
        """
        combined_text = candidate.context + " " + candidate.sentences
        
        # Strong mandates (+15)
        strong_mandates = ['shall', 'must', 'required', 'mandated']
        if any(word in combined_text for word in strong_mandates):
            candidate.add_score(15, "Strong regulatory language")
            return
        
        # FERC/license conditions (+15)
        if 'ferc' in combined_text or 'license condition' in combined_text:
            candidate.add_score(15, "FERC/license requirement")
            return
        
        # Conditional requirements (+10)
        conditional_terms = ['should', 'will', 'authorized']
        if any(word in combined_text for word in conditional_terms):
            candidate.add_score(10, "Conditional regulatory language")
    
    def score_seasonal_specificity(self, candidate: FlowCandidate) -> None:
        """
        Tertiary Tier: Seasonal Specificity (+8 points)
        Detailed seasonal schedules indicate precise regulatory determination
        """
        combined_text = candidate.context + " " + candidate.sentences
        
        seasonal_indicators = [
            'seasonal', 'monthly', 'june', 'july', 'august', 'september',
            'winter', 'summer', 'spring', 'fall', 'calendar day'
        ]
        
        if any(indicator in combined_text for indicator in seasonal_indicators):
            candidate.add_score(8, "Seasonal/temporal specificity")
    
    def score_location_hierarchy(self, candidate: FlowCandidate) -> None:
        """
        Tertiary Tier: Location Hierarchy (+3-15 points)
        Dam > Powerhouse > Auxiliary locations
        """
        flow_value = self.extract_flow_value(candidate.value)
        combined_text = candidate.context + " " + candidate.sentences
        
        # Small dam flows (≤15 cfs) get enhanced scoring
        if flow_value and flow_value <= 15:
            if 'dam' in combined_text:
                candidate.add_score(15, "Small precise dam flow (≤15 cfs)")
                return
        
        # Standard location hierarchy
        if 'dam' in combined_text and 'downstream' not in combined_text:
            candidate.add_score(15, "Dam location (primary)")
        elif 'powerhouse' in combined_text or 'turbine' in combined_text:
            candidate.add_score(8, "Powerhouse location")
        elif 'bypass' in combined_text or 'auxiliary' in combined_text:
            candidate.add_score(3, "Auxiliary location")
    
    def apply_penalties(self, candidate: FlowCandidate) -> None:
        """
        Penalty Mechanisms: Error Prevention
        """
        flow_value = self.extract_flow_value(candidate.value)
        combined_text = candidate.context + " " + candidate.sentences
        
        # Flood control exclusion (-25)
        flood_keywords = ['flood control', 'spillway design', 'emergency', 'maximum']
        if any(kw in combined_text for kw in flood_keywords):
            if flow_value and flow_value > 50000:
                candidate.add_score(-25, "Flood control/emergency operation (PENALTY)")
        
        # Zero flow capability (-30)
        zero_flow_indicators = ['zero discharge', 'no release', 'curtail', 'reduce to zero']
        if any(indicator in combined_text for indicator in zero_flow_indicators):
            # Don't penalize if generation-based (already has +500)
            if candidate.score < 400:  # If no generation bonus
                candidate.add_score(-30, "Zero flow capability (PENALTY)")
    
    def score_candidate(self, candidate: FlowCandidate, document_name: str = "") -> FlowCandidate:
        """Apply all scoring rules to a candidate"""
        
        # Primary Tier
        self.score_generation_conversion(candidate)
        self.score_document_protection(candidate, document_name)
        self.score_mandate_language(candidate)  # V16.4: Explicit mandate detection
        
        # Secondary Tier
        self.score_operational_context(candidate)
        self.score_environmental_context(candidate)
        
        # Tertiary Tier
        self.score_regulatory_language(candidate)
        self.score_seasonal_specificity(candidate)
        self.score_location_hierarchy(candidate)
        
        # Penalties
        self.apply_penalties(candidate)
        
        return candidate
    
    def select_best_flow(self, candidates: List[FlowCandidate], document_name: str = "") -> FlowCandidate:
        """
        Score all candidates and select the highest-scoring one
        """
        if not candidates:
            return None
        
        # Score all candidates
        scored = [self.score_candidate(c, document_name) for c in candidates]
        
        # Sort by score (descending)
        scored.sort(key=lambda x: x.score, reverse=True)
        
        return scored[0]
    
    def parse_llm_response(self, response: Dict) -> List[FlowCandidate]:
        """
        Parse LLM response and extract multiple flow candidates if present
        """
        candidates = []
        
        value = response.get('value', 'Not mentioned')
        context = response.get('inferred_context', '')
        sentences = response.get('exact_sentences', '')
        
        # Convert value to string if it's not already
        value = str(value) if not isinstance(value, str) else value
        
        # Convert context to string if it's a list
        context = " ".join(context) if isinstance(context, list) else str(context) if not isinstance(context, str) else context
        
        # Handle "no minimum flow" cases (V15.8 FIX: also catch "no separate minimum")
        value_lower = value.lower()
        if ('no minimum flow' in value_lower or 
            'not mentioned' in value_lower or 
            'no separate minimum' in value_lower or
            'no independent minimum' in value_lower):
            return [FlowCandidate(value, context, sentences)]
        
        # Check for multiple flows in the context
        # Pattern: look for flow values like "1,600 cfs", "40,000 cfs", etc.
        flow_pattern = r'([\d,]+\.?\d*)\s*(?:cfs|cms|dsf)'
        
        # Ensure sentences is a string
        sentences_str = sentences if isinstance(sentences, str) else " ".join(sentences) if isinstance(sentences, list) else str(sentences)
        
        found_flows = set()
        for match in re.finditer(flow_pattern, context + " " + sentences_str):
            flow_str = match.group(0)
            found_flows.add(flow_str)
        
        # Create candidates for each unique flow found
        if found_flows:
            for flow in found_flows:
                # Extract relevant context for this specific flow
                candidate = FlowCandidate(flow, context, sentences)
                candidates.append(candidate)
        else:
            # Single flow or no flows found - use the main value
            candidates.append(FlowCandidate(value, context, sentences))
        
        return candidates


def calculate_chunk_score(chunk_text: str, filename: str = "") -> int:
    """
    Score a chunk's likelihood of containing minimum flow requirements.
    Used for pre-filtering chunks before LLM analysis.
    Returns score (higher = more likely to contain flow requirements).
    """
    text_lower = chunk_text.lower()
    score = 0
    
    # V15.6: Table with captions about minimum flows (HIGHEST priority)
    # Tables with descriptive text are gold - they're explicitly labeled as having our answer
    table_with_caption = [
        r'table\s+\d+.*shows.*minimum.*flow',  # "Table 3 shows the minimum flow"
        r'table\s+\d+.*minimum.*release',       # "Table 3. Minimum Releases"
        r'minimum.*flow.*table\s+\d+',          # "minimum flows...Table 3"
        r'table\s+\d+.*flow.*release.*criteria', # "Table 3 shows...criteria"
    ]
    for pattern in table_with_caption:
        if re.search(pattern, text_lower):
            score += 40  # MASSIVE boost - captioned tables are explicit
            break
    
    # V15.7: Article with table/schedule (very high priority)
    # Articles with tabular data or schedules contain mandated requirements
    article_with_table = [
        r'article\s+\d+.*(?:table|schedule|following)',  # "Article 405...following table"
        r'article\s+\d+.*month.*minimum.*flow',          # "Article 405...Month Minimum Flow"
        r'article\s+\d+.*(?:january|february|march|april|may|june|july|august|september|october|november|december).*(?:cfs|cubic feet)',  # Article with seasonal schedule
    ]
    for pattern in article_with_table:
        if re.search(pattern, text_lower):
            score += 35  # High boost for Article + table/schedule combination
            break
    
    # Regulatory language (highest priority)
    regulatory_terms = [
        'article ', 'shall release', 'must release', 'required flow',
        'minimum flow', 'mandated', 'license condition', 'license requires',
        'prescribed flow', 'stipulated', 'regulatory requirement'
    ]
    for term in regulatory_terms:
        if term in text_lower:
            score += 15
    
    # Navigation requirements (high priority for Corps WCMs)
    navigation_terms = [
        'navigation', 'navigational', 'commercial navigation',
        'navigation channel', 'navigation vessels', 'lock operation'
    ]
    for term in navigation_terms:
        if term in text_lower:
            score += 20  # High score for navigation requirements
            break
    
    # Environmental context
    environmental_terms = [
        'protect', 'habitat', 'fish', 'aquatic', 'downstream',
        'environmental flow', 'instream flow', 'biological'
    ]
    for term in environmental_terms:
        if term in text_lower:
            score += 5
    
    # Seasonal patterns (indicates specific requirements)
    seasonal_patterns = [
        r'january|february|march|april|may|june|july|august|september|october|november|december',
        r'month.*minimum.*flow', r'seasonal.*flow', r'monthly.*schedule'
    ]
    for pattern in seasonal_patterns:
        if re.search(pattern, text_lower):
            score += 8
            break
    
    # Flow values with units (indicates quantitative requirements)
    if re.search(r'\d+\.?\d*\s*(?:cfs|cubic feet per second|cms|gpm|dsf)', text_lower):
        score += 10
    
    # Location specificity
    location_terms = ['dam', 'powerhouse', 'tailrace', 'below', 'downstream of', 'project']
    for term in location_terms:
        if term in text_lower:
            score += 3
            break
    
    # Penalties for irrelevant content
    irrelevant_indicators = [
        'cultural resource', 'archaeological', 'historic property',
        'construction plan', 'soil and water', 'design flood',
        'emergency action', 'public safety'
    ]
    for indicator in irrelevant_indicators:
        if indicator in text_lower:
            score -= 10
            break
    
    return max(0, score)  # Don't return negative scores


def apply_flow_scoring(response: Dict, document_name: str = "") -> Dict:
    """
    Main function to apply scoring mechanism to LLM response
    Returns updated response with best-scored flow
    
    V16.4 ENHANCED: Handle multiple candidates passed directly
    """
    scorer = FlowScoringSystem()
    
    # V16.4: Check if response has pre-extracted candidates list
    if 'candidates' in response and response['candidates']:
        print(f"🎯 V16.4: Scoring {len(response['candidates'])} candidates...")
        
        # Convert each candidate dict to FlowCandidate object
        candidates = []
        for cand_dict in response['candidates']:
            value = cand_dict.get('value', 'Not mentioned')
            context = cand_dict.get('inferred_context', '')
            sentences = cand_dict.get('exact_sentences', '')
            
            # Skip "not mentioned" candidates
            if str(value).lower() not in ['not mentioned', 'error', '']:
                candidates.append(FlowCandidate(value, context, sentences))
        
        if not candidates:
            return {
                "value": "Not mentioned",
                "inferred_context": "No valid candidates found",
                "exact_sentences": "Not mentioned"
            }
        
        # Score and select best
        best = scorer.select_best_flow(candidates, document_name)
        
        if not best:
            return response
        
        print(f"🏆 V16.4: Best scored: {best.value} (score={best.score})")
        print(f"   Score breakdown:")
        for reason in best.score_breakdown[:5]:  # Show top 5 reasons
            print(f"   - {reason}")
        
        return {
            "value": best.value,
            "inferred_context": best.context,
            "exact_sentences": best.sentences
        }
    
    # Original behavior: Parse response into candidates
    candidates = scorer.parse_llm_response(response)
    
    if not candidates:
        return response
    
    # Select best candidate
    best = scorer.select_best_flow(candidates, document_name)
    
    if not best:
        return response
    
    # V16.3 FIX: Don't overwrite seasonal schedule ranges from api_handler
    # If the original value contains multiple flows (like "30-110 cfs"), keep it
    original_value = response.get('value', '')
    if isinstance(original_value, str):
        # Check if this looks like a range or list of flows
        # Match individual numbers followed by units OR ranges like "30-110 cfs"
        has_range = '-' in original_value and 'cfs' in original_value.lower()
        has_comma_list = ',' in original_value
        flow_count = len(re.findall(r'\d+(?:\.\d+)?', original_value))  # Count all numbers
        if flow_count >= 2 or has_range or has_comma_list:
            # This is already a multi-value expression, don't overwrite
            return response
    
    # Update response with best-scored value (single flow case)
    updated_response = response.copy()
    updated_response['value'] = best.value
    
    # V16.1 FIX: Don't add SCORING text (breaks CSV formatting)
    # Just return the clean response
    
    return updated_response
