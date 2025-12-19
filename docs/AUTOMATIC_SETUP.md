# 🎉 AUTOMATIC SETUP - Just One Command!

## What Changed?

**TL;DR:** Run `docker compose up -d` and everything happens automatically! 🚀

### Before (Manual Setup)
```bash
docker compose up -d
./setup_umarell.sh  # ← You had to run this manually
# Wait 10-20 minutes...
```

### Now (Automatic Setup)
```bash
docker compose up -d  # ← That's it! Models auto-install on first launch
# Watch: docker compose logs -f ollama
```

---

## 🔧 How It Works

### Automatic Initialization System

When you run `docker compose up -d`:

1. **Ollama container starts** with custom entrypoint
2. **Checks for setup marker** (`/root/.ollama/.umarell_setup_complete`)
3. **First launch only:** Downloads models and creates Umarell persona
4. **Subsequent launches:** Skips setup (marker exists)

### Smart Detection

The system checks if each model already exists:
- ✅ **qwen2.5:7b** exists? Skip download
- ✅ **qwen2.5-coder:1.5b** exists? Skip download  
- ✅ **umarell** exists? Skip creation

This means:
- Fast restarts after first launch
- Safe to restart containers anytime
- No duplicate downloads
- Idempotent setup (can run multiple times safely)

---

## 📁 New Files Created

### `/scripts/entrypoint.sh`
Custom Docker entrypoint that:
- Starts Ollama server
- Waits for API to be ready
- Runs initialization script
- Keeps container alive

### `/scripts/init_ollama.sh`
Initialization script that:
- Checks for setup marker file
- Conditionally pulls models (only if missing)
- Creates Umarell persona
- Writes marker file when complete

### `/check_status.sh`
Utility script to check setup status:
```bash
./check_status.sh
```

Shows:
- Container status
- Installed models
- Setup completion status
- Service URLs
- Helpful commands

---

## 🔄 Updated Files

### `docker-compose.yml`
- ✅ Added `./scripts:/scripts` volume mount
- ✅ Custom entrypoint: `/scripts/entrypoint.sh`
- ✅ Healthcheck for Ollama API
- ✅ Proper depends_on with health condition for Open WebUI

### `README.md`
- ✅ Removed manual setup step
- ✅ Updated Quick Start to show automatic setup
- ✅ Clarified first vs subsequent launches

### `DEPLOYMENT.md`
- ✅ Removed Step 4 (manual model setup)
- ✅ Renumbered steps
- ✅ Added `./check_status.sh` to troubleshooting
- ✅ Updated verification commands

### `quickstart.sh`
- ✅ Updated messaging about automatic setup
- ✅ Shows how to watch setup progress

---

## 🎯 New User Experience

### First Launch (10-20 minutes)

```bash
# 1. Configure
cp .env.example .env
nano .env  # Add InfluxDB credentials

# 2. Start (automatic setup begins)
docker compose up -d

# 3. Watch progress (optional)
docker compose logs -f ollama

# 4. Check when ready
./check_status.sh
```

**What you'll see in logs:**
```
🏗️  Umarell Initialization Check
=================================
🆕 First time setup detected - Installing Umarell models...

🧠 Pulling qwen2.5:7b (The Brain - 4.7GB, this may take a while)...
pulling manifest... done
pulling layers... [████████░░░░] 45% 2.1GB/4.7GB

🔧 Pulling qwen2.5-coder:1.5b (The Tool User - 934MB)...
pulling manifest... done
...

👴 Creating custom 'umarell' model with Milanese attitude...
✅ Creating setup marker file...

🎉 Setup Complete!
L'Umarell says: 'Taaac! Everything is ready...'
```

### Subsequent Launches (Instant)

```bash
docker compose up -d
```

**What you'll see:**
```
✅ Umarell is already set up (found marker file)
   Models installed:
   umarell:latest
   qwen2.5:7b
   qwen2.5-coder:1.5b

🎉 L'Umarell says: 'Va bene, I'm ready to inspect!'
```

---

## 🛠️ Maintenance Commands

### Check Setup Status
```bash
./check_status.sh
```

### Force Re-setup (if needed)
```bash
# Remove the marker file
docker exec ollama rm /root/.ollama/.umarell_setup_complete

# Restart to trigger setup
docker compose restart ollama
```

### Manual Model Pull (if needed)
```bash
docker exec ollama ollama pull qwen2.5:7b
docker exec ollama ollama pull qwen2.5-coder:1.5b
docker exec ollama ollama create umarell -f /modelfiles/Modelfile_Umarell
```

### View Setup Logs
```bash
docker compose logs ollama
```

---

## ✅ Benefits

### For Users
- 🚀 **One command deployment** - No manual setup script
- 🔄 **Fast restarts** - Skip setup after first launch
- 🛡️ **Idempotent** - Safe to restart anytime
- 📊 **Status checking** - `./check_status.sh` shows everything

### For Deployment
- 📦 **Production ready** - Works same way in dev and prod
- 🔧 **Self-healing** - Can detect and fix missing models
- 📝 **Better logging** - Clear progress indicators
- ⚡ **Healthchecks** - Open WebUI waits for Ollama to be ready

### Technical
- ✅ **Docker-native** - No external scripts to run
- ✅ **Persistent** - Marker file survives restarts
- ✅ **Conditional** - Only downloads what's missing
- ✅ **Fail-safe** - Validates each step

---

## 📊 File Structure

```
umarell/
├── docker-compose.yml        # ← Updated: entrypoint + healthcheck
├── quickstart.sh            # ← Updated: mentions auto-setup
├── check_status.sh          # ← NEW: status checker
├── setup_umarell.sh         # ← LEGACY: kept for manual use
├── README.md                # ← Updated: removed manual step
├── DEPLOYMENT.md            # ← Updated: auto-setup flow
└── scripts/                 # ← NEW DIRECTORY
    ├── entrypoint.sh       # ← NEW: Docker entrypoint
    └── init_ollama.sh      # ← NEW: Initialization logic
```

---

## 🎓 What You Learned

This implementation demonstrates:

1. **Docker Entrypoint Pattern** - Custom initialization in containers
2. **Idempotent Setup** - Marker files for one-time operations
3. **Healthchecks** - Service dependencies with health conditions
4. **Progressive Enhancement** - Works without setup, better with it
5. **User Experience** - Zero manual intervention needed

---

## 🚀 Deploy Now!

On your VPS:

```bash
# That's literally it
docker compose up -d
```

First launch: Grab coffee ☕ (10-20 min)  
Every other launch: Instant! ⚡

**L'Umarell says:**

> "Taaac! Now THIS is how you do automation! No more running scripts like a barlafus. Just one command and everything works. Bravo!"

---

## 📞 Need Help?

```bash
# Check what's happening
./check_status.sh

# Watch live setup
docker compose logs -f ollama

# Restart everything
docker compose restart

# Nuclear option (fresh start)
docker compose down
docker compose up -d
```

🎉 **Automatic setup complete!** Enjoy your grumpy building inspector!
