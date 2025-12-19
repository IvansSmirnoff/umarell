# 📁 Project Structure

This document explains the organized structure of Project Umarell.

## Directory Layout

```
umarell/
├── 📄 README.md                    # Main project overview
├── 📄 docker-compose.yml           # Infrastructure definition
├── 📄 .env                         # Your credentials (git-ignored)
├── 📄 .env.example                 # → symlink to config/.env.example
├── 📄 .gitignore                   # Git ignore rules
│
├── 📖 docs/                        # All documentation
│   ├── README.md                  # Detailed documentation
│   ├── QUICKREF.md               # Quick reference card
│   ├── DEPLOYMENT.md             # Deployment checklist
│   ├── AUTOMATIC_SETUP.md        # Auto-setup explanation
│   ├── SUMMARY.md                # Task completion summary
│   └── STRUCTURE.md              # This file
│
├── 🔧 scripts/                     # Automation & setup scripts
│   ├── check_status.sh           # System status checker ⭐
│   ├── quickstart.sh             # Quick deployment helper
│   ├── setup_umarell.sh          # Manual setup (legacy)
│   ├── entrypoint.sh             # Docker entrypoint (auto-runs)
│   └── init_ollama.sh            # Model initialization (auto-runs)
│
├── ⚙️  config/                      # Configuration files
│   ├── .env.example              # Environment template
│   ├── sensor_config.json        # Room-to-sensor mapping
│   └── modelfiles/
│       └── Modelfile_Umarell     # L'Umarell persona definition
│
├── 🐍 src/                         # Source code
│   ├── umarell_tool.py           # Open WebUI tool (main)
│   ├── ifc_to_graph.py           # IFC to Neo4j importer
│   ├── llm_router_tool.py        # Alternative tool implementation
│   └── requirements.txt          # Python dependencies
│
└── 💾 [Generated at runtime]
    ├── ollama_data/              # Ollama models storage (git-ignored)
    └── venv/                     # Python virtual env (git-ignored)
```

## File Purposes

### Root Level

- **README.md** - Main entry point, quick start guide
- **docker-compose.yml** - Defines all services (Ollama, Neo4j, Open WebUI)
- **.env** - Your secrets (InfluxDB credentials, etc.)
- **.env.example** - Symlink to `config/.env.example` for convenience

### docs/

All documentation lives here to keep the root clean:

- **README.md** - Comprehensive documentation
- **QUICKREF.md** - One-page cheat sheet
- **DEPLOYMENT.md** - Step-by-step deployment
- **AUTOMATIC_SETUP.md** - How the auto-setup system works
- **SUMMARY.md** - Original task completion summary
- **STRUCTURE.md** - This file (project organization)

### scripts/

Executable automation scripts:

- **check_status.sh** - Check if setup is complete, view installed models
- **quickstart.sh** - One-command deployment helper
- **setup_umarell.sh** - Legacy manual setup (kept for reference)
- **entrypoint.sh** - Docker entrypoint for Ollama container
- **init_ollama.sh** - Automatic model initialization logic

All scripts should be run from project root: `./scripts/script_name.sh`

### config/

Configuration and settings:

- **.env.example** - Template for environment variables
- **sensor_config.json** - Maps IFC room IDs to sensor IDs
- **modelfiles/** - Ollama model definitions
  - **Modelfile_Umarell** - The grumpy inspector persona

### src/

Python source code:

- **umarell_tool.py** - Main Open WebUI tool (install via UI)
- **ifc_to_graph.py** - Import IFC files into Neo4j
- **llm_router_tool.py** - Alternative/reference implementation
- **requirements.txt** - Python package dependencies

## Path References

When referencing files in documentation or scripts:

### From Project Root

```bash
./scripts/check_status.sh
./config/sensor_config.json
./src/umarell_tool.py
docker compose up -d  # reads ./docker-compose.yml
```

### From Docker Compose

Volumes are mounted from project root:

```yaml
- ./config/modelfiles:/modelfiles
- ./config/sensor_config.json:/app/backend/data/sensor_config.json:ro
- ./scripts:/scripts
```

### In Documentation

Use relative paths from docs/:

```markdown
See [Quick Reference](QUICKREF.md)
Check `../config/sensor_config.json`
Run `../scripts/check_status.sh`
```

## Why This Structure?

### Separation of Concerns

- **docs/** - Everything documentation
- **scripts/** - All automation
- **config/** - All configuration
- **src/** - All code

### Clean Root Directory

Only essential files in root:
- README.md (entry point)
- docker-compose.yml (infrastructure)
- .env (secrets - git-ignored)
- .gitignore (version control)

### Professional Appearance

This structure is typical of mature open-source projects:
- Easy to navigate
- Clear organization
- Predictable locations
- Scalable for growth

### User-Friendly

- All scripts in one place (`scripts/`)
- All docs in one place (`docs/`)
- Clear what goes where
- Less clutter, easier to find things

## Adding New Files

### Documentation?
→ Put in `docs/`

### Script/Automation?
→ Put in `scripts/`, make executable

### Configuration?
→ Put in `config/`

### Source Code?
→ Put in `src/`

### Data Files?
→ Git-ignore them, document in README

## Migration Notes

Files were moved from root to organized directories:

**Before:**
```
umarell/
├── README.md
├── QUICKREF.md
├── DEPLOYMENT.md
├── ... (many .md files)
├── check_status.sh
├── quickstart.sh
├── sensor_config.json
├── umarell_tool.py
└── ... (cluttered)
```

**After:**
```
umarell/
├── README.md
├── docker-compose.yml
├── docs/          # All documentation
├── scripts/       # All scripts
├── config/        # All configuration
└── src/           # All code
```

All references in documentation and scripts were updated to reflect new paths.

## Maintenance

When updating the project:

1. **Keep root clean** - Only essential files
2. **Document changes** - Update relevant docs
3. **Update paths** - If moving files, update all references
4. **Test scripts** - Ensure all paths work from project root

---

**L'Umarell says:**

> "Now THIS is organization! Everything in its place, like a proper construction site. Not like before with tools scattered everywhere like a barlafus! Taaac! 👴"
