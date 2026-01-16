# 🏗️ Project Umarell

> *A grumpy Milanese building inspector monitoring your smart building with AI*

**L'Umarell** is an intelligent building management chat interface where the AI embodies a retired Milanese inspector - critical, knowledgeable, and full of personality.

---

## 🚀 Quick Start

```bash
# 1. Configure environment
cp config/.env.example .env
nano .env  # Add your InfluxDB credentials

# 2. Deploy (auto-setup on first launch)
docker compose up -d

# 3. Check status
./scripts/check_status.sh
```

**First launch:** Models download automatically (10-20 min)  
**Subsequent launches:** Instant! ⚡

📖 **[Full Documentation](docs/README.md)** | 📋 **[Quick Reference](docs/QUICKREF.md)** | 🚀 **[Deployment Guide](docs/DEPLOYMENT.md)**

---

## 📁 Project Structure

```
umarell/
├── 📄 docker-compose.yml       # Infrastructure definition
├── 🐳 .env                     # Your credentials (create from .env.example)
│
├── 📖 docs/                    # Documentation
│   ├── README.md              # Detailed documentation
│   ├── QUICKREF.md            # Quick reference card
│   ├── DEPLOYMENT.md          # Deployment checklist
│   ├── AUTOMATIC_SETUP.md     # How auto-setup works
│   └── SUMMARY.md             # Task completion summary
│
├── 🔧 scripts/                 # Automation scripts
│   ├── check_status.sh        # Check system status ⭐
│   ├── quickstart.sh          # Quick deployment helper
│   ├── setup_umarell.sh       # Manual setup (legacy)
│   ├── entrypoint.sh          # Docker entrypoint
│   └── init_ollama.sh         # Model initialization
│
├── ⚙️  config/                  # Configuration files
│   ├── .env.example           # Environment template
│   ├── sensor_config.json     # Room-to-sensor mapping
│   └── modelfiles/
│       └── Modelfile_Umarell  # L'Umarell persona
│
└── 🐍 src/                     # Source code
    ├── umarell_tool.py        # Open WebUI toolkit (3 methods)
    ├── ifc_to_graph.py        # IFC to Neo4j importer (semantic extraction)
    ├── llm_router_tool.py     # Legacy implementation (deprecated)
    └── requirements.txt       # Python dependencies
```

---

## 🎯 What It Does

### The Persona: L'Umarell 👴

In Milanese culture, an "Umarell" is a retired person who watches construction sites and criticizes the work. Our AI embodies this:

- 🗣️ **Speaks English** with Milanese mannerisms
- 🔥 **Complains** about temperatures > 21°C (wasting money!)
- ❄️ **Complains** about temperatures < 19°C (too cold!)
- 💬 **Uses Milanese slang**: "Ué", "Taaac", "Barlafus", "Va che l'è brutta"
- 🧠 **Knowledgeable** about building systems and efficiency

### The Architecture

```
┌─────────────┐
│ Open WebUI  │ ← Chat Interface (http://localhost:8080)
└──────┬──────┘
       │
   ┌───┴────┐
   │        │
   ▼        ▼
┌─────┐  ┌──────────┐
│Ollama│  │ Umarell  │
│Models│  │ Tool     │
└──┬───┘  └────┬─────┘
   │           │
   └────┬──────┘
        │
   ┌────┴─────┐
   │          │
   ▼          ▼
┌──────┐  ┌─────────┐
│Neo4j │  │InfluxDB │
└──────┘  └─────────┘
```

**Components:**
- **Ollama**: Runs AI models (qwen2.5:7b for L'Umarell persona)
- **Neo4j**: Graph database storing building structure (IFC data with semantic properties)
- **Open WebUI**: Chat interface where L'Umarell lives
- **InfluxDB**: Time-series database for sensor data (external)
- **Umarell Toolkit**: Multi-purpose Python toolkit with 3 methods for deterministic database queries

---

## � Umarell Toolkit

The toolkit exposes **3 methods** to the LLM for robust, deterministic queries:

| Method | Purpose | Example Question |
|--------|---------|------------------|
| `query_topology()` | Find building elements | "How many windows on floor 2?" |
| `check_sensor_config()` | Check sensor setup | "Is there a temp sensor in Room 001?" |
| `inspect_zone_metrics()` | Analyze sensor data | "Where is the air quality worst?" |

---

## 💬 Example Conversations

**You:** "How many meeting rooms are on the second floor?"

**L'Umarell:** 
> *[Uses `query_topology(category="meeting", floor="2")`]*
>
> "Ué! I found 3 meeting rooms on floor 2. Not bad, but I bet they're always empty while people waste time at their desks!"

**You:** "Which room has the worst air quality?"

**L'Umarell:** 
> *[Uses `inspect_zone_metrics(zone="whole building", type="co2", goal="max")`]*
>
> "Madòna! Room 205 has CO2 at 1850 ppm! People are breathing like fish in there! Open a window, barlafus!"

---

## 🛠️ Essential Commands

### Check Status
```bash
./scripts/check_status.sh
```

### View Logs
```bash
docker compose logs -f              # All services
docker compose logs -f ollama       # Just Ollama
```

### Restart Services
```bash
docker compose restart
```

### Stop Everything
```bash
docker compose down
```

---

## 📊 Requirements

- **VPS**: 16GB RAM recommended
- **Disk**: ~10GB free space
- **Docker**: Docker Engine + Docker Compose
- **InfluxDB**: External instance with sensor data
- **Ports**: 8080 (Open WebUI), 7474/7687 (Neo4j), 11434 (Ollama)

---

## 🔧 Configuration

### 1. InfluxDB Credentials

Edit `.env` (copy from `config/.env.example`):

```env
INFLUX_HOST=http://your-influxdb:8086
INFLUX_TOKEN=your-token-here
INFLUX_ORG=your-org
INFLUX_BUCKET=your-bucket
```

### 2. Room-to-Sensor Mapping

Edit `config/sensor_config.json`:

```json
{
  "room_to_sensor_map": {
    "ifc_room_001": {
      "temperature": "sensor_001_temp",
      "co2": "sensor_001_co2"
    },
    "ifc_room_002": "sensor_002_temp"
  },
  "sensor_types": {
    "temperature": { "unit": "°C" },
    "co2": { "unit": "ppm" }
  }
}
```

### 3. Import IFC Data

```bash
python src/ifc_to_graph.py --ifc ifc/your_building.ifc --config config/sensor_config.json
```

Extracts IfcSpace entities with semantic properties (storey, category_it/en, area) into Neo4j.

### 4. Install Open WebUI Tool

1. Access http://localhost:8080
2. Go to **Settings** → **Tools** → **+ Add Tool**
3. Copy content of `src/umarell_tool.py`
4. Paste, save, and enable

---

## 🎓 Documentation

- **[README.md](docs/README.md)** - Complete documentation
- **[QUICKREF.md](docs/QUICKREF.md)** - One-page reference
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Deployment checklist
- **[AUTOMATIC_SETUP.md](docs/AUTOMATIC_SETUP.md)** - How auto-setup works

---

## 🚨 Troubleshooting

### Models Not Found?
```bash
./scripts/check_status.sh
docker compose logs ollama
```

### Setup Taking Long?
First launch downloads ~5.5GB of models. Check progress:
```bash
docker compose logs -f ollama
```

### Tool Not Working?
- Verify `.env` has correct InfluxDB credentials
- Check `config/sensor_config.json` is properly configured
- View logs: `docker compose logs open-webui`

---

## 📝 License

Educational and demonstration purposes.

---

## 🙏 Credits

- **Open WebUI**: https://github.com/open-webui/open-webui
- **Ollama**: https://ollama.ai
- **Qwen Models**: Alibaba Cloud
- **Neo4j**: https://neo4j.com
- **Inspiration**: The real Umarells of Milano 👴

---

**L'Umarell says:**

> "Va bene! Now you have a proper project structure. Not like before with files scattered everywhere like a barlafus! Taaac! 👴"

---

## 🚀 Ready to Deploy?

```bash
docker compose up -d
```

**That's it!** Auto-setup handles the rest.

📖 Need help? Check **[docs/QUICKREF.md](docs/QUICKREF.md)**
