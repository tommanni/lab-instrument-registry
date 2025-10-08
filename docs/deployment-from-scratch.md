# Full Deployment from Scratch

This guide is for setting up a completely new deployment (new repository, new group taking over the project).

**For regular deployments**, see [deployment.md](deployment.md).

---

## Prerequisites

- SSH access to `met-metlabs.rd.tuni.fi`
- Sudo privileges
- Access to GitLab repository
- Code merged into `main` branch

---

## Step 1: Clone Repository

```bash
ssh met-metlabs.rd.tuni.fi
cd /var/www/html/metlabs

# Clone to main branch
sudo git clone -b main [YOUR-REPO-URL] [new-directory-name]

# Example:
# sudo git clone -b main git@course-gitlab.tuni.fi:sw-eng-project-2025/proj-a2025-g03-... metlabs-g03

# Set ownership
sudo chown -R apache:apache [new-directory-name]
```

---

## Step 2: Set Up Backend

```bash
cd /var/www/html/metlabs/[new-directory-name]/Backend

# Create virtual environment
sudo python3 -m venv venv
sudo chown -R apache:apache venv

# Install dependencies
source venv/bin/activate
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install -r requirements.txt
sudo ./venv/bin/pip install gunicorn
sudo chown -R apache:apache venv
```

---

## Step 3: Configure Environment

```bash
# Copy .env from old deployment
sudo cp /var/www/html/metlabs/[old-directory]/Backend/Backend/.env \
        /var/www/html/metlabs/[new-directory-name]/Backend/Backend/.env

sudo chown apache:apache /var/www/html/metlabs/[new-directory-name]/Backend/Backend/.env
```

The `.env` file must contain:
```
SECRET_KEY=your-secret-key-here
DB_NAME=metlabs
DB_USER=metlabs
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432
```

Get actual values from `/etc/systemd/system/metlabs.service` or the old `.env` file.

---

## Step 4: Verify Django Settings

Ensure `Backend/Backend/settings/prod.py` has:

```python
from .base import *

SECRET_KEY = env("SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = ['met-metlabs.rd.tuni.fi', 'localhost', '127.0.0.1']

# Static files configuration
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

Add `STATIC_ROOT` if missing.

---

## Step 5: Database Setup

```bash
cd /var/www/html/metlabs/[new-directory-name]/Backend
source venv/bin/activate

# Check and apply migrations
python manage.py showmigrations
python manage.py migrate

# Collect static files
sudo mkdir -p Backend/staticfiles
sudo chown -R apache:apache Backend/staticfiles
sudo python manage.py collectstatic --noinput
sudo chown -R apache:apache Backend/staticfiles
```

---

## Step 6: Fix SELinux and Permissions

**Critical - service will fail without this.**

```bash
# Set SELinux context for gunicorn
sudo chcon -R -t bin_t /var/www/html/metlabs/[new-directory-name]/Backend/venv/bin/

# Verify
ls -Z /var/www/html/metlabs/[new-directory-name]/Backend/venv/bin/gunicorn
# Should show: bin_t

# Fix ownership
sudo chown -R apache:apache /var/www/html/metlabs/[new-directory-name]/Backend/

# Fix directory permissions
sudo chmod o+x /var/www/html/metlabs/[new-directory-name]
sudo chmod o+x /var/www/html/metlabs/[new-directory-name]/Backend
sudo chmod o+x /var/www/html/metlabs/[new-directory-name]/Backend/venv
```

---

## Step 7: Update Service File

```bash
sudo nano /etc/systemd/system/metlabs.service
```

Update these lines:
```ini
WorkingDirectory=/var/www/html/metlabs/[new-directory-name]/Backend/
ExecStart=/var/www/html/metlabs/[new-directory-name]/Backend/venv/bin/gunicorn \
  --workers 3 \
  --bind 0.0.0.0:8000 \
  Backend.wsgi:application
```

Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl stop metlabs
sudo systemctl start metlabs
sudo systemctl status metlabs
```

---

## Step 8: Build and Deploy Frontend

```bash
cd /var/www/html/metlabs/[new-directory-name]/Frontend

# Install and build
sudo chown -R apache:apache .
sudo npm install
sudo npm run build

# Deploy
sudo systemctl stop httpd
sudo mv /var/www/html/metlabs/build /var/www/html/metlabs/build_backup_$(date +%Y-%m-%d)
sudo mv dist /var/www/html/metlabs/build
sudo chown -R apache:apache /var/www/html/metlabs/build
sudo systemctl start httpd
sudo systemctl status httpd
```

---

## Step 9: Update Apache Static Files Config

```bash
sudo nano /etc/httpd/conf.d/django.conf
```

Update paths:
```apache
Alias /static/ /var/www/html/metlabs/[new-directory-name]/Backend/Backend/staticfiles

<Directory /var/www/html/metlabs/[new-directory-name]/Backend/Backend/staticfiles>
    Require shib-session
    AuthType shibboleth
</Directory>
```

Restart Apache:
```bash
sudo systemctl restart httpd
```

---

## Step 10: Verify Deployment

```bash
# Test backend
curl -I http://localhost:8000/api/

# Test frontend
curl -I http://met-metlabs.rd.tuni.fi/

# Check logs
sudo journalctl -u metlabs -n 20 --no-pager
sudo tail -20 /var/log/django_error.log

# Test in browser
# Navigate to https://met-metlabs.rd.tuni.fi
```

---

## Reference

### Database Credentials

- **Name**: metlabs
- **User**: metlabs
- **Password**: In `/etc/systemd/system/metlabs.service` or `.env` file
- **Host**: localhost
- **Port**: 5432

The database is shared and persistent across deployments.

### SELinux

The server uses SELinux in enforcing mode. The `bin_t` context is required for gunicorn.

```bash
# Check context
ls -Z /path/to/file

# Set context
sudo chcon -t bin_t /path/to/file

# Check for denials
sudo ausearch -m avc -ts recent
```

### File Ownership

- **apache:apache**: Files that Apache or backend service needs to access
- **root:root**: System configuration files

---

**Last Updated**: 2025-10-08

