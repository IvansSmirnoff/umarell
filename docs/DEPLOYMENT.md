# 🚀 Project Umarell - Deployment Checklist

## Pre-Deployment

- [ ] VPS with 16GB RAM ready
- [ ] Docker installed (`docker --version`)
- [ ] Docker Compose installed (`docker compose version`)
- [ ] Port 8080 available (Open WebUI)
- [ ] Port 7474, 7687 available (Neo4j)
- [ ] Port 11434 available (Ollama)
- [ ] InfluxDB instance accessible with credentials
- [ ] At least 20GB free disk space (for models)

## Step 1: Initial Setup

```bash
# Clone or copy project files to VPS
cd /path/to/umarell

# Create .env file
cp config/.env.example .env

# Edit .env with your InfluxDB credentials
nano .env
```

**Required .env values:**
- [ ] `INFLUX_HOST` set
- [ ] `INFLUX_TOKEN` set
- [ ] `INFLUX_ORG` set
- [ ] `INFLUX_BUCKET` set

## Step 2: Configure Sensors

Edit `config/sensor_config.json`:

- [ ] Map your IFC room IDs to sensor IDs
- [ ] Add sensor metadata (optional)
- [ ] Validate JSON syntax: `cat config/sensor_config.json | jq`

## Step 3: Start Services

```bash
# Start all containers (models will be set up automatically on first launch)
docker compose up -d

# Watch the setup progress (first launch only)
docker compose logs -f ollama

# Or check status anytime
./scripts/check_status.sh
```

**First Launch:** Ollama will automatically:
- Pull `qwen2.5:7b` (4.7GB)
- Pull `qwen2.5-coder:1.5b` (934MB)
- Create the `umarell` model

This takes 10-20 minutes. **Subsequent launches** skip this setup.

- [ ] All containers running
- [ ] Models downloaded (watch Ollama logs)
- [ ] Setup marker created

**Verify:**
```bash
./scripts/check_status.sh
# Or manually:
docker exec ollama ollama list
```

Expected output:
```
NAME                    ID              SIZE
umarell:latest          abc123...       4.7 GB
qwen2.5:7b             def456...       4.7 GB
qwen2.5-coder:1.5b     ghi789...       934 MB
```

## Step 4: Configure Open WebUI

1. **Access Open WebUI:**
   - [ ] Navigate to `http://your-vps-ip:8080`
   - [ ] Create admin account
   - [ ] Login successful

2. **Install the Tool:**
   - [ ] Go to Settings → Tools
   - [ ] Click "+ Add Tool"
   - [ ] Copy content of `src/umarell_tool.py`
   - [ ] Paste and save
   - [ ] Enable the tool

3. **Select Model:**
   - [ ] Click model dropdown in chat
   - [ ] Select "umarell"
   - [ ] Verify it's selected

## Step 5: Import Building Data (Optional)

If you have an IFC file:

```bash
# Option A: Using Docker
docker run --rm \
  --network umarell_smart-building-net \
  -v $(pwd):/data \
  -e NEO4J_URI=bolt://neo4j:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD= \
  python:3.11-slim bash -c \
    "pip install ifcopenshell neo4j && \
     python /data/ifc_to_graph.py --ifc /data/your-building.ifc --config /data/config/sensor_config.json"

# Option B: Using local Python
pip install -r requirements.txt
python ifc_to_graph.py --ifc your-building.ifc --config config/sensor_config.json
```

- [ ] IFC file imported
- [ ] Room nodes created in Neo4j
- [ ] Verify in Neo4j Browser: `http://your-vps-ip:7474`

```cypher
// Check rooms imported
MATCH (r:Room) RETURN r LIMIT 10
```

## Step 6: Test the System

### Test 1: Basic Chat
- [ ] Open chat in Open WebUI
- [ ] Send: "Hello"
- [ ] L'Umarell responds with personality

### Test 2: Tool Execution
- [ ] Send: "What's the temperature in [room_name]?"
- [ ] Tool executes (you'll see a "thinking" indicator)
- [ ] Response includes sensor data
- [ ] L'Umarell adds grumpy commentary

### Test 3: Verify Tool Function
Check Open WebUI logs:
```bash
docker compose logs -f open-webui
```
- [ ] No Python errors
- [ ] Tool functions execute
- [ ] Neo4j queries succeed
- [ ] InfluxDB queries succeed

## Step 7: Production Hardening

### Security
- [ ] Enable Neo4j authentication (edit docker-compose.yml)
- [ ] Configure firewall rules
- [ ] Use HTTPS reverse proxy (nginx/Caddy)
- [ ] Backup `.env` securely
- [ ] Don't commit `.env` to git

### Monitoring
```bash
# Add to crontab for monitoring
*/5 * * * * docker stats --no-stream >> /var/log/umarell-stats.log
```

- [ ] Set up monitoring
- [ ] Configure log rotation
- [ ] Set up backups for Neo4j data

### Performance
- [ ] Monitor RAM usage: `docker stats`
- [ ] Configure swap if needed (4GB recommended)
- [ ] Set up auto-restart policies (already in compose)

## Troubleshooting Commands

```bash
# Check setup status (recommended!)
./scripts/check_status.sh

# Check all container status
docker compose ps

# View logs
docker compose logs -f

# Restart specific service
docker compose restart ollama

# Check Ollama models
docker exec ollama ollama list

# Check Neo4j
curl http://localhost:7474

# Check Open WebUI
curl http://localhost:8080/health

# Check disk space
df -h

# Check memory
free -h

# Full restart
docker compose down
docker compose up -d
```

## Common Issues

### "Model not found"
```bash
# Check status
./scripts/check_status.sh

# View setup logs
docker compose logs ollama

# If needed, manually trigger setup by restarting
docker compose restart ollama
```

### "Tool not executing"
- Check OLLAMA_BASE_URL in Open WebUI env
- Verify config/sensor_config.json is mounted
- Check InfluxDB credentials in .env

### "Out of memory"
- Check: `docker stats`
- Reduce Ollama mem_limit in docker-compose.yml
- Add swap space
- Consider smaller models

### "Neo4j connection refused"
```bash
docker compose logs neo4j
# Wait 30 seconds for Neo4j to fully start
```

## Success Criteria

- [ ] All containers running
- [ ] Models loaded in Ollama
- [ ] Open WebUI accessible
- [ ] Can chat with L'Umarell
- [ ] Tool executes successfully
- [ ] Receives sensor data
- [ ] L'Umarell complains appropriately 😄

## Post-Deployment

- [ ] Document your specific room-to-sensor mappings
- [ ] Create backup script for Neo4j
- [ ] Set up monitoring/alerting
- [ ] Train users on L'Umarell's personality
- [ ] Enjoy the grumpy building inspector!

---

**L'Umarell says:** "Va bene, if you followed all this, maybe you're not such a barlafus after all. Taaac!"
