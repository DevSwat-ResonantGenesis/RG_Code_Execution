# Configuration for Code Execution Microservice

import os
import secrets
from dotenv import load_dotenv

load_dotenv()


def _get_required_secret(env_var: str, default_dev: str, environment: str) -> str:
    """Get a secret from environment, fail closed in production if not set."""
    value = os.getenv(env_var)
    if value:
        return value
    if environment == "production":
        raise ValueError(f"CRITICAL: {env_var} must be set in production environment!")
    print(f"[WARNING] Using generated default {env_var} - set via environment for production!")
    return default_dev


class Settings:
    SERVICE_NAME = "code-execution"
    VERSION = "1.0.0"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8002))
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development | staging | production

    # Execution settings
    EXECUTION_TIMEOUT = int(os.getenv("EXECUTION_TIMEOUT", 30))  # seconds
    MAX_OUTPUT_SIZE = int(os.getenv("MAX_OUTPUT_SIZE", 1024 * 1024))  # 1MB

    # Sandbox settings
    SANDBOX_ENABLED = os.getenv("SANDBOX_ENABLED", "true").lower() == "true"
    ALLOWED_LANGUAGES = ["python", "javascript", "typescript", "bash", "shell"]

    # Preview server settings
    PREVIEW_PORT_RANGE_START = int(os.getenv("PREVIEW_PORT_START", 3000))
    PREVIEW_PORT_RANGE_END = int(os.getenv("PREVIEW_PORT_END", 3100))

    # Sandbox root: preview projects and terminal cwd must resolve under this
    # directory — prevents path-traversal into arbitrary host paths.
    SANDBOX_ROOT = os.path.realpath(os.getenv("SANDBOX_ROOT", "/tmp/rg_code_exec"))

    # SECURITY: this service is reachable by every other container on
    # app-network and has /var/run/docker.sock mounted (needed for its own
    # Docker-sandboxed execution) — without this key, ANY other container on
    # that network (e.g. one compromised via an unrelated bug) can run
    # arbitrary shell commands here and pivot to full host root via the
    # mounted socket. Every legitimate internal caller must send this value
    # in the `x-internal-service-key` header.
    INTERNAL_SERVICE_KEY = ""


settings = Settings()

if not settings.INTERNAL_SERVICE_KEY:
    settings.INTERNAL_SERVICE_KEY = _get_required_secret(
        "CODE_EXECUTION_INTERNAL_SERVICE_KEY",
        "internal-service-key-" + secrets.token_hex(8),
        settings.ENVIRONMENT,
    )
