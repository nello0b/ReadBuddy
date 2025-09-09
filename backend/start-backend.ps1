# start-backend.ps1

# This script sets up and starts the FastAPI backend server along with
# Redis and a Celery worker using local Python environment.
# For Docker setup, use start-backend-docker.ps1 instead.

param(
    [switch]$ShowLogs    # Show Celery worker logs in separate window
)

Write-Host "Starting ReadBuddy Backend (Local Setup)..." -ForegroundColor Blue

# Step 1: Create the virtual environment if it doesn't already exist
Write-Host "1. Checking virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "   Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
}

# Step 2: Activate the virtual environment
Write-Host "2. Activating virtual environment..." -ForegroundColor Yellow
. .\venv\Scripts\Activate.ps1

# Step 3: Install the required packages
Write-Host "3. Installing/updating dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt | Out-Null

# Step 4: Start Redis using Docker (if not already running)
Write-Host "4. Starting Redis server..." -ForegroundColor Yellow
# Only run a new Redis container if one is not already present
if (-not (docker ps -a -q -f name=readbuddy-redis)) {
    Write-Host "   Creating new Redis container..." -ForegroundColor Gray
    docker run -d -p 6379:6379 --name readbuddy-redis redis | Out-Null
} else {
    Write-Host "   Starting existing Redis container..." -ForegroundColor Gray
    docker start readbuddy-redis | Out-Null
}

# Step 5: Start a Celery worker in the background
Write-Host "5. Starting Celery worker..." -ForegroundColor Yellow
if ($ShowLogs) {
    # Start Celery worker in a new window so you can see ALL output
    $celeryCommand = "cd '$PSScriptRoot'; .\venv\Scripts\Activate.ps1; Write-Host 'Celery Worker Output - All print, logger, errors:' -ForegroundColor Blue; Write-Host '--------------------------------------------------------' -ForegroundColor Gray; python -m celery -A celery_app.celery_app worker --loglevel=info --pool=solo"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $celeryCommand
    Write-Host "   Celery worker started in separate window (shows ALL output)" -ForegroundColor Gray
} else {
    Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m celery -A celery_app.celery_app worker --loglevel=info --pool=solo" -WorkingDirectory $PSScriptRoot
    Write-Host "   Celery worker started in background (use -ShowLogs to see output)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Access Points:" -ForegroundColor Blue
Write-Host "  Backend API: http://localhost:8000" -ForegroundColor Green
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  Redis: localhost:6379" -ForegroundColor Green

Write-Host ""
Write-Host "Output Information:" -ForegroundColor Blue
Write-Host "  FastAPI server: ALL output shown below - print, logger, HTTP requests, errors" -ForegroundColor Cyan
if ($ShowLogs) {
    Write-Host "  Celery worker: ALL output shown in separate window - print, logger, task logs, errors" -ForegroundColor Cyan
} else {
    Write-Host "  Celery worker: Running in background (use -ShowLogs to see ALL output)" -ForegroundColor Cyan
}
Write-Host "  Redis: Use '.\show-logs.ps1 -Mode local -Service redis' to see output" -ForegroundColor Cyan

Write-Host ""
Write-Host "Tips:" -ForegroundColor Blue
Write-Host "  Use -ShowLogs flag to see Celery worker output in separate window" -ForegroundColor Yellow
Write-Host "  Press Ctrl+C to stop the FastAPI server" -ForegroundColor Yellow
Write-Host "  Use start-backend-docker.ps1 for Docker setup" -ForegroundColor Yellow

Write-Host ""
Write-Host "6. Starting FastAPI server..." -ForegroundColor Yellow
Write-Host "FastAPI Server Output - All print, logger, HTTP requests, errors:" -ForegroundColor Blue
Write-Host "--------------------------------------------------------------------" -ForegroundColor Gray

# Step 6: Run the FastAPI server
python run.py
