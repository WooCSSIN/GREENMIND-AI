# 🐳 Docker Deployment Guide for GreenMind AI

**Status:** Ready for Production  
**Docker Version:** 20.10+  
**Docker Compose Version:** 2.0+

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Services Overview](#services-overview)
5. [Development vs Production](#development-vs-production)
6. [Troubleshooting](#troubleshooting)
7. [Scaling](#scaling)

---

## 📦 Prerequisites

### Install Docker & Docker Compose

**Windows:**
```bash
# Download Docker Desktop from https://www.docker.com/products/docker-desktop
# Or use Chocolatey
choco install docker-desktop
```

**macOS:**
```bash
# Using Homebrew
brew install docker docker-compose

# Or download Docker Desktop
# https://www.docker.com/products/docker-desktop
```

**Linux (Ubuntu/Debian):**
```bash
# Install Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### Verify Installation
```bash
docker --version
docker-compose --version
```

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/WooCSSIN/GREENMIND-AI.git
cd GREENMIND-AI
```

### 2. Create Environment File
```bash
cp .env.example .env
```

**Edit .env:**
```env
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this
ALLOWED_HOSTS=localhost,127.0.0.1,web
DB_SERVER=sqlserver
DB_NAME=GreenMind
DB_USER=sa
DB_PASSWORD=YourPassword123!
REDIS_URL=redis://redis:6379/0
```

### 3. Build & Start Services
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f web
```

### 4. Run Migrations
```bash
docker-compose exec web python manage.py migrate
```

### 5. Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### 6. Access Application
- **Web:** http://localhost:8000
- **Admin:** http://localhost:8000/admin
- **API:** http://localhost:8000/api/v1/

---

## ⚙️ Configuration

### Environment Variables

**core/.env:**
```env
# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,web,your-domain.com
CSRF_TRUSTED_ORIGINS=http://localhost:8000,https://your-domain.com

# Database
DB_SERVER=sqlserver
DB_NAME=GreenMind
DB_USER=sa
DB_PASSWORD=YourPassword123!

# Redis
REDIS_URL=redis://redis:6379/0

# Channels
CHANNEL_LAYERS_BACKEND=channels_redis.core.RedisChannelLayer
CHANNEL_LAYERS_CONFIG_HOSTS=redis:6379

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# AI Engine
STORAGE_KWH_PER_UNIT=0.002
GRID_EMISSION_VN=0.4937
```

### Docker Compose Override (Development)

**docker-compose.override.yml:**
```yaml
version: '3.8'

services:
  web:
    environment:
      - DEBUG=True
    command: python manage.py runserver 0.0.0.0:8000
    ports:
      - "8000:8000"
```

---

## 🏗️ Services Overview

### 1. Redis (Message Broker & Cache)
```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# Check connection
PING

# View keys
KEYS *

# Monitor real-time commands
MONITOR
```

### 2. Web (Django Application)
```bash
# View logs
docker-compose logs -f web

# Run management commands
docker-compose exec web python manage.py shell

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### 3. Celery (Async Tasks)
```bash
# View logs
docker-compose logs -f celery

# Inspect active tasks
docker-compose exec celery celery -A core inspect active
```

### 4. Celery Beat (Scheduled Tasks)
```bash
# View logs
docker-compose logs -f celery-beat
```

### 5. Nginx (Reverse Proxy)
```bash
# View logs
docker-compose logs -f nginx

# Test configuration
docker-compose exec nginx nginx -t

# Reload configuration
docker-compose exec nginx nginx -s reload
```

---

## 🔄 Development vs Production

### Development Setup

**docker-compose.override.yml:**
```yaml
version: '3.8'

services:
  web:
    environment:
      - DEBUG=True
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
```

**Start:**
```bash
docker-compose up -d
```

### Production Setup

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  web:
    environment:
      - DEBUG=False
    command: daphne -b 0.0.0.0 -p 8000 core.asgi:application
    restart: always
    
  nginx:
    restart: always
    
  redis:
    restart: always
```

**Start:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 🐛 Troubleshooting

### Issue: Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"
```

### Issue: Redis Connection Failed
```bash
# Check Redis is running
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Test connection
docker-compose exec redis redis-cli ping
```

### Issue: Database Connection Failed
```bash
# Check SQL Server is running
docker-compose ps sqlserver

# Check logs
docker-compose logs sqlserver

# Test connection
docker-compose exec web python manage.py dbshell
```

### Issue: WebSocket Connection Failed
```bash
# Check Daphne is running
docker-compose logs web

# Check Redis Pub/Sub
docker-compose exec redis redis-cli
> SUBSCRIBE dashboard_updates

# Test WebSocket
# Open browser console and check ws:// connection
```

### Issue: Static Files Not Loading
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check Nginx configuration
docker-compose exec nginx nginx -t

# Reload Nginx
docker-compose exec nginx nginx -s reload
```

---

## 📈 Scaling

### Horizontal Scaling (Multiple Web Instances)

**docker-compose.scale.yml:**
```yaml
version: '3.8'

services:
  web:
    deploy:
      replicas: 3
    
  nginx:
    depends_on:
      - web
```

**Start:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d
```

### Load Balancing with Nginx

**nginx.conf:**
```nginx
upstream django {
    least_conn;
    server web:8000;
    server web:8001;
    server web:8002;
}
```

### Redis Cluster (High Availability)

**docker-compose.redis-cluster.yml:**
```yaml
version: '3.8'

services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --port 6379
    
  redis-slave:
    image: redis:7-alpine
    command: redis-server --port 6380 --slaveof redis-master 6379
    depends_on:
      - redis-master
```

---

## 🔐 Security Best Practices

### 1. Change Default Passwords
```env
# .env
DB_PASSWORD=GenerateStrongPassword123!
SECRET_KEY=GenerateRandomSecretKey
```

### 2. Use HTTPS in Production
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
}
```

### 3. Restrict Network Access
```yaml
# docker-compose.yml
networks:
  greenmind-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 4. Use Secrets Management
```bash
# Docker Secrets (Swarm mode)
echo "password" | docker secret create db_password -

# Or use environment files
docker-compose --env-file .env.prod up -d
```

---

## 📊 Monitoring

### Docker Stats
```bash
# View resource usage
docker stats

# Specific container
docker stats greenmind-web
```

### Logs
```bash
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f web

# Last 100 lines
docker-compose logs --tail=100 web

# Since specific time
docker-compose logs --since 2026-05-26T10:00:00 web
```

### Health Checks
```bash
# Check service health
docker-compose ps

# Manual health check
docker-compose exec web curl http://localhost:8000/health/
```

---

## 🧹 Cleanup

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all
```

### Remove Unused Resources
```bash
# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Remove everything unused
docker system prune -a
```

---

## 📚 Useful Commands

```bash
# Build specific service
docker-compose build web

# Rebuild without cache
docker-compose build --no-cache web

# Push to registry
docker-compose push

# Pull latest images
docker-compose pull

# Validate compose file
docker-compose config

# View service dependencies
docker-compose config --services

# Execute command in running container
docker-compose exec web bash

# View container processes
docker-compose top web

# Pause services
docker-compose pause

# Unpause services
docker-compose unpause

# Restart services
docker-compose restart

# Restart specific service
docker-compose restart web
```

---

## 🚀 CI/CD Integration

### GitHub Actions
```yaml
# .github/workflows/docker.yml
name: Build and Push Docker Image

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-buildx-action@v2
      - uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: your-registry/greenmind:latest
```

---

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Check health: `docker-compose ps`
3. Create issue: https://github.com/WooCSSIN/GREENMIND-AI/issues

---

**Last Updated:** May 26, 2026  
**Status:** Production Ready
