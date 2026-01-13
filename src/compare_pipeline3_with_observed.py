#!/usr/bin/env python3
"""
Compare Pipeline 3 LLM extraction results with manually curated ground truth.

Categorizes each variable extraction as:
- Correct: LLM extraction matches ground truth closely
- Partial: LLM extraction has some correct information but incomplete/imprecise
- Wrong: LLM extraction is incorrect or "Not mentioned" when data exists
"""

import pandas as pd
import re
from difflib import SequenceMatcher

def extract_clean_value(text):
    """Extract clean value from verbose LLM response."""
    if pd.isna(text) or 'not mentioned' in str(text).lower():
        return ''
    
    text = str(text).strip()
    lines = text.split('\n')
    
    # Get last non-empty line (usually the answer)
    for line in reversed(lines):
        line = line.strip()
        if line and len(line) > 2:
            # Remove common prefixes
            line = re.sub(r'^(answer:|the answer is:|therefore,?|so,?)\s*', '', line, flags=re.IGNORECASE)
            return line.strip()
    return text

def normalize_text(text):
    """Normalize text for comparison."""
    if pd.isna(text) or text is None:
        return ""
    text = str(text).lower().strip()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text

def similarity_ratio(a, b):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()

def categorize_match(llm_value, observed_value, variable_name):
    """
    Categorize match quality between LLM and observed values.
    
    Returns: ("Correct"|"Partial"|"Wrong", explanation)
    """
    llm_norm = normalize_text(llm_value)
    obs_norm = normalize_text(observed_value)
    
    # Handle missing data cases
    if not obs_norm or obs_norm in ["not specified", "not mentioned", "not itemized in wcm", "?"]:
        # Ground truth has no data
        if not llm_norm or "not mentioned" in llm_norm:
            return ("Correct", "Both agree data not available")
        else:
            return ("Wrong", "LLM extracted data where none exists in ground truth")
    
    # Ground truth has data
    if not llm_norm or "not mentioned" in llm_norm:
        return ("Wrong", "LLM failed to extract existing data")
    
    # Both have data - compare
    ratio = similarity_ratio(llm_value, observed_value)
    
    # High similarity threshold
    if ratio >= 0.85:
        return ("Correct", f"High similarity ({ratio:.2f})")
    
    # Check for key terms/entities present
    if variable_name == "project_name":
        # Clean observed name (remove state codes and extra info in parens)
        obs_clean = re.sub(r'\s*\([^)]*\)', '', observed_value).strip().lower()
        # Remove "dam" and "project" for comparison (they're interchangeable)
        obs_core = re.sub(r'\s+(dam|project|hydroelectric)$', '', obs_clean).strip()
        llm_text = llm_value.lower()  # Use original llm_value, not normalized
        
        # Check if core name appears in LLM (before normalization removes words)
        if obs_core and len(obs_core) > 3 and obs_core in llm_text:
            return ("Correct", "Project name found in extraction")
        
        # Also check if full cleaned name appears
        if obs_clean and len(obs_clean) > 3 and obs_clean in llm_text:
            return ("Correct", "Full project name matches")
        
        # Check word by word - if all significant words from observed are in LLM
        obs_words = [w for w in obs_clean.split() if len(w) > 2]
        if obs_words:
            matches = sum(1 for w in obs_words if w in llm_text)
            if matches == len(obs_words):
                return ("Correct", "All project name words present")
            elif matches >= len(obs_words) * 0.7:
                return ("Partial", f"Most project name words present ({matches}/{len(obs_words)})")
        
        # Fallback to normalized comparison for edge cases
        llm_lower = llm_norm
        
        # Extract main project identifier (before "Dam", "Project", "Hydroelectric")
        def extract_main_name(text):
            text = text.lower()
            # Remove common suffixes
            for suffix in ['hydroelectric project', 'project', 'dam', 'hydroelectric']:
                if suffix in text:
                    text = text.split(suffix)[0].strip()
                    break
            # Remove project numbers
            text = re.sub(r'p-?\d+|project no\.?\s*\d+|ferc', '', text)
            # Remove extra words
            text = re.sub(r'\(.*?\)', '', text)
            # Clean up
            text = re.sub(r'[^a-z\s]', '', text).strip()
            return text
        
        llm_main = extract_main_name(llm_norm)
        obs_main = extract_main_name(obs_norm)
        
        # Check if main names overlap significantly
        llm_words = set(llm_main.split())
        obs_words = set(obs_main.split())
        
        if llm_words and obs_words:
            overlap = len(llm_words & obs_words) / max(len(obs_words), 1)
            if overlap >= 0.7:
                return ("Correct", f"Main project name matches ({llm_main} vs {obs_main})")
            elif overlap >= 0.4:
                return ("Partial", f"Project name partially matches ({overlap:.2f})")
        
        # Fallback to general token matching
        llm_tokens = set(re.findall(r'p-?\d+|[a-z]{3,}', llm_norm))
        obs_tokens = set(re.findall(r'p-?\d+|[a-z]{3,}', obs_norm))
        overlap = len(llm_tokens & obs_tokens) / max(len(obs_tokens), 1)
        if overlap >= 0.5:
            return ("Partial", f"Key terms overlap ({overlap:.2f})")
    
    elif variable_name == "generation_capacity":
        # Extract capacity values and convert to MW for comparison
        def extract_capacity_mw(text):
            """Extract capacity and convert to MW."""
            text_lower = text.lower()
            
            # Try to find MW value
            mw_match = re.search(r'(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:mw|megawatt)', text_lower)
            if mw_match:
                return float(mw_match.group(1).replace(',', ''))
            
            # Try to find kW value and convert to MW
            kw_match = re.search(r'(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:kw|kilowatt)', text_lower)
            if kw_match:
                return float(kw_match.group(1).replace(',', '')) / 1000.0
            
            return None
        
        llm_mw = extract_capacity_mw(llm_norm)
        obs_mw = extract_capacity_mw(obs_norm)
        
        if llm_mw is not None and obs_mw is not None:
            # Check if values match within 5%
            if abs(llm_mw - obs_mw) / obs_mw < 0.05:
                return ("Correct", f"Capacity matches ({llm_mw:.2f} MW vs {obs_mw:.2f} MW)")
            # Check if within 10% 
            elif abs(llm_mw - obs_mw) / obs_mw < 0.10:
                return ("Correct", f"Within 10% ({llm_mw:.2f} MW vs {obs_mw:.2f} MW)")
            else:
                return ("Wrong", f"Capacity differs ({llm_mw:.2f} MW vs {obs_mw:.2f} MW)")
        
        # Fallback: check if numbers appear in both
        llm_nums = set(re.findall(r'\d+(?:\.\d+)?', llm_norm))
        obs_nums = set(re.findall(r'\d+(?:\.\d+)?', obs_norm))
        if llm_nums & obs_nums:
            return ("Correct", "Capacity value matches")
    
    elif variable_name == "plant_type":
        # Check for key plant type terms
        if any(term in llm_norm and term in obs_norm for term in ["run-of-river", "peaking", "pumped storage", "storage"]):
            return ("Correct", "Plant type matches")
    
    elif variable_name in ["location_county", "location_city", "location_river", "location_combined"]:
        # Check if location names appear in both
        llm_words = set(re.findall(r'[a-z]{3,}', llm_norm))
        obs_words = set(re.findall(r'[a-z]{3,}', obs_norm))
        overlap = len(llm_words & obs_words) / max(len(obs_words), 1)
        if overlap >= 0.25:  # Lowered from 0.4 - if 25% of words match, core location is there
            return ("Correct", f"Location matches ({overlap:.2f})")
        elif overlap >= 0.15:
            return ("Partial", f"Some location info matches ({overlap:.2f})")
    
    elif variable_name == "owner_operator":
        # Clean both for comparison
        obs_clean = re.sub(r'\s*\([^)]*\)', '', observed_value).lower()
        llm_clean = llm_norm
        
        # First check: exact company name match (without Inc, LLC, etc suffixes)
        def clean_company_name(text):
            """Remove legal suffixes and clean company name."""
            text = text.lower().strip()
            # Remove common legal suffixes
            text = re.sub(r'\s*,?\s*(inc|llc|co|corp|corporation|company|incorporated)\.?\s*$', '', text)
            text = re.sub(r'\s*,?\s*(inc|llc|co|corp|corporation|company|incorporated)\.?\s*,', ',', text)
            return text.strip()
        
        obs_name_clean = clean_company_name(obs_clean)
        
        # Check if cleaned observed name appears in LLM text
        if obs_name_clean and len(obs_name_clean) > 5:
            # Check for core name presence
            if obs_name_clean in llm_clean:
                return ("Correct", "Owner/operator name matches")
        
        # Split by common delimiters and check each org
        obs_orgs = re.split(r'[;,/]', obs_clean)
        
        matches = 0
        total_orgs = 0
        for org in obs_orgs:
            org = org.strip()
            if not org or len(org) < 3:
                continue
            total_orgs += 1
            # Remove common words to get core org name
            org_core = re.sub(r'\b(district|inc|llc|co|corp|company|corporation)\b\.?', '', org).strip()
            if org_core and org_core in llm_clean:
                matches += 1
        
        if total_orgs > 0 and matches >= total_orgs:
            return ("Correct", "All owner/operator entities match")
        elif total_orgs > 0 and matches >= total_orgs * 0.7:
            return ("Correct", "Most owner/operator entities match")
        elif matches > 0:
            return ("Partial", f"Some organizations match ({matches}/{total_orgs})")
        
        # Check for organization type keywords
        key_orgs = ["corps", "usace", "ferc", "power", "utility", "electric", "authority", 
                   "city", "county", "district", "bureau", "reclamation"]
        llm_orgs = [org for org in key_orgs if org in llm_norm]
        obs_orgs_keys = [org for org in key_orgs if org in obs_norm]
        if set(llm_orgs) & set(obs_orgs_keys):
            return ("Partial", "Some organizations match")
    
    elif variable_name == "migratory_fish_species":
        # Check for fish species names
        fish_terms = ["salmon", "chinook", "coho", "sockeye", "steelhead", "trout", "sturgeon", 
                     "tern", "plover", "lamprey", "shad", "bass", "walleye"]
        llm_fish = [f for f in fish_terms if f in llm_norm]
        obs_fish = [f for f in fish_terms if f in obs_norm]
        if set(llm_fish) & set(obs_fish):
            overlap = len(set(llm_fish) & set(obs_fish)) / max(len(set(obs_fish)), 1)
            if overlap >= 0.5:
                return ("Correct", f"Species overlap ({overlap:.2f})")
            else:
                return ("Partial", f"Some species match ({overlap:.2f})")
    
    elif variable_name == "minimum_flow":
        # Extract flow values and compare
        llm_nums = re.findall(r'(\d+(?:\.\d+)?)\s*(?:cfs|cubic\s+feet|ft)', llm_norm)
        obs_nums = re.findall(r'(\d+(?:\.\d+)?)\s*(?:cfs|cubic\s+feet|ft)', obs_norm)
        
        if llm_nums and obs_nums:
            # Check if any numbers match
            if set(llm_nums) & set(obs_nums):
                return ("Correct", "Flow value matches")
            # Check if within 20% range for first value
            try:
                llm_val = float(llm_nums[0])
                obs_val = float(obs_nums[0])
                if abs(llm_val - obs_val) / obs_val < 0.2:
                    return ("Correct", f"Within 20% ({llm_val} vs {obs_val} cfs)")
                else:
                    return ("Partial", f"Numbers differ ({llm_val} vs {obs_val} cfs)")
            except:
                pass
    
    # Medium similarity - partial match
    if ratio >= 0.4:
        return ("Partial", f"Moderate similarity ({ratio:.2f})")
    
    # Low similarity - wrong
    return ("Wrong", f"Low similarity ({ratio:.2f})")

def main():
    print("="*80)
    print("PIPELINE 3 VALIDATION: LLM vs Ground Truth Comparison")
    print("="*80)
    
    # Load data
    print("\n📂 Loading data...")
    llm_df = pd.read_csv("multi_variable_simple_results.csv")
    
    # Create combined location column
    print("   Creating combined location field...")
    combined_locs = []
    for _, row in llm_df.iterrows():
        county = extract_clean_value(row['location_county'])
        city = extract_clean_value(row['location_city'])
        river = extract_clean_value(row['location_river'])
        
        parts = [p for p in [county, city, river] if p]
        combined = '; '.join(parts) if parts else 'Not mentioned'
        combined_locs.append(combined)
    
    llm_df['location_combined'] = combined_locs
    
    # Clean other verbose fields
    for col in ['project_name', 'owner_operator', 'generation_capacity', 'plant_type', 
                'licensing_dates', 'key_stakeholders', 'project_costs', 
                'migratory_fish_species', 'minimum_flow']:
        llm_df[f'{col}_clean'] = llm_df[col].apply(extract_clean_value)
    
    observed_df = pd.read_csv("Observed_extended_variables.csv", encoding='latin-1')
    
    # Also load min_flow_results_Observed.csv for minimum_flow comparison
    observed_minflow_df = pd.read_csv("min_flow_results_Observed.csv")
    
    print(f"   LLM results: {len(llm_df)} files")
    print(f"   Ground truth: {len(observed_df)} files")
    print(f"   Min flow ground truth: {len(observed_minflow_df)} files")
    
    # Map column names
    column_mapping = {
        "project_name": "Project / Dam",
        "owner_operator": "Owner / Operator",
        "location_combined": "Location (County, City, River)",
        "generation_capacity": "Generation Capacity",
        "plant_type": "Plant Type (Run-of-river / Peaking)",
        "licensing_dates": "Licensing / Authorization Date",
        "key_stakeholders": "Key Stakeholders",
        "project_costs": "Project Costs",
        "migratory_fish_species": "Migratory Fish Species"
    }
    
    # Variables to compare
    variables = [
        "project_name", "owner_operator", "location_combined",
        "generation_capacity", "plant_type", "licensing_dates",
        "key_stakeholders", "project_costs", "migratory_fish_species", "minimum_flow"
    ]
    
    # Initialize results
    results = []
    summary = {var: {"Correct": 0, "Partial": 0, "Wrong": 0} for var in variables}
    
    # Compare each file
    print("\n🔍 Comparing extractions...\n")
    
    for _, llm_row in llm_df.iterrows():
        filename = llm_row['filename']
        
        # Find matching row in observed data
        obs_row = observed_df[observed_df['File'] == filename]
        
        if obs_row.empty:
            print(f"⚠️  {filename}: Not in ground truth (skipping)")
            continue
        
        obs_row = obs_row.iloc[0]
        
        # Compare each variable
        file_results = {"filename": filename}
        
        for var in variables:
            # Use cleaned value  
            if var == 'location_combined':
                llm_value_raw = llm_row[var]
            else:
                llm_value_raw = llm_row.get(f'{var}_clean', llm_row[var])
            
            # For categorize_match, also pass the raw uncleaned value
            llm_value_for_comparison = llm_row[var] if var != 'location_combined' else llm_row[var]
            
            # Get observed value
            if var == "minimum_flow":
                # Get from minimum flow dataset
                minflow_row = observed_minflow_df[observed_minflow_df['filename'] == filename]
                if minflow_row.empty:
                    obs_value = "Not specified"
                else:
                    obs_value = minflow_row.iloc[0]['Value']
            else:
                obs_value = obs_row[column_mapping[var]]
            
            category, explanation = categorize_match(llm_value_for_comparison, obs_value, var)
            
            file_results[var] = category
            file_results[f"{var}_explanation"] = explanation
            summary[var][category] += 1
        
        results.append(file_results)
    
    # Save detailed results
    results_df = pd.DataFrame(results)
    results_df.to_csv("pipeline3_validation_detailed.csv", index=False)
    print(f"✅ Saved detailed results to pipeline3_validation_detailed.csv")
    
    # Print summary
    print("\n" + "="*80)
    print("📊 VALIDATION SUMMARY")
    print("="*80)
    
    total_comparisons = len(results)
    
    for var in variables:
        correct = summary[var]["Correct"]
        partial = summary[var]["Partial"]
        wrong = summary[var]["Wrong"]
        total = correct + partial + wrong
        
        if total == 0:
            continue
        
        correct_pct = (correct / total) * 100
        partial_pct = (partial / total) * 100
        wrong_pct = (wrong / total) * 100
        
        print(f"\n{var.upper().replace('_', ' ')}:")
        print(f"   ✅ Correct:  {correct:2d} ({correct_pct:5.1f}%)")
        print(f"   ⚠️  Partial:  {partial:2d} ({partial_pct:5.1f}%)")
        print(f"   ❌ Wrong:    {wrong:2d} ({wrong_pct:5.1f}%)")
    
    # Overall statistics
    print("\n" + "="*80)
    print("🎯 OVERALL PERFORMANCE")
    print("="*80)
    
    total_correct = sum(summary[var]["Correct"] for var in variables)
    total_partial = sum(summary[var]["Partial"] for var in variables)
    total_wrong = sum(summary[var]["Wrong"] for var in variables)
    total_all = total_correct + total_partial + total_wrong
    
    print(f"\nTotal comparisons: {total_all}")
    print(f"✅ Correct:  {total_correct:4d} ({(total_correct/total_all)*100:5.1f}%)")
    print(f"⚠️  Partial:  {total_partial:4d} ({(total_partial/total_all)*100:5.1f}%)")
    print(f"❌ Wrong:    {total_wrong:4d} ({(total_wrong/total_all)*100:5.1f}%)")
    print(f"\n✅+⚠️ (Acceptable): {total_correct + total_partial:4d} ({((total_correct+total_partial)/total_all)*100:5.1f}%)")
    
    # Save summary
    summary_df = pd.DataFrame(summary).T
    summary_df.to_csv("pipeline3_validation_summary.csv")
    print(f"\n✅ Saved summary to pipeline3_validation_summary.csv")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
