#!/usr/bin/env python3
"""
Compare V14 extraction results against ground truth (Observed.csv)
"""

import csv
import re
from pathlib import Path

def normalize_flow(value):
    """Normalize flow values for comparison"""
    if not value or value.strip() == "":
        return None
    
    value = value.strip().lower()
    
    # Check for "no minimum" patterns
    if any(pattern in value for pattern in [
        "no minimum", "no separate", "not mentioned", 
        "no mandated", "no fixed", "run-of-river"
    ]):
        return "NO_MINIMUM"
    
    # Extract numeric value (first number found)
    match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)', value)
    if match:
        # Remove commas and convert to float
        num_str = match.group(1).replace(',', '')
        return float(num_str)
    
    return None

def load_ground_truth(filepath):
    """Load ground truth from Observed.csv"""
    truth = {}
    with open(filepath, 'r', encoding='latin-1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['filename'].strip()
            if filename and filename.endswith('.pdf'):
                # Get the value and normalize it
                value = row['Value'].strip()
                truth[filename] = {
                    'raw': value,
                    'normalized': normalize_flow(value),
                    'project': row['Project name'].strip()
                }
    return truth

def load_v14_results(filepath):
    """Load V14 extraction results"""
    results = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['filename'].strip()
            if filename and filename.endswith('.pdf'):
                value = row['Minimum_Flow_Value'].strip()
                results[filename] = {
                    'raw': value,
                    'normalized': normalize_flow(value),
                    'project': row['Project_Name'].strip()
                }
    return results

def compare_values(truth_val, extracted_val, tolerance=0.05):
    """
    Compare two normalized values with tolerance
    Returns: ('exact', 'close', 'wrong', 'missing')
    """
    if truth_val is None or extracted_val is None:
        return 'missing'
    
    # Both are "no minimum" - exact match
    if truth_val == "NO_MINIMUM" and extracted_val == "NO_MINIMUM":
        return 'exact'
    
    # One is "no minimum", other is not - wrong
    if truth_val == "NO_MINIMUM" or extracted_val == "NO_MINIMUM":
        return 'wrong'
    
    # Both are numeric
    if isinstance(truth_val, (int, float)) and isinstance(extracted_val, (int, float)):
        # Exact match
        if truth_val == extracted_val:
            return 'exact'
        
        # Close match (within tolerance)
        if truth_val > 0:
            diff_pct = abs(truth_val - extracted_val) / truth_val
            if diff_pct <= tolerance:
                return 'close'
        
        return 'wrong'
    
    return 'wrong'

def main():
    # Load data
    ground_truth = load_ground_truth('/home/fbg/Extract_LLM_FBA/src/Observed.csv')
    v14_results = load_v14_results('/home/fbg/Extract_LLM_FBA/src/min_flow_results.csv')
    
    # Compare
    exact_matches = []
    close_matches = []
    wrong_extractions = []
    missing_in_v14 = []
    
    for filename, truth in ground_truth.items():
        if filename not in v14_results:
            missing_in_v14.append({
                'filename': filename,
                'project': truth['project'],
                'expected': truth['raw']
            })
            continue
        
        extracted = v14_results[filename]
        comparison = compare_values(truth['normalized'], extracted['normalized'])
        
        entry = {
            'filename': filename,
            'project': truth['project'],
            'expected': truth['raw'],
            'extracted': extracted['raw'],
            'expected_norm': truth['normalized'],
            'extracted_norm': extracted['normalized']
        }
        
        if comparison == 'exact':
            exact_matches.append(entry)
        elif comparison == 'close':
            close_matches.append(entry)
        else:
            wrong_extractions.append(entry)
    
    # Print results
    total = len(ground_truth)
    print("=" * 80)
    print("V14 ACCURACY REPORT")
    print("=" * 80)
    print(f"\nTotal ground truth entries: {total}")
    print(f"Total V14 extractions: {len(v14_results)}")
    print(f"\n{'='*80}")
    print(f"EXACT MATCHES: {len(exact_matches)}/{total} ({len(exact_matches)/total*100:.1f}%)")
    print(f"CLOSE MATCHES: {len(close_matches)}/{total} ({len(close_matches)/total*100:.1f}%)")
    print(f"WRONG: {len(wrong_extractions)}/{total} ({len(wrong_extractions)/total*100:.1f}%)")
    print(f"MISSING: {len(missing_in_v14)}/{total} ({len(missing_in_v14)/total*100:.1f}%)")
    print(f"{'='*80}")
    
    combined_correct = len(exact_matches) + len(close_matches)
    print(f"\n🎯 TOTAL ACCURACY: {combined_correct}/{total} ({combined_correct/total*100:.1f}%)")
    print(f"{'='*80}\n")
    
    # Show exact matches
    if exact_matches:
        print(f"\n✅ EXACT MATCHES ({len(exact_matches)}):")
        print("-" * 80)
        for entry in sorted(exact_matches, key=lambda x: x['project']):
            print(f"  {entry['project']}")
            print(f"    Expected: {entry['expected']}")
            print(f"    Extracted: {entry['extracted']}")
            print()
    
    # Show close matches
    if close_matches:
        print(f"\n⚠️  CLOSE MATCHES ({len(close_matches)}):")
        print("-" * 80)
        for entry in sorted(close_matches, key=lambda x: x['project']):
            print(f"  {entry['project']}")
            print(f"    Expected: {entry['expected']} → {entry['expected_norm']}")
            print(f"    Extracted: {entry['extracted']} → {entry['extracted_norm']}")
            print()
    
    # Show wrong extractions
    if wrong_extractions:
        print(f"\n❌ WRONG EXTRACTIONS ({len(wrong_extractions)}):")
        print("-" * 80)
        for entry in sorted(wrong_extractions, key=lambda x: x['project']):
            print(f"  {entry['project']} ({entry['filename']})")
            print(f"    Expected: {entry['expected']} → {entry['expected_norm']}")
            print(f"    Extracted: {entry['extracted']} → {entry['extracted_norm']}")
            print()
    
    # Show missing
    if missing_in_v14:
        print(f"\n🔍 MISSING FROM V14 ({len(missing_in_v14)}):")
        print("-" * 80)
        for entry in sorted(missing_in_v14, key=lambda x: x['project']):
            print(f"  {entry['project']} ({entry['filename']})")
            print(f"    Expected: {entry['expected']}")
            print()

if __name__ == '__main__':
    main()
