"""
V17 DETERMINISTIC SELECTOR
==========================

Applies rule-based selection BEFORE calling RLS LLM.
This eliminates many unnecessary LLM calls and prevents wrong selections.

Decision Hierarchy:
1. If any candidate has is_mandated=true → Return smallest mandated value
2. If temporal minimum exists → Return temporal description
3. If multiple viable numeric at-dam minima → Pass to RLS
4. If only one candidate → Return directly
"""

from typing import List, Dict, Optional


def deterministic_select(candidates: List[Dict], verbose: bool = False) -> Optional[Dict]:
    """
    Apply deterministic selection rules BEFORE RLS.
    
    Returns:
        - Dict with selected candidate if deterministic selection succeeds
        - None if RLS should decide (multiple viable candidates)
    """
    
    if not candidates or len(candidates) == 0:
        if verbose:
            print("\n⚠️ No candidates provided")
        return {'value': 'Not mentioned', 'context': '', 'reasoning': 'No candidates extracted', 'method': 'deterministic'}
    
    if verbose:
        print(f"\n🔍 Deterministic Selector analyzing {len(candidates)} candidates...")
    
    # =============================================================
    # RULE 1: Single Candidate → Return directly
    # =============================================================
    if len(candidates) == 1:
        c = candidates[0]
        if verbose:
            print(f"✅ DETERMINISTIC: Only one candidate → {c.get('value')}")
        return {
            'value': c.get('value'),
            'context': c.get('raw_evidence', ''),
            'reasoning': 'Single candidate - no selection needed',
            'method': 'deterministic_single'
        }
    
    # =============================================================
    # RULE 2: Filter out obvious rejects
    # =============================================================
    viable_candidates = []
    for c in candidates:
        # Reject cost tables
        if c.get('source_type') == 'cost_table':
            if verbose:
                print(f"❌ Rejected (cost_table): {c.get('value')}")
            continue
        
        # Reject "No separate requirement" if other candidates exist
        if 'no separate' in c.get('value', '').lower() or 'not mentioned' in c.get('value', '').lower():
            if verbose:
                print(f"❌ Rejected (no requirement): {c.get('value')}")
            continue
        
        # Accept as viable
        viable_candidates.append(c)
    
    if len(viable_candidates) == 0:
        if verbose:
            print("⚠️ All candidates rejected by filters")
        return {'value': 'Not mentioned', 'context': '', 'reasoning': 'All candidates filtered out', 'method': 'deterministic'}
    
    if len(viable_candidates) == 1:
        c = viable_candidates[0]
        if verbose:
            print(f"✅ DETERMINISTIC: After filtering → {c.get('value')}")
        return {
            'value': c.get('value'),
            'context': c.get('raw_evidence', ''),
            'reasoning': 'Single viable candidate after filtering',
            'method': 'deterministic_filtered'
        }
    
    # =============================================================
    # RULE 3: If any candidate has is_mandated=true
    # → Return SMALLEST mandated value
    # =============================================================
    mandated_candidates = [c for c in viable_candidates if c.get('is_mandated') == True]
    
    if len(mandated_candidates) > 0:
        if verbose:
            print(f"✅ Found {len(mandated_candidates)} mandated candidate(s)")
        
        # If only one mandated, return it
        if len(mandated_candidates) == 1:
            c = mandated_candidates[0]
            if verbose:
                print(f"✅ DETERMINISTIC: Single mandated value → {c.get('value')}")
            return {
                'value': c.get('value'),
                'context': c.get('raw_evidence', ''),
                'reasoning': 'Single mandated value found with explicit mandate language',
                'method': 'deterministic_mandated_single'
            }
        
        # Multiple mandated → return smallest numeric
        numeric_mandated = [c for c in mandated_candidates if c.get('numeric_value') is not None]
        
        if len(numeric_mandated) > 0:
            smallest = min(numeric_mandated, key=lambda x: x.get('numeric_value', float('inf')))
            if verbose:
                print(f"✅ DETERMINISTIC: Smallest mandated value → {smallest.get('value')}")
            return {
                'value': smallest.get('value'),
                'context': smallest.get('raw_evidence', ''),
                'reasoning': f"Smallest of {len(mandated_candidates)} mandated values (applying conservative principle)",
                'method': 'deterministic_mandated_smallest'
            }
    
    # =============================================================
    # RULE 4: If temporal minimum exists → Return it
    # =============================================================
    temporal_candidates = [c for c in viable_candidates if c.get('is_temporal') == True]
    
    if len(temporal_candidates) > 0:
        if verbose:
            print(f"✅ Found {len(temporal_candidates)} temporal candidate(s)")
        
        # Prioritize mandated temporal
        mandated_temporal = [c for c in temporal_candidates if c.get('is_mandated') == True]
        if len(mandated_temporal) > 0:
            c = mandated_temporal[0]
            if verbose:
                print(f"✅ DETERMINISTIC: Mandated temporal → {c.get('value')}")
            return {
                'value': c.get('value'),
                'context': c.get('raw_evidence', ''),
                'reasoning': 'Mandated temporal minimum flow requirement',
                'method': 'deterministic_temporal_mandated'
            }
        
        # Otherwise return first temporal
        c = temporal_candidates[0]
        if verbose:
            print(f"✅ DETERMINISTIC: Temporal minimum → {c.get('value')}")
        return {
            'value': c.get('value'),
            'context': c.get('raw_evidence', ''),
            'reasoning': 'Temporal minimum flow requirement',
            'method': 'deterministic_temporal'
        }
    
    # =============================================================
    # RULE 5: Multiple viable numeric at-dam minima
    # → Pass to RLS for tie-breaking
    # =============================================================
    if verbose:
        print(f"🤖 DEFER TO RLS: {len(viable_candidates)} viable candidates need LLM reasoning")
    
    return None  # Signal that RLS should decide


def format_candidates_for_rls(candidates: List[Dict]) -> str:
    """Format candidates for RLS prompt."""
    
    lines = []
    for c in candidates:
        candidate_id = c.get('candidate_id', 'unknown')
        value = c.get('value', 'unknown')
        is_mandated = "✅ MANDATED" if c.get('is_mandated') else "❌ not mandated"
        is_temporal = "⏰ TEMPORAL" if c.get('is_temporal') else ""
        location = c.get('location', 'unknown')
        source_type = c.get('source_type', 'unknown')
        evidence = c.get('raw_evidence', '')
        
        lines.append(f"{candidate_id}: {value}")
        lines.append(f"   Status: {is_mandated} {is_temporal}")
        lines.append(f"   Location: {location} | Source: {source_type}")
        lines.append(f"   Evidence: {evidence[:200]}...")
        lines.append("")
    
    return "\n".join(lines)
