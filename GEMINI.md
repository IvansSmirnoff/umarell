# Gemini Context: Umarell

## Project Overview
**Umarell** is an intelligent building management chat interface where the AI embodies a retired Milanese inspector ("Umarell"). It integrates **Open WebUI**, **Ollama**, **Neo4j** (Graph DB for building structure from IFC), and **InfluxDB** (Time-series DB for sensor data) to monitor building conditions (temperature, HVAC, etc.) and "complain" about inefficiencies.

## Architecture
-   **Frontend**: Open WebUI (localhost:8080).
-   **AI Backend**: Ollama running `qwen2.5:7b` and `qwen2.5-coder:1.5b`.
-   **Databases**:
    -   **Neo4j**: Stores building topology (Rooms, Zones, etc.) derived from IFC files. Nodes include semantic properties (`storey`, `category_it`, `category_en`, `area`) and full IFC property set dumps.
    -   **InfluxDB**: Stores real-time sensor data.
-   **Integration**: `src/umarell_tool.py` connects the AI to the databases.

## Key Directories
-   **`src/`**: Python source code.
    -   `umarell_tool.py`: Main Open WebUI tool definition.
    -   `ifc_to_graph.py`: Script to import IFC data into Neo4j. Extracts semantics and handles IT/EN translation.
    -   `llm_router_tool.py`: Alternative implementation.
-   **`config/`**: Configuration files.
    -   `modelfiles/Modelfile_Umarell`: Defines the "Umarell" system prompt and persona.
    -   `sensor_config.json`: Maps IFC room IDs to InfluxDB sensor IDs.
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

### Configuration
1.  **Environment**: Copy `config/.env.example` to `.env` and set InfluxDB credentials.
2.  **Sensors**: Update `config/sensor_config.json` to map rooms to specific sensors.
3.  **Tool Installation**: The content of `src/umarell_tool.py` must be manually added to Open WebUI's "Tools" section.

## Conventions
-   **Persona**: The AI must strictly adhere to the "Umarell" persona (Milanese dialect, grumpy, efficiency-obsessed).
-   **Docker-First**: The project is designed to run in containers.
-   **Structure**: Keep code in `src/`, config in `config/`, and scripts in `scripts/`.
