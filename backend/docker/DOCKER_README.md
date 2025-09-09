# ReadBuddy Backend - Setup Guide

## 🚀 Quick Start Options

### Option 1: Docker Setup (Recommended for New Users)
**Best for**: Consistent environment, easy setup, partners/collaborators

```powershell
# Start everything with Docker (from backend directory)
.\start-backend-docker.ps1

# Start in background and show logs
.\start-backend-docker.ps1 -Detached -Logs

# Force rebuild images
.\start-backend-docker.ps1 -Build
```

### Option 2: Local Python Setup (Current Method)
**Best for**: Development, debugging, direct control

```powershell
# Start with FastAPI logs visible (current behavior)
.\start-backend.ps1

# Start with Celery logs in separate window
.\start-backend.ps1 -ShowLogs
```

## 📋 Viewing Logs

### Docker Logs
```powershell
# View all service logs
.\show-logs.ps1 -Mode docker

# View specific service logs
.\show-logs.ps1 -Mode docker -Service backend
.\show-logs.ps1 -Mode docker -Service celery
.\show-logs.ps1 -Mode docker -Service redis
```

### Local Setup Logs
```powershell
# View Redis logs
.\show-logs.ps1 -Mode local -Service redis

# FastAPI logs: visible in main terminal
# Celery logs: use .\start-backend.ps1 -ShowLogs
```

## 🛠️ Development Commands

### Docker Development
```powershell
# Start services (from backend directory)
cd docker
docker-compose up --build

# Start in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart specific service
docker-compose restart backend
```

### Local Development
```powershell
# Standard start
.\start-backend.ps1

# With Celery logs visible
.\start-backend.ps1 -ShowLogs

# Manual Celery restart (if needed)
# Stop: Ctrl+C in Celery window
# Start: python -m celery -A celery_app.celery_app worker --loglevel=info --pool=solo
```

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Backend API | http://localhost:8000 | Main API endpoints |
| API Documentation | http://localhost:8000/docs | Interactive API docs |
| Redis | localhost:6379 | Redis server |

## 🔧 Configuration

### Simple Setup (No Environment Variables Needed)
The backend uses hard-coded configuration from `config.py`. No environment file setup required!

### Docker vs Local Differences
- **Docker**: Uses `redis://redis:6379/0` (internal Docker network)
- **Local**: Uses `redis://localhost:6379/0` (localhost)
- Both configurations are handled automatically

## 🎯 Use Cases

### For Your Partner (Easy Setup)
```powershell
# One-time setup
git clone your-repo
cd backend

# Every time
.\start-backend-docker.ps1
```

### For You (Development)
```powershell
# See everything happening
.\start-backend.ps1 -ShowLogs

# Or use Docker for consistency
.\start-backend-docker.ps1 -Logs
```

### For Production
- Use Docker setup
- Configure proper Azure credentials in `config.py`
- Add reverse proxy (nginx)
- Set up SSL/TLS

## 🐛 Troubleshooting

### Common Issues
1. **Port conflicts**: Change ports in docker/docker-compose.yml
2. **Docker not running**: Start Docker Desktop
3. **Permission issues**: Run as administrator (Windows)

### Log Locations
- **Docker**: `.\show-logs.ps1 -Mode docker` or `cd docker && docker-compose logs -f`
- **Local FastAPI**: Main terminal
- **Local Celery**: Separate window (with -ShowLogs) or background
- **Redis**: `docker logs -f readbuddy-redis`

## 📁 File Organization

```
backend/
├── start-backend.ps1           # Local setup script
├── start-backend-docker.ps1    # Docker setup script  
├── show-logs.ps1              # Log viewing helper
├── docker/                    # All Docker files
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .dockerignore
│   └── DOCKER_README.md
├── app/                       # Your application code
├── static/                    # Static files
└── temp/                      # Temporary files
```
