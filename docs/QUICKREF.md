# 🚀 Project Umarell - Quick Reference

## One-Command Deployment

```bash
docker compose up -d
```

**That's it!** First launch auto-installs models (10-20 min). Subsequent launches are instant.

---

## Essential Commands

### Check Status
```bash
./scripts/check_status.sh
```

### Watch Setup Progress (First Launch)
```bash
docker compose logs -f ollama
```

### Access Services
- **Open WebUI:** http://localhost:8080
- **Neo4j Browser:** http://localhost:7474
- **Ollama API:** http://localhost:11434

### Restart Services
```bash
docker compose restart
```

### Stop Everything
```bash
docker compose down
```

### Fresh Start
```bash
docker compose down
docker compose up -d
```

---

## First-Time Setup Checklist

1. **Configure environment:**
   ```bash
   cp config/.env.example .env
   nano .env  # Add InfluxDB credentials
   ```

2. **Start services:**
   ```bash
   docker compose up -d
   ```

3. **Wait for models** (first launch only - 10-20 min):
   ```bash
   docker compose logs -f ollama
   # Or check: ./scripts/check_status.sh
   ```

4. **Access Open WebUI:** http://localhost:8080
   - Create account (first user = admin)
   - Go to Settings → Tools → + Add Tool
   - Paste content of `src/umarell_tool.py`
   - Enable the tool

5. **Select model:** Choose "umarell" from dropdown

6. **Start chatting!** 🎉

---

## File Overview

### Core Files
- `docker-compose.yml` - Infrastructure definition
- `modelfiles/Modelfile_Umarell` - L'Umarell persona
- `config/sensor_config.json` - Room-to-sensor mapping
- `src/umarell_tool.py` - Open WebUI tool (install in UI)

### Scripts
- `check_status.sh` - Check setup status ⭐
- `quickstart.sh` - Quick deployment helper
- `setup_umarell.sh` - Legacy manual setup (not needed)
- `scripts/entrypoint.sh` - Docker entrypoint (auto-runs)
- `scripts/init_ollama.sh` - Model initialization (auto-runs)

### Documentation
- `README.md` - Full documentation
- `DEPLOYMENT.md` - Deployment checklist
- `AUTOMATIC_SETUP.md` - How auto-setup works
- `SUMMARY.md` - Task completion summary

### Configuration
- `config/.env.example` - Template (copy to `.env`)
- `.env` - Your credentials (don't commit!)

---

## Installed Models

After first launch:

| Model | Size | Purpose |
|-------|------|---------|
| **umarell:latest** | 4.7 GB | L'Umarell persona (grumpy inspector) |
| **qwen2.5:7b** | 4.7 GB | Base model (the brain) |
| **qwen2.5-coder:1.5b** | 934 MB | Query generator (writes Cypher/Flux) |

**Total:** ~5.5 GB

---

## Troubleshooting

### Models Not Found?
```bash
./scripts/check_status.sh
docker compose logs ollama
```

### Setup Stuck?
```bash
# Check if downloading
docker compose logs ollama | grep -i pulling

# Restart if needed
docker compose restart ollama
```

### Force Re-setup
```bash
docker exec ollama rm /root/.ollama/.umarell_setup_complete
docker compose restart ollama
```

### Out of Memory?
```bash
docker stats  # Check usage
# Consider reducing mem_limit in docker-compose.yml
```

### Tool Not Working?
- Check `.env` has correct InfluxDB credentials
- Verify `config/sensor_config.json` is mounted
- Check Open WebUI logs: `docker compose logs open-webui`

---

## Example Conversation

**You:** "What's the temperature in Room 101?"

**L'Umarell:** 
> "Ué! Let me check... *grumbles*"
>
> [Tool: Queries Neo4j → Finds room → Queries InfluxDB → Gets 24°C]
>
> "Madòna! Room 101 is at 24 degrees! Ma sèm matt? We're burning money to heat the whole neighborhood! Turn it down, barlafus! This is sprechi (waste)!"

---

## Resource Usage (16GB VPS)

- **Ollama:** ~8 GB (limited)
- **Neo4j:** ~2 GB
- **Open WebUI:** ~1 GB  
- **System:** ~2 GB
- **Free:** ~3 GB ✅

**Disk:** ~8-10 GB (models + containers)

---

## Production Checklist

- [ ] Configure `.env` with real InfluxDB credentials
- [ ] Enable Neo4j authentication (edit `docker-compose.yml`)
- [ ] Set up HTTPS reverse proxy (nginx/Caddy)
- [ ] Configure firewall (only expose 8080)
- [ ] Set up backups for `neo4j_data` volume
- [ ] Monitor resources: `docker stats`
- [ ] Set up log rotation

---

## Support

**Check status:**
```bash
./scripts/check_status.sh
```

**View logs:**
```bash
docker compose logs -f         # All services
docker compose logs -f ollama  # Just Ollama
docker compose logs -f open-webui  # Just Open WebUI
```

**Common files to check:**
- `.env` - InfluxDB credentials
- `config/sensor_config.json` - Room mappings
- `docker-compose.yml` - Service config

---

## L'Umarell's Wisdom

> "Listen, barlafus! It's simple:
> 1. Run `docker compose up -d`
> 2. Wait for setup (first time)
> 3. Access http://localhost:8080
> 4. Install the tool
> 5. Chat with me
> 
> Don't overthink it! Taaac!"

---

**🎉 Ready to deploy? Just run:** `docker compose up -d`
