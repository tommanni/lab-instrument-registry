# Deployment Guide for MetLabs Instrument Registry (DEPRECATED)

**⚠️ DEPRECATED**: This guide describes the old systemd-based deployment method. The system was migrated to containers on 2025-11-04.

**For current deployment instructions, see [deployment-containers.md](deployment-containers.md)**

---

Production server: `met-metlabs.rd.tuni.fi`

**Stack**: Vue.js + Django REST API + Apache + PostgreSQL

**Note**: This documentation is kept for reference and rollback purposes only.

---

## Before You Deploy

**Checklist**:
- [ ] Code merged into `main` branch and tested locally
- [ ] Database backup completed (see [Database Backup](#database-backup))
- [ ] No one else is actively using the system (if possible)
- [ ] You know which parts changed (frontend, backend, or both)

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

### Backend Only
```bash
cd /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab/Backend
sudo git pull origin main
source venv/bin/activate
sudo ./venv/bin/pip install -r requirements.txt  # if requirements.txt changed
python manage.py migrate  # if models changed
sudo python manage.py collectstatic --noinput  # if static files changed
sudo chown -R apache:apache .
sudo systemctl restart metlabs
```

**Verify**: `sudo systemctl status metlabs` and `sudo systemctl status httpd`

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
cd Backend
source venv/bin/activate

# 2. Update dependencies (only if requirements.txt changed)
sudo ./venv/bin/pip install -r requirements.txt

# 3. Run migrations (only if models changed)
python manage.py showmigrations  # Check what will be applied
python manage.py migrate

# 4. Collect static files (only if admin/DRF templates changed)
sudo python manage.py collectstatic --noinput

# 5. Fix ownership and restart
sudo chown -R apache:apache /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab/Backend/
sudo systemctl restart metlabs
```

**Verify**:
```bash
sudo systemctl status metlabs
sudo journalctl -u metlabs -n 20 --no-pager
curl -I http://localhost:8000/api/
```

---

## Critical: SELinux Configuration

**This server uses SELinux in enforcing mode.** If you deploy a new backend or recreate the venv, you MUST set the correct SELinux context or the service will fail with "Permission denied".

**Required after creating/recreating venv**:
```bash
sudo chcon -R -t bin_t /var/www/html/metlabs/[repo]/Backend/venv/bin/
```

**Verify**:
```bash
ls -Z /var/www/html/metlabs/[repo]/Backend/venv/bin/gunicorn
# Should show: bin_t
```

**Check for SELinux denials**:
```bash
sudo ausearch -m avc -ts recent
```

---

## Server Architecture

**Key directories**:
- `/var/www/html/metlabs/build/` - Frontend (served by Apache)
- `/var/www/html/metlabs/proj-a2025-g02-.../Backend/` - Django backend
- `/etc/systemd/system/metlabs.service` - Backend service config
- `/etc/httpd/conf.d/` - Apache configs (metlabs.conf, django.conf)

**Ports**:
- 80/443: Apache (public)
- 8000: Django/Gunicorn (internal, proxied by Apache)

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
sudo git reset --hard [commit-hash]
cd Backend
source venv/bin/activate
sudo ./venv/bin/pip install -r requirements.txt
sudo systemctl restart metlabs
```

### Database Migrations
```bash
cd /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab/Backend
source venv/bin/activate
python manage.py showmigrations
python manage.py migrate instrument_registry [migration_name]
sudo systemctl restart metlabs
```

---

## Maintenance

### Database Backup

**Do this before deploying migrations.**

```bash
cd /var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab/Backend
source venv/bin/activate
python manage.py export_csv
# Creates: laiterekisteri_YYYY-MM-DD.csv
```

**Copy to local**:
```bash
scp USERNAME@met-metlabs.rd.tuni.fi:/var/www/html/metlabs/proj-a2025-g02-instrument-registry-for-met-lab/Backend/laiterekisteri_*.csv ./
```

### Viewing Logs

```bash
# Backend logs
sudo journalctl -u metlabs -n 50 --no-pager  # Last 50 lines
sudo journalctl -u metlabs -f               # Follow live

# Apache logs
sudo tail -f /var/log/django_error.log
sudo tail -f /var/log/django_access.log
```

### Restarting Services

```bash
sudo systemctl restart metlabs  # Backend
sudo systemctl restart httpd    # Apache
```

---

## Troubleshooting

### General Approach

1. **Check service status**: `sudo systemctl status metlabs` and `sudo systemctl status httpd`
2. **Check logs**: `sudo journalctl -u metlabs -n 50` and `sudo tail -50 /var/log/django_error.log`
3. **Check ports**: `sudo netstat -tlnp | grep -E '(8000|80|443)'`

### Permission Denied Errors

**Most common cause**: SELinux blocking gunicorn

```bash
# Check SELinux context
ls -Z /var/www/html/metlabs/[repo]/Backend/venv/bin/gunicorn

# Fix if not bin_t
sudo chcon -R -t bin_t /var/www/html/metlabs/[repo]/Backend/venv/bin/

# Check for SELinux denials
sudo ausearch -m avc -ts recent
```

**Other causes**: File ownership or directory permissions

```bash
# Fix ownership
sudo chown -R apache:apache /var/www/html/metlabs/[repo]/Backend/

# Fix directory traversal
sudo chmod o+x /var/www/html/metlabs/[repo]
sudo chmod o+x /var/www/html/metlabs/[repo]/Backend
```

### Backend Won't Start

**Check**:
- Service logs: `sudo journalctl -u metlabs -n 50 --no-pager`
- Port in use: `sudo netstat -tlnp | grep 8000`
- Service file paths: `cat /etc/systemd/system/metlabs.service | grep WorkingDirectory`

**Common causes**:
- SELinux (see above)
- Wrong paths in service file
- Missing `.env` file or wrong DB credentials
- Missing dependencies in venv

### Frontend Issues

**Check**:
- Apache status: `sudo systemctl status httpd`
- Build directory: `ls -la /var/www/html/metlabs/build/`
- Apache logs: `sudo tail -50 /var/log/django_error.log`

**Common causes**:
- Build directory empty or wrong ownership
- Apache not running

### API Errors (502/504)

**Check**:
- Backend running: `sudo systemctl status metlabs`
- Port listening: `sudo netstat -tlnp | grep 8000`
- Backend logs: `sudo journalctl -u metlabs -f`

**Common cause**: Backend service crashed or not running

### Database Connection Errors

**Check**:
- `.env` file exists: `cat /var/www/html/metlabs/[repo]/Backend/Backend/.env`
- Test connection: `python manage.py dbshell` (from Backend with venv activated)

**Common cause**: Wrong credentials in `.env` file

### Static Files Missing (CSS/JS)

**Check**:
- Staticfiles exist: `ls -la /var/www/html/metlabs/[repo]/Backend/Backend/staticfiles/`
- Apache config: `cat /etc/httpd/conf.d/django.conf | grep Alias`

**Fix**:
```bash
cd /var/www/html/metlabs/[repo]/Backend
source venv/bin/activate
sudo python manage.py collectstatic --noinput
sudo systemctl restart httpd
```

---

## Configuration Files Reference

### metlabs.service
**Location**: `/etc/systemd/system/metlabs.service`

**Key settings**:
- `WorkingDirectory`: Path to Backend directory
- `ExecStart`: Path to gunicorn in venv
- `Environment=DJANGO_SETTINGS_MODULE=Backend.settings.prod`: Django uses production settings

**After editing**: `sudo systemctl daemon-reload && sudo systemctl restart metlabs`

### Apache Configs

**Note**: There are two Apache config files (metlabs.conf and django.conf). This is somewhat redundant - both define API proxying, and they could be consolidated into one file. However, since it's currently working, don't change it unless necessary. The setup exists because:
- `metlabs.conf` handles HTTPS (port 443) - frontend + API proxy
- `django.conf` handles HTTP (port 80) - static files + API proxy

### django.conf
**Location**: `/etc/httpd/conf.d/django.conf`

**Key settings**:
- `Alias /static/`: Path to Backend staticfiles directory (needed for Django admin/DRF browsable API)
- `ProxyPass /api`: Proxies API requests to port 8000

**After editing**: `sudo systemctl restart httpd`

### metlabs.conf
**Location**: `/etc/httpd/conf.d/metlabs.conf`

**Key settings**:
- `DocumentRoot`: Points to `/var/www/html/metlabs/build`
- `ProxyPass /api`: Proxies API requests to port 8000

---

## Full Deployment from Scratch

**Note**: This section is for setting up a completely new deployment (new repository, new group). For regular deployments, use the sections above.

See [deployment-from-scratch.md](deployment-from-scratch.md) for complete instructions.

---

**Last Updated**: 2025-10-08
**Server**: met-metlabs.rd.tuni.fi (RHEL-based, SELinux enforcing)
**Python**: 3.9.21 | **Node**: 22.19.0





