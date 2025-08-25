#!/bin/bash
# Initialize Git Repository for Clean Research Project

echo "🚀 Initializing Clean LLM Research Repository"
echo "=============================================="

# Initialize git repository
git init

# Create .gitignore for Python and research projects
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
.env

# Data files (optional - you may want to include these)
# *.csv
# *.json

# Model files and outputs
*.log
debug.log
extracted_chunks*/
temp/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Results (can be regenerated)
results/temp/
EOF

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: Clean LLM pipeline comparison study

- Complex vs simple pipeline comparison
- 4 models: Llama 3.3 70B, GPT-OSS 20B, Llama 3 8B, Llama 3.2 3B
- Ground truth validated results
- Publication-ready figures and analysis"

echo "✅ Git repository initialized!"
echo ""
echo "📋 Next steps:"
echo "1. Create GitHub repository"
echo "2. Add remote: git remote add origin <your-github-url>"
echo "3. Push: git push -u origin main"
echo ""
echo "🎯 Your clean repository is ready for publication!"
