# Changelog

All notable changes to Project Umarell.

---

## [3.0.0] - 2026-01-15 - Robust Multi-Purpose Toolkit

### 🎯 Major Architecture Overhaul

#### Added
- **3-method toolkit architecture** in `umarell_tool.py`:
  - `query_topology(category, floor, name_contains)` - Find building elements
  - `check_sensor_config(room_name)` - Check sensor configuration for a room
  - `inspect_zone_metrics(zone, type, goal, time_range)` - Analyze sensor data across zones
- **Deterministic query building** - All Cypher/Flux queries built in Python with sanitized inputs
- **Input sanitization** - Prevents injection attacks in both Cypher and Flux queries
- **Graceful library handling** - Missing `neo4j` or `influxdb_client` handled with helpful errors
- **Multi-path config loading** - Searches multiple paths for `sensor_config.json` with caching
- **Flexible sensor config formats** - Supports dict, string, or list mappings
- **Batch InfluxDB queries** - Uses regex filters to fetch all sensor data in single query
- **Multiple analysis modes** - `report`, `max`, `min`, `avg` for zone metrics

#### Changed
- **Removed LLM query generation** - No more `_ask_llm()` for writing raw SQL/Flux
- **Removed dual-LLM architecture** - No longer needs `qwen2.5-coder:1.5b`
- **Updated `ifc_to_graph.py`** - Enhanced semantic extraction from IFC_Locali property sets
- **Updated documentation** - GEMINI.md, README.md reflect new toolkit architecture

#### Removed
- `_ask_llm()` method - Replaced with deterministic query building
- `inspect_building()` method - Replaced with 3 specialized methods
- Dependency on `qwen2.5-coder:1.5b` model

#### Why This Matters
The old tool was fragile because it relied on an LLM to write raw database queries at runtime. The new toolkit:
- **More reliable** - Deterministic queries never have syntax errors
- **More secure** - Input sanitization prevents injection
- **More capable** - 3 specialized methods handle different use cases
- **Simpler** - Only needs one LLM model (qwen2.5:7b)

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

- **v3.0.0** - Robust multi-purpose toolkit (deterministic queries)
- **v2.0.0** - Professional project structure
- **v1.0.0** - Automatic setup system
- **v0.1.0** - Initial working implementation

---

## Upgrade Guide

### From v2.0.0 to v3.0.0

**Breaking change**: The tool API has changed completely.

1. **Pull latest changes:**
   ```bash
   git pull
   ```

2. **Update sensor_config.json** (optional - new format supported):
   ```json
   {
     "room_to_sensor_map": {
       "room_id": {
         "temperature": "sensor_temp_001",
         "co2": "sensor_co2_001"
       }
     },
     "sensor_types": {
       "temperature": { "unit": "°C" },
       "co2": { "unit": "ppm" }
     }
   }
   ```

3. **Re-install the tool in Open WebUI:**
   - Go to Settings → Tools
   - Delete old Umarell tool
   - Add new tool from `src/umarell_tool.py`

4. **Remove qwen2.5-coder model** (no longer needed):
   ```bash
   docker exec ollama ollama rm qwen2.5-coder:1.5b
   ```

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

### v3.0.0
- **Tool API completely changed** - Old `inspect_building()` replaced with 3 new methods
- **Must re-install tool** in Open WebUI
- **qwen2.5-coder:1.5b no longer used** - Can be removed to save space

### v2.0.0
- **File paths changed** - All paths updated in code
- **docker-compose.yml volumes** - Now point to new locations
- **No API changes** - Functionality unchanged

### v1.0.0
- None (only additions)

---

## Future Plans

- [x] ~~Robust deterministic query building~~ (v3.0.0)
- [ ] Web UI for sensor config management
- [ ] Advanced HVAC control integration
- [ ] Multi-language support (keep Milanese attitude!)
- [ ] Energy optimization suggestions
- [ ] Historical data analysis
- [ ] Building automation integration

---

**L'Umarell says:**

> "Look at this beautiful changelog! Now everyone knows what changed and when. This is how you do professional work, not like some barlafus who changes things without documenting! Taaac! 👴"
