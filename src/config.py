"""
Configuration file for LLM Pipeline Comparison Study

Users: Edit the PDF_FOLDER path below to point to your PDF documents.
"""

import os

# =============================================================================
# USER CONFIGURATION - EDIT THIS SECTION
# =============================================================================

# Path to your PDF documents folder
# Users should create this folder and put their PDF files there
PDF_FOLDER = "data/input_pdfs"

# Alternative paths (uncomment one if needed):
# PDF_FOLDER = "/path/to/your/pdf/documents"
# PDF_FOLDER = "../your_pdfs"
# PDF_FOLDER = "input_documents"

# =============================================================================
# SYSTEM CONFIGURATION - DO NOT EDIT BELOW THIS LINE
# =============================================================================

# Results output configuration
RESULTS_OUTPUT_DIR = "results"
FIGURES_OUTPUT_DIR = "figures"

# Ground truth data paths
GROUND_TRUTH_FILE = "src/min_flow_results_Observed.csv"
BASELINE_RESULTS_FILE = "data/min_flow_results4.csv"

# Model configurations
MODELS = {
    "llama_70b": {
        "name": "llama3.3:70b",
        "display_name": "Llama 3.3 70B",
        "description": "Large model for complex pipeline"
    },
    "gpt_oss_20b": {
        "name": "gpt-oss:20b", 
        "display_name": "GPT-OSS 20B",
        "description": "Mid-size open source model"
    },
    "llama_8b": {
        "name": "llama3:8b",
        "display_name": "Llama 3 8B", 
        "description": "Efficient small-large model"
    },
    "llama_3b": {
        "name": "llama3.2:3b",
        "display_name": "Llama 3.2 3B",
        "description": "Resource-constrained model"
    }
}

def get_pdf_folder():
    """Get the configured PDF folder path, making it absolute."""
    # Get the repository root directory (parent of src/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    
    # If PDF_FOLDER is relative, make it relative to repo root
    if not os.path.isabs(PDF_FOLDER):
        return os.path.join(repo_root, PDF_FOLDER)
    else:
        return PDF_FOLDER

def get_absolute_path(relative_path):
    """Convert relative path to absolute path from repository root."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    
    if not os.path.isabs(relative_path):
        return os.path.join(repo_root, relative_path)
    else:
        return relative_path

def ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        get_pdf_folder(),
        get_absolute_path(RESULTS_OUTPUT_DIR),
        get_absolute_path(FIGURES_OUTPUT_DIR),
        os.path.dirname(get_absolute_path(GROUND_TRUTH_FILE)),
    ]
    
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Created directory: {directory}")

def validate_setup():
    """Validate that the setup is correct before running experiments."""
    errors = []
    
    # Get absolute paths
    pdf_folder = get_pdf_folder()
    ground_truth_file = get_absolute_path(GROUND_TRUTH_FILE)
    
    # Check if PDF folder exists and has PDFs
    if not os.path.exists(pdf_folder):
        errors.append(f"❌ PDF folder not found: {pdf_folder}")
        errors.append(f"   Please create the folder and add your PDF files")
    else:
        pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
        if not pdf_files:
            errors.append(f"❌ No PDF files found in: {pdf_folder}")
            errors.append(f"   Please add PDF files to process")
        else:
            print(f"✅ Found {len(pdf_files)} PDF files in {pdf_folder}")
    
    # Check if ground truth files exist
    if not os.path.exists(ground_truth_file):
        errors.append(f"❌ Ground truth file not found: {ground_truth_file}")
    
    if errors:
        print("\n🚨 SETUP ERRORS:")
        for error in errors:
            print(error)
        print(f"\n💡 QUICK FIX:")
        print(f"1. Create folder: mkdir -p {pdf_folder}")
        print(f"2. Add your PDF files to: {pdf_folder}/")
        print(f"3. Run the script again")
        return False
    
    print("✅ Setup validation passed!")
    return True

if __name__ == "__main__":
    print("🔧 Configuration Test")
    print("=" * 40)
    print(f"PDF Folder: {get_pdf_folder()}")
    print(f"Results Folder: {get_absolute_path(RESULTS_OUTPUT_DIR)}")
    ensure_directories()
    validate_setup()
