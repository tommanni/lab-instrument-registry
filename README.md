# Instrument Registry for METLAB

A Django REST API backend with Vue.js frontend for managing laboratory equipment inventory.

## Git Policy

- All changes should be merged into `dev` via a merge request.
- All merge requests should be reviewed by at least one person.
- When starting work on a new issue, create a new branch:
  - A new branch can be created in multiple ways
    - First make sure you are currently on the `dev` branch and you have the newest changes locally
      - you can pull the latest changes by running `git pull origin dev`
    - To create the branch: one example is `git checkout -b <branch-name>`)
  - Begin the branch name with the issue ID, followed by a short description separated by hyphens.
  - Example: Issue #34232 is about deleting the whole system, branch naming would be `34232-delete-entire-system`.
  - Including the issue ID helps GitLab automatically link the branch to the issue under "Related branches".
- When necessary changes have been checked by the customer, `dev` is merged into `main`
- Write code comments in English.
- Use `snake_case` for variable names in Python.
- Use `camelCase` for variable names in Vue.


## 🚀 Quick Start

```
Assuming you have the repo already cloned, follow the instructions below:

# 1. Start the backend, database, and semantic search service
make up

# 2. Import your data (optional), file needs to be in the Backend directory under root
make import-csv-old FILE=your-data.csv 

# 3.1 Install dependencies (first time only) with
make frontend-install

# 3.2 Start frontend in dev mode
make frontend-dev

If it complains about Node.js version, run the following command in the Frontend folder:
nvm use

# 3. Access the system
Frontend: http://localhost:5173

In the future once data has been imported, you can simply run:
make fullstack
```

## 📋 Prerequisites

**Required:**
- **Docker Desktop** - https://www.docker.com/products/docker-desktop/
- **Git** - Usually pre-installed (Windows: https://git-scm.com/)
- **Make** - Pre-installed on Mac/Linux. Windows: `choco install make` or use Git Bash

**Optional (frontend development only):**
- **Node.js 18+** - https://nodejs.org/
- **Node Version Manager (nvm)** - https://github.com/nvm-sh/nvm or fnm

## 🛠️ Development Commands

### Backend (Django + PostgreSQL)
```bash
make up          # Start backend services
make semantic-search   # Start semantic search service only
make down        # Stop services
make logs        # View logs
make shell       # Django shell
make db-shell    # PostgreSQL shell
make test        # Run tests
```

### Data Management
```bash
# Import commands compute translations and embeddings for instruments automatically
make import-csv-old FILE=data.csv    # Import Excel CSV
make import-csv FILE=data.csv        # Import normal CSV (already in correct format)
make export-csv                      # Export to CSV
make preprocess-instruments          # Compute translations and embeddings for instruments manually 
```

### Frontend (Vue.js)
```bash
make frontend-install    # Install dependencies (first time)
make frontend-dev        # Start dev server (http://localhost:5173)
make frontend-build      # Build for production
make frontend-test       # Run tests
```

### Full Stack
```bash
make fullstack          # Start both backend + frontend
```

### Semantic Search Service
```bash
make semantic-search          # (Re)start FastAPI translator/embedding service
docker compose logs -f semantic-search-service   # Follow logs
```
The semantic-search container powers Finnish→English translations and English embeddings; imports and preprocessing commands rely on it.

## 🗂️ Project Structure

```
├── Backend/           # Django REST API
│   ├── instrument_registry/  # Main app
│   ├── requirements.txt
│   └── manage.py
├── Frontend/          # Vue.js SPA
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── semantic_search_service/ # FastAPI translator + embedding microservice
├── docker-compose.yml # Services configuration
└── Makefile          # Development commands
```

## 📊 Features

- **REST API** - Full CRUD operations for instruments
- **CSV Import/Export** - Handle Excel data easily
- **Search & Filter** - Find instruments by various criteria
- **User Authentication** - Token-based auth with Knox
- **Responsive UI** - Vue.js frontend with Bootstrap
- **Docker Ready** - Containerized development environment

## 🔧 Configuration

The system uses Docker environment variables (no manual setup needed):
- **Database:** PostgreSQL 17 on port 5432
- **Backend:** Django on port 8000
- **Frontend:** Vite dev server on port 5173

## 🚨 Troubleshooting

### Windows Users
If `make` commands don't work, use Docker Compose directly:
```bash
docker-compose up        # Instead of 'make up'
docker-compose down      # Instead of 'make down'
docker-compose logs -f   # Instead of 'make logs'
```

### Common Issues
- **Port conflicts:** Stop other services using ports 5432, 8000, 5173
- **Docker not running:** Start Docker Desktop
- **Permission errors:** Ensure Docker has proper permissions

## 📚 Additional Documentation

- **Backend details:** `Backend/README.md`
- **Frontend details:** `Frontend/README.md`
- **Original setup instructions:** `Backend/instructions/`

## 🎯 Architecture

**API-First Design:**
- Django REST API backend handles all data operations
- Vue.js frontend consumes the API
- PostgreSQL database for data persistence
- Token-based authentication
- Docker containers for easy deployment

---

**Need help?** Run `make help` to see all available commands.
