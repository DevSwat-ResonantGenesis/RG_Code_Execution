# Configuration for Code Execution Microservice

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SERVICE_NAME = "code-execution"
    VERSION = "1.0.0"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8002))
    
    # Execution settings
    EXECUTION_TIMEOUT = int(os.getenv("EXECUTION_TIMEOUT", 30))  # seconds
    MAX_OUTPUT_SIZE = int(os.getenv("MAX_OUTPUT_SIZE", 1024 * 1024))  # 1MB
    
    # Sandbox settings
    SANDBOX_ENABLED = os.getenv("SANDBOX_ENABLED", "true").lower() == "true"
    ALLOWED_LANGUAGES = ["python", "javascript", "typescript", "bash", "shell"]
    
    # Preview server settings
    PREVIEW_PORT_RANGE_START = int(os.getenv("PREVIEW_PORT_START", 3000))
    PREVIEW_PORT_RANGE_END = int(os.getenv("PREVIEW_PORT_END", 3100))

settings = Settings()
