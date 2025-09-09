# 📚 ReadBuddy Backend — API Server

This is the FastAPI backend server for the ReadBuddy application, providing AI-powered text processing, OCR, summarization, and text-to-speech capabilities for users with learning disabilities.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                FastAPI Application                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │   Routes    │ │  Services   │ │      Models         │ │
│  │             │ │             │ │                     │ │
│  │ • Auth      │ │ • OCR       │ │ • User              │ │
│  │ • Upload    │ │ • GPT       │ │ • Quiz              │ │
│  │ • Quizzes   │ │ • TTS       │ │ • Summary           │ │
│  │ • Summary   │ │ • Language  │ │ • Glossary          │ │
│  │ • Glossary  │ │             │ │ • Tasks             │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                Celery Task Queue                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │   Redis     │ │   Workers   │ │      Tasks          │ │
│  │             │ │             │ │                     │ │
│  │ • Broker    │ │ • Async     │ │ • Image OCR         │ │
│  │ • Results   │ │ • Parallel  │ │ • Text Summary      │ │
│  │ • Queue     │ │ • Scalable  │ │ • Quiz Generation   │ │
│  │             │ │             │ │ • Glossary Creation │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│              External Services                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │   Azure     │ │   OpenAI    │ │      MongoDB        │ │
│  │             │ │             │ │                     │ │
│  │ • OCR       │ │ • GPT-4     │ │ • Document Store    │ │
│  │ • TTS       │ │ • Embeddings│ │ • User Data         │ │
│  │ • Language  │ │ • Chat API  │ │ • History           │ │
│  │ • KeyVault  │ │             │ │ • Sessions          │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Options

### Option 1: Local Setup (Recommended for Development)

**One command to start everything:**

```powershell
.\start-backend.ps1
```

This will:
- ✅ Create/activate virtual environment
- ✅ Install/update dependencies  
- ✅ Start Redis container
- ✅ Start Celery worker
- ✅ Launch FastAPI server
- ✅ Show all server output in terminal

**Want to see Celery worker logs too?**

```powershell
.\start-backend.ps1 -ShowLogs
```

This opens Celery logs in a separate window so you can see everything happening.

### Option 2: Docker Setup (Great for Partners/Clean Environment)

**Super simple one-command setup:**

```powershell
.\start-backend-docker.ps1
```

This handles everything with Docker containers - no Python setup needed!

**Start in background and view logs:**

```powershell
.\start-backend-docker.ps1 -Detached -Logs
```

---

## 📋 Viewing Logs

### See All Server Output

```powershell
# View logs from any service
.\show-logs.ps1

# Docker logs (all services)
.\show-logs.ps1 -Mode docker

# Local setup logs
.\show-logs.ps1 -Mode local
```

**What you'll see:**
- All `print()` statements
- Logger output (info, errors, warnings)
- HTTP requests
- Celery task execution
- Everything the server prints!

---

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Backend API | http://localhost:8000 | Main API endpoints |
| API Documentation | http://localhost:8000/docs | Interactive API docs |
| Redis | localhost:6379 | Redis server |

---

## 🛠️ Development Tips

### Local Development
```powershell
# Standard start (FastAPI logs visible)
.\start-backend.ps1

# See Celery logs in separate window
.\start-backend.ps1 -ShowLogs

# View specific logs anytime
.\show-logs.ps1 -Mode local -Service redis
```

### Docker Development
```powershell
# Quick start
.\start-backend-docker.ps1

# View all logs
.\start-backend-docker.ps1 -Logs

# Manual Docker commands (from docker/ folder)
cd docker
docker-compose up --build
docker-compose logs -f
docker-compose down
```

---

## ⚠️ Requirements

### For Local Setup:
- Python 3.9+
- Docker Desktop (for Redis container)
- Azure Cognitive Services credentials (configured in `config.py`)

### For Docker Setup:
- Docker Desktop only!

---

## 🔧 Technical Stack

### Core Technologies
- **FastAPI**: Modern, fast web framework for building APIs
- **Celery**: Distributed task queue for background processing
- **Redis**: In-memory data structure store (message broker)
- **MongoDB**: NoSQL database for document storage
- **Uvicorn**: ASGI server for running FastAPI

### AI & Services
- **OpenAI GPT-4**: Text summarization and quiz generation
- **Azure Cognitive Services**: OCR, Text Analytics, Speech
- **Azure Key Vault**: Secure credential management
- **Azure Document Intelligence**: Advanced document processing

### Python Libraries
- **PyMongo**: MongoDB driver for Python
- **Pillow**: Image processing and manipulation
- **aiofiles**: Async file operations
- **python-jose**: JWT token handling
- **bcrypt**: Password hashing
- **tiktoken**: Token counting for AI models

## 📁 Project Structure

```
backend/
├── 📄 main.py                 # FastAPI application entry point
├── 📄 config.py               # Configuration and environment variables
├── 📄 celery_app.py           # Celery configuration and setup
├── 📄 key_vault.py            # Azure Key Vault integration
├── 📄 requirements.txt        # Python dependencies
├── 📄 reset_database.py       # Database reset utility
├── 📄 run.py                  # Development server runner
├── 📁 app/                    # Main application package
│   ├── 📁 models/             # Data models and schemas
│   │   ├── 📄 user.py         # User model
│   │   ├── 📄 quiz.py         # Quiz and question models
│   │   ├── 📄 summary.py      # Summary model
│   │   ├── 📄 glossary.py     # Glossary models
│   │   ├── 📄 task_status.py  # Task status model
│   │   └── 📄 ...             # Other models
│   ├── 📁 routes/             # API route handlers
│   │   ├── 📄 auth_routes.py  # Authentication endpoints
│   │   ├── 📄 image_upload.py # Image upload handling
│   │   ├── 📄 quizzes.py      # Quiz-related endpoints
│   │   ├── 📄 summaries.py    # Summary endpoints
│   │   ├── 📄 glossary.py     # Glossary endpoints
│   │   ├── 📄 task_routes.py  # Task status endpoints
│   │   └── 📄 ...             # Other route modules
│   ├── 📁 services/           # Business logic layer
│   │   ├── 📄 gpt_interface.py    # OpenAI GPT integration
│   │   ├── 📄 ocr_interface.py    # OCR processing
│   │   ├── 📄 tts_interface.py    # Text-to-speech
│   │   ├── 📄 language_interface.py # Language detection
│   │   ├── 📁 auth/               # Authentication services
│   │   └── 📁 azure/              # Azure service integrations
│   ├── 📁 tasks/              # Celery background tasks
│   │   ├── 📄 image_extraction_result_tasks.py
│   │   ├── 📄 create_quiz_task.py
│   │   ├── 📄 create_glossary_task.py
│   │   └── 📄 summarise_articles_task.py
│   └── 📁 utils/              # Utility functions
│       ├── 📄 gpt.py          # GPT utility functions
│       ├── 📄 ocr.py          # OCR utilities
│       ├── 📄 tts.py          # TTS utilities
│       ├── 📄 language.py     # Language processing
│       ├── 📄 text.py         # Text processing
│       └── 📄 ...             # Other utilities
├── 📁 database/               # Database abstraction layer
│   ├── 📄 interface.py        # Database interface
│   └── 📄 mongo_impl.py       # MongoDB implementation
├── 📁 docker/                 # Docker configuration
│   ├── 📄 Dockerfile          # Container definition
│   ├── 📄 docker-compose.yml  # Multi-service setup
│   └── 📄 DOCKER_README.md    # Docker documentation
├── 📁 static/                 # Static file serving
│   └── 📁 image/              # Image assets
├── 📁 tests/                  # Test suite
│   └── 📄 test_task_routes.py # Route testing
└── 📄 *.ps1                   # PowerShell startup scripts
```
