.PHONY: help build up down restart logs shell db-shell superuser migrate clean status test frontend-install frontend-dev frontend-build frontend-preview frontend-test fullstack

# Default target
help: ## Show this help message
	@echo "🛠️  Instrument Registry - Development Commands"
	@echo ""
	@echo "Usage: make <command>"
	@echo ""
	@echo "Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🚀 Quick start: make up"

# Docker commands
build: ## Build the Docker containers
	@echo "📦 Building containers..."
	@docker-compose build

up: ## Start all services (build if needed)
	@echo "🚀 Starting services..."
	@docker-compose up --build -d
	@echo "⏳ Waiting for services to be ready..."
	@echo "✅ Services are running!"
	@echo ""
	@echo "🌐 Django backend: http://localhost:8000"
	@echo "🗄️  PostgreSQL: localhost:5432"
	@echo ""
	@echo "📋 Next steps:"
	@echo "  - Create superuser: make superuser"
	@echo "  - View logs: make logs"
	@echo "  - Stop services: make down"

down: ## Stop all services
	@echo "🛑 Stopping services..."
	@docker-compose down

restart: ## Restart all services
	@echo "🔄 Restarting services..."
	@docker-compose restart

logs: ## Show logs from all services
	@docker-compose logs -f

logs-web: ## Show logs from Django web service only
	@docker-compose logs -f web

logs-db: ## Show logs from database service only
	@docker-compose logs -f db

# Development commands
shell: ## Access Django shell
	@echo "🐍 Opening Django shell..."
	@docker-compose exec web python manage.py shell

db-shell: ## Access PostgreSQL shell
	@echo "🗄️  Opening PostgreSQL shell..."
	@docker-compose exec db psql -U postgres -d instrumentRegistry

superuser: ## Create Django superuser
	@echo "👤 Creating Django superuser..."
	@docker-compose exec web python manage.py createsuperuser

migrate: ## Run Django migrations
	@echo "🔄 Running migrations..."
	@docker-compose exec web python manage.py migrate

makemigrations: ## Create new Django migrations
	@echo "📝 Creating migrations..."
	@docker-compose exec web python manage.py makemigrations

# Data management
export-csv: ## Export database to CSV
	@echo "📤 Exporting database to CSV..."
	@docker-compose exec web python manage.py export_csv
	@echo "✅ CSV exported to Backend/ directory"

import-csv: ## Import CSV to database (usage: make import-csv FILE=filename.csv)
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Please specify a file: make import-csv FILE=filename.csv"; \
		exit 1; \
	fi
	@echo "📥 Importing $(FILE) to database..."
	@docker-compose exec web python manage.py import_csv $(FILE)

import-csv-old: ## Import "janky" CSV with old mode (usage: make import-csv-old FILE=filename.csv)
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Please specify a file: make import-csv-old FILE=filename.csv"; \
		exit 1; \
	fi
	@echo "📥 Importing $(FILE) to database using old mode (for Excel exports)..."
	@docker-compose exec web python manage.py import_csv $(FILE) --mode old

# Testing
test: ## Run Django tests
	@echo "🧪 Running tests..."
	@docker-compose exec web python manage.py test

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	@docker-compose exec web coverage run --source='.' manage.py test
	@docker-compose exec web coverage report

# Utility commands
status: ## Show status of all services
	@echo "📊 Service status:"
	@docker-compose ps

clean: ## Stop services and remove volumes (⚠️  deletes database data)
	@echo "⚠️  This will delete all database data!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "🧹 Cleaning up..."
	@docker-compose down -v
	@docker system prune -f
	@echo "✅ Cleanup complete"

reset: ## Full reset - rebuild everything from scratch
	@echo "🔄 Full reset - rebuilding everything..."
	@docker-compose down -v
	@docker-compose build --no-cache
	@docker-compose up -d
	@echo "✅ Reset complete"

# Development helpers
dev: up ## Alias for 'up' - start development environment
	@echo "🎉 Development environment ready!"

stop: down ## Alias for 'down' - stop services

# Health check
health: ## Check if services are healthy
	@echo "🏥 Checking service health..."
	@curl -s -o /dev/null -w "Django: %{http_code}\n" http://localhost:8000 || echo "Django: Not responding"
	@docker-compose exec db pg_isready -U postgres && echo "PostgreSQL: Healthy" || echo "PostgreSQL: Not healthy"

# Frontend Development Commands
frontend-install: ## Install frontend dependencies
	@echo "📦 Installing frontend dependencies..."
	@cd Frontend && npm install
	@echo "✅ Frontend dependencies installed"

frontend-dev: ## Start frontend development server
	@echo "🚀 Starting frontend development server..."
	@echo "🌐 Frontend will be available at: http://localhost:5173"
	@cd Frontend && LAUNCH_EDITOR=idea npm run dev

frontend-build: ## Build frontend for production
	@echo "🏗️  Building frontend for production..."
	@cd Frontend && npm run build
	@echo "✅ Frontend built successfully"

frontend-preview: ## Preview production build
	@echo "👀 Starting frontend preview server..."
	@echo "🌐 Preview will be available at: http://localhost:4173"
	@cd Frontend && npm run preview

frontend-test: ## Run frontend unit tests
	@echo "🧪 Running frontend unit tests..."
	@cd Frontend && npm run test:unit

# Full stack development
fullstack: ## Start both backend and frontend in parallel
	@echo "🚀 Starting full stack development environment..."
	@echo "🔧 Backend: http://localhost:8000"
	@echo "🎨 Frontend: http://localhost:5173"
	@make up
	@echo "⏳ Waiting for backend to be ready..."
	@make frontend-dev
