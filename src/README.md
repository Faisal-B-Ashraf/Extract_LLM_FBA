# Source Code Overview

## Python Scripts in this Repository

### 🔧 Complex Pipeline (`src/complex_pipeline/`)

#### `llama_70b_complex_pipeline.py` 
**Llama 3.3 70B model with complex pipeline approach**
- Processes PDFs using production-grade extraction pipeline
- Optimized for Llama 3.3 70B model (achieves 88.9% accuracy)
- Handles chunking, API calls, and result saving
- **Usage**: `python llama_70b_complex_pipeline.py`

#### `multi_model_complex_pipeline.py`
**3 smaller models testing with complex pipeline**
- Tests 3 models: Llama 3 8B, Llama 3.2 3B, GPT-OSS 20B
- Uses same complex pipeline as 70B script
- Demonstrates pipeline failure on smaller models (0% accuracy)
- **Usage**: `python multi_model_complex_pipeline.py`

#### `api_handler.py`
**API interface for LLM communication**
- Handles Ollama API calls for all models
- Includes retry logic and error handling
- Smart chunking strategies
- Model-agnostic interface

#### `task_definitions_min_flow.py`
**Extraction prompts and task definitions**
- Contains complex prompts for minimum flow extraction
- V12 enhanced prompts achieving 90% accuracy
- Detailed instructions for precise extraction

#### `pdf_processor_min_flow.py`
**PDF text extraction utilities**
- Extracts text from PDF documents
- Token-based text splitting
- Text preprocessing functions

---

### 🧪 Simple Pipeline (`src/simple_pipeline/`)

#### `multi_model_simple_pipeline.py`
**All 4 models testing with simple prompt approach**
- Tests: Llama 3.3 70B, GPT-OSS 20B, Llama 3 8B, Llama 3.2 3B
- Uses minimal, straightforward prompts (52-78% accuracy range)
- Validates against human ground truth data
- **Usage**: `python multi_model_simple_pipeline.py`

---

### 📊 Evaluation (`src/evaluation/`)

#### `create_final_comparison.py`
**Generates publication-ready analysis and figures**
- Compares all model results
- Creates performance visualization
- Generates summary tables
- **Usage**: `python create_final_comparison.py`

---

## Quick Start Commands

### Test Single Model (Fast)
```bash
cd src/simple_pipeline
python multi_model_simple_pipeline.py --models llama3.2:3b --sample 5
```

### Run 70B Complex Pipeline
```bash
cd src/complex_pipeline
python llama_70b_complex_pipeline.py
```

### Test All Smaller Models (Complex Approach)
```bash
cd src/complex_pipeline
python multi_model_complex_pipeline.py
```

### Test All Models (Simple Approach)
```bash
cd src/simple_pipeline
python multi_model_simple_pipeline.py
```

### Generate Analysis
```bash
cd src/evaluation
python create_final_comparison.py
```

## File Sizes
- **llama_70b_complex_pipeline.py**: 10KB (278 lines)
- **multi_model_complex_pipeline.py**: 19KB (486 lines)  
- **multi_model_simple_pipeline.py**: 9KB (247 lines)
- **api_handler.py**: 118KB (2,136 lines)
- **create_final_comparison.py**: 8KB

All scripts are complete and ready to run!
