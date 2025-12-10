"""
🧠 REASONING LLM SELECTOR (RLS) - V17 with Structured Data
==========================================================

This module implements an LLM-based reasoning system to select the correct
minimum flow value from extracted candidates with full metadata.

ARCHITECTURE:
- V17: Works with structured candidates (metadata-rich)
- V16.5: Works with legacy candidates (value/context only)
- Fallback to scoring system if LLM is uncertain
- Can be easily enabled/disabled for A/B testing

USAGE:
    from api_handler_rls import select_best_flow_with_reasoning_v17
    
    result = select_best_flow_with_reasoning_v17(candidates, llm)
"""

import time
import json
import re
from typing import List, Dict, Optional


def select_best_flow_with_reasoning(
    candidates: List[Dict],
    llm,
    fallback_to_scoring: bool = True,
    verbose: bool = True
) -> Dict:
    """
    🧠 Uses LLM reasoning to select the correct minimum flow from candidates.
    
    Args:
        candidates: List of candidate dicts with 'value', 'context', 'sentences'
        llm: Ollama LLM instance
        fallback_to_scoring: If True, use scoring when LLM is uncertain
        verbose: Print detailed reasoning process
        
    Returns:
        Dict with 'value', 'context', 'reasoning', 'method' (llm|scoring)
    """
    
    if not candidates:
        return {
            'value': 'No flows extracted',
            'context': '',
            'reasoning': 'No candidates provided',
            'method': 'error'
        }
    
    if len(candidates) == 1:
        return {
            'value': candidates[0]['value'],
            'context': candidates[0].get('context', ''),
            'reasoning': 'Only one candidate, no selection needed',
            'method': 'single'
        }
    
    if verbose:
        print("\n" + "="*70)
        print("🧠 REASONING LLM SELECTOR (RLS) - V16.5")
        print("="*70)
        print(f"📊 Analyzing {len(candidates)} candidate flows...")
    
    # ========== STEP 1: Prepare candidates for LLM ==========
    candidate_text = _format_candidates_for_llm(candidates, verbose)
    
    # ========== STEP 2: Build reasoning prompt ==========
    prompt = _build_reasoning_prompt(candidate_text)
    
    # ========== STEP 3: Get LLM reasoning ==========
    try:
        if verbose:
            print("\n⏳ Sending to LLM for reasoning...")
        
        start_time = time.time()
        llm_response = llm.invoke(prompt).strip()
        elapsed = time.time() - start_time
        
        if verbose:
            print(f"✅ LLM responded in {elapsed:.1f}s")
            print(f"\n📝 LLM Response:")
            print("-" * 70)
            print(llm_response)
            print("-" * 70)
        
        # ========== STEP 4: Parse LLM response ==========
        selected_value, llm_context, justification = _parse_llm_response(llm_response)
        
        # ========== STEP 5: Validate LLM provided a value ==========
        if selected_value is None or selected_value.strip() == "":
            if verbose:
                print("\n⚠️ LLM did not provide a value - Falling back to scoring system...")
            if fallback_to_scoring:
                return _fallback_to_scoring(candidates, verbose)
            else:
                # Use first candidate as last resort
                return {
                    'value': candidates[0]['value'],
                    'context': candidates[0].get('context', ''),
                    'reasoning': 'LLM failed to provide value, used first candidate',
                    'method': 'error_fallback'
                }
        
        # ========== STEP 6: Use LLM's value directly (no matching needed!) ==========
        # The LLM is smart enough to extract the right value and context
        # We trust its judgment based on the tier rules
        
        if verbose:
            print(f"\n✅ RLS SELECTION: {selected_value}")
            print(f"📝 Context: {llm_context}")
            print(f"💡 Justification: {justification}")
        
        return {
            'value': selected_value,
            'context': llm_context,
            'reasoning': justification,
            'method': 'llm_reasoning'
        }
        
    except Exception as e:
        if verbose:
            print(f"\n❌ LLM reasoning failed: {e}")
        
        if fallback_to_scoring:
            if verbose:
                print("↩️ Falling back to scoring system...")
            return _fallback_to_scoring(candidates, verbose)
        else:
            return {
                'value': candidates[0]['value'],
                'context': candidates[0].get('context', ''),
                'reasoning': f'LLM error: {str(e)}',
                'method': 'error_fallback'
            }


def _format_candidates_for_llm(candidates: List[Dict], verbose: bool) -> str:
    """Format candidates into a clear numbered list for the LLM."""
    lines = []
    
    for i, candidate in enumerate(candidates, 1):
        value = candidate.get('value', 'UNKNOWN')
        context = candidate.get('context', candidate.get('sentences', ''))
        
        # Clean up context
        context = context.replace('\n', ' ').strip()
        if len(context) > 500:
            context = context[:500] + "..."
        
        lines.append(f"Candidate {i}: {value}")
        lines.append(f"Context: {context}")
        lines.append("")
    
    result = "\n".join(lines)
    
    if verbose:
        print("\n📋 Candidates prepared for LLM:")
        print("-" * 70)
        print(result)
        print("-" * 70)
    
    return result


def _build_reasoning_prompt_v17(candidate_text: str) -> str:
    """Build V17 RLS prompt - uses structured metadata for constrained selection."""
    
    prompt = f"""You are selecting the minimum legally required release for this hydroelectric project.

**CRITICAL**: You must ONLY choose from the provided candidates below. Do NOT invent or synthesize values.

**CANDIDATES**:
{candidate_text}

**DECISION RULES** (apply in strict priority order):

1. **Prefer MANDATED values** (marked MANDATED):
   - Values with "shall release", "must maintain", "Article XXX requires"
   - These are legally binding requirements
   - Choose the SMALLEST mandated value if multiple exist

2. **Prefer TEMPORAL minimums** (marked TEMPORAL):
   - "1 hour generation daily", "0.5 hour every other day"
   - These are valid minimum flow requirements
   - Do NOT convert to cfs - preserve as stated

3. **Prefer location = "at_dam"** over downstream gages:
   - Requirements at the dam/powerhouse take precedence
   - Downstream gage requirements are secondary

4. **Reject source_type = "cost_table"**:
   - These are budget items, not flow requirements
   - Never select these

5. **Prefer smaller numeric minimums**:
   - If multiple candidates are equally viable, choose smallest
   - Conservative approach for regulatory compliance

6. **Avoid operational targets** (NOT mandated):
   - "typical", "average", "normal operating range"
   - Only use if no mandated values exist

**OUTPUT FORMAT** (CRITICAL):
Return ONLY this JSON structure:
{{
  "chosen_candidate_id": "c3",
  "value": "3,000 cfs",
  "context": "Section 7-10.2.1: A minimum release of 3,000 cfs was established in 1992...",
  "explanation": "Selected c3 because it has explicit mandate language in Section 7-10.2.1 (Rule 1), is located at_dam (Rule 3), and is the smallest mandated value (Rule 5)."
}}

**IMPORTANT**:
- You MUST select one of the provided candidate IDs (c1, c2, c3, etc.)
- The 'value' should match the candidate's value field exactly
- The 'context' should come from the candidate's raw_evidence field
- The 'explanation' should reference which rules you applied

Now analyze and select (respond ONLY with valid JSON):
"""
    return prompt


def _parse_llm_response(response: str) -> tuple:
    """Parse LLM's JSON response to extract value, context, and justification."""
    
    try:
        # Try to parse as JSON first
        response_clean = response.strip()
        
        # Remove markdown code blocks if present
        if '```json' in response_clean:
            json_match = re.search(r'```json\s*\n(.*?)\n```', response_clean, re.DOTALL)
            if json_match:
                response_clean = json_match.group(1)
        elif '```' in response_clean:
            json_match = re.search(r'```\s*\n(.*?)\n```', response_clean, re.DOTALL)
            if json_match:
                response_clean = json_match.group(1)
        
        # Parse JSON
        data = json.loads(response_clean)
        
        value = data.get('value', None)
        context = data.get('context', '')
        justification = data.get('justification', '')
        
        return value, context, justification
        
    except (json.JSONDecodeError, ValueError):
        # Fallback: Try old format (Answer: / Justification:)
        lines = response.split('\n')
        selected_value = None
        justification = ""
        
        for line in lines:
            line = line.strip()
            
            if line.lower().startswith('answer:'):
                selected_value = line.split(':', 1)[1].strip()
            elif line.lower().startswith('justification:'):
                justification = line.split(':', 1)[1].strip()
        
        # If still no value, try to extract first flow pattern
        if selected_value is None:
            match = re.search(r'(\d{1,3}(?:,?\d{3})*(?:\.\d+)?)\s*(?:cfs|cubic feet per second)', response, re.IGNORECASE)
            if match:
                selected_value = match.group(1)
        
        if justification == "":
            justification = response
        
        return selected_value, "", justification


def _is_llm_uncertain(response: str, selected_value: Optional[str]) -> bool:
    """Check if LLM expressed uncertainty."""
    
    response_lower = response.lower()
    
    # Explicit uncertainty
    if 'uncertain' in response_lower:
        return True
    
    # No value found
    if selected_value is None:
        return True
    
    # Weak confidence indicators
    weak_indicators = [
        'not sure', 'unclear', 'difficult to determine',
        'cannot determine', 'insufficient information',
        'ambiguous', 'could be', 'might be', 'possibly'
    ]
    
    for indicator in weak_indicators:
        if indicator in response_lower:
            return True
    
    return False


def _find_matching_candidate(candidates: List[Dict], selected_value: str) -> Optional[Dict]:
    """Find the candidate that matches the LLM's selected value."""
    
    if selected_value is None:
        return None
    
    # Normalize selected value (remove commas, spaces, etc.)
    selected_normalized = re.sub(r'[,\s]', '', selected_value.lower())
    selected_normalized = re.sub(r'cfs|cubic feet per second', '', selected_normalized).strip()
    
    for candidate in candidates:
        candidate_value = str(candidate.get('value', ''))
        candidate_normalized = re.sub(r'[,\s]', '', candidate_value.lower())
        candidate_normalized = re.sub(r'cfs|cubic feet per second', '', candidate_normalized).strip()
        
        # Try exact match
        if selected_normalized == candidate_normalized:
            return candidate
        
        # Try numeric match
        try:
            selected_num = float(selected_normalized)
            candidate_num = float(candidate_normalized)
            if abs(selected_num - candidate_num) < 0.1:
                return candidate
        except:
            pass
        
        # Try if selected value is contained in candidate
        if selected_normalized in candidate_normalized or candidate_normalized in selected_normalized:
            return candidate
    
    return None


def _fallback_to_scoring(candidates: List[Dict], verbose: bool) -> Dict:
    """Fallback to the original scoring system."""
    
    if verbose:
        print("\n🔄 Using rule-based scoring as fallback...")
    
    # Import the scoring function from api_handler
    # This avoids circular imports
    from api_handler import ask_ollama_to_select_best
    
    # The scoring function expects candidates in a specific format
    # We'll just return the first candidate with a note
    # (Full integration would require more refactoring)
    
    best_candidate = candidates[0]
    max_score = 0
    
    # Simple scoring fallback (simplified version)
    for candidate in candidates:
        score = 0
        context = candidate.get('context', '').lower()
        
        # MANDATE language
        if any(kw in context for kw in ['established', 'mandated', 'required']):
            score += 55
        
        # DAM location
        if 'dam' in context:
            score += 15
        
        # OPERATIONAL
        if any(kw in context for kw in ['operational', 'irrigation', 'navigation']):
            score += 35
        
        if score > max_score:
            max_score = score
            best_candidate = candidate
    
    if verbose:
        print(f"✅ Scoring selected: {best_candidate['value']} (score: {max_score})")
    
    return {
        'value': best_candidate['value'],
        'context': best_candidate.get('context', ''),
        'reasoning': f'Selected by fallback scoring (score: {max_score})',
        'method': 'scoring_fallback'
    }


# ============================================================================
# V17 STRUCTURED DATA FUNCTIONS
# ============================================================================

def _build_v17_rls_prompt(candidates_text: str) -> str:
    """Build V17 RLS prompt for structured candidates with metadata."""
    
    return f"""You are selecting the minimum legally required release for this hydroelectric project.
You MUST choose from the provided candidates. DO NOT invent new values.

**CANDIDATES**:
{candidates_text}

**SELECTION RULES** (strict priority order):

1. **Mandated values** (is_mandated = true):
   - ALWAYS prioritize candidates with mandate language
   - Among mandated values, prefer:
     * Temporal minimums (is_temporal = true) over numeric
     * At-dam location over downstream gages
     * Smallest numeric value if multiple at-dam numeric mandated values

2. **Reject obviously wrong**:
   - Candidates from cost tables (check raw_evidence for $/unit, contractor, budget)
   - Operational targets without mandate (is_operational = true AND is_mandated = false)
   - Downstream gage values when at-dam values exist

3. **Temporal minimums**:
   - If no mandated values exist, temporal minimums are VALID
   - Prefer temporal over operational numeric values

4. **Conservative selection**:
   - Among viable numeric at-dam values, prefer smallest
   - Never choose large "plausible" values over small mandated ones

**OUTPUT FORMAT** (return ONLY this JSON):
{{
  "chosen_candidate_id": "c3",
  "explanation": "Candidate 3 has is_mandated=true with Article 401 language, and is_temporal=true, satisfying Rule 1. Temporal mandate takes priority over numeric operational values."
}}

**CRITICAL RULES**:
- You MUST choose a candidate_id from the list above
- DO NOT return "uncertain" - make your best selection
- DO NOT invent values - only select from provided candidates
- Base decision on metadata fields (is_mandated, is_temporal, location)

Analyze and select (return ONLY the JSON object):"""


def select_best_flow_with_reasoning_v17(
    candidates: List[Dict],
    llm,
    verbose: bool = True
) -> Dict:
    """
    🧠 V17 RLS: Select best flow from structured candidates with full metadata.
    
    Args:
        candidates: List of structured candidate dicts with metadata
        llm: Ollama LLM instance
        verbose: Print detailed reasoning process
        
    Returns:
        Dict with 'value', 'context', 'reasoning', 'method'
    """
    
    if not candidates:
        return {
            'value': 'No flows extracted',
            'context': '',
            'reasoning': 'No candidates provided',
            'method': 'error'
        }
    
    # ========== Format candidates for LLM ==========
    candidate_text = _format_structured_candidates_for_llm(candidates)
    
    if verbose:
        print(f"\n📋 V17 RLS: Analyzing {len(candidates)} structured candidates...")
    
    # ========== Build prompt ==========
    prompt = _build_v17_rls_prompt(candidate_text)
    
    # ========== Get LLM reasoning ==========
    try:
        if verbose:
            print("⏳ Sending to V17 RLS...")
        
        start_time = time.time()
        llm_response = llm.invoke(prompt).strip()
        elapsed = time.time() - start_time
        
        if verbose:
            print(f"✅ V17 RLS responded in {elapsed:.1f}s")
            print(f"\n📝 RLS Response:")
            print("-" * 70)
            print(llm_response)
            print("-" * 70)
        
        # ========== Parse LLM response ==========
        chosen_id, explanation = _parse_v17_rls_response(llm_response)
        
        if chosen_id is None:
            if verbose:
                print("\n⚠️ V17 RLS failed to select - using first candidate")
            return {
                'value': candidates[0]['value'],
                'context': candidates[0].get('raw_evidence', ''),
                'reasoning': 'RLS parsing failed, used first candidate',
                'method': 'rls_error'
            }
        
        # ========== Find selected candidate ==========
        selected = None
        for c in candidates:
            if c.get('candidate_id') == chosen_id:
                selected = c
                break
        
        if selected is None:
            if verbose:
                print(f"\n⚠️ V17 RLS selected '{chosen_id}' but not found in candidates")
            return {
                'value': candidates[0]['value'],
                'context': candidates[0].get('raw_evidence', ''),
                'reasoning': f'RLS selected non-existent {chosen_id}, used first candidate',
                'method': 'rls_error'
            }
        
        if verbose:
            print(f"\n✅ V17 RLS SELECTION: {selected['value']}")
            print(f"💡 Explanation: {explanation}")
        
        return {
            'value': selected['value'],
            'context': selected.get('raw_evidence', ''),
            'reasoning': explanation,
            'method': 'rls_v17'
        }
        
    except Exception as e:
        if verbose:
            print(f"\n❌ V17 RLS error: {e}")
        
        return {
            'value': candidates[0]['value'],
            'context': candidates[0].get('raw_evidence', ''),
            'reasoning': f'RLS error: {str(e)}',
            'method': 'rls_error'
        }


def _format_structured_candidates_for_llm(candidates: List[Dict]) -> str:
    """Format structured V17 candidates for RLS."""
    
    lines = []
    for c in candidates:
        cid = c.get('candidate_id', 'unknown')
        value = c.get('value', 'UNKNOWN')
        mandated = c.get('is_mandated', False)
        temporal = c.get('is_temporal', False)
        operational = c.get('is_operational', False)
        location = c.get('location', 'unknown')
        evidence = c.get('raw_evidence', 'No evidence')[:200]
        
        lines.append(f"{cid}: {value}")
        lines.append(f"  - Mandated: {mandated}")
        lines.append(f"  - Temporal: {temporal}")
        lines.append(f"  - Operational: {operational}")
        lines.append(f"  - Location: {location}")
        lines.append(f"  - Evidence: {evidence}")
        lines.append("")
    
    return "\n".join(lines)


def _parse_v17_rls_response(response: str) -> tuple:
    """Parse V17 RLS JSON response."""
    
    try:
        # Remove markdown code blocks if present
        response_clean = response.strip()
        if '```json' in response_clean:
            json_match = re.search(r'```json\s*\n(.*?)\n```', response_clean, re.DOTALL)
            if json_match:
                response_clean = json_match.group(1)
        elif '```' in response_clean:
            json_match = re.search(r'```\s*\n(.*?)\n```', response_clean, re.DOTALL)
            if json_match:
                response_clean = json_match.group(1)
        
        # Parse JSON
        data = json.loads(response_clean)
        chosen_id = data.get('chosen_candidate_id')
        explanation = data.get('explanation', '')
        
        return chosen_id, explanation
        
    except Exception:
        # Fallback: try to extract candidate_id from text
        match = re.search(r'candidate[_\s]*(\w+)', response, re.IGNORECASE)
        if match:
            return f"c{match.group(1)}", response
        return None, response
