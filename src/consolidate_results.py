#!/usr/bin/env python3
"""
Consolidate multi-model extraction results into unified files.
Creates:
  - min_flow_results_consolidated.csv (all model results)
  - min_flow_timing_consolidated.csv (all model timings)
"""

import csv
import os

# Model configurations
MODELS = {
    "70b": {
        "name": "Llama 3.3 70B",
        "results_file": "min_flow_results.csv",
        "timing_file": "min_flow_timing_results.csv"  # 70B timing file
    },
    "8b": {
        "name": "Llama 3 8B",
        "results_file": "min_flow_results_llama3_8b.csv",
        "timing_file": "min_flow_timing_llama3_8b.csv"
    },
    "3b": {
        "name": "Llama 3.2 3B",
        "results_file": "min_flow_results_llama32_3b.csv",
        "timing_file": "min_flow_timing_llama32_3b.csv"
    },
    "20b": {
        "name": "GPT-OSS 20B",
        "results_file": "min_flow_results_gpt_oss_20b.csv",
        "timing_file": "min_flow_timing_gpt_oss_20b.csv"
    }
}

def consolidate_results():
    """Consolidate all min_flow_results files into one."""
    output_file = "min_flow_results_consolidated.csv"
    
    # Standard output columns
    fieldnames = [
        "Model",
        "Row_Number",
        "Project_Name",
        "filename",
        "Project_Location",
        "Minimum_Flow_Value",
        "Minimum_Flow_Inferred_Context",
        "Minimum_Flow_Exact_Sentences"
    ]
    
    rows_written = 0
    
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for model_key, model_info in MODELS.items():
            results_file = model_info["results_file"]
            model_name = model_info["name"]
            
            if not os.path.exists(results_file):
                print(f"⚠️  Skipping {model_name} - file not found: {results_file}")
                continue
            
            print(f"📖 Reading {model_name} results from {results_file}")
            
            with open(results_file, 'r', encoding='utf-8') as infile:
                # Try both quote styles
                reader = csv.DictReader(infile)
                
                for row in reader:
                    # Normalize column names (handle variations)
                    normalized_row = {
                        "Model": model_name,
                        "Row_Number": row.get("Row_Number", row.get("row_number", "")),
                        "Project_Name": row.get("Project_Name", row.get("Project Name", "")),
                        "filename": row.get("filename", ""),
                        "Project_Location": row.get("Project_Location", row.get("Project Location", "")),
                        "Minimum_Flow_Value": row.get("Minimum_Flow_Value", row.get("Minimum_Flow Value", "")),
                        "Minimum_Flow_Inferred_Context": row.get("Minimum_Flow_Inferred_Context", row.get("Minimum_Flow Inferred Context", "")),
                        "Minimum_Flow_Exact_Sentences": row.get("Minimum_Flow_Exact_Sentences", row.get("Minimum_Flow Exact Sentences", ""))
                    }
                    
                    writer.writerow(normalized_row)
                    rows_written += 1
    
    print(f"✅ Consolidated {rows_written} rows into {output_file}")
    return output_file

def consolidate_timing():
    """Consolidate all timing files into one."""
    output_file = "min_flow_timing_consolidated.csv"
    
    # Standard timing columns
    fieldnames = [
        "Model",
        "filename",
        "total_time_seconds",
        "name_extraction_time",
        "location_extraction_time", 
        "flow_extraction_time"
    ]
    
    rows_written = 0
    
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for model_key, model_info in MODELS.items():
            timing_file = model_info.get("timing_file")
            model_name = model_info["name"]
            
            if not timing_file:
                continue  # Skip if no timing file specified
            
            if not os.path.exists(timing_file):
                print(f"⚠️  Skipping {model_name} timing - file not found: {timing_file}")
                continue
            
            print(f"⏱️  Reading {model_name} timing from {timing_file}")
            
            with open(timing_file, 'r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                
                for row in reader:
                    normalized_row = {
                        "Model": model_name,
                        "filename": row.get("filename", ""),
                        "total_time_seconds": row.get("total_time_seconds", ""),
                        "name_extraction_time": row.get("name_extraction_time", ""),
                        "location_extraction_time": row.get("location_extraction_time", ""),
                        "flow_extraction_time": row.get("flow_extraction_time", "")
                    }
                    
                    writer.writerow(normalized_row)
                    rows_written += 1
    
    print(f"✅ Consolidated {rows_written} timing rows into {output_file}")
    return output_file

if __name__ == "__main__":
    print("🔄 Consolidating multi-model results...\n")
    
    results_file = consolidate_results()
    print()
    
    timing_file = consolidate_timing()
    print()
    
    print("=" * 60)
    print("✅ Consolidation complete!")
    print(f"📊 Results: {results_file}")
    print(f"⏱️  Timing: {timing_file}")
    print("=" * 60)
