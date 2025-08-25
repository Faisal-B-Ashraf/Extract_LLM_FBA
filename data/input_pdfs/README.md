# PDF Input Folder

This folder is where you should place your PDF documents for processing.

## Setup Instructions

1. **Add your PDF files here:**
   ```bash
   cp /path/to/your/documents/*.pdf data/input_pdfs/
   ```

2. **Supported file types:**
   - `.pdf` files only
   - Any size (processing time varies)
   - Technical documents, reports, regulatory filings, etc.

3. **Example PDF types that work well:**
   - Technical reports
   - Regulatory documents  
   - License applications
   - Water control manuals
   - Engineering reports

## What the Code Does

The LLM models will:
1. Extract text from each PDF
2. Search for minimum flow requirements
3. Compare different extraction approaches
4. Validate results against ground truth data

## Expected Processing Time

- **3B model**: ~2 minutes per PDF
- **8B model**: ~1.5 minutes per PDF  
- **20B model**: ~9 minutes per PDF
- **70B model**: ~10 minutes per PDF

## File Naming

- Use descriptive filenames
- Avoid special characters
- Example: `ProjectName_WaterControlManual_2024.pdf`

## Privacy Note

All processing happens locally on your machine. No data is sent to external servers (when using local Ollama models).

---

**Ready to start?** Add your PDFs to this folder and run the experiments!
