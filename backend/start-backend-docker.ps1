# start-backend-docker.ps1

# This script starts the ReadBuddy backend using Docker Compose
# Benefits: Consistent environment, easy setup, no local dependencies needed

param(
    [switch]$Build,      # Force rebuild of Docker images
    [switch]$Detached,   # Run in background (detached mode)
    [switch]$Logs        # Show logs after starting
)

# Check if secret_credential.py exists in the backend directory
$secretCredentialPath = "../backend/secret_credential.py"
if (-Not (Test-Path $secretCredentialPath)) {
    Write-Host "ERROR: Required file 'secret_credential.py' is missing in the backend directory. You have to provide this file to run the backend with Docker." -ForegroundColor Red
    exit 1
}


Write-Host "Starting ReadBuddy Backend with Docker..." -ForegroundColor Blue

# Check if Docker is running
try {
    docker version | Out-Null
} catch {
    Write-Host "ERROR: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Change to docker directory to run docker-compose
Push-Location docker

# Prepare docker-compose command
$dockerCmd = "docker-compose up"

if ($Build) {
    $dockerCmd += " --build"
    Write-Host "Building Docker images..." -ForegroundColor Yellow
}

if ($Detached) {
    $dockerCmd += " -d"
    Write-Host "Starting services in background..." -ForegroundColor Green
} else {
    Write-Host "Starting services (press Ctrl+C to stop)..." -ForegroundColor Green
}

# Start the services
try {
    Invoke-Expression $dockerCmd
    
    if ($Detached -or $Logs) {
        Write-Host ""
        Write-Host "Services Status:" -ForegroundColor Blue
        docker-compose ps
        
        Write-Host ""
        Write-Host "Access Points:" -ForegroundColor Blue
        Write-Host "  Backend API: http://localhost:8000" -ForegroundColor Green
        Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Green
        Write-Host "  Redis: localhost:6379" -ForegroundColor Green
        
        if ($Logs) {
            Write-Host ""
            Write-Host "Live Output - ALL print, logger, HTTP requests, errors:" -ForegroundColor Blue
            Write-Host "Press Ctrl+C to stop viewing output..." -ForegroundColor Yellow
            docker-compose logs -f
        } else {
            Write-Host ""
            Write-Host "Commands:" -ForegroundColor Blue
            Write-Host "  View ALL output: docker-compose logs -f" -ForegroundColor Cyan
            Write-Host "  View specific service: docker-compose logs -f backend" -ForegroundColor Cyan
            Write-Host "  Stop services: docker-compose down" -ForegroundColor Cyan
            Write-Host "  Restart: docker-compose restart" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "ERROR: Failed to start services: $_" -ForegroundColor Red
    exit 1
} finally {
    # Return to original directory
    Pop-Location
}
