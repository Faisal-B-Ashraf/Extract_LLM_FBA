# Source Code Documentation

## Main Pipeline

### `llama_70b_complex_pipeline.py`
**Primary extraction pipeline**

Main entry point for processing regulatory documents. Orchestrates the entire extraction workflow from PDF input to CSV output.

**Key Functions:**
- `process_file_v11()` - Processes single PDF file
- `load_existing_results()` - Resumes interrupted runs
- `save_extracted_chunks()` - Saves intermediate text chunks
- `main()` - Orchestrates batch processing

**Workflow:**
1. Check for already-processed files
2. Extract and chunk PDF text
3. Send chunks to LLM for candidate extraction
4. Apply scoring to select best candidate
5. Save results to CSV

**Usage:**
```bash
python llama_70b_complex_pipeline.py
```

**Output Files:**
- `min_flow_results.csv` - Final extraction results
- `min_flow_timing_results.csv` - Performance metrics
- `extracted_chunks_[filename].txt` - Cached text chunks

---

## Core Modules

### `api_handler.py`
**LLM API interface and text processing**

Handles communication with Ollama server and implements intelligent text chunking strategies.

**Key Functions:**
- `check_ollama_server()` - Verifies Ollama is running
- `enhanced_flow_extraction()` - Extracts candidates from text chunks
- `smart_chunking_strategy()` - Splits text while preserving context
- `call_ollama_api()` - Low-level API wrapper with retry logic

**Features:**
- Automatic retry on API failures
- Context-aware text chunking
- Token counting and management
- Error handling and logging

---

### `flow_scoring.py`
**Candidate scoring and selection logic**

Implements rule-based scoring to identify the most authoritative minimum flow value when multiple candidates are found.

**Scoring Criteria:**
1. **Regulatory Authority** - Mandatory language (30 points)
2. **Location Specificity** - At dam/project (25 points)
3. **Temporal Continuity** - Continuous/year-round (20 points)
4. **Numeric Precision** - Exact values over ranges (15 points)
5. **Source Quality** - Clear regulatory context (10 points)

**Key Functions:**
- `apply_flow_scoring()` - Main scoring entry point
- `score_candidate()` - Calculates score for single candidate
- `select_best_candidate()` - Returns highest-scored candidate

---

### `task_definitions_min_flow.py`
**LLM extraction prompts**

Contains carefully engineered prompts for minimum flow extraction. Prompts guide the LLM to:
- Identify numeric flow values with units
- Extract supporting context
- Preserve exact source sentences
- Format output as structured JSON

**Key Functions:**
- `get_prompts()` - Returns task-specific prompts
- Prompt engineering for regulatory document analysis
- Output format specifications

---

### `pdf_processor_min_flow.py`
**PDF text extraction utilities**

Handles PDF file processing and text preprocessing.

**Key Functions:**
- `extract_text_from_pdf()` - Extracts text from PDF files
- `split_text_by_tokens()` - Splits text into token-limited chunks
- `preprocess_text()` - Cleans and normalizes text

**Features:**
- PyPDF2-based text extraction
- Token-aware text splitting
- Preserves document structure

---

### `config.py`
**Configuration management**

Centralizes all configuration settings for the pipeline.

**Settings:**
- PDF input folder paths
- Ollama API endpoint
- Model selection (llama3.3:70b)
- Output file locations
- Logging configuration

**Key Functions:**
- `get_pdf_folder()` - Returns PDF input directory
- `ensure_directories()` - Creates required folders
- `validate_setup()` - Checks prerequisites

---

## Validation

### `compare_v14_results.py`
**Accuracy validation against ground truth**

Compares pipeline output against human-verified values in `data/Observed.csv`.

**Usage:**
```bash
python compare_v14_results.py
```

**Output:**
- Accuracy percentage
- Detailed match/mismatch report
- Error analysis

---

## Running the Pipeline

### Basic Execution
```bash
cd src
python llama_70b_complex_pipeline.py
```

### Resume Interrupted Run
The pipeline automatically skips already-processed files based on `min_flow_results.csv`.

### Process Specific Files
Edit `config.py` to change the PDF input folder or modify the file list in `main()`.

---

## Development Notes

**Code Organization:**
- Main pipeline in `llama_70b_complex_pipeline.py`
- Modular design with separate concerns
- Logging throughout for debugging
- Error handling with graceful degradation

**Performance:**
- ~10 minutes per document (70B model)
- Parallel chunk processing where possible
- Caching of intermediate results

**Maintenance:**
- Prompts in `task_definitions_min_flow.py` for easy tuning
- Scoring rules in `flow_scoring.py` for adjustment
- Configuration centralized in `config.py`
- **create_final_comparison.py**: 8KB

All scripts are complete and ready to run!
