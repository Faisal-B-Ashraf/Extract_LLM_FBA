"""
V17 Deterministic Selector - Rule-based selection before RLS
"""
from typing import List, Dict, Optional, Tuple

def select_deterministic(candidates: List[Dict]) -> Tuple[Optional[Dict], str]:
    """
    Apply deterministic selection rules before RLS.
    
    Returns: (selected_candidate, method)
    - If deterministic selection succeeds: (candidate, method_name)
    - If RLS needed: (None, "needs_rls")
    """
    
    if not candidates:
        return None, "no_candidates"
    
    # Rule 1: Single candidate - no selection needed
    if len(candidates) == 1:
        return candidates[0], "deterministic_single"
    
    # Rule 2: Mandated values exist - select smallest mandated
    mandated = [c for c in candidates if c.get('is_mandated', False)]
    if mandated:
        # If only one mandated value, use it
        if len(mandated) == 1:
            return mandated[0], "deterministic_mandated"
        
        # Multiple mandated - prefer temporal over numeric
        temporal_mandated = [c for c in mandated if c.get('is_temporal', False)]
        if temporal_mandated:
            if len(temporal_mandated) == 1:
                return temporal_mandated[0], "deterministic_temporal_mandated"
            # Multiple temporal mandated - needs RLS
            return None, "needs_rls"
        
        # Multiple numeric mandated - select smallest at-dam
        at_dam_mandated = [c for c in mandated if c.get('location') == 'at_dam']
        if at_dam_mandated:
            # Get smallest numeric
            numeric_mandated = [c for c in at_dam_mandated if c.get('numeric_value') is not None]
            if numeric_mandated:
                smallest = min(numeric_mandated, key=lambda x: x['numeric_value'])
                if len([c for c in numeric_mandated if c['numeric_value'] == smallest['numeric_value']]) == 1:
                    return smallest, "deterministic_smallest_mandated"
        
        # Multiple mandated with same value or need tie-breaking - needs RLS
        return None, "needs_rls"
    
    # Rule 3: Temporal minima exist (non-mandated)
    temporal = [c for c in candidates if c.get('is_temporal', False)]
    if temporal:
        if len(temporal) == 1:
            return temporal[0], "deterministic_temporal"
        # Multiple temporal - needs RLS
        return None, "needs_rls"
    
    # Rule 4: Only at-dam numeric values
    at_dam = [c for c in candidates if c.get('location') == 'at_dam']
    if at_dam:
        # Filter out operational targets
        non_operational = [c for c in at_dam if not c.get('is_operational', False)]
        if non_operational:
            numeric = [c for c in non_operational if c.get('numeric_value') is not None]
            if numeric:
                if len(numeric) == 1:
                    return numeric[0], "deterministic_at_dam"
                # Multiple numeric at-dam - needs RLS for tie-break
                return None, "needs_rls"
    
    # Rule 5: Cannot determine deterministically - needs RLS
    return None, "needs_rls"


def format_candidates_for_rls(candidates: List[Dict]) -> str:
    """Format structured candidates for RLS prompt."""
    
    lines = []
    for i, c in enumerate(candidates, 1):
        lines.append(f"Candidate {i}:")
        lines.append(f"  Value: {c.get('value', 'UNKNOWN')}")
        lines.append(f"  Mandated: {c.get('is_mandated', False)}")
        lines.append(f"  Temporal: {c.get('is_temporal', False)}")
        lines.append(f"  Location: {c.get('location', 'unknown')}")
        lines.append(f"  Evidence: {c.get('raw_evidence', 'No evidence')[:150]}")
        lines.append("")
    
    return "\n".join(lines)
