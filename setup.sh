#!/bin/bash
# User Setup Script for LLM Pipeline Comparison Study

echo "🚀 LLM Pipeline Comparison Study - User Setup"
echo "============================================="
echo ""

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PDF_FOLDER="$SCRIPT_DIR/data/input_pdfs"

echo "📁 Setting up directories..."

# Create the PDF input folder
mkdir -p "$PDF_FOLDER"
mkdir -p "$SCRIPT_DIR/results"
mkdir -p "$SCRIPT_DIR/figures"

echo "✅ Created directories:"
echo "   📂 $PDF_FOLDER (for your PDF files)"
echo "   📂 $SCRIPT_DIR/results (for output results)"
echo "   📂 $SCRIPT_DIR/figures (for generated figures)"
echo ""

# Check if PDFs already exist
PDF_COUNT=$(find "$PDF_FOLDER" -name "*.pdf" 2>/dev/null | wc -l)

if [ "$PDF_COUNT" -eq 0 ]; then
    echo "📄 PDF SETUP REQUIRED:"
    echo "   1. Add your PDF documents to: $PDF_FOLDER"
    echo "   2. Supported formats: .pdf files"
    echo "   3. Example documents: technical reports, regulatory documents, etc."
    echo ""
    echo "💡 QUICK START:"
    echo "   cp /path/to/your/pdfs/*.pdf $PDF_FOLDER/"
    echo ""
else
    echo "✅ Found $PDF_COUNT PDF files in input folder"
    echo ""
fi

# Test configuration
echo "🔧 Testing configuration..."
cd "$SCRIPT_DIR"
python src/config.py

echo ""
echo "🎯 NEXT STEPS:"
echo ""
echo "1. ADD YOUR PDFs:"
echo "   cp /path/to/your/documents/*.pdf $PDF_FOLDER/"
echo ""
echo "2. INSTALL OLLAMA (if not already installed):"
echo "   curl -fsSL https://ollama.ai/install.sh | sh"
echo ""
echo "3. DOWNLOAD MODELS:"
echo "   ollama pull llama3.3:70b"
echo "   ollama pull llama3:8b" 
echo "   ollama pull llama3.2:3b"
echo "   ollama pull gpt-oss:20b"
echo ""
echo "4. RUN EXPERIMENTS:"
echo "   # Test 70B model with complex pipeline:"
echo "   cd src/complex_pipeline && python llama_70b_complex_pipeline.py"
echo ""
echo "   # Test all models with simple pipeline:"
echo "   cd src/simple_pipeline && python multi_model_simple_pipeline.py"
echo ""
echo "5. GENERATE ANALYSIS:"
echo "   cd src/evaluation && python create_final_comparison.py"
echo ""
echo "📚 For detailed instructions, see: docs/SETUP.md"
echo ""
echo "✅ Setup complete! Add your PDFs and start experimenting!"
