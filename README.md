# SkillCorner X PySport Analytics Cup
## Analyst Track Abstract Template (max. 300 words)
### Introduction
This project introduces an open-source framework designed to empower football analysts through the use of compact, efficient language models (LLMs). By utilising smaller models such as Llama 3.1, the system prioritises speed and customisability, addressing the latency and cost issues often associated with larger commercial models. The architecture is built to function as a flexible library, allowing users to swap models and train the system on proprietary data, thereby democratising access to high-level data science tools within the football industry.

### Usecase(s)
The system currently automates the retrieval of physical performance data and the generation of key visualisations, including scatter plots, bar charts, and radar profiles. Recognising the instability of LLM-generated SQL, the framework incorporates robust guardrails and self-correction mechanisms to ensure query reliability. Moving forward, the tool is designed to support bespoke metric definition, enabling clubs to generate real-time analysis tailored to specific tactical requirements. The ultimate goal is a fully autonomous agent that intelligently selects the most appropriate visualisation method and report format without human intervention.

### Potential Audience
The primary beneficiaries are professional performance analysts and recruitment departments seeking to integrate bespoke, real-time insights into their workflow without extensive engineering overhead. Additionally, by lowering the technical barrier to entry, this project serves the wider football analytics community, including independent scouts and tactical bloggers. It offers a scalable solution that allows non-technical experts to harness the power of generative AI for sophisticated, data-driven storytelling.
---

## Video URL

---

## Run Instructions
# Run Instructions

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

