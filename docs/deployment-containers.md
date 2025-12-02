# Deployment Guide - Containerized System (Podman)

Production server: `met-metlabs.rd.tuni.fi`

**Stack**: Vue.js + Django REST API (containerized) + PostgreSQL (containerized) + Semantic Search (containerized) + Apache

**Migration Date**: 2025-11-04  
**Previous deployment method**: See [deployment.md](deployment.md) (systemd-based, deprecated)

---

## Architecture Overview

**Containers** (managed by Podman):
- `metlabs-db`: PostgreSQL 17 with pgvector extension (port 5433 → 5432)
- `metlabs-web`: Django + Gunicorn (port 8000)
- `metlabs-semantic-search`: FastAPI semantic search service (port 8001)

**Apache**: Serves frontend static files and proxies `/api/*` to containerized Django

**Frontend**: Built with Vite, served from `/var/www/html/metlabs/build/`

### Rootless Podman Setup

**Important**: This system uses **rootless podman** running under a dedicated service account (not root). This is a secure and valid production setup.

**Current setup**:
- Containers run under the `metlabs` user account (dedicated service account)
- Volumes stored in `/opt/tuni/containers/metlabs/storage/volumes/`
- The `metlabs` user was created specifically for running these containers

**Why a dedicated user?**
- Using a dedicated service account (`metlabs`) ensures the system continues working regardless of individual user account changes
- More secure and follows IT department recommendations

**For future developers**:
- Use `sudo su - metlabs` to switch to the service account
- Manage containers with `podman` and `podman-compose` commands
- The service account has lingering enabled, so containers auto-start on server reboot

**Why rootless?**
- More secure (containers don't run as root)
- Proper isolation between users
- Standard practice for multi-user servers

---

## Before You Deploy

**Checklist**:
- [ ] Code merged into `main` branch and tested locally
- [ ] Database backup completed (see [Database Backup](#database-backup))
- [ ] No one else is actively using the system
- [ ] You know which parts changed (frontend, backend, containers)

**If deploying both**: Deploy backend first, then frontend.

---

## Quick Reference

### Frontend Only
```bash
cd /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab/Frontend
sudo git pull origin main
sudo npm install  # if package.json changed
sudo npm run build
sudo systemctl stop httpd
sudo mv /var/www/html/metlabs/build /var/www/html/metlabs/build_backup_$(date +%Y-%m-%d_%H%M)
sudo mv dist /var/www/html/metlabs/build
sudo chown -R apache:apache /var/www/html/metlabs/build
sudo systemctl start httpd
```

### Backend Only (Code Changes)
```bash
# Pull latest code
cd /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab
sudo git pull origin main

# Switch to metlabs service account
sudo su - metlabs
cd /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab

# Rebuild and recreate web container
podman-compose -f docker-compose.prod.yml build web
podman stop metlabs-web
podman rm metlabs-web
podman-compose -f docker-compose.prod.yml up -d web

# Check logs
podman logs -f metlabs-web
```

### Backend (Dependency Changes)
```bash
# Pull latest code
cd /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab
sudo git pull origin main

# Switch to metlabs service account
sudo su - metlabs
cd /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab

# Rebuild with --no-cache to force fresh install
podman-compose -f docker-compose.prod.yml build --no-cache web
podman stop metlabs-web
podman rm metlabs-web
podman-compose -f docker-compose.prod.yml up -d web
```

### Database Migrations
```bash
# Switch to metlabs service account
sudo su - metlabs

# Migrations run automatically on container start
# Check migration status
podman exec metlabs-web python manage.py showmigrations

# Or run manually
podman exec metlabs-web python manage.py migrate
```

---

## Detailed Deployment Steps

### Frontend Deployment

**When**: You've changed Vue.js code only.

```bash
# 1. Pull latest code
cd /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab
sudo git pull origin main
cd Frontend

# 2. Install dependencies (only if package.json changed)
sudo npm install

# 3. Build
sudo npm run build

# 4. Deploy
sudo systemctl stop httpd
sudo mv /var/www/html/metlabs/build /var/www/html/metlabs/build_backup_$(date +%Y-%m-%d_%H%M)
sudo mv dist /var/www/html/metlabs/build
sudo chown -R apache:apache /var/www/html/metlabs/build
sudo systemctl start httpd
```

**Verify**:
```bash
sudo systemctl status httpd
curl -I http://met-metlabs.rd.tuni.fi/
```

### Backend Deployment

**When**: You've changed Django code, models, or dependencies.

```bash
# 1. Pull latest code
cd /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab
sudo git pull origin main

# 2. Switch to metlabs service account
sudo su - metlabs
cd /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab

# 3. Rebuild web container
podman-compose -f docker-compose.prod.yml build web

# 4. Recreate container
podman stop metlabs-web
podman rm metlabs-web
podman-compose -f docker-compose.prod.yml up -d web

# 5. Watch logs to ensure it starts correctly
podman logs -f metlabs-web
# Press Ctrl+C when you see "Booting worker with pid"
```

**Verify**:
```bash
podman ps  # All containers should show "Up" and "healthy"
curl http://localhost:8000/api/instruments/
```

**Note**: Migrations run automatically on container start (see `docker-compose.prod.yml` command).

---

## Container Management

### View Running Containers
```bash
podman ps
```

### View Logs
```bash
# Switch to metlabs service account first
sudo su - metlabs

# All containers
podman-compose -f docker-compose.prod.yml logs

# Specific container
podman logs metlabs-web
podman logs metlabs-db
podman logs metlabs-semantic-search

# Follow logs (live)
podman logs -f metlabs-web
```

### Restart Containers
```bash
# Switch to metlabs service account first
sudo su - metlabs

# Restart all
podman-compose -f docker-compose.prod.yml restart

# Restart specific container
podman restart metlabs-web
```

### Stop/Start Containers
```bash
# Switch to metlabs service account first
sudo su - metlabs

# Stop all
podman-compose -f docker-compose.prod.yml down

# Start all
podman-compose -f docker-compose.prod.yml up -d

# Stop specific container
podman stop metlabs-web

# Start specific container
podman start metlabs-web
```

### Execute Commands in Containers
```bash
# Switch to metlabs service account first
sudo su - metlabs

# Django management commands
podman exec metlabs-web python manage.py migrate
podman exec metlabs-web python manage.py createsuperuser
podman exec metlabs-web python manage.py collectstatic --noinput
podman exec metlabs-web python manage.py precompute_embeddings

# Interactive shell
podman exec -it metlabs-web bash
podman exec -it metlabs-db psql -U metlabs -d metlabs

# Database shell
podman exec -it metlabs-web python manage.py dbshell
```

---

## Maintenance

### Database Backup

**PostgreSQL dump** (recommended):
```bash
# Switch to metlabs service account first
sudo su - metlabs

# Create backup
podman exec metlabs-db pg_dump -U metlabs -d metlabs > ~/backup_$(date +%Y%m%d_%H%M%S).sql

# Copy to local machine (from your local terminal, not on server)
scp USERNAME@met-metlabs.rd.tuni.fi:/home/metlabs/backup_*.sql ./
```

**CSV export** (alternative):
```bash
# Switch to metlabs service account first
sudo su - metlabs

podman exec metlabs-web python manage.py export_csv
podman cp metlabs-web:/app/laiterekisteri_*.csv ~/
```

### Media Files Backup

**CRITICAL**: The `media_files` volume contains all user-uploaded file attachments. If this volume is lost, all attachments are permanently deleted.

**Backup media files**:
```bash
# Switch to metlabs service account first
sudo su - metlabs

# Option 1: Using podman volume export (recommended)
podman volume export proj-a2025-g02-instrument-registry-for-met-lab_media_files -o ~/media_backup_$(date +%Y%m%d_%H%M%S).tar

# Option 2: Direct tar from volume location
# First, find your volume location:
podman volume inspect proj-a2025-g02-instrument-registry-for-met-lab_media_files | grep Mountpoint
# Then backup (replace <username> with your actual username):
sudo tar -czf ~/media_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /opt/tuni/containers/<username>/storage/volumes/proj-a2025-g02-instrument-registry-for-met-lab_media_files/_data/ .

# Copy to local machine
scp USERNAME@met-metlabs.rd.tuni.fi:~/media_backup_*.tar* ./
```

**Restore media files**:
```bash
# Option 1: Using podman volume import
podman volume import proj-a2025-g02-instrument-registry-for-met-lab_media_files ~/media_backup_TIMESTAMP.tar

# Option 2: Extract tar to volume location
# Stop web container first
podman stop metlabs-web
# Extract (replace <username> with your actual username)
sudo tar -xzf ~/media_backup_TIMESTAMP.tar.gz -C /opt/tuni/containers/<username>/storage/volumes/proj-a2025-g02-instrument-registry-for-met-lab_media_files/_data/
# Restart web container
podman start metlabs-web
```

**Backup schedule recommendation**:
- Database: Before every deployment
- Media files: Weekly or before major changes
- Store backups in a safe location (not just on the server)

### Database Restore

**From PostgreSQL dump**:
```bash
# Copy backup to server
scp backup_TIMESTAMP.sql USERNAME@met-metlabs.rd.tuni.fi:~/

# Copy into container
podman cp ~/backup_TIMESTAMP.sql metlabs-db:/tmp/backup.sql

# Stop web container
podman stop metlabs-web

# Drop and recreate database
podman exec -it metlabs-db psql -U metlabs -d postgres -c "DROP DATABASE metlabs;"
podman exec -it metlabs-db psql -U metlabs -d postgres -c "CREATE DATABASE metlabs;"

# Restore
podman exec -it metlabs-db psql -U metlabs -d metlabs -f /tmp/backup.sql

# Start web container (migrations will run)
podman start metlabs-web
```

### Precompute Embeddings

After importing data or adding new instruments:
```bash
podman exec metlabs-web python manage.py precompute_embeddings
```

### Update Semantic Search Models

Models are cached in a volume. To force re-download:
```bash
podman volume rm proj-a2025-g02-instrument-registry-for-met-lab_semantic-models-data
podman-compose -f docker-compose.prod.yml up -d semantic-search-service
```

---

## Rollback

### Frontend
```bash
sudo systemctl stop httpd
sudo rm -rf /var/www/html/metlabs/build
sudo cp -r /var/www/html/metlabs/build_backup_[TIMESTAMP] /var/www/html/metlabs/build
sudo systemctl start httpd
```

### Backend
```bash
cd /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab
git reset --hard [commit-hash]
podman-compose -f docker-compose.prod.yml build web
podman stop metlabs-web
podman rm metlabs-web
podman-compose -f docker-compose.prod.yml up -d web
```

### Database
```bash
# Restore from backup (see Database Restore section)
```

---

## Troubleshooting

### General Approach

1. **Check container status**: `podman ps`
2. **Check logs**: `podman logs metlabs-web`
3. **Check Apache**: `sudo systemctl status httpd`
4. **Check ports**: `sudo netstat -tlnp | grep -E '(8000|8001|5433)'`

### Container Won't Start

**Check logs**:
```bash
podman logs metlabs-web
podman logs metlabs-db
podman logs metlabs-semantic-search
```

**Common causes**:
- Dependency missing in requirements.txt → rebuild with `--no-cache`
- Database not healthy → check `podman logs metlabs-db`
- Port conflict → check `sudo netstat -tlnp | grep 8000`

### Database Connection Errors

**Check**:
```bash
# Verify db container is healthy
podman ps

# Check db logs
podman logs metlabs-db

# Test connection from web container
podman exec metlabs-web python manage.py dbshell
```

**Common causes**:
- Wrong credentials in `.env` file
- Database container not running or unhealthy

### Semantic Search Not Working

**Check**:
```bash
# Check if container is healthy
podman ps

# Check logs
podman logs metlabs-semantic-search

# Test endpoint
curl http://localhost:8001/healthz
```

**Common causes**:
- Models not downloaded → check logs for download progress
- Container unhealthy → healthcheck requires `curl` in container

### API Returns 502/504

**Check**:
```bash
# Backend running?
podman ps | grep metlabs-web

# Backend logs
podman logs metlabs-web

# Apache proxy config
sudo cat /etc/httpd/conf.d/metlabs.conf | grep ProxyPass
```

**Common causes**:
- Web container crashed → check logs
- Apache proxying to wrong port → should be 8000
- Conflicting Apache configs → only metlabs.conf should proxy /api

---

## Configuration Files

### docker-compose.prod.yml
**Location**: `/var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab/docker-compose.prod.yml`

**Key settings**:
- Port mappings (localhost only for security)
- Environment variables from `.env` file
- Volume mounts for persistent data
- Health checks
- Restart policies

**After editing**: Rebuild and restart containers

### .env
**Location**: `/var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab/.env`

**Contains**:
- `SECRET_KEY`: Django secret key
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Database credentials
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `FINE_TUNED_OPUS_MT_ID`: HuggingFace model ID

**Security**: Never commit this file to git (already in .gitignore)

### Apache Configs
**Location**: `/etc/httpd/conf.d/metlabs.conf`

**Key settings**:
- `DocumentRoot /var/www/html/metlabs/build`: Frontend location
- `ProxyPass /api http://127.0.0.1:8000/api`: Proxy to containerized Django

**After editing**: `sudo systemctl restart httpd`

**Note**: `django.conf` should be disabled (renamed to `.disabled`) to avoid conflicts.

---

## Server Architecture

**Directories**:
- `/var/www/html/metlabs/build/` - Frontend (served by Apache)
- `/var/www/html/metlabs/proj-a2025-g02-.../` - Project root
- `/var/www/html/metlabs/backups/` - Database backups

**Ports**:
- 80/443: Apache (public)
- 8000: Django/Gunicorn (internal, containerized)
- 8001: Semantic search (internal, containerized)
- 5433: PostgreSQL (internal, containerized, mapped from 5432)

**Volumes** (persistent data):
- `postgres_data`: Database files
- `semantic-models-data`: ML models cache
- `static_files`: Django static files
- `media_files`: User uploads

---

**Last Updated**: 2025-11-18 (Added rootless podman documentation and media files backup)
**Server**: met-metlabs.rd.tuni.fi (RHEL-based)
**Podman**: 5.4.0 (rootless) | **podman-compose**: 1.5.0

