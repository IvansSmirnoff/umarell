# Changelog

All notable changes to Project Umarell.

---

## [2.0.0] - 2025-11-20 - Project Reorganization

### 🎯 Major Structural Improvements

#### Added
- **Organized directory structure** - Professional layout with clear separation
- **docs/** - All documentation in one place
- **scripts/** - All automation scripts organized
- **config/** - All configuration files centralized
- **src/** - All source code in dedicated directory
- **docs/STRUCTURE.md** - Complete project structure documentation
- Symlink `.env.example` → `config/.env.example` for convenience

#### Changed
- **Moved all .md files** to `docs/` directory
- **Moved all scripts** to `scripts/` directory  
- **Moved configuration** to `config/` directory
- **Moved source code** to `src/` directory
- **Updated docker-compose.yml** with new paths
- **Updated all documentation** with correct file paths
- **Updated all scripts** to reference new structure
- **Root README.md** now clean overview pointing to detailed docs

#### Directory Structure
```
Before: Cluttered root with 15+ files
After:  Clean root with organized subdirectories
```

**Root directory now contains only:**
- README.md (overview)
- docker-compose.yml (infrastructure)
- .env (git-ignored secrets)
- .gitignore (version control)
- Organized subdirectories

---

## [1.0.0] - 2025-11-20 - Automatic Setup

### 🚀 Automation Features

#### Added
- **Automatic model setup** on first `docker compose up`
- **Smart initialization** - Checks if models exist before downloading
- **Setup marker file** - Tracks completion to avoid re-downloads
- **Docker healthchecks** - Proper service dependency management
- **scripts/entrypoint.sh** - Custom Docker entrypoint
- **scripts/init_ollama.sh** - Automatic initialization logic
- **scripts/check_status.sh** - Status checking utility
- **docs/AUTOMATIC_SETUP.md** - Documentation of auto-setup system

#### Changed
- **One-command deployment** - No manual setup script needed
- **Subsequent launches** instant (skip model downloads)
- **Open WebUI** waits for Ollama health before starting
- Updated documentation to reflect automatic setup

#### Removed
- Manual model setup requirement (now automatic)

---

## [0.1.0] - 2025-11-20 - Initial Implementation

### ✨ Core Features

#### Added
- **Docker Compose** infrastructure
  - Ollama service (AI models)
  - Neo4j (graph database)
  - Open WebUI (chat interface)
- **L'Umarell Persona** - Grumpy Milanese inspector
  - Based on qwen2.5:7b
  - Custom Modelfile with personality
  - Milanese slang and attitude
- **Umarell Tool** - Open WebUI Python tool
  - Neo4j integration for room lookup
  - InfluxDB integration for sensor data
  - LLM-generated database queries
- **Dual-LLM Architecture**
  - qwen2.5:7b for personality
  - qwen2.5-coder:1.5b for query generation
- **IFC to Neo4j** importer
- **Configuration files**
  - sensor_config.json (room-to-sensor mapping)
  - .env.example (environment template)
- **Complete documentation**
  - README.md
  - DEPLOYMENT.md
  - QUICKREF.md
  - SUMMARY.md

---

## Version History

- **v2.0.0** - Professional project structure
- **v1.0.0** - Automatic setup system
- **v0.1.0** - Initial working implementation

---

## Upgrade Guide

### From v1.0.0 to v2.0.0

**No functional changes** - Only file reorganization.

If you have an existing installation:

1. **Pull latest changes:**
   ```bash
   git pull
   ```

2. **Move your .env file** (if in config/):
   ```bash
   mv config/.env .env  # Move to root
   ```

3. **Restart services:**
   ```bash
   docker compose down
   docker compose up -d
   ```

Everything should work exactly as before, just better organized!

### From v0.1.0 to v1.0.0

1. Remove manual setup step (now automatic)
2. Just run: `docker compose up -d`
3. Setup happens automatically on first launch

---

## Breaking Changes

### v2.0.0
- **File paths changed** - All paths updated in code
- **docker-compose.yml volumes** - Now point to new locations
- **No API changes** - Functionality unchanged

### v1.0.0
- None (only additions)

---

## Future Plans

- [ ] Web UI for sensor config management
- [ ] Advanced HVAC control integration
- [ ] Multi-language support (keep Milanese attitude!)
- [ ] Energy optimization suggestions
- [ ] Historical data analysis
- [ ] Building automation integration

---

**L'Umarell says:**

> "Look at this beautiful changelog! Now everyone knows what changed and when. This is how you do professional work, not like some barlafus who changes things without documenting! Taaac! 👴"
