import os
from __init__ import vault

# MongoDB connection string - auto-detect Docker vs local environment
def get_database_url():
    # Check if we're running in Docker by looking for the container environment
    if os.path.exists('/.dockerenv') or os.environ.get('RUNNING_IN_DOCKER'):
        # Running in Docker - use service name from docker-compose.yml
        return "mongodb://mongodb:27017"
    else:
        # Running locally - use localhost
        return "mongodb://localhost:27017"

DATABASE_URL = os.environ.get('DATABASE_URL', get_database_url())

# Server config
SERVER_HOST = os.environ.get('SERVER_HOST', "0.0.0.0")  # Use 0.0.0.0 for Docker compatibility
SERVER_PORT = int(os.environ.get('SERVER_PORT', 8000))

# Auth0 config
AUTH0_DOMAIN = "dev-0k5re5452sqz7ypj.eu.auth0.com"
AUTH0_AUDIENCE = "https://readbuddy/api"

# Set to True for debug mode, False for production
DEBUG_MODE = True

# Database key for deletion
DATABASE_KEY = vault.database_key

# Azure config
key_dict = {
    "AZURE_SPEECH_KEY": "tts-key",
    "AZURE_READ_KEY": "ocr-key",
    "AZURE_LANGUAGE_KEY": "language-key",
    "AZURE_GPT_KEY": "gpt-key"
}

AZURE_SPEECH_KEY = vault.tts_key
AZURE_SPEECH_ENDPOINT = "https://westeurope.api.cognitive.microsoft.com/"
AZURE_SPEECH_REGION = "westeurope"

AZURE_READ_KEY = vault.ocr_key
AZURE_READ_ENDPOINT = "https://readbuddyocr-eu.cognitiveservices.azure.com/"
AZURE_READ_REGION = "westeurope"

AZURE_LANGUAGE_KEY = vault.language_key
AZURE_LANGUAGE_ENDPOINT = "https://readbuddylanguage-eu.cognitiveservices.azure.com/"
AZURE_LANGUAGE_REGION = "westeurope"

AZURE_GPT_KEY = vault.gpt_key
AZURE_GPT_ENDPOINT = "https://netan-mayc86mv-swedencentral.cognitiveservices.azure.com/"
AZURE_GPT_API_VERSION = "2024-12-01-preview"

# Azure GPT model configuration
TOKENS_PER_MINUTE_4O_MINI = 200000
TOKENS_PER_MINUTE_35_TURBO = 200000
TOKENS_PER_MINUTE_4O = 50000

MAX_TOTAL_ALLOWED_35_TURBO = 4096
MAX_TOTAL_ALLOWED_4O_MINI = 8192 # Real 128000 # 128K
MAX_TOTAL_ALLOWED_4O = 8192 # Real 1000000 # 1M

# Base and Advance models
AZURE_GPT_DEPLOYMENT_BASE = "gpt-4o-mini" # gpt-35-turbo # gpt-4o-mini # gpt-4o
TOKENS_PER_MINUTE_BASE = TOKENS_PER_MINUTE_4O_MINI
MAX_TOTAL_ALLOWED_BASE = MAX_TOTAL_ALLOWED_4O_MINI

# Advance models
AZURE_GPT_DEPLOYMENT_ADVANCE = "gpt-4o" # gpt-35-turbo # gpt-4o-mini # gpt-4o
TOKENS_PER_MINUTE_ADVANCE = TOKENS_PER_MINUTE_4O
MAX_TOTAL_ALLOWED_ADVANCE = MAX_TOTAL_ALLOWED_4O

TOKENIZER = "cl100k_base"  # cl100k_base for gpt-4o, gpt-4o-mini, and gpt-35-turbo

MAX_CONCURRENT_REQUESTS = 10  # Set the maximum concurrent requests to 20

# Azure OCR configuration
MIN_DIMENSION = 50
MAX_DIMENSION = 10000