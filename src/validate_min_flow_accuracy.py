#!/usr/bin/env python3
"""
GROUND TRUTH: Minimum Flow Extraction Accuracy Validator
This is the single source of truth for validating minimum flow extraction accuracy.
Use this script to get consistent, verified accuracy numbers.
"""

import pandas as pd
import re

def validate_min_flow_extraction(llm_value, observed_value):
    """
    Validates if LLM extraction matches observed ground truth.
    
    Returns: True if correct, False if wrong
    
    Logic:
    1. Check if LLM found nothing ("not mentioned", "not found", "nan") → WRONG
    2. Check if observed text appears in LLM result → CORRECT
    3. Check if any numbers match between observed and LLM → CORRECT
    4. Otherwise → WRONG
    """
    # Convert to strings
    obs_str = str(observed_value).strip()
    llm_str = str(llm_value).strip()
    
    # Check if LLM found nothing (BEFORE normalization!)
    llm_lower = llm_str.lower()
    if 'not mentioned' in llm_lower or 'not found' in llm_lower or llm_str == 'nan':
        return False
    
    # Normalize for comparison
    obs_norm = re.sub(r'[^a-z0-9]', '', obs_str.lower())
    llm_norm = re.sub(r'[^a-z0-9]', '', llm_str.lower())
    
    # Check if observed appears in LLM
    if obs_norm in llm_norm or llm_norm in obs_norm:
        return True
    
    # Check if any numbers match
    obs_nums = set(re.findall(r'\d+', obs_str.replace(',', '')))
    llm_nums = set(re.findall(r'\d+', llm_str.replace(',', '')))
    
    if obs_nums & llm_nums:  # Set intersection - any common numbers
        return True
    
    return False


def validate_pipeline(results_csv, value_column, observed_csv='min_flow_results_Observed.csv', pipeline_name='Pipeline'):
    """
    Validate a pipeline's minimum flow extraction against ground truth.
    
    Args:
        results_csv: Path to pipeline results CSV
        value_column: Column name containing minimum flow values
        observed_csv: Path to observed ground truth CSV
        pipeline_name: Name for display
        
    Returns:
        dict with accuracy metrics
    """
    # Load data
    observed = pd.read_csv(observed_csv)
    results = pd.read_csv(results_csv)
    
    correct_list = []
    wrong_list = []
    
    for idx, row in results.iterrows():
        file = row['filename'].replace('.pdf', '')
        obs_match = observed[observed['filename'].str.replace('.pdf', '', regex=False) == file]
        
        if len(obs_match) > 0:
            observed_val = str(obs_match.iloc[0]['Manual Value']).strip()
            llm_val = str(row[value_column]).strip()
            
            if validate_min_flow_extraction(llm_val, observed_val):
                correct_list.append((file, observed_val, llm_val))
            else:
                wrong_list.append((file, observed_val, llm_val))
    
    total = len(correct_list) + len(wrong_list)
    accuracy = len(correct_list) / total * 100 if total > 0 else 0
    
    return {
        'pipeline_name': pipeline_name,
        'correct': len(correct_list),
        'wrong': len(wrong_list),
        'total': total,
        'accuracy': accuracy,
        'correct_list': correct_list,
        'wrong_list': wrong_list
    }


if __name__ == "__main__":
    print("="*100)
    print("OFFICIAL MINIMUM FLOW EXTRACTION ACCURACY VALIDATION")
    print("="*100)
    
    # Validate Complex Pipeline (Pipeline 1)
    complex_metrics = validate_pipeline(
        results_csv='min_flow_results.csv',
        value_column='Minimum_Flow_Value',
        pipeline_name='Complex Pipeline (Pipeline 1)'
    )
    
    # Validate Simple Pipeline (Pipeline 3)
    simple_metrics = validate_pipeline(
        results_csv='multi_variable_simple_results.csv',
        value_column='minimum_flow',
        pipeline_name='Simple Pipeline (Pipeline 3)'
    )
    
    print(f"\n{simple_metrics['pipeline_name']}:")
    print(f"  Correct: {simple_metrics['correct']}/{simple_metrics['total']}")
    print(f"  Accuracy: {simple_metrics['accuracy']:.1f}%")
    
    print(f"\n{complex_metrics['pipeline_name']}:")
    print(f"  Correct: {complex_metrics['correct']}/{complex_metrics['total']}")
    print(f"  Accuracy: {complex_metrics['accuracy']:.1f}%")
    
    print(f"\nComparison:")
    improvement = complex_metrics['accuracy'] - simple_metrics['accuracy']
    print(f"  Absolute improvement: {improvement:.1f} percentage points")
    print(f"  Relative improvement: {(complex_metrics['accuracy']/simple_metrics['accuracy'] - 1)*100:.1f}%")
    
    print("\n" + "="*100)
    print("VERIFIED NUMBERS FOR PUBLICATIONS/FIGURES:")
    print("="*100)
    print(f"Simple Pipeline:  {simple_metrics['accuracy']:.1f}% ({simple_metrics['correct']}/{simple_metrics['total']})")
    print(f"Complex Pipeline: {complex_metrics['accuracy']:.1f}% ({complex_metrics['correct']}/{complex_metrics['total']})")
    print(f"Improvement:      +{improvement:.1f} percentage points")
    print("="*100)
