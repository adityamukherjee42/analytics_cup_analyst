# SkillCorner X PySport Analytics Cup
## Analyst Track Abstract Template (max. 300 words)
### Introduction
This project presents an open-source framework dedicated to assisting football analysts by integrating compact language models, such as Llama 3.1, into the data analysis workflow. By utilising smaller, efficient models, the system addresses latency and cost while offering the potential for bespoke training on proprietary datasets. The architecture is designed as a flexible library, reducing the technical barrier to entry and democratising access to advanced data science tools within the football industry.

### Usecase(s)
The system currently facilitates the automated retrieval of physical performance data and the generation of specific visualisations, including scatter plots, bar charts, and radar profiles. Acknowledging the inherent instability of SQL generation in large language models, the framework implements robust guardrails and self-correction protocols to ensure query reliability. The roadmap envisages a fully autonomous agent capable of defining club-specific metrics and executing real-time analysis. This evolution aims to allow the model to independently select optimal visualisation methods and generate comprehensive reports, shifting the focus from manual coding to strategic interpretation.

### Potential Audience
The primary users are professional performance analysts and recruitment scouts seeking to enhance their workflow with tailored, real-time insights without requiring extensive engineering support. Furthermore, this project supports the broader football analytics community by providing a scalable, open-source solution that allows non-technical experts to leverage generative AI for sophisticated data storytelling and opposition analysis.

## Video URL

---

## Run Instructions
## Quick Start Guide

### Step 1: Install Ollama and Pull Model
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Llama 3.1 model (approximately 4.7GB download)
ollama pull llama3.1:latest

# Start Ollama service
ollama serve
```
---

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows
```

---

### Step 3: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
# Start the app
python -m streamlit run app.py

# OR use the helper script
./run_app.sh
```

**Open your browser to: http://localhost:8501**

---

## Alternative: One-Command Setup

```bash
# Run complete automated setup (performs steps 1-3)
chmod +x src/setup/setup_ollama.sh
./src/setup/setup_ollama.sh
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Ollama not running | Run `ollama serve` in a separate terminal |
| Model not found | Run `ollama pull llama3.1:latest` |
| Import errors | Run `pip install -r requirements.txt` |
| Permission denied | Run `chmod +x *.sh` |
| Port already in use | Change port in run_app.sh or use `python -m streamlit run app.py --server.port 8502` |

---

## Verification Steps

```bash
# Check Ollama
ollama list  # Should show llama3.1:latest

# Check Python packages
pip list | grep streamlit  # Should show version

# Test the app
python -m streamlit run app.py
```
---

