# FitLib Vault - Comprehensive Fitness Research Knowledge Base

A curated collection of evidence-based fitness, nutrition, and neuroscience research organized in Obsidian-compatible Markdown format.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ or 3.12
- Node.js 16+ (for frontend only)
- Git

### Initial Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/dopalici/fitlibvault.git
cd fitlibvault
```

#### 2. Set Up Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### 3. Set Up Frontend (Optional)
```bash
cd organized_library/frontend
npm install
npm start
```

#### 4. Configure API Keys (if using research scripts)
```bash
# Create .env file in project root
cp .env.example .env

# Edit .env and add your API keys:
# PUBMED_API_KEY=your_key_here
# SEMANTIC_SCHOLAR_API_KEY=your_key_here
```

## 📁 Project Structure

```
fitlibvault-main/
├── 00_System/              # Scripts and automation tools
│   ├── Scripts/            # Research fetching, parsing, linking
│   └── logs/              # Application logs (gitignored)
├── A-Series/              # Foundational concepts
├── B-Series/              # Resistance training
├── C-Series/              # Nutrition & diet
├── organized_library/     # Frontend web interface
├── NEURO_PSYCH_VAULT/    # Neuroscience research (240 nodes)
├── Auto_Updates/          # AI-generated research (gitignored)
├── .gitignore             # Files to exclude from git
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🛠️ Development

### Running Research Scripts
```bash
source venv/bin/activate
python 00_System/Scripts/run_neuro_research.py
```

### Adding New Research
1. Place new markdown files in appropriate series folders
2. Run vault linker to create internal links:
```bash
python 00_System/Scripts/vault_linker.py
```

## 📝 Git Workflow

```bash
# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Add new research on [topic]"

# Push to GitHub
git push origin main
```

## ⚠️ Important Notes

- **Never commit** `venv/`, `node_modules/`, or `Auto_Updates/` (already in .gitignore)
- **Always use** requirements.txt and package.json to share dependencies
- **API keys** must be kept in `.env` file (gitignored for security)
- Generated research files in `Auto_Updates/` should be manually reviewed before integration

## 🔧 Rebuilding After Fresh Clone

If you clone this repository on a new machine:

```bash
# 1. Recreate Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Recreate Node modules (if using frontend)
cd organized_library/frontend
npm install

# 3. Configure your environment
cp .env.example .env
# Edit .env with your API keys
```

## 📚 Resources

- [Obsidian](https://obsidian.md/) - Recommended markdown editor
- [GitHub Repository](https://github.com/dopalici/fitlibvault)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-research`)
3. Commit your changes (`git commit -m 'Add amazing research'`)
4. Push to the branch (`git push origin feature/amazing-research`)
5. Open a Pull Request

## 📄 License

This project is for educational and research purposes.

---

**Last Updated:** May 3, 2026
