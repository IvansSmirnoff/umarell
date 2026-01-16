# Gemini Context: Umarell

## Project Overview
**Umarell** is an intelligent building management chat interface where the AI embodies a retired Milanese inspector ("Umarell"). It integrates **Open WebUI**, **Ollama**, **Neo4j** (Graph DB for building structure from IFC), and **InfluxDB** (Time-series DB for sensor data) to monitor building conditions (temperature, HVAC, etc.) and "complain" about inefficiencies.

## Architecture
-   **Frontend**: Open WebUI (localhost:8080).
-   **AI Backend**: Ollama running `qwen2.5:7b` (personality model).
-   **Databases**:
    -   **Neo4j**: Stores building topology (Rooms, Zones, etc.) derived from IFC files. Nodes include semantic properties (`storey`, `category_it`, `category_en`, `area`) and full IFC property set dumps.
    -   **InfluxDB**: Stores real-time sensor data.
-   **Integration**: `src/umarell_tool.py` is a **multi-purpose toolkit** exposing 3 methods to the LLM.

## Umarell Toolkit (3 Methods)

The toolkit uses **deterministic query building** (no LLM-generated SQL/Cypher) for robustness:

| Method | Purpose | Example Question |
|--------|---------|------------------|
| `query_topology(category, floor, name_contains)` | Find building elements | "How many windows on floor 2?" |
| `check_sensor_config(room_name)` | Check sensor configuration | "Is there a temp sensor in Room 001?" |
| `inspect_zone_metrics(zone, type, goal, time_range)` | Analyze sensor data across zones | "Where is the air quality worst?" |

### Method Details
-   **query_topology**: Searches Neo4j for rooms/elements by category (EN/IT), floor, or name. Returns JSON with count and items.
-   **check_sensor_config**: Finds room in Neo4j, looks up `sensor_config.json`, returns configured sensors.
-   **inspect_zone_metrics**: Multi-step pipeline: (1) find rooms in zone, (2) filter by sensor type, (3) batch query InfluxDB with regex, (4) aggregate results (report/max/min/avg).

## Key Directories
-   **`src/`**: Python source code.
    -   `umarell_tool.py`: Main Open WebUI toolkit (3 methods, deterministic queries).
    -   `ifc_to_graph.py`: IFC to Neo4j importer. Extracts semantics (`storey`, `category_it`, `category_en`, `area`) from IfcSpace entities and IFC_Locali property sets.
    -   `llm_router_tool.py`: Legacy implementation (deprecated).
-   **`config/`**: Configuration files.
    -   `modelfiles/Modelfile_Umarell`: Defines the "Umarell" system prompt and persona.
    -   `sensor_config.json`: Maps IFC room IDs to InfluxDB sensor IDs (supports dict, string, or list formats).
    -   `.env.example`: Template for environment variables.
-   **`scripts/`**: Automation scripts.
    -   `check_status.sh`: Verifies service health.
    -   `init_ollama.sh`: Handles model downloading and creation.
    -   `entrypoint.sh`: Docker container entrypoint.
-   **`docs/`**: Comprehensive documentation.

## Development & Usage

### Prerequisites
-   Docker & Docker Compose.
-   External InfluxDB instance (credentials in `.env`).

### Common Commands
-   **Start Services**: `docker compose up -d`
-   **Check Status**: `./scripts/check_status.sh`
-   **Logs**: `docker compose logs -f` (or `docker compose logs -f ollama`)
-   **Stop**: `docker compose down`
-   **Restart**: `docker compose restart`

### IFC Import
```bash
python src/ifc_to_graph.py --ifc path/to/file.ifc --config config/sensor_config.json
```
Extracts IfcSpace entities with semantic properties from IFC_Locali psets (storey, category) and creates Room nodes in Neo4j.

### Configuration
1.  **Environment**: Copy `config/.env.example` to `.env` and set InfluxDB credentials.
2.  **Sensors**: Update `config/sensor_config.json` to map rooms to specific sensors.
3.  **Tool Installation**: The content of `src/umarell_tool.py` must be manually added to Open WebUI's "Tools" section.

## Conventions
-   **Persona**: The AI must strictly adhere to the "Umarell" persona (Milanese dialect, grumpy, efficiency-obsessed).
-   **Docker-First**: The project is designed to run in containers.
-   **Structure**: Keep code in `src/`, config in `config/`, and scripts in `scripts/`.
-   **No LLM Query Generation**: All database queries are built deterministically in Python with sanitized inputs.
